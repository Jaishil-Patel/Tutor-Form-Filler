"""Data model for a tutoring session plus the hours math/formatting rules."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


_DATE_ISO = "%Y-%m-%d"
_DATE_DISPLAY = "%d/%m/%Y"
_TIME_FMT = "%H:%M"


def parse_time(value: str) -> datetime:
    """Parse an 'HH:MM' 24-hour string. Raises ValueError if malformed."""
    return datetime.strptime(value.strip(), _TIME_FMT)


def computed_hours(start: str, end: str) -> float:
    """Decimal hours between two 'HH:MM' times (end - start).

    14:00 -> 17:00 == 3.0, 10:00 -> 11:30 == 1.5.
    Returns 0.0 if either time is blank/invalid.
    """
    try:
        t0 = parse_time(start)
        t1 = parse_time(end)
    except (ValueError, AttributeError):
        return 0.0
    minutes = (t1 - t0).total_seconds() / 60.0
    if minutes < 0:
        # crossing midnight is not expected for tutoring; treat as same-day span
        minutes += 24 * 60
    return round(minutes / 60.0, 2)


def format_hours(value: float) -> str:
    """Trim trailing '.0' so 3.0 -> '3' but 1.5 -> '1.5'."""
    if value is None:
        return ""
    rounded = round(float(value), 2)
    if rounded == int(rounded):
        return str(int(rounded))
    # strip trailing zeros e.g. 1.50 -> 1.5
    return ("%g" % rounded)


def iso_to_display(iso_date: str) -> str:
    """'2026-03-02' -> '02/03/2026'."""
    return datetime.strptime(iso_date, _DATE_ISO).strftime(_DATE_DISPLAY)


def display_to_iso(display_date: str) -> str:
    """'02/03/2026' -> '2026-03-02'. Raises ValueError if malformed."""
    return datetime.strptime(display_date.strip(), _DATE_DISPLAY).strftime(_DATE_ISO)


@dataclass
class Session:
    """One recorded tutoring activity (one row of the main table)."""

    date: str  # ISO 'YYYY-MM-DD'
    course_code: str  # e.g. 'COMS1015A'
    activity: str  # e.g. 'Tutoring'
    time_started: str  # 'HH:MM'
    time_ended: str  # 'HH:MM'
    total_hours_override: Optional[float] = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    # --- derived values -------------------------------------------------
    def effective_hours_value(self) -> float:
        if self.total_hours_override is not None:
            return float(self.total_hours_override)
        return computed_hours(self.time_started, self.time_ended)

    def effective_hours(self) -> str:
        return format_hours(self.effective_hours_value())

    def display_date(self) -> str:
        try:
            return iso_to_display(self.date)
        except ValueError:
            return self.date

    def display_time_started(self) -> str:
        return self.time_started.replace(":", "h")

    def display_time_ended(self) -> str:
        return self.time_ended.replace(":", "h")

    @property
    def year(self) -> int:
        return datetime.strptime(self.date, _DATE_ISO).year

    @property
    def month(self) -> int:
        return datetime.strptime(self.date, _DATE_ISO).month

    # --- (de)serialization ---------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        kwargs = dict(
            date=data["date"],
            course_code=data.get("course_code", ""),
            activity=data.get("activity", ""),
            time_started=data.get("time_started", ""),
            time_ended=data.get("time_ended", ""),
            total_hours_override=data.get("total_hours_override"),
        )
        if data.get("id"):
            kwargs["id"] = data["id"]
        return cls(**kwargs)


def sessions_for_month(sessions: list["Session"], year: int, month: int) -> list["Session"]:
    """Return sessions in the given year+month, sorted by date then start time."""
    subset = [s for s in sessions if s.year == year and s.month == month]
    return sorted(subset, key=lambda s: (s.date, s.time_started))
