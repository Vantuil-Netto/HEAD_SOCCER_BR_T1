import pygame
import os
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, IMAGES_DIR,
    WHITE, RED, YELLOW, BLUE, GRAY, GREEN, BLACK, CHARACTERS
)


def load_image(name: str, fallback_color=WHITE, size=(100, 100)) -> pygame.Surface:
    path = os.path.join(IMAGES_DIR, name)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.ellipse(surf, fallback_color, (0, 0, size[0], size[1]))
    return surf


def load_shoe_sprite():
    shoe_path = os.path.join(IMAGES_DIR, "chuteira.png")
    if os.path.exists(shoe_path):
        shoe = pygame.image.load(shoe_path).convert_alpha()
        shoe = pygame.transform.scale(shoe, (150, 90))
    else:
        shoe = pygame.Surface((150, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(shoe, (220, 60, 40), pygame.Rect(10, 10, 128, 60))
        pygame.draw.rect(shoe, (220, 60, 40), pygame.Rect(10, 30, 128, 40))
        pygame.draw.polygon(shoe, WHITE, [(130, 35), (148, 42), (135, 60)])
        pygame.draw.line(shoe, BLACK, (10, 75), (138, 75), 6)
    shoe_r = pygame.transform.flip(shoe, True, False)
    return shoe, shoe_r


def load_head(name: str, color=WHITE):
    img = load_image(name, fallback_color=color, size=(180, 180))
    head = pygame.transform.scale(img, (180, 180))
    r_head = pygame.transform.flip(head, True, False)
    return head, r_head


class Assets:
    heads = {
        "Argentina": load_head("neymarjr_head.png", BLUE),
        "Brasil": load_head("ronaldinho_head.png", YELLOW),
        "Alemanha": load_head("kaka_head.png", WHITE),
        "Espanha": load_head("fenomeno_head.png", RED)
    }

    character_previews = []
    for i, char in enumerate(CHARACTERS):
        colors = [RED, YELLOW, WHITE, BLUE]
        img = load_image(char["file"], fallback_color=colors[i], size=(160, 160))
        preview = pygame.transform.scale(img, (160, 160))
        character_previews.append(preview)

    logo_raw = load_image("logo.png", fallback_color=YELLOW, size=(450, 170))
    logo = pygame.transform.scale(logo_raw, (450, 215))
    shoe, shoe_r = load_shoe_sprite()
    ball = load_image("new_ball.png", fallback_color=WHITE, size=(56, 56))
    goal_img = load_image("goal.png", fallback_color=GRAY, size=(100, 200))
    goal_img_r = pygame.transform.flip(goal_img, True, False)

    bg_path = os.path.join(IMAGES_DIR, "new_background.png")
    if os.path.exists(bg_path):
        background = pygame.image.load(bg_path).convert()
        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.fill(GREEN)

    start_bg_path = os.path.join(IMAGES_DIR, "start_background.png")
    if os.path.exists(start_bg_path):
        start_background = pygame.image.load(start_bg_path).convert()
        start_background = pygame.transform.scale(start_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        start_background = background
