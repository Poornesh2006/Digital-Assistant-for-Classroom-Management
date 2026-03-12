from flask import Blueprint, Response, abort, flash, redirect, render_template, request, send_file, session, url_for

from classroom_app.blueprints.auth import login_required
from classroom_app.config import DEPARTMENTS
from classroom_app.legacy import (
    activity,
    add_course,
    courses,
    dashboard,
    delete_course,
    department_view,
    edit_course,
    export_department_report,
    export_student_pdf,
    leaderboard,
    student_profile,
    student_profile_alias,
)
from classroom_app.services.ai_logs import fetch_ai_logs
from classroom_app.services.data import SEMESTER_ATT_COLS, SEMESTER_TOTAL_COLS, append_feedback_entry, ensure_feedback_file, get_course_info, load_students, log_activity
from classroom_app.services.student_management import (
    add_student as add_student_record,
    bulk_delete_students,
    delete_student as delete_student_record,
    edit_student as edit_student_record,
    export_students_csv,
    get_student_by_id,
    get_student_management_data,
)
from utils.graph_generator import chart_file_map, generate_student_charts

bp = Blueprint("pages", __name__)

bp.add_url_rule("/dashboard", view_func=dashboard, methods=["GET"])
bp.add_url_rule("/department/<path:department_name>", view_func=department_view, methods=["GET"])
bp.add_url_rule("/student/<path:register_number>", view_func=student_profile, methods=["GET"], endpoint="student_profile")
bp.add_url_rule("/export/<path:register_number>", view_func=export_student_pdf, methods=["GET"], endpoint="export_student")
bp.add_url_rule("/student_profile/<path:register_number>", view_func=student_profile_alias, methods=["GET"])
bp.add_url_rule("/student-profile/<path:register_number>", view_func=student_profile_alias, methods=["GET"], endpoint="student_profile_kebab")
bp.add_url_rule("/leaderboard", view_func=leaderboard, methods=["GET"])
bp.add_url_rule("/export_department/<path:department_name>", view_func=export_department_report, methods=["GET"])
bp.add_url_rule("/activity", view_func=activity, methods=["GET"])
bp.add_url_rule("/courses", view_func=courses, methods=["GET"])
bp.add_url_rule("/add_course", view_func=add_course, methods=["POST"])
bp.add_url_rule("/edit_course/<code>", view_func=edit_course, methods=["GET", "POST"])
bp.add_url_rule("/delete_course/<code>", view_func=delete_course, methods=["GET"])


@bp.route("/")
def home():
    return render_template("ai_intro.html")


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


@bp.route("/intro")
@login_required
def intro_animation():
    return render_template("intro_animation.html", username=session.get("username", "Faculty"))


@bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback_page():
    success = None
    error = None
    form_data = {"name": "", "email": "", "message": "", "rating": ""}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        rating = request.form.get("rating", "").strip()
        form_data = {"name": name, "email": email, "message": message, "rating": rating}

        if not name:
            error = "Please fill all fields."
        elif not email:
            error = "Please fill all fields."
        elif not message:
            error = "Please fill all fields."
        elif not rating:
            error = "Please fill all fields."
        else:
            try:
                ensure_feedback_file()
                append_feedback_entry(
                    {
                        "name": name,
                        "email": email,
                        "message": message,
                        "rating": rating,
                    }
                )
                log_activity("Feedback submitted", username=session.get("username", "Faculty"), details=f"{name} ({rating})")
                success = "Your feedback submitted successfully"
                form_data = {"name": "", "email": "", "message": "", "rating": ""}
            except Exception:
                log_activity("Feedback submission failed", username=session.get("username", "Faculty"), details=name or "Unknown")
                error = "Unable to save feedback right now. Please try again."

    return render_template(
        "feedback.html",
        username=session.get("username", "Faculty"),
        success=success,
        error=error,
        form_data=form_data,
    )


@bp.route("/students")
@login_required
def students():
    context = get_student_management_data(
        search=request.args.get("search", ""),
        department=request.args.get("department", "All"),
        sort=request.args.get("sort", "name_asc"),
    )
    return render_template(
        "students.html",
        username=session.get("username", "Faculty"),
        **context,
    )


@bp.route("/student-management")
@login_required
def student_management():
    context = get_student_management_data(
        search=request.args.get("search", ""),
        department=request.args.get("department", "All"),
        sort=request.args.get("sort", "name_asc"),
    )
    return render_template(
        "student_management.html",
        username=session.get("username", "Faculty"),
        **context,
    )


@bp.route("/add_student", methods=["GET", "POST"])
@login_required
def student_management_add_student():
    course_info = get_course_info()
    if request.method == "GET":
        return render_template(
            "student_form.html",
            username=session.get("username", "Faculty"),
            page_title="Add Student",
            submit_label="Save Student",
            action_url=url_for("pages.student_management_add_student"),
            student=None,
            departments=DEPARTMENTS,
            course_info=course_info,
        )

    try:
        add_student_record(request.form, request.files.get("profile_image"), username=session.get("username", "Faculty"))
        flash("Student added successfully.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
        return render_template(
            "student_form.html",
            username=session.get("username", "Faculty"),
            page_title="Add Student",
            submit_label="Save Student",
            action_url=url_for("pages.student_management_add_student"),
            student=request.form,
            departments=DEPARTMENTS,
            course_info=course_info,
        )
    except Exception:
        log_activity("Student add failed", username=session.get("username", "Faculty"), details="Unexpected form or file error")
        flash("Unable to save the student record right now. Please verify the input and try again.", "error")
        return render_template(
            "student_form.html",
            username=session.get("username", "Faculty"),
            page_title="Add Student",
            submit_label="Save Student",
            action_url=url_for("pages.student_management_add_student"),
            student=request.form,
            departments=DEPARTMENTS,
            course_info=course_info,
        )
    return redirect(url_for("pages.student_management"))


@bp.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
@login_required
def student_management_edit_student(student_id: int):
    course_info = get_course_info()
    try:
        student = get_student_by_id(student_id)
    except ValueError:
        abort(404)

    if request.method == "GET":
        return render_template(
            "student_form.html",
            username=session.get("username", "Faculty"),
            page_title="Edit Student",
            submit_label="Update Student",
            action_url=url_for("pages.student_management_edit_student", student_id=student_id),
            student=student,
            departments=DEPARTMENTS,
            course_info=course_info,
        )

    try:
        edit_student_record(student_id, request.form, request.files.get("profile_image"), username=session.get("username", "Faculty"))
        flash("Student updated successfully.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
        return render_template(
            "student_form.html",
            username=session.get("username", "Faculty"),
            page_title="Edit Student",
            submit_label="Update Student",
            action_url=url_for("pages.student_management_edit_student", student_id=student_id),
            student=request.form,
            departments=DEPARTMENTS,
            course_info=course_info,
        )
    except Exception:
        log_activity("Student update failed", username=session.get("username", "Faculty"), details=f"Student ID {student_id}")
        flash("Unable to update the student record right now. Please try again.", "error")
        return render_template(
            "student_form.html",
            username=session.get("username", "Faculty"),
            page_title="Edit Student",
            submit_label="Update Student",
            action_url=url_for("pages.student_management_edit_student", student_id=student_id),
            student=request.form,
            departments=DEPARTMENTS,
            course_info=course_info,
        )
    return redirect(url_for("pages.student_management"))


@bp.route("/delete_student/<int:student_id>", methods=["POST"])
@login_required
def student_management_delete_student(student_id: int):
    try:
        delete_student_record(student_id, username=session.get("username", "Faculty"))
        flash("Student deleted successfully.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    except Exception:
        log_activity("Student delete failed", username=session.get("username", "Faculty"), details=f"Student ID {student_id}")
        flash("Unable to delete the student right now.", "error")
    return redirect(url_for("pages.student_management"))


@bp.route("/students/bulk-delete", methods=["POST"])
@login_required
def student_management_bulk_delete():
    raw_ids = request.form.getlist("student_ids")
    parsed_ids: list[int] = []
    for raw_id in raw_ids:
        try:
            parsed_ids.append(int(raw_id))
        except ValueError:
            continue

    try:
        deleted_count = bulk_delete_students(parsed_ids, username=session.get("username", "Faculty"))
        if deleted_count:
            flash(f"{deleted_count} students deleted successfully.", "success")
        else:
            flash("Select at least one student to delete.", "error")
    except Exception:
        log_activity("Bulk student delete failed", username=session.get("username", "Faculty"), details=",".join(raw_ids))
        flash("Unable to complete bulk delete. Please try again.", "error")
    return redirect(url_for("pages.student_management"))


@bp.route("/students/export", methods=["GET"])
@login_required
def student_management_export():
    try:
        csv_content, filename = export_students_csv(
            search=request.args.get("search", ""),
            department=request.args.get("department", "All"),
            sort=request.args.get("sort", "name_asc"),
        )
        log_activity("Student export", username=session.get("username", "Faculty"), details=filename)
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception:
        log_activity("Student export failed", username=session.get("username", "Faculty"), details="CSV export error")
        flash("Unable to export student data right now.", "error")
        return redirect(url_for("pages.student_management"))


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
    {"rule": "/", "endpoint": "home", "target": "pages.home", "methods": ["GET"]},
    {"rule": "/login", "endpoint": "login_form", "target": "auth.login", "methods": ["GET", "POST"]},
    {"rule": "/logout", "endpoint": "logout", "target": "auth.logout", "methods": ["GET"]},
    {"rule": "/dashboard", "endpoint": "dashboard", "target": "pages.dashboard", "methods": ["GET"]},
    {"rule": "/intro", "endpoint": "intro_animation", "target": "pages.intro_animation", "methods": ["GET"]},
    {"rule": "/department/<path:department_name>", "endpoint": "department_view", "target": "pages.department_view", "methods": ["GET"]},
    {"rule": "/student/<path:register_number>", "endpoint": "student_profile", "target": "pages.student_profile", "methods": ["GET"]},
    {"rule": "/export/<path:register_number>", "endpoint": "export_student", "target": "pages.export_student", "methods": ["GET"]},
    {"rule": "/students", "endpoint": "students", "target": "pages.students", "methods": ["GET"]},
    {"rule": "/student-management", "endpoint": "student_management", "target": "pages.student_management", "methods": ["GET"]},
    {"rule": "/leaderboard", "endpoint": "leaderboard", "target": "pages.leaderboard", "methods": ["GET"]},
    {"rule": "/export_department/<path:department_name>", "endpoint": "export_department_report", "target": "pages.export_department_report", "methods": ["GET"]},
    {"rule": "/activity", "endpoint": "activity", "target": "pages.activity", "methods": ["GET"]},
    {"rule": "/courses", "endpoint": "courses", "target": "pages.courses", "methods": ["GET"]},
    {"rule": "/add_course", "endpoint": "add_course", "target": "pages.add_course", "methods": ["POST"]},
    {"rule": "/edit_course/<code>", "endpoint": "edit_course", "target": "pages.edit_course", "methods": ["GET", "POST"]},
    {"rule": "/delete_course/<code>", "endpoint": "delete_course", "target": "pages.delete_course", "methods": ["GET"]},
    {"rule": "/ai-logs", "endpoint": "ai_logs_page", "target": "pages.ai_logs_page", "methods": ["GET"]},
    {"rule": "/feedback", "endpoint": "feedback_page", "target": "pages.feedback_page", "methods": ["GET", "POST"]},
    {"rule": "/add_student", "endpoint": "student_management_add_student", "target": "pages.student_management_add_student", "methods": ["GET", "POST"]},
    {"rule": "/edit_student/<int:student_id>", "endpoint": "student_management_edit_student", "target": "pages.student_management_edit_student", "methods": ["GET", "POST"]},
    {"rule": "/delete_student/<int:student_id>", "endpoint": "student_management_delete_student", "target": "pages.student_management_delete_student", "methods": ["POST"]},
    {"rule": "/students/bulk-delete", "endpoint": "student_management_bulk_delete", "target": "pages.student_management_bulk_delete", "methods": ["POST"]},
    {"rule": "/students/export", "endpoint": "student_management_export", "target": "pages.student_management_export", "methods": ["GET"]},
    {"rule": "/charts/<chart_type>/<path:student_name>.png", "endpoint": "student_chart", "target": "pages.student_chart", "methods": ["GET"]},
]
