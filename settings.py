import pygame
import os

pygame.init()
_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH: int = _screen.get_width()
SCREEN_HEIGHT: int = _screen.get_height()
pygame.display.set_caption("Head Soccer BR")
FPS: int = 60

ASSETS_DIR: str = os.path.join(os.path.dirname(__file__), "assets")
IMAGES_DIR: str = os.path.join(ASSETS_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

pygame.mixer.init()
SOUNDS_DIR: str = os.path.join(ASSETS_DIR, "sounds")

GRAVITY: float = 0.45
BALL_GRAVITY: float = 0.24
BOUNCE: float = 0.72
BALL_FRICTION: float = 0.98
FRICTION: float = 0.985
MAX_BALL_SPEED: float = 28
MAX_BALL_VERTICAL_SPEED: float = 30
KICK_FORCE_MIN: float = 22
KICK_FORCE_MAX: float = 28
KICK_UPWARD_LOW_BALL: float = -20
KICK_UPWARD_HIGH_BALL: float = -10

WHITE: tuple[int, int, int] = (255, 255, 255)
BLACK: tuple[int, int, int] = (0, 0, 0)
RED: tuple[int, int, int] = (220, 20, 60)
BLUE: tuple[int, int, int] = (30, 144, 255)
GREEN: tuple[int, int, int] = (34, 139, 34)
YELLOW: tuple[int, int, int] = (255, 215, 0)
ORANGE: tuple[int, int, int] = (255, 140, 0)
CYAN: tuple[int, int, int] = (0, 255, 255)
PURPLE: tuple[int, int, int] = (128, 0, 128)
GRAY: tuple[int, int, int] = (169, 169, 169)
DARK_GRAY: tuple[int, int, int] = (40, 40, 40)

CHARACTERS: list[dict] = [
    {"name": "Ronaldo Fenômeno", "file": "fenomeno_head.png", "key": "Espanha"},
    {"name": "Ronaldinho Gaúcho", "file": "ronaldinho_head.png", "key": "Brasil"},
    {"name": "Kaká", "file": "kaka_head.png", "key": "Alemanha"},
    {"name": "Neymar Junior", "file": "neymarjr_head.png", "key": "Argentina"}
]

ARENAS: dict[str, dict] = {
    "Grama": {
        "gravity": 0.45,
        "ball_gravity": 0.24,
        "bounce": 0.72,
        "friction": 0.98,
        "player_speed": 4.5,
        "jump_power": -13,
        "wall_bounce": 0.6,
        "max_ball_speed": 28,
        "max_ball_vertical_speed": 30,
        "bg_file": "campo_grama.png",
        "fallback_color": (34, 139, 34),
        "label": "Grama (Normal)",
    },
    "Gelo": {
        "gravity": 0.40,
        "ball_gravity": 0.22,
        "bounce": 0.80,
        "friction": 0.998,
        "player_speed": 5.5,
        "jump_power": -12,
        "wall_bounce": 0.7,
        "max_ball_speed": 28,
        "max_ball_vertical_speed": 30,
        "bg_file": "campo_gelo.jpg",
        "fallback_color": (200, 230, 255),
        "label": "Gelo (Escorregadio)",
    },
}
