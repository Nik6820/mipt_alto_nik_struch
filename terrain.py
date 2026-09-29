import math
import pygame
from settings import WIDTH, HEIGHT


# Положительный → трасса уходит ВНИЗ с ростом x
GLOBAL_SLOPE = 0.06


def height(x: float) -> float:
    trend = GLOBAL_SLOPE * x
    waves = (
        math.sin(x * 0.00030 + 0.4) * 70.0 +
        math.sin(x * 0.00150 + 1.1) * 35.0 +
        math.sin(x * 0.00400 + 3.7) * 20.0 +
        math.sin(x * 0.00900 + 0.9) * 8.0 +
        math.sin(x * 0.01800 + 2.3) * 4.0 +
        math.sin(x * 0.03500 + 4.5) * 1.5
    )
    return 420.0 + trend + waves


def slope(x: float) -> float:
    return (
        GLOBAL_SLOPE +
        math.cos(x * 0.00030 + 0.4) * 70.0 * 0.00030 +
        math.cos(x * 0.00150 + 1.1) * 35.0 * 0.00150 +
        math.cos(x * 0.00400 + 3.7) * 20.0 * 0.00400 +
        math.cos(x * 0.00900 + 0.9) * 8.0 * 0.00900 +
        math.cos(x * 0.01800 + 2.3) * 4.0 * 0.01800 +
        math.cos(x * 0.03500 + 4.5) * 1.5 * 0.03500
    )


BIOME_COLORS = {
    "dunes":   ((247, 250, 255), (185, 205, 235)),
    "canyons": ((255, 225, 190), (200, 145, 100)),
    "temples": ((215, 240, 215), (110, 165, 110)),
}


def draw(screen: pygame.Surface, camera, biome: str = "dunes") -> None:
    step = 8
    start_x = int(camera.x) - step
    end_x = int(camera.x) + WIDTH + step

    points = []
    for sx in range(start_x, end_x + step, step):
        wy = height(sx) - camera.y
        points.append((sx - camera.x, wy))

    fill, line = BIOME_COLORS.get(biome, BIOME_COLORS["dunes"])
    poly = points + [(points[-1][0], HEIGHT), (points[0][0], HEIGHT)]
    pygame.draw.polygon(screen, fill, poly)
    pygame.draw.lines(screen, line, False, points, 2)
