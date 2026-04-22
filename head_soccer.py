import pygame
import random
import math
import sys

# --- Configurações Iniciais ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_desktop_sizes()[0]
FPS = 60

# === FÍSICA ARCADE ===
# Gravidade do jogador
GRAVITY = 0.6

# Gravidade da bola (leve e responsiva)
BALL_GRAVITY = 0.35

# Bounce (quanto mais alto, mais "viva" a bola fica)
BOUNCE = 0.75  # Aumentado para mais energia

# Atrito aéreo (quanto mais alto, mais lento diminui a velocidade)
BALL_FRICTION = 0.99
FRICTION = 0.98  # Atrito no chão

# Limites de velocidade (evita bugs e voo infinito)
MAX_BALL_SPEED = 25
MAX_BALL_VERTICAL_SPEED = 30

# Força de chute arcade (exagerada para se sentir bem)
KICK_FORCE_MULTIPLIER = 1.2  # Multiplicador para aumentar "punch" do chute
KICK_UPWARD_FORCE = 12  # Força vertical do chute (arcade - exagerada)

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

# --- Classes do Jogo ---

class Player:
    def __init__(self, x, y, color, name, controls, ability):
        self.initial_x = x
        self.initial_y = y
        self.rect = pygame.Rect(x, y, 69, 92)  # Aumentado em 15%
        self.color = color
        self.name = name
        self.controls = controls # {left, right, jump, special}
        self.ability = ability
        
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 10  # Aumentado para jogador mais rápido
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
        
        # Animação de chute
        self.kicking = False
        self.kick_timer = 0
        
        # Ajustes baseados no personagem
        if name == "Bolt": # Chute forte, velocidade média
            self.kick_force = 22
        elif name == "Frost": # Pulo alto, mais rápido
            self.speed = 11  # Aumentado para Frost mais rápido
            self.kick_force = 22

    def reset_position(self):
        self.rect.x = self.initial_x
        self.rect.y = self.initial_y
        self.vel_x = 0
        self.vel_y = 0

    def apply_powerup(self, type):
        if type == "fire":
            self.super_kick = True
            self.super_kick_timer = pygame.time.get_ticks() + 5000
        elif type == "ice":
            # O outro jogador deve ser congelado, a lógica está no Game.update
            pass 
        elif type == "speed":
            self.speed_boost = True
            self.speed_timer = pygame.time.get_ticks() + 5000

    def update(self):
        now = pygame.time.get_ticks()
        
        # Gerenciar Timers de Power-ups
        if self.frozen and now > self.freeze_timer:
            self.frozen = False
        if self.speed_boost and now > self.speed_timer:
            self.speed_boost = False
        if self.super_kick and now > self.super_kick_timer:
            self.super_kick = False
        
        # Gerenciar animação de chute
        if self.kicking and now > self.kick_timer:
            self.kicking = False

        if self.frozen:
            return

        keys = pygame.key.get_pressed()
        
        # Movimentação Horizontal
        current_speed = self.speed * 1.5 if self.speed_boost else self.speed
        if keys[self.controls['left']]:
            self.vel_x = -current_speed
        elif keys[self.controls['right']]:
            self.vel_x = current_speed
        else:
            self.vel_x = 0

        # Pulo
        if keys[self.controls['jump']] and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True

        # Animação de chute
        if keys[self.controls['special']] and not self.kicking:
            self.kicking = True
            self.kick_timer = pygame.time.get_ticks() + 300  # 300ms

        # Gravidade
        self.vel_y += GRAVITY
        
        # Atualizar Posição
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Colisão com o chão
        if self.rect.bottom >= SCREEN_HEIGHT - 20:
            self.rect.bottom = SCREEN_HEIGHT - 20
            self.vel_y = 0
            self.is_jumping = False

        # Limites da tela
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

    def draw(self, screen):
        # Corpo
        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
        # Cabeça (estilo Head Soccer)
        head_rect = pygame.Rect(self.rect.centerx - 25, self.rect.top - 40, 50, 50)
        pygame.draw.ellipse(screen, self.color, head_rect)
        # Olhos
        eye_color = WHITE
        eye_x_offset = 15 if self.initial_x < SCREEN_WIDTH/2 else -15
        pygame.draw.circle(screen, eye_color, (head_rect.centerx + eye_x_offset, head_rect.centery - 5), 5)
        
        # Animação de chute
        if self.kicking:
            kick_dir = 1 if self.initial_x < SCREEN_WIDTH/2 else -1
            kick_start = (self.rect.centerx, self.rect.bottom)
            kick_end = (self.rect.centerx + kick_dir * 50, self.rect.centery)
            pygame.draw.line(screen, self.color, kick_start, kick_end, 14)  # Aumentado para 14
        
        # Indicador de Power-up
        if self.frozen:
            pygame.draw.rect(screen, CYAN, self.rect, 3, border_radius=10)
        if self.speed_boost:
            pygame.draw.rect(screen, YELLOW, self.rect, 3, border_radius=10)
        if self.super_kick:
            pygame.draw.rect(screen, ORANGE, self.rect, 3, border_radius=10)

class Ball:
    def __init__(self):
        self.radius = 30  # Aumentado em 100%
        self.reset()
        self.low_gravity = False
        self.low_gravity_timer = 0

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vel_x = 0
        self.vel_y = 0

    def update(self):
        now = pygame.time.get_ticks()
        if self.low_gravity and now > self.low_gravity_timer:
            self.low_gravity = False

        # Gravidade (reduzida para bola flutuar mais)
        current_gravity = BALL_GRAVITY * 0.4 if self.low_gravity else BALL_GRAVITY
        self.vel_y += current_gravity
        
        # Movimento
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Atrito aéreo (apenas horizontal)
        self.vel_x *= BALL_FRICTION
        
        # === LIMITES DE VELOCIDADE (ARCADE) ===
        if abs(self.vel_x) > MAX_BALL_SPEED:
            self.vel_x = MAX_BALL_SPEED if self.vel_x > 0 else -MAX_BALL_SPEED
        if abs(self.vel_y) > MAX_BALL_VERTICAL_SPEED:
            self.vel_y = MAX_BALL_VERTICAL_SPEED if self.vel_y > 0 else -MAX_BALL_VERTICAL_SPEED

        # Colisão com as paredes
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vel_x *= -BOUNCE
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vel_x *= -BOUNCE

        # Colisão com o teto
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vel_y *= -BOUNCE

        # Colisão com o chão
        if self.y + self.radius > SCREEN_HEIGHT - 20:
            self.y = SCREEN_HEIGHT - 20 - self.radius
            
            # === BOUNCE ARCADE ===
            if abs(self.vel_y) < 1:
                self.vel_y = 0
            else:
                self.vel_y *= -BOUNCE
            
            # Atrito no chão
            self.vel_x *= FRICTION

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 2)
        if self.low_gravity:
            pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)), self.radius + 4, 2)

class Goal:
    def __init__(self, side):
        self.side = side # 'left' or 'right'
        self.width = 48  # Aumentado em 20%
        self.height = 180  # Aumentado em 20%
        if side == 'left':
            self.rect = pygame.Rect(0, SCREEN_HEIGHT - 20 - self.height, self.width, self.height)
        else:
            self.rect = pygame.Rect(SCREEN_WIDTH - self.width, SCREEN_HEIGHT - 20 - self.height, self.width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        # Rede
        for i in range(0, self.height, 20):
            pygame.draw.line(screen, GRAY, (self.rect.left, self.rect.top + i), (self.rect.right, self.rect.top + i))
        for i in range(0, self.width, 10):
            pygame.draw.line(screen, GRAY, (self.rect.left + i, self.rect.top), (self.rect.left + i, self.rect.bottom))

class PowerUp:
    def __init__(self):
        self.types = ["fire", "ice", "speed", "wind"] # Super chute, Congelar, Velocidade, Bola leve
        self.type = random.choice(self.types)
        self.radius = 15
        self.x = random.randint(100, SCREEN_WIDTH - 100)
        self.y = random.randint(100, SCREEN_HEIGHT - 150)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 7000 # 7 segundos
        
        self.colors = {
            "fire": ORANGE,
            "ice": CYAN,
            "speed": YELLOW,
            "wind": PURPLE
        }

    def draw(self, screen):
        color = self.colors[self.type]
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.radius, 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Head Soccer Python")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 32, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 64, bold=True)
        
        self.reset_game()
        self.state = "START" # START, PLAYING, GOAL, END

    def reset_game(self):
        # Jogador 1: A, D, W, Espaço
        self.p1 = Player(100, SCREEN_HEIGHT - 100, RED, "Bolt", 
                        {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'special': pygame.K_SPACE}, 
                        "Super Kick")
        
        # Jogador 2: Setas, Enter
        self.p2 = Player(SCREEN_WIDTH - 160, SCREEN_HEIGHT - 100, BLUE, "Frost", 
                        {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'special': pygame.K_RETURN}, 
                        "High Jump")
        
        self.ball = Ball()
        self.goal_left = Goal('left')
        self.goal_right = Goal('right')
        
        self.powerups = []
        self.last_powerup_spawn = pygame.time.get_ticks()
        
        self.game_time = 120 # 120 segundos
        self.start_ticks = 0
        self.goal_message_timer = 0
        self.winner = ""

    def handle_collisions(self):
        # Bola e Jogadores
        for p in [self.p1, self.p2]:
            # Criar um círculo aproximado para o jogador (cabeça + corpo)
            player_center = p.rect.center
            dist = math.hypot(self.ball.x - player_center[0], self.ball.y - player_center[1])
            
            if dist < self.ball.radius + 40: # 40 é o raio aproximado do jogador
                # Vetor de colisão
                dx = self.ball.x - player_center[0]
                dy = self.ball.y - player_center[1]
                angle = math.atan2(dy, dx)
                
                # === FORÇA DO CHUTE ARCADE ===
                force = p.kick_force * 1.5 if p.super_kick else p.kick_force
                force *= KICK_FORCE_MULTIPLIER
                
                # Se o jogador está chutando, aplicar física arcade baseada no ângulo do pé
                if p.kicking:
                    # Calcular o ângulo da linha do pé (do chão até o peito)
                    kick_dir = 1 if p.initial_x < SCREEN_WIDTH/2 else -1
                    foot_start = (p.rect.centerx, p.rect.bottom)
                    foot_end = (p.rect.centerx + kick_dir * 50, p.rect.centery)

                    # Calcular vetor do pé
                    foot_dx = foot_end[0] - foot_start[0]
                    foot_dy = foot_end[1] - foot_start[1]
                    foot_length = math.hypot(foot_dx, foot_dy)

                    if foot_length > 0:
                        # Normalizar vetor do pé
                        foot_dx /= foot_length
                        foot_dy /= foot_length

                        # === SISTEMA DE SPIN (OPCIONAL) ===
                        spin_factor = 1.0 + (abs(p.vel_x) * 0.02)

                        # Bias horizontal: garante componente para frente mesmo em chute mais vertical
                        min_horiz = 0.5
                        horiz = max(abs(foot_dx), min_horiz)
                        horiz_sign = 1 if foot_dx >= 0 else -1

                        # Aplicar velocidade na direção do pé, com bias para frente e menor upward
                        self.ball.vel_x = horiz_sign * horiz * force * spin_factor + p.vel_x * 0.35
                        # vertical reduzida para não enviar muito pra cima; mantém responsividade
                        self.ball.vel_y = foot_dy * force * 0.45 + p.vel_y * 0.25 - (KICK_UPWARD_FORCE * 0.35)
                else:
                    # Chute normal (sem animação)
                    self.ball.vel_x = math.cos(angle) * force + p.vel_x * 0.3
                    self.ball.vel_y = math.sin(angle) * force + p.vel_y * 0.3
                    # Se o jogador está pulando, aumentar vel_y negativo
                    if p.is_jumping:
                        self.ball.vel_y -= 6
                
                # Empurrar a bola para fora do jogador para evitar prender
                self.ball.x = player_center[0] + math.cos(angle) * (self.ball.radius + 45)
                self.ball.y = player_center[1] + math.sin(angle) * (self.ball.radius + 45)

        # Bola e Gols (Traves)
        for goal in [self.goal_left, self.goal_right]:
            if goal.rect.collidepoint(self.ball.x, self.ball.y):
                # Se bater na parte de cima do gol (trave)
                if abs(self.ball.y - goal.rect.top) < 10:
                    self.ball.vel_y *= -1
                    self.ball.y = goal.rect.top - self.ball.radius
                else:
                    self.ball.vel_x *= -1
        
        # Detecção de Gol
        if self.ball.x < self.goal_left.rect.right and self.ball.y > self.goal_left.rect.top:
            self.p2.score += 1
            self.trigger_goal("GOL PARA FROST!")
        elif self.ball.x > self.goal_right.rect.left and self.ball.y > self.goal_right.rect.top:
            self.p1.score += 1
            self.trigger_goal("GOL PARA BOLT!")

        # Jogadores e Power-ups
        now = pygame.time.get_ticks()
        for pw in self.powerups[:]:
            for p in [self.p1, self.p2]:
                dist = math.hypot(p.rect.centerx - pw.x, p.rect.centery - pw.y)
                if dist < pw.radius + 30:
                    # Aplicar poder
                    if pw.type == "ice":
                        other = self.p2 if p == self.p1 else self.p1
                        other.frozen = True
                        other.freeze_timer = now + 3000 # 3 segundos
                    elif pw.type == "wind":
                        self.ball.low_gravity = True
                        self.ball.low_gravity_timer = now + 6000 # 6 segundos
                    else:
                        p.apply_powerup(pw.type)
                    
                    self.powerups.remove(pw)
                    break

    def trigger_goal(self, msg):
        self.state = "GOAL"
        self.goal_message = msg
        self.goal_message_timer = pygame.time.get_ticks() + 2000
        if self.p1.score >= 5 or self.p2.score >= 5:
            self.end_game()

    def end_game(self):
        self.state = "END"
        if self.p1.score > self.p2.score:
            self.winner = "BOLT VENCEU!"
        elif self.p2.score > self.p1.score:
            self.winner = "FROST VENCEU!"
        else:
            self.winner = "EMPATE!"

    def update(self):
        if self.state == "START":
            self.current_time = self.game_time
            return
            
        if self.state == "PLAYING":
            # Timer
            seconds_passed = (pygame.time.get_ticks() - self.start_ticks) // 1000
            self.current_time = max(0, self.game_time - seconds_passed)
            if self.current_time <= 0:
                self.end_game()

            # Power-up Spawn
            now = pygame.time.get_ticks()
            if now - self.last_powerup_spawn > 10000: # A cada 10 segundos
                if len(self.powerups) < 2:
                    self.powerups.append(PowerUp())
                self.last_powerup_spawn = now
            
            # Limpar power-ups expirados
            for pw in self.powerups[:]:
                if now - pw.spawn_time > pw.lifetime:
                    self.powerups.remove(pw)

            self.p1.update()
            self.p2.update()
            self.ball.update()
            self.handle_collisions()

        elif self.state == "GOAL":
            if pygame.time.get_ticks() > self.goal_message_timer:
                if self.state != "END":
                    self.state = "PLAYING"
                    self.ball.reset()
                    self.p1.reset_position()
                    self.p2.reset_position()

    def draw(self):
        # Fundo (Campo)
        self.screen.fill(GREEN)
        # Chão
        pygame.draw.rect(self.screen, GRAY, (0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20))
        # Linha central
        pygame.draw.line(self.screen, WHITE, (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT-20), 2)
        pygame.draw.circle(self.screen, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 50, 2)

        # Objetos
        self.goal_left.draw(self.screen)
        self.goal_right.draw(self.screen)
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        self.ball.draw(self.screen)
        
        for pw in self.powerups:
            pw.draw(self.screen)

        # Interface
        p1_text = self.font.render(f"BOLT: {self.p1.score}", True, RED)
        p2_text = self.font.render(f"FROST: {self.p2.score}", True, BLUE)
        time_text = self.font.render(f"TEMPO: {getattr(self, 'current_time', 120)}s", True, WHITE)
        
        self.screen.blit(p1_text, (50, 20))
        self.screen.blit(p2_text, (SCREEN_WIDTH - 200, 20))
        self.screen.blit(time_text, (SCREEN_WIDTH // 2 - 70, 20))

        if self.state == "START":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            start_text = self.large_font.render("HEAD SOCCER PYTHON", True, YELLOW)
            hint_text = self.font.render("Pressione ENTER para começar", True, WHITE)
            self.screen.blit(start_text, (SCREEN_WIDTH//2 - 320, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(hint_text, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 50))
            
            # Controles Info
            c1 = self.font.render("P1: W,A,D | Espaço", True, RED)
            c2 = self.font.render("P2: Setas | Enter", True, BLUE)
            self.screen.blit(c1, (100, SCREEN_HEIGHT - 100))
            self.screen.blit(c2, (SCREEN_WIDTH - 350, SCREEN_HEIGHT - 100))

        elif self.state == "GOAL":
            goal_text = self.large_font.render(self.goal_message, True, YELLOW)
            self.screen.blit(goal_text, (SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 50))

        elif self.state == "END":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            win_text = self.large_font.render(self.winner, True, YELLOW)
            restart_text = self.font.render("Pressione R para reiniciar", True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 + 50))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
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
