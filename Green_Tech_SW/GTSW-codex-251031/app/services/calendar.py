# app/services/calendar.py
# -*- coding: utf-8 -*-
"""Utility helpers to build a month matrix for the calendar widget."""
from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from ..models import LedgerEntry

@dataclass
class CalendarCell:
    """Represents a single day cell in the calendar view."""
    day: int | None
    date: date | None
    entries: list[LedgerEntry]

def build_month_matrix(year: int, month: int, entries: Iterable[LedgerEntry]) -> list[list[CalendarCell]]:
    """Return a matrix representing the requested month (Sunday-start)."""
    cal = calendar.Calendar(firstweekday=6)  # Sunday
    grouped: defaultdict[date, list[LedgerEntry]] = defaultdict(list)
    for entry in entries:
        if entry.occurred_on:
            grouped[entry.occurred_on].append(entry)

    # income 먼저 → expense 나중(가독성)
    ORDER = {"income": 0, "expense": 1}

    matrix: list[list[CalendarCell]] = []
    for week in cal.monthdatescalendar(year, month):
        row: list[CalendarCell] = []
        for day in week:
            if day.month != month:
                row.append(CalendarCell(day=None, date=None, entries=[]))
            else:
                row.append(
                    CalendarCell(
                        day=day.day,
                        date=day,
                        entries=sorted(
                            grouped.get(day, []),
                            key=lambda e: (ORDER.get(e.entry_type, 99), getattr(e, "created_at", None) or 0),
                        ),
                    )
                )
        matrix.append(row)
    return matrix
