import sqlite3

from database.db import get_db_path


def log_ai_result(data: dict, result: dict) -> None:
    conn = sqlite3.connect(get_db_path())
    try:
        conn.execute(
            "INSERT INTO ai_logs (student_name, risk_level, performance_score) VALUES (?, ?, ?)",
            (
                data.get("Name"),
                result["risk_level"],
                result["performance_score"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_ai_logs(limit: int = 100, student_name: str | None = None) -> list[dict[str, str | int | float]]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        query = "SELECT id, student_name, risk_level, performance_score, timestamp FROM ai_logs"
        params: list[object] = []
        if student_name:
            query += " WHERE student_name LIKE ?"
            params.append(f"%{student_name}%")
        query += " ORDER BY timestamp DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
