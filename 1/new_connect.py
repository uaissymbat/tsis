import psycopg2
from new_config import load_config

def connect():
    """Connect to the PostgreSQL database."""
    config = load_config()  
    try:
        conn = psycopg2.connect(**config)
        print('Connected to the PostgreSQL server.')
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Database connection failed: {error}")
        return None

if __name__ == '__main__':
    connect()