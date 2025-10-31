# app/services/receipt_ai.py
# -*- coding: utf-8 -*-
"""Lightweight helpers simulating machine learning receipt extraction."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class ReceiptExtraction:
    """Structured information returned by :func:`extract_receipt_information`."""
    total: float | None
    store_name: str | None
    card: str | None
    timestamp: datetime
    items: List[dict[str, str | float]] = field(default_factory=list)

_STORE_PATTERN = re.compile(r"(?:매장|지점|STORE)\s*[:\-]?\s*(?P<store>[\w가-힣 ]+)")
_TOTAL_PATTERN = re.compile(r"(?:합계|총액|TOTAL)\s*[:\-]?\s*(?:₩|KRW|원)?\s*(?P<total>[\d,]+)")
_CARD_PATTERN  = re.compile(r"(?:카드|CARD)\s*[:\-]?\s*(?P<card>[*\dxX\-]{4,19})")
_ITEM_PATTERN  = re.compile(r"(?P<name>[가-힣A-Za-z0-9 ]+)\s+(?:₩|KRW|원)?\s*(?P<amount>[\d,]+)")
_DATE_PATTERN  = re.compile(r"(?P<year>20\d{2})[./-](?P<month>\d{1,2})[./-](?P<day>\d{1,2})")

def _parse_amount(value: str | None) -> float | None:
    if not value:
        return None
    try: return float(value.replace(",", ""))
    except ValueError: return None

def extract_receipt_information(raw_text: str) -> ReceiptExtraction:
    """Extract structured information from ``raw_text`` using regex heuristics."""
    raw_text = raw_text or ""
    store_match = _STORE_PATTERN.search(raw_text)
    total_match = _TOTAL_PATTERN.search(raw_text)
    card_match  = _CARD_PATTERN.search(raw_text)
    date_match  = _DATE_PATTERN.search(raw_text)

    ts = datetime.now()
    if date_match:
        ts = datetime(int(date_match["year"]), int(date_match["month"]), int(date_match["day"]))

    items: List[dict[str, str | float]] = []
    for m in _ITEM_PATTERN.finditer(raw_text):
        name = (m.group("name") or "").strip()
        if name and name.upper() not in {"합계", "총액", "TOTAL"}:
            amt = _parse_amount(m.group("amount"))
            if amt is not None:
                items.append({"name": name, "amount": amt})

    return ReceiptExtraction(
        total=_parse_amount(total_match.group("total") if total_match else None),
        store_name=store_match.group("store").strip() if store_match else None,
        card=(card_match.group("card").strip() if card_match else None),
        timestamp=ts,
        items=items,
    )
