import math
import random
import pygame
import terrain


# ---------- конкретные постройки ----------

def _draw_pine(surf, cx, base_y, s, seed, t):
    trunk_w = 6 * s
    trunk_h = 18 * s
    pygame.draw.rect(surf, (75, 50, 35),
                     (cx - trunk_w / 2, base_y - trunk_h, trunk_w, trunk_h))

    layers = [(36, 45, 0), (30, 38, 26), (22, 32, 50)]
    for i, (w, h, dy) in enumerate(layers):
        bot_y = base_y - trunk_h - dy * s
        top_y = bot_y - h * s
        color = (35, 75, 55) if i % 2 == 0 else (48, 92, 68)
        pygame.draw.polygon(surf, color, [
            (cx - w * s / 2, bot_y),
            (cx + w * s / 2, bot_y),
            (cx, top_y),
        ])
        # снежная шапка
        pygame.draw.polygon(surf, (240, 245, 255), [
            (cx - w * s * 0.30, bot_y - h * s * 0.15),
            (cx + w * s * 0.30, bot_y - h * s * 0.15),
            (cx, top_y),
        ])


def _draw_cabin(surf, cx, base_y, s, seed, t):
    w, h, roof_h = 60 * s, 40 * s, 20 * s
    pygame.draw.rect(surf, (125, 90, 60),
                     (cx - w / 2, base_y - h, w, h))
    pygame.draw.polygon(surf, (75, 45, 45), [
        (cx - w / 2 - 6 * s, base_y - h),
        (cx + w / 2 + 6 * s, base_y - h),
        (cx, base_y - h - roof_h),
    ])
    # окно
    pygame.draw.rect(surf, (245, 225, 150),
                     (cx - 8 * s, base_y - h * 0.75, 16 * s, 14 * s))
    # дверь
    pygame.draw.rect(surf, (55, 35, 25),
                     (cx - 5 * s, base_y - 18 * s, 10 * s, 18 * s))


def _draw_windmill(surf, cx, base_y, s, seed, t):
    body_h = 70 * s
    body_w = 26 * s
    # корпус
    pygame.draw.polygon(surf, (175, 155, 135), [
        (cx - body_w, base_y),
        (cx + body_w, base_y),
        (cx + body_w * 0.6, base_y - body_h),
        (cx - body_w * 0.6, base_y - body_h),
    ])
    pygame.draw.polygon(surf, (90, 75, 65), [
        (cx - body_w, base_y),
        (cx + body_w, base_y),
        (cx + body_w * 0.6, base_y - body_h),
        (cx - body_w * 0.6, base_y - body_h),
    ], 2)
    # крыша
    pygame.draw.polygon(surf, (80, 50, 45), [
        (cx - body_w * 0.75, base_y - body_h),
        (cx + body_w * 0.75, base_y - body_h),
        (cx, base_y - body_h - 14 * s),
    ])
    # лопасти — вращаются
    hub_y = base_y - body_h - 5 * s
    for i in range(4):
        a = t * 1.5 + i * math.pi / 2
        bx = math.cos(a) * 38 * s
        by = math.sin(a) * 38 * s
        pygame.draw.line(surf, (220, 220, 230),
                         (cx, hub_y), (cx + bx, hub_y + by),
                         max(2, int(4 * s)))
    pygame.draw.circle(surf, (50, 50, 60),
                       (int(cx), int(hub_y)), max(3, int(5 * s)))


def _draw_tower(surf, cx, base_y, s, seed, t):
    w, h = 22 * s, 80 * s
    pygame.draw.rect(surf, (150, 145, 140),
                     (cx - w / 2, base_y - h, w, h))
    pygame.draw.rect(surf, (120, 115, 110),
                     (cx - w / 2, base_y - h, w, h), 2)
    # зубцы сверху
    for i in range(3):
        pygame.draw.rect(surf, (130, 125, 120),
                         (cx - w / 2 + i * (w / 2.5), base_y - h - 6 * s,
                          w / 5, 6 * s))
    # окно
    pygame.draw.circle(surf, (60, 60, 80),
                       (int(cx), int(base_y - h * 0.7)), int(4 * s))


def _draw_arch(surf, cx, base_y, s, seed, t):
    w, h, thick = 50 * s, 35 * s, 10 * s
    color = (145, 135, 125)
    dark = (105, 95, 90)
    # столбы
    pygame.draw.rect(surf, color, (cx - w / 2, base_y - h, thick, h))
    pygame.draw.rect(surf, color, (cx + w / 2 - thick, base_y - h, thick, h))
    # верхняя перекладина
    pygame.draw.rect(surf, color, (cx - w / 2, base_y - h - thick, w, thick))
    # обводка
    pygame.draw.rect(surf, dark, (cx - w / 2, base_y - h - thick, w, thick), 2)


def _draw_rock(surf, cx, base_y, s, seed, t):
    pygame.draw.polygon(surf, (135, 140, 150), [
        (cx - 18 * s, base_y),
        (cx - 12 * s, base_y - 14 * s),
        (cx + 4 * s, base_y - 16 * s),
        (cx + 16 * s, base_y - 6 * s),
        (cx + 18 * s, base_y),
    ])
    pygame.draw.polygon(surf, (185, 195, 210), [
        (cx - 10 * s, base_y - 14 * s),
        (cx + 2 * s, base_y - 16 * s),
        (cx - 2 * s, base_y - 10 * s),
    ])


DRAWERS = {
    "pine": _draw_pine,
    "cabin": _draw_cabin,
    "windmill": _draw_windmill,
    "tower": _draw_tower,
    "arch": _draw_arch,
    "rock": _draw_rock,
}


class Scenery:
    """Процедурно расставляет постройки вдоль рельефа."""

    WEIGHTS = {
        "pine": 6,
        "rock": 3,
        "cabin": 3,
        "windmill": 2,
        "tower": 2,
        "arch": 2,
    }

    def __init__(self):
        self.items = []
        self.next_x = 900.0

    def update(self, player_x: float) -> None:
        kinds = list(self.WEIGHTS.keys())
        weights = list(self.WEIGHTS.values())

        while self.next_x < player_x + 2400:
            gap = random.uniform(300, 700)
            kind = random.choices(kinds, weights=weights)[0]
            self.items.append({
                "x": self.next_x + random.uniform(-40, 40),
                "kind": kind,
                "seed": random.uniform(0, 1000),
                "scale": random.uniform(0.8, 1.25),
            })
            self.next_x += gap

        self.items = [it for it in self.items
                      if it["x"] > player_x - 600]

    def draw(self, screen, camera, t):
        for it in self.items:
            wx = it["x"]
            sx = wx - camera.x
            if sx < -200 or sx > screen.get_width() + 200:
                continue
            sy = terrain.height(wx) - camera.y
            DRAWERS[it["kind"]](screen, sx, sy,
                                it["scale"], it["seed"], t)
