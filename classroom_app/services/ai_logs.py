import sqlite3

from database.db import get_db_path

_ai_logs_version = 0
_ai_logs_cache: dict[tuple[int, int, str | None], list[dict[str, str | int | float]]] = {}


def log_ai_result(data: dict, result: dict) -> None:
    global _ai_logs_version
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
    _ai_logs_version += 1
    _ai_logs_cache.clear()


def fetch_ai_logs(limit: int = 100, student_name: str | None = None) -> list[dict[str, str | int | float]]:
    cache_key = (_ai_logs_version, int(limit), student_name or None)
    cached = _ai_logs_cache.get(cache_key)
    if cached is not None:
        return [dict(row) for row in cached]

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
        result = [dict(row) for row in rows]
        _ai_logs_cache[cache_key] = [dict(row) for row in result]
        return result
    finally:
        conn.close()
