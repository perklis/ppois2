import pygame


class HelpScreen:
    """Displays game rules and controls."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.exit_rect = None
        self.lines = [
            "Добро пожаловать в Jewel Quest!",
            "Небольшое напоминание правил перед стартом:",
            "- Меняйте местами два соседних кубика.",
            "- Соберите 3+ одинаковых кубика по горизонтали или вертикали.",
            "- Комбинации исчезают, кубики падают, возможны каскады.",
            "- Спец-кубики: бомба (3x3), линия (строка/колонка), цветной (все одного цвета).",
            "",
            "Управление очень простое:",
            "- ЛКМ: выбрать и поменять кубики.",
            "- ESC: вернуться в меню.",
            "",
            "Удачной игры и высоких рекордов!"
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.exit_rect and self.exit_rect.collidepoint(event.pos):
                return "back"
        return None

    def draw(self, surface, screen_w, screen_h):
        panel = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        panel.fill((16, 20, 28, 210))
        surface.blit(panel, (0, 0))
        title = self.font.render("Справка", True, (255, 255, 255))
        surface.blit(title, (screen_w // 2 - title.get_width() // 2, int(screen_h * 0.12)))
        y = int(screen_h * 0.24)
        for line in self.lines:
            text = self.small_font.render(line, True, (255, 255, 255))
            surface.blit(text, (int(screen_w * 0.08), y))
            y += int(screen_h * 0.045)

        btn_w = int(screen_w * 0.22)
        btn_h = int(screen_h * 0.07)
        self.exit_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.exit_rect.center = (screen_w // 2, int(screen_h * 0.88))
        btn = pygame.Surface(self.exit_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(btn, (255, 255, 255, 160), btn.get_rect(), border_radius=12)
        surface.blit(btn, self.exit_rect.topleft)
        label = self.small_font.render("Выход", True, (0, 0, 0))
        surface.blit(
            label,
            (self.exit_rect.centerx - label.get_width() // 2, self.exit_rect.centery - label.get_height() // 2),
        )
