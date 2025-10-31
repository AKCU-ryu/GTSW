# app/routes.py
# -*- coding: utf-8 -*-
"""Route handlers for the group expense tracker."""
from __future__ import annotations

from datetime import date
import json
from typing import Iterable, Tuple

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


def _resolve_month_and_year() -> Tuple[int, int]:
    today = date.today()
    selected_month = request.args.get("month", type=int, default=today.month)
    selected_year = request.args.get("year", type=int, default=today.year)
    return selected_year, selected_month


@bp.route("/")
def landing() -> str:
    """Cover page with login and registration prompts."""
    return render_template("main.html")


@bp.route("/admin")
def admin_base() -> str:
    """Treasurer overview page with quick stats."""
    selected_year, selected_month = _resolve_month_and_year()
    month_query = (
        LedgerEntry.query.filter(
            db.extract("year", LedgerEntry.occurred_on) == selected_year,
            db.extract("month", LedgerEntry.occurred_on) == selected_month,
        ).order_by(LedgerEntry.occurred_on.desc())
    )

    month_entries = month_query.all()
    latest_entries = month_entries[:6]
    monthly_totals = calculate_monthly_totals(month_entries)
    member_balances = calculate_member_balances(selected_year, selected_month)

    # base.html이 레이아웃이라면 admin.html 템플릿을 별도 사용해도 됨
    return render_template(
        "base.html",
        monthly_totals=monthly_totals,
        member_balances=member_balances,
        latest_entries=latest_entries,
        date=date,
    )


@bp.route("/main/index")
def main_index() -> str:
    """Render the main calendar index with all ledger data."""
    selected_year, selected_month = _resolve_month_and_year()
    month_entries = LedgerEntry.query.filter(
        db.extract("year", LedgerEntry.occurred_on) == selected_year,
        db.extract("month", LedgerEntry.occurred_on) == selected_month,
    ).all()

    incomes = [e for e in month_entries if e.entry_type == "income"]
    expenses = [e for e in month_entries if e.entry_type == "expense"]

    monthly_totals = calculate_monthly_totals(month_entries)
    member_balances = calculate_member_balances(selected_year, selected_month)

    month_matrix = build_month_matrix(selected_year, selected_month, month_entries)
    holidays = {h.observed_on: h for h in Holiday.query.all()}

    return render_template(
        "main_index.html",
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


@bp.route("/members/overview")
def member_overview() -> str:
    """Overview listing for members with quick access buttons."""
    return render_template("member_overview.html")


@bp.route("/members/<int:member_id>")
def member_detail(member_id: int) -> str:
    """Show a member specific ledger page."""
    member = Member.query.get_or_404(member_id)
    entries = (
        LedgerEntry.query.filter_by(member_id=member.id)
        .order_by(LedgerEntry.occurred_on.desc())
        .all()
    )
    return render_template("member.html", member=member, entries=entries, date=date)


@bp.route("/members/<int:member_id>/index")
def member_index(member_id: int) -> str:
    """Calendar style index for a single member."""
    selected_year, selected_month = _resolve_month_and_year()
    member = Member.query.get_or_404(member_id)
    month_entries = (
        LedgerEntry.query.filter_by(member_id=member.id)
        .filter(db.extract("year", LedgerEntry.occurred_on) == selected_year)
        .filter(db.extract("month", LedgerEntry.occurred_on) == selected_month)
        .all()
    )
    month_matrix = build_month_matrix(selected_year, selected_month, month_entries)
    holidays = {h.observed_on: h for h in Holiday.query.all()}

    return render_template(
        "member_index.html",
        member=member,
        month=selected_month,
        year=selected_year,
        month_matrix=month_matrix,
        holidays=holidays,
        date=date,
    )


@bp.route("/members", methods=["POST"])
def add_member() -> Response:
    """Create a new member."""
    name = (request.form.get("name") or "").strip()
    nickname = (request.form.get("nickname") or "").strip() or None
    email = (request.form.get("email") or "").strip() or None
    is_admin = request.form.get("is_admin") == "on"

    if not name:
        flash("멤버 이름은 필수입니다.", "error")
        return redirect(request.referrer or url_for("main.main_index"))

    member = Member(name=name, nickname=nickname, email=email, is_admin=is_admin)
    db.session.add(member)
    db.session.commit()

    if email:
        flash(f"{name}님에게 초대장이 이메일({email})로 발송됩니다.", "info")
    flash(f"새 멤버 {member.display_name()}가 추가되었습니다.", "success")
    return redirect(request.referrer or url_for("main.member_overview"))


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
    return redirect(request.referrer or url_for("main.member_overview"))


@bp.route("/ledger", methods=["POST"])
def create_entry() -> Response:
    """Create an income or expense entry with optional even split."""
    entry_type = request.form.get("entry_type", "expense")
    amount = request.form.get("amount", type=float)

    if amount is None or amount < 0:
        flash("금액을 올바르게 입력해주세요.", "error")
        return redirect(request.referrer or url_for("main.main_index"))

    member_id = request.form.get("member_id", type=int)
    created_by_id = request.form.get("created_by_id", type=int)
    occurred_on_str = request.form.get("occurred_on") or date.today().isoformat()
    description = request.form.get("description") or None
    category = request.form.get("category") or "기타"
    split_evenly = request.form.get("split_evenly") == "on"
    selected_member_ids = [
        int(mid) for mid in request.form.getlist("split_members") if str(mid).isdigit()
    ]

    entry = LedgerEntry(
        entry_type=entry_type,
        amount=amount,
        member_id=member_id,
        created_by_id=created_by_id,
        occurred_on=date.fromisoformat(occurred_on_str),
        description=description,
        category=category,
        split_evenly=split_evenly,
    )

    db.session.add(entry)
    db.session.flush()  # entry.id 확보

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
    return redirect(request.referrer or url_for("main.main_index"))


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
    """Endpoint that simulates machine learning based receipt extraction."""
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        content = payload.get("content", "") or ""
        filename = payload.get("filename")
    else:
        uploaded_file = request.files.get("file")
        content = (
            uploaded_file.read().decode("utf-8", errors="ignore") if uploaded_file else ""
        )
        filename = uploaded_file.filename if uploaded_file else None

    extraction = extract_receipt_information(content or "")

    log = ReceiptExtractionLog(
        uploaded_filename=filename,
        detected_total=extraction.total,
        detected_store=extraction.store_name,
        detected_card=extraction.card,
        raw_payload=json.dumps({"content": (content or "")[:500]}),
        status="success" if extraction.total else "needs_review",
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(
        {
            "total": extraction.total,
            "store": extraction.store_name,
            "card": extraction.card,
            "timestamp": extraction.timestamp.isoformat(),
            "items": extraction.items,
            "log_id": log.id,
        }
    )


@bp.route("/api/receipt/<int:log_id>")
def receipt_log_detail(log_id: int) -> Response:
    """Expose stored receipt extraction results."""
    log = ReceiptExtractionLog.query.get_or_404(log_id)
    payload = json.loads(log.raw_payload) if log.raw_payload else None
    return jsonify(
        {
            "filename": log.uploaded_filename,
            "total": log.detected_total,
            "store": log.detected_store,
            "card": log.detected_card,
            "status": log.status,
            "processed_at": log.processed_at.isoformat(),
            "raw_payload": payload,
        }
    )
