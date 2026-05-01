import pygame
import random

W, H = 800, 600
GRID = 20
BASE_SPEED = 8

COLORS = {
    'bg': (0,0,0), 'grid': (40,40,40), 'food': (255,255,0), 
    'poison': (139,0,0), 'obstacle': (100,100,100), 
    'text': (255,255,255),
    'powerup': {'speed': (0,255,255), 'slow': (255,0,255), 'shield': (255,255,0)}
}

class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def tuple(self):
        return (self.x, self.y)
    
    def random():
        return Pos(random.randrange(0, W, GRID), random.randrange(0, H, GRID))

class Food:
    def __init__(self, pos, weight=1, is_poison=False, spawn=None):
        self.pos = pos
        self.weight = weight
        self.is_poison = is_poison
        self.spawn = spawn if spawn is not None else pygame.time.get_ticks()
    
    def expired(self, t):
        return t - self.spawn > 10000

class PowerUp:
    def __init__(self, pos, type, spawn=None):
        self.pos = pos
        self.type = type
        self.spawn = spawn if spawn is not None else pygame.time.get_ticks()
    
    def expired(self, t):
        return t - self.spawn > 8000

class Snake:
    def __init__(self):
        self.body = [Pos(W//2, H//2)]
        self.dir = (GRID, 0)
        self.grow_flag = False
        self.speed_mult = 1.0
        self.shield = False
        self.powerup_end = 0
    
    def move(self):
        head = self.body[0]
        new = Pos(head.x + self.dir[0], head.y + self.dir[1])
        
        if (new.x < 0 or new.x >= W or new.y < 0 or new.y >= H or
            new.tuple() in [p.tuple() for p in self.body[1:]]):
            return not self.shield, None
        
        self.body.insert(0, new)
        if not self.grow_flag:
            self.body.pop()
        self.grow_flag = False
        return False, new
    
    def grow(self):
        self.grow_flag = True
    
    def shorten(self):
        for _ in range(2):
            if len(self.body) > 1:
                self.body.pop()
        return len(self.body) <= 1
    
    def change_dir(self, d):
        if d[0] != -self.dir[0] or d[1] != -self.dir[1]:
            self.dir = d
    
    def apply(self, type, t):
        if type == 'speed':
            self.speed_mult = 1.5
        elif type == 'slow':
            self.speed_mult = 0.6
        elif type == 'shield':
            self.shield = True
        self.powerup_end = t + 5000
    
    def update(self, t):
        if t >= self.powerup_end:
            self.speed_mult = 1.0
            self.shield = False

class Game:
    def __init__(self, settings):
        self.settings = settings
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = {s: pygame.font.Font(None, s) for s in [20,24,36]}
        self.init_game()
    
    def init_game(self):
        self.snake = Snake()
        self.score = 0
        self.level = 1
        self.food_count = 0
        self.foods = [Food(Pos.random())]
        self.powerup = None
        self.obstacles = []
    
    def get_empty(self):
        while True:
            pos = Pos.random()
            if (pos.tuple() not in [p.tuple() for p in self.snake.body] and
                pos.tuple() not in self.obstacles and
                not any(f.pos.tuple() == pos.tuple() for f in self.foods)):
                return pos
    
    def gen_obstacles(self):
        if self.level < 3:
            return
        self.obstacles = []
        for _ in range(min(5 + self.level, 20)):
            pos = self.get_empty()
            if abs(pos.x - self.snake.body[0].x) < GRID * 3 and abs(pos.y - self.snake.body[0].y) < GRID * 3:
                continue
            self.obstacles.append(pos.tuple())
    
    def update(self):
        now = pygame.time.get_ticks()
        self.foods = [f for f in self.foods if not f.expired(now)]
        if self.powerup and self.powerup.expired(now):
            self.powerup = None
        
        self.snake.update(now)
        game_over, new_head = self.snake.move()
        if game_over or (new_head and new_head.tuple() in self.obstacles):
            return True
        
        if new_head:
            for food in self.foods[:]:
                if new_head.x == food.pos.x and new_head.y == food.pos.y:
                    if food.is_poison:
                        if self.snake.shorten():
                            return True
                    else:
                        self.score += food.weight
                        self.food_count += 1
                        self.snake.grow()
                        if self.food_count >= self.level * 3:
                            self.level += 1
                            self.gen_obstacles()
                        self.foods.append(Food(self.get_empty(), random.choice([1,2,3,5])))
                        if random.random() < 0.1:
                            self.foods.append(Food(self.get_empty(), 0, True))
                    self.foods.remove(food)
                    break
            
            if self.powerup and new_head.x == self.powerup.pos.x and new_head.y == self.powerup.pos.y:
                self.snake.apply(self.powerup.type, now)
                self.powerup = None
        
        if random.random() < 0.02:
            self.foods.append(Food(self.get_empty(), random.choice([1,2,3,5])))
        if not self.powerup and random.random() < 0.03:
            self.powerup = PowerUp(self.get_empty(), random.choice(['speed', 'slow', 'shield']))
        
        return False
    
    def draw_grid(self):
        if self.settings.get('grid', True):
            for x in range(0, W, GRID):
                pygame.draw.line(self.screen, COLORS['grid'], (x, 0), (x, H))
            for y in range(0, H, GRID):
                pygame.draw.line(self.screen, COLORS['grid'], (0, y), (W, y))
    
    def draw(self):
        self.screen.fill(COLORS['bg'])
        self.draw_grid()
        
        for obs in self.obstacles:
            pygame.draw.rect(self.screen, COLORS['obstacle'], (*obs, GRID, GRID), border_radius=3)
        
        for food in self.foods:
            c = COLORS['poison'] if food.is_poison else COLORS['food']
            pygame.draw.rect(self.screen, c, (food.pos.x, food.pos.y, GRID, GRID), border_radius=5)
            if not food.is_poison:
                txt = self.font[20].render(str(food.weight), True, (0,0,0))
                self.screen.blit(txt, (food.pos.x + 6, food.pos.y + 4))
        
        if self.powerup:
            c = COLORS['powerup'][self.powerup.type]
            pygame.draw.rect(self.screen, c, (self.powerup.pos.x, self.powerup.pos.y, GRID, GRID), border_radius=5)
            sym = {'speed': '⚡', 'slow': '🐢', 'shield': '🛡'}[self.powerup.type]
            txt = self.font[20].render(sym, True, (0,0,0))
            self.screen.blit(txt, (self.powerup.pos.x + 4, self.powerup.pos.y + 2))
        
        color = tuple(self.settings.get('snake_color', [0,255,0]))
        for i, seg in enumerate(self.snake.body):
            if i == 0 and self.snake.shield:
                pygame.draw.rect(self.screen, (255,215,0), (seg.x, seg.y, GRID, GRID), border_radius=5)
            else:
                pygame.draw.rect(self.screen, color, (seg.x, seg.y, GRID, GRID), border_radius=3)
        
        y = 10
        for text in [f"Score: {self.score}", f"Level: {self.level}"]:
            self.screen.blit(self.font[36].render(text, True, COLORS['text']), (10, y))
            y += 40
        
        pygame.display.flip()
    
    def run(self):
        running = True
        last_move = pygame.time.get_ticks()
        game_over = False
        
        while running and not game_over:
            now = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    keys = {pygame.K_UP: (0, -GRID), pygame.K_DOWN: (0, GRID),
                           pygame.K_LEFT: (-GRID, 0), pygame.K_RIGHT: (GRID, 0)}
                    if event.key in keys:
                        self.snake.change_dir(keys[event.key])
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            speed = BASE_SPEED * self.snake.speed_mult
            if now - last_move > 1000 // speed:
                game_over = self.update()
                last_move = now
            
            self.draw()
            self.clock.tick(60)
        
        return self.score, self.level, game_over