import math
import pygame
from settings import WIDTH, HEIGHT


def _make_gradient(top, bottom):
    h = 64
    surf = pygame.Surface((1, h))
    for y in range(h):
        f = y / (h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3))
        surf.set_at((0, y), c)
    return pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))


class Sky:
    KEYFRAMES = [
        (0.00, (110, 180, 240), (250, 220, 190)),
        (0.25, (90, 150, 220), (255, 200, 160)),
        (0.40, (255, 130, 90), (255, 200, 130)),
        (0.50, (60, 50, 110), (240, 110, 90)),
        (0.65, (12, 18, 50), (35, 40, 80)),
        (0.85, (40, 35, 90), (200, 100, 110)),
        (1.00, (110, 180, 240), (250, 220, 190)),
    ]

    def __init__(self):
        self._surf = None
        self._key = None

    def _colors(self, t):
        kf = self.KEYFRAMES
        for i in range(len(kf) - 1):
            t0, top0, bot0 = kf[i]
            t1, top1, bot1 = kf[i + 1]
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                top = tuple(int(a + (b - a) * f) for a, b in zip(top0, top1))
                bot = tuple(int(a + (b - a) * f) for a, b in zip(bot0, bot1))
                return top, bot
        return kf[0][1], kf[0][2]

    def draw(self, screen, t):
        key = int(t * 128)
        if key != self._key:
            self._key = key
            top, bot = self._colors(t)
            self._surf = _make_gradient(top, bot)
        screen.blit(self._surf, (0, 0))


def draw_mountains(screen, camera, t):
    layers = [
        (0.15, -60, 130, 0.0009, (185, 205, 235), 0.0),
        (0.30, -10, 110, 0.0013, (145, 175, 215), 1.7),
        (0.50,  50,  90, 0.0020, (100, 135, 185), 3.3),
    ]
    for par, base_off, amp, freq, color, seed in layers:
        pts = []
        for sx in range(-20, WIDTH + 30, 10):
            wx = sx + camera.x * par
            y = (HEIGHT * 0.50 + base_off
                 + math.sin(wx * freq + seed) * amp
                 + math.sin(wx * freq * 2.7 + seed * 1.9) * amp * 0.45)
            y -= camera.y * par * 0.6
            pts.append((sx, y))
        pts.append((WIDTH + 30, HEIGHT))
        pts.append((-20, HEIGHT))
        pygame.draw.polygon(screen, color, pts)
