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

# Система полос движения
LANE_COUNT = 3
LANE_WIDTH = SCREEN_WIDTH // LANE_COUNT
LANES = [LANE_WIDTH // 2 + i * LANE_WIDTH for i in range(LANE_COUNT)]

# Типы событий
EVENT_NITRO = 0
EVENT_OIL_SPILL = 1
EVENT_SPEED_BUMP = 2

# Типы power-ups
POWERUP_NITRO = 0
POWERUP_SHIELD = 1
POWERUP_REPAIR = 2

FPS = 60


class Entity:
    def __init__(self, width, aspect_ratio, image_path, speed):
        self.width = width
        self.aspect_ratio = aspect_ratio
        self.height = self.width / self.aspect_ratio
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = self.image.get_rect()
        self.MOVEMENT_SPEED = speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Obstacle(Entity):
    def __init__(self, width, aspect_ratio, image_path, speed):
        super().__init__(width, aspect_ratio, image_path, speed)
        self.rect.center = self.randomize_position()

    def randomize_position(self):
        y = int(-self.height)
        lane = random.choice(LANES)
        x = lane - self.rect.width // 2
        x = max(10, min(x, SCREEN_WIDTH - 10 - self.rect.width))
        return x, y

    def move(self):
        self.rect.move_ip(0, self.MOVEMENT_SPEED)
        if self.rect.top > 600:
            self.__init__()


class RoadEvent:
    def __init__(self, event_type, x, y, duration=90):
        self.event_type = event_type
        self.rect = pygame.Rect(x, y, LANE_WIDTH - 20, 30)
        self.duration = duration
        self.lifetime = 0

    def draw(self, screen):
        if self.event_type == EVENT_NITRO:
            pygame.draw.rect(screen, BLUE, self.rect)
            pygame.draw.rect(screen, WHITE, self.rect, 2)
            font = pygame.font.SysFont("Arial", 18)
            text = font.render("NITRO", True, WHITE)
            text_rect = text.get_rect(center=self.rect.center)
            screen.blit(text, text_rect)
        elif self.event_type == EVENT_OIL_SPILL:
            pygame.draw.rect(screen, GRAY, self.rect)
            for _ in range(30):
                offset_x = random.randint(-8, 8)
                offset_y = random.randint(-5, 5)
                pygame.draw.circle(screen, BLACK, (self.rect.centerx + offset_x, self.rect.centery + offset_y), 2)
        elif self.event_type == EVENT_SPEED_BUMP:
            pygame.draw.rect(screen, ORANGE, self.rect)
            for i in range(3):
                y = self.rect.y + 10 + i * 10
                pygame.draw.line(screen, BLACK, (self.rect.x + 5, y), (self.rect.right - 5, y), 3)

    def update(self):
        self.lifetime += 1
        return self.lifetime >= self.duration


class PowerUp:
    def __init__(self, power_type, x, y):
        self.power_type = power_type
        self.rect = pygame.Rect(x, y, 30, 30)
        self.lifetime = 300  # Исчезает через 5 секунд
        self.age = 0
    
    def draw(self, screen):
        colors = [BLUE, GREEN, YELLOW]
        texts = ["N", "S", "R"]
        pygame.draw.rect(screen, colors[self.power_type], self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        font = pygame.font.SysFont("Arial", 20)
        text = font.render(texts[self.power_type], True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)
    
    def update(self):
        self.age += 1
        return self.age >= self.lifetime

class Player(Entity):
    def __init__(self, car_color="purple"):
        super().__init__(60, 0.5, f"images/car_{car_color}.png", SPEED * 2)
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.current_lane = 1
        self.target_x = LANES[self.current_lane]
        self.rect.centerx = LANES[self.current_lane]
        self.nitro_active = False
        self.nitro_timer = 0
        self.speed_multiplier = 1.0
        self.shield_active = False
        self.shield_hits_left = 1
        self.move_speed = 3  # Скорость перемещения между полосами (было 8-10, теперь 3)

    def move(self, slippery=False):
        pressed = pygame.key.get_pressed()
        
        # Проверяем нажатия клавиш для смены полосы
        move_left = pressed[pygame.K_LEFT] and self.current_lane > 0
        move_right = pressed[pygame.K_RIGHT] and self.current_lane < LANE_COUNT - 1
        
        # Меняем целевую позицию при нажатии
        if move_left:
            self.current_lane -= 1
            self.target_x = LANES[self.current_lane]
        if move_right:
            self.current_lane += 1
            self.target_x = LANES[self.current_lane]
        
        # Медленное перемещение к целевой позиции
        dx = self.target_x - self.rect.centerx
        if abs(dx) > self.move_speed:
            # Двигаемся с постоянной скоростью
            if dx > 0:
                self.rect.centerx += self.move_speed
            else:
                self.rect.centerx -= self.move_speed
        else:
            # Добираем остаток
            self.rect.centerx = self.target_x
        
        # Обработка нитро
        if self.nitro_active:
            self.nitro_timer += 1
            if self.nitro_timer > 180:
                self.nitro_active = False
                self.nitro_timer = 0
                self.speed_multiplier = 1.0
        
        # Расчет скорости движения вперед
        movement_speed = self.MOVEMENT_SPEED
        if slippery:
            movement_speed = int(self.MOVEMENT_SPEED * 0.4)
        
        movement_speed = int(movement_speed * self.speed_multiplier)
        
        # Движение вперед (не используется, но оставим для совместимости)
        if self.rect.left > 0 and self.rect.right < SCREEN_WIDTH:
            if pressed[pygame.K_LEFT]:
                self.rect.move_ip(-movement_speed, 0)
            if pressed[pygame.K_RIGHT]:
                self.rect.move_ip(movement_speed, 0)
        
        # Границы
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

    def activate_nitro(self):
        if not self.nitro_active:
            self.nitro_active = True
            self.speed_multiplier = 1.8
            self.nitro_timer = 0
    
    def activate_shield(self):
        self.shield_active = True
        self.shield_hits_left = 1
    
    def repair(self):
        self.speed_multiplier = 1.0
        self.nitro_active = False
    
    def apply_speed_bump(self):
        self.speed_multiplier = 0.6
        self.nitro_timer = 0
    
    def draw_shield(self, screen):
        if self.shield_active:
            pygame.draw.circle(screen, GREEN, self.rect.center, self.rect.width // 2 + 5, 3)
            
class Enemy(Obstacle):
    def __init__(self, speed=SPEED):
        colors_path = "images/cars"
        colors = os.listdir(colors_path)
        car_name = random.choice(colors)
        super().__init__(60, 0.5, colors_path + "/" + car_name, speed)
        self.image = pygame.transform.rotate(self.image, 180)


class Coin(Obstacle):
    def __init__(self, speed=SPEED):
        super().__init__(20, 1, "images/coin.png", speed)
        self.weight = random.choice(COIN_WEIGHTS)


class Game:
    def __init__(self, username, data_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Racer Game")
        self.running = True
        self.font = pygame.font.SysFont("Courier New", 30)
        self.small_font = pygame.font.SysFont("Courier New", 20)
        
        self.username = username
        self.data_manager = data_manager
        
        self.createBg()
        self.createCounters()
        self.createEntities()
        
        self.road_events = []
        self.powerups = []
        self.enemies = []
        self.coins_list = []
        
        self.event_timer = 0
        self.enemy_spawn_timer = 0
        self.powerup_spawn_timer = 0
        self.coin_spawn_timer = 0
        
        self.distance = 0
        self.active_powerup = None
        self.powerup_time_left = 0
        
        # Загружаем настройки сложности
        self.diff_settings = self.data_manager.get_difficulty_settings()
        self.enemy_speed = self.diff_settings['enemy_speed']
        self.spawn_rates = {
            'enemy': self.diff_settings['enemy_spawn_rate'],
            'powerup': self.diff_settings['powerup_spawn_rate'],
            'coin': 60
        }
    
    def createBg(self):
        self.bg = pygame.image.load("images/bg.png")
        bg_aspect_ratio = self.bg.get_width() / self.bg.get_height()
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, math.ceil(SCREEN_WIDTH / bg_aspect_ratio)))
        self.copies = math.ceil(SCREEN_HEIGHT / self.bg.get_height()) + 1
    
    def drawBg(self):
        self.screen.fill(WHITE)
        self.scroll = (self.scroll + self.speed // 1.5) % self.bg.get_height()
        for i in range(self.copies):
            self.screen.blit(self.bg, (0, self.scroll + (i - 1) * (self.bg.get_height() - 1)))
        
        # Рисуем линии полос
        for i in range(1, LANE_COUNT):
            x = i * LANE_WIDTH
            for y in range(0, SCREEN_HEIGHT, 40):
                pygame.draw.line(self.screen, WHITE, (x, y + self.scroll % 40), (x, y + 20 + self.scroll % 40), 3)
    
    def createCounters(self):
        self.scroll = 0
        self.coins = 0
        self.speed = SPEED
        self.score = 0
        self.enemies_speed_increment_count = 0
    
    def createEntities(self):
        car_color = self.data_manager.settings.get('car_color', 'purple')
        self.player = Player(car_color)
    
    def spawn_enemy(self):
        if self.enemy_spawn_timer >= self.spawn_rates['enemy']:
            self.enemies.append(Enemy(self.enemy_speed))
            self.enemy_spawn_timer = 0
        else:
            self.enemy_spawn_timer += 1
    
    def spawn_powerup(self):
        if self.powerup_spawn_timer >= self.spawn_rates['powerup']:
            lane = random.randint(0, LANE_COUNT - 1)
            x = LANES[lane] - 15
            y = -30
            power_type = random.choice([POWERUP_NITRO, POWERUP_SHIELD, POWERUP_REPAIR])
            self.powerups.append(PowerUp(power_type, x, y))
            self.powerup_spawn_timer = 0
        else:
            self.powerup_spawn_timer += 1
    
    def spawn_coin(self):
        if self.coin_spawn_timer >= self.spawn_rates['coin']:
            self.coins_list.append(Coin(self.speed))
            self.coin_spawn_timer = 0
        else:
            self.coin_spawn_timer += 1
    
    def generate_road_event(self):
        self.event_timer += 1
        if self.event_timer > random.randint(180, 300):
            self.event_timer = 0
            event_type = random.choice([EVENT_NITRO, EVENT_OIL_SPILL, EVENT_SPEED_BUMP])
            lane = random.randint(0, LANE_COUNT - 1)
            x = LANES[lane] - (LANE_WIDTH - 20) // 2
            y = -30
            self.road_events.append(RoadEvent(event_type, x, y))
    
    def update_entities(self):
        # Обновляем врагов
        for enemy in self.enemies[:]:
            enemy.move()
            if enemy.rect.top > SCREEN_HEIGHT:
                self.enemies.remove(enemy)
        
        # Обновляем монеты
        for coin in self.coins_list[:]:
            coin.move()
            if coin.rect.top > SCREEN_HEIGHT:
                self.coins_list.remove(coin)
        
        # Обновляем power-ups
        for powerup in self.powerups[:]:
            powerup.rect.move_ip(0, self.speed)
            if powerup.update() or powerup.rect.top > SCREEN_HEIGHT:
                self.powerups.remove(powerup)
    
    def watch_collisions(self):
        slippery = False
        
        # Проверяем столкновения с врагами
        for enemy in self.enemies[:]:
            if self.player.rect.colliderect(enemy.rect):
                if self.player.shield_active:
                    self.player.shield_active = False
                    self.enemies.remove(enemy)
                else:
                    return False
        
        # Проверяем столкновения с монетами
        for coin in self.coins_list[:]:
            if self.player.rect.colliderect(coin.rect):
                self.coins_list.remove(coin)
                self.coins += coin.weight
                self.score += coin.weight * 10
                self.enemies_speed_increment_count += coin.weight
                
                if self.enemies_speed_increment_count >= COINS_FOR_SPEED_INCREASE:
                    self.enemy_speed += ENEMY_SPEED_INCREMENT
                    self.enemies_speed_increment_count = 0
        
        # Проверяем столкновения с событиями на дороге
        for event in self.road_events[:]:
            if self.player.rect.colliderect(event.rect):
                if event.event_type == EVENT_NITRO:
                    self.player.activate_nitro()
                elif event.event_type == EVENT_OIL_SPILL:
                    slippery = True
                elif event.event_type == EVENT_SPEED_BUMP:
                    self.player.apply_speed_bump()
                self.road_events.remove(event)
        
        # Проверяем столкновения с power-ups
        for powerup in self.powerups[:]:
            if self.player.rect.colliderect(powerup.rect):
                if powerup.power_type == POWERUP_NITRO:
                    self.player.activate_nitro()
                    self.active_powerup = "NITRO"
                    self.powerup_time_left = 180
                elif powerup.power_type == POWERUP_SHIELD:
                    self.player.activate_shield()
                    self.active_powerup = "SHIELD"
                    self.powerup_time_left = 1
                elif powerup.power_type == POWERUP_REPAIR:
                    self.player.repair()
                    self.active_powerup = "REPAIR"
                    self.powerup_time_left = 1
                self.powerups.remove(powerup)
        
        # Обновляем события
        for event in self.road_events[:]:
            event.rect.move_ip(0, self.speed)
            if event.update():
                self.road_events.remove(event)
        
        # Обновляем активный power-up
        if self.powerup_time_left > 0:
            self.powerup_time_left -= 1
            if self.powerup_time_left <= 0:
                self.active_powerup = None
        
        # Двигаем игрока
        self.player.move(slippery)
        
        # Обновляем дистанцию и счет
        self.distance += int(self.speed)
        self.score += int(self.speed / 10)
        
        return True
    
    def draw_ui(self):
        # Счетчик монет
        pygame.draw.rect(self.screen, PURPLE, (SCREEN_WIDTH - 70, 0, 70, 60), border_radius=15)
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH - 65, 5, 60, 50), border_radius=10)
        coins_text = self.font.render(str(self.coins), True, BLACK)
        text_rect = coins_text.get_rect(center=(SCREEN_WIDTH - 35, 30))
        self.screen.blit(coins_text, text_rect)
        
        # Счет
        score_text = self.small_font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Дистанция
        dist_text = self.small_font.render(f"DIST: {self.distance}m", True, WHITE)
        self.screen.blit(dist_text, (10, 35))
        
        # Активный power-up
        if self.active_powerup:
            power_text = self.small_font.render(f"{self.active_powerup}", True, YELLOW)
            self.screen.blit(power_text, (SCREEN_WIDTH // 2 - 40, 10))
        
        # Скорость врагов
        speed_text = self.small_font.render(f"ENEMY SPEED: {self.enemy_speed}", True, WHITE)
        self.screen.blit(speed_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))
    
    def draw_entities(self):
        self.player.draw(self.screen)
        self.player.draw_shield(self.screen)
        
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for coin in self.coins_list:
            coin.draw(self.screen)
        for event in self.road_events:
            event.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
    
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
            
            # Спавн объектов
            self.spawn_enemy()
            self.spawn_powerup()
            self.spawn_coin()
            self.generate_road_event()
            self.update_entities()
            
            # Проверяем столкновения
            if not self.watch_collisions():
                # Игра окончена
                total_score = self.score + self.coins * 5 + self.distance // 10
                self.data_manager.add_score(self.username, total_score, self.distance, self.coins)
                return total_score, self.distance, self.coins
            
            # Отрисовка
            self.drawBg()
            self.draw_entities()
            self.draw_ui()
            
            pygame.display.flip()
            clock.tick(FPS)