
import os
import sys
import traceback

# Install the crash hook before importing or initializing pygame.
def show_crash(exc_type, exc_value, exc_tb):
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        base_dir = os.environ.get("ANDROID_PRIVATE") or os.path.expanduser("~")
        os.makedirs(base_dir, exist_ok=True)
        with open(os.path.join(base_dir, "galaxy_crash.txt"), "w", encoding="utf-8") as log_file:
            log_file.write(details)
            log_file.flush()
    except Exception:
        pass

    # If SDL/Pygame is usable, keep an error screen open for the user.
    try:
        import pygame
        if not pygame.get_init():
            pygame.init()
        info = pygame.display.Info()
        width = max(480, info.current_w or 480)
        height = max(320, info.current_h or 760)
        error_screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("GALAXY DEFENDER - STARTUP ERROR")
        error_font = pygame.font.Font(None, 22)
        title_font = pygame.font.Font(None, 30)
        lines = details.strip().splitlines()
        active = True
        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    active = False
            error_screen.fill((18, 5, 15))
            error_screen.blit(title_font.render("STARTUP ERROR - PLEASE SEND SCREENSHOT", True, (255, 100, 100)), (10, 10))
            y = 52
            for line in lines[-24:]:
                for offset in range(0, max(1, len(line)), 48):
                    error_screen.blit(error_font.render(line[offset:offset+48], True, (255, 235, 235)), (10, y))
                    y += 22
                    if y > height - 10:
                        break
                if y > height - 10:
                    break
            pygame.display.flip()
            pygame.time.wait(150)
        pygame.quit()
    except Exception:
        # Native SDL failures may prevent an on-screen Python traceback.
        pass

sys.excepthook = show_crash

import pygame
import random
import math
import array

pygame.init()

# Audio is optional on Android.
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO = True
except Exception:
    AUDIO = False

pygame.display.set_caption("GALAXY DEFENDER 3.3")
display_info = pygame.display.Info()
display_w = max(1, display_info.current_w or 480)
display_h = max(1, display_info.current_h or 854)
display_surface = pygame.display.set_mode((display_w, display_h), pygame.FULLSCREEN)
display_w, display_h = display_surface.get_size()

# Keep the game's original 480x760 coordinate system so every button,
# collision, and gameplay position remains consistent. Stretch only the
# final frame to the real portrait display to eliminate unused screen areas.
W, H = 480, 760
screen = pygame.Surface((W, H)).convert()
clock = pygame.time.Clock()

BLACK = (3, 5, 22)
WHITE = (245, 250, 255)
CYAN = (30, 230, 255)
BLUE = (55, 105, 255)
PURPLE = (175, 65, 255)
RED = (255, 65, 85)
ORANGE = (255, 170, 50)
GREEN = (80, 255, 150)
YELLOW = (255, 230, 80)

SECTOR_NAMES = ["ORION", "NEBULA", "VOID", "NOVA", "OMEGA"]
BOSS_NAMES = ["ORION WARDEN", "NEBULA TITAN", "VOID REAPER", "NOVA COLOSSUS", "OMEGA CORE"]
BOSS_PALETTES = [
    (PURPLE, RED, ORANGE),
    (BLUE, CYAN, WHITE),
    ((90, 35, 150), (190, 55, 255), (80, 20, 120)),
    ((180, 65, 25), (255, 100, 35), YELLOW),
    ((35, 65, 125), (70, 180, 255), WHITE),
]
SECTOR_NEBULA_PALETTES = [
    [(35, 10, 80), (8, 35, 85), (65, 12, 60)],
    [(5, 55, 75), (10, 30, 100), (30, 70, 90)],
    [(45, 8, 65), (20, 10, 95), (75, 15, 45)],
    [(75, 25, 8), (90, 35, 10), (55, 15, 60)],
    [(8, 45, 95), (25, 20, 85), (60, 10, 80)],
]

font = pygame.font.Font(None, 27)
small = pygame.font.Font(None, 21)
big = pygame.font.Font(None, 51)

SAVE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "galaxy_highscore.txt"
)

def load_best():
    try:
        with open(SAVE_FILE, "r") as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return 0

best_score = load_best()

def save_best():
    try:
        with open(SAVE_FILE, "w") as f:
            f.write(str(best_score))
    except OSError:
        pass

# -------- Procedural sound effects --------

def make_tone(start_freq, duration, volume=0.25, slide=0):
    if not AUDIO:
        return None
    try:
        rate = 22050
        count = int(rate * duration)
        samples = array.array("h")
        for i in range(count):
            t = i / rate
            freq = start_freq + slide * t
            envelope = max(0, 1 - i / count)
            value = int(
                32767 * volume * envelope *
                math.sin(2 * math.pi * freq * t)
            )
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())
    except (pygame.error, ValueError):
        return None

laser_sound = make_tone(1000, 0.07, 0.16, -450)
hit_sound = make_tone(350, 0.16, 0.25, -220)
power_sound = make_tone(450, 0.35, 0.22, 1400)
boss_sound = make_tone(180, 0.45, 0.25, -100)
gameover_sound = make_tone(450, 0.6, 0.2, -350)

sound_on = True

def play_sound(sound):
    if sound_on and sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass

# -------- Animated galaxy --------

stars = []
for _ in range(125):
    stars.append([
        random.randrange(W), random.randrange(H),
        random.choice([1, 1, 2, 3]),
        random.uniform(0.8, 3.5),
        random.random() * 6.28
    ])

nebulae = []
for _ in range(9):
    nebulae.append((
        random.randrange(W),
        random.randrange(H),
        random.randint(45, 105),
        random.choice([
            (35, 10, 80), (8, 35, 85),
            (65, 12, 60), (10, 55, 70)
        ])
    ))

def draw_background():
    screen.fill(BLACK)

    # Sector-specific nebula colors make each stage visually distinct.
    sector_palette = SECTOR_NEBULA_PALETTES[(sector - 1) % len(SECTOR_NEBULA_PALETTES)]
    for index, (x, y, radius, color) in enumerate(nebulae):
        color = sector_palette[index % len(sector_palette)]
        pygame.draw.circle(screen, color, (x, y), radius)

    # Moving stars with gentle twinkle
    for s in stars:
        s[1] += s[3]
        s[4] += 0.06

        if s[1] > H:
            s[0] = random.randrange(W)
            s[1] = -2

        brightness = 170 + int(85 * abs(math.sin(s[4])))
        color = (brightness, brightness, min(255, brightness + 10))

        pygame.draw.circle(
            screen, color,
            (int(s[0]), int(s[1])), s[2]
        )

def text(label, f, color, x, y, center=False):
    image = f.render(str(label), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    screen.blit(image, rect)

def draw_button(rect, label, color=CYAN):
    pygame.draw.rect(screen, (12, 20, 50), rect, border_radius=12)
    pygame.draw.rect(screen, color, rect, 2, border_radius=12)
    text(label, font, WHITE, rect.centerx, rect.centery, True)

SHIP_TYPES = [
    {"name": "SCOUT", "role": "FAST", "color": CYAN, "speed": 0.30, "lives": 3, "fire": 230, "spread": False},
    {"name": "GUARDIAN", "role": "ARMORED", "color": GREEN, "speed": 0.21, "lives": 4, "fire": 255, "spread": False},
    {"name": "STRIKER", "role": "ATTACK", "color": ORANGE, "speed": 0.25, "lives": 3, "fire": 185, "spread": True},
]
selected_ship = 0

def draw_ship(x, y, shield=False, ship_type=0):
    x, y = int(x), int(y)
    ship_color = SHIP_TYPES[ship_type]["color"]

    # Engine glow
    pygame.draw.circle(screen, (30, 30, 100), (x, y + 10), 31)
    pygame.draw.circle(screen, PURPLE, (x, y + 23), 9)
    pygame.draw.circle(screen, CYAN, (x, y + 23), 4)

    # Wings
    pygame.draw.polygon(screen, ship_color, [
        (x - 8, y + 2), (x - 34, y + 23),
        (x - 17, y + 21)
    ])
    pygame.draw.polygon(screen, ship_color, [
        (x + 8, y + 2), (x + 34, y + 23),
        (x + 17, y + 21)
    ])

    # Ship body
    pygame.draw.polygon(screen, ship_color, [
        (x, y - 31), (x - 19, y + 18),
        (x, y + 10), (x + 19, y + 18)
    ])
    pygame.draw.polygon(screen, WHITE, [
        (x, y - 23), (x - 5, y - 2), (x + 5, y - 2)
    ])
    pygame.draw.circle(screen, PURPLE, (x, y - 5), 5)

    if shield:
        pygame.draw.circle(screen, CYAN, (x, y), 37, 3)
        pygame.draw.circle(screen, BLUE, (x, y), 42, 1)

def draw_octopus_boss(bx, by, phase):
    """Draw the final boss as a living alien octopus with animated tentacles."""
    tick = pygame.time.get_ticks() / 1000.0
    tentacle_color = (145, 35, 205)
    edge_color = (255, 70, 125)

    # Eight independently waving tentacles, four on each side.
    tips = []
    for i in range(8):
        side = -1 if i < 4 else 1
        row = i if i < 4 else i - 4
        start_x = bx + side * (17 + row * 8)
        start_y = by + 18 + row * 3
        reach = 72 + row * 18
        wave = math.sin(tick * (2.2 + row * 0.25) + i * 0.9) * (10 + phase * 3)
        tip_x = bx + side * (reach + wave)
        tip_y = by + 52 + row * 13 + math.cos(tick * 1.7 + i) * 9
        points = []
        for step in range(7):
            t = step / 6
            curve_x = start_x + (tip_x - start_x) * t
            curve_y = start_y + (tip_y - start_y) * t + math.sin(t * math.pi + tick * 2 + i) * 13 * t
            points.append((int(curve_x), int(curve_y)))
        pygame.draw.lines(screen, tentacle_color, False, points, 13 - row)
        pygame.draw.lines(screen, edge_color, False, points, 3)
        for suction in range(1, 6):
            t = suction / 6
            sx = int(start_x + (tip_x - start_x) * t)
            sy = int(start_y + (tip_y - start_y) * t + math.sin(t * math.pi + tick * 2 + i) * 13 * t)
            pygame.draw.circle(screen, (255, 155, 190), (sx, sy), 3)
        tips.append((tip_x, tip_y))

    # Armored alien head, glowing eyes and a tooth-filled mouth.
    pygame.draw.ellipse(screen, (65, 15, 105), (bx - 57, by - 53, 114, 112))
    pygame.draw.ellipse(screen, (185, 45, 160), (bx - 51, by - 49, 102, 100), 5)
    pygame.draw.circle(screen, (255, 55, 35), (bx - 22, by - 8), 13)
    pygame.draw.circle(screen, (255, 225, 90), (bx - 22, by - 8), 6)
    pygame.draw.circle(screen, (255, 55, 35), (bx + 22, by - 8), 13)
    pygame.draw.circle(screen, (255, 225, 90), (bx + 22, by - 8), 6)
    pygame.draw.ellipse(screen, (25, 3, 20), (bx - 25, by + 12, 50, 31))
    for tooth_x in range(-18, 19, 9):
        pygame.draw.polygon(screen, WHITE, [(bx + tooth_x, by + 13), (bx + tooth_x + 4, by + 25), (bx + tooth_x + 8, by + 13)])
    pygame.draw.ellipse(screen, (255, 90, 145), (bx - 57, by - 53, 114, 112), 2)
    return tips

def explosion(x, y, color, amount=22):
    for _ in range(amount):
        angle = random.random() * math.tau
        speed = random.uniform(1.2, 5.5)
        particles.append([
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            random.uniform(4, 9),
            color
        ])

def reset_game():
    global px, py, bullets, enemies, drops, particles, enemy_bullets
    global score, lives, level, boss, spawn_timer, shot_timer
    global shield_timer, weapon_timer, boss_done, shake, boss_warning_timer
    global combo, combo_timer, bombs, bomb_flash, sector, sector_banner_timer
    global weapon_level, max_lives, upgrade_flash_timer, upgrade_message

    px, py = W / 2, H - 110
    bullets, enemies, drops, particles, enemy_bullets = [], [], [], [], []
    score, lives, level = 0, SHIP_TYPES[selected_ship]["lives"], 1
    max_lives = lives
    weapon_level = 1
    upgrade_flash_timer = 0
    upgrade_message = "WEAPON SYSTEM READY"
    boss = None
    spawn_timer = shot_timer = 0
    shield_timer = weapon_timer = 0
    boss_done = 0
    boss_warning_timer = 0
    shake = 0
    combo, combo_timer, bombs, bomb_flash = 0, 0, 2, 0
    sector, sector_banner_timer = 1, 0

MENU, SELECT_SHIP, PLAY, PAUSE, OVER, EXIT_CONFIRM = range(6)
state = MENU
touching = False
touch_pos = (W / 2, H - 100)
sound_button = pygame.Rect(10, 72, 112, 34)
pause_button = pygame.Rect(W - 100, 72, 88, 34)
play_button = pygame.Rect(90, 365, 300, 60)
resume_button = pygame.Rect(90, 355, 300, 55)
menu_button = pygame.Rect(90, 425, 300, 55)
exit_button = pygame.Rect(90, 390, 300, 58)
cancel_exit_button = pygame.Rect(90, 465, 300, 55)
ship_prev_button = pygame.Rect(35, 420, 115, 52)
ship_next_button = pygame.Rect(W - 150, 420, 115, 52)
ship_start_button = pygame.Rect(90, 510, 300, 58)
bomb_button = pygame.Rect(W - 118, 116, 108, 38)

reset_game()
running = True
paused_from_play = False

while running:
    dt = min(clock.tick(60), 40)
    draw_background()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            back_keys = (pygame.K_ESCAPE, getattr(pygame, "K_AC_BACK", pygame.K_ESCAPE))
            if event.key in back_keys:
                # Android phone Back opens a clear exit confirmation.
                paused_from_play = state in (PLAY, PAUSE)
                state = EXIT_CONFIRM
                touching = False

            if event.key in (pygame.K_LEFT, pygame.K_a) and state == SELECT_SHIP:
                selected_ship = (selected_ship - 1) % len(SHIP_TYPES)
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and state == SELECT_SHIP:
                selected_ship = (selected_ship + 1) % len(SHIP_TYPES)

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if state == MENU:
                    state = SELECT_SHIP
                elif state == SELECT_SHIP:
                    reset_game()
                    state = PLAY
                elif state == OVER:
                    reset_game()
                    state = PLAY
                elif state == PAUSE:
                    state = PLAY

            if event.key == pygame.K_m:
                sound_on = not sound_on

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = (int(event.pos[0] * W / display_w), int(event.pos[1] * H / display_h))

            if sound_button.collidepoint(pos):
                sound_on = not sound_on

            elif state == MENU and play_button.collidepoint(pos):
                state = SELECT_SHIP

            elif state == SELECT_SHIP:
                if ship_prev_button.collidepoint(pos):
                    selected_ship = (selected_ship - 1) % len(SHIP_TYPES)
                elif ship_next_button.collidepoint(pos):
                    selected_ship = (selected_ship + 1) % len(SHIP_TYPES)
                elif ship_start_button.collidepoint(pos):
                    reset_game()
                    state = PLAY

            elif state == PLAY:
                if pause_button.collidepoint(pos):
                    state = PAUSE
                    touching = False
                elif bomb_button.collidepoint(pos):
                    if bombs > 0:
                        bombs -= 1
                        bomb_flash = 900
                        enemies.clear()
                        enemy_bullets.clear()
                        if boss is not None:
                            boss["hp"] -= 30
                        explosion(px, py, YELLOW, 45)
                        play_sound(power_sound)
                else:
                    touching = True
                    touch_pos = pos

            elif state == PAUSE:
                if resume_button.collidepoint(pos):
                    state = PLAY
                elif menu_button.collidepoint(pos):
                    state = MENU

            elif state == OVER:
                if play_button.collidepoint(pos):
                    reset_game()
                    state = PLAY
                elif menu_button.collidepoint(pos):
                    state = MENU

            elif state == EXIT_CONFIRM:
                if exit_button.collidepoint(pos):
                    running = False
                elif cancel_exit_button.collidepoint(pos):
                    state = PLAY if paused_from_play else MENU

        elif event.type == pygame.MOUSEMOTION:
            if touching:
                touch_pos = (int(event.pos[0] * W / display_w), int(event.pos[1] * H / display_h))

        elif event.type == pygame.MOUSEBUTTONUP:
            touching = False

        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * W), int(event.y * H))

            if sound_button.collidepoint(pos):
                sound_on = not sound_on

            elif state == MENU and play_button.collidepoint(pos):
                state = SELECT_SHIP

            elif state == SELECT_SHIP:
                if ship_prev_button.collidepoint(pos):
                    selected_ship = (selected_ship - 1) % len(SHIP_TYPES)
                elif ship_next_button.collidepoint(pos):
                    selected_ship = (selected_ship + 1) % len(SHIP_TYPES)
                elif ship_start_button.collidepoint(pos):
                    reset_game()
                    state = PLAY

            elif state == PLAY:
                if pause_button.collidepoint(pos):
                    state = PAUSE
                    touching = False
                elif bomb_button.collidepoint(pos):
                    if bombs > 0:
                        bombs -= 1
                        bomb_flash = 900
                        enemies.clear()
                        enemy_bullets.clear()
                        if boss is not None:
                            boss["hp"] -= 18
                        explosion(px, py, YELLOW, 45)
                        play_sound(power_sound)
                else:
                    touching = True
                    touch_pos = pos

            elif state == PAUSE:
                if resume_button.collidepoint(pos):
                    state = PLAY
                elif menu_button.collidepoint(pos):
                    state = MENU

            elif state == OVER:
                if play_button.collidepoint(pos):
                    reset_game()
                    state = PLAY
                elif menu_button.collidepoint(pos):
                    state = MENU

            elif state == EXIT_CONFIRM:
                if exit_button.collidepoint(pos):
                    running = False
                elif cancel_exit_button.collidepoint(pos):
                    state = PLAY if paused_from_play else MENU

        elif event.type == pygame.FINGERMOTION:
            touch_pos = (int(event.x * W), int(event.y * H))

        elif event.type == pygame.FINGERUP:
            touching = False

    # Sound toggle is shown on all screens
    draw_button(
        sound_button,
        "SOUND ON" if sound_on else "SOUND OFF",
        CYAN if sound_on else RED
    )

    if state == PLAY:
        if touching:
            tx, ty = touch_pos
            move_speed = SHIP_TYPES[selected_ship]["speed"]
            px += (tx - px) * move_speed
            py += (ty - py) * move_speed

        px = max(35, min(W - 35, px))
        py = max(65, min(H - 45, py))

        shot_timer += dt
        spawn_timer += dt
        shield_timer = max(0, shield_timer - dt)
        weapon_timer = max(0, weapon_timer - dt)
        boss_warning_timer = max(0, boss_warning_timer - dt)
        combo_timer = max(0, combo_timer - dt)
        bomb_flash = max(0, bomb_flash - dt)
        upgrade_flash_timer = max(0, upgrade_flash_timer - dt)
        if combo_timer == 0:
            combo = 0
        shake = max(0, shake - dt)

        level = score // 100 + 1
        new_sector = (level - 1) // 5 + 1
        if new_sector > sector:
            sector = new_sector
            sector_banner_timer = 2800
        sector_banner_timer = max(0, sector_banner_timer - dt)

        # A major boss closes each five-level sector.
        if level % 5 == 0 and boss is None and boss_done < level:
            ultimate_boss = level >= 25
            # The alien octopus is the signature boss from the very first boss encounter.
            # Its health scales normally early and gains the ultimate bonus only at level 25.
            octopus_boss = True
            boss_hp = int((85 + level * 7) * (1.5 if ultimate_boss else 1.0))
            boss = {
                "x": W / 2, "y": 155,
                "hp": boss_hp,
                "maxhp": boss_hp,
                "dir": 1, "fire": 0,
                "name": "VOID OCTOPUS" if ultimate_boss else "SPACE OCTOPUS",
                "style": (sector - 1) % len(BOSS_PALETTES),
                "phase": 1, "pattern": 0,
                "ultimate": ultimate_boss,
                "octopus": octopus_boss
            }
            boss_warning_timer = 2200
            boss_done = level
            enemies.clear()
            play_sound(boss_sound)

        # Auto-fire
        ship_data = SHIP_TYPES[selected_ship]
        normal_fire_rate = ship_data["fire"]
        # Permanent upgrades earned from bosses improve fire rate and damage
        # for the rest of the current run.
        fire_interval = max(85, normal_fire_rate - (weapon_level - 1) * 22)
        if weapon_timer > 0:
            fire_interval = min(fire_interval, 100)
        shot_damage = 1 + (weapon_level - 1) // 2
        if shot_timer > fire_interval:
            if weapon_level >= 3 or weapon_timer > 0 or ship_data["spread"]:
                bullets.extend([
                    [px - 10, py - 24, -1.2, shot_damage],
                    [px, py - 30, 0, shot_damage],
                    [px + 10, py - 24, 1.2, shot_damage]
                ])
            elif weapon_level == 2:
                bullets.extend([
                    [px - 10, py - 26, -0.5, shot_damage],
                    [px + 10, py - 26, 0.5, shot_damage]
                ])
            else:
                bullets.append([px, py - 28, 0, shot_damage])

            shot_timer = 0
            if random.random() < 0.12:
                play_sound(laser_sound)

        for b in bullets[:]:
            b[1] -= 10
            b[0] += b[2]
            pygame.draw.line(
                screen, CYAN,
                (int(b[0]), int(b[1] + 12)),
                (int(b[0]), int(b[1])),
                4
            )
            pygame.draw.circle(
                screen, WHITE, (int(b[0]), int(b[1])), 2
            )
            if b[1] < -25:
                bullets.remove(b)

        # Enemy spawning
        if boss is None and spawn_timer > max(300, 850 - level * 35):
            kind = random.choices(["scout", "armored", "shooter"], weights=[55, 25, 20], k=1)[0]
            base = {"scout": (3.4, 13, 1), "armored": (1.25, 22, 3), "shooter": (2.0, 17, 1)}[kind]
            enemies.append({"x": random.randint(25, W - 25), "y": -25,
                "speed": base[0] + level * 0.10, "radius": base[1],
                "kind": kind, "hp": base[2], "fire": random.randint(700, 1500)})
            spawn_timer = 0

        for e in enemies[:]:
            e["y"] += e["speed"]
            ex, ey, radius = e["x"], e["y"], e["radius"]
            kind = e["kind"]
            color = {"scout": CYAN, "armored": PURPLE, "shooter": ORANGE}[kind]
            if kind == "armored":
                pygame.draw.circle(screen, color, (int(ex), int(ey)), radius + 4, 3)
                pygame.draw.rect(screen, color, (int(ex-radius), int(ey-radius), radius*2, radius*2), border_radius=5)
            elif kind == "shooter":
                pygame.draw.polygon(screen, ORANGE, [(int(ex), int(ey+radius)), (int(ex-radius), int(ey-radius)), (int(ex+radius), int(ey-radius))])
                e["fire"] -= dt
                if e["fire"] <= 0 and ey < H - 170:
                    enemy_bullets.append([ex, ey + radius, 3.8 + level * 0.08])
                    e["fire"] = random.randint(1500, 2300)
            else:
                pygame.draw.polygon(screen, CYAN, [(int(ex), int(ey+radius)), (int(ex-radius), int(ey-radius)), (int(ex), int(ey-radius//2)), (int(ex+radius), int(ey-radius))])
            pygame.draw.circle(screen, WHITE, (int(ex), int(ey)), 3)

            for b in bullets[:]:
                if math.hypot(ex - b[0], ey - b[1]) < radius + 9:
                    bullets.remove(b)
                    e["hp"] -= b[3] if len(b) > 3 else 1
                    if e["hp"] <= 0:
                        enemies.remove(e)
                        combo = min(5, combo + 1) if combo_timer > 0 else 1
                        combo_timer = 2400
                        score += 10 * combo
                        explosion(ex, ey, color, 26 if kind == "armored" else 18)
                        play_sound(hit_sound)
                        if random.random() < 0.24:
                            drops.append([ex, ey, random.choices(
                                ["shield", "weapon", "bomb", "repair"],
                                weights=[35, 35, 20, 10], k=1
                            )[0]])
                    break
            if e not in enemies:
                continue
            if ey > H + 25:
                enemies.remove(e)
                lives -= 1
                combo, combo_timer = 0, 0
                shake = 150
                continue
            if math.hypot(ex - px, ey - py) < radius + 18:
                enemies.remove(e)
                if shield_timer <= 0:
                    lives -= 1
                    combo, combo_timer = 0, 0
                    shake = 220
                    explosion(px, py, RED)
                    play_sound(hit_sound)
                else:
                    explosion(ex, ey, CYAN)

        # Boss
        if boss is not None:
            boss["phase"] = (
                3 if boss["hp"] <= boss["maxhp"] * 0.20
                else 2 if boss["hp"] <= boss["maxhp"] * 0.5
                else 1
            )
            boss_speed = 2.0 + level * 0.07
            # Later phases become faster, with a third phase for the ultimate boss.
            if boss["phase"] == 2:
                boss_speed *= 1.55
            elif boss["phase"] == 3:
                boss_speed *= 1.9
            boss["x"] += boss["dir"] * boss_speed

            if boss["x"] > W - 75:
                boss["dir"] = -1
            if boss["x"] < 75:
                boss["dir"] = 1

            boss["fire"] += dt
            fire_interval = 900 if boss["phase"] == 1 else 540 if boss["phase"] == 2 else 380
            if boss["fire"] > fire_interval:
                if boss.get("octopus"):
                    # The octopus fires from its tentacles; each phase adds lanes.
                    lanes = 3 if boss["phase"] == 1 else 5 if boss["phase"] == 2 else 7
                    spread = 22 if boss["phase"] == 1 else 28
                    for lane in range(lanes):
                        dx = (lane - (lanes - 1) / 2) * spread
                        speed = 3.8 + boss["phase"] * 0.75
                        enemy_bullets.append([boss["x"] + dx, boss["y"] + 65, speed])
                elif boss["phase"] == 1:
                    shots = [(-36, 3.6), (0, 4.1), (36, 3.6)]
                elif boss["phase"] == 2:
                    # Phase II cycles through wider, denser attack waves.
                    patterns = [
                        [(-64, 4.2), (-32, 4.5), (0, 4.8), (32, 4.5), (64, 4.2)],
                        [(-42, 5.0), (-14, 5.3), (14, 5.3), (42, 5.0)],
                        [(-72, 4.7), (-48, 4.9), (-24, 5.1), (0, 5.3), (24, 5.1), (48, 4.9), (72, 4.7)],
                    ]
                    shots = patterns[boss["pattern"] % len(patterns)]
                    boss["pattern"] = (boss["pattern"] + 1) % len(patterns)
                else:
                    # Every boss becomes enraged below 20% health and fires a heavy seven-lane volley.
                    shots = [(-84, 5.0), (-56, 5.3), (-28, 5.6), (0, 5.9),
                             (28, 5.6), (56, 5.3), (84, 5.0)]
                if not boss.get("octopus"):
                    for dx, speed in shots:
                        enemy_bullets.append([boss["x"] + dx, boss["y"] + 32, speed])
                boss["fire"] = 0

            bx, by = int(boss["x"]), int(boss["y"])

            # Sector-specific boss colors and identity.
            boss_color, boss_core, boss_glow = BOSS_PALETTES[boss["style"]]
            if boss.get("octopus"):
                draw_octopus_boss(bx, by, boss["phase"])
            else:
                pygame.draw.circle(screen, boss_glow, (bx, by), 59)
                pygame.draw.circle(screen, boss_color, (bx, by), 49, 3)
                pygame.draw.polygon(screen, boss_core, [
                    (bx, by - 40), (bx - 55, by - 12),
                    (bx - 42, by + 30), (bx, by + 18),
                    (bx + 42, by + 30), (bx + 55, by - 12)
                ])
                pygame.draw.circle(screen, boss_glow, (bx, by), 14)
                pygame.draw.circle(screen, WHITE, (bx, by), 5)

            for b in bullets[:]:
                if math.hypot(bx - b[0], by - b[1]) < 48:
                    bullets.remove(b)
                    boss["hp"] -= b[3] if len(b) > 3 else 1

            # Boss identity and health
            phase_label = "  - PHASE III" if boss["phase"] == 3 else "  - PHASE II" if boss["phase"] == 2 else ""
            text(boss["name"] + phase_label, small, boss_core, W / 2, 108, True)
            bw = 230
            pygame.draw.rect(screen, RED, (W // 2 - 115, 130, bw, 10))
            hpw = max(0, int(bw * boss["hp"] / boss["maxhp"]))
            pygame.draw.rect(screen, GREEN, (W // 2 - 115, 130, hpw, 10))

            if boss["hp"] <= 0:
                explosion(bx, by, PURPLE, 55)
                score += 100
                # Boss rewards are permanent until this run ends.
                weapon_level = min(5, weapon_level + 1)
                max_lives = min(8, max_lives + 1)
                lives = min(max_lives, lives + 1)
                bombs = min(4, bombs + 1)
                shield_timer = max(shield_timer, 2500)
                weapon_timer = max(weapon_timer, 3500)
                upgrade_message = "UPGRADE! WEAPON LV " + str(weapon_level) + "  HULL +" 
                upgrade_flash_timer = 3200
                boss = None
                play_sound(power_sound)

        # Enemy projectiles
        for b in enemy_bullets[:]:
            b[1] += b[2]
            pygame.draw.circle(screen, RED, (int(b[0]), int(b[1])), 6)

            if b[1] > H:
                enemy_bullets.remove(b)
            elif math.hypot(b[0] - px, b[1] - py) < 22:
                enemy_bullets.remove(b)
                if shield_timer <= 0:
                    lives -= 1
                    shake = 180
                    play_sound(hit_sound)
                else:
                    explosion(px, py, CYAN)

        # Pickups
        for d in drops[:]:
            d[1] += 2
            color = {
                "shield": CYAN, "weapon": YELLOW,
                "bomb": ORANGE, "repair": GREEN
            }[d[2]]
            pygame.draw.circle(screen, color, (int(d[0]), int(d[1])), 14, 3)
            pickup_label = {"shield": "S", "weapon": "W", "bomb": "B", "repair": "+"}[d[2]]
            text(pickup_label, small, color, d[0], d[1], True)

            if math.hypot(d[0] - px, d[1] - py) < 30:
                if d[2] == "shield":
                    shield_timer = 5000
                elif d[2] == "weapon":
                    weapon_timer = 7000
                elif d[2] == "bomb":
                    bombs = min(4, bombs + 1)
                else:
                    lives = min(max_lives, lives + 1)
                drops.remove(d)
                play_sound(power_sound)
            elif d[1] > H:
                drops.remove(d)

        draw_ship(px, py, shield_timer > 0, selected_ship)

        # HUD
        text("GALAXY DEFENDER", small, CYAN, 10, 10)
        text("SCORE " + str(score), font, WHITE, 10, 37)
        text("LEVEL " + str(level), font, YELLOW, 10, 101)
        text("LIVES " + str(lives) + "/" + str(max_lives), font, GREEN, 10, 129)
        text("WEAPON LV " + str(weapon_level), small, YELLOW, 10, 157)
        text("SECTOR " + str(sector) + " - " + SECTOR_NAMES[(sector - 1) % len(SECTOR_NAMES)], small, CYAN, 10, 207)

        draw_button(pause_button, "PAUSE", PURPLE)
        draw_button(bomb_button, "BOMB x" + str(bombs), YELLOW)
        if combo > 1 and combo_timer > 0:
            text("COMBO x" + str(combo), font, YELLOW, W / 2, 70, True)
        if boss_warning_timer > 0:
            warning_box = pygame.Rect(35, 220, W - 70, 54)
            pygame.draw.rect(screen, (45, 8, 20), warning_box, border_radius=12)
            pygame.draw.rect(screen, RED, warning_box, 2, border_radius=12)
            text("WARNING: BOSS APPROACHING!", font, YELLOW,
                 W / 2, warning_box.centery, True)
        if sector_banner_timer > 0:
            banner = pygame.Rect(45, 285, W - 90, 48)
            pygame.draw.rect(screen, (10, 25, 65), banner, border_radius=10)
            pygame.draw.rect(screen, CYAN, banner, 2, border_radius=10)
            text("NEW SECTOR: " + SECTOR_NAMES[(sector - 1) % len(SECTOR_NAMES)], small, WHITE, W / 2, banner.centery, True)

        if shield_timer > 0:
            text("SHIELD", small, CYAN, 10, 181)
        if weapon_timer > 0:
            text("POWER WEAPON", small, YELLOW, 150, 181)
        if upgrade_flash_timer > 0:
            upgrade_box = pygame.Rect(28, 345, W - 56, 54)
            pygame.draw.rect(screen, (12, 35, 65), upgrade_box, border_radius=12)
            pygame.draw.rect(screen, YELLOW, upgrade_box, 2, border_radius=12)
            text(upgrade_message, small, YELLOW, W / 2, upgrade_box.centery, True)

        # Shake flash
        if shake > 0:
            pygame.draw.rect(screen, RED, (0, 0, W, H), 4)

        if lives <= 0:
            state = OVER
            if score > best_score:
                best_score = score
                save_best()
            play_sound(gameover_sound)

    # Particles
    for p in particles[:]:
        p[0] += p[2]
        p[1] += p[3]
        p[2] *= 0.98
        p[3] *= 0.98
        p[4] -= 0.16

        if p[4] <= 0:
            particles.remove(p)
        else:
            pygame.draw.circle(
                screen, p[5],
                (int(p[0]), int(p[1])),
                max(1, int(p[4]))
            )

    # Menus
    if state == MENU:
        text("GALAXY", big, CYAN, W / 2, 190, True)
        text("DEFENDER", big, PURPLE, W / 2, 245, True)
        draw_ship(W / 2, 310, True)
        draw_button(play_button, "CHOOSE SHIP", CYAN)
        text("BEST SCORE: " + str(best_score),
             font, YELLOW, W / 2, 460, True)
        text("TOUCH TO MOVE • AUTO LASER",
             small, WHITE, W / 2, 510, True)
        text("SOUND: M KEY OR BUTTON ABOVE",
             small, CYAN, W / 2, 540, True)

    elif state == SELECT_SHIP:
        ship_data = SHIP_TYPES[selected_ship]
        text("SELECT YOUR SHIP", big, CYAN, W / 2, 205, True)
        draw_ship(W / 2, 320, True, selected_ship)
        text(ship_data["name"], big, ship_data["color"], W / 2, 375, True)
        text(ship_data["role"], font, WHITE, W / 2, 405, True)
        text("SPEED: " + str(int(ship_data["speed"] * 100)) +
             "   LIVES: " + str(ship_data["lives"]), small, YELLOW, W / 2, 455, True)
        text("WEAPON: " + ("TRIPLE SHOT" if ship_data["spread"] else "LASER"),
             small, CYAN, W / 2, 480, True)
        draw_button(ship_prev_button, "< PREVIOUS", PURPLE)
        draw_button(ship_next_button, "NEXT >", PURPLE)
        draw_button(ship_start_button, "START GAME", GREEN)

    elif state == PAUSE:
        text("PAUSED", big, CYAN, W / 2, 265, True)
        draw_button(resume_button, "RESUME", GREEN)
        draw_button(menu_button, "MAIN MENU", PURPLE)

    elif state == OVER:
        text("GAME OVER", big, RED, W / 2, 260, True)
        text("SCORE: " + str(score), font, WHITE, W / 2, 320, True)
        text("BEST: " + str(best_score), font, YELLOW, W / 2, 350, True)
        draw_button(play_button, "PLAY AGAIN", CYAN)
        draw_button(menu_button, "MAIN MENU", PURPLE)

    elif state == EXIT_CONFIRM:
        # Dim the current screen and ask before closing the app.
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 15, 205))
        screen.blit(overlay, (0, 0))
        text("EXIT GAME?", big, YELLOW, W / 2, 300, True)
        text("Do you want to close Galaxy Defender?", small, WHITE, W / 2, 345, True)
        draw_button(exit_button, "EXIT GAME", RED)
        draw_button(cancel_exit_button, "CANCEL", GREEN)

    scaled_frame = pygame.transform.scale(screen, (display_w, display_h))
    display_surface.blit(scaled_frame, (0, 0))
    pygame.display.flip()

pygame.quit()
