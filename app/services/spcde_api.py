"""Integration helpers for the Korean Special Day public API (Spcde)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Iterable
from xml.etree import ElementTree

import requests

LOGGER = logging.getLogger(__name__)

_BASE_URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService"
_ENDPOINTS = {
    "anniversary": "getAnniversaryInfo",
    "rest": "getRestDeInfo",
    "holiday": "getHoliDeInfo",
    "divisions": "get24DivisionsInfo",
    "sundry": "getSundryDayInfo",
}


@dataclass
class SpecialDay:
    """Normalized special-day information returned from the public API."""

    name: str
    occurred_on: date
    category: str
    raw: dict[str, str]


class SpcdeServiceError(RuntimeError):
    """Raised when the Spcde API returns an error response."""


def _parse_locdate(value: str | None) -> date | None:
    if not value or len(value) != 8:
        return None
    try:
        year = int(value[0:4])
        month = int(value[4:6])
        day = int(value[6:8])
    except ValueError:  # pragma: no cover - defensive branch
        return None
    return date(year, month, day)


def _extract_items(xml_content: bytes) -> Iterable[dict[str, str]]:
    """Yield raw item dictionaries from the API XML payload."""

    root = ElementTree.fromstring(xml_content)
    for item in root.findall(".//item"):
        yield {child.tag: (child.text or "").strip() for child in item}


def fetch_special_days(
    category: str,
    service_key: str,
    *,
    year: int,
    month: int,
    page: int = 1,
    rows: int = 100,
    timeout: float = 10,
    **extra_params: str,
) -> list[SpecialDay]:
    """Fetch normalized special-day information from the requested category.

    Parameters
    ----------
    category:
        One of ``anniversary``, ``rest``, ``holiday``, ``divisions``, ``sundry``.
    service_key:
        Open API service key issued by data.go.kr.
    year / month:
        Target Gregorian year and month.
    page / rows:
        Pagination controls for the API.
    timeout:
        Timeout in seconds for the HTTP request.
    extra_params:
        Additional query string parameters passed verbatim to the API.
    """

    endpoint = _ENDPOINTS.get(category)
    if not endpoint:
        raise ValueError(f"Unknown category '{category}'.")

    params: dict[str, str | int] = {
        "serviceKey": service_key,
        "pageNo": page,
        "numOfRows": rows,
        "solYear": f"{year:04d}",
        "solMonth": f"{month:02d}",
    }
    params.update(extra_params)

    response = requests.get(f"{_BASE_URL}/{endpoint}", params=params, timeout=timeout)
    if response.status_code != 200:
        raise SpcdeServiceError(
            f"Spcde API error {response.status_code}: {response.text[:200]}"
        )

    items: list[SpecialDay] = []
    for raw in _extract_items(response.content):
        locdate = _parse_locdate(raw.get("locdate"))
        if not locdate:
            LOGGER.debug("Skipping item without valid locdate: %s", raw)
            continue
        name = raw.get("dateName") or raw.get("anniversary") or raw.get("solarTerm")
        if not name:
            LOGGER.debug("Skipping item without recognizable name: %s", raw)
            continue
        items.append(SpecialDay(name=name, occurred_on=locdate, category=category, raw=raw))
    return items


def merge_label(existing: str | None, new_label: str) -> str:
    """Merge a label string ensuring no duplicates."""

    if not existing:
        return new_label
    parts = {part.strip() for part in existing.split("/") if part.strip()}
    parts.add(new_label)
    return " / ".join(sorted(parts))


def merge_source(existing: str | None, new_source: str) -> str:
    """Append a new source tag to the stored ``source`` column."""

    if not existing:
        return new_source
    parts = {part.strip() for part in existing.split(";") if part.strip()}
    parts.add(new_source)
    return ";".join(sorted(parts))
