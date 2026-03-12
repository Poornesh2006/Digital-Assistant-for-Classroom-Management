from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from flask import Blueprint, jsonify, request

from classroom_app.services.ai_logs import fetch_ai_logs, log_ai_result
from classroom_app.services.data import log_activity
from utils.ai_engine import analyze_student

bp = Blueprint("api", __name__, url_prefix="/api")

AI_TIMEOUT_SECONDS = 5
_ANALYSIS_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def _safe_student_label(data: dict) -> str:
    name = str(data.get("Name", "")).strip() or "Unknown"
    register_number = str(data.get("RegisterNumber", "")).strip().upper() or "N/A"
    return f"{name} ({register_number})"


def _run_analysis_with_timeout(data: dict) -> dict:
    future = _ANALYSIS_EXECUTOR.submit(analyze_student, data)
    return future.result(timeout=AI_TIMEOUT_SECONDS)


@bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    try:
        result = _run_analysis_with_timeout(data)
        log_ai_result(data, result)
        log_activity("AI analysis", details=_safe_student_label(data))
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except FutureTimeoutError:
        log_activity("AI analysis timeout", details=_safe_student_label(data))
        return jsonify({"error": f"AI processing timed out after {AI_TIMEOUT_SECONDS} seconds."}), 504
    except Exception:
        log_activity("AI analysis failed", details=_safe_student_label(data))
        return jsonify({"error": "AI processing failed. Please try again."}), 500


@bp.route("/analyze_async", methods=["POST"])
def analyze_async():
    return analyze()


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
