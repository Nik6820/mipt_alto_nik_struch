import math
import sys
import pygame

from settings import WIDTH, HEIGHT, FPS
import terrain
import background
from player import Player
from particles import ParticleSystem


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self._init = False

    def update(self, tx, ty, dt):
        desired_x = tx - WIDTH * 0.35
        desired_y = ty - HEIGHT * 0.55
        if not self._init:
            self.x, self.y = desired_x, desired_y
            self._init = True
            return
        kx = 1.0 - math.exp(-8.0 * dt)
        ky = 1.0 - math.exp(-5.0 * dt)
        self.x += (desired_x - self.x) * kx
        self.y += (desired_y - self.y) * ky


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Alto-like (Python)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 32, bold=True)
        self.big = pygame.font.SysFont("Arial", 72, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(0.0)
        self.camera = Camera()
        self.particles = ParticleSystem()
        self.sky = background.Sky()
        self.distance = 0.0
        self.start_x = self.player.x
        self.state = "playing"
        self.time = 0.0
        self.spray_timer = 0.0

    # ---------- события ----------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if e.key == pygame.K_r and self.state == "gameover":
                    self.reset()

    # ---------- обновление ----------
    def update(self, dt, keys):
        self.player.update(dt, keys)

        if self.state == "playing":
            if self.player.crashed:
                self.state = "gameover"

            self.distance = max(self.distance, self.player.x - self.start_x)

            # снежный спрей
            if self.player.on_ground and self.player.vx > 200:
                self.spray_timer -= dt
                if self.spray_timer <= 0:
                    self.spray_timer = 0.02
                    gy = terrain.height(self.player.x) - 4
                    self.particles.emit_snow(self.player.x, gy, self.player.vx)

        self.particles.update(dt)
        self.camera.update(self.player.x, self.player.y, dt)
        self.time += dt

    # ---------- отрисовка ----------
    def draw(self):
        t = (self.time * 0.02) % 1.0
        self.sky.draw(self.screen, t)
        background.draw_mountains(self.screen, self.camera, t)
        terrain.draw(self.screen, self.camera)
        self.particles.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        # HUD
        score = self.font.render(f"{int(self.distance / 10)} m", True, (30, 30, 40))
        self.screen.blit(score, (30, 25))

        if self.state == "gameover":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            self.screen.blit(overlay, (0, 0))

            txt = self.big.render("CRASHED!", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))

            dist = self.font.render(
                f"Distance: {int(self.distance / 10)} m", True, (235, 235, 235)
            )
            self.screen.blit(dist, dist.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

            hint = self.font.render("Press R to restart", True, (220, 220, 220))
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))

    # ---------- главный цикл ----------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self.handle_events()
            keys = pygame.key.get_pressed()
            self.update(dt, keys)
            self.draw()
            pygame.display.flip()
