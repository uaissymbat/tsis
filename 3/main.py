import pygame
import sys
from racer import Game
from ui import MainMenu, SettingsScreen, LeaderboardScreen, GameOverScreen
from persistence import DataManager

def main():
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    pygame.display.set_caption("Racer Game")
    font = pygame.font.SysFont("Courier New", 30)
    
    data_manager = DataManager()
    username = ""
    
    while True:
        # Главное меню
        menu = MainMenu(screen, font)
        
        # Ввод имени
        entering_name = True
        while entering_name:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if menu.handle_username_input(event):
                    username = menu.username
                    entering_name = False
            
            menu.draw_username_screen()
            pygame.display.flip()
        
        # Основной цикл меню
        in_menu = True
        while in_menu:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            action = menu.handle_events(events)
            
            if action == "play":
                # Запускаем игру
                game = Game(username, data_manager)
                result = game.run()
                
                if result:
                    score, distance, coins = result
                    # Показываем экран Game Over
                    game_over = GameOverScreen(screen, font, score, distance, coins)
                    waiting = True
                    while waiting:
                        go_events = pygame.event.get()
                        for event in go_events:
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                        
                        go_action = game_over.handle_events(go_events)
                        if go_action == "retry":
                            waiting = False
                            # Перезапускаем игру
                            game = Game(username, data_manager)
                            result = game.run()
                            if result:
                                score, distance, coins = result
                                game_over = GameOverScreen(screen, font, score, distance, coins)
                            else:
                                waiting = False
                        elif go_action == "menu":
                            waiting = False
                        
                        game_over.draw()
                        pygame.display.flip()
                
            elif action == "leaderboard":
                leaderboard = LeaderboardScreen(screen, font, data_manager)
                in_leaderboard = True
                while in_leaderboard:
                    lb_events = pygame.event.get()
                    for event in lb_events:
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                    
                    lb_action = leaderboard.handle_events(lb_events)
                    if lb_action == "back":
                        in_leaderboard = False
                    
                    leaderboard.draw()
                    pygame.display.flip()
                    
            elif action == "settings":
                settings = SettingsScreen(screen, font, data_manager)
                in_settings = True
                while in_settings:
                    st_events = pygame.event.get()
                    for event in st_events:
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                    
                    st_action = settings.handle_events(st_events)
                    if st_action == "back":
                        in_settings = False
                    
                    settings.draw()
                    pygame.display.flip()
                    
            elif action == "quit":
                pygame.quit()
                sys.exit()
            
            menu.draw()
            pygame.display.flip()

if __name__ == "__main__":
    main()