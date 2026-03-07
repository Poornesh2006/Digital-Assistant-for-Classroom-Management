import sqlite3

from database.db import get_db_path, init_db, seed_demo_ai_logs


def get_connection() -> sqlite3.Connection:
    init_db()
    return sqlite3.connect(get_db_path())


__all__ = ["get_connection", "init_db", "seed_demo_ai_logs"]
