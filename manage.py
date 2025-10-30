"""Entry point for running the development server and utilities."""
from __future__ import annotations

import os
from datetime import date

from flask.cli import with_appcontext
import click

from app import create_app, db
from app.models import Holiday, Member
from app.services.receipt_ml import ReceiptModelNotReady, train_model
from app.services.spcde_api import fetch_special_days, merge_label, merge_source

app = create_app()


@app.cli.command("init-data")
@with_appcontext
def init_data() -> None:
    """Seed the database with an initial treasurer and sample holidays."""
    if not Member.query.filter_by(is_admin=True).first():
        treasurer = Member(name="총무", nickname="Treasurer", email="finance@example.com", is_admin=True)
        db.session.add(treasurer)
    holidays = [
        ("신정", date(2024, 1, 1)),
        ("삼일절", date(2024, 3, 1)),
        ("광복절", date(2024, 8, 15)),
    ]
    for name, date_value in holidays:
        if not Holiday.query.filter_by(observed_on=date_value).first():
            db.session.add(Holiday(name=name, observed_on=date_value))
    db.session.commit()
    click.echo("기본 데이터가 준비되었습니다.")


@app.cli.command("sync-spcde")
@click.option("--year", type=int, default=date.today().year, show_default=True)
@click.option("--month", type=int, default=date.today().month, show_default=True)
@click.option(
    "--category",
    type=click.Choice(["anniversary", "rest", "holiday", "divisions", "sundry"], case_sensitive=False),
    multiple=True,
    help="조회할 분류를 선택합니다. 여러 번 지정할 수 있습니다.",
)
@with_appcontext
def sync_spcde(year: int, month: int, category: tuple[str, ...]) -> None:
    """Fetch anniversaries/holidays from the public API and store them locally."""

    service_key = os.getenv("SPCDE_SERVICE_KEY")
    if not service_key:
        raise click.UsageError("환경 변수 SPCDE_SERVICE_KEY에 서비스 키를 설정해주세요.")

    categories = category or ("anniversary", "holiday", "rest")
    inserted = 0
    updated = 0
    for selected in categories:
        try:
            items = fetch_special_days(selected.lower(), service_key, year=year, month=month)
        except Exception as exc:  # pragma: no cover - API/network failure
            raise click.ClickException(f"{selected} 조회 중 오류가 발생했습니다: {exc}") from exc

        for item in items:
            record = Holiday.query.filter_by(observed_on=item.occurred_on).first()
            if record:
                merged = merge_label(record.name, item.name)
                if merged != (record.name or ""):
                    record.name = merged
                    updated += 1
                record.source = merge_source(record.source, f"spcde:{item.category}")
            else:
                record = Holiday(
                    name=item.name,
                    observed_on=item.occurred_on,
                    source=f"spcde:{item.category}",
                )
                db.session.add(record)
                inserted += 1

    db.session.commit()
    click.echo(
        f"Spcde 동기화 완료 - 새 항목 {inserted}건, 업데이트 {updated}건 (대상 {categories})."
    )


@app.cli.command("train-receipt-model")
@click.option("--epochs", type=int, default=20, show_default=True)
@with_appcontext
def train_receipt_model(epochs: int) -> None:
    """Train the TensorFlow-based receipt classifier."""

    try:
        model_path, class_indices = train_model(epochs=epochs)
    except ReceiptModelNotReady as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"모델이 {model_path}에 저장되었습니다. 클래스: {list(class_indices.keys())}")


if __name__ == "__main__":
    app.run(debug=True)
