import math
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity


class FloatingText:
    __slots__ = ("text", "x", "y", "life", "max_life", "color")

    def __init__(self, text, x, y, color=(255, 240, 180), life=1.5):
        self.text = text
        self.x, self.y = x, y
        self.color = color
        self.life = self.max_life = life

    def update(self, dt):
        self.y -= 45 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, screen, camera, font):
        f = max(0.0, self.life / self.max_life)
        alpha = int(255 * min(1.0, f * 2.0))
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(self.x - camera.x,
                                     self.y - camera.y))
        screen.blit(surf, rect)


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def emit_snow(self, x, y, vx):
        for _ in range(random.randint(1, 3)):
            self.particles.append(Particle(
                x + random.uniform(-5, 5),
                y + random.uniform(-3, 3),
                -vx * random.uniform(0.05, 0.20) + random.uniform(-30, 30),
                random.uniform(-90, -20),
                random.uniform(0.25, 0.6),
                (255, 255, 255),
                random.uniform(1.5, 3.5),
                gravity=450.0,
            ))

    def emit_burst(self, x, y, color, count=8, speed=180.0):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            s = random.uniform(speed * 0.4, speed)
            self.particles.append(Particle(
                x, y,
                math.cos(a) * s,
                math.sin(a) * s,
                random.uniform(0.3, 0.6),
                color,
                random.uniform(2, 4),
                gravity=300.0,
            ))

    def update(self, dt):
        for p in self.particles:
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, screen, camera):
        for p in self.particles:
            size = max(1, int(p.size))
            pos = (int(p.x - camera.x), int(p.y - camera.y))
            pygame.draw.circle(screen, p.color, pos, size)
