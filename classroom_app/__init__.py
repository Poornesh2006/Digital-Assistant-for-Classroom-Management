from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from database.db import init_db

from classroom_app.blueprints.api import bp as api_bp
from classroom_app.blueprints.auth import bp as auth_bp
from classroom_app.blueprints.pages import ALIAS_ROUTES, bp as pages_bp
from classroom_app.config import SECRET_KEY
from classroom_app.legacy import not_found
from classroom_app.services.data import _ensure_activity_log_file, ensure_feedback_file, sync_students_with_courses


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["TEMPLATES_AUTO_RELOAD"] = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

    try:
        from flask_compress import Compress

        Compress(app)
    except ModuleNotFoundError:
        pass

    init_db()
    sync_students_with_courses()
    _ensure_activity_log_file()
    ensure_feedback_file()

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)

    for route in ALIAS_ROUTES:
        app.add_url_rule(
            route["rule"],
            endpoint=route["endpoint"],
            view_func=app.view_functions[route["target"]],
            methods=route["methods"],
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        if isinstance(exc, HTTPException):
            return exc

        app.logger.exception("Unhandled application error", exc_info=exc)
        return render_template("error.html", message="An unexpected error occurred. Please try again."), 500

    app.register_error_handler(404, not_found)
    return app
