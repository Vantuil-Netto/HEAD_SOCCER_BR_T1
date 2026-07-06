import pygame
import sys
import math
import random
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WHITE, BLACK, RED, BLUE, GREEN, YELLOW, GRAY,
    CHARACTERS, ARENAS, KICK_FORCE_MIN, KICK_FORCE_MAX,
    KICK_UPWARD_LOW_BALL, KICK_UPWARD_HIGH_BALL
)
from assets import Assets
from entities import Player, Ball, Goal

MUSIC_LOOP_EVENT = pygame.USEREVENT + 1


class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 80, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 44, bold=True)

        self.state = "SPLASH"
        self.menu_option = 0
        self.pause_option = 0
        self.field_select_option = 0

        self.p1_selected_char = 0
        self.p2_selected_char = 1
        self.current_arena_key: str = "Grama"
        self.game_mode: str = "2P"

        self._end_sound_played: bool = False
        self.reset_game()

    def reset_game(self) -> None:
        char1 = CHARACTERS[self.p1_selected_char]
        char2 = CHARACTERS[self.p2_selected_char]
        arena = ARENAS[self.current_arena_key]

        self.p1 = Player(180, SCREEN_HEIGHT - 220, char1, {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'special': pygame.K_SPACE}, 0, arena, self.current_arena_key)
        self.p2 = Player(SCREEN_WIDTH - 325, SCREEN_HEIGHT - 220, char2, {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'special': pygame.K_RETURN}, 1, arena, self.current_arena_key, is_ai=(self.game_mode == "1P"))
        self.ball = Ball(arena)
        self.goal_left = Goal(0, 0)
        self.goal_right = Goal(SCREEN_WIDTH - 125, 1)

        self.game_time = 60
        self.current_time = 60
        self.start_ticks = 0
        self.winner = ""
        self.last_conceded_by = 0
        self.is_golden_goal = False
        self._end_sound_played = False

    def update(self) -> None:
        if self.state == "PLAYING":
            now = pygame.time.get_ticks()
            self.current_time = self.game_time - (now - self.start_ticks) // 1000

            if self.p1.score >= 3:
                self.state = "END"
                self.winner = f"{self.p1.name} VENCEU! (3 GOLS)"
            elif self.p2.score >= 3:
                self.state = "END"
                self.winner = f"{self.p2.name} VENCEU! (3 GOLS)"
            elif self.current_time <= 0:
                if self.p1.score > self.p2.score:
                    self.state = "END"
                    self.winner = f"{self.p1.name} VENCEU!"
                elif self.p2.score > self.p1.score:
                    self.state = "END"
                    self.winner = f"{self.p2.name} VENCEU!"
                else:
                    self.state = "GOLDEN_GOAL"
                    self.is_golden_goal = True
                    self.game_time = 30
                    self.current_time = 30
                    self.start_ticks = pygame.time.get_ticks()

            self.p1.update()
            self.p2.update(self.ball.x, self.ball.y)
            self.ball.update()
            self.check_collisions()

        elif self.state == "GOLDEN_GOAL":
            now = pygame.time.get_ticks()
            self.current_time = self.game_time - (now - self.start_ticks) // 1000

            if self.current_time <= 0:
                self.state = "END"
                self.winner = "EMPATE! (Ninguém marcou no Golden Goal)"

            self.p1.update()
            self.p2.update(self.ball.x, self.ball.y)
            self.ball.update()
            self.check_collisions()

        elif self.state == "PAUSED":
            pass
        elif self.state == "FIELD_SELECT":
            pass

    def check_collisions(self) -> None:
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
            collided_with_shoe = False
            if hasattr(p, 'shoe_hitbox') and p.shoe_hitbox.colliderect(ball_rect):
                collided_with_shoe = True
                Assets.hit_sound.play()
                dx = self.ball.x - p.shoe_hitbox.centerx
                dy = self.ball.y - p.shoe_hitbox.centery
                angle = math.atan2(dy, dx)

                if p.kicking:
                    force = random.uniform(KICK_FORCE_MIN, KICK_FORCE_MAX)
                    vertical_boost = KICK_UPWARD_LOW_BALL if self.ball.y > SCREEN_HEIGHT - 140 else KICK_UPWARD_HIGH_BALL

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
                else:
                    bounce_force = 10
                    self.ball.vel_x = math.cos(angle) * bounce_force
                    self.ball.vel_y = math.sin(angle) * bounce_force

                    dist = math.hypot(dx, dy)
                    overlap = (self.ball.radius + 75) - dist
                    if overlap > 0:
                        self.ball.x += math.cos(angle) * overlap
                        self.ball.y += math.sin(angle) * overlap

            if not collided_with_shoe:
                dx = self.ball.x - p.rect.centerx
                dy = self.ball.y - p.rect.centery
                dist = math.hypot(dx, dy)
                collision_dist = 67 + self.ball.radius

                if dist < collision_dist and dist > 0:
                    Assets.hit_sound.play()
                    angle = math.atan2(dy, dx)
                    force = 10

                    self.ball.vel_x += math.cos(angle) * force
                    self.ball.vel_y += math.sin(angle) * force

                    overlap = collision_dist - dist
                    self.ball.x += math.cos(angle) * overlap
                    self.ball.y += math.sin(angle) * overlap

        ball_rect = pygame.Rect(self.ball.x - self.ball.radius, self.ball.y - self.ball.radius, self.ball.radius * 2, self.ball.radius * 2)
        for goal in [self.goal_left, self.goal_right]:
            if ball_rect.colliderect(goal.crossbar):
                Assets.hit_sound.play()
                if self.ball.y < goal.crossbar.centery:
                    self.ball.y = goal.crossbar.top - self.ball.radius
                    if self.ball.vel_y > 0:
                        self.ball.vel_y = -self.ball.vel_y * 0.75
                else:
                    self.ball.y = goal.crossbar.bottom + self.ball.radius
                    if self.ball.vel_y < 0:
                        self.ball.vel_y = -self.ball.vel_y * 0.75

        if self.goal_right.rect.collidepoint(self.ball.x, self.ball.y):
            self.p1.score += 1
            Assets.goal_sound.play(maxtime=5000)
            if self.is_golden_goal:
                self.state = "END"
                self.winner = f"{self.p1.name} VENCEU! (GOL DE OURO)"
            else:
                self.trigger_goal(f"GOL DE {self.p1.name.upper()}!", conceded_by=2)
        elif self.goal_left.rect.collidepoint(self.ball.x, self.ball.y):
            self.p2.score += 1
            Assets.goal_sound.play(maxtime=5000)
            if self.is_golden_goal:
                self.state = "END"
                self.winner = f"{self.p2.name} VENCEU! (GOL DE OURO)"
            else:
                self.trigger_goal(f"GOL DE {self.p2.name.upper()}!", conceded_by=1)

    def trigger_goal(self, msg: str, conceded_by: int) -> None:
        self.state = "GOAL"
        self.goal_message = msg
        self.goal_timer = pygame.time.get_ticks() + 2000
        self.last_conceded_by = conceded_by

    def draw_splash(self) -> None:
        self.screen.blit(Assets.start_background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        alpha = 128 + math.sin(pygame.time.get_ticks() * 0.005) * 127
        txt = self.button_font.render("PRESSIONE QUALQUER BOTÃO", True, WHITE)
        txt.set_alpha(int(alpha))
        self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT - 150))
        pygame.display.flip()

    def draw_button(self, text: str, y: int, selected: bool, mouse_pos=None):
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

    def draw_menu(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.screen.blit(Assets.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        logo_x = SCREEN_WIDTH // 2 - Assets.logo.get_width() // 2
        logo_y = 60
        self.screen.blit(Assets.logo, (logo_x, logo_y))

        options = ["1 Jogador", "2 Jogadores", "Sair"]
        self.menu_buttons = []
        for i, option in enumerate(options):
            rect = self.draw_button(option, 280 + i * 110, i == self.menu_option, mouse_pos)
            self.menu_buttons.append(rect)
        pygame.display.flip()

    def draw_pause(self) -> None:
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

    def draw_character_select(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.screen.blit(Assets.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title_text = self.large_font.render("SELEÇÃO DE PERSONAGENS", True, YELLOW)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 40))

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
            self.screen.blit(name_text, (draw_rect.centerx - name_text.get_width() // 2, draw_rect.bottom - 30))

            if idx == self.p1_selected_char:
                pygame.draw.rect(self.screen, GREEN, draw_rect, 5, border_radius=15)
            if idx == self.p2_selected_char and self.game_mode == "2P":
                pygame.draw.rect(self.screen, BLUE, draw_rect, 5, border_radius=15)

        if self.game_mode == "1P":
            hint_text1 = self.font.render("P1: WASD + ESPAÇO", True, GREEN)
            hint_text3 = self.font.render("ENTER: Começar", True, YELLOW)
            self.screen.blit(hint_text1, (50, SCREEN_HEIGHT - 60))
            self.screen.blit(hint_text3, (SCREEN_WIDTH // 2 - hint_text3.get_width() // 2, SCREEN_HEIGHT - 60))
        else:
            hint_text1 = self.font.render("P1: WASD + ESPAÇO", True, GREEN)
            hint_text2 = self.font.render("P2: SETAS + ENTER", True, BLUE)
            hint_text3 = self.font.render("ENTER: Começar", True, YELLOW)
            self.screen.blit(hint_text1, (50, SCREEN_HEIGHT - 60))
            self.screen.blit(hint_text3, (SCREEN_WIDTH // 2 - hint_text3.get_width() // 2, SCREEN_HEIGHT - 60))
            self.screen.blit(hint_text2, (SCREEN_WIDTH - 50 - hint_text2.get_width(), SCREEN_HEIGHT - 60))
        pygame.display.flip()

    def draw_field_select(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.screen.blit(Assets.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        title_text = self.large_font.render("SELECIONE O CAMPO", True, YELLOW)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 40))

        arena_list = list(ARENAS.items())
        key, data = arena_list[self.field_select_option]

        preview_w, preview_h = 400, 400
        preview_x = SCREEN_WIDTH // 2 - preview_w // 2
        preview_y = 130
        preview_rect = pygame.Rect(preview_x, preview_y, preview_w, preview_h)
        self.field_rects = [preview_rect]

        shadow = preview_rect.copy()
        shadow.x += 8
        shadow.y += 8
        pygame.draw.rect(self.screen, (0, 0, 0, 80), shadow, border_radius=12)
        pygame.draw.rect(self.screen, (30, 30, 30), preview_rect, border_radius=12)
        inner_rect = preview_rect.inflate(-12, -12)
        self.screen.blit(Assets.arena_previews[key], inner_rect.topleft)
        pygame.draw.rect(self.screen, YELLOW, preview_rect, 4, border_radius=12)

        arrow_y = preview_y + preview_h // 2 - 25
        lx = preview_x - 60
        rx = preview_x + preview_w + 20
        left_arrow_rect = pygame.Rect(lx, arrow_y, 50, 50)
        right_arrow_rect = pygame.Rect(rx, arrow_y, 50, 50)
        self.field_rects.extend([left_arrow_rect, right_arrow_rect])

        l_hover = left_arrow_rect.collidepoint(mouse_pos)
        r_hover = right_arrow_rect.collidepoint(mouse_pos)
        l_color = (100, 100, 100) if l_hover else (50, 50, 50)
        r_color = (100, 100, 100) if r_hover else (50, 50, 50)

        for r, c in ((left_arrow_rect, l_color), (right_arrow_rect, r_color)):
            pygame.draw.rect(self.screen, (0, 0, 0), (r.x + 3, r.y + 3, r.w, r.h), border_radius=8)
            pygame.draw.rect(self.screen, c, r, border_radius=8)

        arr = self.font.render("<", True, WHITE)
        self.screen.blit(arr, (left_arrow_rect.centerx - arr.get_width() // 2, left_arrow_rect.centery - arr.get_height() // 2))
        arr = self.font.render(">", True, WHITE)
        self.screen.blit(arr, (right_arrow_rect.centerx - arr.get_width() // 2, right_arrow_rect.centery - arr.get_height() // 2))

        name_text = self.button_font.render(data["label"], True, WHITE)
        self.screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, preview_y + preview_h + 20))

        hint_text = self.font.render("← →: Navegar    ENTER: Confirmar    ESC: Voltar", True, (200, 200, 200))
        self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 60))
        pygame.display.flip()

    def draw(self) -> None:
        if self.state == "SPLASH":
            self.draw_splash()
            return
        elif self.state == "MENU":
            self.draw_menu()
            return
        elif self.state == "CHARACTER_SELECT":
            self.draw_character_select()
            return
        elif self.state == "FIELD_SELECT":
            self.draw_field_select()
            return

        self.screen.blit(Assets.arena_backgrounds[self.current_arena_key], (0, 0))

        self.goal_left.draw(self.screen)
        self.goal_right.draw(self.screen)
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        self.ball.draw(self.screen)

        p1_label = self.small_font.render(self.p1.name, True, BLACK)
        p1_score = self.large_font.render(str(self.p1.score), True, BLACK)
        self.screen.blit(p1_label, (50, 15))
        self.screen.blit(p1_score, (50, 45))

        p2_name_display = f"{self.p2.name} (CPU)" if self.game_mode == "1P" else self.p2.name
        p2_label = self.small_font.render(p2_name_display, True, BLACK)
        p2_score = self.large_font.render(str(self.p2.score), True, BLACK)
        self.screen.blit(p2_label, (SCREEN_WIDTH - 50 - p2_label.get_width(), 15))
        self.screen.blit(p2_score, (SCREEN_WIDTH - 50 - p2_score.get_width(), 45))

        t_val = self.current_time if self.state in ["PLAYING", "GOLDEN_GOAL"] else self.game_time
        timer_color = YELLOW if self.state == "GOLDEN_GOAL" else BLACK
        timer_text = self.large_font.render(str(max(0, t_val)), True, timer_color)
        self.screen.blit(timer_text, (SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 20))

        if self.state == "PAUSED":
            self.draw_pause()
        elif self.state == "GOAL":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
            goal_text = self.large_font.render(self.goal_message, True, YELLOW)
            self.screen.blit(goal_text, (SCREEN_WIDTH // 2 - goal_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            if pygame.time.get_ticks() > self.goal_timer:
                self.ball.reset(conceded_by=self.last_conceded_by)
                self.p1.reset_position()
                self.p2.reset_position()
                self.state = "PLAYING"
                self.start_ticks += 2000
        elif self.state == "GOLDEN_GOAL":
            if pygame.time.get_ticks() - self.start_ticks < 3000:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))
                self.screen.blit(overlay, (0, 0))
                golden_text = self.large_font.render("GOL DE OURO!", True, YELLOW)
                self.screen.blit(golden_text, (SCREEN_WIDTH // 2 - golden_text.get_width() // 2, SCREEN_HEIGHT // 2))
        elif self.state == "END":
            if not self._end_sound_played:
                Assets.whistle_end.play()
                self._end_sound_played = True
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            win_text = self.large_font.render(self.winner, True, YELLOW)
            restart_text = self.font.render("Pressione R para voltar ao menu", True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

        pygame.display.flip()

    def _start_menu_music(self) -> None:
        pygame.mixer.music.play(start=33.0)
        pygame.time.set_timer(MUSIC_LOOP_EVENT, 228000)

    def _stop_menu_music(self) -> None:
        pygame.mixer.music.stop()
        pygame.time.set_timer(MUSIC_LOOP_EVENT, 0)

    def run(self) -> None:
        self._start_menu_music()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MUSIC_LOOP_EVENT:
                    if self.state in ("SPLASH", "MENU", "CHARACTER_SELECT", "FIELD_SELECT"):
                        pygame.mixer.music.play(start=33.0)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "SPLASH":
                        self.state = "MENU"
                    elif self.state == "MENU" and event.button == 1:
                        for i, rect in enumerate(self.menu_buttons):
                            if rect.collidepoint(event.pos):
                                if i == 0:
                                    self.game_mode = "1P"
                                    self.state = "CHARACTER_SELECT"
                                elif i == 1:
                                    self.game_mode = "2P"
                                    self.state = "CHARACTER_SELECT"
                                else:
                                    pygame.quit()
                                    sys.exit()
                    elif self.state == "PAUSED" and event.button == 1:
                        for i, rect in enumerate(self.pause_buttons):
                            if rect.collidepoint(event.pos):
                                if i == 0:
                                    self.state = "PLAYING"
                                    self.start_ticks += (pygame.time.get_ticks() - self.pause_start_ticks)
                                elif i == 1:
                                    self.reset_game()
                                    self.state = "PLAYING"
                                    Assets.whistle_start.play()
                                    self._stop_menu_music()
                                    self.start_ticks = pygame.time.get_ticks()
                                elif i == 2:
                                    self.state = "MENU"
                                    self._start_menu_music()
                    elif self.state == "CHARACTER_SELECT":
                        for i, rect in enumerate(self.char_rects):
                            if rect.collidepoint(event.pos):
                                if event.button == 1:
                                    self.p1_selected_char = i
                                elif event.button == 3 and self.game_mode == "2P":
                                    self.p2_selected_char = i
                    elif self.state == "FIELD_SELECT" and event.button == 1:
                        for i, rect in enumerate(self.field_rects):
                            if rect.collidepoint(event.pos):
                                if i == 0:
                                    self.current_arena_key = list(ARENAS.keys())[self.field_select_option]
                                    self.reset_game()
                                    self.state = "PLAYING"
                                    Assets.whistle_start.play()
                                    self._stop_menu_music()
                                    self.start_ticks = pygame.time.get_ticks()
                                elif i == 1:
                                    self.field_select_option = (self.field_select_option - 1) % len(ARENAS)
                                elif i == 2:
                                    self.field_select_option = (self.field_select_option + 1) % len(ARENAS)

                if event.type == pygame.KEYDOWN:
                    if self.state == "SPLASH":
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                        else:
                            self.state = "MENU"
                    elif self.state == "MENU":
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            self.menu_option = (self.menu_option - 1) % 3
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            self.menu_option = (self.menu_option + 1) % 3
                        elif event.key == pygame.K_RETURN:
                            if self.menu_option == 0:
                                self.game_mode = "1P"
                                self.state = "CHARACTER_SELECT"
                            elif self.menu_option == 1:
                                self.game_mode = "2P"
                                self.state = "CHARACTER_SELECT"
                            else:
                                pygame.quit()
                                sys.exit()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "SPLASH"

                    elif self.state == "CHARACTER_SELECT":
                        if event.key == pygame.K_w:
                            self.p1_selected_char = (self.p1_selected_char - 2) % 4
                        elif event.key == pygame.K_s:
                            self.p1_selected_char = (self.p1_selected_char + 2) % 4
                        elif event.key == pygame.K_a:
                            if self.p1_selected_char % 2 == 1:
                                self.p1_selected_char -= 1
                        elif event.key == pygame.K_d:
                            if self.p1_selected_char % 2 == 0:
                                self.p1_selected_char += 1

                        if self.game_mode == "2P":
                            if event.key == pygame.K_UP:
                                self.p2_selected_char = (self.p2_selected_char - 2) % 4
                            elif event.key == pygame.K_DOWN:
                                self.p2_selected_char = (self.p2_selected_char + 2) % 4
                            elif event.key == pygame.K_LEFT:
                                if self.p2_selected_char % 2 == 1:
                                    self.p2_selected_char -= 1
                            elif event.key == pygame.K_RIGHT:
                                if self.p2_selected_char % 2 == 0:
                                    self.p2_selected_char += 1

                        if self.game_mode == "1P":
                            self.p2_selected_char = (self.p1_selected_char + 1) % 4

                        if event.key == pygame.K_RETURN:
                            self.state = "FIELD_SELECT"
                            self.field_select_option = 0
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "MENU"

                    elif self.state == "FIELD_SELECT":
                        if event.key in (pygame.K_a, pygame.K_LEFT):
                            self.field_select_option = (self.field_select_option - 1) % len(ARENAS)
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            self.field_select_option = (self.field_select_option + 1) % len(ARENAS)
                        elif event.key == pygame.K_RETURN:
                            self.current_arena_key = list(ARENAS.keys())[self.field_select_option]
                            self.reset_game()
                            self.state = "PLAYING"
                            Assets.whistle_start.play()
                            self._stop_menu_music()
                            self.start_ticks = pygame.time.get_ticks()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "CHARACTER_SELECT"

                    elif self.state == "PLAYING":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "PAUSED"
                            self.pause_start_ticks = pygame.time.get_ticks()

                    elif self.state == "PAUSED":
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            self.pause_option = (self.pause_option - 1) % 3
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            self.pause_option = (self.pause_option + 1) % 3
                        elif event.key == pygame.K_RETURN:
                            if self.pause_option == 0:
                                self.state = "PLAYING"
                                self.start_ticks += (pygame.time.get_ticks() - self.pause_start_ticks)
                            elif self.pause_option == 1:
                                self.reset_game()
                                self.state = "PLAYING"
                                Assets.whistle_start.play()
                                self._stop_menu_music()
                                self.start_ticks = pygame.time.get_ticks()
                            elif self.pause_option == 2:
                                self.state = "MENU"
                                self._start_menu_music()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "PLAYING"
                            self.start_ticks += (pygame.time.get_ticks() - self.pause_start_ticks)

                    elif self.state == "END" and event.key == pygame.K_r:
                        self.state = "MENU"
                        self._start_menu_music()

            self.update()
            self.draw()
            self.clock.tick(FPS)
