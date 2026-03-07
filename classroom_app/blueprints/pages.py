from flask import Blueprint, abort, render_template, request, send_file, session

from classroom_app.blueprints.auth import login_required
from classroom_app.legacy import (
    activity,
    add_course,
    add_student,
    courses,
    dashboard,
    delete_course,
    delete_student,
    department_view,
    edit_course,
    edit_student,
    export_department_report,
    export_student_pdf,
    leaderboard,
    student_profile,
    student_profile_alias,
    students_directory,
)
from classroom_app.services.ai_logs import fetch_ai_logs
from classroom_app.services.data import SEMESTER_ATT_COLS, SEMESTER_TOTAL_COLS, load_students
from utils.graph_generator import chart_file_map, generate_student_charts

bp = Blueprint("pages", __name__)

bp.add_url_rule("/dashboard", view_func=dashboard, methods=["GET"])
bp.add_url_rule("/department/<path:department_name>", view_func=department_view, methods=["GET"])
bp.add_url_rule("/add-student", view_func=add_student, methods=["GET", "POST"])
bp.add_url_rule("/student/<path:student_name>", view_func=student_profile, methods=["GET"], endpoint="student_profile")
bp.add_url_rule("/export/<path:student_name>", view_func=export_student_pdf, methods=["GET"], endpoint="export_student")
bp.add_url_rule("/student_profile/<path:student_name>", view_func=student_profile_alias, methods=["GET"])
bp.add_url_rule("/student-profile/<path:student_name>", view_func=student_profile_alias, methods=["GET"], endpoint="student_profile_kebab")
bp.add_url_rule("/students", view_func=students_directory, methods=["GET"], endpoint="students_directory")
bp.add_url_rule("/leaderboard", view_func=leaderboard, methods=["GET"])
bp.add_url_rule("/export_department/<path:department_name>", view_func=export_department_report, methods=["GET"])
bp.add_url_rule("/activity", view_func=activity, methods=["GET"])
bp.add_url_rule("/edit-student/<path:student_name>", view_func=edit_student, methods=["POST"])
bp.add_url_rule("/delete-student/<path:student_name>", view_func=delete_student, methods=["POST"])
bp.add_url_rule("/courses", view_func=courses, methods=["GET"])
bp.add_url_rule("/add_course", view_func=add_course, methods=["POST"])
bp.add_url_rule("/edit_course/<code>", view_func=edit_course, methods=["GET", "POST"])
bp.add_url_rule("/delete_course/<code>", view_func=delete_course, methods=["GET"])


@bp.route("/ai-logs")
@login_required
def ai_logs_page():
    limit_raw = request.args.get("limit", "100").strip()
    student_name = request.args.get("student", "").strip()

    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 100

    limit = max(1, min(limit, 500))
    logs = fetch_ai_logs(limit=limit, student_name=student_name or None)
    return render_template(
        "ai_logs.html",
        username=session.get("username", "Faculty"),
        logs=logs,
        limit=limit,
        student_name=student_name,
    )


@bp.route("/charts/<chart_type>/<path:student_name>.png")
@login_required
def student_chart(chart_type: str, student_name: str):
    chart_type = chart_type.strip().lower()
    if chart_type not in {"performance", "attendance", "contribution"}:
        abort(404)

    students_df = load_students()
    selected = students_df[students_df["Name"].astype(str) == student_name]
    if selected.empty:
        selected = students_df[students_df["Name"].astype(str).str.lower() == student_name.lower()]
    if selected.empty:
        abort(404)

    student = selected.iloc[0]
    semester_totals = [int(student[col]) for col in SEMESTER_TOTAL_COLS]
    semester_attendance = [int(student[col]) for col in SEMESTER_ATT_COLS]
    generate_student_charts(str(student["Name"]), semester_totals, semester_attendance)

    chart_path = chart_file_map(str(student["Name"]))[chart_type]
    if not chart_path.exists():
        abort(404)

    return send_file(chart_path, mimetype="image/png")


ALIAS_ROUTES = [
    {"rule": "/", "endpoint": "login", "target": "auth.login", "methods": ["GET", "POST"]},
    {"rule": "/login", "endpoint": "login_form", "target": "auth.login", "methods": ["GET", "POST"]},
    {"rule": "/logout", "endpoint": "logout", "target": "auth.logout", "methods": ["GET"]},
    {"rule": "/dashboard", "endpoint": "dashboard", "target": "pages.dashboard", "methods": ["GET"]},
    {"rule": "/department/<path:department_name>", "endpoint": "department_view", "target": "pages.department_view", "methods": ["GET"]},
    {"rule": "/add-student", "endpoint": "add_student", "target": "pages.add_student", "methods": ["GET", "POST"]},
    {"rule": "/student/<path:student_name>", "endpoint": "student_profile", "target": "pages.student_profile", "methods": ["GET"]},
    {"rule": "/export/<path:student_name>", "endpoint": "export_student", "target": "pages.export_student", "methods": ["GET"]},
    {"rule": "/students", "endpoint": "students_directory", "target": "pages.students_directory", "methods": ["GET"]},
    {"rule": "/leaderboard", "endpoint": "leaderboard", "target": "pages.leaderboard", "methods": ["GET"]},
    {"rule": "/export_department/<path:department_name>", "endpoint": "export_department_report", "target": "pages.export_department_report", "methods": ["GET"]},
    {"rule": "/activity", "endpoint": "activity", "target": "pages.activity", "methods": ["GET"]},
    {"rule": "/edit-student/<path:student_name>", "endpoint": "edit_student", "target": "pages.edit_student", "methods": ["POST"]},
    {"rule": "/delete-student/<path:student_name>", "endpoint": "delete_student", "target": "pages.delete_student", "methods": ["POST"]},
    {"rule": "/courses", "endpoint": "courses", "target": "pages.courses", "methods": ["GET"]},
    {"rule": "/add_course", "endpoint": "add_course", "target": "pages.add_course", "methods": ["POST"]},
    {"rule": "/edit_course/<code>", "endpoint": "edit_course", "target": "pages.edit_course", "methods": ["GET", "POST"]},
    {"rule": "/delete_course/<code>", "endpoint": "delete_course", "target": "pages.delete_course", "methods": ["GET"]},
    {"rule": "/ai-logs", "endpoint": "ai_logs_page", "target": "pages.ai_logs_page", "methods": ["GET"]},
    {"rule": "/charts/<chart_type>/<path:student_name>.png", "endpoint": "student_chart", "target": "pages.student_chart", "methods": ["GET"]},
]
