import random

import pygame

from game.jewel import Jewel
from game.animation import AnimationManager, MoveAnimation, ScaleAnimation, ExplosionEffect
from game.effects import (
    SPECIAL_BOMB,
    SPECIAL_COLOR,
    SPECIAL_LINE_H,
    SPECIAL_LINE_V,
    special_positions,
)


class Board:
    """Match-3 board with swap/match/fall animations."""

    def __init__(self, settings, level_conf):
        self.settings = settings
        self.rows = settings["board"]["rows"]
        self.cols = settings["board"]["cols"]
        self.tile_size = settings["board"]["tile_size"]
        self.origin = settings["board"]["origin"]
        self.colors = settings["colors"]
        self.swap_time = settings["animation"]["swap_time"]
        self.remove_time = settings["animation"]["remove_time"]
        self.fall_time = settings["animation"]["fall_time"]
        self.score_base = settings["score"]["base"]
        self.score_cascade = settings["score"]["cascade_multiplier"]
        self.score_special = settings["score"]["special_bonus"]
        self.level_conf = level_conf
        self.jewel_type_count = min(level_conf.get("jewel_types", 6), len(self.colors))
        self.rng = random.Random()
        self.blocked = {tuple(cell) for cell in level_conf.get("blocked", [])}

        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.animations = AnimationManager()
        self.effects = []
        self.state = "idle"
        self.selected = None
        self.swap_positions = None
        self.pending_removals = set()
        self.pending_specials = {}
        self.cascade_step = 0
        self.events = []

        self._generate_initial_board()
        self.rescale(
            self.settings["screen"]["width"],
            self.settings["screen"]["height"],
        )

    def _cell_center(self, row, col):
        x = self.origin[0] + col * self.tile_size + self.tile_size / 2
        y = self.origin[1] + row * self.tile_size + self.tile_size / 2
        return x, y

    def _create_jewel(self, row, col, color_id=None, special=None):
        if color_id is None:
            color_id = self.rng.randrange(self.jewel_type_count)
        jewel = Jewel(color_id, row, col, self.tile_size, special=special)
        x, y = self._cell_center(row, col)
        jewel.set_pixel_pos(x, y)
        return jewel

    def _generate_initial_board(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.blocked:
                    self.grid[r][c] = None
                    continue
                color_id = self._choose_color_without_match(r, c)
                jewel = self._create_jewel(r, c, color_id=color_id)
                self.grid[r][c] = jewel

    def _choose_color_without_match(self, row, col):
        attempts = list(range(self.jewel_type_count))
        self.rng.shuffle(attempts)
        for color_id in attempts:
            if not self._creates_match(row, col, color_id):
                return color_id
        return self.rng.randrange(self.jewel_type_count)

    def _creates_match(self, row, col, color_id):
        # Check horizontal
        if col >= 2:
            left1 = self.grid[row][col - 1]
            left2 = self.grid[row][col - 2]
            if left1 and left2 and left1.color_id == color_id and left2.color_id == color_id:
                return True
        # Check vertical
        if row >= 2:
            up1 = self.grid[row - 1][col]
            up2 = self.grid[row - 2][col]
            if up1 and up2 and up1.color_id == color_id and up2.color_id == color_id:
                return True
        return False

    def reset(self, level_conf):
        self.level_conf = level_conf
        self.jewel_type_count = min(level_conf.get("jewel_types", 6), len(self.colors))
        self.blocked = {tuple(cell) for cell in level_conf.get("blocked", [])}
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.animations.clear()
        self.effects = []
        self.state = "idle"
        self.selected = None
        self.swap_positions = None
        self.pending_removals = set()
        self.pending_specials = {}
        self.cascade_step = 0
        self.events = []
        self._generate_initial_board()
        self.rescale(
            self.settings["screen"]["width"],
            self.settings["screen"]["height"],
        )

    def rescale(self, screen_w, screen_h):
        max_w = int(screen_w * 0.65)
        max_h = int(screen_h * 0.65)
        self.tile_size = max(36, min(max_w // self.cols, max_h // self.rows))
        board_w = self.cols * self.tile_size
        board_h = self.rows * self.tile_size
        self.origin = ((screen_w - board_w) // 2, (screen_h - board_h) // 2)
        for r in range(self.rows):
            for c in range(self.cols):
                jewel = self.grid[r][c]
                if jewel:
                    jewel.tile_size = self.tile_size
                    jewel.set_pixel_pos(*self._cell_center(r, c))
        self.animations.clear()
        self.effects = []

    def handle_click(self, pos):
        if self.state != "idle":
            return
        cell = self.cell_at_point(pos)
        if cell is None:
            return
        if cell in self.blocked:
            return
        if self.selected is None:
            self.selected = cell
            return
        if cell == self.selected:
            self.selected = None
            return
        if self._is_adjacent(cell, self.selected):
            self.start_swap(self.selected, cell)
            self.selected = None
        else:
            self.selected = cell

    def cell_at_point(self, pos):
        x, y = pos
        board_x, board_y = self.origin
        if x < board_x or y < board_y:
            return None
        col = int((x - board_x) // self.tile_size)
        row = int((y - board_y) // self.tile_size)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None

    def _is_adjacent(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def start_swap(self, pos_a, pos_b):
        jewel_a = self.grid[pos_a[0]][pos_a[1]]
        jewel_b = self.grid[pos_b[0]][pos_b[1]]
        if jewel_a is None or jewel_b is None:
            return
        # Swap in grid first
        self._swap_grid(pos_a, pos_b)
        self.swap_positions = (pos_a, pos_b)
        self.cascade_step = 0
        self.state = "swapping"

        start_a = (jewel_a.x, jewel_a.y)
        start_b = (jewel_b.x, jewel_b.y)
        end_a = self._cell_center(jewel_a.row, jewel_a.col)
        end_b = self._cell_center(jewel_b.row, jewel_b.col)

        self.animations.add(MoveAnimation(jewel_a, start_a, end_a, self.swap_time))
        self.animations.add(MoveAnimation(jewel_b, start_b, end_b, self.swap_time))

    def _swap_grid(self, pos_a, pos_b):
        ra, ca = pos_a
        rb, cb = pos_b
        self.grid[ra][ca], self.grid[rb][cb] = self.grid[rb][cb], self.grid[ra][ca]
        if self.grid[ra][ca]:
            self.grid[ra][ca].row, self.grid[ra][ca].col = ra, ca
        if self.grid[rb][cb]:
            self.grid[rb][cb].row, self.grid[rb][cb].col = rb, cb

    def update(self, dt):
        self._update_effects(dt)
        self.animations.update(dt)
        if self.animations.is_busy():
            return

        if self.state == "swapping":
            matches = self.find_matches()
            if not matches:
                # Check for color special activation
                pos_a, pos_b = self.swap_positions
                jewel_a = self.grid[pos_a[0]][pos_a[1]]
                jewel_b = self.grid[pos_b[0]][pos_b[1]]
                if jewel_a and jewel_a.special == SPECIAL_COLOR:
                    self._activate_color_swap(pos_a, jewel_b.color_id)
                    return
                if jewel_b and jewel_b.special == SPECIAL_COLOR:
                    self._activate_color_swap(pos_b, jewel_a.color_id)
                    return
                # revert swap
                self._swap_grid(pos_a, pos_b)
                self.state = "reverting"
                self.events.append({"type": "swap_invalid"})
                start_a = (jewel_a.x, jewel_a.y)
                start_b = (jewel_b.x, jewel_b.y)
                end_a = self._cell_center(jewel_a.row, jewel_a.col)
                end_b = self._cell_center(jewel_b.row, jewel_b.col)
                self.animations.add(MoveAnimation(jewel_a, start_a, end_a, self.swap_time))
                self.animations.add(MoveAnimation(jewel_b, start_b, end_b, self.swap_time))
            else:
                self._begin_remove(matches)
        elif self.state == "reverting":
            self.state = "idle"
        elif self.state == "removing":
            self._apply_removals()
            self._collapse_and_fill()
        elif self.state == "falling":
            matches = self.find_matches()
            if matches:
                self.cascade_step += 1
                self._begin_remove(matches)
            else:
                self.state = "idle"

    def _activate_color_swap(self, color_pos, target_color):
        positions = special_positions(SPECIAL_COLOR, color_pos, self.rows, self.cols, target_color, self.grid)
        self.pending_removals = positions
        self.pending_specials = {}
        for pos in positions:
            jewel = self.grid[pos[0]][pos[1]]
            if jewel:
                self.animations.add(ScaleAnimation(jewel, 1.0, 0.0, self.remove_time))
        self.state = "removing"
        self.events.append({"type": "special", "count": 1})

    def _begin_remove(self, matches):
        removal, specials_to_create, activated_specials, explosions = self._compute_removals(matches)
        self.pending_removals = removal
        self.pending_specials = specials_to_create

        for pos in removal:
            jewel = self.grid[pos[0]][pos[1]]
            if jewel:
                self.animations.add(ScaleAnimation(jewel, 1.0, 0.0, self.remove_time))

        if activated_specials:
            self.events.append({"type": "special", "count": activated_specials})
        for pos in explosions:
            center = self._cell_center(pos[0], pos[1])
            self.effects.append(
                ExplosionEffect(center, duration=self.remove_time + 0.25, max_radius=int(self.tile_size * 1.1))
            )

        self.state = "removing"

    def _compute_removals(self, matches):
        removal = set()
        specials_to_create = {}
        activated_specials = 0
        explosions = []
        if self._should_clear_board(matches):
            for r in range(self.rows):
                for c in range(self.cols):
                    if (r, c) in self.blocked:
                        continue
                    if self.grid[r][c]:
                        removal.add((r, c))
            for pos in removal:
                jewel = self.grid[pos[0]][pos[1]]
                if jewel and jewel.special == SPECIAL_BOMB:
                    explosions.append(pos)
            return removal, {}, 2, explosions

        counts = {}
        for match in matches:
            for pos in match["positions"]:
                counts[pos] = counts.get(pos, 0) + 1

        # T/L intersection -> bomb
        for pos, count in counts.items():
            if count >= 2:
                specials_to_create[pos] = SPECIAL_BOMB

        for match in matches:
            positions = list(match["positions"])
            if len(positions) >= 5:
                anchor = self._choose_anchor(positions)
                if anchor not in specials_to_create:
                    specials_to_create[anchor] = SPECIAL_COLOR
            elif len(positions) == 4:
                anchor = self._choose_anchor(positions)
                if anchor not in specials_to_create:
                    specials_to_create[anchor] = (
                        SPECIAL_LINE_H if match["orientation"] == "h" else SPECIAL_LINE_V
                    )
            removal.update(positions)

        # Keep specials that will be created
        removal -= set(specials_to_create.keys())

        # Expand removals by activated specials
        expanded = set(removal)
        for pos in list(removal):
            jewel = self.grid[pos[0]][pos[1]]
            if jewel and jewel.special:
                if jewel.special == SPECIAL_COLOR:
                    target_color = self._color_from_match(pos, matches)
                    expanded |= special_positions(
                        jewel.special, pos, self.rows, self.cols, target_color, self.grid
                    )
                else:
                    expanded |= special_positions(jewel.special, pos, self.rows, self.cols)
                activated_specials += 1
                if jewel.special == SPECIAL_BOMB:
                    explosions.append(pos)

        expanded -= set(specials_to_create.keys())
        return expanded, specials_to_create, activated_specials, explosions

    def _should_clear_board(self, matches):
        yellow_id = 2
        for match in matches:
            positions = list(match["positions"])
            for pos in positions:
                jewel = self.grid[pos[0]][pos[1]]
                if not jewel:
                    continue
                if jewel.special != SPECIAL_BOMB or jewel.color_id != yellow_id:
                    continue
                # look for vertical neighbor bomb in same match
                for other in positions:
                    if other[1] == pos[1] and abs(other[0] - pos[0]) == 1:
                        other_jewel = self.grid[other[0]][other[1]]
                        if other_jewel and other_jewel.special == SPECIAL_BOMB and other_jewel.color_id == yellow_id:
                            return True
        return False

    def _color_from_match(self, pos, matches):
        for match in matches:
            if pos in match["positions"]:
                for other in match["positions"]:
                    if other != pos:
                        jewel = self.grid[other[0]][other[1]]
                        if jewel:
                            return jewel.color_id
        return self.rng.randrange(self.jewel_type_count)

    def _choose_anchor(self, positions):
        if self.swap_positions:
            for pos in self.swap_positions:
                if pos in positions:
                    return pos
        return positions[0]

    def _apply_removals(self):
        removed_count = len(self.pending_removals)
        for pos in self.pending_removals:
            self.grid[pos[0]][pos[1]] = None
        for pos, special in self.pending_specials.items():
            jewel = self.grid[pos[0]][pos[1]]
            if jewel:
                jewel.special = special
                jewel.scale = 1.0

        if removed_count > 0:
            multiplier = 1.0 + self.cascade_step * self.score_cascade
            score = int(self.score_base * removed_count * multiplier)
            score += int(self.score_special * max(0, len(self.pending_specials)))
            self.events.append({"type": "score", "value": score})
            self.events.append({"type": "match", "count": removed_count})

        self.pending_removals = set()
        self.pending_specials = {}

    def _collapse_and_fill(self):
        moves = []
        for col in range(self.cols):
            segment_rows = []
            for row in range(self.rows - 1, -1, -1):
                if (row, col) in self.blocked:
                    self._process_segment(col, segment_rows, moves)
                    segment_rows = []
                else:
                    segment_rows.append(row)
            self._process_segment(col, segment_rows, moves)

        for jewel, start_pos, end_pos in moves:
            self.animations.add(MoveAnimation(jewel, start_pos, end_pos, self.fall_time))

        self.state = "falling"

    def _process_segment(self, col, segment_rows, moves):
        if not segment_rows:
            return
        jewels = []
        for row in segment_rows:
            jewel = self.grid[row][col]
            if jewel:
                jewels.append(jewel)
        for row in segment_rows:
            self.grid[row][col] = None
        for idx, jewel in enumerate(jewels):
            target_row = segment_rows[idx]
            self.grid[target_row][col] = jewel
            if jewel.row != target_row:
                start_pos = (jewel.x, jewel.y)
                jewel.row = target_row
                jewel.col = col
                end_pos = self._cell_center(target_row, col)
                moves.append((jewel, start_pos, end_pos))
        for idx in range(len(jewels), len(segment_rows)):
            target_row = segment_rows[idx]
            jewel = self._create_jewel(target_row, col)
            self.grid[target_row][col] = jewel
            start_x, _ = self._cell_center(target_row, col)
            start_y = self.origin[1] - self.tile_size * (len(segment_rows) - idx) + self.tile_size / 2
            jewel.set_pixel_pos(start_x, start_y)
            end_pos = self._cell_center(target_row, col)
            moves.append((jewel, (jewel.x, jewel.y), end_pos))

    def find_matches(self):
        matches = []
        # horizontal
        for r in range(self.rows):
            run = [0]
            for c in range(1, self.cols):
                if self._same_color(r, c, r, c - 1):
                    run.append(c)
                else:
                    if len(run) >= 3:
                        positions = {(r, cc) for cc in run}
                        matches.append({"positions": positions, "orientation": "h"})
                    run = [c]
            if len(run) >= 3:
                positions = {(r, cc) for cc in run}
                matches.append({"positions": positions, "orientation": "h"})

        # vertical
        for c in range(self.cols):
            run = [0]
            for r in range(1, self.rows):
                if self._same_color(r, c, r - 1, c):
                    run.append(r)
                else:
                    if len(run) >= 3:
                        positions = {(rr, c) for rr in run}
                        matches.append({"positions": positions, "orientation": "v"})
                    run = [r]
            if len(run) >= 3:
                positions = {(rr, c) for rr in run}
                matches.append({"positions": positions, "orientation": "v"})

        return matches

    def _same_color(self, r1, c1, r2, c2):
        j1 = self.grid[r1][c1]
        j2 = self.grid[r2][c2]
        if j1 is None or j2 is None:
            return False
        return j1.color_id == j2.color_id

    def draw(self, surface):
        board_w = self.cols * self.tile_size
        board_h = self.rows * self.tile_size
        board_rect = pygame.Rect(self.origin[0], self.origin[1], board_w, board_h)
        board_surf = pygame.Surface(board_rect.size, pygame.SRCALPHA)
        board_surf.fill((255, 255, 255, 120))
        surface.blit(board_surf, board_rect.topleft)

        # grid
        for r in range(self.rows):
            for c in range(self.cols):
                cell_rect = pygame.Rect(
                    self.origin[0] + c * self.tile_size,
                    self.origin[1] + r * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                pygame.draw.rect(surface, (255, 255, 255, 40), cell_rect, 1)

        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.blocked:
                    cell_rect = pygame.Rect(
                        self.origin[0] + c * self.tile_size,
                        self.origin[1] + r * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                    pygame.draw.rect(surface, (60, 50, 55), cell_rect, border_radius=6)
                    pygame.draw.rect(surface, (25, 20, 22), cell_rect, 2, border_radius=6)
                    continue
                jewel = self.grid[r][c]
                if jewel:
                    jewel.draw(surface, self.colors)

        if self.selected:
            r, c = self.selected
            highlight = pygame.Rect(
                self.origin[0] + c * self.tile_size,
                self.origin[1] + r * self.tile_size,
                self.tile_size,
                self.tile_size,
            )
            pygame.draw.rect(surface, (255, 215, 120), highlight, 3, border_radius=4)

        for effect in self.effects:
            effect.draw(surface)

    def pop_events(self):
        events = list(self.events)
        self.events = []
        return events

    def _update_effects(self, dt):
        remaining = []
        for effect in self.effects:
            if not effect.update(dt):
                remaining.append(effect)
        self.effects = remaining
