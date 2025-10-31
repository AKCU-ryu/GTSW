"""Application factory for the group expense tracker web app."""
from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Global SQLAlchemy instance used across modules
# The instance is initialized in :func:`create_app` to support the application factory
# pattern which is friendly for testing and flexible configuration.
db = SQLAlchemy()


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Parameters
    ----------
    test_config:
        Optional dictionary used to override configuration for tests.

    Returns
    -------
    flask.Flask
        The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Default configuration. In production the ``SECRET_KEY`` should be set via
    # environment variable. We fall back to a development friendly value.
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///finance.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    # Ensure the instance path exists (where the SQLite DB will live).
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    # Import routes so the view functions are registered and blueprints attached.
    from .routes import bp as main_bp  # noqa: WPS433
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
