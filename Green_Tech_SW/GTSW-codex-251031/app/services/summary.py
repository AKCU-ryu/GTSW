# app/services/summary.py
# -*- coding: utf-8 -*-
"""Summaries and helper calculations for the ledger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Dict, List
from collections import defaultdict

from sqlalchemy import extract, func

from .. import db
from ..models import LedgerEntry, Member, EntryShare

@dataclass
class ShareResult:
    """Helper structure describing how an entry is split."""
    member: Member
    amount: float

def _to_float(x) -> float:
    if x is None: return 0.0
    try: return float(x)
    except Exception: return 0.0

def calculate_monthly_totals(entries: Iterable[LedgerEntry]) -> dict[str, float]:
    income = 0.0; expense = 0.0
    for e in entries:
        if e.entry_type == "income":  income += _to_float(e.amount)
        elif e.entry_type == "expense": expense += _to_float(e.amount)
    return {"income": income, "expense": expense, "net": income - expense}

def calculate_member_balances(year: int, month: int) -> list[dict[str, object]]:
    """Per-member (income - expense) for the month."""
    # 1) income per member
    income_rows = (
        db.session.query(LedgerEntry.member_id, func.coalesce(func.sum(LedgerEntry.amount), 0))
        .filter(
            LedgerEntry.entry_type == "income",
            extract("year", LedgerEntry.occurred_on) == year,
            extract("month", LedgerEntry.occurred_on) == month,
        )
        .group_by(LedgerEntry.member_id).all()
    )
    income_map: Dict[int, float] = {(mid or 0): _to_float(total) for mid, total in income_rows}

    # 2-a) shared expenses (EntryShare)
    shared_rows = (
        db.session.query(EntryShare.member_id, func.coalesce(func.sum(EntryShare.amount), 0))
        .join(LedgerEntry, LedgerEntry.id == EntryShare.entry_id)
        .filter(
            LedgerEntry.entry_type == "expense",
            extract("year", LedgerEntry.occurred_on) == year,
            extract("month", LedgerEntry.occurred_on) == month,
        )
        .group_by(EntryShare.member_id).all()
    )
    shared_map: Dict[int, float] = {mid: _to_float(total) for mid, total in shared_rows}

    # 2-b) direct expenses (not split)
    direct_rows = (
        db.session.query(LedgerEntry.member_id, func.coalesce(func.sum(LedgerEntry.amount), 0))
        .filter(
            LedgerEntry.entry_type == "expense",
            LedgerEntry.split_evenly == False,  # noqa: E712
            LedgerEntry.member_id.isnot(None),
            extract("year", LedgerEntry.occurred_on) == year,
            extract("month", LedgerEntry.occurred_on) == month,
        )
        .group_by(LedgerEntry.member_id).all()
    )
    direct_map: Dict[int, float] = {mid: _to_float(total) for mid, total in direct_rows}

    expense_map: Dict[int, float] = defaultdict(float)
    for mid, v in shared_map.items():
        if mid is not None: expense_map[mid] += v
    for mid, v in direct_map.items():
        if mid is not None: expense_map[mid] += v

    members: List[Member] = Member.query.order_by(Member.name.asc()).all()
    results: list[dict[str, object]] = []
    for m in members:
        inc = income_map.get(m.id, 0.0)
        exp = expense_map.get(m.id, 0.0)
        results.append({"member": m, "income": inc, "expense": exp, "balance": round(inc - exp, 2)})
    return results

def split_evenly_among_members(amount: float, members: Iterable[Member]) -> list[ShareResult]:
    """Even split with 2-decimal rounding; last member gets diff adjustment."""
    members = list(members)
    if not members: return []
    total = _to_float(amount); n = len(members)
    each = round(total / n, 2)
    results = [ShareResult(member=m, amount=each) for m in members]
    diff = round(total - each * n, 2)
    if results: results[-1].amount = round(results[-1].amount + diff, 2)
    return results
