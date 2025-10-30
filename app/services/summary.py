"""Summaries and helper calculations for the ledger."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import extract

from .. import db
from ..models import LedgerEntry, Member


@dataclass
class ShareResult:
    """Helper structure describing how an entry is split."""

    member: Member
    amount: float


def calculate_monthly_totals(entries: Iterable[LedgerEntry]) -> dict[str, float]:
    """Return monthly totals for income and expense."""
    totals = defaultdict(float)
    for entry in entries:
        totals[entry.entry_type] += entry.amount
    totals.setdefault("income", 0.0)
    totals.setdefault("expense", 0.0)
    totals["net"] = totals["income"] - totals["expense"]
    return totals


def calculate_member_balances(year: int, month: int) -> list[dict[str, object]]:
    """Return per-member balance for the requested period."""
    entries = (
        db.session.query(LedgerEntry)
        .filter(extract("year", LedgerEntry.occurred_on) == year)
        .filter(extract("month", LedgerEntry.occurred_on) == month)
        .all()
    )

    expenses_by_member = defaultdict(float)
    incomes_by_member = defaultdict(float)

    for entry in entries:
        if entry.entry_type == "income" and entry.member_id:
            incomes_by_member[entry.member_id] += entry.amount
        if entry.entry_type == "expense":
            if entry.shares:
                for share in entry.shares:
                    expenses_by_member[share.member_id] += share.amount
            elif entry.member_id:
                expenses_by_member[entry.member_id] += entry.amount

    members = Member.query.all()
    balances: list[dict[str, object]] = []
    for member in members:
        balance = incomes_by_member[member.id] - expenses_by_member[member.id]
        balances.append(
            {
                "member": member,
                "income": incomes_by_member[member.id],
                "expense": expenses_by_member[member.id],
                "balance": balance,
            }
        )
    return balances


def split_evenly_among_members(amount: float, members: Iterable[Member]) -> list[ShareResult]:
    """Split ``amount`` evenly among ``members`` rounding to two decimals."""
    members = list(members)
    if not members:
        return []
    share = round(amount / len(members), 2)
    results = [ShareResult(member=member, amount=share) for member in members]
    # Adjust the final member to account for rounding differences.
    difference = round(amount - share * len(members), 2)
    if results:
        results[-1].amount += difference
    return results
