from flask import Flask

from database.db import init_db

from classroom_app.blueprints.api import bp as api_bp
from classroom_app.blueprints.auth import bp as auth_bp
from classroom_app.blueprints.pages import ALIAS_ROUTES, bp as pages_bp
from classroom_app.config import SECRET_KEY
from classroom_app.legacy import not_found
from classroom_app.services.data import _ensure_activity_log_file, sync_students_with_courses


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = SECRET_KEY

    init_db()
    sync_students_with_courses()
    _ensure_activity_log_file()

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

    app.register_error_handler(404, not_found)
    return app
