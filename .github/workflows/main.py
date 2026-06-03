import asyncio
import pygame
import sys
import os
import random
import math
import array

pygame.init()

# Browser detection for Pygbag/mobile web
IS_BROWSER = sys.platform == "emscripten"

# =========================
# SOUND SYSTEM
# =========================
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
    SOUND_ON = True
except Exception:
    SOUND_ON = False


# =========================
# WINDOW / DISPLAY
# =========================
# Logical game size. Keep the game drawn at 1000x700, then scale it to the real
# browser/phone screen. This prevents the mobile browser from showing a tiny
# desktop canvas.
WIDTH, HEIGHT = 1000, 700
DISPLAY_W, DISPLAY_H = WIDTH, HEIGHT

DISPLAY_FLAGS = 0
try:
    DISPLAY_FLAGS = pygame.SCALED | pygame.RESIZABLE
except Exception:
    DISPLAY_FLAGS = 0

def get_browser_display_size():
    """Get the best available browser/canvas size for Pygbag/mobile."""
    try:
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            return info.current_w, info.current_h
    except Exception:
        pass
    return WIDTH, HEIGHT

if IS_BROWSER:
    DISPLAY_W, DISPLAY_H = get_browser_display_size()
    display_screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H), DISPLAY_FLAGS)
    # All game drawing still happens on this virtual screen.
    screen = pygame.Surface((WIDTH, HEIGHT))
else:
    display_screen = pygame.display.set_mode((WIDTH, HEIGHT), DISPLAY_FLAGS)
    screen = display_screen

pygame.display.set_caption("CyberShield Academy: Teen Digital Defenders")
clock = pygame.time.Clock()


def screen_to_game_pos(pos):
    """Convert real screen/touch coordinates to the 1000x700 game coordinates."""
    if not IS_BROWSER:
        return pos

    x, y = pos
    game_x = int(x * WIDTH / max(1, DISPLAY_W))
    game_y = int(y * HEIGHT / max(1, DISPLAY_H))
    return game_x, game_y


def update_display_size(w=None, h=None):
    """Update browser/mobile canvas size when phone orientation or window changes."""
    global DISPLAY_W, DISPLAY_H, display_screen

    if not IS_BROWSER:
        return

    if w is None or h is None:
        w, h = get_browser_display_size()

    DISPLAY_W = max(1, int(w))
    DISPLAY_H = max(1, int(h))
    display_screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H), DISPLAY_FLAGS)


def present_frame():
    """Show the game. On mobile/browser it stretches to the full device frame."""
    if IS_BROWSER:
        scaled_frame = pygame.transform.smoothscale(screen, (DISPLAY_W, DISPLAY_H))
        display_screen.blit(scaled_frame, (0, 0))

    pygame.display.flip()

# =========================
# THEME COLOURS
# =========================
WHITE = (235, 242, 250)
BLACK = (8, 13, 20)

DARK_BG = (10, 18, 32)
DARK_PANEL = (15, 29, 50)
CARD_BG = (22, 38, 62)

NEON_BLUE = (66, 153, 225)
NEON_GREEN = (72, 187, 120)
NEON_PURPLE = (128, 90, 213)
NEON_PINK = (213, 63, 140)

RED = (229, 62, 62)
YELLOW = (236, 201, 75)
ORANGE = (237, 137, 54)
GRAY = (113, 128, 150)

SOFT_BLUE = (49, 130, 206)
OPTION_BG = (28, 54, 88)
OPTION_HOVER = (66, 153, 225)
OPTION_BORDER = (99, 179, 237)
PROGRESS_BG = (31, 41, 55)

# =========================
# ASSET / FONT LOADING
# =========================
def base_path():
    """Works in normal Python, PyInstaller, and Pygbag."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = base_path()
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")


def load_font(filename, size, fallback="arial", bold=False):
    """
    Put these optional fonts in assets/fonts:
        Rajdhani-Bold.ttf
        Inter-Regular.ttf
        Inter-SemiBold.ttf

    If they are missing, the game still runs using system fonts.
    """
    path = os.path.join(FONT_DIR, filename)
    try:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    except Exception:
        pass

    try:
        return pygame.font.SysFont(fallback, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


font = load_font("Inter-SemiBold.ttf", 25, bold=True)
small_font = load_font("Inter-Regular.ttf", 19)
title_font = load_font("Rajdhani-Bold.ttf", 44, bold=True)
big_title_font = load_font("Rajdhani-Bold.ttf", 56, bold=True)

HIGH_SCORE_FILE = os.path.join(BASE_DIR, "cybershield_teen_defenders_highscore.txt")

# =========================
# SOUND HELPERS
# =========================
def make_sound(freq=440, duration=0.2, volume=0.4):
    if not SOUND_ON:
        return None

    sample_rate = 44100
    samples = int(sample_rate * duration)
    buf = array.array("h")

    for i in range(samples):
        value = int(32767 * volume * math.sin(2 * math.pi * freq * i / sample_rate))
        buf.append(value)

    try:
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


click_sound = make_sound(500, 0.08)
correct_sound = make_sound(850, 0.15)
wrong_sound = make_sound(180, 0.25)
coin_sound = make_sound(1100, 0.08)
win_sound = make_sound(700, 0.5)


def play(sound):
    if SOUND_ON and sound:
        try:
            sound.play()
        except Exception:
            pass


# =========================
# HIGH SCORE
# =========================
def load_high_score():
    if IS_BROWSER:
        return 0

    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as file:
                return int(file.read())
        except Exception:
            return 0
    return 0


def save_high_score(value):
    if IS_BROWSER:
        return

    try:
        with open(HIGH_SCORE_FILE, "w") as file:
            file.write(str(value))
    except Exception:
        pass


# =========================
# GAME VARIABLES
# =========================
score = 0
coins = 0
level = 0
lives = 3
game_state = "start"
selected_message = ""
badges = []
question_start_time = 0
mini_start_time = 0
high_score = load_high_score()

mouse_clicked = False
pointer_pressed = False
pointer_pos = (0, 0)

selected_quiz_option = None
mission_passed = False
completed_levels = set()

player = pygame.Rect(80, 500, 42, 55)
player_speed = 5
hero_frame = 0

enemy = pygame.Rect(750, 470, 60, 60)
enemy_speed = 3
enemy_direction = 1

collectibles = []
mini_target = 4
mini_collected = 0

# Shorter play area leaves room for mobile touch controls at the bottom.
PLAY_AREA = pygame.Rect(40, 220, 920, 340)
COLLECTIBLE_SIZE = 26
COLLECTIBLE_PADDING = 34

particles = []

# Mobile touch D-pad
touch_left = pygame.Rect(55, 610, 60, 60)
touch_right = pygame.Rect(185, 610, 60, 60)
touch_up = pygame.Rect(120, 545, 60, 60)
touch_down = pygame.Rect(120, 610, 60, 60)

tools = [
    "Firewall Shield",
    "Password Scanner",
    "Privacy Cloak",
    "2-Step Login Boost"
]

levels = [
    {
        "title": "Level 1: Password Power-Up",
        "zone": "Collect password cores and dodge weak-password bots.",
        "story": "Your school game account is under attack by a weak password bot.",
        "question": "Which password is the strongest choice?",
        "options": ["12345678", "password", "K@vAli#2026!", "myname123"],
        "answer": 2,
        "lesson": "A strong password mixes uppercase letters, lowercase letters, numbers, and symbols.",
        "badge": "Password Pro",
        "enemy": "Weak Password Bot",
        "item": "Password Core",
        "theme": NEON_BLUE
    },
    {
        "title": "Level 2: Scam Message Zone",
        "zone": "Collect trusted messages and avoid scam traps.",
        "story": "A message says: 'You won a free phone! Click now to claim it.'",
        "question": "What is the safest move?",
        "options": ["Click the link", "Forward it", "Check the sender and report it", "Enter your password"],
        "answer": 2,
        "lesson": "Scam messages often use prizes, pressure, or fake links to trick people.",
        "badge": "Scam Spotter",
        "enemy": "Phishing Phantom",
        "item": "Trusted Message",
        "theme": NEON_GREEN
    },
    {
        "title": "Level 3: Privacy Street",
        "zone": "Collect privacy tokens and avoid oversharing drones.",
        "story": "A friend wants to post their home address on a public profile.",
        "question": "What advice should you give?",
        "options": ["Post it publicly", "Share it with strangers", "Keep personal details private", "Add their phone number too"],
        "answer": 2,
        "lesson": "Keep addresses, phone numbers, school details, and private information away from public posts.",
        "badge": "Privacy Guardian",
        "enemy": "Overshare Drone",
        "item": "Privacy Token",
        "theme": NEON_PURPLE
    },
    {
        "title": "Level 4: Malware Rush",
        "zone": "Collect clean files and avoid infected downloads.",
        "story": "A pop-up says it can make your laptop faster if you download a file.",
        "question": "What should you do?",
        "options": ["Download it", "Close it and avoid unknown downloads", "Send it to friends", "Turn off antivirus"],
        "answer": 1,
        "lesson": "Unknown downloads can hide viruses, spyware, or malware.",
        "badge": "Malware Blocker",
        "enemy": "Virus Bug",
        "item": "Clean File",
        "theme": ORANGE
    },
    {
        "title": "Level 5: Kindness Arena",
        "zone": "Collect support stars and avoid toxic comments.",
        "story": "Someone is being bullied in an online group chat.",
        "question": "What is the best response?",
        "options": ["Join in", "Laugh at it", "Block, report, support, and save evidence", "Share the post"],
        "answer": 2,
        "lesson": "Cyberbullying should be reported. Support the person affected and keep evidence.",
        "badge": "Online Respect Hero",
        "enemy": "Toxic Comment",
        "item": "Support Star",
        "theme": NEON_PINK
    },
    {
        "title": "Final Level: ShadowNet Showdown",
        "zone": "Collect security codes and avoid ShadowNet drones.",
        "story": "ShadowNet creates a fake login page to steal student accounts.",
        "question": "How can you protect your account better?",
        "options": ["Use two-factor authentication", "Give away your password", "Use the same password everywhere", "Turn off security"],
        "answer": 0,
        "lesson": "Two-factor authentication adds an extra step, making your account harder to steal.",
        "badge": "ShadowNet Stopper",
        "enemy": "ShadowNet Drone",
        "item": "Security Code",
        "theme": RED
    }
]


# =========================
# UI FUNCTIONS
# =========================
def get_font(size="normal"):
    if size == "title":
        return title_font
    if size == "big":
        return big_title_font
    if size == "small":
        return small_font
    return font


def spaced_line_width(text, used_font, extra_word_spacing=0):
    words = text.split(" ")
    if len(words) <= 1:
        return used_font.size(text)[0]

    total = 0
    space_width = used_font.size(" ")[0] + extra_word_spacing

    for index, word in enumerate(words):
        total += used_font.size(word)[0]
        if index < len(words) - 1:
            total += space_width

    return total


def draw_spaced_line(text, x, y, color=WHITE, size="normal", extra_word_spacing=2):
    used_font = get_font(size)
    words = text.split(" ")

    if len(words) <= 1:
        render = used_font.render(text, True, color)
        screen.blit(render, (x, y))
        return render.get_width()

    cursor_x = x
    space_width = used_font.size(" ")[0] + extra_word_spacing

    for index, word in enumerate(words):
        render = used_font.render(word, True, color)
        screen.blit(render, (cursor_x, y))
        cursor_x += render.get_width()
        if index < len(words) - 1:
            cursor_x += space_width

    return cursor_x - x


def draw_text(text, x, y, color=WHITE, size="normal"):
    draw_spaced_line(text, x, y, color, size, 1)


def draw_centered_text(text, y, color=WHITE, size="normal", x=0, width=WIDTH):
    used_font = get_font(size)
    extra_spacing = 5 if size in ["big", "title"] else 2
    text_width = spaced_line_width(text, used_font, extra_spacing)
    text_x = x + (width - text_width) // 2
    draw_spaced_line(text, text_x, y, color, size, extra_spacing)


def wrap_text_lines(text, max_width, used_font):
    words = text.split(" ")
    lines = []
    line = ""

    for word in words:
        test_line = (line + " " + word).strip()

        if used_font.size(test_line)[0] <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines


def draw_wrapped_text(text, x, y, max_width, color=WHITE, size="small", line_gap=10, align="left", word_spacing=2):
    used_font = get_font(size)
    safe_width = max_width - 10
    lines = wrap_text_lines(text, safe_width, used_font)

    for line in lines:
        line_width = spaced_line_width(line, used_font, word_spacing)

        if align == "center":
            line_x = x + (max_width - line_width) // 2
        elif align == "right":
            line_x = x + max_width - line_width
        else:
            line_x = x

        draw_spaced_line(line, line_x, y, color, size, word_spacing)
        y += used_font.get_height() + line_gap

    return y - line_gap


def draw_panel_title(text, x, y, w, color=WHITE, size="normal"):
    draw_centered_text(text, y, color, size, x, w)


def draw_progress_bar(x, y, w, h, value, fill_color):
    value = max(0, min(1, value))
    bg_rect = pygame.Rect(x, y, w, h)
    fill_rect = pygame.Rect(x, y, int(w * value), h)

    pygame.draw.rect(screen, PROGRESS_BG, bg_rect, border_radius=10)
    pygame.draw.rect(screen, fill_color, fill_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, bg_rect, 2, border_radius=10)


def is_dark_colour(color):
    brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000
    return brightness < 120


def draw_cyber_background():
    screen.fill(DARK_BG)

    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (18, 35, 75), (x, 0), (x, HEIGHT), 1)

    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (18, 35, 75), (0, y), (WIDTH, y), 1)

    pygame.draw.circle(screen, (0, 80, 120), (850, 120), 75, 2)
    pygame.draw.circle(screen, (80, 40, 130), (130, 560), 95, 2)
    pygame.draw.circle(screen, (0, 100, 80), (500, 650), 120, 1)

    # Low particle count for better mobile performance.
    for _ in range(12):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, (0, 80, 120), (x, y), 1)


def draw_panel(x, y, w, h, border_color=NEON_BLUE):
    panel = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, CARD_BG, panel, border_radius=18)
    pygame.draw.rect(screen, border_color, panel, 2, border_radius=18)


def draw_button(text, x, y, w, h, color=NEON_GREEN):
    global mouse_clicked

    rect = pygame.Rect(x, y, w, h)
    hover = rect.collidepoint(pointer_pos)

    if hover:
        button_color = YELLOW
        text_color = BLACK
        border_color = WHITE
    else:
        button_color = color
        text_color = WHITE if is_dark_colour(color) else BLACK
        border_color = OPTION_BORDER if is_dark_colour(color) else NEON_BLUE

    pygame.draw.rect(screen, button_color, rect, border_radius=15)
    pygame.draw.rect(screen, border_color, rect, 3, border_radius=15)

    lines = wrap_text_lines(text, w - 34, small_font)
    total_height = len(lines) * small_font.get_height() + max(0, len(lines) - 1) * 6
    text_y = y + (h - total_height) // 2

    for line in lines:
        line_width = spaced_line_width(line, small_font, 2)
        text_x = x + (w - line_width) // 2
        draw_spaced_line(line, text_x, text_y, text_color, "small", 2)
        text_y += small_font.get_height() + 6

    if hover and mouse_clicked:
        play(click_sound)
        return True

    return False


def draw_quiz_option_button(index, text, x, y, w, h, accent_color):
    global mouse_clicked

    rect = pygame.Rect(x, y, w, h)
    hover = rect.collidepoint(pointer_pos)

    button_color = OPTION_HOVER if hover else OPTION_BG
    border_color = YELLOW if hover else accent_color
    text_color = BLACK if hover else WHITE
    number_color = BLACK if hover else YELLOW

    pygame.draw.rect(screen, button_color, rect, border_radius=16)
    pygame.draw.rect(screen, border_color, rect, 3, border_radius=16)

    number_rect = pygame.Rect(x + 14, y + 10, 42, h - 20)
    pygame.draw.rect(screen, border_color, number_rect, border_radius=12)
    draw_centered_text(str(index + 1), y + 15, number_color, "small", x + 14, 42)

    draw_wrapped_text(text, x + 72, y + 13, w - 92, text_color, "small", 4, "left", 3)

    if hover and mouse_clicked:
        play(click_sound)
        return True

    return False


def draw_hud():
    pygame.draw.rect(screen, DARK_PANEL, (0, 0, WIDTH, 82))
    pygame.draw.line(screen, NEON_BLUE, (0, 82), (WIDTH, 82), 3)

    draw_text("SCORE: " + str(score), 30, 25, NEON_BLUE, "small")
    draw_text("CREDITS: " + str(coins), 175, 25, NEON_GREEN, "small")
    draw_text("LIVES: " + str(lives), 320, 25, RED, "small")
    draw_text("HIGH SCORE: " + str(high_score), 520, 25, NEON_PURPLE, "small")
    draw_text("LEVEL: " + str(level + 1) + "/" + str(len(levels)), 800, 25, YELLOW, "small")


def create_particles(x, y, color):
    for _ in range(12):
        particles.append([
            x,
            y,
            random.randint(-4, 4),
            random.randint(-4, 4),
            random.randint(15, 30),
            color
        ])


def update_particles():
    for p in particles[:]:
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1

        if p[4] <= 0:
            particles.remove(p)
        else:
            pygame.draw.circle(screen, p[5], (int(p[0]), int(p[1])), 3)


def draw_mobile_controls():
    """Touch D-pad used on mobile browser and also works with mouse on desktop."""
    draw_centered_text("TOUCH CONTROLS", 580, GRAY, "small", 40, 260)

    controls = [
        (touch_left, "LEFT"),
        (touch_right, "RIGHT"),
        (touch_up, "UP"),
        (touch_down, "DOWN")
    ]

    for rect, label in controls:
        is_pressed = pointer_pressed and rect.collidepoint(pointer_pos)
        fill = OPTION_HOVER if is_pressed else OPTION_BG
        border = YELLOW if is_pressed else OPTION_BORDER

        pygame.draw.rect(screen, fill, rect, border_radius=15)
        pygame.draw.rect(screen, border, rect, 3, border_radius=15)

        short_label = {
            "LEFT": "←",
            "RIGHT": "→",
            "UP": "↑",
            "DOWN": "↓"
        }[label]

        draw_centered_text(short_label, rect.y + 13, WHITE if not is_pressed else BLACK, "normal", rect.x, rect.w)


def handle_touch_movement():
    """Move the player when the user holds a touch-control button."""
    if not pointer_pressed:
        return

    if touch_left.collidepoint(pointer_pos):
        player.x -= player_speed
    if touch_right.collidepoint(pointer_pos):
        player.x += player_speed
    if touch_up.collidepoint(pointer_pos):
        player.y -= player_speed
    if touch_down.collidepoint(pointer_pos):
        player.y += player_speed


# =========================
# CHARACTER DRAWING
# =========================
def draw_animated_player():
    global hero_frame

    hero_frame += 1
    bounce = int(math.sin(hero_frame * 0.15) * 4)

    pygame.draw.circle(screen, (0, 80, 120), (player.centerx, player.centery + bounce), 38)
    pygame.draw.circle(screen, NEON_BLUE, (player.centerx, player.y + 15 + bounce), 19)

    pygame.draw.rect(
        screen,
        NEON_GREEN,
        (player.x + 7, player.y + 32 + bounce, 28, 28),
        border_radius=8
    )

    pygame.draw.rect(
        screen,
        BLACK,
        (player.x + 11, player.y + 8 + bounce, 22, 8),
        border_radius=4
    )

    pygame.draw.circle(screen, WHITE, (player.x + 17, player.y + 12 + bounce), 3)
    pygame.draw.circle(screen, WHITE, (player.x + 27, player.y + 12 + bounce), 3)

    if hero_frame % 30 < 15:
        pygame.draw.line(screen, WHITE, (player.x + 12, player.y + 58 + bounce), (player.x + 5, player.y + 70), 3)
        pygame.draw.line(screen, WHITE, (player.x + 30, player.y + 58 + bounce), (player.x + 37, player.y + 70), 3)
    else:
        pygame.draw.line(screen, WHITE, (player.x + 12, player.y + 58 + bounce), (player.x + 16, player.y + 70), 3)
        pygame.draw.line(screen, WHITE, (player.x + 30, player.y + 58 + bounce), (player.x + 25, player.y + 70), 3)


def draw_enemy(name):
    pygame.draw.circle(screen, (120, 20, 40), enemy.center, 45)
    pygame.draw.rect(screen, RED, enemy, border_radius=12)
    pygame.draw.rect(screen, NEON_PINK, enemy, 3, border_radius=12)

    pygame.draw.circle(screen, BLACK, (enemy.x + 18, enemy.y + 20), 6)
    pygame.draw.circle(screen, BLACK, (enemy.x + 42, enemy.y + 20), 6)

    pygame.draw.circle(screen, WHITE, (enemy.x + 18, enemy.y + 20), 2)
    pygame.draw.circle(screen, WHITE, (enemy.x + 42, enemy.y + 20), 2)

    pygame.draw.line(screen, BLACK, (enemy.x + 15, enemy.y + 43), (enemy.x + 45, enemy.y + 43), 4)
    draw_wrapped_text(name, enemy.x - 50, enemy.y - 38, 160, RED, "small")


def draw_collectible(item):
    pygame.draw.circle(screen, YELLOW, item.center, 13)
    pygame.draw.circle(screen, ORANGE, item.center, 7)
    pygame.draw.circle(screen, WHITE, item.center, 3)


def create_safe_collectible():
    min_x = PLAY_AREA.left + COLLECTIBLE_PADDING
    max_x = PLAY_AREA.right - COLLECTIBLE_PADDING - COLLECTIBLE_SIZE
    min_y = PLAY_AREA.top + COLLECTIBLE_PADDING
    max_y = PLAY_AREA.bottom - COLLECTIBLE_PADDING - COLLECTIBLE_SIZE

    for _ in range(120):
        item = pygame.Rect(
            random.randint(min_x, max_x),
            random.randint(min_y, max_y),
            COLLECTIBLE_SIZE,
            COLLECTIBLE_SIZE
        )

        too_close_to_player = item.colliderect(player.inflate(120, 120))
        too_close_to_enemy = item.colliderect(enemy.inflate(110, 110))
        too_close_to_other_items = any(item.colliderect(other.inflate(55, 55)) for other in collectibles)

        if not too_close_to_player and not too_close_to_enemy and not too_close_to_other_items:
            return item

    return pygame.Rect(
        random.randint(min_x, max_x),
        random.randint(min_y, max_y),
        COLLECTIBLE_SIZE,
        COLLECTIBLE_SIZE
    )


# =========================
# GAME RESET
# =========================
def reset_game():
    global score, coins, level, lives, game_state, badges, selected_message
    global question_start_time, selected_quiz_option, mission_passed, completed_levels

    score = 0
    coins = 0
    level = 0
    lives = 3
    badges = []
    selected_message = ""
    question_start_time = 0
    selected_quiz_option = None
    mission_passed = False
    completed_levels.clear()
    game_state = "start"


def reset_mini_game():
    global player, enemy, collectibles, mini_collected, mini_start_time, enemy_direction, mission_passed

    mission_passed = False

    player.x = PLAY_AREA.left + 50
    player.y = PLAY_AREA.bottom - player.height - 15

    enemy.x = PLAY_AREA.right - enemy.width - 150
    enemy.y = random.randint(PLAY_AREA.top + 35, PLAY_AREA.bottom - enemy.height - 25)
    enemy_direction = 1

    mini_collected = 0
    mini_start_time = pygame.time.get_ticks()

    collectibles.clear()
    for _ in range(mini_target):
        collectibles.append(create_safe_collectible())


# =========================
# SCREENS
# =========================
def start_screen():
    draw_cyber_background()

    draw_centered_text("CYBERSHIELD ACADEMY", 62, NEON_BLUE, "big")
    draw_centered_text("TEEN DIGITAL DEFENDERS", 128, NEON_GREEN, "title")

    draw_panel(130, 195, 740, 285, NEON_PURPLE)
    draw_panel_title("WELCOME TO THE ACADEMY", 130, 225, 740, YELLOW, "small")

    draw_wrapped_text(
        "Train like a digital defender in a fast cyber-safety game made for teenagers. Complete missions, dodge online threats, answer quick safety questions, earn badges, and stop ShadowNet before it takes over the school network.",
        185,
        265,
        630,
        WHITE,
        "small",
        8,
        "center"
    )

    draw_panel_title("PLAYER ROLE", 130, 365, 740, NEON_BLUE, "small")
    draw_wrapped_text(
        "You are a CyberShield cadet. Your mission is to protect accounts, spot scams, keep private information safe, and make smart choices online.",
        220,
        400,
        560,
        WHITE,
        "small",
        8,
        "center"
    )

    if IS_BROWSER:
        draw_centered_text("Mobile browser mode: tap buttons and use touch controls.", 488, GRAY, "small")
    else:
        draw_centered_text("Desktop mode: use mouse and arrow keys.", 488, GRAY, "small")

    if draw_button("START GAME", 365, 525, 270, 60, NEON_GREEN):
        return "intro"

    if draw_button("QUIT", 420, 610, 160, 45, RED):
        pygame.quit()
        sys.exit()

    return "start"


def intro_screen():
    draw_cyber_background()

    draw_centered_text("PLAYER BRIEFING", 55, NEON_PURPLE, "title")
    draw_panel(80, 125, 840, 430, NEON_BLUE)

    lines = [
        "ShadowNet has launched a digital attack on the academy network.",
        "As a CyberShield cadet, you will complete six missions based on real online safety skills.",
        "Move your character, collect mission items, avoid enemies, and answer each question before time runs out.",
        "Your choices matter. Smart decisions earn badges and keep the network safe."
    ]

    y = 165
    for line in lines:
        y = draw_wrapped_text(line, 130, y, 760, WHITE, "small", 8, "center")
        y += 14

    draw_panel_title("CADET GEAR", 80, 345, 840, NEON_GREEN, "normal")

    tool_lines = [
        "Firewall Shield - blocks unsafe attacks",
        "Password Scanner - finds weak passwords",
        "Privacy Cloak - protects personal information",
        "2-Step Login Boost - adds extra account protection"
    ]

    y = 388
    for item in tool_lines:
        draw_wrapped_text("• " + item, 185, y, 630, WHITE, "small", 6, "center")
        y += 34

    if draw_button("CONTINUE", 390, 600, 220, 60, NEON_GREEN):
        return "concept"

    return "intro"


def concept_screen():
    draw_cyber_background()

    draw_centered_text("HOW TO PLAY", 55, NEON_BLUE, "title")
    draw_panel(85, 130, 830, 430, NEON_GREEN)

    lines = [
        "Desktop: use arrow keys to move your cadet around the mission zone.",
        "Mobile: hold the touch D-pad buttons to move your cadet.",
        "Collect all mission items before the timer reaches zero.",
        "Avoid enemies. Touching one will cost you a life.",
        "After every mission, answer a quick cyber-safety question."
    ]

    y = 175
    for line in lines:
        draw_panel(145, y - 8, 710, 42, NEON_BLUE)
        draw_wrapped_text(line, 175, y, 650, WHITE, "small", 6, "center")
        y += 68

    if draw_button("OPEN MISSION MAP", 340, 600, 320, 60, NEON_GREEN):
        return "map"

    return "concept"


def map_screen():
    global level

    draw_cyber_background()
    draw_hud()

    first_level_unlocked = 0 in completed_levels

    draw_centered_text("MISSION MAP", 110, YELLOW, "title")

    if first_level_unlocked:
        draw_centered_text("Level 1 unlocked the map. Choose any mission you want to play.", 165, WHITE, "small")
    else:
        draw_centered_text("Play Level 1 first to unlock the full mission map.", 165, WHITE, "small")

    zone_names = [
        "Password Power-Up",
        "Scam Message Zone",
        "Privacy Street",
        "Malware Rush",
        "Kindness Arena",
        "ShadowNet Showdown"
    ]

    x_positions = [80, 330, 620, 140, 430, 720]
    y_positions = [230, 230, 230, 415, 415, 415]

    for i, name in enumerate(zone_names):
        zone_rect = pygame.Rect(x_positions[i], y_positions[i], 210, 95)
        is_completed = i in completed_levels
        is_locked = not first_level_unlocked
        is_selected = first_level_unlocked and i == level and not is_completed
        is_hovered = zone_rect.collidepoint(pointer_pos) and first_level_unlocked

        if is_locked:
            color = ORANGE if i == 0 else GRAY
            status = "LOCKED"
        elif is_completed:
            color = NEON_GREEN
            status = "CLEARED"
        elif is_selected:
            color = YELLOW
            status = "SELECTED"
        else:
            color = NEON_BLUE if is_hovered else NEON_PURPLE
            status = "ACTIVE"

        draw_panel(x_positions[i], y_positions[i], 210, 95, color)
        draw_wrapped_text(name, x_positions[i] + 15, y_positions[i] + 22, 180, color, "small", 4, "center")
        draw_panel_title(status, x_positions[i], y_positions[i] + 65, 210, color, "small")

        if is_hovered and mouse_clicked:
            play(click_sound)
            level = i

    draw_panel(170, 540, 660, 58, NEON_PURPLE)

    if first_level_unlocked:
        draw_wrapped_text(
            "SELECTED MISSION: " + levels[level]["title"],
            205,
            558,
            590,
            WHITE,
            "small",
            6,
            "center"
        )
        button_text = "START SELECTED MISSION"
        button_color = NEON_GREEN
        button_x = 330
        button_w = 340
    else:
        level = 0
        draw_wrapped_text(
            "ENTRY CHALLENGE: Complete Level 1 once to unlock all other missions.",
            205,
            555,
            590,
            WHITE,
            "small",
            6,
            "center"
        )
        button_text = "PLAY LEVEL 1"
        button_color = ORANGE
        button_x = 380
        button_w = 240

    if draw_button(button_text, button_x, 615, button_w, 60, button_color):
        reset_mini_game()
        return "mini"

    return "map"


def mini_game_screen():
    global lives, coins, score, enemy_direction, selected_message

    current = levels[level]
    theme_color = current["theme"]

    draw_cyber_background()
    draw_hud()

    elapsed = (pygame.time.get_ticks() - mini_start_time) // 1000
    mission_time = 25
    time_left = max(0, mission_time - elapsed)
    timer_ratio = time_left / mission_time

    draw_centered_text(current["title"], 100, theme_color, "normal")
    draw_wrapped_text(current["zone"], 100, 135, 800, WHITE, "small", 7, "center", 3)

    draw_text("COLLECT: " + str(mini_target) + " " + current["item"], 55, 180, NEON_GREEN, "small")
    draw_text("TIME: " + str(time_left), 805, 100, RED, "small")
    draw_progress_bar(735, 135, 210, 18, timer_ratio, theme_color if timer_ratio > 0.35 else RED)
    draw_centered_text("Desktop: arrow keys  •  Mobile: touch D-pad  •  Avoid enemies", 200, GRAY, "small")

    pygame.draw.rect(screen, DARK_PANEL, PLAY_AREA, border_radius=20)
    pygame.draw.rect(screen, theme_color, PLAY_AREA, 2, border_radius=20)

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.x -= player_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.x += player_speed
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        player.y -= player_speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        player.y += player_speed

    handle_touch_movement()

    player.left = max(player.left, PLAY_AREA.left + 10)
    player.right = min(player.right, PLAY_AREA.right - 10)
    player.top = max(player.top, PLAY_AREA.top + 10)
    player.bottom = min(player.bottom, PLAY_AREA.bottom - 10)

    current_enemy_speed = enemy_speed + (level * 0.25)
    enemy.x += current_enemy_speed * enemy_direction

    if enemy.left <= PLAY_AREA.left + 20 or enemy.right >= PLAY_AREA.right - 20:
        enemy_direction *= -1
        enemy.y = random.randint(PLAY_AREA.top + 35, PLAY_AREA.bottom - enemy.height - 25)

    for item in collectibles[:]:
        draw_collectible(item)

        if player.colliderect(item):
            collectibles.remove(item)
            coins += 2
            score += 2
            create_particles(item.centerx, item.centery, YELLOW)
            play(coin_sound)

    draw_animated_player()
    draw_enemy(current["enemy"])
    update_particles()

    collected_now = mini_target - len(collectibles)
    draw_centered_text("COLLECTED: " + str(collected_now) + "/" + str(mini_target), 572, NEON_GREEN, "small")
    draw_progress_bar(390, 595, 220, 14, collected_now / mini_target, NEON_GREEN)

    draw_mobile_controls()

    if player.colliderect(enemy):
        lives -= 1
        play(wrong_sound)
        selected_message = "You touched an enemy and lost one life. Keep moving and try again!"
        create_particles(player.centerx, player.centery, RED)

        player.x = PLAY_AREA.left + 50
        player.y = PLAY_AREA.bottom - player.height - 15
        enemy.x = PLAY_AREA.right - enemy.width - 150

        if lives <= 0:
            return "end"

    if len(collectibles) == 0:
        play(correct_sound)
        score += 5
        return "quiz"

    if time_left <= 0:
        lives -= 1
        selected_message = "Mission timer ended. You lost one life, but you can recover on the next try."
        play(wrong_sound)

        if lives <= 0:
            return "end"

        return "map"

    return "mini"


def quiz_screen():
    global score, coins, level, selected_message, lives
    global question_start_time, selected_quiz_option, mission_passed

    current = levels[level]
    theme_color = current["theme"]

    draw_cyber_background()
    draw_hud()

    if question_start_time == 0:
        question_start_time = pygame.time.get_ticks()

    elapsed = (pygame.time.get_ticks() - question_start_time) // 1000
    question_time = 15
    time_left = max(0, question_time - elapsed)
    timer_ratio = time_left / question_time

    draw_centered_text(current["title"], 102, theme_color, "title")
    draw_centered_text("QUESTION TIMER: " + str(time_left), 153, RED, "small")
    draw_progress_bar(365, 176, 270, 16, timer_ratio, theme_color if timer_ratio > 0.35 else RED)

    draw_panel(55, 205, 890, 420, theme_color)

    draw_panel_title("MISSION STORY", 55, 230, 890, NEON_BLUE, "normal")
    draw_wrapped_text(current["story"], 105, 267, 790, WHITE, "small", 7, "center", 3)

    draw_panel_title("QUESTION", 55, 325, 890, NEON_GREEN, "normal")
    draw_wrapped_text(current["question"], 105, 360, 790, WHITE, "small", 7, "center", 3)
    draw_centered_text("Choose with mouse/touch or press keys 1 - 4", 400, GRAY, "small")

    y = 428
    for i, option in enumerate(current["options"]):
        clicked = draw_quiz_option_button(i, option, 110, y, 780, 48, theme_color)
        key_selected = selected_quiz_option == i

        if clicked or key_selected:
            question_start_time = 0
            selected_quiz_option = None

            if i == current["answer"]:
                mission_passed = True
                score += 10
                coins += 5

                if current["badge"] not in badges:
                    badges.append(current["badge"])

                selected_message = "Correct! Badge earned: " + current["badge"] + ". " + current["lesson"]
                play(correct_sound)
            else:
                mission_passed = False
                lives -= 1
                selected_message = "Wrong choice. " + current["lesson"]
                play(wrong_sound)

                if lives <= 0:
                    return "end"

            return "result"

        y += 56

    if time_left <= 0:
        question_start_time = 0
        selected_quiz_option = None
        mission_passed = False
        lives -= 1
        selected_message = "Time over! " + current["lesson"]
        play(wrong_sound)

        if lives <= 0:
            return "end"

        return "result"

    return "quiz"


def result_screen():
    global level, mission_passed, completed_levels

    draw_cyber_background()
    draw_hud()

    if mission_passed:
        completed_levels.add(level)
        all_unlocked_missions_done = len(completed_levels) >= len(levels)
        title_text = "MISSION PASSED"
        button_text = "VIEW FINAL REPORT" if all_unlocked_missions_done else "BACK TO MAP"
        title_color = NEON_GREEN
    else:
        all_unlocked_missions_done = False
        title_text = "MISSION NOT PASSED"
        button_text = "RETRY MISSION"
        title_color = ORANGE

    draw_centered_text(title_text, 110, title_color, "title")

    draw_panel(85, 180, 830, 330, title_color)
    draw_wrapped_text(selected_message, 135, 225, 730, WHITE, "small", 8, "center")

    if mission_passed:
        draw_panel_title("TOOLS USED", 85, 330, 830, NEON_BLUE, "normal")

        y = 372
        for tool in tools:
            draw_wrapped_text("• " + tool, 180, y, 640, WHITE, "small", 6, "center")
            y += 35
    else:
        draw_panel_title("TRY AGAIN TIP", 85, 330, 830, NEON_BLUE, "normal")
        draw_wrapped_text(
            "Complete the mission item collection again, then answer the question correctly to pass this mission.",
            180,
            375,
            640,
            WHITE,
            "small",
            6,
            "center"
        )

    if draw_button(button_text, 375, 590, 250, 60, NEON_BLUE if mission_passed else ORANGE):
        if mission_passed:
            passed_level = level
            mission_passed = False

            if all_unlocked_missions_done:
                play(win_sound)
                return "end"

            if passed_level == 0:
                level = 1

            return "map"

        reset_mini_game()
        return "mini"

    return "result"


def end_screen():
    global high_score

    draw_cyber_background()

    if score > high_score:
        high_score = score
        save_high_score(high_score)

    draw_centered_text("GAME COMPLETE", 55, NEON_PURPLE, "big")
    draw_panel(110, 135, 780, 430, NEON_BLUE)

    draw_centered_text("FINAL REPORT", 165, YELLOW, "normal", 110, 780)
    draw_centered_text("FINAL SCORE: " + str(score), 210, NEON_BLUE, "normal", 110, 780)
    draw_centered_text("DEFENDER CREDITS: " + str(coins), 250, NEON_GREEN, "normal", 110, 780)
    draw_centered_text("HIGH SCORE: " + str(high_score), 290, NEON_PURPLE, "normal", 110, 780)

    if lives <= 0:
        ending = "ShadowNet broke through this time. Replay the academy missions and level up your cyber skills."
        rank = "Rookie Cadet"
        rank_color = RED
    elif score >= 85:
        ending = "Amazing work! You stopped ShadowNet, protected the academy, and proved you are a top digital defender."
        rank = "Elite Teen Defender"
        rank_color = YELLOW
    elif score >= 65:
        ending = "Great job! You stopped most of ShadowNet's attack and made strong cyber-safety decisions."
        rank = "CyberShield Hero"
        rank_color = NEON_GREEN
    elif score >= 45:
        ending = "Good effort! You protected key parts of the network, but a few skills still need practice."
        rank = "Skilled Cadet"
        rank_color = NEON_BLUE
    else:
        ending = "You completed the basics. Try again to earn more badges and improve your score."
        rank = "New Defender"
        rank_color = WHITE

    draw_centered_text("RANK: " + rank, 335, rank_color, "normal", 110, 780)
    draw_wrapped_text(ending, 170, 380, 660, WHITE, "small", 8, "center")

    draw_centered_text("BADGES EARNED", 442, NEON_GREEN, "small", 110, 780)

    y = 472
    if badges:
        for badge in badges[:4]:
            draw_wrapped_text("• " + badge, 220, y, 560, WHITE, "small", 4, "center")
            y += 25
    else:
        draw_centered_text("No badges earned yet.", y, WHITE, "small", 110, 780)

    if draw_button("PLAY AGAIN", 260, 610, 230, 55, NEON_GREEN):
        reset_game()
        return "start"

    if draw_button("QUIT GAME", 520, 610, 220, 55, RED):
        pygame.quit()
        sys.exit()

    return "end"


# =========================
# INPUT HELPERS
# =========================
def finger_to_screen(event):
    """Convert mobile touch coordinate from 0..1 into game screen coordinates."""
    return int(event.x * WIDTH), int(event.y * HEIGHT)


def update_input_from_event(event):
    global mouse_clicked, pointer_pressed, pointer_pos, selected_quiz_option, game_state

    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

    if IS_BROWSER and event.type == pygame.VIDEORESIZE:
        update_display_size(event.w, event.h)

    if event.type == pygame.MOUSEMOTION:
        pointer_pos = screen_to_game_pos(event.pos)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        pointer_pressed = True
        mouse_clicked = True
        pointer_pos = screen_to_game_pos(event.pos)

    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        pointer_pressed = False
        pointer_pos = screen_to_game_pos(event.pos)

    if event.type == pygame.FINGERDOWN:
        pointer_pressed = True
        mouse_clicked = True
        pointer_pos = finger_to_screen(event)

    if event.type == pygame.FINGERMOTION:
        pointer_pressed = True
        pointer_pos = finger_to_screen(event)

    if event.type == pygame.FINGERUP:
        pointer_pressed = False
        pointer_pos = finger_to_screen(event)

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

        if event.key == pygame.K_r and game_state == "end":
            reset_game()

        if game_state == "quiz":
            if event.key == pygame.K_1:
                selected_quiz_option = 0
            elif event.key == pygame.K_2:
                selected_quiz_option = 1
            elif event.key == pygame.K_3:
                selected_quiz_option = 2
            elif event.key == pygame.K_4:
                selected_quiz_option = 3


# =========================
# MAIN GAME LOOP
# =========================
async def main():
    global mouse_clicked, pointer_pos, game_state

    while True:
        mouse_clicked = False

        # Desktop mouse hover support. In browser/mobile, convert real screen
        # coordinates back into the virtual 1000x700 game coordinates.
        if not pointer_pressed:
            try:
                pointer_pos = screen_to_game_pos(pygame.mouse.get_pos())
            except Exception:
                pass

        for event in pygame.event.get():
            update_input_from_event(event)

        if game_state == "start":
            game_state = start_screen()

        elif game_state == "intro":
            game_state = intro_screen()

        elif game_state == "concept":
            game_state = concept_screen()

        elif game_state == "map":
            game_state = map_screen()

        elif game_state == "mini":
            game_state = mini_game_screen()

        elif game_state == "quiz":
            game_state = quiz_screen()

        elif game_state == "result":
            game_state = result_screen()

        elif game_state == "end":
            game_state = end_screen()

        present_frame()
        clock.tick(60)

        # Required for Pygbag/mobile browser. Also works on desktop.
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
