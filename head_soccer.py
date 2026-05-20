import pygame
import random
import math
import sys
import os
import glob
import time

# --- Configurações Iniciais ---
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH = screen.get_width()
SCREEN_HEIGHT = screen.get_height()
pygame.display.set_caption("Head Soccer Classic - Futebol Raiz")
FPS = 60

# Caminhos dos Assets
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# === FÍSICA ARCADE ===
GRAVITY = 0.45
BALL_GRAVITY = 0.24
BOUNCE = 0.72
BALL_FRICTION = 0.98
FRICTION = 0.985
MAX_BALL_SPEED = 22
MAX_BALL_VERTICAL_SPEED = 22
KICK_FORCE_MULTIPLIER = 1.3
KICK_UPWARD_FORCE = 8

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
GREEN = (34, 139, 34)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
GRAY = (169, 169, 169)
DARK_GRAY = (40, 40, 40)

# Personagens disponíveis
CHARACTERS = [
    {"name": "Ronaldo Fenômeno", "file": "fenomeno_head.png", "key": "Espanha"},
    {"name": "Ronaldinho Gaúcho", "file": "ronaldinho_head.png", "key": "Brasil"},
    {"name": "Kaká", "file": "kaka_head.png", "key": "Alemanha"},
    {"name": "Neymar Junior", "file": "neymarjr_head.png", "key": "Argentina"}
]

# --- Carregamento de Assets ---

def load_image(name, fallback_color=WHITE, size=(100, 100)):
    path = os.path.join(IMAGES_DIR, name)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(surf, fallback_color, (0, 0, size[0], size[1]))
        return surf

def load_shoe_sprite():
    """Carrega sprite de chuteira do arquivo PNG"""
    shoe_path = os.path.join(IMAGES_DIR, "chuteira.png")
    if os.path.exists(shoe_path):
        shoe = pygame.image.load(shoe_path).convert_alpha()
        shoe = pygame.transform.scale(shoe, (150, 90))
    else:
        # Fallback: criar sprite simples e gigante
        shoe = pygame.Surface((150, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(shoe, (220, 60, 40), pygame.Rect(10, 10, 128, 60))
        pygame.draw.rect(shoe, (220, 60, 40), pygame.Rect(10, 30, 128, 40))
        pygame.draw.polygon(shoe, WHITE, [(130, 35), (148, 42), (135, 60)])
        pygame.draw.line(shoe, BLACK, (10, 75), (138, 75), 6)
    shoe_r = pygame.transform.flip(shoe, True, False)
    return shoe, shoe_r

def load_head(name, color=WHITE):
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

# --- Classes do Jogo ---

class Player:
    def __init__(self, x, y, char_data, controls, side):
        self.initial_x = x
        self.initial_y = y
        self.rect = pygame.Rect(x, y, 145, 175)
        self.hitbox_offset_x = 18
        self.name = char_data["name"]
        self.key = char_data["key"]
        self.controls = controls
        self.side = side
        
        self.head_img, self.head_img_r = Assets.heads[self.key]
        self.current_img = self.head_img if side == 0 else self.head_img_r
        
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 4.5
        self.jump_power = -13
        self.is_jumping = False
        self.score = 0
        
        self.kicking = False
        self.kick_force = 16
        
        self.shoe_angle = 0
        self.shoe_offset_x = 0
        self.shoe_offset_y = 0
        self.kick_animation_timer = 0

    def reset_position(self):
        self.rect.x = self.initial_x
        self.rect.y = self.initial_y
        self.vel_x = 0
        self.vel_y = 0
        self.shoe_angle = 0
        self.shoe_offset_x = 0
        self.shoe_offset_y = 0
        self.kicking = False

    def update(self):
        now = pygame.time.get_ticks()
        
        if self.kicking:
            elapsed = now - self.kick_animation_timer
            progress = min(1.0, elapsed / 250.0)
            
            if progress < 0.5:
                ratio = progress * 2
                self.shoe_angle = ratio * 90
                self.shoe_offset_x = ratio * 90 if self.side == 0 else -ratio * 90
                self.shoe_offset_y = -ratio * 35
            else:
                ratio = (progress - 0.5) * 2
                self.shoe_angle = (1 - ratio) * 90
                self.shoe_offset_x = (1 - ratio) * 90 if self.side == 0 else -(1 - ratio) * 90
                self.shoe_offset_y = -(1 - ratio) * 35
            
            if elapsed >= 250:
                self.kicking = False
                self.shoe_angle = 0
                self.shoe_offset_x = 0
                self.shoe_offset_y = 0

        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]:
            self.vel_x = -self.speed
        elif keys[self.controls['right']]:
            self.vel_x = self.speed
        else:
            self.vel_x = 0

        if keys[self.controls['jump']] and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True

        if keys[self.controls['special']] and not self.kicking:
            self.kicking = True
            self.kick_animation_timer = pygame.time.get_ticks()

        self.vel_y += GRAVITY
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        if self.rect.bottom >= SCREEN_HEIGHT - 40:
            self.rect.bottom = SCREEN_HEIGHT - 40
            self.vel_y = 0
            self.is_jumping = False

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        
        shoe_x = self.rect.centerx + self.shoe_offset_x + (90 if self.side == 0 else -90)
        shoe_y = self.rect.centery + self.shoe_offset_y + 55
        self.shoe_hitbox = pygame.Rect(0, 0, 160, 100)
        self.shoe_hitbox.center = (int(shoe_x), int(shoe_y))

    def draw(self, screen):
        img = self.head_img if self.vel_x >= 0 else self.head_img_r
        if self.side == 1 and self.vel_x <= 0:
            img = self.head_img_r
        elif self.side == 1 and self.vel_x > 0:
            img = self.head_img
        elif self.side == 0 and self.vel_x < 0:
            img = self.head_img_r
        elif self.side == 0 and self.vel_x >= 0:
            img = self.head_img
        
        screen.blit(img, (self.rect.x - self.hitbox_offset_x, self.rect.y))
        
        shoe_img = Assets.shoe if self.side == 0 else Assets.shoe_r
        if self.shoe_angle != 0:
            shoe_img = pygame.transform.rotate(shoe_img, self.shoe_angle if self.side == 0 else -self.shoe_angle)
        
        shoe_x = self.rect.centerx + self.shoe_offset_x + (90 if self.side == 0 else -90)
        shoe_y = self.rect.centery + self.shoe_offset_y + 55
        shoe_rect = shoe_img.get_rect(center=(int(shoe_x), int(shoe_y)))
        screen.blit(shoe_img, shoe_rect)

class Ball:
    def __init__(self):
        self.radius = 48
        self.img = pygame.transform.smoothscale(Assets.ball, (96, 96))
        self.reset(conceded_by=0)

    def reset(self, conceded_by=0):
        if conceded_by == 1:
            self.x = SCREEN_WIDTH // 2 - 280
        elif conceded_by == 2:
            self.x = SCREEN_WIDTH // 2 + 280
        else:
            self.x = SCREEN_WIDTH // 2
        self.y = 100
        self.vel_x = 0
        self.vel_y = 0
        self.angle = 0
        self.angle_speed = 0

    def update(self):
        self.vel_y += BALL_GRAVITY
        self.vel_x *= 0.995
        
        if 0 < abs(self.vel_x) < 0.1:
            self.vel_x *= 1.02
        
        for _ in range(2):
            self.x += self.vel_x * 0.5
            self.y += self.vel_y * 0.5

            if self.y + self.radius >= SCREEN_HEIGHT - 40:
                self.y = SCREEN_HEIGHT - 40 - self.radius
                if self.vel_y > 0:
                    self.vel_y = -self.vel_y * BOUNCE
                if abs(self.vel_y) < 1: self.vel_y = 0

            if self.x - self.radius < 0:
                self.x = self.radius
                self.vel_x = abs(self.vel_x) * 0.6
            elif self.x + self.radius > SCREEN_WIDTH:
                self.x = SCREEN_WIDTH - self.radius
                self.vel_x = -abs(self.vel_x) * 0.6
                
            if self.y - self.radius < 0:
                self.y = self.radius
                if self.vel_y < 0:
                    self.vel_y = 0

        if abs(self.vel_x) > MAX_BALL_SPEED:
            self.vel_x = (self.vel_x / abs(self.vel_x)) * MAX_BALL_SPEED
        if abs(self.vel_y) > MAX_BALL_VERTICAL_SPEED:
            self.vel_y = (self.vel_y / abs(self.vel_y)) * MAX_BALL_VERTICAL_SPEED

        self.angle_speed += self.vel_x * 0.04
        self.angle += self.angle_speed
        self.angle_speed *= 0.98

    def draw(self, screen):
        shadow = pygame.Surface((70, 25), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, 70, 25))
        ground_y = SCREEN_HEIGHT - 40
        height_diff = ground_y - (self.y + self.radius)
        if height_diff < 0: height_diff = 0
        shadow_scale = max(0.2, 1.0 - height_diff / 300)
        shadow_scaled = pygame.transform.scale(shadow, (int(70 * shadow_scale), int(25 * shadow_scale)))
        screen.blit(shadow_scaled, (self.x - shadow_scaled.get_width() // 2, ground_y - shadow_scaled.get_height() // 2))

        rotated_ball = pygame.transform.rotozoom(self.img, -self.angle, 1)
        ball_rect = rotated_ball.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated_ball, ball_rect)

class Goal:
    def __init__(self, x, side):
        self.rect = pygame.Rect(x, SCREEN_HEIGHT - 400, 125, 360)
        self.crossbar = pygame.Rect(x, SCREEN_HEIGHT - 400, 125, 16)
        self.side = side
        if os.path.exists(os.path.join(IMAGES_DIR, "goal.png")):
            self.img = pygame.transform.scale(Assets.goal_img, (125, 360))
            self.img_r = pygame.transform.scale(Assets.goal_img_r, (125, 360))
        else:
            self.img = pygame.Surface((125, 360))
            self.img.fill(GRAY)
            self.img_r = self.img

    def draw(self, screen):
        # Usar imagem invertida para o gol do lado direito (jogador 2)
        if self.side == 0:
            screen.blit(self.img, self.rect)
        else:
            screen.blit(self.img_r, self.rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 80, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 44, bold=True)
        
        self.state = "SPLASH"
        self.menu_option = 0
        self.pause_option = 0
        
        self.p1_selected_char = 0
        self.p2_selected_char = 1
        
        self.reset_game()

    def reset_game(self):
        char1 = CHARACTERS[self.p1_selected_char]
        char2 = CHARACTERS[self.p2_selected_char]
        
        self.p1 = Player(180, SCREEN_HEIGHT - 220, char1, {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'special': pygame.K_SPACE}, 0)
        self.p2 = Player(SCREEN_WIDTH - 325, SCREEN_HEIGHT - 220, char2, {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'special': pygame.K_RETURN}, 1)
        self.ball = Ball()
        self.goal_left = Goal(0, 0)
        self.goal_right = Goal(SCREEN_WIDTH - 110, 1)
        
        self.game_time = 60
        self.current_time = 60
        self.start_ticks = 0
        self.winner = ""
        self.last_conceded_by = 0
        self.is_golden_goal = False  # Controla se estamos na fase de gol de ouro

    def update(self):
        if self.state == "PLAYING":
            now = pygame.time.get_ticks()
            self.current_time = self.game_time - (now - self.start_ticks) // 1000
            
            # Verificar condições de vitória
            # 1. Alguém alcançou 3 gols
            if self.p1.score >= 3:
                self.state = "END"
                self.winner = f"{self.p1.name} VENCEU! (3 GOLS)"
            elif self.p2.score >= 3:
                self.state = "END"
                self.winner = f"{self.p2.name} VENCEU! (3 GOLS)"
            # 2. Tempo acabou
            elif self.current_time <= 0:
                if self.p1.score > self.p2.score:
                    self.state = "END"
                    self.winner = f"{self.p1.name} VENCEU!"
                elif self.p2.score > self.p1.score:
                    self.state = "END"
                    self.winner = f"{self.p2.name} VENCEU!"
                else:
                    # Empate - ativar gol de ouro por 30 segundos
                    self.state = "GOLDEN_GOAL"
                    self.is_golden_goal = True
                    self.game_time = 30
                    self.current_time = 30
                    self.start_ticks = pygame.time.get_ticks()
            
            self.p1.update()
            self.p2.update()
            self.ball.update()
            self.check_collisions()
        
        elif self.state == "GOLDEN_GOAL":
            now = pygame.time.get_ticks()
            self.current_time = self.game_time - (now - self.start_ticks) // 1000
            
            # Se alguém fizer gol em gol de ouro, vence imediatamente
            # ou se o tempo de gol de ouro acabar, é empate
            if self.current_time <= 0:
                self.state = "END"
                self.winner = "EMPATE! (Ninguém marcou no Golden Goal)"
            
            self.p1.update()
            self.p2.update()
            self.ball.update()
            self.check_collisions()
        
        elif self.state == "PAUSED":
            pass

    def check_collisions(self):
        if self.p1.rect.colliderect(self.p2.rect):
            if self.p1.rect.centerx < self.p2.rect.centerx:
                overlap = self.p1.rect.right - self.p2.rect.left
                self.p1.rect.x -= overlap // 2
                self.p2.rect.x += overlap // 2
            else:
                overlap = self.p2.rect.right - self.p1.rect.left
                self.p2.rect.x -= overlap // 2
                self.p1.rect.x += overlap // 2
            self.p1.vel_x = 0
            self.p2.vel_x = 0

        left_player = self.p1 if self.p1.rect.centerx < self.p2.rect.centerx else self.p2
        right_player = self.p2 if self.p1.rect.centerx < self.p2.rect.centerx else self.p1
        
        if left_player.rect.right > self.ball.x - self.ball.radius and right_player.rect.left < self.ball.x + self.ball.radius:
            if left_player.rect.right > right_player.rect.left - self.ball.radius * 2:
                if self.ball.y > min(left_player.rect.top, right_player.rect.top):
                    self.ball.vel_x *= 0.2
                    self.ball.vel_y *= 0.2
                    if left_player.rect.right > right_player.rect.left - self.ball.radius:
                        self.ball.vel_x = 0

        ball_rect = pygame.Rect(self.ball.x - self.ball.radius, self.ball.y - self.ball.radius, self.ball.radius * 2, self.ball.radius * 2)

        for p in [self.p1, self.p2]:
            if p.kicking and hasattr(p, 'shoe_hitbox') and p.shoe_hitbox.colliderect(ball_rect):
                dx = self.ball.x - p.shoe_hitbox.centerx
                dy = self.ball.y - p.shoe_hitbox.centery
                angle = math.atan2(dy, dx)
                force = random.uniform(22, 26)
                
                vertical_boost = -6 if self.ball.y > SCREEN_HEIGHT - 140 else -2
                
                cos_val = abs(math.cos(angle))
                if cos_val < 0.7:
                    cos_val = 0.7
                
                if p.side == 0:
                    self.ball.vel_x = cos_val * force
                else:
                    self.ball.vel_x = -cos_val * force
                
                self.ball.vel_y = vertical_boost
                self.ball.angle_speed = self.ball.vel_x * 0.05
                
                overlap = (self.ball.radius + 80) - math.hypot(dx, dy)
                if overlap > 0:
                    push_dir = 1 if p.side == 0 else -1
                    self.ball.x += push_dir * overlap
                    self.ball.y -= overlap

            dx = self.ball.x - p.rect.centerx
            dy = self.ball.y - p.rect.centery
            dist = math.hypot(dx, dy)
            collision_dist = 67 + self.ball.radius
            
            if dist < collision_dist and dist > 0:
                angle = math.atan2(dy, dx)
                force = 10
                
                self.ball.vel_x += math.cos(angle) * force
                self.ball.vel_y += math.sin(angle) * force
                
                overlap = collision_dist - dist
                self.ball.x += math.cos(angle) * overlap
                self.ball.y += math.sin(angle) * overlap
        
        # Colisão com o travessão do gol
        ball_rect = pygame.Rect(self.ball.x - self.ball.radius, self.ball.y - self.ball.radius, self.ball.radius * 2, self.ball.radius * 2)
        if ball_rect.colliderect(self.goal_left.crossbar):
            self.ball.vel_y *= -0.75
        if ball_rect.colliderect(self.goal_right.crossbar):
            self.ball.vel_y *= -0.75

        # Gols
        if self.goal_right.rect.collidepoint(self.ball.x, self.ball.y):
            self.p1.score += 1
            # Se estamos em gol de ouro, P1 vence imediatamente (sem animação de gol)
            if self.is_golden_goal:
                self.state = "END"
                self.winner = f"{self.p1.name} VENCEU! (GOL DE OURO)"
            else:
                self.trigger_goal(f"GOL DE {self.p1.name.upper()}!", conceded_by=2)
        elif self.goal_left.rect.collidepoint(self.ball.x, self.ball.y):
            self.p2.score += 1
            # Se estamos em gol de ouro, P2 vence imediatamente (sem animação de gol)
            if self.is_golden_goal:
                self.state = "END"
                self.winner = f"{self.p2.name} VENCEU! (GOL DE OURO)"
            else:
                self.trigger_goal(f"GOL DE {self.p2.name.upper()}!", conceded_by=1)

    def trigger_goal(self, msg, conceded_by):
        self.state = "GOAL"
        self.goal_message = msg
        self.goal_timer = pygame.time.get_ticks() + 2000
        self.last_conceded_by = conceded_by
    
    def draw_splash(self):
        self.screen.blit(Assets.start_background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        
        alpha = 128 + math.sin(pygame.time.get_ticks() * 0.005) * 127
        txt = self.button_font.render("PRESSIONE QUALQUER BOTÃO", True, WHITE)
        txt.set_alpha(int(alpha))
        self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT - 150))
        pygame.display.flip()

    def draw_button(self, text, y, selected, mouse_pos=None):
        rect_width = 420
        rect_height = 85
        rect_x = SCREEN_WIDTH // 2 - rect_width // 2
        button_rect = pygame.Rect(rect_x, y, rect_width, rect_height)
        
        is_hovered = mouse_pos and button_rect.collidepoint(mouse_pos)
        is_active = selected or is_hovered
        
        color = YELLOW if is_active else WHITE
        bg_color = (60, 60, 60) if is_active else (30, 30, 30)
        
        draw_rect = button_rect.copy()
        if is_hovered:
            draw_rect.inflate_ip(10, 10)
            
        pygame.draw.rect(self.screen, (0, 0, 0), (draw_rect.x + 6, draw_rect.y + 6, draw_rect.width, draw_rect.height), border_radius=22)
        pygame.draw.rect(self.screen, bg_color, draw_rect, border_radius=22)
        pygame.draw.rect(self.screen, color, draw_rect, 3, border_radius=22)
        
        txt_surf = self.button_font.render(text, True, color)
        self.screen.blit(txt_surf, (draw_rect.centerx - txt_surf.get_width() // 2, draw_rect.centery - txt_surf.get_height() // 2))
        
        return button_rect

    def draw_menu(self):
        mouse_pos = pygame.mouse.get_pos()
        self.screen.blit(Assets.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        logo_x = SCREEN_WIDTH // 2 - Assets.logo.get_width() // 2
        logo_y = 60
        self.screen.blit(Assets.logo, (logo_x, logo_y))
        
        options = ["Iniciar Jogo", "Sair"]
        self.menu_buttons = []
        for i, option in enumerate(options):
            rect = self.draw_button(option, 280 + i * 110, i == self.menu_option, mouse_pos)
            self.menu_buttons.append(rect)
        pygame.display.flip()

    def draw_pause(self):
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        panel_width, panel_height = 500, 450
        panel_x = SCREEN_WIDTH // 2 - panel_width // 2
        panel_y = SCREEN_HEIGHT // 2 - panel_height // 2
        
        pygame.draw.rect(self.screen, (0, 0, 0), (panel_x + 8, panel_y + 8, panel_width, panel_height), border_radius=20)
        pygame.draw.rect(self.screen, (40, 40, 40), (panel_x, panel_y, panel_width, panel_height), border_radius=20)
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 3, border_radius=20)
        
        title = self.large_font.render("PAUSA", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, panel_y + 30))
        
        pause_options = ["Continuar", "Reiniciar", "Menu Inicial"]
        self.pause_buttons = []
        for i, option in enumerate(pause_options):
            rect = self.draw_button(option, panel_y + 130 + i * 100, i == self.pause_option, mouse_pos)
            self.pause_buttons.append(rect)
        pygame.display.flip()

    def draw_character_select(self):
        mouse_pos = pygame.mouse.get_pos()
        self.screen.blit(Assets.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        title_text = self.large_font.render("SELEÇÃO DE PERSONAGENS", True, YELLOW)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 40))
        
        card_w, card_h = 180, 220
        spacing_x, spacing_y = 60, 50
        grid_w = (card_w * 2) + spacing_x
        grid_h = (card_h * 2) + spacing_y
        start_x = SCREEN_WIDTH // 2 - grid_w // 2
        start_y = 160
        
        positions = [
            (start_x, start_y),
            (start_x + card_w + spacing_x, start_y),
            (start_x, start_y + card_h + spacing_y),
            (start_x + card_w + spacing_x, start_y + card_h + spacing_y)
        ]
        
        self.char_rects = []
        for idx, pos in enumerate(positions):
            x, y = pos
            rect = pygame.Rect(x, y, card_w, card_h)
            self.char_rects.append(rect)
            
            is_hovered = rect.collidepoint(mouse_pos)
            bg_color = (70, 70, 70) if is_hovered else (45, 45, 45)
            
            if is_hovered:
                draw_rect = rect.inflate(10, 10)
            else:
                draw_rect = rect
                
            pygame.draw.rect(self.screen, (0, 0, 0), (draw_rect.x + 6, draw_rect.y + 6, draw_rect.width, draw_rect.height), border_radius=15)
            pygame.draw.rect(self.screen, bg_color, draw_rect, border_radius=15)
            
            preview = Assets.character_previews[idx]
            self.screen.blit(preview, (draw_rect.centerx - preview.get_width() // 2, draw_rect.y + 10))
            
            name_text = self.small_font.render(CHARACTERS[idx]["name"], True, WHITE)
            self.screen.blit(name_text, (draw_rect.centerx - name_text.get_width()//2, draw_rect.bottom - 30))
            
            if idx == self.p1_selected_char:
                pygame.draw.rect(self.screen, GREEN, draw_rect, 5, border_radius=15)
            if idx == self.p2_selected_char:
                pygame.draw.rect(self.screen, BLUE, draw_rect, 5, border_radius=15)
                
        hint_text1 = self.font.render("P1: WASD + ESPAÇO", True, GREEN)
        hint_text2 = self.font.render("P2: SETAS + ENTER", True, BLUE)
        hint_text3 = self.font.render("ENTER: Começar", True, YELLOW)
        
        self.screen.blit(hint_text1, (50, SCREEN_HEIGHT - 60))
        self.screen.blit(hint_text3, (SCREEN_WIDTH//2 - hint_text3.get_width()//2, SCREEN_HEIGHT - 60))
        self.screen.blit(hint_text2, (SCREEN_WIDTH - 50 - hint_text2.get_width(), SCREEN_HEIGHT - 60))
        pygame.display.flip()

    def draw(self):
        if self.state == "SPLASH":
            self.draw_splash()
            return
        elif self.state == "MENU":
            self.draw_menu()
            return
        elif self.state == "CHARACTER_SELECT":
            self.draw_character_select()
            return
        
        self.screen.blit(Assets.background, (0, 0))
        pygame.draw.rect(self.screen, (35, 70, 25), (0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40)) # Chão
        
        self.goal_left.draw(self.screen)
        self.goal_right.draw(self.screen)
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        self.ball.draw(self.screen)

        # UI - Placar com nomes reais
        # Jogador 1 (Esquerda)
        p1_label = self.small_font.render(self.p1.name, True, WHITE)
        p1_score = self.large_font.render(str(self.p1.score), True, WHITE)
        self.screen.blit(p1_label, (50, 15))
        self.screen.blit(p1_score, (50, 45))
        
        # Jogador 2 (Direita)
        p2_label = self.small_font.render(self.p2.name, True, WHITE)
        p2_score = self.large_font.render(str(self.p2.score), True, WHITE)
        self.screen.blit(p2_label, (SCREEN_WIDTH - 50 - p2_label.get_width(), 15))
        self.screen.blit(p2_score, (SCREEN_WIDTH - 50 - p2_score.get_width(), 45))
        
        # Timer Central
        t_val = self.current_time if self.state in ["PLAYING", "GOLDEN_GOAL"] else self.game_time
        timer_color = (255, 215, 0) if self.state == "GOLDEN_GOAL" else YELLOW
        timer_text = self.large_font.render(str(max(0, t_val)), True, timer_color)
        self.screen.blit(timer_text, (SCREEN_WIDTH//2 - timer_text.get_width()//2, 20))

        if self.state == "PAUSED":
            self.draw_pause()
        elif self.state == "GOAL":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
            goal_text = self.large_font.render(self.goal_message, True, YELLOW)
            self.screen.blit(goal_text, (SCREEN_WIDTH//2 - goal_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            if pygame.time.get_ticks() > self.goal_timer:
                self.ball.reset(conceded_by=self.last_conceded_by)
                self.p1.reset_position()
                self.p2.reset_position()
                self.state = "PLAYING"
                self.start_ticks += 2000
        elif self.state == "GOLDEN_GOAL":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
            golden_text = self.large_font.render("GOL DE OURO!", True, (255, 215, 0))
            self.screen.blit(golden_text, (SCREEN_WIDTH//2 - golden_text.get_width()//2, SCREEN_HEIGHT//2))
        elif self.state == "END":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            win_text = self.large_font.render(self.winner, True, YELLOW)
            restart_text = self.font.render("Pressione R para reiniciar", True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "SPLASH":
                        self.state = "MENU"
                    elif self.state == "MENU" and event.button == 1:
                        for i, rect in enumerate(self.menu_buttons):
                            if rect.collidepoint(event.pos):
                                if i == 0: self.state = "CHARACTER_SELECT"
                                else: pygame.quit(); sys.exit()
                    elif self.state == "PAUSED" and event.button == 1:
                        for i, rect in enumerate(self.pause_buttons):
                            if rect.collidepoint(event.pos):
                                if i == 0:
                                    self.state = "PLAYING"
                                    self.start_ticks += (pygame.time.get_ticks() - self.pause_start_ticks)
                                elif i == 1:
                                    self.reset_game()
                                    self.state = "PLAYING"
                                    self.start_ticks = pygame.time.get_ticks()
                                elif i == 2:
                                    self.state = "MENU"
                    elif self.state == "CHARACTER_SELECT":
                        for i, rect in enumerate(self.char_rects):
                            if rect.collidepoint(event.pos):
                                if event.button == 1: self.p1_selected_char = i
                                elif event.button == 3: self.p2_selected_char = i

                if event.type == pygame.KEYDOWN:
                    if self.state == "SPLASH":
                        self.state = "MENU"
                    elif self.state == "MENU":
                        if event.key in [pygame.K_w, pygame.K_UP]: self.menu_option = (self.menu_option - 1) % 2
                        elif event.key in [pygame.K_s, pygame.K_DOWN]: self.menu_option = (self.menu_option + 1) % 2
                        elif event.key == pygame.K_RETURN:
                            if self.menu_option == 0: self.state = "CHARACTER_SELECT"
                            else: pygame.quit(); sys.exit()
                    
                    elif self.state == "CHARACTER_SELECT":
                        if event.key == pygame.K_w: self.p1_selected_char = (self.p1_selected_char - 2) % 4
                        elif event.key == pygame.K_s: self.p1_selected_char = (self.p1_selected_char + 2) % 4
                        elif event.key == pygame.K_a:
                            if self.p1_selected_char % 2 == 1: self.p1_selected_char -= 1
                        elif event.key == pygame.K_d:
                            if self.p1_selected_char % 2 == 0: self.p1_selected_char += 1
                        
                        elif event.key == pygame.K_UP: self.p2_selected_char = (self.p2_selected_char - 2) % 4
                        elif event.key == pygame.K_DOWN: self.p2_selected_char = (self.p2_selected_char + 2) % 4
                        elif event.key == pygame.K_LEFT:
                            if self.p2_selected_char % 2 == 1: self.p2_selected_char -= 1
                        elif event.key == pygame.K_RIGHT:
                            if self.p2_selected_char % 2 == 0: self.p2_selected_char += 1
                        
                        elif event.key == pygame.K_RETURN:
                            self.reset_game()
                            self.state = "PLAYING"
                            self.start_ticks = pygame.time.get_ticks()
                    
                    elif self.state == "PLAYING":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "PAUSED"
                            self.pause_start_ticks = pygame.time.get_ticks()
                    
                    elif self.state == "PAUSED":
                        if event.key in [pygame.K_w, pygame.K_UP]: self.pause_option = (self.pause_option - 1) % 3
                        elif event.key in [pygame.K_s, pygame.K_DOWN]: self.pause_option = (self.pause_option + 1) % 3
                        elif event.key == pygame.K_RETURN:
                            if self.pause_option == 0: # Continuar
                                self.state = "PLAYING"
                                self.start_ticks += (pygame.time.get_ticks() - self.pause_start_ticks)
                            elif self.pause_option == 1: # Reiniciar
                                self.reset_game()
                                self.state = "PLAYING"
                                self.start_ticks = pygame.time.get_ticks()
                            elif self.pause_option == 2: # Menu
                                self.state = "MENU"
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "PLAYING"
                            self.start_ticks += (pygame.time.get_ticks() - self.pause_start_ticks)

                    elif self.state == "END" and event.key == pygame.K_r:
                        self.state = "MENU"

            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()