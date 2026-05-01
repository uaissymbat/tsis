import pygame
import random
import os
import math
from persistence import DataManager

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
PURPLE = (191, 105, 245)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
BLUE = (0, 150, 255)
GREEN = (0, 255, 0)

SPEED = 5
COIN_WEIGHTS = [1, 2, 3]
ENEMY_SPEED_INCREMENT = 20
COINS_FOR_SPEED_INCREASE = 5

LANE_COUNT = 3
LANE_WIDTH = SCREEN_WIDTH // LANE_COUNT
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(LANE_COUNT)]

EVENT_NITRO = 0
EVENT_OIL_SPILL = 1
EVENT_SPEED_BUMP = 2

POWERUP_NITRO = 0
POWERUP_SHIELD = 1
POWERUP_REPAIR = 2

FPS = 60


class Entity:
    def __init__(self, width, aspect_ratio, image_path, speed):
        self.width = width
        self.height = width / aspect_ratio
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (width, self.height))
        self.rect = self.image.get_rect()
        self.MOVEMENT_SPEED = speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Obstacle(Entity):
    def __init__(self, width, aspect_ratio, image_path, speed):
        super().__init__(width, aspect_ratio, image_path, speed)
        self.reset()

    def reset(self):
        lane = random.choice(LANES)
        self.rect.centerx = max(10, min(lane, SCREEN_WIDTH - 10))
        self.rect.y = -self.height

    def move(self):
        self.rect.y += self.MOVEMENT_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.reset()


class RoadEvent:
    def __init__(self, event_type, x, y):
        self.event_type = event_type
        self.rect = pygame.Rect(x, y, LANE_WIDTH - 20, 30)
        self.lifetime = 0

    def draw(self, screen):
        colors = [BLUE, GRAY, ORANGE]
        pygame.draw.rect(screen, colors[self.event_type], self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

    def update(self):
        self.lifetime += 1
        return self.lifetime > 90


class PowerUp:
    def __init__(self, power_type, x, y):
        self.power_type = power_type
        self.rect = pygame.Rect(x, y, 30, 30)
        self.age = 0
    
    def draw(self, screen):
        colors = [BLUE, GREEN, YELLOW]
        pygame.draw.rect(screen, colors[self.power_type], self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
    
    def update(self):
        self.age += 1
        return self.age > 300


class Player(Entity):
    def __init__(self, car_color="purple"):
        super().__init__(60, 0.5, f"images/car_{car_color}.png", SPEED * 2)
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.current_lane = 1
        self.target_x = LANES[1]
        self.rect.centerx = LANES[1]
        self.nitro_timer = 0
        self.speed_multiplier = 1.0
        self.shield_active = False
        self.move_speed = 3

    def move(self, slippery=False):
        pressed = pygame.key.get_pressed()
        
        if pressed[pygame.K_LEFT] and self.current_lane > 0:
            self.current_lane -= 1
            self.target_x = LANES[self.current_lane]
        if pressed[pygame.K_RIGHT] and self.current_lane < LANE_COUNT - 1:
            self.current_lane += 1
            self.target_x = LANES[self.current_lane]
        
        dx = self.target_x - self.rect.centerx
        if abs(dx) > self.move_speed:
            self.rect.centerx += self.move_speed if dx > 0 else -self.move_speed
        else:
            self.rect.centerx = self.target_x
        
        if self.nitro_timer > 0:
            self.nitro_timer -= 1
            if self.nitro_timer == 0:
                self.speed_multiplier = 1.0
        
        movement = self.MOVEMENT_SPEED * self.speed_multiplier
        if slippery:
            movement *= 0.4
        
        self.rect.left = max(0, min(self.rect.left, SCREEN_WIDTH - self.rect.width))

    def activate_nitro(self):
        if self.nitro_timer == 0:
            self.nitro_timer = 180
            self.speed_multiplier = 1.8
    
    def activate_shield(self):
        self.shield_active = True
    
    def draw_shield(self, screen):
        if self.shield_active:
            pygame.draw.circle(screen, GREEN, self.rect.center, self.rect.width // 2 + 5, 3)


class Enemy(Obstacle):
    def __init__(self, speed=SPEED):
        colors_path = "images/cars"
        colors = os.listdir(colors_path)
        super().__init__(60, 0.5, f"{colors_path}/{random.choice(colors)}", speed)
        self.image = pygame.transform.rotate(self.image, 180)


class Coin(Obstacle):
    def __init__(self, speed=SPEED):
        super().__init__(20, 1, "images/coin.png", speed)
        self.weight = random.choice(COIN_WEIGHTS)


class Game:
    def __init__(self, username, data_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.username = username
        self.data_manager = data_manager
        
        self.font = pygame.font.SysFont("Courier New", 30)
        self.small_font = pygame.font.SysFont("Courier New", 20)
        
        self.createBg()
        self.reset_game()
        
        self.road_events = []
        self.powerups = []
        self.enemies = []
        self.coins_list = []
        
        self.spawn_timers = {'enemy': 0, 'powerup': 0, 'coin': 0, 'event': 0}
        self.distance = 0
        self.active_powerup = None
        
        diff = self.data_manager.get_difficulty_settings()
        self.enemy_speed = diff['enemy_speed']
        self.spawn_rates = {
            'enemy': diff['enemy_spawn_rate'],
            'powerup': diff['powerup_spawn_rate'],
            'coin': 60
        }
    
    def createBg(self):
        self.bg = pygame.image.load("images/bg.png")
        ratio = self.bg.get_width() / self.bg.get_height()
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, int(SCREEN_WIDTH / ratio)))
        self.copies = SCREEN_HEIGHT // self.bg.get_height() + 2
    
    def drawBg(self):
        self.scroll = (self.scroll + self.speed // 1.5) % self.bg.get_height()
        for i in range(self.copies):
            self.screen.blit(self.bg, (0, self.scroll + (i - 1) * self.bg.get_height()))
        
        for i in range(1, LANE_COUNT):
            x = i * LANE_WIDTH
            for y in range(0, SCREEN_HEIGHT, 40):
                pygame.draw.line(self.screen, WHITE, (x, y + self.scroll % 40), (x, y + 20 + self.scroll % 40), 3)
    
    def reset_game(self):
        self.scroll = 0
        self.coins = 0
        self.speed = SPEED
        self.score = 0
        self.enemy_speed_counter = 0
        car_color = self.data_manager.settings.get('car_color', 'purple')
        self.player = Player(car_color)
    
    def spawn_object(self, timer_name, obj_list, obj_creator):
        if self.spawn_timers[timer_name] >= self.spawn_rates[timer_name]:
            obj_list.append(obj_creator())
            self.spawn_timers[timer_name] = 0
        else:
            self.spawn_timers[timer_name] += 1
    
    def update_objects(self):
        for enemy in self.enemies[:]:
            enemy.move()
            if enemy.rect.top > SCREEN_HEIGHT:
                self.enemies.remove(enemy)
        
        for coin in self.coins_list[:]:
            coin.move()
            if coin.rect.top > SCREEN_HEIGHT:
                self.coins_list.remove(coin)
        
        for powerup in self.powerups[:]:
            powerup.rect.y += self.speed
            if powerup.update() or powerup.rect.top > SCREEN_HEIGHT:
                self.powerups.remove(powerup)
    
    def watch_collisions(self):
        slippery = False
        
        for enemy in self.enemies[:]:
            if self.player.rect.colliderect(enemy.rect):
                if self.player.shield_active:
                    self.player.shield_active = False
                    self.enemies.remove(enemy)
                else:
                    return False
        
        for coin in self.coins_list[:]:
            if self.player.rect.colliderect(coin.rect):
                self.coins_list.remove(coin)
                self.coins += coin.weight
                self.score += coin.weight * 10
                self.enemy_speed_counter += coin.weight
                if self.enemy_speed_counter >= COINS_FOR_SPEED_INCREASE:
                    self.enemy_speed += ENEMY_SPEED_INCREMENT
                    self.enemy_speed_counter = 0
        
        for event in self.road_events[:]:
            if self.player.rect.colliderect(event.rect):
                if event.event_type == EVENT_NITRO:
                    self.player.activate_nitro()
                elif event.event_type == EVENT_OIL_SPILL:
                    slippery = True
                self.road_events.remove(event)
            else:
                event.rect.y += self.speed
                if event.update():
                    self.road_events.remove(event)
        
        for powerup in self.powerups[:]:
            if self.player.rect.colliderect(powerup.rect):
                if powerup.power_type == POWERUP_NITRO:
                    self.player.activate_nitro()
                elif powerup.power_type == POWERUP_SHIELD:
                    self.player.activate_shield()
                self.powerups.remove(powerup)
        
        self.player.move(slippery)
        self.distance += self.speed
        self.score += self.speed // 10
        return True
    
    def draw_ui(self):
        pygame.draw.rect(self.screen, PURPLE, (SCREEN_WIDTH - 70, 0, 70, 60), border_radius=15)
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH - 65, 5, 60, 50), border_radius=10)
        coins_text = self.font.render(str(self.coins), True, BLACK)
        self.screen.blit(coins_text, coins_text.get_rect(center=(SCREEN_WIDTH - 35, 30)))
        
        self.screen.blit(self.small_font.render(f"SCORE: {self.score}", True, WHITE), (10, 10))
        self.screen.blit(self.small_font.render(f"DIST: {self.distance}m", True, WHITE), (10, 35))
        self.screen.blit(self.small_font.render(f"ENEMY SPEED: {self.enemy_speed}", True, WHITE), (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))
    
    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
            
            self.spawn_object('enemy', self.enemies, lambda: Enemy(self.enemy_speed))
            self.spawn_object('powerup', self.powerups, lambda: PowerUp(random.choice([0,1,2]), random.choice(LANES) - 15, -30))
            self.spawn_object('coin', self.coins_list, lambda: Coin(self.speed))
            
            if self.spawn_timers['event'] > random.randint(180, 300):
                self.spawn_timers['event'] = 0
                lane = random.randint(0, LANE_COUNT - 1)
                self.road_events.append(RoadEvent(random.choice([0,1,2]), LANES[lane] - (LANE_WIDTH - 20)//2, -30))
            else:
                self.spawn_timers['event'] += 1
            
            self.update_objects()
            
            if not self.watch_collisions():
                total_score = self.score + self.coins * 5 + self.distance // 10
                self.data_manager.add_score(self.username, total_score, self.distance, self.coins)
                return total_score, self.distance, self.coins
            
            self.drawBg()
            self.player.draw(self.screen)
            self.player.draw_shield(self.screen)
            for obj in self.enemies + self.coins_list + self.road_events + self.powerups:
                obj.draw(self.screen)
            self.draw_ui()
            
            pygame.display.flip()
            clock.tick(FPS)
