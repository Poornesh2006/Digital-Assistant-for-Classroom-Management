import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")


def get_db_path() -> str:
    return DB_PATH


def init_db() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                risk_level TEXT,
                performance_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        seed_demo_ai_logs(conn)
    finally:
        conn.close()


def seed_demo_ai_logs(conn: sqlite3.Connection | None = None) -> None:
    owns_connection = conn is None
    connection = conn or sqlite3.connect(DB_PATH)
    try:
        row = connection.execute("SELECT COUNT(*) FROM ai_logs").fetchone()
        count = int(row[0]) if row else 0
        if count > 0:
            return

        demo_rows = [
            ("Aarav Kumar", "Low", 8.7),
            ("Diya Mishra", "Medium", 6.9),
            ("Rahul Nair", "High", 4.8),
        ]
        connection.executemany(
            "INSERT INTO ai_logs (student_name, risk_level, performance_score) VALUES (?, ?, ?)",
            demo_rows,
        )
        connection.commit()
    finally:
        if owns_connection:
            connection.close()
