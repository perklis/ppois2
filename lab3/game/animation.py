import pygame


class Animation:
    def __init__(self, duration, on_complete=None):
        self.duration = max(duration, 0.001)
        self.elapsed = 0.0
        self.on_complete = on_complete

    def update(self, dt):
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)
        self.apply(t)
        done = self.elapsed >= self.duration
        if done and self.on_complete:
            self.on_complete()
        return done

    def apply(self, t):
        raise NotImplementedError


class MoveAnimation(Animation):
    def __init__(self, jewel, start_pos, end_pos, duration, on_complete=None):
        super().__init__(duration, on_complete)
        self.jewel = jewel
        self.start_pos = start_pos
        self.end_pos = end_pos

    def apply(self, t):
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        self.jewel.set_pixel_pos(x, y)


class ScaleAnimation(Animation):
    def __init__(self, jewel, start_scale, end_scale, duration, on_complete=None):
        super().__init__(duration, on_complete)
        self.jewel = jewel
        self.start_scale = start_scale
        self.end_scale = end_scale

    def apply(self, t):
        self.jewel.scale = self.start_scale + (self.end_scale - self.start_scale) * t


class AnimationManager:
    def __init__(self):
        self.animations = []

    def add(self, animation):
        self.animations.append(animation)

    def update(self, dt):
        remaining = []
        for anim in self.animations:
            if not anim.update(dt):
                remaining.append(anim)
        self.animations = remaining

    def is_busy(self):
        return len(self.animations) > 0

    def clear(self):
        self.animations = []


class ExplosionEffect:
    """Simple radial explosion effect."""

    def __init__(self, center, duration=0.35, max_radius=42):
        self.center = center
        self.duration = max(duration, 0.05)
        self.elapsed = 0.0
        self.max_radius = max_radius

    def update(self, dt):
        self.elapsed += dt
        return self.elapsed >= self.duration

    def draw(self, surface):
        t = min(self.elapsed / self.duration, 1.0)
        radius = int(self.max_radius * (0.4 + 0.6 * t))
        alpha = int(200 * (1.0 - t))
        if alpha <= 0 or radius <= 0:
            return
        ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            ring,
            (255, 200, 80, alpha),
            (ring.get_width() // 2, ring.get_height() // 2),
            radius,
            width=4,
        )
        surface.blit(ring, (self.center[0] - ring.get_width() // 2, self.center[1] - ring.get_height() // 2))
