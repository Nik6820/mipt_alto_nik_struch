import math
import pygame
from settings import (
    GRAVITY, MIN_SPEED, MAX_SPEED, JUMP_VELOCITY,
    GROUND_OFFSET, FLIP_SPEED, LAND_TOLERANCE,
)
import terrain


def _normalize_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _lerp_angle(a, b, t):
    d = _normalize_angle(b - a)
    return a + d * t


class Player:
    def __init__(self, x=0.0):
        self.x = x
        self.y = terrain.height(x) - GROUND_OFFSET
        self.vx = 250.0
        self.vy = 0.0
        self.on_ground = True
        self.angle = math.atan(terrain.slope(x))
        self.angular_velocity = 0.0
        self.air_time = 0.0
        self.rotation_accum = 0.0
        self.crashed = False
        self._space_prev = False

    # ---------- управление ----------
    def jump(self):
        if self.on_ground and not self.crashed:
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            self.air_time = 0.0
            self.rotation_accum = 0.0

    # ---------- физика ----------
    def update(self, dt, keys):
        space = keys[pygame.K_SPACE]
        space_pressed = space and not self._space_prev

        if self.crashed:
            self.vy += GRAVITY * dt
            self.x += self.vx * dt * 0.4
            self.y += self.vy * dt
            self.angle += self.angular_velocity * dt
            self.vx *= 0.97
            self.angular_velocity *= 0.99
            self._space_prev = space
            return

        if self.on_ground and space_pressed:
            self.jump()

        if self.on_ground:
            slope = math.atan(terrain.slope(self.x))

            # ускорение под уклон
            self.vx += -math.sin(slope) * GRAVITY * 0.55 * dt
            # трение
            self.vx *= max(0.0, 1.0 - 0.08 * dt)
            self.vx = max(MIN_SPEED, min(MAX_SPEED, self.vx))

            self.x += self.vx * dt
            self.y = terrain.height(self.x) - GROUND_OFFSET
            self.angle = _lerp_angle(self.angle, slope, min(1.0, 14.0 * dt))

            # авто-отрыв на крутом спуске
            ahead = terrain.height(self.x + self.vx * 0.05) - GROUND_OFFSET
            if ahead - self.y > 14.0:
                self.on_ground = False
                self.vy = 0.0
                self.air_time = 0.0
                self.rotation_accum = 0.0

        else:
            self.vy += GRAVITY * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.air_time += dt

            if space:
                self.angular_velocity = -FLIP_SPEED
            else:
                self.angular_velocity *= max(0.0, 1.0 - 3.0 * dt)

            self.angle += self.angular_velocity * dt
            self.rotation_accum += self.angular_velocity * dt

            ground_y = terrain.height(self.x) - GROUND_OFFSET
            if self.y >= ground_y and self.vy >= 0:
                slope = math.atan(terrain.slope(self.x))
                diff = abs(_normalize_angle(self.angle - slope))
                if diff > LAND_TOLERANCE:
                    self.crashed = True
                    self.angular_velocity = 7.0
                    self.vy = -400.0
                    self._space_prev = space
                    return

                self.y = ground_y
                self.vy = 0.0
                self.on_ground = True
                self.angular_velocity = 0.0
                self.angle = slope
                self.air_time = 0.0
                self.rotation_accum = 0.0

        self._space_prev = space

    # ---------- отрисовка ----------
    def draw(self, screen, camera):
        surf = pygame.Surface((90, 90), pygame.SRCALPHA)

        # доска (центр в 45,45)
        pygame.draw.ellipse(surf, (90, 55, 35), (10, 41, 70, 8))
        # тело
        pygame.draw.circle(surf, (200, 70, 60), (45, 26), 13)
        # голова
        pygame.draw.circle(surf, (245, 210, 180), (45, 10), 9)
        # шапка/волосы
        pygame.draw.arc(surf, (55, 45, 65), (36, 2, 18, 14), 0.2, math.pi - 0.2, 5)

        rotated = pygame.transform.rotate(surf, -math.degrees(self.angle))
        rect = rotated.get_rect(center=(self.x - camera.x, self.y - camera.y))
        screen.blit(rotated, rect)
