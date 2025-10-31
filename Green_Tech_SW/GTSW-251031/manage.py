# manage.py
# -*- coding: utf-8 -*-
"""Entry point for running the development server and CLI utilities."""
from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv
load_dotenv()  # .env 자동 로드

import click
from flask.cli import with_appcontext

from app import create_app, db
from flask_migrate import Migrate

# Flask 앱 & Migrate 연결 (db 커맨드 등록의 핵심)
app = create_app()
migrate = Migrate(app, db)

# ─────────────────────────────
# CLI: 초기 데이터 시드
# ─────────────────────────────
@app.cli.command("init-data")
@with_appcontext
def init_data() -> None:
    """Seed the database with an initial treasurer and sample holidays."""
    from app.models import Holiday, Member  # 지연 import (모듈 의존성 최소화)

    if not Member.query.filter_by(is_admin=True).first():
        treasurer = Member(
            name="총무", nickname="Treasurer",
            email="finance@example.com", is_admin=True
        )
        db.session.add(treasurer)

    holidays = [
        ("신정", date(2024, 1, 1)),
        ("삼일절", date(2024, 3, 1)),
        ("광복절", date(2024, 8, 15)),
    ]
    for name, when in holidays:
        if not Holiday.query.filter_by(observed_on=when).first():
            db.session.add(Holiday(name=name, observed_on=when))

    db.session.commit()
    click.echo("✅ 기본 데이터가 준비되었습니다.")

# ─────────────────────────────
# CLI: 공공데이터포털 SPCDE 동기화
# ─────────────────────────────
@app.cli.command("sync-spcde")
@click.option("--year", type=int, default=date.today().year, show_default=True)
@click.option("--month", type=int, default=date.today().month, show_default=True)
@click.option(
    "--category",
    type=click.Choice(
        ["anniversary", "rest", "holiday", "divisions", "sundry"],
        case_sensitive=False,
    ),
    multiple=True,
    help="조회할 분류를 선택합니다. 여러 번 지정 가능.",
)
@with_appcontext
def sync_spcde(year: int, month: int, category: tuple[str, ...]) -> None:
    """Fetch anniversaries/holidays from the public API and store them locally."""
    # 지연 import (모듈이 없을 때도 manage.py import는 성공하도록)
    from app.models import Holiday
    try:
        from app.services.spcde_api import fetch_special_days, merge_label, merge_source
    except ImportError as exc:
        raise click.ClickException("spcde_api 모듈을 찾을 수 없습니다.") from exc

    service_key = os.getenv("SPCDE_SERVICE_KEY")
    if not service_key:
        raise click.UsageError("환경 변수 SPCDE_SERVICE_KEY에 서비스 키를 설정해주세요.")

    categories = category or ("anniversary", "holiday", "rest")
    inserted = 0
    updated = 0

    for selected in categories:
        try:
            items = fetch_special_days(selected.lower(), service_key, year=year, month=month)
        except Exception as exc:
            raise click.ClickException(f"{selected} 조회 중 오류: {exc}") from exc

        for item in items:
            record = Holiday.query.filter_by(observed_on=item.occurred_on).first()
            if record:
                merged = merge_label(record.name or "", item.name)
                if merged != (record.name or ""):
                    record.name = merged
                    updated += 1
                record.source = merge_source(record.source, f"spcde:{item.category}")
            else:
                db.session.add(
                    Holiday(
                        name=item.name,
                        observed_on=item.occurred_on,
                        source=f"spcde:{item.category}",
                    )
                )
                inserted += 1

    db.session.commit()
    click.echo(f"✅ Spcde 동기화 완료 - 새 {inserted}건, 업데이트 {updated}건 (대상 {categories}).")

# ─────────────────────────────
# CLI: 영수증 ML 모델 학습
# ─────────────────────────────
@app.cli.command("train-receipt-model")
@click.option("--epochs", type=int, default=20, show_default=True)
@with_appcontext
def train_receipt_model(epochs: int) -> None:
    """Train the TensorFlow-based receipt classifier."""
    try:
        # 지연 import (모듈 없으면 이 커맨드만 실패하고 나머지는 정상 동작)
        from app.services.receipt_ml import ReceiptModelNotReady, train_model  # type: ignore
    except ImportError as exc:
        raise click.ClickException("receipt_ml 모듈을 찾을 수 없습니다.") from exc

    try:
        model_path, class_indices = train_model(epochs=epochs)
    except ReceiptModelNotReady as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"✅ 모델 저장: {model_path} | 클래스: {list(class_indices.keys())}")

# ─────────────────────────────
# 개발 서버
# ─────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
