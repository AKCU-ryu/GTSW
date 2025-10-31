# app/__init__.py
# -*- coding: utf-8 -*-
"""Application factory for the group expense tracker web app."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Global SQLAlchemy instance used across modules
db = SQLAlchemy()
migrate = Migrate()  # ✅ Alembic/Flask-Migrate 연결용

def create_app(test_config: Dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # 기본값(로컬 개발 친화): 환경변수 없을 때 사용
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///finance.db"),

        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # instance/config.py (비공개 설정) 있으면 덮어씀
    app.config.from_pyfile("config.py", silent=True)

    # 테스트가 지정되면 최종 덮어쓰기
    if test_config:
        app.config.update(test_config)

    # instance 폴더 보장 (예: SQLite 파일 위치)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)  # ✅ 마이그레이션 활성화

    # 선택: 외부 API 키를 config에도 노출하고 싶다면(필수 아님)
    # app.config["SPCDE_SERVICE_KEY"] = os.getenv("SPCDE_SERVICE_KEY")

    # 블루프린트 등록
    from .routes import bp as main_bp  # noqa: WPS433
    app.register_blueprint(main_bp)

    # ❌ 마이그레이션을 사용할 땐 create_all()을 호출하지 않습니다.
    # with app.app_context():
    #     db.create_all()

    return app
