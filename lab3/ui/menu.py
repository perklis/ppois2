import pygame

class Menu:
    
    def __init__(self, items, font, small_font=None, title=None):
        self.items = items
        self.font = font
        self.small_font = small_font or font
        self.title = title
        self.selected = 0
        self.screen_width = 800
        self.item_rects = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.items[self.selected][1]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._item_at_pos(event.pos)
            if idx is not None:
                self.selected = idx
                return self.items[idx][1]
        elif event.type == pygame.MOUSEMOTION:
            idx = self._item_at_pos(event.pos)
            if idx is not None:
                self.selected = idx
        return None

    def _item_at_pos(self, pos):
        x, y = pos
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(x, y):
                return i
        return None

    def draw(self, surface, screen_w, screen_h):
        self.screen_width = screen_w

        self.item_rects = []
        start_y = int(screen_h * 0.55)
        line_h = max(46, int(screen_h * 0.08))
        btn_w = min(420, int(screen_w * 0.5))
        btn_h = 44
        for i, (label, _) in enumerate(self.items):
            rect = pygame.Rect(0, 0, btn_w, btn_h)
            rect.center = (screen_w // 2, start_y + i * line_h)
            self.item_rects.append(rect)
            is_sel = i == self.selected
            fill = (255, 255, 255, 255)
            btn = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(btn, fill, btn.get_rect(), border_radius=12)
            surface.blit(btn, rect.topleft)
            text_surf = self.small_font.render(label, True, (0, 0, 0))
            surface.blit(
                text_surf,
                (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2),
            )
