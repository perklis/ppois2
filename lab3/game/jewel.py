import pygame


class Jewel:
    """Single jewel on the board."""

    def __init__(self, color_id, row, col, tile_size, special=None):
        self.color_id = color_id
        self.row = row
        self.col = col
        self.tile_size = tile_size
        self.special = special  # None, "bomb", "line_h", "line_v", "color"
        self.scale = 1.0
        self.x = 0
        self.y = 0

    def set_pixel_pos(self, x, y):
        self.x = x
        self.y = y

    def draw(self, surface, colors):
        size = int(self.tile_size * 0.78 * self.scale)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.x), int(self.y))
        base_color = colors[self.color_id]
        pygame.draw.rect(surface, base_color, rect, border_radius=max(4, size // 6))
        # subtle highlight
        highlight = (min(base_color[0] + 40, 255), min(base_color[1] + 40, 255), min(base_color[2] + 40, 255))
        pygame.draw.rect(surface, highlight, rect.inflate(-size // 3, -size // 3), border_radius=max(4, size // 6))

        if self.special:
            self._draw_special(surface, rect)

    def _draw_special(self, surface, rect):
        if self.special == "bomb":
            pygame.draw.circle(surface, (40, 40, 40), rect.center, rect.width // 3)
            pygame.draw.circle(surface, (200, 50, 50), rect.center, rect.width // 6)
        elif self.special == "line_h":
            pygame.draw.rect(surface, (240, 240, 240), (rect.left, rect.centery - 3, rect.width, 6))
        elif self.special == "line_v":
            pygame.draw.rect(surface, (240, 240, 240), (rect.centerx - 3, rect.top, 6, rect.height))
        elif self.special == "color":
            pygame.draw.circle(surface, (255, 255, 255), rect.center, rect.width // 3, 2)
            pygame.draw.circle(surface, (255, 215, 0), rect.center, rect.width // 5)
