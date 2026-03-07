import asyncio

from flask import Blueprint, jsonify, request

from classroom_app.services.ai_logs import fetch_ai_logs, log_ai_result
from utils.ai_engine import analyze_student

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    result = analyze_student(data)
    log_ai_result(data, result)
    return jsonify(result)


@bp.route("/analyze_async", methods=["POST"])
async def analyze_async():
    data = request.json or {}
    result = await asyncio.to_thread(analyze_student, data)
    await asyncio.to_thread(log_ai_result, data, result)
    return jsonify(result)


@bp.route("/ai-logs", methods=["GET"])
def ai_logs():
    limit_raw = request.args.get("limit", "100").strip()
    student_name = request.args.get("student", "").strip()

    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 100

    limit = max(1, min(limit, 500))
    logs = fetch_ai_logs(limit=limit, student_name=student_name or None)
    return jsonify({"count": len(logs), "logs": logs})
