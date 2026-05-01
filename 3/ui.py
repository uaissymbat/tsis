import pygame
import sys

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = font
        self.current_color = color
    
    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color
        
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

class MainMenu:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.buttons = []
        self.username = ""
        self.entering_name = True
        
        # Создаем кнопки
        button_width, button_height = 200, 50
        center_x = screen.get_width() // 2 - button_width // 2
        start_y = 200
        
        self.play_button = Button(center_x, start_y, button_width, button_height, 
                                  "PLAY", (0, 128, 0), (0, 255, 0), font)
        self.leaderboard_button = Button(center_x, start_y + 70, button_width, button_height,
                                        "LEADERBOARD", (0, 100, 200), (0, 150, 255), font)
        self.settings_button = Button(center_x, start_y + 140, button_width, button_height,
                                     "SETTINGS", (200, 100, 0), (255, 150, 0), font)
        self.quit_button = Button(center_x, start_y + 210, button_width, button_height,
                                 "QUIT", (200, 0, 0), (255, 0, 0), font)
    
    def handle_username_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.username.strip():
                self.entering_name = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            else:
                if len(self.username) < 20 and event.unicode.isprintable():
                    self.username += event.unicode
        return False
    
    def draw_username_screen(self):
        self.screen.fill((20, 20, 30))
        title = pygame.font.Font(None, 60).render("ENTER YOUR NAME", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Рисуем поле ввода
        input_rect = pygame.Rect(self.screen.get_width() // 2 - 150, 250, 300, 50)
        pygame.draw.rect(self.screen, (50, 50, 70), input_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect, 2)
        
        name_surface = self.font.render(self.username + "_", True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=input_rect.center)
        self.screen.blit(name_surface, name_rect)
        
        instruction = pygame.font.Font(None, 30).render("Press ENTER to start", True, (200, 200, 200))
        inst_rect = instruction.get_rect(center=(self.screen.get_width() // 2, 350))
        self.screen.blit(instruction, inst_rect)
    
    def draw(self):
        self.screen.fill((20, 20, 30))
        title = pygame.font.Font(None, 80).render("RACER GAME", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title, title_rect)
        
        self.play_button.draw(self.screen)
        self.leaderboard_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        self.quit_button.draw(self.screen)
    
    def handle_events(self, events):
        for event in events:
            if self.play_button.is_clicked(event):
                return "play"
            elif self.leaderboard_button.is_clicked(event):
                return "leaderboard"
            elif self.settings_button.is_clicked(event):
                return "settings"
            elif self.quit_button.is_clicked(event):
                pygame.quit()
                sys.exit()
        return None

class SettingsScreen:
    def __init__(self, screen, font, data_manager):
        self.screen = screen
        self.font = font
        self.data_manager = data_manager
        
        button_width, button_height = 250, 40
        center_x = screen.get_width() // 2 - button_width // 2
        start_y = 150
        
        self.sound_button = Button(center_x, start_y, button_width, button_height,
                                   "", (100, 100, 100), (150, 150, 150), font)
        self.car_color_button = Button(center_x, start_y + 60, button_width, button_height,
                                      "", (100, 100, 100), (150, 150, 150), font)
        self.difficulty_button = Button(center_x, start_y + 120, button_width, button_height,
                                       "", (100, 100, 100), (150, 150, 150), font)
        self.back_button = Button(center_x, start_y + 200, button_width, button_height,
                                 "BACK", (100, 0, 0), (200, 0, 0), font)
        
        self.update_button_texts()
    
    def update_button_texts(self):
        sound_text = f"SOUND: {'ON' if self.data_manager.settings['sound_enabled'] else 'OFF'}"
        self.sound_button.text = sound_text
        
        color_text = f"CAR COLOR: {self.data_manager.settings['car_color'].upper()}"
        self.car_color_button.text = color_text
        
        diff_text = f"DIFFICULTY: {self.data_manager.settings['difficulty'].upper()}"
        self.difficulty_button.text = diff_text
    
    def draw(self):
        self.screen.fill((20, 20, 30))
        title = self.font.render("SETTINGS", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)
        
        self.sound_button.draw(self.screen)
        self.car_color_button.draw(self.screen)
        self.difficulty_button.draw(self.screen)
        self.back_button.draw(self.screen)
    
    def handle_events(self, events):
        for event in events:
            if self.sound_button.is_clicked(event):
                self.data_manager.settings['sound_enabled'] = not self.data_manager.settings['sound_enabled']
                self.data_manager.save_settings()
                self.update_button_texts()
                return None
            elif self.car_color_button.is_clicked(event):
                colors = ['purple', 'red', 'blue', 'green']
                current = self.data_manager.settings['car_color']
                next_idx = (colors.index(current) + 1) % len(colors)
                self.data_manager.settings['car_color'] = colors[next_idx]
                self.data_manager.save_settings()
                self.update_button_texts()
                return None
            elif self.difficulty_button.is_clicked(event):
                difficulties = ['easy', 'normal', 'hard']
                current = self.data_manager.settings['difficulty']
                next_idx = (difficulties.index(current) + 1) % len(difficulties)
                self.data_manager.settings['difficulty'] = difficulties[next_idx]
                self.data_manager.save_settings()
                self.update_button_texts()
                return None
            elif self.back_button.is_clicked(event):
                return "back"
        return None

class LeaderboardScreen:
    def __init__(self, screen, font, data_manager):
        self.screen = screen
        self.font = font
        self.data_manager = data_manager
        self.back_button = Button(screen.get_width() // 2 - 100, 400, 200, 50,
                                 "BACK", (100, 0, 0), (200, 0, 0), font)
    
    def draw(self):
        self.screen.fill((20, 20, 30))
        title = self.font.render("TOP 10 RACERS", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Заголовки таблицы
        headers = ["#", "NAME", "SCORE", "DIST", "COINS"]
        x_positions = [50, 120, 250, 350, 430]
        small_font = pygame.font.Font(None, 24)
        
        for i, header in enumerate(headers):
            text = small_font.render(header, True, (255, 255, 255))
            self.screen.blit(text, (x_positions[i], 100))
        
        # Отображаем рекорды
        y = 140
        for i, entry in enumerate(self.data_manager.leaderboard[:10]):
            color = (255, 215, 0) if i == 0 else (200, 200, 200)
            rank = small_font.render(str(i + 1), True, color)
            name = small_font.render(entry['name'][:15], True, color)
            score = small_font.render(str(entry['score']), True, color)
            distance = small_font.render(str(entry['distance']), True, color)
            coins = small_font.render(str(entry['coins']), True, color)
            
            self.screen.blit(rank, (x_positions[0], y))
            self.screen.blit(name, (x_positions[1], y))
            self.screen.blit(score, (x_positions[2], y))
            self.screen.blit(distance, (x_positions[3], y))
            self.screen.blit(coins, (x_positions[4], y))
            y += 30
            
            if y > 380:
                break
        
        self.back_button.draw(self.screen)
    
    def handle_events(self, events):
        for event in events:
            if self.back_button.is_clicked(event):
                return "back"
        return None

class GameOverScreen:
    def __init__(self, screen, font, score, distance, coins):
        self.screen = screen
        self.font = font
        self.score = score
        self.distance = distance
        self.coins = coins
        
        button_width, button_height = 150, 40
        center_x = screen.get_width() // 2 - button_width // 2
        
        self.retry_button = Button(center_x - 85, 350, button_width, button_height,
                                  "RETRY", (0, 128, 0), (0, 255, 0), font)
        self.menu_button = Button(center_x + 85, 350, button_width, button_height,
                                 "MENU", (100, 0, 0), (200, 0, 0), font)
    
    def draw(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        game_over = pygame.font.Font(None, 70).render("GAME OVER", True, (255, 0, 0))
        go_rect = game_over.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(game_over, go_rect)
        
        info = [
            f"SCORE: {self.score}",
            f"DISTANCE: {self.distance}m",
            f"COINS: {self.coins}"
        ]
        
        y = 200
        for text in info:
            surf = self.font.render(text, True, (255, 255, 255))
            rect = surf.get_rect(center=(self.screen.get_width() // 2, y))
            self.screen.blit(surf, rect)
            y += 40
        
        self.retry_button.draw(self.screen)
        self.menu_button.draw(self.screen)
    
    def handle_events(self, events):
        for event in events:
            if self.retry_button.is_clicked(event):
                return "retry"
            elif self.menu_button.is_clicked(event):
                return "menu"
        return None 