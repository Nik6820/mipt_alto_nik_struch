import math
import random
import sys
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, MAX_SPEED,
    COIN_VALUE, TRICK_FLIP_BONUS, MAX_COMBO_MULT,
    BOOST_PER_FLIP, MAX_SPEED_BOOST,
    BIOME_DUNES_END, BIOME_CANYONS_END,
    BALLOON_BOUNCE_VELOCITY,
)
import terrain
import background
from player import Player
from particles import ParticleSystem, FloatingText
from pickups import CoinField
from scenery import Scenery
from leaderboard import Leaderboard
from mechanics import Wall, GrindRail, Balloon


MAX_LEADERBOARD_ROWS = 10


def _trick_name(flips, direction):
    word = "BACKFLIP" if direction == "back" else "FRONTFLIP"
    if flips == 1:
        return word + "!"
    if flips == 2:
        return "DOUBLE " + word + "!"
    if flips == 3:
        return "TRIPLE " + word + "!"
    return f"{flips}x " + word + "!"


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
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.small = pygame.font.SysFont("Arial", 22)
        self.big = pygame.font.SysFont("Arial", 72, bold=True)
        self.trick_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.tiny = pygame.font.SysFont("Arial", 18)
        self.leaderboard = Leaderboard()
        self.reset()

    def reset(self):
        self.player = Player(0.0)
        self.camera = Camera()
        self.particles = ParticleSystem()
        self.coins = CoinField()
        self.scenery = Scenery()
        self.sky = background.Sky()

        self.start_x = self.player.x
        self.distance = 0.0
        self.coins_count = 0
        self.tricks_score = 0
        self.combo = 0
        self.state = "playing"
        self.time = 0.0
        self.spray_timer = 0.0
        self.floats: list[FloatingText] = []

        self.player_name = ""
        self.saved_entry = None
        self.saved_rank = -1
        self.blink = 0.0

        # Новые механики
        self.walls: list[Wall] = []
        self.rails: list[GrindRail] = []
        self.balloons: list[Balloon] = []
        self.next_wall_x = 1200.0
        self.next_rail_x = 900.0
        self.next_balloon_x = 1400.0
        self.biome = "dunes"

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

                if self.state == "enter_name":
                    if e.key == pygame.K_RETURN:
                        entry = self.leaderboard.add(
                            self.player_name,
                            self._total_score(),
                            int(self.distance / 10),
                            self.coins_count,
                        )
                        self.saved_entry = entry
                        self.saved_rank = self.leaderboard.rank_of(entry)
                        self.state = "gameover"
                    elif e.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    else:
                        ch = e.unicode
                        if ch and ch.isprintable() and len(self.player_name) < 14:
                            self.player_name += ch
                    continue

                if self.state == "playing" and e.key == pygame.K_w:
                    if self.player.try_activate_wingsuit():
                        self.particles.emit_burst(
                            self.player.x, self.player.y,
                            (100, 200, 255), count=20, speed=220,
                        )

                if e.key == pygame.K_r and self.state == "gameover":
                    self.reset()

    # ---------- логика ----------
    def update(self, dt, keys):
        if self.state == "playing":
            self.player.update(dt, keys)
            self.coins.update(self.player.x)
            self.scenery.update(self.player.x)

            self.distance = max(self.distance, self.player.x - self.start_x)

            # --- Спавн механик впереди ---
            self._spawn_mechanics()

            # --- Обновление тросов ---
            for rail in self.rails:
                rail.update(dt)
                if (not self.player.on_ground
                        and not self.player.grinding
                        and not self.player.wall_riding
                        and not self.player.crashed
                        and rail.can_attach(self.player.x, self.player.y)):
                    self.player.start_grind(rail)

            # --- Обновление шаров ---
            for b in self.balloons:
                b.update(dt, self.time)
                if (not self.player.crashed
                        and b.check_bounce(self.player.x, self.player.y, self.player.vy)):
                    self.player.vy = BALLOON_BOUNCE_VELOCITY
                    self.player.on_ground = False
                    self.player.wingsuit.active = False
                    self.particles.emit_burst(
                        b.x, b.y, (255, 120, 120), count=18, speed=260,
                    )
                    self.floats.append(FloatingText(
                        "BOUNCE!", b.x, b.y - 60,
                        color=(255, 180, 180),
                    ))

            # --- Wall ride триггер ---
            if (not self.player.on_ground
                    and not self.player.grinding
                    and not self.player.wall_riding
                    and not self.player.crashed):
                for w in self.walls:
                    if w.can_ride(self.player.x, self.player.y):
                        self.player.start_wall_ride(w)
                        break

            # --- Обработка событий игрока ---
            for ev in self.player.events:
                if ev[0] == "land":
                    _, flips, direction = ev
                    mult = min(self.combo + flips, MAX_COMBO_MULT)
                    gained = flips * TRICK_FLIP_BONUS * max(1, mult)
                    self.tricks_score += gained
                    self.combo += flips

                    self.player.add_boost(flips * BOOST_PER_FLIP)

                    self.floats.append(FloatingText(
                        _trick_name(flips, direction),
                        self.player.x, self.player.y - 80,
                        color=(255, 235, 140),
                    ))
                    self.particles.emit_burst(
                        self.player.x, self.player.y,
                        (255, 240, 150), count=12, speed=220,
                    )
                elif ev[0] == "crash":
                    total = self._total_score()
                    if self.leaderboard.qualifies(total):
                        self.player_name = ""
                        self.state = "enter_name"
                    else:
                        self.state = "gameover"
                elif ev[0] == "wall_ride_start":
                    self.floats.append(FloatingText(
                        "WALL RIDE!", self.player.x, self.player.y - 70,
                        color=(200, 220, 255),
                    ))
                elif ev[0] == "grind_start":
                    self.floats.append(FloatingText(
                        "GRIND!", self.player.x, self.player.y - 70,
                        color=(220, 255, 200),
                    ))

            # --- Сбор монет ---
            if not self.player.crashed:
                pts = self.player.collision_points()
                earned, positions = self.coins.collect(pts)
                if earned:
                    self.coins_count += earned // COIN_VALUE
                    for (cx, cy) in positions:
                        self.particles.emit_burst(
                            cx, cy, (255, 215, 80), count=6, speed=160,
                        )

            # --- Снежный спрей под доской ---
            if self.player.on_ground and self.player.vx > 200:
                self.spray_timer -= dt
                if self.spray_timer <= 0:
                    self.spray_timer = 0.02
                    gy = terrain.height(self.player.x) - 4
                    self.particles.emit_snow(self.player.x, gy, self.player.vx)

            # --- Смена биома ---
            dist_m = self.distance / 10
            if dist_m > BIOME_CANYONS_END:
                self.biome = "temples"
            elif dist_m > BIOME_DUNES_END:
                self.biome = "canyons"
            else:
                self.biome = "dunes"

            # --- Очистка ушедших объектов ---
            self.walls = [w for w in self.walls if w.x > self.player.x - 800]
            self.rails = [r for r in self.rails if r.x2 > self.player.x - 800]
            self.balloons = [b for b in self.balloons
                             if b.x > self.player.x - 800]

        self.particles.update(dt)
        self.camera.update(self.player.x, self.player.y, dt)
        self.floats = [f for f in self.floats if f.update(dt)]
        self.time += dt
        self.blink += dt

    # ---------- генерация механик ----------
    def _spawn_mechanics(self):
        px = self.player.x

        while self.next_wall_x < px + 2400:
            gy = terrain.height(self.next_wall_x)
            self.walls.append(Wall(self.next_wall_x, gy, height=random.randint(180, 260)))
            self.next_wall_x += random.uniform(1400, 2400)

        while self.next_rail_x < px + 2400:
            x1 = self.next_rail_x
            x2 = x1 + random.uniform(300, 500)
            y1 = terrain.height(x1) - random.uniform(180, 260)
            y2 = y1 + random.uniform(40, 90)
            self.rails.append(GrindRail(x1, y1, x2, y2))
            self.next_rail_x += random.uniform(1200, 2200)

        while self.next_balloon_x < px + 2600:
            gy = terrain.height(self.next_balloon_x)
            y = gy - random.uniform(320, 420)
            self.balloons.append(Balloon(self.next_balloon_x, y))
            self.next_balloon_x += random.uniform(1400, 2400)

    # ---------- отрисовка ----------
    def _total_score(self):
        return (int(self.distance / 10)
                + self.coins_count * COIN_VALUE
                + self.tricks_score)

    def draw(self):
        t = (self.time * 0.02) % 1.0
        self.sky.draw(self.screen, t)
        background.draw_mountains(self.screen, self.camera, t)

        # Скалы за рельефом (их верхняя часть видна)
        for w in self.walls:
            w.draw(self.screen, self.camera, self.biome)

        self.scenery.draw(self.screen, self.camera, self.time)
        terrain.draw(self.screen, self.camera, self.biome)

        # Тросы и шары — над рельефом, под игроком
        for r in self.rails:
            r.draw(self.screen, self.camera)
        for b in self.balloons:
            b.draw(self.screen, self.camera)

        self.player.draw_trail(self.screen, self.camera)
        self.coins.draw(self.screen, self.camera, self.time)
        self.particles.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        for f in self.floats:
            f.draw(self.screen, self.camera, self.trick_font)

        self._draw_hud()

        if self.state == "gameover":
            self._draw_gameover()
        elif self.state == "enter_name":
            self._draw_name_input()

    def _draw_hud(self):
        dist = self.font.render(
            f"{int(self.distance / 10)} m", True, (30, 30, 40))
        self.screen.blit(dist, (30, 25))

        coin_txt = self.font.render(
            f"★ {self.coins_count}", True, (200, 140, 20))
        self.screen.blit(coin_txt, (30, 65))

        trick_txt = self.font.render(
            f"Tricks: {self.tricks_score}", True, (90, 40, 140))
        self.screen.blit(trick_txt, (WIDTH - 260, 25))

        if self.combo >= 2:
            mult = min(self.combo, MAX_COMBO_MULT)
            combo_txt = self.font.render(
                f"x{mult} COMBO", True, (220, 60, 60))
            self.screen.blit(combo_txt, (WIDTH - 220, 65))

        # Биом
        biome_names = {"dunes": "Dunes", "canyons": "Canyons", "temples": "Temples"}
        biome_txt = self.small.render(
            biome_names.get(self.biome, ""), True, (80, 80, 100))
        self.screen.blit(biome_txt, (WIDTH - 260, 105))

        # Wingsuit charges
        ws = self.player.wingsuit
        if ws.charges > 0 or ws.active:
            color = (100, 220, 255) if ws.active else (150, 180, 200)
            ws_txt = self.small.render(
                f"WINGSUIT: {ws.charges}", True, color)
            self.screen.blit(ws_txt, (30, 105))

        # Индикатор буста
        if self.player.speed_boost > 1.0:
            f = self.player.speed_boost / MAX_SPEED_BOOST
            bar_w = 220
            x = WIDTH - 260
            y = HEIGHT - 40
            pygame.draw.rect(self.screen, (40, 40, 50),
                             (x, y, bar_w, 12), border_radius=6)
            pygame.draw.rect(self.screen, (255, 180, 40),
                             (x, y, int(bar_w * f), 12), border_radius=6)
            label = self.small.render("BOOST", True, (255, 220, 140))
            self.screen.blit(label, (x, y - 22))

    def _draw_name_input(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.big.render("NEW HIGH SCORE!", True, (255, 230, 120))
        self.screen.blit(title, title.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 160)))

        score = self.font.render(
            f"Total: {self._total_score()}", True, (240, 240, 240))
        self.screen.blit(score, score.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 90)))

        label = self.small.render("Enter your name:", True, (200, 200, 200))
        self.screen.blit(label, label.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 30)))

        box_w, box_h = 380, 56
        box = pygame.Rect(0, 0, box_w, box_h)
        box.center = (WIDTH // 2, HEIGHT // 2 + 30)

        pygame.draw.rect(self.screen, (30, 30, 45), box, border_radius=8)
        pygame.draw.rect(self.screen, (120, 160, 220), box, 2, border_radius=8)

        shown = self.player_name
        if self.blink % 1.0 < 0.55:
            shown += "|"
        txt = self.font.render(shown or " ", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=box.center))

        hint = self.small.render(
            "Press Enter to save   ·   Backspace to delete",
            True, (180, 180, 180))
        self.screen.blit(hint, hint.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 + 110)))

    def _draw_gameover(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.big.render("CRASHED!", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(
            center=(WIDTH // 2, 80)))

        left_x = 120
        y = 200
        self.screen.blit(self.font.render("RESULTS", True, (255, 220, 120)),
                         (left_x, y))
        y += 46

        lines = [
            f"Distance : {int(self.distance / 10)} m",
            f"Coins    : {self.coins_count}  (+{self.coins_count * COIN_VALUE})",
            f"Tricks   : {self.tricks_score}",
        ]
        for line in lines:
            self.screen.blit(self.font.render(line, True, (230, 230, 230)),
                             (left_x, y))
            y += 36

        y += 8
        total = self._total_score()
        self.screen.blit(self.font.render(
            f"TOTAL    : {total}", True, (255, 220, 120)), (left_x, y))
        y += 56

        if self.saved_rank > 0:
            rank_txt = self.font.render(
                f"You are #{self.saved_rank}!", True, (120, 220, 120))
            self.screen.blit(rank_txt, (left_x, y))
            y += 40

        hint = self.small.render(
            "Press R to restart   ·   Esc to quit", True, (200, 200, 200))
        self.screen.blit(hint, (left_x, y + 20))

        right_x = WIDTH // 2 + 60
        y = 200
        self.screen.blit(self.font.render("LEADERBOARD", True, (140, 200, 255)),
                         (right_x, y))
        y += 46

        header = self.tiny.render(
            f"{'#':<3}{'NAME':<16}{'SCORE':>8}", True, (160, 160, 180))
        self.screen.blit(header, (right_x, y))
        y += 26

        if not self.leaderboard.entries:
            self.screen.blit(
                self.small.render("- no records yet -", True, (150, 150, 160)),
                (right_x, y))
        else:
            for i, e in enumerate(self.leaderboard.entries[:MAX_LEADERBOARD_ROWS]):
                is_new = (e is self.saved_entry)
                color = (255, 220, 120) if is_new else (220, 220, 220)
                row = f"{i + 1:<3}{e['name']:<16}{e['score']:>8}"
                surf = self.tiny.render(row, True, color)
                self.screen.blit(surf, (right_x, y))
                y += 24

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


if __name__ == "__main__":
    Game().run()
