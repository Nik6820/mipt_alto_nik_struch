import math
import random
import pygame
from settings import COIN_RADIUS, COIN_VALUE
import terrain


class Coin:
    __slots__ = ("x", "y", "collected", "anim")

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.anim = random.uniform(0, math.tau)


class CoinField:
    def __init__(self):
        self.coins: list[Coin] = []
        self.next_x = 600.0

    def update(self, player_x: float) -> None:
        while self.next_x < player_x + 2200:
            gap = random.uniform(320, 720)
            base = self.next_x

            if random.random() < 0.45:
                arc_h = random.uniform(140, 240)
                n = 5
                for i in range(n):
                    cx = base + i * 48
                    t = (i - (n - 1) / 2) / ((n - 1) / 2)
                    cy = terrain.height(cx) - 50 - arc_h * (1 - t * t)
                    self.coins.append(Coin(cx, cy))
                self.next_x = base + n * 48 + gap
            else:
                n = random.randint(3, 6)
                for i in range(n):
                    cx = base + i * 50
                    cy = terrain.height(cx) - 48
                    self.coins.append(Coin(cx, cy))
                self.next_x = base + n * 50 + gap

        self.coins = [c for c in self.coins
                      if not c.collected and c.x > player_x - 400]

    def collect(self, points):
        """points — список (x, y) точек тела игрока в мировых координатах."""
        earned = 0
        hit_positions = []
        r2 = (COIN_RADIUS + 8) ** 2
        for c in self.coins:
            if c.collected:
                continue
            for (px, py) in points:
                dx, dy = c.x - px, c.y - py
                if dx * dx + dy * dy < r2:
                    c.collected = True
                    earned += COIN_VALUE
                    hit_positions.append((c.x, c.y))
                    break
        return earned, hit_positions

    def draw(self, screen, camera, t):
        for c in self.coins:
            phase = (t * 4.0 + c.anim) % math.tau
            w = abs(math.cos(phase)) * COIN_RADIUS + 3
            cx, cy = int(c.x - camera.x), int(c.y - camera.y)
            rect = pygame.Rect(0, 0, int(w * 2), COIN_RADIUS * 2)
            rect.center = (cx, cy)
            pygame.draw.ellipse(screen, (255, 200, 50), rect)
            pygame.draw.ellipse(screen, (255, 240, 150), rect, 2)
