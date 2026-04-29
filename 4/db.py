# db.py - Version that works with or without PostgreSQL
import json
from datetime import datetime
import os

class Database:
    def __init__(self, dbname="snake_game", user="postgres", password="Rei_111333", host="localhost"):
        self.use_postgres = False
        self.conn = None
        
        # Try to import psycopg2
        try:
            import psycopg2
            self.psycopg2 = psycopg2
            self.use_postgres = True
        except ImportError:
            print("psycopg2 not installed. Using local JSON file storage.")
            self.use_postgres = False
            self.init_json_storage()
        
        if self.use_postgres:
            try:
                self.conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host
                )
                self.cur = self.conn.cursor()
                self.create_tables()
                print("Connected to PostgreSQL database")
            except Exception as e:
                print(f"Database connection error: {e}")
                print("Falling back to local JSON file storage")
                self.use_postgres = False
                self.init_json_storage()
    
    def init_json_storage(self):
        """Initialize JSON file storage"""
        self.json_file = "game_data.json"
        if not os.path.exists(self.json_file):
            with open(self.json_file, 'w') as f:
                json.dump({"players": {}, "sessions": []}, f)
    
    def create_tables(self):
        """Create tables if they don't exist"""
        if not self.conn:
            return
            
        # Create players table
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        
        # Create game_sessions table
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id),
                score INTEGER NOT NULL,
                level_reached INTEGER NOT NULL,
                played_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
    
    def get_or_create_player(self, username):
        """Get existing player or create new one"""
        if not self.use_postgres:
            return self.json_get_or_create_player(username)
            
        # Try to get existing player
        self.cur.execute("SELECT id FROM players WHERE username = %s", (username,))
        result = self.cur.fetchone()
        
        if result:
            return result[0]
        
        # Create new player
        self.cur.execute("INSERT INTO players (username) VALUES (%s) RETURNING id", (username,))
        player_id = self.cur.fetchone()[0]
        self.conn.commit()
        return player_id
    
    def json_get_or_create_player(self, username):
        """JSON storage version of get_or_create_player"""
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        if username not in data["players"]:
            player_id = len(data["players"]) + 1
            data["players"][username] = {"id": player_id, "username": username}
            with open(self.json_file, 'w') as f:
                json.dump(data, f)
            return player_id
        else:
            return data["players"][username]["id"]
    
    def save_game_result(self, username, score, level_reached):
        """Save game result to database"""
        if not self.use_postgres:
            self.json_save_game_result(username, score, level_reached)
            return
            
        player_id = self.get_or_create_player(username)
        
        self.cur.execute("""
            INSERT INTO game_sessions (player_id, score, level_reached)
            VALUES (%s, %s, %s)
        """, (player_id, score, level_reached))
        
        self.conn.commit()
    
    def json_save_game_result(self, username, score, level_reached):
        """JSON storage version of save_game_result"""
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        player_id = self.json_get_or_create_player(username)
        
        session = {
            "player_id": player_id,
            "username": username,
            "score": score,
            "level_reached": level_reached,
            "played_at": datetime.now().isoformat()
        }
        data["sessions"].append(session)
        
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
    
    def get_leaderboard(self, limit=10):
        """Get top 10 scores"""
        if not self.use_postgres:
            return self.json_get_leaderboard(limit)
            
        self.cur.execute("""
            SELECT p.username, gs.score, gs.level_reached, gs.played_at
            FROM game_sessions gs
            JOIN players p ON gs.player_id = p.id
            ORDER BY gs.score DESC
            LIMIT %s
        """, (limit,))
        
        return self.cur.fetchall()
    
    def json_get_leaderboard(self, limit=10):
        """JSON storage version of get_leaderboard"""
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        # Sort sessions by score
        sessions = sorted(data["sessions"], key=lambda x: x["score"], reverse=True)
        
        result = []
        for session in sessions[:limit]:
            result.append((
                session["username"],
                session["score"],
                session["level_reached"],
                datetime.fromisoformat(session["played_at"])
            ))
        
        return result
    
    def get_personal_best(self, username):
        """Get player's best score"""
        if not self.use_postgres:
            return self.json_get_personal_best(username)
            
        player_id = self.get_or_create_player(username)
        
        self.cur.execute("""
            SELECT MAX(score) FROM game_sessions
            WHERE player_id = %s
        """, (player_id,))
        
        result = self.cur.fetchone()
        return result[0] if result[0] else 0
    
    def json_get_personal_best(self, username):
        """JSON storage version of get_personal_best"""
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        best_score = 0
        for session in data["sessions"]:
            if session["username"] == username and session["score"] > best_score:
                best_score = session["score"]
        
        return best_score
    
    def close(self):
        """Close database connection"""
        if self.use_postgres and self.conn:
            self.cur.close()
            self.conn.close()