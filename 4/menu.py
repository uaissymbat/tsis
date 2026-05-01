import pygame
import json
from datetime import datetime
from game import Game

W, H = 800, 600
GRID = 20
COLORS = {
    'bg': (0,0,0), 'text': (255,255,255), 'green': (0,255,0), 'red': (255,0,0),
    'button': {'normal': (0,100,0), 'hover': (0,150,0), 'quit': (100,0,0), 'quit_hover': (150,0,0),
               'back': (60,60,100), 'back_hover': (80,80,130)}
}

class Button:
    def __init__(self, x, y, w, h, text, color_key='normal'):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color_key = color_key
    
    def draw(self, screen, font):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        if hover:
            color = COLORS['button'].get(f'{self.color_key}_hover', COLORS['button'][self.color_key])
        else:
            color = COLORS['button'][self.color_key]
        
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (100,100,150), self.rect, 2, border_radius=8)
        txt = font.render(self.text, True, COLORS['text'])
        screen.blit(txt, txt.get_rect(center=self.rect.center))
    
    def clicked(self, pos): 
        return self.rect.collidepoint(pos)

class Toggle:
    def __init__(self, x, y, label, is_on=True):
        self.x, self.y = x, y
        self.label = label
        self.is_on = is_on
        self.w, self.h = 60, 30
    
    def draw(self, screen, font):
        label_surf = font.render(self.label, True, COLORS['text'])
        screen.blit(label_surf, (self.x, self.y + 5))
        
        color = (60,180,60) if self.is_on else (180,60,60)
        rect = pygame.Rect(self.x + 200, self.y, self.w, self.h)
        pygame.draw.rect(screen, color, rect, border_radius=15)
        pygame.draw.rect(screen, (100,100,150), rect, 2, border_radius=15)
        
        knob_x = self.x + 200 + (self.w - 20) if self.is_on else self.x + 200 + 4
        pygame.draw.circle(screen, (255,255,255), (knob_x + 8, self.y + self.h//2), 10)
        
        status = font.render("ON" if self.is_on else "OFF", True, color)
        screen.blit(status, (self.x + 280, self.y + 5))
    
    def clicked(self, pos):
        rect = pygame.Rect(self.x + 200, self.y, self.w, self.h)
        if rect.collidepoint(pos):
            self.is_on = not self.is_on
            return True
        return False

class ColorPicker:
    def __init__(self, x, y, colors):
        self.x, self.y = x, y
        self.colors = colors
        self.idx = 0
        self.size = 35
        self.spacing = 10
    
    def draw(self, screen, font):
        label = font.render("Snake Color:", True, COLORS['text'])
        screen.blit(label, (self.x, self.y + 8))
        
        for i, color in enumerate(self.colors):
            rect = pygame.Rect(self.x + 200 + i*(self.size + self.spacing), self.y, self.size, self.size)
            pygame.draw.rect(screen, tuple(color), rect, border_radius=5)
            pygame.draw.rect(screen, (100,100,150), rect, 2, border_radius=5)
            
            if i == self.idx:
                pygame.draw.line(screen, COLORS['text'], (rect.x+8, rect.y+self.size//2),
                               (rect.x+self.size//2, rect.y+self.size-8), 3)
                pygame.draw.line(screen, COLORS['text'], (rect.x+self.size//2, rect.y+self.size-8),
                               (rect.x+self.size-8, rect.y+8), 3)
    
    def clicked(self, pos):
        for i in range(len(self.colors)):
            rect = pygame.Rect(self.x + 200 + i*(self.size + self.spacing), self.y, self.size, self.size)
            if rect.collidepoint(pos):
                self.idx = i
                return self.colors[i]
        return None

class Menu:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 28)
        self.font_xl = pygame.font.Font(None, 36)
        self.font_xxl = pygame.font.Font(None, 48)
        
        self.load_settings()
        
        self.username = ""
        self.input_text = ""
        self.personal_best = 0
        self.state = "username"
        
        self.load_scores()
        
        self.create_buttons()
        
        self.available_colors = [[0,255,0], [255,0,0], [0,0,255], [255,255,0], [255,0,255], [0,255,255]]
        self.color_picker = ColorPicker(250, 320, self.available_colors)
        
        current_color = self.settings.get('snake_color', [0,255,0])
        if current_color in self.available_colors:
            self.color_picker.idx = self.available_colors.index(current_color)
        else:
            self.color_picker.idx = 0
        
        self.grid_toggle = Toggle(250, 200, "Show Grid", self.settings.get('grid', True))
        self.sound_toggle = Toggle(250, 260, "Sound Effects", self.settings.get('sound', True))
    
    def load_settings(self):
        default = {"snake_color": [0,255,0], "grid": True, "sound": True}
        try:
            with open('settings.json', 'r') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.settings = default.copy()
                    self.settings.update(loaded)
                else:
                    self.settings = default.copy()
        except:
            self.settings = default.copy()
    
    def save_settings(self):
        self.settings['grid'] = self.grid_toggle.is_on
        self.settings['sound'] = self.sound_toggle.is_on
        self.settings['snake_color'] = self.available_colors[self.color_picker.idx]
        
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def load_scores(self):
        try:
            with open('scores.json', 'r') as f:
                self.scores = json.load(f)
        except:
            self.scores = {"sessions": []}
    
    def save_score(self, score, level):
        if self.username:
            self.scores["sessions"].append({
                "username": self.username,
                "score": score,
                "level": level,
                "date": datetime.now().isoformat()
            })
            with open('scores.json', 'w') as f:
                json.dump(self.scores, f, indent=2)
    
    def get_leaderboard(self):
        sorted_sessions = sorted(self.scores["sessions"], key=lambda x: x["score"], reverse=True)
        return [(s["username"], s["score"], s["level"], s["date"][:10]) for s in sorted_sessions[:10]]
    
    def get_personal_best(self):
        best = 0
        for s in self.scores["sessions"]:
            if s["username"] == self.username and s["score"] > best:
                best = s["score"]
        return best
    
    def create_buttons(self):
        cx, w = W//2 - 100, 200
        self.btns = {
            'main': [
                Button(cx, 200, w, 50, "PLAY"),
                Button(cx, 270, w, 50, "LEADERBOARD"),
                Button(cx, 340, w, 50, "SETTINGS"),
                Button(cx, 410, w, 50, "QUIT", 'quit')
            ],
            'back': Button(W-150, H-80, 120, 40, "BACK", 'back'),
            'save': Button(W//2-100, H-100, 200, 50, "SAVE & BACK")
        }
    
    def start_game(self):
  
        self.save_settings()
        
        game_settings = self.settings.copy()
        
        game = Game(game_settings)
        score, level, game_over = game.run()
        
        if game_over:
            self.save_score(score, level)
            self.personal_best = self.get_personal_best()
        
        self.state = "menu"
        pygame.display.set_mode((W, H))
        pygame.display.set_caption("Snake Game")
    
    def draw_username(self):
        self.screen.fill(COLORS['bg'])
        
        title = self.font_xxl.render("ENTER USERNAME", True, COLORS['green'])
        self.screen.blit(title, title.get_rect(center=(W//2, 150)))
        
        box = pygame.Rect(W//2 - 150, 250, 300, 50)
        pygame.draw.rect(self.screen, COLORS['text'], box, 2, border_radius=8)
        
        text_surface = self.font_xl.render(self.input_text, True, COLORS['text'])
        self.screen.blit(text_surface, (box.x + 10, box.y + 10))
        
        inst = self.font_medium.render("Press ENTER to start", True, (150,150,150))
        self.screen.blit(inst, inst.get_rect(center=(W//2, 350)))
        
        pygame.display.flip()
    
    def draw_menu(self):
        self.screen.fill(COLORS['bg'])
        
        title = self.font_xxl.render("SNAKE GAME", True, COLORS['green'])
        self.screen.blit(title, title.get_rect(center=(W//2, 100)))
        
        if self.username:
            name_text = self.font_medium.render(f"Player: {self.username}", True, COLORS['text'])
            self.screen.blit(name_text, (20, 20))
            
            if self.personal_best > 0:
                best_text = self.font_medium.render(f"Best: {self.personal_best}", True, COLORS['green'])
                self.screen.blit(best_text, (20, 50))
        
        for btn in self.btns['main']:
            btn.draw(self.screen, self.font_xl)
        
        pygame.display.flip()
    
    def draw_leaderboard(self):
        self.screen.fill(COLORS['bg'])
        
        title = self.font_xxl.render("LEADERBOARD", True, COLORS['green'])
        self.screen.blit(title, title.get_rect(center=(W//2, 50)))
        
        headers = ["#", "NAME", "SCORE", "LVL", "DATE"]
        x_pos = [50, 150, 400, 520, 600]
        
        for i, h in enumerate(headers):
            self.screen.blit(self.font_medium.render(h, True, (255,255,0)), (x_pos[i], 120))
        
        y = 170
        for rank, (name, score, level, date) in enumerate(self.get_leaderboard(), 1):
            color = (255,215,0) if rank == 1 else COLORS['text']
            
            self.screen.blit(self.font_medium.render(str(rank), True, color), (x_pos[0], y))
            self.screen.blit(self.font_medium.render(name[:15], True, COLORS['text']), (x_pos[1], y))
            self.screen.blit(self.font_medium.render(str(score), True, COLORS['text']), (x_pos[2], y))
            self.screen.blit(self.font_medium.render(str(level), True, COLORS['text']), (x_pos[3], y))
            self.screen.blit(self.font_small.render(date, True, COLORS['text']), (x_pos[4], y))
            
            y += 35
            if y > 500:
                break
        
        self.btns['back'].draw(self.screen, self.font_xl)
        pygame.display.flip()
    
    def draw_settings(self):
        self.screen.fill(COLORS['bg'])
        
        title = self.font_xxl.render("SETTINGS", True, COLORS['green'])
        self.screen.blit(title, title.get_rect(center=(W//2, 50)))
        
        self.grid_toggle.draw(self.screen, self.font_large)
        self.sound_toggle.draw(self.screen, self.font_large)
        self.color_picker.draw(self.screen, self.font_large)
        
        preview_text = self.font_small.render("Preview:", True, COLORS['text'])
        self.screen.blit(preview_text, (250, 400))
        
        preview_color = tuple(self.available_colors[self.color_picker.idx])
        for i in range(3):
            pygame.draw.rect(self.screen, preview_color, (350 + i*25, 395, 20, 20), border_radius=3)
        
        self.btns['save'].draw(self.screen, self.font_xl)
        pygame.display.flip()
    
    def handle_username_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.input_text.strip():
                self.username = self.input_text
                self.personal_best = self.get_personal_best()
                self.state = "menu"
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif len(self.input_text) < 20 and hasattr(event, 'unicode') and event.unicode.isalnum():
                self.input_text += event.unicode
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif self.state == "username":
                    self.handle_username_input(event)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    
                    if self.state == "menu":
                        if self.btns['main'][0].clicked(pos):
                            self.start_game()
                        elif self.btns['main'][1].clicked(pos):
                            self.state = "leaderboard"
                        elif self.btns['main'][2].clicked(pos):
                            self.grid_toggle.is_on = self.settings.get('grid', True)
                            self.sound_toggle.is_on = self.settings.get('sound', True)
                            self.state = "settings"
                        elif self.btns['main'][3].clicked(pos):
                            running = False
                    
                    elif self.state == "leaderboard":
                        if self.btns['back'].clicked(pos):
                            self.state = "menu"
                    
                    elif self.state == "settings":
                        self.grid_toggle.clicked(pos)
                        self.sound_toggle.clicked(pos)
                        
                        new_color = self.color_picker.clicked(pos)
                        if new_color:
                            self.settings['snake_color'] = new_color
                        
                        if self.btns['save'].clicked(pos):
                            self.save_settings()
                            self.state = "menu"
            
            if self.state == "username":
                self.draw_username()
            elif self.state == "menu":
                self.draw_menu()
            elif self.state == "leaderboard":
                self.draw_leaderboard()
            elif self.state == "settings":
                self.draw_settings()
            
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    menu = Menu()
    menu.run()