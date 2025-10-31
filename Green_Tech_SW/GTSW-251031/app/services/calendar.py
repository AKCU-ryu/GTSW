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
    day: int | None
    date: date | None
    entries: list[LedgerEntry]

def build_month_matrix(year: int, month: int, entries: Iterable[LedgerEntry]) -> list[list[CalendarCell]]:
    cal = calendar.Calendar(firstweekday=6)
    grouped = defaultdict(list)
    for entry in entries:
        if entry.occurred_on:
            grouped[entry.occurred_on].append(entry)

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
                        entries=sorted(grouped.get(day, []), key=lambda e: e.entry_type),
                    )
                )
        matrix.append(row)
    return matrix
