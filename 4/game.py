import pygame
import random
import json
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional

SCREEN = (800, 600)
GRID_SIZE = 20
INITIAL_SPEED = 8
COLORS = {
    'bg': (0, 0, 0),
    'grid': (40, 40, 40),
    'food': (255, 210, 0),
    'poison': (139, 0, 0),
    'obstacle': (100, 100, 100),
    'powerup': {'speed': (0, 255, 255), 'slow': (255, 0, 255), 'shield': (255, 255, 0)},
    'button': {'normal': (0, 100, 0), 'hover': (0, 150, 0), 'quit': (100, 0, 0)}
}

@dataclass
class Position:
    x: int
    y: int
    
    def tuple(self):
        return (self.x, self.y)
    
    @staticmethod
    def random():
        return Position(
            random.randrange(0, SCREEN[0], GRID_SIZE),
            random.randrange(0, SCREEN[1], GRID_SIZE)
        )

@dataclass
class Food:
    pos: Position
    weight: int = 1
    is_poison: bool = False
    spawn_time: int = None
    
    def __post_init__(self):
        self.spawn_time = pygame.time.get_ticks()
    
    def expired(self, current_time):
        return current_time - self.spawn_time > 10000

@dataclass  
class PowerUp:
    pos: Position
    type: str
    spawn_time: int = None
    
    def __post_init__(self):
        self.spawn_time = pygame.time.get_ticks()
    
    def expired(self, current_time):
        return current_time - self.spawn_time > 8000

class Button:
    def __init__(self, x, y, w, h, text, color_key='normal'):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color_key = color_key
    
    def draw(self, screen, font):
        color = COLORS['button']['hover'] if self.rect.collidepoint(pygame.mouse.get_pos()) else COLORS['button'][self.color_key]
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (255,255,255), self.rect, 2)
        text_surf = font.render(self.text, True, (255,255,255))
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))
    
    def clicked(self, pos):
        return self.rect.collidepoint(pos)

class Snake:
    def __init__(self):
        self.body = [Position(SCREEN[0]//2, SCREEN[1]//2)]
        self.dir = (GRID_SIZE, 0)
        self.grow_flag = False
        self.speed_mult = 1.0
        self.shield = False
        self.powerup_end = 0
    
    def move(self):
        head = self.body[0]
        new_head = Position(head.x + self.dir[0], head.y + self.dir[1])
        
        # Collisions
        if (new_head.x < 0 or new_head.x >= SCREEN[0] or 
            new_head.y < 0 or new_head.y >= SCREEN[1] or
            new_head.tuple() in [p.tuple() for p in self.body[1:]]):
            return not self.shield, None
        
        self.body.insert(0, new_head)
        if not self.grow_flag:
            self.body.pop()
        self.grow_flag = False
        return False, new_head
    
    def grow(self):
        self.grow_flag = True
    
    def shorten(self):
        for _ in range(2):
            if len(self.body) > 1:
                self.body.pop()
        return len(self.body) <= 1
    
    def change_dir(self, new_dir):
        if (new_dir[0] != -self.dir[0] or new_dir[1] != -self.dir[1]):
            self.dir = new_dir
    
    def apply_powerup(self, type, time):
        effects = {'speed': 1.5, 'slow': 0.6}
        if type in effects:
            self.speed_mult = effects[type]
        elif type == 'shield':
            self.shield = True
        self.powerup_end = time + 5000
    
    def update(self, time):
        if time >= self.powerup_end:
            self.speed_mult = 1.0
            self.shield = False

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN)
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = {size: pygame.font.Font(None, size) for size in [24, 36, 48]}
        
        # Load settings - FIXED
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except:
            self.settings = {"snake_color": [0,255,0], "grid": True, "sound": True}
        
        # Ensure settings has correct structure
        if isinstance(self.settings, list):
            self.settings = {"snake_color": [0,255,0], "grid": True, "sound": True}
        
        # Game state
        self.username = ""
        self.input_text = ""
        self.game_state = "username"
        self.init_game()
        self.create_buttons()
        self.load_db()
    
    def init_game(self):
        self.snake = Snake()
        self.score = 0
        self.level = 1
        self.foods = [Food(Position.random())]
        self.powerup = None
        self.obstacles = []
        self.food_count = 0
        self.base_speed = INITIAL_SPEED
    
    def load_db(self):
        try:
            with open('scores.json', 'r') as f:
                self.scores = json.load(f)
        except:
            self.scores = {"players": {}, "sessions": []}
    
    def save_score(self):
        if not self.username:
            return
        
        # Update player
        if self.username not in self.scores["players"]:
            self.scores["players"][self.username] = len(self.scores["players"]) + 1
        
        # Save session
        self.scores["sessions"].append({
            "username": self.username,
            "score": self.score,
            "level": self.level,
            "date": datetime.now().isoformat()
        })
        
        with open('scores.json', 'w') as f:
            json.dump(self.scores, f, indent=2)
    
    def get_leaderboard(self):
        sessions = sorted(self.scores["sessions"], key=lambda x: x["score"], reverse=True)
        return [(s["username"], s["score"], s["level"], s["date"]) for s in sessions[:10]]
    
    def get_personal_best(self):
        best = 0
        for s in self.scores["sessions"]:
            if s["username"] == self.username and s["score"] > best:
                best = s["score"]
        return best
    
    def create_buttons(self):
        w, h = 200, 50
        cx = SCREEN[0]//2 - w//2
        self.btns = {
            'main': [
                Button(cx, 200, w, h, "Play"),
                Button(cx, 270, w, h, "Leaderboard"),
                Button(cx, 340, w, h, "Settings"),
                Button(cx, 410, w, h, "Quit", 'quit')
            ],
            'gameover': [
                Button(cx-110, 400, 180, 50, "Retry"),
                Button(cx+110, 400, 180, 50, "Menu")
            ],
            'back': Button(SCREEN[0]-150, SCREEN[1]-80, 120, 40, "Back"),
            'settings': [
                Button(cx, 200, w, h, "Toggle Grid"),
                Button(cx, 270, w, h, "Toggle Sound"),
                Button(cx, 340, w, h, "Change Color"),
                Button(cx, 410, w, h, "Save & Back")
            ]
        }
    
    def get_empty_pos(self):
        while True:
            pos = Position.random()
            if (pos.tuple() not in [p.tuple() for p in self.snake.body] and
                pos.tuple() not in self.obstacles and
                not any(f.pos.tuple() == pos.tuple() for f in self.foods)):
                return pos
    
    def generate_obstacles(self):
        if self.level < 3:
            return
        self.obstacles = []
        for _ in range(min(5 + self.level, 20)):
            pos = self.get_empty_pos()
            if abs(pos.x - self.snake.body[0].x) < GRID_SIZE*3 and abs(pos.y - self.snake.body[0].y) < GRID_SIZE*3:
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
            self.game_over()
            return
        
        # Check food collision
        if new_head:
            for food in self.foods[:]:
                if new_head.x == food.pos.x and new_head.y == food.pos.y:
                    if food.is_poison:
                        if self.snake.shorten():
                            self.game_over()
                            return
                    else:
                        self.score += food.weight
                        self.food_count += 1
                        self.snake.grow()
                        
                        if self.food_count >= self.level * 3:
                            self.level += 1
                            self.generate_obstacles()
                        
                        # Spawn new food
                        self.foods.append(Food(self.get_empty_pos(), random.choice([1,2,3,5])))
                        if random.random() < 0.1:
                            self.foods.append(Food(self.get_empty_pos(), 0, True))
                    
                    self.foods.remove(food)
                    break
        
        # Powerup collision
        if self.powerup and new_head and new_head.x == self.powerup.pos.x and new_head.y == self.powerup.pos.y:
            self.snake.apply_powerup(self.powerup.type, now)
            self.powerup = None
        
        # Random spawns
        if random.random() < 0.02:
            self.foods.append(Food(self.get_empty_pos(), random.choice([1,2,3,5])))
        if not self.powerup and random.random() < 0.03:
            self.powerup = PowerUp(self.get_empty_pos(), random.choice(['speed', 'slow', 'shield']))
    
    def game_over(self):
        self.save_score()
        self.personal_best = self.get_personal_best()
        self.game_state = "gameover"
    
    def draw_grid(self):
        if self.settings.get('grid', True):  # FIXED: use .get() with default
            for x in range(0, SCREEN[0], GRID_SIZE):
                pygame.draw.line(self.screen, COLORS['grid'], (x,0), (x,SCREEN[1]))
            for y in range(0, SCREEN[1], GRID_SIZE):
                pygame.draw.line(self.screen, COLORS['grid'], (0,y), (SCREEN[0],y))
    
    def draw(self):
        self.screen.fill(COLORS['bg'])
        
        if self.game_state == "playing":
            self.draw_grid()
            
            # Obstacles
            for obs in self.obstacles:
                pygame.draw.rect(self.screen, COLORS['obstacle'], (*obs, GRID_SIZE, GRID_SIZE))
            
            # Foods
            for food in self.foods:
                color = COLORS['poison'] if food.is_poison else COLORS['food']
                pygame.draw.rect(self.screen, color, (food.pos.x, food.pos.y, GRID_SIZE, GRID_SIZE))
                if not food.is_poison:
                    txt = self.font[24].render(str(food.weight), True, (0,0,0))
                    self.screen.blit(txt, (food.pos.x+5, food.pos.y+5))
            
            # Powerup
            if self.powerup:
                color = COLORS['powerup'][self.powerup.type]
                pygame.draw.rect(self.screen, color, (self.powerup.pos.x, self.powerup.pos.y, GRID_SIZE, GRID_SIZE))
            
            # Snake
            color = tuple(self.settings.get('snake_color', [0,255,0]))  # FIXED: use .get()
            for i, seg in enumerate(self.snake.body):
                if i == 0 and self.snake.shield:
                    pygame.draw.rect(self.screen, (255,215,0), (seg.x, seg.y, GRID_SIZE, GRID_SIZE))
                else:
                    pygame.draw.rect(self.screen, color, (seg.x, seg.y, GRID_SIZE, GRID_SIZE))
            
            # HUD
            hud = [
                f"Score: {self.score}",
                f"Level: {self.level}",
                f"Best: {self.personal_best}" if hasattr(self, 'personal_best') else ""
            ]
            for i, text in enumerate(hud):
                if text:
                    self.screen.blit(self.font[36].render(text, True, (255,255,255)), (10, 10 + i*40))
        
        elif self.game_state == "menu":
            title = self.font[48].render("SNAKE GAME", True, (0,255,0))
            self.screen.blit(title, title.get_rect(center=(SCREEN[0]//2, 100)))
            for btn in self.btns['main']:
                btn.draw(self.screen, self.font[36])
        
        elif self.game_state == "gameover":
            texts = [
                ("GAME OVER", self.font[48], (255,0,0)),
                (f"Score: {self.score}", self.font[36], (255,255,255)),
                (f"Level: {self.level}", self.font[36], (255,255,255)),
                (f"Best: {self.personal_best}", self.font[36], (255,255,0)) if hasattr(self, 'personal_best') else None
            ]
            y = 150
            for text, font, color in texts:
                if text:
                    surf = font.render(text, True, color)
                    self.screen.blit(surf, surf.get_rect(center=(SCREEN[0]//2, y)))
                    y += 60
            
            for btn in self.btns['gameover']:
                btn.draw(self.screen, self.font[36])
        
        elif self.game_state == "leaderboard":
            title = self.font[48].render("LEADERBOARD", True, (0,255,0))
            self.screen.blit(title, title.get_rect(center=(SCREEN[0]//2, 50)))
            
            headers = ["Rank", "Name", "Score", "Lvl"]
            x_pos = [50, 150, 400, 550]
            for i, h in enumerate(headers):
                self.screen.blit(self.font[36].render(h, True, (255,255,0)), (x_pos[i], 120))
            
            y = 170
            for rank, (name, score, lvl, _) in enumerate(self.get_leaderboard(), 1):
                texts = [str(rank), name[:15], str(score), str(lvl)]
                for i, t in enumerate(texts):
                    self.screen.blit(self.font[24].render(t, True, (255,255,255)), (x_pos[i], y))
                y += 30
                if y > SCREEN[1] - 100:
                    break
            
            self.btns['back'].draw(self.screen, self.font[36])
        
        elif self.game_state == "settings":
            title = self.font[48].render("SETTINGS", True, (0,255,0))
            self.screen.blit(title, title.get_rect(center=(SCREEN[0]//2, 50)))
            
            status = [
                f"Grid: {'ON' if self.settings.get('grid', True) else 'OFF'}",
                f"Sound: {'ON' if self.settings.get('sound', True) else 'OFF'}",
                f"Color: {tuple(self.settings.get('snake_color', [0,255,0]))}"
            ]
            y = 160
            for text in status:
                self.screen.blit(self.font[36].render(text, True, (255,255,255)), (SCREEN[0]//2 - 100, y))
                y += 35
            
            for btn in self.btns['settings']:
                btn.draw(self.screen, self.font[36])
        
        elif self.game_state == "username":
            title = self.font[48].render("ENTER USERNAME", True, (0,255,0))
            self.screen.blit(title, title.get_rect(center=(SCREEN[0]//2, 150)))
            
            input_box = pygame.Rect(SCREEN[0]//2 - 150, 250, 300, 50)
            pygame.draw.rect(self.screen, (255,255,255), input_box, 2)
            input_surface = self.font[36].render(self.input_text, True, (255,255,255))
            self.screen.blit(input_surface, (input_box.x+10, input_box.y+10))
            
            inst = self.font[24].render("Press ENTER to start", True, (200,200,200))
            self.screen.blit(inst, inst.get_rect(center=(SCREEN[0]//2, 350)))
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if self.game_state == "username":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.input_text.strip():
                        self.username = self.input_text
                        self.personal_best = self.get_personal_best()
                        self.game_state = "menu"
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif len(self.input_text) < 20 and hasattr(event, 'unicode') and event.unicode.isalnum():
                        self.input_text += event.unicode
            
            elif self.game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    keys = {pygame.K_UP: (0,-GRID_SIZE), pygame.K_DOWN: (0,GRID_SIZE),
                           pygame.K_LEFT: (-GRID_SIZE,0), pygame.K_RIGHT: (GRID_SIZE,0)}
                    if event.key in keys:
                        self.snake.change_dir(keys[event.key])
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = "menu"
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                
                if self.game_state == "menu":
                    if self.btns['main'][0].clicked(pos):
                        self.init_game()
                        self.game_state = "playing"
                    elif self.btns['main'][1].clicked(pos):
                        self.game_state = "leaderboard"
                    elif self.btns['main'][2].clicked(pos):
                        self.game_state = "settings"
                    elif self.btns['main'][3].clicked(pos):
                        return False
                
                elif self.game_state == "gameover":
                    if self.btns['gameover'][0].clicked(pos):
                        self.init_game()
                        self.game_state = "playing"
                    elif self.btns['gameover'][1].clicked(pos):
                        self.game_state = "menu"
                
                elif self.game_state == "leaderboard" and self.btns['back'].clicked(pos):
                    self.game_state = "menu"
                
                elif self.game_state == "settings":
                    btn_grid, btn_sound, btn_color, btn_save = self.btns['settings']
                    if btn_grid.clicked(pos):
                        self.settings['grid'] = not self.settings.get('grid', True)
                    elif btn_sound.clicked(pos):
                        self.settings['sound'] = not self.settings.get('sound', True)
                    elif btn_color.clicked(pos):
                        colors = [[0,255,0], [255,0,0], [0,0,255], [255,255,0]]
                        current = self.settings.get('snake_color', [0,255,0])
                        idx = colors.index(current) if current in colors else 0
                        self.settings['snake_color'] = colors[(idx+1) % len(colors)]
                    elif btn_save.clicked(pos):
                        with open('settings.json', 'w') as f:
                            json.dump(self.settings, f, indent=2)
                        self.game_state = "menu"
        
        return True
    
    def run(self):
        running = True
        last_move = pygame.time.get_ticks()
        
        while running:
            now = pygame.time.get_ticks()
            running = self.handle_events()
            
            if self.game_state == "playing":
                speed = self.base_speed * self.snake.speed_mult
                if now - last_move > 1000 // speed:
                    self.update()
                    last_move = now
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    Game().run()