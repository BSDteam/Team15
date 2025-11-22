# db.py
import psycopg2
from config import DB_CONFIG

def execute_query(query: str, params: tuple = None, fetch: bool = False):
    """
    Выполняет SQL-запрос.
    - Если fetch=True — возвращает результат (для SELECT).
    - Иначе — только выполняет (для INSERT/UPDATE).
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
    finally:
        conn.close()