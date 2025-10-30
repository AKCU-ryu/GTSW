"""Entry point for running the development server and utilities."""
from __future__ import annotations

from datetime import date

from flask.cli import with_appcontext
import click

from app import create_app, db
from app.models import Holiday, Member

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


if __name__ == "__main__":
    app.run(debug=True)
