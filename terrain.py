import math
import pygame
from settings import WIDTH, HEIGHT


def height(x: float) -> float:
    """Высота рельефа в мировых координатах."""
    return 420.0 + (
        math.sin(x * 0.0016) * 130.0 +
        math.sin(x * 0.0037 + 1.7) * 55.0 +
        math.sin(x * 0.0081 + 3.1) * 22.0 +
        math.sin(x * 0.0170 + 0.5) * 8.0
    )


def slope(x: float) -> float:
    """Производная высоты (тангенс угла наклона)."""
    return (
        math.cos(x * 0.0016) * 130.0 * 0.0016 +
        math.cos(x * 0.0037 + 1.7) * 55.0 * 0.0037 +
        math.cos(x * 0.0081 + 3.1) * 22.0 * 0.0081 +
        math.cos(x * 0.0170 + 0.5) * 8.0 * 0.0170
    )


def draw(screen: pygame.Surface, camera) -> None:
    step = 8
    start_x = int(camera.x) - step
    end_x = int(camera.x) + WIDTH + step

    points = []
    for sx in range(start_x, end_x + step, step):
        wy = height(sx) - camera.y
        points.append((sx - camera.x, wy))

    poly = points + [(points[-1][0], HEIGHT), (points[0][0], HEIGHT)]
    pygame.draw.polygon(screen, (247, 250, 255), poly)
    pygame.draw.lines(screen, (185, 205, 235), False, points, 2)
