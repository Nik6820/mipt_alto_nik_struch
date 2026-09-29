import math
import random
import pygame
from settings import (
    BALLOON_RADIUS, GRIND_BREAK_CHANCE,
    WALL_RIDE_DURATION,
)


class Wall:
    """Вертикальная скала — игрок может проехать по ней вверх."""
    def __init__(self, x, y_bottom, height=220):
        self.x = x
        self.y_bottom = y_bottom
        self.y_top = y_bottom - height

    def can_ride(self, px, py):
        return (abs(px - self.x) < 50
                and self.y_top - 20 < py < self.y_bottom + 20)

    def draw(self, screen, camera, biome="dunes"):
        x = int(self.x - camera.x)
        y_top = int(self.y_top - camera.y)
        y_bot = int(self.y_bottom - camera.y)
        palette = {
            "dunes":   ((180, 170, 160), (120, 110, 100)),
            "canyons": ((190, 130, 90),  (140, 80, 50)),
            "temples": ((140, 150, 120), (90, 100, 70)),
        }
        body, outline = palette.get(biome, palette["dunes"])
        pygame.draw.rect(screen, body, (x - 18, y_top, 36, y_bot - y_top))
        pygame.draw.rect(screen, outline, (x - 18, y_top, 36, y_bot - y_top), 2)
        for i in range(4):
            yy = y_top + (y_bot - y_top) * (i + 1) / 5
            pygame.draw.line(screen, outline, (x - 18, yy), (x + 18, yy), 1)


class GrindRail:
    """Трос для скольжения. Может оборваться в случайный момент."""
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.broken = False
        self.break_timer = 0.0
        self.length = max(1.0, math.hypot(x2 - x1, y2 - y1))

    def can_attach(self, px, py, radius=45):
        if self.broken:
            return False
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        t = ((px - self.x1) * dx + (py - self.y1) * dy) / (self.length ** 2)
        t = max(0, min(1, t))
        proj_x = self.x1 + t * dx
        proj_y = self.y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y) < radius

    def update(self, dt):
        if not self.broken and random.random() < GRIND_BREAK_CHANCE * dt:
            self.broken = True
            self.break_timer = 0.6
        if self.broken and self.break_timer > 0:
            self.break_timer -= dt

    def draw(self, screen, camera):
        if self.broken and self.break_timer <= 0:
            return
        color = (150, 60, 50) if self.broken else (70, 60, 50)
        width = 1 if self.broken and self.break_timer > 0 else 3
        pygame.draw.line(screen, color,
                         (self.x1 - camera.x, self.y1 - camera.y),
                         (self.x2 - camera.x, self.y2 - camera.y), width)


class Balloon:
    """Шар — при касании подбрасывает игрока вверх."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = BALLOON_RADIUS
        self.bob_phase = random.uniform(0, math.tau)
        self.popped = False

    def update(self, dt, t):
        if not self.popped:
            self._bob = math.sin(t * 2 + self.bob_phase) * 6
        else:
            self._bob = 0

    def check_bounce(self, px, py, pvy):
        if self.popped:
            return False
        dist = math.hypot(px - self.x, py - (self.y + getattr(self, "_bob", 0)))
        if dist < self.radius + 20 and pvy > 0:
            self.popped = True
            return True
        return False

    def draw(self, screen, camera):
        if self.popped:
            return
        bob = getattr(self, "_bob", 0)
        x = int(self.x - camera.x)
        y = int(self.y + bob - camera.y)
        pygame.draw.circle(screen, (220, 70, 70), (x, y), self.radius)
        pygame.draw.circle(screen, (255, 140, 140),
                           (x - 12, y - 12), self.radius // 3)
        pygame.draw.line(screen, (120, 100, 80),
                         (x, y + self.radius),
                         (x, y + self.radius + 30), 2)
