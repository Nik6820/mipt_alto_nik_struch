import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity


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
