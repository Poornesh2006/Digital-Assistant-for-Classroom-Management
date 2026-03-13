from functools import wraps

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

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


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Faculty login page."""
    if session.get("user") or session.get("logged_in"):
        return redirect(url_for("pages.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = current_app.config.get("LOGIN_USERS", {})

        if not username or not password:
            return render_template("login.html", error="Username and password are required.")

        if username in users and users[username] == password:
            session["user"] = username
            session["logged_in"] = True
            session["username"] = username
            log_activity("Faculty logged in", username=username, details="Successful login")
            return redirect(url_for("pages.intro_animation"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html", error=None)


@bp.route("/logout")
def logout():
    """Clear session and redirect to login page."""
    log_activity(
        "Faculty logged out",
        username=session.get("user") or session.get("username", "Faculty"),
        details="Session ended",
    )
    session.clear()
    return render_template("logout_animation.html")
