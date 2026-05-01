
import json
import os

class DataManager:
    def __init__(self):
        self.settings_file = "settings.json"
        self.leaderboard_file = "leaderboard.json"
        self.load_settings()
        self.load_leaderboard()
    
    def load_settings(self):
        default_settings = {
            "sound_enabled": True,
            "car_color": "purple",
            "difficulty": "normal"  # easy, normal, hard
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings
            self.save_settings()
    
    def save_settings(self):
        """Сохраняет настройки в файл"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def load_leaderboard(self):
        """Загружает таблицу рекордов"""
        if os.path.exists(self.leaderboard_file):
            try:
                with open(self.leaderboard_file, 'r') as f:
                    self.leaderboard = json.load(f)
            except:
                self.leaderboard = []
        else:
            self.leaderboard = []
    
    def save_leaderboard(self):
        """Сохраняет таблицу рекордов"""
        # Сортируем по убыванию очков и берем топ-10
        self.leaderboard.sort(key=lambda x: x['score'], reverse=True)
        self.leaderboard = self.leaderboard[:10]
        
        with open(self.leaderboard_file, 'w') as f:
            json.dump(self.leaderboard, f, indent=4)
    
    def add_score(self, name, score, distance, coins):
        """Добавляет новый результат"""
        self.leaderboard.append({
            'name': name,
            'score': score,
            'distance': distance,
            'coins': coins
        })
        self.save_leaderboard()
    
    def get_difficulty_settings(self):
        """Возвращает настройки сложности"""
        difficulty = self.settings.get('difficulty', 'normal')
        if difficulty == 'easy':
            return {
                'enemy_speed': 3,
                'enemy_spawn_rate': 120,
                'obstacle_spawn_rate': 180,
                'powerup_spawn_rate': 300
            }
        elif difficulty == 'hard':
            return {
                'enemy_speed': 7,
                'enemy_spawn_rate': 60,
                'obstacle_spawn_rate': 90,
                'powerup_spawn_rate': 200
            }
        else:  # normal
            return {
                'enemy_speed': 5,
                'enemy_spawn_rate': 90,
                'obstacle_spawn_rate': 120,
                'powerup_spawn_rate': 250
            }