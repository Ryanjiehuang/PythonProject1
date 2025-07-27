import pygame
import sys
import random
from pygame import K_LEFT
import asyncio

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Snake Platformer")

# Game states
MENU = "menu"
LEVEL_SELECT = "level_select"
GAME = "game"
game_state = MENU

# Level selection
selected_level = 1

# Snake settings
SEGMENT_SIZE = 20
SEGMENT_DISTANCE = SEGMENT_SIZE
GRAVITY = 0.5
JUMP_STRENGTH = -12
MOVE_SPEED = 5
SNAKE_MAX_HEALTH = 100
snake_health = SNAKE_MAX_HEALTH

# Enemy settings
ENEMY_RADIUS = 20
ENEMY_HEALTH = 100
ENEMY_MOVE_SPEED = 2
ENEMY_LEFT_LIMIT = 100
ENEMY_RIGHT_LIMIT = 700
ENEMY_JUMP_STRENGTH = -10
ENEMY_JUMP_INTERVAL = 120

# Poison settings
POISON_COLOR = (255, 0, 255)
POISON_SIZE = 10
POISON_SPEED = 10

# Colors
PLATFORM_COLOR = (100, 100, 100)
HEALTH_BAR_COLOR = (0, 255, 0)
HEALTH_BAR_BG_COLOR = (255, 0, 0)

# Load and scale snake head and body images
snake_head_image = pygame.transform.scale(
    pygame.image.load("assets/head.png").convert_alpha(),
    (SEGMENT_SIZE, SEGMENT_SIZE)
)
snake_body_image = pygame.transform.scale(
    pygame.image.load("assets/body.png").convert_alpha(),
    (SEGMENT_SIZE, SEGMENT_SIZE)
)

class Segment:
    def __init__(self, x, y, is_head=False):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.is_head = is_head
        self.on_ground = False

    def update_physics(self, platforms):
        self.on_ground = False
        self.vel.y += GRAVITY
        move_x = self.vel.x
        move_y = self.vel.y

        self.pos.x += move_x
        rect_x = pygame.Rect(self.pos.x, self.pos.y, SEGMENT_SIZE, SEGMENT_SIZE)
        for p in platforms:
            if rect_x.colliderect(p.rect):
                if move_x > 0:
                    self.pos.x = p.rect.left - SEGMENT_SIZE
                elif move_x < 0:
                    self.pos.x = p.rect.right
                self.vel.x = 0

        self.pos.y += move_y
        rect_y = pygame.Rect(self.pos.x, self.pos.y, SEGMENT_SIZE, SEGMENT_SIZE)
        for p in platforms:
            if rect_y.colliderect(p.rect):
                if move_y > 0:
                    self.pos.y = p.rect.top - SEGMENT_SIZE
                    self.on_ground = True
                    self.vel.y = 0
                elif move_y < 0:
                    self.pos.y = p.rect.bottom
                    self.vel.y = 0

    def follow(self, target):
        direction = self.pos - target.pos
        distance = direction.length()
        if distance > SEGMENT_DISTANCE:
            correction = direction.normalize() * (distance - SEGMENT_DISTANCE)
            self.pos -= correction
            if abs(target.vel.x) > 0:
                self.vel.x = target.vel.x

    def draw(self):
        if self.is_head:
            screen.blit(snake_head_image, (self.pos.x, self.pos.y))
        else:
            screen.blit(snake_body_image, (self.pos.x, self.pos.y))

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
    def draw(self):
        pygame.draw.rect(screen, PLATFORM_COLOR, self.rect)

class Poison:
    def __init__(self, x, y, direction):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(direction * POISON_SPEED, 0)
    def update(self):
        self.pos += self.vel
        pygame.draw.rect(screen, POISON_COLOR, (self.pos.x, self.pos.y, POISON_SIZE, POISON_SIZE))
    def collides_with_enemy(self, enemy_rect):
        poison_rect = pygame.Rect(self.pos.x, self.pos.y, POISON_SIZE, POISON_SIZE)
        return poison_rect.colliderect(enemy_rect)

class MySprite(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        orig_width, orig_height = self.original_image.get_size()
        self.image = pygame.transform.scale(self.original_image, (orig_width, orig_height))
        self.rect = self.image.get_rect(center=(x, y))
    def update(self):
        pass

# Load enemy sprite
my_sprite = MySprite("assets/owl.png", 900, 900)
all_sprites = pygame.sprite.Group(my_sprite)

def draw_main_menu():
    screen.fill((50, 50, 50))
    font = pygame.font.SysFont(None, 60)
    title = font.render("Snake Platformer", True, (255, 255, 255))
    play = font.render("Press ENTER to Play", True, (200, 200, 0))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 200))
    screen.blit(play, (WIDTH // 2 - play.get_width() // 2, 300))

def draw_level_select():
    screen.fill((30, 30, 60))
    font = pygame.font.SysFont(None, 50)
    level1 = font.render("1. Easy Level", True, (255, 255, 255))
    level2 = font.render("2. Hard Level", True, (255, 255, 255))
    screen.blit(level1, (WIDTH // 2 - level1.get_width() // 2, 250))
    screen.blit(level2, (WIDTH // 2 - level2.get_width() // 2, 320))

def draw_health_bar(x, y, health, max_health):
    w, h = 50, 5
    fill = max(0, (health / max_health) * w)
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (x, y, w, h))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (x, y, fill, h))

def draw_snake_health_bar(health, max_health):
    bar_x, bar_y = 20, 20
    bar_width, bar_height = 200, 15
    fill = max(0, (health / max_health) * bar_width)
    pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, fill, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

def start_game():
    global segments, head, platforms, enemy_pos, enemy_health, enemy_vel, \
           enemy_vertical_vel, enemy_jump_timer, poisons, last_direction, snake_health

    segments = [
        Segment(400 - i * SEGMENT_DISTANCE, 300, is_head=(i == 0))
        for i in range(6)
    ]
    head = segments[0]

    if selected_level == 1:
        platforms = [
            Platform(100, HEIGHT - 150, 200, 20),
            Platform(400, HEIGHT - 250, 150, 20),
            Platform(600, HEIGHT - 350, 200, 20),
            Platform(0, HEIGHT - 50, WIDTH, 50)
        ]
    else:
        platforms = [
            Platform(50, HEIGHT - 200, 150, 20),
            Platform(250, HEIGHT - 300, 150, 20),
            Platform(500, HEIGHT - 250, 200, 20),
            Platform(300, HEIGHT - 150, 150, 20),
            Platform(0, HEIGHT - 50, WIDTH, 50)
        ]

    enemy_pos = pygame.Vector2(400, HEIGHT - 300 - ENEMY_RADIUS)
    enemy_health = ENEMY_HEALTH
    enemy_vel = pygame.Vector2(ENEMY_MOVE_SPEED, 0)
    enemy_vertical_vel = 0
    enemy_jump_timer = 0
    poisons = []
    last_direction = 1
    snake_health = SNAKE_MAX_HEALTH

running = True
while running:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if game_state == MENU:
        draw_main_menu()
        if keys[pygame.K_RETURN]:
            game_state = LEVEL_SELECT

    elif game_state == LEVEL_SELECT:
        draw_level_select()
        if keys[pygame.K_1]:
            selected_level = 1
            ENEMY_HEALTH = 100
            ENEMY_MOVE_SPEED = 2
            start_game()
            game_state = GAME
        elif keys[pygame.K_2]:
            selected_level = 2
            ENEMY_HEALTH = 200
            ENEMY_MOVE_SPEED = 4
            start_game()
            game_state = GAME

    elif game_state == GAME:
        # Handle input
        head.vel.x = 0
        if keys[pygame.K_a or pygame.K_LEFT]:
            head.vel.x = -MOVE_SPEED
            last_direction = -1
        if keys[pygame.K_d]:
            head.vel.x = MOVE_SPEED
            last_direction = 1
        if keys[pygame.K_w] and head.on_ground:
            head.vel.y = JUMP_STRENGTH
        if keys[pygame.K_SPACE]:
            poisons.append(Poison(head.pos.x, head.pos.y, last_direction))

        # Physics & updates
        head.update_physics(platforms)
        for i in range(1, len(segments)):
            segments[i].update_physics(platforms)
            segments[i].follow(segments[i - 1])

        for poison in poisons[:]:
            poison.update()
            enemy_rect = pygame.Rect(
                enemy_pos.x - ENEMY_RADIUS, enemy_pos.y - ENEMY_RADIUS,
                ENEMY_RADIUS * 2, ENEMY_RADIUS * 2
            )
            if poison.collides_with_enemy(enemy_rect):
                enemy_health -= 1
                poisons.remove(poison)

        # Enemy movement
        enemy_pos += enemy_vel
        enemy_vertical_vel += GRAVITY
        enemy_pos.y += enemy_vertical_vel
        if enemy_pos.y + ENEMY_RADIUS >= HEIGHT - 50:
            enemy_pos.y = HEIGHT - 50 - ENEMY_RADIUS
            enemy_vertical_vel = 0
        enemy_jump_timer += 1
        if enemy_jump_timer >= ENEMY_JUMP_INTERVAL:
            enemy_vertical_vel = ENEMY_JUMP_STRENGTH
            enemy_jump_timer = 0
        if (enemy_pos.x - ENEMY_RADIUS <= ENEMY_LEFT_LIMIT or
                enemy_pos.x + ENEMY_RADIUS >= ENEMY_RIGHT_LIMIT):
            enemy_vel.x *= -1

        # Draw everything
        for p in platforms:
            p.draw()
        for s in segments:
            s.draw()
        if enemy_health > 0:
            my_sprite.rect.center = (int(enemy_pos.x), int(enemy_pos.y))
            all_sprites.update()
            all_sprites.draw(screen)
            draw_health_bar(enemy_pos.x - 25, enemy_pos.y - 40, enemy_health, ENEMY_HEALTH)

        # Death & win conditions
        head_rect = pygame.Rect(head.pos.x, head.pos.y, SEGMENT_SIZE, SEGMENT_SIZE)
        enemy_rect = pygame.Rect(
            enemy_pos.x - ENEMY_RADIUS, enemy_pos.y - ENEMY_RADIUS,
            ENEMY_RADIUS * 2, ENEMY_RADIUS * 2
        )
        if head_rect.colliderect(enemy_rect):
            snake_health -= 1
            if snake_health <= 0:
                print("Game Over! The snake ran out of health.")
                running = False

        if head.pos.y > HEIGHT:
            print("Game Over! The snake fell.")
            running = False

        if enemy_health <= 0:
            print("You defeated the enemy!")
            running = False

        draw_snake_health_bar(snake_health, SNAKE_MAX_HEALTH)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
