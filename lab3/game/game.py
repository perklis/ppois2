
import os
from datetime import datetime
from pathlib import Path
import pygame

from config_loader import load_json, resolve_path, save_json
from score import HighScoreTable
from game.board import Board
from ui.menu import Menu
from ui.help_screen import HelpScreen


class AudioManager:
    def __init__(self, settings, base_dir):
        self.settings = settings
        self.base_dir = base_dir
        self.sfx = {}
        self.music_sound = None
        self.music_path = resolve_path(base_dir, settings["assets"]["music"])
        self._init_sfx()

    def _init_sfx(self):
        import array
        sample_rate = 44100

        def tone(freq=440, duration=0.12, volume=0.4):
            n_samples = int(sample_rate * duration)
            buf = array.array("h")
            amplitude = int(32767 * volume)
            for i in range(n_samples):
                value = amplitude if (i * freq / sample_rate) % 1 < 0.5 else -amplitude
                buf.append(value)
            return pygame.mixer.Sound(buffer=buf.tobytes())

        sfx_paths = self.settings["assets"]["sfx"]
        for name, rel_path in sfx_paths.items():
            full_path = resolve_path(self.base_dir, rel_path)
            if os.path.exists(full_path):
                self.sfx[name] = pygame.mixer.Sound(full_path)
            else:
                self.sfx[name] = tone(520 + 40 * len(self.sfx))
            self.sfx[name].set_volume(self.settings["audio"]["sfx_volume"])

        # simple looping tone for music fallback
        self.music_sound = tone(220, duration=0.5, volume=0.2)
        self.music_sound.set_volume(self.settings["audio"]["music_volume"])

    def play_sfx(self, name):
        sound = self.sfx.get(name)
        if sound:
            sound.play()

    def play_music(self):
        if os.path.exists(self.music_path):
            try:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(self.settings["audio"]["music_volume"])
                pygame.mixer.music.play(-1)
                return
            except pygame.error:
                pass
        if self.music_sound:
            self.music_sound.play(-1)

    def stop_music(self):
        pygame.mixer.music.stop()
        if self.music_sound:
            self.music_sound.stop()


class Game:
    def __init__(self, screen, base_dir):
        self.screen = screen
        self.base_dir = Path(base_dir)
        self.settings = load_json(self.base_dir / "data" / "settings.json")
        self.levels_data = load_json(self.base_dir / "data" / "levels.json")
        self.highscores_time = HighScoreTable(self.base_dir / "data" / "highscores.json", "time")
        self.highscores_score = HighScoreTable(self.base_dir / "data" / "highscores.json", "score")
        self.base_title_size = 52
        self.base_ui_size = 30
        self.base_tiny_size = 22
        self.scale = 1.0
        self.font = pygame.font.SysFont(self.settings["fonts"]["title"], self.base_title_size)
        self.small_font = pygame.font.SysFont(self.settings["fonts"]["ui"], self.base_ui_size)
        self.tiny_font = pygame.font.SysFont(self.settings["fonts"]["ui"], self.base_tiny_size)

        self.menu_main = Menu(
            [
                ("Начать игру", "start"),
                ("Выбор уровня", "level_select"),
                ("Таблица рекордов", "scores"),
                ("Справка", "help"),
                ("Выход", "exit"),
            ],
            self.font,
            self.small_font,
            title="Jewel Quest",
        )
        self.menu_mode = Menu(
            [
                ("Режим: На время", "time"),
                ("Режим: На очки", "score"),
                ("Назад", "back"),
            ],
            self.font,
            self.small_font,
            title="Выбор режима",
        )
        self.menu_level = Menu(
            self._build_level_items(),
            self.font,
            self.small_font,
            title="Выбор уровня",
        )
        self.help_screen = HelpScreen(self.font, self.small_font)

        base_w = 960
        base_h = 720
        self.scale = min(
            self.settings["screen"]["width"] / base_w,
            self.settings["screen"]["height"] / base_h,
        )
        self._update_fonts()
        self.background = self._build_background()
        self.backgrounds = self._load_backgrounds()

        self.audio = AudioManager(self.settings, self.base_dir)
        self.audio.play_music()

        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"
        self.mode = None

        self.board = None
        self.time_left = 0
        self.total_score = 0
        self.level_score = 0
        self.level_index = 0
        self.level_complete_timer = 0.0

        self.confirm_exit = False
        self.progress_dirty = False
        self.endless_mode = False
        self.record_name = ""
        self.record_score = 0
        self.record_mode = None
        self.scores_scroll = 0

        self.player = load_json(self.base_dir / "data" / "player.json", default={"name": "", "confirmed": False})
        self.player_name = self.player.get("name", "")
        self.name_confirmed = False
        self.name_focus = False
        self.menu_warning = ""

        self.state_data = load_json(self.base_dir / "data" / "state.json", default={"score_mode": {}})

    def start_time_mode(self):
        self.mode = "time"
        self.state = "playing"
        self.total_score = 0
        self.level_score = 0
        self.level_index = 0
        self.time_left = self.settings["time_mode"]["time_limit"]
        self._clear_score_progress()
        level_conf = {
            "jewel_types": self.settings["time_mode"]["jewel_types"],
            "target_score": 0,
        }
        self.board = Board(self.settings, level_conf)

    def start_score_mode(self, level_index=0, use_saved=False):
        self.mode = "score"
        self.state = "playing"
        self.endless_mode = False
        if use_saved and self._has_saved_score_progress():
            saved = self.state_data.get("score_mode", {})
            self.total_score = int(saved.get("total_score", 0))
            self.level_score = int(saved.get("level_score", 0))
            self.level_index = int(saved.get("level_index", 0))
        else:
            self.total_score = 0
            self.level_score = 0
            self.level_index = level_index
            self._clear_score_progress()
        self._load_level()
        self._save_score_progress()

    def _load_level(self):
        if self.level_index < 0:
            self.level_index = 0
        if self.level_index >= len(self.levels_data["levels"]):
            self.level_index = max(0, len(self.levels_data["levels"]) - 1)
        level_conf = self.levels_data["levels"][self.level_index]
        self.level_score = 0
        self.board = Board(self.settings, level_conf)

    def run(self):
        while self.running:
            dt = self.clock.tick(self.settings["fps"]) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.VIDEORESIZE:
                self._on_resize(event.w, event.h)
                continue

            if self.state == "menu":
                action = self.menu_main.handle_event(event)
                if action:
                    self._handle_menu_action(action)
            elif self.state == "mode":
                action = self.menu_mode.handle_event(event)
                if action:
                    if action == "time":
                        self.start_time_mode()
                    elif action == "score":
                        self.start_score_mode(use_saved=True)
                    elif action == "back":
                        self.state = "menu"
            elif self.state == "level_select":
                action = self.menu_level.handle_event(event)
                if action is not None:
                    if action == "back":
                        self.state = "menu"
                    else:
                        self.start_score_mode(level_index=action, use_saved=False)
            elif self.state == "help":
                if self.help_screen.handle_event(event) == "back":
                    self.state = "menu"
            elif self.state == "scores":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                if event.type == pygame.MOUSEWHEEL:
                    self._scroll_scores(-event.y)
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self._scroll_scores(1)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._scroll_scores(-1)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._scores_exit_clicked(event.pos):
                        self.state = "menu"
            elif self.state == "playing":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "confirm_exit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._exit_button_rect().collidepoint(event.pos):
                        self.state = "confirm_exit"
                    else:
                        self.board.handle_click(event.pos)
            elif self.state == "confirm_exit":
                self._handle_confirm_exit(event)
            elif self.state == "post_levels":
                self._handle_post_levels(event)
            elif self.state == "record_input":
                self._handle_record_input(event)
            elif self.state == "game_over":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.state = "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._game_over_ok_clicked(event.pos):
                        self.state = "menu"

    def _handle_menu_action(self, action):
        if action == "start":
            self.menu_warning = ""
            self.state = "mode"
        elif action == "level_select":
            self.menu_warning = ""
            self.menu_level = Menu(
                self._build_level_items(),
                self.font,
                self.small_font,
                title="Выбор уровня",
            )
            self.state = "level_select"
        elif action == "scores":
            self.state = "scores"
        elif action == "help":
            self.state = "help"
        elif action == "exit":
            self.running = False

    def _update(self, dt):
        if self.state == "playing":
            self.board.update(dt)
            for event in self.board.pop_events():
                if event["type"] == "score":
                    self.total_score += event["value"]
                    self.level_score += event["value"]
                    self.audio.play_sfx("match")
                    self.progress_dirty = True
                elif event["type"] == "special":
                    self.audio.play_sfx("special")
                elif event["type"] == "swap_invalid":
                    self.audio.play_sfx("invalid")

            if self.mode == "time":
                self.time_left = max(0.0, self.time_left - dt)
                if self.time_left <= 0:
                    self._finish_game()
            elif self.mode == "score":
                if not self.endless_mode:
                    target = self.levels_data["levels"][self.level_index]["target_score"]
                    if (
                        self.level_score >= target
                        and self.level_complete_timer <= 0
                        and self.board.state == "idle"
                    ):
                        self.level_complete_timer = 1.5
                        self.state = "level_complete"
                # if surpassed top record, prompt immediately
                if self.state == "playing":
                    table = self.highscores_score
                    if table.is_new_record(self.total_score):
                        self.record_score = self.total_score
                        self.record_mode = "score"
                        self.record_name = ""
                        self.state = "record_input"
                if self.progress_dirty:
                    self._save_score_progress()
                    self.progress_dirty = False

        elif self.state == "level_complete":
            self.level_complete_timer -= dt
            if self.level_complete_timer <= 0:
                self.level_index += 1
                if self.level_index >= len(self.levels_data["levels"]):
                    self.state = "post_levels"
                else:
                    self.state = "playing"
                    self._load_level()
                    self._save_score_progress()

    def _finish_game(self):
        table = self.highscores_time if self.mode == "time" else self.highscores_score
        if table.is_new_record(self.total_score):
            self.record_score = self.total_score
            self.record_mode = self.mode
            self.record_name = ""
            self.state = "record_input"
        else:
            self._clear_score_progress()
            self.state = "game_over"

    def _abandon_game(self):
        self.board = None
        self.mode = None
        self.level_index = 0
        self.level_score = 0
        self.total_score = 0
        self.time_left = 0
        self.level_complete_timer = 0.0
        self._clear_score_progress()
        self.state = "menu"

    def _draw(self):
        screen_w = self.settings["screen"]["width"]
        screen_h = self.settings["screen"]["height"]

        if self.state == "menu":
            self._draw_background("menu")
            self._draw_menu_header()
            self.menu_main.draw(self.screen, screen_w, screen_h)
        elif self.state == "mode":
            self._draw_background("menu")
            self._draw_mode_header()
            self.menu_mode.draw(self.screen, screen_w, screen_h)
        elif self.state == "level_select":
            self._draw_background("menu")
            self.menu_level.draw(self.screen, screen_w, screen_h)
        elif self.state == "help":
            self._draw_background("help")
            self.help_screen.draw(self.screen, screen_w, screen_h)
        elif self.state == "scores":
            self._draw_background("scores")
            self._draw_scores()
        elif self.state in ("playing", "level_complete", "game_over", "confirm_exit", "record_input"):
            if self.mode == "time":
                self._draw_background("time")
            else:
                self._draw_background("score")
            if self.board:
                self.board.draw(self.screen)
            self._draw_hud()
            if self.state == "level_complete":
                self._draw_center_text("Уровень пройден!", 0)
            if self.state == "game_over":
                self._draw_game_over_dialog()
            if self.state == "confirm_exit":
                self._draw_confirm_dialog()
            if self.state == "record_input":
                self._draw_record_dialog()
        elif self.state == "post_levels":
            self._draw_background("score")
            if self.board:
                self.board.draw(self.screen)
            self._draw_hud()
            self._draw_post_levels_dialog()

        pygame.display.flip()

    def _draw_hud(self):
        info_y = int(16 * self.scale)
        left = int(14 * self.scale)

        if self.mode == "score":
            if 0 <= self.level_index < len(self.levels_data["levels"]):
                level_conf = self.levels_data["levels"][self.level_index]
                level_text = f"Уровень: {level_conf['id']}  Цель: {level_conf['target_score']}  Текущий: {self.level_score}"
            else:
                level_text = f"Уровень: финал  Текущий: {self.level_score}"

            score_surface = self.small_font.render(f"Очки: {self.total_score}", True, (50, 40, 35))
            level_surface = self.small_font.render(level_text, True, (50, 40, 35))
            padding_x = int(14 * self.scale)
            padding_y = int(10 * self.scale)
            line_gap = int(8 * self.scale)
            panel_w = max(score_surface.get_width(), level_surface.get_width()) + padding_x * 2
            panel_h = score_surface.get_height() + level_surface.get_height() + padding_y * 2 + line_gap
            panel = pygame.Rect(left, info_y, panel_w, panel_h)
            panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
            panel_surf.fill((255, 255, 255, 170))
            self.screen.blit(panel_surf, panel.topleft)
            self.screen.blit(score_surface, (panel.left + padding_x, panel.top + padding_y))
            self.screen.blit(level_surface, (panel.left + padding_x, panel.top + padding_y + score_surface.get_height() + line_gap))
        else:
            panel_w = int(230 * self.scale)
            panel_h = int(90 * self.scale)
            panel = pygame.Rect(left, info_y, panel_w, panel_h)
            panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
            panel_surf.fill((255, 255, 255, 170))
            self.screen.blit(panel_surf, panel.topleft)
            score_text = self.small_font.render(f"Очки: {self.total_score}", True, (50, 40, 35))
            self.screen.blit(score_text, (panel.left + int(12 * self.scale), panel.top + int(10 * self.scale)))
            time_text = self.small_font.render(f"Время: {int(self.time_left)}", True, (50, 40, 35))
            self.screen.blit(time_text, (panel.left + int(12 * self.scale), panel.top + int(46 * self.scale)))

        exit_rect = self._exit_button_rect()
        btn = pygame.Surface(exit_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn, (255, 255, 255, 160), btn.get_rect(), border_radius=12)
        self.screen.blit(btn, exit_rect.topleft)
        exit_text = self.tiny_font.render("Выход", True, (0, 0, 0))
        self.screen.blit(
            exit_text,
            (exit_rect.centerx - exit_text.get_width() // 2, exit_rect.centery - exit_text.get_height() // 2),
        )

    def _draw_scores(self):
        panel = pygame.Surface(
            (self.settings["screen"]["width"], self.settings["screen"]["height"]), pygame.SRCALPHA
        )
        panel.fill((14, 16, 22, 210))
        self.screen.blit(panel, (0, 0))
        y = int(80 * self.scale) - self.scores_scroll
        title = self.font.render("Таблица рекордов", True, (255, 255, 255))
        self.screen.blit(title, (self.settings["screen"]["width"] // 2 - title.get_width() // 2, y))
        y += int(70 * self.scale)
        section_gap = int(32 * self.scale)
        col_x = {
            "rank": int(150 * self.scale),
            "name": int(200 * self.scale),
            "score": int(440 * self.scale),
            "date": int(540 * self.scale),
        }

        def draw_table(title, entries):
            nonlocal y
            label = self.small_font.render(title, True, (255, 255, 255))
            self.screen.blit(label, (int(140 * self.scale), y))
            y += int(26 * self.scale)
            header = self.small_font.render("№", True, (255, 255, 255))
            self.screen.blit(header, (col_x["rank"], y))
            header = self.small_font.render("Имя", True, (255, 255, 255))
            self.screen.blit(header, (col_x["name"], y))
            header = self.small_font.render("Очки", True, (255, 255, 255))
            self.screen.blit(header, (col_x["score"], y))
            header = self.small_font.render("Дата/время", True, (255, 255, 255))
            self.screen.blit(header, (col_x["date"], y))
            y += int(28 * self.scale)
            if entries:
                for idx, entry in enumerate(entries[:10], start=1):
                    stamp = entry.get("timestamp", "--")
                    score = entry.get("score", 0)
                    name = entry.get("name", "Игрок")
                    row_rect = pygame.Rect(int(140 * self.scale), y - int(4 * self.scale), int(560 * self.scale), int(26 * self.scale))
                    if idx % 2 == 1:
                        row = pygame.Surface(row_rect.size, pygame.SRCALPHA)
                        row.fill((255, 255, 255, 70))
                        self.screen.blit(row, row_rect.topleft)
                    rank_text = self.small_font.render(f"{idx}.", True, (255, 255, 255))
                    name_text = self.small_font.render(name, True, (255, 255, 255))
                    score_text = self.small_font.render(str(score), True, (255, 255, 255))
                    date_text = self.small_font.render(stamp, True, (255, 255, 255))
                    self.screen.blit(rank_text, (col_x["rank"], y))
                    self.screen.blit(name_text, (col_x["name"], y))
                    self.screen.blit(score_text, (col_x["score"], y))
                    self.screen.blit(date_text, (col_x["date"], y))
                    y += int(28 * self.scale)
            else:
                empty = self.small_font.render("Пока нет рекордов.", True, (255, 255, 255))
                self.screen.blit(empty, (int(160 * self.scale), y))
                y += int(28 * self.scale)
            y += section_gap

        draw_table("Режим: На время", self.highscores_time.get_entries())
        draw_table("Режим: На очки", self.highscores_score.get_entries())

        btn_w = int(self.settings["screen"]["width"] * 0.22)
        btn_h = int(self.settings["screen"]["height"] * 0.07)
        self.scores_exit_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.scores_exit_rect.center = (self.settings["screen"]["width"] // 2, self.settings["screen"]["height"] - int(40 * self.scale))
        btn = pygame.Surface(self.scores_exit_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn, (255, 255, 255, 160), btn.get_rect(), border_radius=12)
        self.screen.blit(btn, self.scores_exit_rect.topleft)
        label = self.small_font.render("Выход", True, (0, 0, 0))
        self.screen.blit(
            label,
            (self.scores_exit_rect.centerx - label.get_width() // 2, self.scores_exit_rect.centery - label.get_height() // 2),
        )

    def _scores_exit_clicked(self, pos):
        return hasattr(self, "scores_exit_rect") and self.scores_exit_rect.collidepoint(pos)

    def _scroll_scores(self, direction):
        step = int(28 * self.scale)
        max_scroll = int(200 * self.scale)
        self.scores_scroll = max(0, min(self.scores_scroll + direction * step, max_scroll))

    def _draw_center_text(self, text, line):
        surface = self.small_font.render(text, True, (255, 230, 180))
        x = self.settings["screen"]["width"] // 2 - surface.get_width() // 2
        y = self.settings["screen"]["height"] // 2 + int(line * 40 * self.scale)
        self.screen.blit(surface, (x, y))

    def _build_background(self):
        width = self.settings["screen"]["width"]
        height = self.settings["screen"]["height"]
        bg = pygame.Surface((width, height))
        top = self.settings.get("background", {}).get("top", [10, 14, 26])
        bottom = self.settings.get("background", {}).get("bottom", [22, 30, 48])
        for y in range(height):
            t = y / max(1, height - 1)
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pygame.draw.line(bg, (r, g, b), (0, y), (width, y))

        stars = self.settings.get("background", {}).get("stars", 80)
        rng = pygame.math.Vector2(12, 7)
        for i in range(stars):
            x = int((i * 97 + rng.x * 13) % width)
            y = int((i * 53 + rng.y * 17) % height)
            color = (200, 210, 230) if i % 3 else (255, 240, 200)
            bg.set_at((x, y), color)
        return bg

    def _draw_background(self, key):
        image = self.backgrounds.get(key)
        if image:
            self.screen.blit(image, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))

    def _load_backgrounds(self):
        result = {}
        bg_cfg = self.settings.get("background_images", {})
        for key, rel_path in bg_cfg.items():
            full_path = resolve_path(self.base_dir, rel_path)
            if os.path.exists(full_path):
                image = pygame.image.load(full_path).convert()
                image = pygame.transform.scale(image, self.screen.get_size())
                result[key] = image
        return result

    def _exit_button_rect(self):
        width = int(110 * self.scale)
        height = int(36 * self.scale)
        x = self.settings["screen"]["width"] - width - 20
        y = int(20 * self.scale)
        return pygame.Rect(x, y, width, height)

    def _draw_confirm_dialog(self):
        screen_w = self.settings["screen"]["width"]
        screen_h = self.settings["screen"]["height"]
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        dialog = pygame.Rect(0, 0, int(460 * self.scale), int(220 * self.scale))
        dialog.center = (screen_w // 2, screen_h // 2)
        dialog_surf = pygame.Surface(dialog.size, pygame.SRCALPHA)
        dialog_surf.fill((255, 255, 255, 180))
        self.screen.blit(dialog_surf, dialog.topleft)

        title = self.small_font.render("Выйти из текущей игры?", True, (0, 0, 0))
        self.screen.blit(title, (dialog.centerx - title.get_width() // 2, dialog.top + 30))

        subtitle = self.tiny_font.render("Прогресс текущей игры не сохранится.", True, (0, 0, 0))
        self.screen.blit(subtitle, (dialog.centerx - subtitle.get_width() // 2, dialog.top + 70))

        yes_rect = pygame.Rect(dialog.left + int(70 * self.scale), dialog.bottom - int(70 * self.scale), int(120 * self.scale), int(40 * self.scale))
        no_rect = pygame.Rect(dialog.right - int(190 * self.scale), dialog.bottom - int(70 * self.scale), int(120 * self.scale), int(40 * self.scale))
        btn_yes = pygame.Surface(yes_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn_yes, (255, 255, 255, 160), btn_yes.get_rect(), border_radius=12)
        self.screen.blit(btn_yes, yes_rect.topleft)
        btn_no = pygame.Surface(no_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn_no, (255, 255, 255, 160), btn_no.get_rect(), border_radius=12)
        self.screen.blit(btn_no, no_rect.topleft)

        yes_text = self.tiny_font.render("Да", True, (0, 0, 0))
        no_text = self.tiny_font.render("Нет", True, (0, 0, 0))
        self.screen.blit(yes_text, (yes_rect.centerx - yes_text.get_width() // 2, yes_rect.centery - yes_text.get_height() // 2))
        self.screen.blit(no_text, (no_rect.centerx - no_text.get_width() // 2, no_rect.centery - no_text.get_height() // 2))

        self.confirm_yes_rect = yes_rect
        self.confirm_no_rect = no_rect

    def _handle_confirm_exit(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_y, pygame.K_RETURN):
                self._abandon_game()
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                self.state = "playing"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, "confirm_yes_rect") and self.confirm_yes_rect.collidepoint(event.pos):
                self._abandon_game()
            elif hasattr(self, "confirm_no_rect") and self.confirm_no_rect.collidepoint(event.pos):
                self.state = "playing"

    def _draw_post_levels_dialog(self):
        screen_w = self.settings["screen"]["width"]
        screen_h = self.settings["screen"]["height"]
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        dialog = pygame.Rect(0, 0, int(620 * self.scale), int(260 * self.scale))
        dialog.center = (screen_w // 2, screen_h // 2)
        dialog_surf = pygame.Surface(dialog.size, pygame.SRCALPHA)
        dialog_surf.fill((255, 255, 255, 180))
        self.screen.blit(dialog_surf, dialog.topleft)

        title = self.small_font.render("Вы прошли три уровня игры!", True, (0, 0, 0))
        self.screen.blit(title, (dialog.centerx - title.get_width() // 2, dialog.top + int(24 * self.scale)))
        subtitle = self.tiny_font.render("Нажмите Да, чтобы продолжить игру, или Нет — вернуться в меню.", True, (0, 0, 0))
        self.screen.blit(subtitle, (dialog.centerx - subtitle.get_width() // 2, dialog.top + int(70 * self.scale)))

        yes_rect = pygame.Rect(dialog.left + int(90 * self.scale), dialog.bottom - int(70 * self.scale), int(140 * self.scale), int(44 * self.scale))
        no_rect = pygame.Rect(dialog.right - int(230 * self.scale), dialog.bottom - int(70 * self.scale), int(140 * self.scale), int(44 * self.scale))
        btn_yes = pygame.Surface(yes_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn_yes, (255, 255, 255, 160), btn_yes.get_rect(), border_radius=12)
        self.screen.blit(btn_yes, yes_rect.topleft)
        btn_no = pygame.Surface(no_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn_no, (255, 255, 255, 160), btn_no.get_rect(), border_radius=12)
        self.screen.blit(btn_no, no_rect.topleft)

        yes_text = self.small_font.render("Да", True, (0, 0, 0))
        no_text = self.small_font.render("Нет", True, (0, 0, 0))
        self.screen.blit(yes_text, (yes_rect.centerx - yes_text.get_width() // 2, yes_rect.centery - yes_text.get_height() // 2))
        self.screen.blit(no_text, (no_rect.centerx - no_text.get_width() // 2, no_rect.centery - no_text.get_height() // 2))

        self.post_yes_rect = yes_rect
        self.post_no_rect = no_rect

    def _handle_post_levels(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_y, pygame.K_RETURN):
                self.endless_mode = True
                self.state = "playing"
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                self._finish_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, "post_yes_rect") and self.post_yes_rect.collidepoint(event.pos):
                self.endless_mode = True
                self.state = "playing"
            elif hasattr(self, "post_no_rect") and self.post_no_rect.collidepoint(event.pos):
                self._finish_game()

    def _draw_game_over_dialog(self):
        screen_w = self.settings["screen"]["width"]
        screen_h = self.settings["screen"]["height"]
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        dialog = pygame.Rect(0, 0, int(420 * self.scale), int(200 * self.scale))
        dialog.center = (screen_w // 2, screen_h // 2)
        dialog_surf = pygame.Surface(dialog.size, pygame.SRCALPHA)
        dialog_surf.fill((255, 255, 255, 180))
        self.screen.blit(dialog_surf, dialog.topleft)

        title = self.small_font.render("Игра окончена!", True, (0, 0, 0))
        self.screen.blit(title, (dialog.centerx - title.get_width() // 2, dialog.top + int(30 * self.scale)))

        ok_rect = pygame.Rect(0, 0, int(140 * self.scale), int(44 * self.scale))
        ok_rect.center = (dialog.centerx, dialog.bottom - int(44 * self.scale))
        btn = pygame.Surface(ok_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn, (255, 255, 255, 160), btn.get_rect(), border_radius=12)
        self.screen.blit(btn, ok_rect.topleft)
        ok_text = self.small_font.render("ОК", True, (0, 0, 0))
        self.screen.blit(ok_text, (ok_rect.centerx - ok_text.get_width() // 2, ok_rect.centery - ok_text.get_height() // 2))

        self.game_over_ok_rect = ok_rect

    def _game_over_ok_clicked(self, pos):
        return hasattr(self, "game_over_ok_rect") and self.game_over_ok_rect.collidepoint(pos)

    def _on_resize(self, width, height):
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.settings["screen"]["width"] = width
        self.settings["screen"]["height"] = height
        base_w = 960
        base_h = 720
        self.scale = min(width / base_w, height / base_h)
        self._update_fonts()
        self.background = self._build_background()
        self.backgrounds = self._load_backgrounds()
        if self.board:
            self.board.rescale(width, height)

    def _update_fonts(self):
        title_size = max(32, int(self.base_title_size * self.scale))
        ui_size = max(20, int(self.base_ui_size * self.scale))
        tiny_size = max(16, int(self.base_tiny_size * self.scale))
        self.font = pygame.font.SysFont(self.settings["fonts"]["title"], title_size)
        self.small_font = pygame.font.SysFont(self.settings["fonts"]["ui"], ui_size)
        self.tiny_font = pygame.font.SysFont(self.settings["fonts"]["ui"], tiny_size)
        self.menu_main.font = self.font
        self.menu_main.small_font = self.small_font
        self.menu_mode.font = self.font
        self.menu_mode.small_font = self.small_font
        self.menu_level.font = self.font
        self.menu_level.small_font = self.small_font
        self.help_screen.font = self.font
        self.help_screen.small_font = self.small_font

    def _draw_menu_header(self):
        if self.menu_warning:
            screen_w = self.settings["screen"]["width"]
            warn = self.tiny_font.render(self.menu_warning, True, (0, 0, 0))
            self.screen.blit(warn, (screen_w // 2 - warn.get_width() // 2, int(60 * self.scale)))

    def _draw_mode_header(self):
        screen_w = self.settings["screen"]["width"]
        text = self.small_font.render("Выбор режима", True, (0, 0, 0))
        pad_x = int(18 * self.scale)
        pad_y = int(10 * self.scale)
        rect = pygame.Rect(0, 0, text.get_width() + pad_x * 2, text.get_height() + pad_y * 2)
        rect.center = (screen_w // 2, int(140 * self.scale))
        box = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(box, (255, 255, 255, 255), box.get_rect(), border_radius=12)
        self.screen.blit(box, rect.topleft)
        self.screen.blit(text, (rect.left + pad_x, rect.top + pad_y))

    def _draw_record_dialog(self):
        screen_w = self.settings["screen"]["width"]
        screen_h = self.settings["screen"]["height"]
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        dialog = pygame.Rect(0, 0, int(560 * self.scale), int(280 * self.scale))
        dialog.center = (screen_w // 2, screen_h // 2)
        dialog_surf = pygame.Surface(dialog.size, pygame.SRCALPHA)
        dialog_surf.fill((255, 255, 255, 180))
        self.screen.blit(dialog_surf, dialog.topleft)

        title = self.font.render("Новый мировой рекорд!", True, (0, 0, 0))
        self.screen.blit(title, (dialog.centerx - title.get_width() // 2, dialog.top + int(18 * self.scale)))
        score_line = self.small_font.render(f"Счёт: {self.record_score}", True, (0, 0, 0))
        self.screen.blit(score_line, (dialog.centerx - score_line.get_width() // 2, dialog.top + int(70 * self.scale)))

        input_rect = pygame.Rect(0, 0, int(380 * self.scale), int(70 * self.scale))
        input_rect.center = (dialog.centerx, dialog.centery)

        input_surf = pygame.Surface(input_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(input_surf, (255, 255, 255, 160), input_surf.get_rect(), border_radius=12)
        self.screen.blit(input_surf, input_rect.topleft)
        label = self.tiny_font.render("Введите имя:", True, (0, 0, 0))
        self.screen.blit(label, (input_rect.left + int(12 * self.scale), input_rect.top + int(6 * self.scale)))
        name_text = self.small_font.render(self.record_name or " ", True, (0, 0, 0))
        self.screen.blit(name_text, (input_rect.left + int(12 * self.scale), input_rect.top + int(28 * self.scale)))

        save_rect = pygame.Rect(0, 0, int(180 * self.scale), int(44 * self.scale))
        save_rect.center = (dialog.centerx, dialog.bottom - int(44 * self.scale))
        save_surf = pygame.Surface(save_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(save_surf, (255, 255, 255, 160), save_surf.get_rect(), border_radius=12)
        self.screen.blit(save_surf, save_rect.topleft)
        save_label = self.small_font.render("Сохранить", True, (0, 0, 0))
        self.screen.blit(
            save_label,
            (save_rect.centerx - save_label.get_width() // 2, save_rect.centery - save_label.get_height() // 2),
        )

        hint = self.tiny_font.render("Введите имя и нажмите Сохранить", True, (0, 0, 0))
        self.screen.blit(hint, (dialog.centerx - hint.get_width() // 2, dialog.bottom - int(90 * self.scale)))

        self.record_input_rect = input_rect
        self.record_save_rect = save_rect

    def _handle_record_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, "record_input_rect") and self.record_input_rect.collidepoint(event.pos):
                self.name_focus = True
            elif hasattr(self, "record_save_rect") and self.record_save_rect.collidepoint(event.pos):
                self._commit_record()
            else:
                self.name_focus = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._commit_record()
            elif event.key == pygame.K_BACKSPACE:
                self.record_name = self.record_name[:-1]
            else:
                if len(self.record_name) < 14 and event.unicode.isprintable():
                    self.record_name += event.unicode

    def _commit_record(self):
        if not self.record_name.strip():
            return
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        table = self.highscores_time if self.record_mode == "time" else self.highscores_score
        table.add(self.record_name.strip(), self.record_score, stamp)
        self._clear_score_progress()
        self.state = "game_over"

    def _build_level_items(self):
        items = []
        for idx, level in enumerate(self.levels_data["levels"]):
            items.append((f"{level['id']}. {level['name']}", idx))
        items.append(("Назад", "back"))
        return items

    def _has_saved_score_progress(self):
        saved = self.state_data.get("score_mode", {})
        return bool(saved.get("active", False))

    def _save_score_progress(self):
        self.state_data["score_mode"] = {
            "active": True,
            "level_index": self.level_index,
            "total_score": self.total_score,
            "level_score": self.level_score,
        }
        save_json(self.base_dir / "data" / "state.json", self.state_data)

    def _clear_score_progress(self):
        self.state_data["score_mode"] = {"active": False, "level_index": 0, "total_score": 0, "level_score": 0}
        save_json(self.base_dir / "data" / "state.json", self.state_data)
