import pygame
import random
import math
import sys
import os
import glob
import time

# --- Configurações Iniciais ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600 # Ajustado para combinar com o jogo de referência
pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
FPS = 60

# Caminhos dos Assets
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# === FÍSICA ARCADE ===
GRAVITY = 0.6
BALL_GRAVITY = 0.35
BOUNCE = 0.75
BALL_FRICTION = 0.99
FRICTION = 0.98
MAX_BALL_SPEED = 25
MAX_BALL_VERTICAL_SPEED = 30
KICK_FORCE_MULTIPLIER = 1.2
KICK_UPWARD_FORCE = 12

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

# --- Carregamento de Assets ---

def load_image(name):
    path = os.path.join(IMAGES_DIR, name)
    return pygame.image.load(path).convert_alpha()

def load_head(name):
    img = load_image(name)
    head = pygame.transform.scale(img, (70, 70))
    r_head = pygame.transform.flip(head, True, False)
    return head, r_head

def load_dir_both(dirname):
    path = os.path.join(IMAGES_DIR, dirname, "*.png")
    files = sorted(glob.glob(path))
    result = []
    for f in files:
        img = pygame.image.load(f).convert_alpha()
        r_img = pygame.transform.flip(img, True, False)
        result.append([img, r_img])
    return result

class Assets:
    heads = {
        "Argentina": load_head("neymarjr_head.png"),
        "Brasil": load_head("ronaldinho_head.png"),
        "Alemanha": load_head("kaka_head.png"),
        "Espanha": load_head("fenomeno_head.png")
    }
    ball = load_image("classic_ball.png") # Usando classic_ball como bola para estilo
    goal_img = load_image("goal.png")
    goal_img_r = pygame.transform.flip(goal_img, True, False)
    goal_anim = load_dir_both("goalA")
    backgrounds = [load_image(f"back{i}.png") for i in range(1, 7)]
    stadium = load_image("ORT_staidium_v1.png")

# --- Classes de Suporte ---

class Animation:
    def __init__(self, frames, side=0, freq=10):
        self.frames = frames
        self.side = side
        self.freq = freq
        self.period = 1.0 / freq
        self.current_frame = 0
        self.playing = False
        self.ref_time = 0
        self.stop_at_end = True

    def start(self, stop_at_end=True):
        if not self.playing:
            self.ref_time = time.time() * 1000
            self.playing = True
            self.stop_at_end = stop_at_end

    def update(self):
        if self.playing:
            length = len(self.frames)
            dt = time.time() * 1000 - self.ref_time
            frame_idx = int(float(length) * (float(dt) / (float(self.period * 1000))))

            if frame_idx >= length:
                if self.stop_at_end:
                    self.current_frame = 0
                    self.playing = False
                else:
                    self.ref_time = time.time() * 1000
                    self.current_frame = 0
            else:
                self.current_frame = frame_idx

    def get_image(self):
        return self.frames[self.current_frame][self.side]

# --- Classes do Jogo ---

class Player:
    def __init__(self, x, y, name, controls, side):
        self.initial_x = x
        self.initial_y = y
        self.rect = pygame.Rect(x, y, 70, 70)
        self.name = name
        self.controls = controls # {left, right, jump, special}
        self.side = side # 0 for left, 1 for right
        
        self.head_img, self.head_img_r = Assets.heads[name]
        self.current_img = self.head_img if side == 0 else self.head_img_r
        
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 10
        self.jump_power = -15
        self.is_jumping = False
        self.score = 0
        
        # Power-up status
        self.frozen = False
        self.freeze_timer = 0
        self.speed_boost = False
        self.speed_timer = 0
        self.super_kick = False
        self.super_kick_timer = 0
        
        self.kicking = False
        self.kick_timer = 0
        self.kick_force = 22

    def reset_position(self):
        self.rect.x = self.initial_x
        self.rect.y = self.initial_y
        self.vel_x = 0
        self.vel_y = 0

    def update(self):
        now = pygame.time.get_ticks()
        
        if self.frozen and now > self.freeze_timer:
            self.frozen = False
        if self.speed_boost and now > self.speed_timer:
            self.speed_boost = False
        if self.super_kick and now > self.super_kick_timer:
            self.super_kick = False
        
        if self.kicking and now > self.kick_timer:
            self.kicking = False

        if self.frozen:
            return

        keys = pygame.key.get_pressed()
        
        current_speed = self.speed * 1.5 if self.speed_boost else self.speed
        if keys[self.controls['left']]:
            self.vel_x = -current_speed
        elif keys[self.controls['right']]:
            self.vel_x = current_speed
        else:
            self.vel_x = 0

        if keys[self.controls['jump']] and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True

        if keys[self.controls['special']] and not self.kicking:
            self.kicking = True
            self.kick_timer = pygame.time.get_ticks() + 300

        self.vel_y += GRAVITY
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        if self.rect.bottom >= SCREEN_HEIGHT - 40:
            self.rect.bottom = SCREEN_HEIGHT - 40
            self.vel_y = 0
            self.is_jumping = False

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

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
            
        screen.blit(img, self.rect)
        
        if self.kicking:
            kick_dir = 1 if self.side == 0 else -1
            # Desenhar um pequeno efeito de chute
            pygame.draw.circle(screen, YELLOW, (self.rect.centerx + kick_dir*40, self.rect.centery + 20), 10)
        
        if self.frozen:
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((0, 255, 255, 100))
            screen.blit(overlay, self.rect)

class Ball:
    def __init__(self):
        self.radius = 30
        self.img = pygame.transform.scale(Assets.ball, (60, 60))
        self.reset()
        self.low_gravity = False
        self.low_gravity_timer = 0
        self.angle = 0

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vel_x = 0
        self.vel_y = 0

    def update(self):
        now = pygame.time.get_ticks()
        if self.low_gravity and now > self.low_gravity_timer:
            self.low_gravity = False

        current_gravity = BALL_GRAVITY * 0.4 if self.low_gravity else BALL_GRAVITY
        self.vel_y += current_gravity
        
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_x *= BALL_FRICTION
        
        if abs(self.vel_x) > MAX_BALL_SPEED:
            self.vel_x = MAX_BALL_SPEED if self.vel_x > 0 else -MAX_BALL_SPEED
        if abs(self.vel_y) > MAX_BALL_VERTICAL_SPEED:
            self.vel_y = MAX_BALL_VERTICAL_SPEED if self.vel_y > 0 else -MAX_BALL_VERTICAL_SPEED

        if self.x - self.radius < 0:
            self.x = self.radius
            self.vel_x *= -BOUNCE
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vel_x *= -BOUNCE

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vel_y *= -BOUNCE

        if self.y + self.radius > SCREEN_HEIGHT - 40:
            self.y = SCREEN_HEIGHT - 40 - self.radius
            if abs(self.vel_y) < 1:
                self.vel_y = 0
            else:
                self.vel_y *= -BOUNCE
            self.vel_x *= FRICTION
            
        self.angle += self.vel_x * 2

    def draw(self, screen):
        rotated_ball = pygame.transform.rotate(self.img, -self.angle)
        new_rect = rotated_ball.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated_ball, new_rect.topleft)

class Goal:
    def __init__(self, side):
        self.side = side # 'left' or 'right'
        self.width = 60
        self.height = 160
        if side == 'left':
            self.rect = pygame.Rect(0, SCREEN_HEIGHT - 40 - self.height, self.width, self.height)
            self.img = Assets.goal_img
            self.anim = Animation(Assets.goal_anim, side=0)
        else:
            self.rect = pygame.Rect(SCREEN_WIDTH - self.width, SCREEN_HEIGHT - 40 - self.height, self.width, self.height)
            self.img = Assets.goal_img_r
            self.anim = Animation(Assets.goal_anim, side=1)

    def draw(self, screen):
        if self.anim.playing:
            self.anim.update()
            img = self.anim.get_image()
            screen.blit(img, (self.rect.x, self.rect.y))
        else:
            screen.blit(self.img, self.rect)

class PowerUp:
    def __init__(self):
        self.types = ["fire", "ice", "speed", "wind"]
        self.type = random.choice(self.types)
        self.radius = 15
        self.x = random.randint(100, SCREEN_WIDTH - 100)
        self.y = random.randint(100, SCREEN_HEIGHT - 150)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 7000
        
        self.colors = {"fire": ORANGE, "ice": CYAN, "speed": YELLOW, "wind": PURPLE}

    def draw(self, screen):
        color = self.colors[self.type]
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.radius, 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        pygame.display.set_caption("Head Soccer - Estilo Clássico")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 32, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 64, bold=True)
        
        self.bg_idx = random.randint(0, 5)
        self.reset_game()
        self.state = "START"

    def reset_game(self):
        self.p1 = Player(100, SCREEN_HEIGHT-150, "Brasil", 
                        {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'special': pygame.K_SPACE}, 0)
        self.p2 = Player(SCREEN_WIDTH-170, SCREEN_HEIGHT-150, "Argentina", 
                        {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'special': pygame.K_RETURN}, 1)
        self.ball = Ball()
        self.goal_left = Goal('left')
        self.goal_right = Goal('right')
        self.powerups = []
        self.last_powerup_spawn = pygame.time.get_ticks()
        self.game_time = 90
        self.start_ticks = 0
        self.goal_message = ""
        self.goal_timer = 0
        self.winner = ""

    def update(self):
        if self.state != "PLAYING":
            return

        now = pygame.time.get_ticks()
        seconds = (now - self.start_ticks) // 1000
        self.current_time = self.game_time - seconds
        
        if self.current_time <= 0:
            self.state = "END"
            if self.p1.score > self.p2.score: self.winner = "JOGADOR 1 VENCEU!"
            elif self.p2.score > self.p1.score: self.winner = "JOGADOR 2 VENCEU!"
            else: self.winner = "EMPATE!"

        self.p1.update()
        self.p2.update()
        self.ball.update()

        # Spawn Power-ups
        if now - self.last_powerup_spawn > 10000:
            self.powerups.append(PowerUp())
            self.last_powerup_spawn = now

        # Colisões Jogador-Bola
        for p in [self.p1, self.p2]:
            dist = math.hypot(self.ball.x - p.rect.centerx, self.ball.y - p.rect.centery)
            if dist < self.ball.radius + 35:
                # Física simples de rebatida
                angle = math.atan2(self.ball.y - p.rect.centery, self.ball.x - p.rect.centerx)
                force = 15
                if p.kicking:
                    force = p.kick_force * KICK_FORCE_MULTIPLIER
                    self.ball.vel_y = -KICK_UPWARD_FORCE
                    if p.super_kick: force *= 1.5
                
                self.ball.vel_x = math.cos(angle) * force
                # Impedir que a bola fique presa
                self.ball.x = p.rect.centerx + math.cos(angle) * (self.ball.radius + 36)

        # Colisões Power-up
        for pu in self.powerups[:]:
            for p in [self.p1, self.p2]:
                if math.hypot(p.rect.centerx - pu.x, p.rect.centery - pu.y) < 40:
                    if pu.type == "ice":
                        other = self.p2 if p == self.p1 else self.p1
                        other.frozen = True
                        other.freeze_timer = pygame.time.get_ticks() + 3000
                    elif pu.type == "wind":
                        self.ball.low_gravity = True
                        self.ball.low_gravity_timer = pygame.time.get_ticks() + 5000
                    else:
                        p.apply_powerup(pu.type)
                    self.powerups.remove(pu)
                    break
            if pu in self.powerups and now - pu.spawn_time > pu.lifetime:
                self.powerups.remove(pu)

        # Gols
        if self.goal_right.rect.collidepoint(self.ball.x, self.ball.y):
            self.p1.score += 1
            self.goal_right.anim.start()
            self.trigger_goal("GOL DO JOGADOR 1!")
        elif self.goal_left.rect.collidepoint(self.ball.x, self.ball.y):
            self.p2.score += 1
            self.goal_left.anim.start()
            self.trigger_goal("GOL DO JOGADOR 2!")

    def trigger_goal(self, msg):
        self.state = "GOAL"
        self.goal_message = msg
        self.goal_timer = pygame.time.get_ticks() + 2000

    def draw(self):
        # Background
        self.screen.blit(Assets.backgrounds[self.bg_idx], (0, 0))
        self.screen.blit(Assets.stadium, (0, 0))
        
        # Chão (visual)
        pygame.draw.rect(self.screen, (50, 50, 50), (0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40))

        self.goal_left.draw(self.screen)
        self.goal_right.draw(self.screen)
        
        for pu in self.powerups:
            pu.draw(self.screen)
            
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        self.ball.draw(self.screen)

        # UI
        s1 = self.font.render(f"{self.p1.name}: {self.p1.score}", True, WHITE)
        s2 = self.font.render(f"{self.p2.name}: {self.p2.score}", True, WHITE)
        self.screen.blit(s1, (50, 30))
        self.screen.blit(s2, (SCREEN_WIDTH - 250, 30))
        
        t_val = self.current_time if self.state == "PLAYING" else self.game_time
        timer_text = self.large_font.render(str(max(0, t_val)), True, WHITE)
        self.screen.blit(timer_text, (SCREEN_WIDTH//2 - 30, 20))

        if self.state == "START":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            start_text = self.large_font.render("HEAD SOCCER CLASSIC", True, YELLOW)
            hint_text = self.font.render("Pressione ENTER para começar", True, WHITE)
            self.screen.blit(start_text, (SCREEN_WIDTH//2 - 320, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(hint_text, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 50))

        elif self.state == "GOAL":
            goal_text = self.large_font.render(self.goal_message, True, YELLOW)
            self.screen.blit(goal_text, (SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2 - 50))
            if pygame.time.get_ticks() > self.goal_timer:
                self.ball.reset()
                self.p1.reset_position()
                self.p2.reset_position()
                self.state = "PLAYING"

        elif self.state == "END":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            win_text = self.large_font.render(self.winner, True, YELLOW)
            restart_text = self.font.render("Pressione R para reiniciar", True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 + 50))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.state == "START" and event.key == pygame.K_RETURN:
                        self.state = "PLAYING"
                        self.start_ticks = pygame.time.get_ticks()
                    if self.state == "END" and event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "PLAYING"
                        self.start_ticks = pygame.time.get_ticks()

            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
