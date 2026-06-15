import os
import random
import time

import pgzrun
import pygame
from pygame import Rect


WIDTH = 1366
HEIGHT = 768
TITLE = "The Chicken Across the Street: Coleta Seletiva"
BASE_WIDTH = 768
UI_OFFSET_X = (WIDTH - BASE_WIDTH) // 2

ASSET_DIR = "images"
CATEGORY_COLORS = {
    "plastico": "#d94b4b",
    "papel": "#3f83d6",
    "metal": "#e3c63b",
    "vidro": "#3ca66b",
    "organico": "#9a6638",
}
CATEGORY_LABELS = {
    "plastico": "Plástico",
    "papel": "Papel",
    "metal": "Metal",
    "vidro": "Vidro",
    "organico": "Orgânico",
}
CATEGORY_REASONS = {
    "plastico": "materiais plásticos recicláveis devem ir na lixeira vermelha.",
    "papel": "papéis limpos devem ir na lixeira azul.",
    "metal": "latas e objetos metálicos devem ir na lixeira amarela.",
    "vidro": "garrafas e potes de vidro devem ir na lixeira verde.",
    "organico": "restos de comida viram adubo na lixeira marrom.",
}

music.set_volume(0.3)
sound_on = True
music_on = True
game_state = "menu"
previous_game_state = "menu"
level_index = 0
score = 0
feedback_text = ""
feedback_timer = 0
feedback_icon = None
dragging_item = None
drag_offset = (0, 0)
level_started_at = 0
map_transition_from = 0
map_transition_to = 0
map_transition_timer = 0

scaled_cache = {}
ui_cache = {}
SOUND_RECT = Rect(WIDTH - 66, 16, 50, 50)
BUTTON_CROP = Rect(170, 340, 700, 290)
ICON_CROP = Rect(270, 245, 500, 520)
SOUND_CROP = Rect(300, 285, 430, 430)
BANNER_CROP = Rect(80, 285, 870, 380)
DRAG_ITEM_SIZE = 46
MAP_TRANSITION_DURATION = 300
MAP_POINTS = [
    (118, 604),
    (347, 604),
    (553, 604),
    (767, 604),
    (983, 604),
    (1227, 604),
]


def load_scaled(name, size):
    key = (name, size)
    if key not in scaled_cache:
        filename = os.path.join(ASSET_DIR, f"{name}.png")
        surface = pygame.image.load(filename)
        scaled_cache[key] = pygame.transform.smoothscale(surface, size)
    return scaled_cache[key]


def blit_scaled(name, pos, size):
    screen.surface.blit(load_scaled(name, size), pos)


def draw_road_background():
    blit_scaled("road_bg", (0, 0), (WIDTH, HEIGHT))


def draw_map_background():
    blit_scaled("maps_bg", (0, 0), (WIDTH, HEIGHT))


def load_ui_scaled(name, size, crop):
    crop_key = (crop.x, crop.y, crop.width, crop.height)
    key = (name, size, crop_key)
    if key not in ui_cache:
        filename = os.path.join(ASSET_DIR, f"{name}.png")
        surface = pygame.image.load(filename).convert_alpha()
        cropped = surface.subsurface(crop).copy()
        ui_cache[key] = pygame.transform.smoothscale(cropped, size)
    return ui_cache[key]


def blit_ui(name, pos, size, crop):
    screen.surface.blit(load_ui_scaled(name, size, crop), pos)


def draw_asset_button(name, rect):
    blit_ui(name, rect.topleft, rect.size, BUTTON_CROP)


def draw_sound_toggle():
    name = "sound_on" if sound_on else "sound_off"
    blit_ui(name, SOUND_RECT.topleft, SOUND_RECT.size, SOUND_CROP)


def draw_panel(rect, color=(20, 45, 40), alpha=218, border="#d7f7d2"):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((*color, alpha))
    screen.surface.blit(panel, rect.topleft)
    screen.draw.rect(rect, border)


def draw_wood_panel(rect):
    screen.draw.filled_rect(rect, "#7b431e")
    screen.draw.rect(rect, "#1b120b")
    inner = Rect(rect.x + 5, rect.y + 5, rect.width - 10, rect.height - 10)
    screen.draw.rect(inner, "#c07a34")
    for y in range(rect.y + 18, rect.bottom - 8, 20):
        screen.draw.line((rect.x + 10, y), (rect.right - 10, y), "#5a2e16")


def wrap_lines(text, width, fontsize):
    words = text.split()
    lines = []
    current = ""
    max_chars = max(10, width // max(8, fontsize // 2))
    for word in words:
        test = f"{current} {word}".strip()
        if len(test) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(text, x, y, width, fontsize=28, color="white", line_height=34):
    lines = wrap_lines(text, width, fontsize)
    for i, line in enumerate(lines):
        screen.draw.text(line, (x, y + i * line_height), fontsize=fontsize, color=color)
    return y + len(lines) * line_height


def draw_text_in_box(text, rect, fontsize=22, color="#fff1c7", icon=None):
    icon_space = 54 if icon else 0
    text_rect = Rect(rect.x + 16 + icon_space, rect.y + 12, rect.width - 32 - icon_space, rect.height - 24)
    while fontsize >= 14:
        line_height = fontsize + 4
        lines = wrap_lines(text, text_rect.width, fontsize)
        if len(lines) * line_height <= text_rect.height:
            break
        fontsize -= 1
    max_lines = max(1, text_rect.height // (fontsize + 4))
    lines = wrap_lines(text, text_rect.width, fontsize)[:max_lines]
    old_clip = screen.surface.get_clip()
    screen.surface.set_clip(rect)
    if icon:
        blit_ui(icon, (rect.x + 14, rect.y + rect.height // 2 - 20), (40, 40), ICON_CROP)
    for i, line in enumerate(lines):
        screen.draw.text(line, (text_rect.x, text_rect.y + i * (fontsize + 4)), fontsize=fontsize, color=color)
    screen.surface.set_clip(old_clip)


def button_rect(cx, cy, w=228, h=74):
    return Rect(cx - w // 2, cy - h // 2, w, h)


def centered_rect(x, y, w, h):
    return Rect(x + UI_OFFSET_X, y, w, h)


def centered_pos(x, y):
    return x + UI_OFFSET_X, y


class Chicken:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 74
        self.speed = 3
        self.image = "chicken_idle1"
        self.frame = 0
        self.frame_timer = 0
        self.hitbox = Rect(self.x - 18, self.y - 18, 36, 36)

    def move(self):
        moved = False
        if keyboard.up or keyboard.w:
            self.y -= self.speed
            moved = True
        if keyboard.down or keyboard.s:
            self.y += self.speed
            moved = True
        if keyboard.left or keyboard.a:
            self.x -= self.speed
            moved = True
        if keyboard.right or keyboard.d:
            self.x += self.speed
            moved = True

        self.x = max(28, min(WIDTH - 28, self.x))
        self.y = max(34, min(HEIGHT - 34, self.y))
        self.hitbox = Rect(self.x - 18, self.y - 18, 36, 36)

        if moved:
            self.frame_timer += 1
            if self.frame_timer >= 9:
                self.frame_timer = 0
                self.frame = (self.frame + 1) % 2
                self.image = ["chicken_walk1", "chicken_walk2"][self.frame]
        else:
            self.image = "chicken_idle1"

    def draw(self):
        blit_scaled(self.image, (self.x - 28, self.y - 28), (56, 56))


class Car:
    def __init__(self, y, speed_min, speed_max, delay=0):
        self.y = y
        self.x = WIDTH + delay + random.randint(0, 260)
        self.speed_min = speed_min
        self.speed_max = speed_max
        self.speed = random.uniform(speed_min, speed_max)
        self.hitbox = Rect(self.x + 22, self.y + 54, 148, 74)

    def move(self):
        self.x -= self.speed
        if self.x < -220:
            self.x = WIDTH + random.randint(80, 330)
            self.speed = random.uniform(self.speed_min, self.speed_max)
        self.hitbox = Rect(self.x + 22, self.y + 54, 148, 74)

    def draw(self):
        blit_scaled("car1", (self.x, self.y), (190, 190))


class Waste:
    def __init__(self, name, label, category, pos):
        self.name = name
        self.label = label
        self.category = category
        self.x, self.y = pos
        self.collected = False
        self.discarded = False
        self.first_try = True
        self.drag_pos = [0, 0]
        self.home_pos = [0, 0]
        self.rect = Rect(self.x - 24, self.y - 24, 48, 48)

    def collect(self):
        self.collected = True

    def draw_on_road(self):
        if not self.collected:
            blit_scaled(self.name, (self.x - 23, self.y - 23), (46, 46))

    def draw_drag(self):
        if not self.discarded:
            blit_scaled(self.name, self.drag_pos, (DRAG_ITEM_SIZE, DRAG_ITEM_SIZE))

    def drag_rect(self):
        return Rect(self.drag_pos[0], self.drag_pos[1], DRAG_ITEM_SIZE, DRAG_ITEM_SIZE)


class Bin:
    def __init__(self, category, rect):
        self.category = category
        self.rect = rect


LEVELS = [
    {
        "title": "Fase 1: Plástico",
        "focus": "Atravesse a rua, colete garrafas PET e sacolas plásticas. Depois descarte tudo na lixeira vermelha.",
        "cars": 2,
        "speed": (1.8, 3.0),
        "wastes": [
            ("garrafa_pet_1", "garrafa PET", "plastico", (210, 455)),
            ("sacola_plastica_2", "sacola plástica", "plastico", (530, 300)),
        ],
    },
    {
        "title": "Fase 2: Papel",
        "focus": "Atravesse a rua com cuidado. Papel limpo pode ser reciclado: procure papéis, jornais e papelão.",
        "cars": 3,
        "speed": (2.2, 3.8),
        "wastes": [
            ("papel_amassado_1", "papel amassado", "papel", (180, 505)),
            ("jornal_1", "jornal", "papel", (470, 382)),
            ("caixa_papelao_1", "caixa de papelão", "papel", (330, 250)),
        ],
    },
    {
        "title": "Fase 3: Metal",
        "focus": "Atravesse a rua, evite os carros e colete metais. Latas e tampas metálicas vão para a lixeira amarela.",
        "cars": 4,
        "speed": (2.7, 4.6),
        "wastes": [
            ("lata_metal_1", "lata de metal", "metal", (180, 485)),
            ("lata_metal_2", "lata de alumínio", "metal", (585, 395)),
            ("lata_metal_1", "tampa metálica", "metal", (340, 285)),
        ],
    },
    {
        "title": "Fase 4: Vidro",
        "focus": "Atravesse a rua planejando sua rota. Vidros recicláveis precisam da lixeira verde.",
        "cars": 4,
        "speed": (3.0, 5.1),
        "wastes": [
            ("garrafa_vidro_1", "garrafa de vidro", "vidro", (560, 512)),
            ("pote_vidro_1", "pote de vidro", "vidro", (180, 372)),
            ("garrafa_vidro_1", "frasco de vidro", "vidro", (390, 242)),
        ],
    },
    {
        "title": "Fase 5: Orgânico",
        "focus": "Restos de comida e cascas podem virar adubo. Leve tudo para a lixeira marrom.",
        "cars": 5,
        "speed": (3.1, 5.3),
        "wastes": [
            ("casca_banana_1", "casca de banana", "organico", (180, 520)),
            ("maca_mordida_1", "maçã mordida", "organico", (560, 430)),
            ("resto_comida_1", "resto de comida", "organico", (280, 330)),
            ("casca_banana_1", "casca de fruta", "organico", (500, 230)),
        ],
    },
    {
        "title": "Fase 6: Revisão geral",
        "focus": "Atravesse a rua e revise tudo: separe plástico, papel, metal, vidro e orgânico.",
        "cars": 5,
        "speed": (3.5, 6.0),
        "wastes": [
            ("garrafa_pet_2", "garrafa PET", "plastico", (160, 525)),
            ("jornal_1", "jornal", "papel", (575, 468)),
            ("lata_metal_2", "lata de metal", "metal", (260, 385)),
            ("pote_vidro_1", "pote de vidro", "vidro", (525, 300)),
            ("casca_banana_1", "casca de banana", "organico", (340, 210)),
        ],
    },
]


chicken = Chicken()
cars = []
wastes = []
bins = []
level_stats = []
current_stats = {}


def current_level():
    return LEVELS[level_index]


def set_feedback(text, duration=180, icon=None):
    global feedback_text, feedback_timer, feedback_icon
    feedback_text = text
    feedback_timer = duration
    feedback_icon = icon


def build_cars():
    level = current_level()
    rows = [170, 270, 370, 470, 565][: level["cars"]]
    return [Car(y, level["speed"][0], level["speed"][1], i * 190) for i, y in enumerate(rows)]


def build_wastes():
    built_wastes = []
    for name, label, category, pos in current_level()["wastes"]:
        scaled_pos = (int(pos[0] * WIDTH / BASE_WIDTH), pos[1])
        built_wastes.append(Waste(name, label, category, scaled_pos))
    return built_wastes


def start_level(index=None):
    global level_index, chicken, cars, wastes, game_state, score, level_started_at, current_stats
    if index is not None:
        level_index = index
    chicken = Chicken()
    cars = build_cars()
    wastes = build_wastes()
    score = 0
    level_started_at = time.time()
    current_stats = {
        "level": level_index + 1,
        "collected": 0,
        "correct_discards": 0,
        "wrong_discards": 0,
        "first_try_discards": 0,
        "time": 0,
        "stars": 0,
    }
    set_feedback(current_level()["focus"], 240)
    game_state = "intro"


def restart_current_level():
    start_level(level_index)


def start_map_transition(from_index, to_index):
    global game_state, map_transition_from, map_transition_to, map_transition_timer
    map_transition_from = from_index
    map_transition_to = to_index
    map_transition_timer = 0
    game_state = "map_transition"


def request_menu_confirmation():
    global game_state, previous_game_state
    if game_state == "menu":
        return
    previous_game_state = game_state
    game_state = "confirm_menu"


def confirm_go_to_menu():
    global game_state, dragging_item
    dragging_item = None
    game_state = "menu"


def cancel_menu_confirmation():
    global game_state
    game_state = previous_game_state


def prepare_sorting():
    global bins, game_state
    scale_x = WIDTH / BASE_WIDTH
    bins = [
        Bin("papel", Rect(int(45 * scale_x), 330, int(130 * scale_x), 335)),
        Bin("plastico", Rect(int(184 * scale_x), 330, int(130 * scale_x), 335)),
        Bin("metal", Rect(int(323 * scale_x), 330, int(130 * scale_x), 335)),
        Bin("vidro", Rect(int(462 * scale_x), 330, int(130 * scale_x), 335)),
        Bin("organico", Rect(int(600 * scale_x), 330, int(130 * scale_x), 335)),
    ]

    collected = [item for item in wastes if item.collected]
    for i, item in enumerate(collected):
        item.home_pos = [UI_OFFSET_X + 26 + i * 54, 700]
        item.drag_pos = item.home_pos[:]
    set_feedback("Arraste cada resíduo para a lixeira correta.", 210)
    game_state = "sorting"


def collected_count():
    return sum(1 for item in wastes if item.collected)


def all_collected():
    return all(item.collected for item in wastes)


def all_discarded():
    return all(item.discarded for item in wastes if item.collected)


def finish_level():
    global game_state
    current_stats["time"] = int(time.time() - level_started_at)
    errors = current_stats["wrong_discards"]
    if errors == 0:
        stars = 3
    elif errors <= 2:
        stars = 2
    else:
        stars = 1
    current_stats["stars"] = stars
    level_stats.append(current_stats.copy())
    set_feedback("Parabéns! Você ajudou a manter a cidade limpa.", 240, "correct_icon")
    game_state = "level_complete"


def draw_menu():
    draw_road_background()
    draw_wood_panel(centered_rect(78, 72, 612, 560))
    screen.draw.text("The Chicken Across the Street", center=(WIDTH // 2, 128), fontsize=44, color="#fff1c7")
    screen.draw.text("Coleta seletiva", center=(WIDTH // 2, 178), fontsize=40, color="#ffe08a")
    draw_asset_button("button_start", button_rect(WIDTH // 2, 284))
    draw_asset_button("button_how_to_play", button_rect(WIDTH // 2, 382))
    draw_asset_button("button_exit", button_rect(WIDTH // 2, 480))


def draw_how_to_play():
    draw_road_background()
    draw_wood_panel(centered_rect(54, 58, 660, 596))
    screen.draw.text("Como jogar", center=(WIDTH // 2, 104), fontsize=46, color="#fff1c7")
    text = (
        "Use as setas ou WASD para mover a galinha. O objetivo é atravessar a rua "
        "com atenção, coletar todos os resíduos da fase e chegar ao outro lado. "
        "Depois, arraste cada item para a lixeira correta: plástico, papel, metal, "
        "vidro ou orgânico. O jogo mostra dicas para você aprender com cada tentativa."
    )
    draw_text_in_box(text, centered_rect(92, 154, 584, 330), fontsize=28)
    draw_asset_button("button_menu", button_rect(WIDTH // 2, 585))


def draw_intro():
    draw_road_background()
    draw_wood_panel(centered_rect(58, 96, 652, 470))
    level = current_level()
    screen.draw.text(level["title"], center=(WIDTH // 2, 150), fontsize=44, color="#fff1c7")
    draw_text_in_box(level["focus"], centered_rect(96, 198, 576, 120), fontsize=30)
    draw_text_in_box("Objetivo: atravesse a rua, recolha todos os resíduos, evite os carros e faça o descarte correto.", centered_rect(96, 342, 576, 96), fontsize=27)
    draw_asset_button("button_start", button_rect(WIDTH // 2, 505))


def draw_hud():
    level = current_level()
    draw_wood_panel(centered_rect(12, 10, 744, 58))
    screen.draw.text(level["title"], centered_pos(26, 24), fontsize=24, color="#fff1c7")
    screen.draw.text(f"Coletados: {collected_count()}/{len(wastes)}", centered_pos(330, 24), fontsize=24, color="#ffe08a")
    screen.draw.text(f"Pontos: {score}", centered_pos(555, 24), fontsize=24, color="#ffd447")


def draw_playing():
    draw_road_background()
    for item in wastes:
        item.draw_on_road()
    for car in cars:
        car.draw()
    chicken.draw()
    draw_hud()
    if feedback_timer > 0:
        feedback_rect = centered_rect(60, 680, 648, 64)
        draw_wood_panel(feedback_rect)
        draw_text_in_box(feedback_text, feedback_rect, fontsize=23, icon=feedback_icon)


def draw_gameover():
    draw_road_background()
    draw_wood_panel(centered_rect(74, 150, 620, 470))
    screen.draw.text("A galinha foi atropelada!", center=(WIDTH // 2, 220), fontsize=36, color="#ffd6c2")
    draw_text_in_box("Observe o trânsito, espere uma abertura segura e tente novamente.", centered_rect(112, 262, 544, 112), fontsize=28)
    blit_ui("wrong_icon", (WIDTH // 2 - 42, 388), (84, 84), ICON_CROP)
    draw_asset_button("button_restart", button_rect(WIDTH // 2, 500))
    draw_asset_button("button_menu", button_rect(WIDTH // 2, 575))


def draw_sorting():
    try:
        blit_scaled("lixeira_BG", (0, 0), (WIDTH, HEIGHT))
    except FileNotFoundError:
        draw_road_background()
    draw_wood_panel(centered_rect(14, 642, 302, 112))
    screen.draw.text("ITENS", center=(UI_OFFSET_X + 165, 662), fontsize=22, color="#fff1c7")
    for item in wastes:
        if item.collected and not item.discarded and item is not dragging_item:
            item.draw_drag()
    if dragging_item is not None:
        dragging_item.draw_drag()
    feedback_rect = centered_rect(330, 642, 424, 112)
    draw_wood_panel(feedback_rect)
    draw_text_in_box(
        feedback_text or "Arraste os resíduos para as lixeiras.",
        feedback_rect,
        fontsize=22,
        icon=feedback_icon,
    )


def draw_stars(stars, y):
    for i in range(3):
        name = "star_full" if i < stars else "star_empty"
        blit_scaled(name, (WIDTH // 2 - 144 + i * 102, y), (84, 84))


def draw_level_complete():
    draw_road_background()
    draw_wood_panel(centered_rect(58, 86, 652, 560))
    blit_ui("congratulations_banner", (WIDTH // 2 - 250, 92), (500, 218), BANNER_CROP)
    draw_stars(current_stats["stars"], 278)
    screen.draw.text(f"Pontos: {score}", center=(WIDTH // 2, 382), fontsize=32, color="#f3d24f")
    screen.draw.text(f"Descartes corretos: {current_stats['correct_discards']}", center=(WIDTH // 2, 428), fontsize=28, color="#fff1c7")
    screen.draw.text(f"Tentativas para corrigir: {current_stats['wrong_discards']}", center=(WIDTH // 2, 468), fontsize=28, color="#fff1c7")
    draw_text_in_box("Parabéns! Você ajudou a manter a cidade limpa.", centered_rect(118, 496, 532, 58), fontsize=28)
    if level_index < len(LEVELS) - 1:
        draw_asset_button("button_next", button_rect(WIDTH // 2 - 130, 594))
    else:
        draw_asset_button("button_next", button_rect(WIDTH // 2 - 130, 594))
    draw_asset_button("button_menu", button_rect(WIDTH // 2 + 130, 594))


def draw_game_complete():
    draw_road_background()
    draw_wood_panel(centered_rect(48, 54, 672, 650))
    screen.draw.text("Você concluiu o jogo!", center=(WIDTH // 2, 108), fontsize=44, color="#fff1c7")
    total_correct = sum(item["correct_discards"] for item in level_stats)
    total_wrong = sum(item["wrong_discards"] for item in level_stats)
    total_stars = sum(item["stars"] for item in level_stats)
    draw_text_in_box("Agora você sabe atravessar com atenção, coletar resíduos do cotidiano e escolher a lixeira correta.", centered_rect(88, 150, 592, 88), fontsize=28)
    screen.draw.text(f"Resíduos classificados: {total_correct}", center=(WIDTH // 2, 282), fontsize=30, color="#fff1c7")
    screen.draw.text(f"Erros corrigidos com aprendizagem: {total_wrong}", center=(WIDTH // 2, 326), fontsize=30, color="#fff1c7")
    screen.draw.text(f"Estrelas conquistadas: {total_stars}/{len(LEVELS) * 3}", center=(WIDTH // 2, 370), fontsize=30, color="#f3d24f")
    draw_text_in_box("Evidências de aprendizagem: você atravessou a rua, coletou resíduos, comparou materiais, corrigiu tentativas e aplicou a coleta seletiva na fase de revisão.", centered_rect(88, 414, 592, 116), fontsize=24)
    draw_asset_button("button_restart", button_rect(WIDTH // 2 - 130, 638))
    draw_asset_button("button_menu", button_rect(WIDTH // 2 + 130, 638))


def draw_confirm_menu():
    if previous_game_state == "sorting":
        draw_sorting()
    elif previous_game_state == "level_complete":
        draw_level_complete()
    elif previous_game_state == "game_complete":
        draw_game_complete()
    elif previous_game_state == "gameover":
        draw_gameover()
    elif previous_game_state == "map_transition":
        draw_map_transition()
    elif previous_game_state == "how_to_play":
        draw_how_to_play()
    elif previous_game_state == "intro":
        draw_intro()
    else:
        draw_playing()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.surface.blit(overlay, (0, 0))
    panel = centered_rect(108, 206, 552, 310)
    draw_wood_panel(panel)
    screen.draw.text("Voltar ao menu?", center=(WIDTH // 2, 260), fontsize=42, color="#fff1c7")
    draw_text_in_box(
        "Seu progresso da fase atual será perdido. Deseja mesmo retornar ao menu?",
        centered_rect(150, 304, 468, 92),
        fontsize=27,
    )
    draw_asset_button("button_menu", button_rect(WIDTH // 2 - 130, 450))
    draw_asset_button("button_next", button_rect(WIDTH // 2 + 130, 450))


def draw_map_transition():
    progress = min(1, map_transition_timer / MAP_TRANSITION_DURATION)
    start_x, start_y = MAP_POINTS[map_transition_from]
    end_x, end_y = MAP_POINTS[map_transition_to]
    eased = progress * progress * (3 - 2 * progress)
    chicken_x = start_x + (end_x - start_x) * eased
    chicken_y = start_y + (end_y - start_y) * eased - 54
    frame = "chicken_walk1" if (map_transition_timer // 12) % 2 == 0 else "chicken_walk2"

    draw_map_background()
    blit_scaled(frame, (chicken_x - 28, chicken_y - 28), (56, 56))
    draw_wood_panel(Rect(WIDTH // 2 - 196, 660, 392, 68))
    draw_text_in_box(
        f"Indo da fase {map_transition_from + 1} para a fase {map_transition_to + 1}...",
        Rect(WIDTH // 2 - 180, 668, 360, 52),
        fontsize=24,
    )


def draw():
    screen.clear()
    if game_state == "menu":
        draw_menu()
    elif game_state == "how_to_play":
        draw_how_to_play()
    elif game_state == "intro":
        draw_intro()
    elif game_state == "playing":
        draw_playing()
    elif game_state == "gameover":
        draw_gameover()
    elif game_state == "sorting":
        draw_sorting()
    elif game_state == "level_complete":
        draw_level_complete()
    elif game_state == "game_complete":
        draw_game_complete()
    elif game_state == "map_transition":
        draw_map_transition()
    elif game_state == "confirm_menu":
        draw_confirm_menu()
    draw_sound_toggle()


def update():
    global game_state, score, feedback_timer, map_transition_timer
    if feedback_timer > 0:
        feedback_timer -= 1
    if game_state == "map_transition":
        map_transition_timer += 1
        if map_transition_timer >= MAP_TRANSITION_DURATION:
            start_level(map_transition_to)
        return
    if game_state != "playing":
        return

    chicken.move()
    for car in cars:
        car.move()
        if chicken.hitbox.colliderect(car.hitbox):
            if sound_on:
                sounds.honk.play()
            set_feedback("Observe o trânsito e tente novamente.", 180, "wrong_icon")
            game_state = "gameover"
            return

    for item in wastes:
        if not item.collected and chicken.hitbox.colliderect(item.rect):
            item.collect()
            score += 10
            current_stats["collected"] += 1
            set_feedback(f"Você coletou {item.label}. Leve para a lixeira certa depois!", 150, "correct_icon")

    if chicken.y < 55:
        if all_collected():
            prepare_sorting()
        else:
            missing = len(wastes) - collected_count()
            set_feedback(f"Ainda há {missing} resíduo(s) para recolher antes de atravessar.", 180)
            chicken.y = 88


def toggle_sound():
    global sound_on, music_on
    sound_on = not sound_on
    music_on = sound_on
    if music_on:
        music.play("chicken_theme")
    else:
        music.stop()


def on_key_down(key):
    global game_state
    if key == keys.ESCAPE:
        if game_state == "confirm_menu":
            cancel_menu_confirmation()
        elif game_state != "menu":
            request_menu_confirmation()
        return
    if game_state == "gameover" and key == keys.R:
        restart_current_level()
    elif game_state == "intro" and (key == keys.RETURN or key == keys.SPACE):
        game_state = "playing"
        if music_on:
            music.play("chicken_theme")


def on_mouse_down(pos):
    global game_state, dragging_item, drag_offset
    x, y = pos
    if SOUND_RECT.collidepoint(pos):
        toggle_sound()
        return
    if game_state == "menu":
        if button_rect(WIDTH // 2, 284).collidepoint(pos):
            level_stats.clear()
            start_level(0)
            if music_on:
                music.play("chicken_theme")
        elif button_rect(WIDTH // 2, 382).collidepoint(pos):
            game_state = "how_to_play"
        elif button_rect(WIDTH // 2, 480).collidepoint(pos):
            exit()
    elif game_state == "how_to_play":
        if button_rect(WIDTH // 2, 585).collidepoint(pos):
            request_menu_confirmation()
    elif game_state == "intro":
        if button_rect(WIDTH // 2, 505).collidepoint(pos):
            game_state = "playing"
    elif game_state == "gameover":
        if button_rect(WIDTH // 2, 500).collidepoint(pos):
            restart_current_level()
        elif button_rect(WIDTH // 2, 575).collidepoint(pos):
            request_menu_confirmation()
    elif game_state == "sorting":
        for item in reversed(wastes):
            if item.collected and not item.discarded and item.drag_rect().collidepoint(pos):
                dragging_item = item
                drag_offset = (x - item.drag_pos[0], y - item.drag_pos[1])
                break
    elif game_state == "level_complete":
        if button_rect(WIDTH // 2 - 130, 594).collidepoint(pos):
            if level_index < len(LEVELS) - 1:
                start_map_transition(level_index, level_index + 1)
            else:
                game_state = "game_complete"
        elif button_rect(WIDTH // 2 + 130, 594).collidepoint(pos):
            request_menu_confirmation()
    elif game_state == "game_complete":
        if button_rect(WIDTH // 2 - 130, 638).collidepoint(pos):
            level_stats.clear()
            start_level(0)
        elif button_rect(WIDTH // 2 + 130, 638).collidepoint(pos):
            request_menu_confirmation()
    elif game_state == "confirm_menu":
        if button_rect(WIDTH // 2 - 130, 450).collidepoint(pos):
            confirm_go_to_menu()
        elif button_rect(WIDTH // 2 + 130, 450).collidepoint(pos):
            cancel_menu_confirmation()


def on_mouse_move(pos):
    if game_state == "sorting" and dragging_item is not None:
        dragging_item.drag_pos = [pos[0] - drag_offset[0], pos[1] - drag_offset[1]]


def on_mouse_up(pos):
    global dragging_item, score
    if game_state != "sorting" or dragging_item is None:
        dragging_item = None
        return

    dropped_on = None
    drag_rect = dragging_item.drag_rect()
    for bin_obj in bins:
        if drag_rect.colliderect(bin_obj.rect):
            dropped_on = bin_obj
            break

    if dropped_on and dropped_on.category == dragging_item.category:
        dragging_item.discarded = True
        current_stats["correct_discards"] += 1
        score += 20
        if dragging_item.first_try:
            current_stats["first_try_discards"] += 1
            score += 10
        set_feedback("Parabéns! Você descartou corretamente esse material.", 180, "correct_icon")
        if all_discarded():
            finish_level()
    elif dropped_on:
        dragging_item.first_try = False
        current_stats["wrong_discards"] += 1
        label = CATEGORY_LABELS[dragging_item.category]
        reason = CATEGORY_REASONS[dragging_item.category]
        set_feedback(f"{dragging_item.label} deve ir em {label}: {reason}", 260, "wrong_icon")
        dragging_item.drag_pos = dragging_item.home_pos[:]
    else:
        dragging_item.drag_pos = dragging_item.home_pos[:]

    dragging_item = None


start_level(0)
game_state = "menu"
pgzrun.go()
