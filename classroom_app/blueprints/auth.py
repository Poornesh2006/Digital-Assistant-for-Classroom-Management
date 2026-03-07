from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from classroom_app.config import FACULTY_USERS
from classroom_app.services.data import log_activity

bp = Blueprint("auth", __name__)


def login_required(route_func):
    """Decorator to protect faculty-only routes."""

    @wraps(route_func)
    def wrapper(*args, **kwargs):
        if not (session.get("user") or session.get("logged_in")):
            flash("Please login to continue.", "error")
            return redirect(url_for("auth.login"))
        return route_func(*args, **kwargs)

    return wrapper


@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login():
    """Faculty login page."""
    if session.get("user") or session.get("logged_in"):
        return redirect(url_for("pages.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        is_default_admin = username == "admin" and password == "admin"
        is_faculty_user = username in FACULTY_USERS and FACULTY_USERS[username] == password

        if is_default_admin or is_faculty_user:
            session["user"] = username
            session["logged_in"] = True
            session["username"] = username
            log_activity("Faculty logged in", username=username, details="Successful login")
            flash("Login successful.", "success")
            return redirect(url_for("pages.dashboard"))

        flash("Invalid login credentials", "error")

    return render_template("login.html")


@bp.route("/logout")
def logout():
    """Clear session and redirect to login page."""
    log_activity(
        "Faculty logged out",
        username=session.get("user") or session.get("username", "Faculty"),
        details="Session ended",
    )
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
