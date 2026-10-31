
import pygame
import random
import math
import os
import sys
import traceback
import array

pygame.init()

# Sound is optional: the game still works if audio is unavailable.
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO = True
except pygame.error:
    AUDIO = False

W, H = 480, 760
screen = pygame.display.set_mode((W, H))

# Show unexpected Python errors on-screen instead of silently closing.
def show_crash(exc_type, exc_value, exc_tb):
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        log_path = os.path.join(os.path.expanduser("~"), "galaxy_crash.txt")
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(details)
    except Exception:
        pass

    try:
        pygame.display.set_caption("GALAXY DEFENDER - ERROR")
        error_font = pygame.font.Font(None, 22)
        lines = details.strip().splitlines()
        running_error = True
        while running_error:
            for error_event in pygame.event.get():
                if error_event.type == pygame.QUIT:
                    running_error = False
            screen.fill((18, 5, 15))
            title_image = pygame.font.Font(None, 32).render(
                "GAME ERROR - SEND THIS SCREEN", True, (255, 100, 100)
            )
            screen.blit(title_image, (12, 12))
            y = 55
            for line in lines[-26:]:
                # Keep long traceback lines inside the phone screen.
                for start in range(0, max(1, len(line)), 48):
                    part = line[start:start + 48]
                    image = error_font.render(part, True, (255, 235, 235))
                    screen.blit(image, (12, y))
                    y += 22
                    if y > screen.get_height() - 12:
                        break
                if y > screen.get_height() - 12:
                    break
            pygame.display.flip()
            pygame.time.wait(150)
        pygame.quit()
    except Exception:
        pass

sys.excepthook = show_crash
pygame.display.set_caption("GALAXY DEFENDER ULTIMATE V2")
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

    # Soft colorful nebulae
    for x, y, radius, color in nebulae:
        pygame.draw.circle(
            screen, color, (x, y), radius
        )

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

def draw_ship(x, y, shield=False):
    x, y = int(x), int(y)

    # Engine glow
    pygame.draw.circle(screen, (30, 30, 100), (x, y + 10), 31)
    pygame.draw.circle(screen, PURPLE, (x, y + 23), 9)
    pygame.draw.circle(screen, CYAN, (x, y + 23), 4)

    # Wings
    pygame.draw.polygon(screen, BLUE, [
        (x - 8, y + 2), (x - 34, y + 23),
        (x - 17, y + 21)
    ])
    pygame.draw.polygon(screen, BLUE, [
        (x + 8, y + 2), (x + 34, y + 23),
        (x + 17, y + 21)
    ])

    # Ship body
    pygame.draw.polygon(screen, CYAN, [
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
    global shield_timer, weapon_timer, boss_done, shake

    px, py = W / 2, H - 110
    bullets, enemies, drops, particles, enemy_bullets = [], [], [], [], []
    score, lives, level = 0, 3, 1
    boss = None
    spawn_timer = shot_timer = 0
    shield_timer = weapon_timer = 0
    boss_done = 0
    shake = 0

MENU, PLAY, PAUSE, OVER = range(4)
state = MENU
touching = False
touch_pos = (W / 2, H - 100)
sound_button = pygame.Rect(10, 72, 112, 34)
pause_button = pygame.Rect(W - 100, 72, 88, 34)
play_button = pygame.Rect(90, 365, 300, 60)
resume_button = pygame.Rect(90, 355, 300, 55)
menu_button = pygame.Rect(90, 425, 300, 55)

reset_game()
running = True

while running:
    dt = min(clock.tick(60), 40)
    draw_background()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if state == PLAY:
                    state = PAUSE
                elif state == PAUSE:
                    state = PLAY
                else:
                    running = False

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if state in (MENU, OVER):
                    reset_game()
                    state = PLAY
                elif state == PAUSE:
                    state = PLAY

            if event.key == pygame.K_m:
                sound_on = not sound_on

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if sound_button.collidepoint(pos):
                sound_on = not sound_on

            elif state == MENU and play_button.collidepoint(pos):
                reset_game()
                state = PLAY

            elif state == PLAY:
                if pause_button.collidepoint(pos):
                    state = PAUSE
                    touching = False
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

        elif event.type == pygame.MOUSEMOTION:
            if touching:
                touch_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            touching = False

        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * W), int(event.y * H))

            if sound_button.collidepoint(pos):
                sound_on = not sound_on

            elif state == MENU and play_button.collidepoint(pos):
                reset_game()
                state = PLAY

            elif state == PLAY:
                if pause_button.collidepoint(pos):
                    state = PAUSE
                    touching = False
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
            px += (tx - px) * 0.24
            py += (ty - py) * 0.24

        px = max(35, min(W - 35, px))
        py = max(65, min(H - 45, py))

        shot_timer += dt
        spawn_timer += dt
        shield_timer = max(0, shield_timer - dt)
        weapon_timer = max(0, weapon_timer - dt)
        shake = max(0, shake - dt)

        level = score // 100 + 1

        # Boss every five levels
        if level % 5 == 0 and boss is None and boss_done < level:
            boss = {
                "x": W / 2, "y": 155,
                "hp": 40 + level * 5,
                "maxhp": 40 + level * 5,
                "dir": 1, "fire": 0
            }
            boss_done = level
            enemies.clear()
            play_sound(boss_sound)

        # Auto-fire
        if shot_timer > (120 if weapon_timer > 0 else 230):
            if weapon_timer > 0:
                bullets.extend([
                    [px - 10, py - 24, -1.2],
                    [px, py - 30, 0],
                    [px + 10, py - 24, 1.2]
                ])
            else:
                bullets.append([px, py - 28, 0])

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
            enemies.append([
                random.randint(25, W - 25), -25,
                random.uniform(1.5, 2.8) + level * 0.15,
                random.randint(14, 21)
            ])
            spawn_timer = 0

        for e in enemies[:]:
            e[1] += e[2]
            ex, ey, speed, radius = e

            pygame.draw.polygon(screen, RED, [
                (int(ex), int(ey + radius)),
                (int(ex - radius), int(ey - radius)),
                (int(ex), int(ey - radius // 2)),
                (int(ex + radius), int(ey - radius))
            ])
            pygame.draw.circle(screen, ORANGE, (int(ex), int(ey)), 4)

            hit = False
            for b in bullets[:]:
                if math.hypot(ex - b[0], ey - b[1]) < radius + 9:
                    bullets.remove(b)
                    hit = True
                    break

            if hit:
                enemies.remove(e)
                score += 10
                explosion(ex, ey, random.choice([ORANGE, CYAN, PURPLE]))
                play_sound(hit_sound)

                if random.random() < 0.20:
                    drops.append([
                        ex, ey,
                        random.choice(["shield", "weapon"])
                    ])
                continue

            if ey > H + 25:
                enemies.remove(e)
                lives -= 1
                shake = 150
                continue

            if math.hypot(ex - px, ey - py) < radius + 18:
                enemies.remove(e)
                if shield_timer <= 0:
                    lives -= 1
                    shake = 220
                    explosion(px, py, RED)
                    play_sound(hit_sound)
                else:
                    explosion(ex, ey, CYAN)

        # Boss
        if boss is not None:
            boss["x"] += boss["dir"] * (2 + level * 0.08)

            if boss["x"] > W - 75:
                boss["dir"] = -1
            if boss["x"] < 75:
                boss["dir"] = 1

            boss["fire"] += dt
            if boss["fire"] > 900:
                for dx, speed in [(-30, 3.5), (0, 4), (30, 3.5)]:
                    enemy_bullets.append([
                        boss["x"] + dx, boss["y"] + 32, speed
                    ])
                boss["fire"] = 0

            bx, by = int(boss["x"]), int(boss["y"])

            # Boss glow
            pygame.draw.circle(screen, (45, 15, 100), (bx, by), 59)
            pygame.draw.circle(screen, PURPLE, (bx, by), 49, 3)
            pygame.draw.polygon(screen, RED, [
                (bx, by - 40), (bx - 55, by - 12),
                (bx - 42, by + 30), (bx, by + 18),
                (bx + 42, by + 30), (bx + 55, by - 12)
            ])
            pygame.draw.circle(screen, ORANGE, (bx, by), 14)
            pygame.draw.circle(screen, WHITE, (bx, by), 5)

            for b in bullets[:]:
                if math.hypot(bx - b[0], by - b[1]) < 48:
                    bullets.remove(b)
                    boss["hp"] -= 1

            # Boss health
            bw = 230
            pygame.draw.rect(screen, RED, (W // 2 - 115, 130, bw, 10))
            hpw = max(0, int(bw * boss["hp"] / boss["maxhp"]))
            pygame.draw.rect(screen, GREEN, (W // 2 - 115, 130, hpw, 10))

            if boss["hp"] <= 0:
                explosion(bx, by, PURPLE, 55)
                score += 100
                lives = min(5, lives + 1)
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
            color = CYAN if d[2] == "shield" else YELLOW
            pygame.draw.circle(screen, color, (int(d[0]), int(d[1])), 14, 3)
            text("S" if d[2] == "shield" else "W",
                 small, color, d[0], d[1], True)

            if math.hypot(d[0] - px, d[1] - py) < 30:
                if d[2] == "shield":
                    shield_timer = 5000
                else:
                    weapon_timer = 7000
                drops.remove(d)
                play_sound(power_sound)
            elif d[1] > H:
                drops.remove(d)

        draw_ship(px, py, shield_timer > 0)

        # HUD
        text("GALAXY DEFENDER", small, CYAN, 10, 10)
        text("SCORE " + str(score), font, WHITE, 10, 37)
        text("LEVEL " + str(level), font, YELLOW, 10, 101)
        text("LIVES " + str(lives), font, GREEN, 10, 129)

        draw_button(pause_button, "PAUSE", PURPLE)

        if shield_timer > 0:
            text("SHIELD", small, CYAN, 10, 157)
        if weapon_timer > 0:
            text("POWER WEAPON", small, YELLOW, 10, 181)

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
        draw_button(play_button, "PLAY", CYAN)
        text("BEST SCORE: " + str(best_score),
             font, YELLOW, W / 2, 460, True)
        text("TOUCH TO MOVE • AUTO LASER",
             small, WHITE, W / 2, 510, True)
        text("SOUND: M KEY OR BUTTON ABOVE",
             small, CYAN, W / 2, 540, True)

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

    pygame.display.flip()

pygame.quit()
