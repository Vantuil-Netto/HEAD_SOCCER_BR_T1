import pygame
import math
import random
import os
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, BALL_GRAVITY, BOUNCE,
    BALL_FRICTION, FRICTION, MAX_BALL_SPEED, MAX_BALL_VERTICAL_SPEED,
    KICK_FORCE_MIN, KICK_FORCE_MAX, KICK_UPWARD_LOW_BALL, KICK_UPWARD_HIGH_BALL,
    GRAY, IMAGES_DIR
)
from assets import Assets


class Player:
    def __init__(self, x: int, y: int, char_data: dict, controls: dict, side: int) -> None:
        self.initial_x: int = x
        self.initial_y: int = y
        self.rect: pygame.Rect = pygame.Rect(x, y, 145, 175)
        self.hitbox_offset_x: int = 18
        self.name: str = char_data["name"]
        self.key: str = char_data["key"]
        self.controls: dict = controls
        self.side: int = side

        self.head_img, self.head_img_r = Assets.heads[self.key]
        self.current_img = self.head_img if side == 0 else self.head_img_r

        self.vel_x: float = 0
        self.vel_y: float = 0
        self.speed: float = 4.5
        self.jump_power: float = -13
        self.is_jumping: bool = False
        self.score: int = 0

        self.kicking: bool = False
        self.kick_force: float = 16

        self.shoe_angle: float = 0
        self.shoe_offset_x: float = 0
        self.shoe_offset_y: float = 0
        self.kick_animation_timer: int = 0
        self.shoe_hitbox: pygame.Rect = pygame.Rect(0, 0, 160, 100)

    def reset_position(self) -> None:
        self.rect.x = self.initial_x
        self.rect.y = self.initial_y
        self.vel_x = 0
        self.vel_y = 0
        self.shoe_angle = 0
        self.shoe_offset_x = 0
        self.shoe_offset_y = 0
        self.kicking = False

    def update(self) -> None:
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

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        shoe_x = self.rect.centerx + self.shoe_offset_x + (90 if self.side == 0 else -90)
        shoe_y = self.rect.centery + self.shoe_offset_y + 55
        self.shoe_hitbox.center = (int(shoe_x), int(shoe_y))

    def draw(self, screen: pygame.Surface) -> None:
        shoe_img = Assets.shoe if self.side == 0 else Assets.shoe_r
        if self.shoe_angle != 0:
            shoe_img = pygame.transform.rotate(shoe_img, self.shoe_angle if self.side == 0 else -self.shoe_angle)

        shoe_x = self.rect.centerx + self.shoe_offset_x + (90 if self.side == 0 else -90)
        shoe_y = self.rect.centery + self.shoe_offset_y + 55
        shoe_rect = shoe_img.get_rect(center=(int(shoe_x), int(shoe_y)))
        screen.blit(shoe_img, shoe_rect)

        if self.side == 1 and self.vel_x <= 0:
            img = self.head_img_r
        elif self.side == 1 and self.vel_x > 0:
            img = self.head_img
        elif self.side == 0 and self.vel_x < 0:
            img = self.head_img_r
        else:
            img = self.head_img

        screen.blit(img, (self.rect.x - self.hitbox_offset_x, self.rect.y))


class Ball:
    def __init__(self) -> None:
        self.radius: int = 48
        self.img = pygame.transform.smoothscale(Assets.ball, (96, 96))
        self.x: float = 0
        self.y: float = 0
        self.vel_x: float = 0
        self.vel_y: float = 0
        self.angle: float = 0
        self.angle_speed: float = 0
        self.reset(conceded_by=0)

    def reset(self, conceded_by: int = 0) -> None:
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

    def update(self) -> None:
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
                if abs(self.vel_y) < 1:
                    self.vel_y = 0

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

    def draw(self, screen: pygame.Surface) -> None:
        shadow = pygame.Surface((70, 25), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, 70, 25))
        ground_y = SCREEN_HEIGHT - 40
        height_diff = ground_y - (self.y + self.radius)
        if height_diff < 0:
            height_diff = 0
        shadow_scale = max(0.2, 1.0 - height_diff / 300)
        shadow_scaled = pygame.transform.scale(shadow, (int(70 * shadow_scale), int(25 * shadow_scale)))
        screen.blit(shadow_scaled, (self.x - shadow_scaled.get_width() // 2, ground_y - shadow_scaled.get_height() // 2))

        rotated_ball = pygame.transform.rotozoom(self.img, -self.angle, 1)
        ball_rect = rotated_ball.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated_ball, ball_rect)


class Goal:
    def __init__(self, x: int, side: int) -> None:
        self.rect = pygame.Rect(x, SCREEN_HEIGHT - 400, 125, 360)
        self.crossbar = pygame.Rect(x, SCREEN_HEIGHT - 400, 125, 30)
        self.side = side
        if os.path.exists(os.path.join(IMAGES_DIR, "goal.png")):
            self.img = pygame.transform.scale(Assets.goal_img, (125, 360))
            self.img_r = pygame.transform.scale(Assets.goal_img_r, (125, 360))
        else:
            self.img = pygame.Surface((125, 360))
            self.img.fill(GRAY)
            self.img_r = self.img

    def draw(self, screen: pygame.Surface) -> None:
        if self.side == 0:
            screen.blit(self.img, self.rect)
        else:
            screen.blit(self.img_r, self.rect)
