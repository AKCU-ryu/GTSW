"""Route handlers for the group expense tracker."""
from __future__ import annotations

from datetime import date
import json
from typing import Iterable

from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from . import db
from .models import EntryShare, Holiday, LedgerEntry, Member, ReceiptExtractionLog
from .services.calendar import build_month_matrix
from .services.receipt_ai import extract_receipt_information
from .services.summary import (
    calculate_member_balances,
    calculate_monthly_totals,
    split_evenly_among_members,
)

bp = Blueprint("main", __name__)


@bp.app_context_processor
def inject_members() -> dict[str, Iterable[Member]]:
    """Inject member list into templates for side index rendering."""
    return {"members": Member.query.order_by(Member.name).all()}


@bp.route("/")
def dashboard() -> str:
    """Render the treasurer dashboard with summaries and calendar."""
    today = date.today()
    selected_month = request.args.get("month", type=int, default=today.month)
    selected_year = request.args.get("year", type=int, default=today.year)

    month_entries = LedgerEntry.query.filter(
        db.extract("year", LedgerEntry.occurred_on) == selected_year,
        db.extract("month", LedgerEntry.occurred_on) == selected_month,
    ).all()

    incomes = [entry for entry in month_entries if entry.entry_type == "income"]
    expenses = [entry for entry in month_entries if entry.entry_type == "expense"]

    monthly_totals = calculate_monthly_totals(month_entries)
    member_balances = calculate_member_balances(selected_year, selected_month)

    month_matrix = build_month_matrix(selected_year, selected_month, month_entries)
    holidays = {holiday.observed_on: holiday for holiday in Holiday.query.all()}

    return render_template(
        "index.html",
        month=selected_month,
        year=selected_year,
        incomes=incomes,
        expenses=expenses,
        monthly_totals=monthly_totals,
        member_balances=member_balances,
        month_matrix=month_matrix,
        holidays=holidays,
        date=date,
    )


@bp.route("/members/<int:member_id>")
def member_detail(member_id: int) -> str:
    """Show a member specific ledger page."""
    member = Member.query.get_or_404(member_id)
    entries = (
        LedgerEntry.query.filter_by(member_id=member.id)
        .order_by(LedgerEntry.occurred_on.desc())
        .all()
    )
    return render_template("member.html", member=member, entries=entries)


@bp.route("/members", methods=["POST"])
def add_member() -> Response:
    """Create a new member.

    The name field is mandatory while nickname and email are optional. When an email
    address is present we display a success flash message indicating that the invite
    would be sent. The actual e-mail integration is mocked to keep the demo
    self-contained.
    """
    name = request.form.get("name", "").strip()
    nickname = request.form.get("nickname", "").strip() or None
    email = request.form.get("email", "").strip() or None
    is_admin = request.form.get("is_admin") == "on"

    if not name:
        flash("멤버 이름은 필수입니다.", "error")
        return redirect(request.referrer or url_for("main.dashboard"))

    member = Member(name=name, nickname=nickname, email=email, is_admin=is_admin)
    db.session.add(member)
    db.session.commit()

    if email:
        flash(f"{name}님에게 초대장이 이메일({email})로 발송됩니다.", "info")
    flash(f"새 멤버 {member.display_name()}가 추가되었습니다.", "success")
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/members/<int:member_id>/toggle", methods=["POST"])
def toggle_member(member_id: int) -> Response:
    """Toggle the activation state of a member (lock/unlock)."""
    member = Member.query.get_or_404(member_id)
    member.is_active = not member.is_active
    db.session.commit()
    flash(
        f"{member.display_name()} 상태가 {'활성화' if member.is_active else '잠금'}으로 변경되었습니다.",
        "info",
    )
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/ledger", methods=["POST"])
def create_entry() -> Response:
    """Create an income or expense entry with optional even split."""
    entry_type = request.form.get("entry_type", "expense")
    amount = request.form.get("amount", type=float)
    if amount is None or amount < 0:
        flash("금액을 올바르게 입력해주세요.", "error")
        return redirect(request.referrer or url_for("main.dashboard"))

    member_id = request.form.get("member_id", type=int)
    created_by_id = request.form.get("created_by_id", type=int)
    occurred_on = request.form.get("occurred_on") or date.today().isoformat()
    description = request.form.get("description") or None
    category = request.form.get("category") or "기타"
    split_evenly = request.form.get("split_evenly") == "on"
    selected_member_ids = [
        int(member_id)
        for member_id in request.form.getlist("split_members")
        if member_id.isdigit()
    ]

    entry = LedgerEntry(
        entry_type=entry_type,
        amount=amount,
        member_id=member_id,
        created_by_id=created_by_id,
        occurred_on=date.fromisoformat(occurred_on),
        description=description,
        category=category,
        split_evenly=split_evenly,
    )

    db.session.add(entry)
    db.session.flush()

    if split_evenly:
        members = Member.query.filter(Member.id.in_(selected_member_ids)).all()
        if not members:
            members = Member.query.filter_by(is_active=True).all()
        for share in split_evenly_among_members(entry.amount, members):
            db.session.add(
                EntryShare(entry_id=entry.id, member_id=share.member.id, amount=share.amount)
            )

    db.session.commit()
    flash("새로운 가계부 내역이 추가되었습니다.", "success")
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/api/holidays")
def holiday_feed() -> Response:
    """Return holiday data in JSON for the calendar widget."""
    items = [
        {
            "name": holiday.name,
            "date": holiday.observed_on.isoformat(),
            "source": holiday.source,
        }
        for holiday in Holiday.query.order_by(Holiday.observed_on).all()
    ]
    return jsonify(items)


@bp.route("/api/receipt/analyze", methods=["POST"])
def analyze_receipt() -> Response:
    """Endpoint that simulates machine learning based receipt extraction.

    In a production grade application this route would delegate to an OCR and machine
    learning pipeline. Here we accept either plain text or JSON payloads to keep the
    example self contained while still demonstrating the integration points.
    """
    if request.content_type == "application/json":
        payload = request.get_json(force=True)
        content = payload.get("content", "")
        filename = payload.get("filename")
    else:
        uploaded_file = request.files.get("file")
        content = uploaded_file.read().decode("utf-8", errors="ignore") if uploaded_file else ""
        filename = uploaded_file.filename if uploaded_file else None

    extraction = extract_receipt_information(content)

    log = ReceiptExtractionLog(
        uploaded_filename=filename,
        detected_total=extraction.total,
        detected_store=extraction.store_name,
        detected_card=extraction.card,
        raw_payload=json.dumps({"content": content[:500]}),
        status="success" if extraction.total else "needs_review",
    )
    db.session.add(log)
    db.session.commit()

    response_payload = {
        "total": extraction.total,
        "store": extraction.store_name,
        "card": extraction.card,
        "timestamp": extraction.timestamp.isoformat(),
        "items": extraction.items,
    }
    return jsonify(response_payload)


def register_blueprints(app):
    """Convenience helper for unit tests to register blueprints."""
    app.register_blueprint(bp)


# Register blueprint when module is imported.
register_blueprints = register_blueprints  # appease linters for unused function
