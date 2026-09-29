import math
import pygame
from settings import (
    GRAVITY, MIN_SPEED, MAX_SPEED, JUMP_VELOCITY,
    GROUND_OFFSET, FLIP_SPEED, LAND_TOLERANCE,
    BOOST_DECAY, MAX_SPEED_BOOST,
    WALL_RIDE_SPEED, WALL_RIDE_DURATION,
    GRIND_SPEED,
    WINGSUIT_DURATION, WINGSUIT_SPEED_BOOST, WINGSUIT_FALL_SPEED,
)
import terrain


def _normalize_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _lerp_angle(a, b, t):
    d = _normalize_angle(b - a)
    return a + d * t


_BODY_POINTS = [
    (45, 10),
    (45, 26),
    (15, 45),
    (75, 45),
    (45, 45),
]


class Wingsuit:
    def __init__(self):
        self.reset()

    def reset(self):
        self.active = False
        self.timer = 0.0
        self.charges = 3

    def activate(self):
        if self.charges > 0 and not self.active:
            self.active = True
            self.timer = WINGSUIT_DURATION
            self.charges -= 1
            return True
        return False

    def update(self, dt):
        if self.active:
            self.timer -= dt
            if self.timer <= 0:
                self.active = False
                self.timer = 0.0


class Player:
    def __init__(self, x=0.0):
        self.wingsuit = Wingsuit()
        self.reset(x)

    def reset(self, x=0.0):
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
        self._down_prev = False

        self.trail = []
        self.trail_timer = 0.0
        self.events = []
        self.speed_boost = 0.0

        self.wall_riding = False
        self.wall_ride_timer = 0.0
        self.current_wall = None

        self.grinding = False
        self.grind_rail = None

        self.wingsuit.reset()

    # ---------- утилиты ----------
    def collision_points(self):
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        out = []
        for lx, ly in _BODY_POINTS:
            dx, dy = lx - 45, ly - 45
            rx = dx * ca - dy * sa
            ry = dx * sa + dy * ca
            out.append((self.x + rx, self.y + ry))
        return out

    def add_boost(self, amount):
        self.speed_boost = min(MAX_SPEED_BOOST, self.speed_boost + amount)
        cap = MAX_SPEED + self.speed_boost
        self.vx = min(cap, self.vx + amount * 0.6)

    def jump(self):
        if self.on_ground and not self.crashed:
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            self.air_time = 0.0
            self.rotation_accum = 0.0

    def try_activate_wingsuit(self):
        if (self.crashed or self.on_ground
                or self.grinding or self.wall_riding):
            return False
        return self.wingsuit.activate()

    def start_wall_ride(self, wall):
        self.wall_riding = True
        self.wall_ride_timer = WALL_RIDE_DURATION
        self.current_wall = wall
        self.on_ground = False
        self.vy = -WALL_RIDE_SPEED
        self.angular_velocity = 0.0
        self.events.append(("wall_ride_start",))

    def start_grind(self, rail):
        self.grinding = True
        self.grind_rail = rail
        self.on_ground = False
        self.vy = 0.0
        self.angular_velocity = 0.0
        self.rotation_accum = 0.0
        self.events.append(("grind_start",))

    # ---------- физика ----------
    def update(self, dt, keys):
        self.events.clear()

        space = keys[pygame.K_SPACE]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        space_pressed = space and not self._space_prev
        down_pressed = down and not self._down_prev

        # ---- CRASHED ----
        if self.crashed:
            self.vy += GRAVITY * dt
            self.x += self.vx * dt * 0.4
            self.y += self.vy * dt
            self.angle += self.angular_velocity * dt
            self.vx *= 0.97
            self.angular_velocity *= 0.99
            self._space_prev = space
            self._down_prev = down
            return

        # ---- WALL RIDE ----
        if self.wall_riding:
            self.wall_ride_timer -= dt
            self.y -= WALL_RIDE_SPEED * dt
            self.angle = -math.pi / 2 + math.pi  # ~вертикально

            wall = self.current_wall
            top_reached = wall is not None and self.y <= wall.y_top
            if self.wall_ride_timer <= 0 or top_reached:
                self.wall_riding = False
                self.current_wall = None
                self.vy = -300.0
                self.rotation_accum = 0.0
                self.events.append(("wall_ride_end",))

            self.wingsuit.update(dt)
            self._update_trail(dt)
            self._space_prev = space
            self._down_prev = down
            return

        # ---- GRIND ----
        if self.grinding and self.grind_rail:
            rail = self.grind_rail
            dx = rail.x2 - rail.x1
            dy = rail.y2 - rail.y1
            length = rail.length

            if rail.broken or length < 1:
                self.grinding = False
                self.grind_rail = None
                self.on_ground = False
                self.vy = 0.0
                self.events.append(("grind_end",))
            else:
                # Проекция игрока на трос
                t = ((self.x - rail.x1) * dx + (self.y - rail.y1) * dy) / (length * length)
                t = max(0.0, min(1.0, t))

                self.angle = math.atan2(dy, dx)
                self.vx = GRIND_SPEED * (dx / length)
                self.vy = GRIND_SPEED * (dy / length)
                self.x += self.vx * dt
                self.y += self.vy * dt

                # Проехали конец троса?
                if t >= 0.999:
                    self.grinding = False
                    self.grind_rail = None
                    self.on_ground = False
                    self.vy = -100.0
                    self.events.append(("grind_end",))

            self.wingsuit.update(dt)
            self._update_trail(dt)
            self._space_prev = space
            self._down_prev = down
            return

        # ---- NORMAL ----
        if self.on_ground and (space_pressed or down_pressed):
            self.jump()

        if self.speed_boost > 0.0:
            self.speed_boost = max(0.0, self.speed_boost - BOOST_DECAY * dt)

        if self.on_ground:
            slope = math.atan(terrain.slope(self.x))
            self.vx += math.sin(slope) * GRAVITY * 0.55 * dt
            self.vx *= max(0.0, 1.0 - 0.08 * dt)

            cap = MAX_SPEED + self.speed_boost
            self.vx = max(MIN_SPEED, min(cap, self.vx))

            self.x += self.vx * dt
            self.y = terrain.height(self.x) - GROUND_OFFSET
            self.angle = _lerp_angle(self.angle, slope, min(1.0, 14.0 * dt))

            ahead = terrain.height(self.x + self.vx * 0.05) - GROUND_OFFSET
            if ahead - self.y > 14.0:
                self.on_ground = False
                self.vy = 0.0
                self.air_time = 0.0
                self.rotation_accum = 0.0
        else:
            # В воздухе
            if self.wingsuit.active:
                self.vy = WINGSUIT_FALL_SPEED
                self.vx += WINGSUIT_SPEED_BOOST * dt
                cap = MAX_SPEED + self.speed_boost + WINGSUIT_SPEED_BOOST
                self.vx = min(cap, self.vx)
            else:
                self.vy += GRAVITY * dt

            self.x += self.vx * dt
            self.y += self.vy * dt
            self.air_time += dt

            if space:
                self.angular_velocity = -FLIP_SPEED
            elif down:
                self.angular_velocity = FLIP_SPEED
            else:
                self.angular_velocity *= max(0.0, 1.0 - 3.0 * dt)

            self.angle += self.angular_velocity * dt
            self.rotation_accum += self.angular_velocity * dt

            ground_y = terrain.height(self.x) - GROUND_OFFSET
            if self.y >= ground_y and self.vy >= 0:
                slope = math.atan(terrain.slope(self.x))
                diff = abs(_normalize_angle(self.angle - slope))

                turns = abs(self.rotation_accum) / (2 * math.pi)
                flips = int(turns + 0.4)
                direction = "back" if self.rotation_accum < 0 else "front"

                if diff > LAND_TOLERANCE:
                    # Крах — но очки за сальто начисляем
                    self.crashed = True
                    self.angular_velocity = 7.0
                    self.vy = -400.0
                    if flips > 0:
                        self.events.append(("land", flips, direction))
                    self.events.append(("crash",))
                    self._space_prev = space
                    self._down_prev = down
                    return

                # Успешное приземление
                self.y = ground_y
                self.vy = 0.0
                self.on_ground = True
                self.angular_velocity = 0.0
                self.angle = slope
                self.air_time = 0.0
                self.rotation_accum = 0.0
                self.wingsuit.active = False
                if flips > 0:
                    self.events.append(("land", flips, direction))

        self.wingsuit.update(dt)
        self._update_trail(dt)
        self._space_prev = space
        self._down_prev = down

    # ---------- след ----------
    def _update_trail(self, dt):
        if (self.on_ground or self.grinding or self.wall_riding) and self.vx > 60:
            self.trail_timer -= dt
            if self.trail_timer <= 0:
                self.trail_timer = 0.025
                self.trail.append([self.x, self.y + 6, 1.5])
        for p in self.trail:
            p[2] -= dt
        self.trail = [p for p in self.trail if p[2] > 0]

    # ---------- отрисовка ----------
    def draw_trail(self, screen, camera):
        if not self.trail:
            return
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for x, y, life in self.trail:
            f = max(0.0, life / 1.5)
            a = int(140 * f)
            r = max(1, int(3 * f + 1))
            pygame.draw.circle(surf, (210, 225, 250, a),
                               (int(x - camera.x), int(y - camera.y)), r)
        screen.blit(surf, (0, 0))

    def draw(self, screen, camera):
        surf = pygame.Surface((90, 90), pygame.SRCALPHA)

        if self.wingsuit.active:
            pygame.draw.polygon(surf, (80, 150, 220),
                                [(45, 26), (10, 45), (45, 45)])
            pygame.draw.polygon(surf, (80, 150, 220),
                                [(45, 26), (80, 45), (45, 45)])

        pygame.draw.ellipse(surf, (90, 55, 35), (10, 41, 70, 8))
        pygame.draw.circle(surf, (200, 70, 60), (45, 26), 13)
        pygame.draw.circle(surf, (245, 210, 180), (45, 10), 9)
        pygame.draw.arc(surf, (55, 45, 65),
                        (36, 2, 18, 14), 0.2, math.pi - 0.2, 5)

        rotated = pygame.transform.rotate(surf, -math.degrees(self.angle))
        rect = rotated.get_rect(center=(self.x - camera.x, self.y - camera.y))
        screen.blit(rotated, rect)
