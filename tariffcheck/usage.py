"""Summaries of a household's usage, shown next to the comparison."""

from collections import defaultdict
from decimal import Decimal

from tariffcheck.tariffs import Reading, Window


def _require_readings(readings: list[Reading]) -> None:
    if not readings:
        raise ValueError("No readings to summarise")


def days_covered(readings: list[Reading]) -> int:
    """How many different days the readings cover."""
    _require_readings(readings)
    return len({r.timestamp.date() for r in readings})


def average_daily_kwh(readings: list[Reading]) -> Decimal:
    """Total kWh divided by the number of days."""
    total = sum((r.kwh for r in readings), Decimal(0))
    return total / days_covered(readings)


def hourly_profile(readings: list[Reading]) -> list[Decimal]:
    """Average kWh used in each hour of the day (24 values, midnight first)."""
    days = days_covered(readings)
    totals: dict[int, Decimal] = defaultdict(Decimal)
    for r in readings:
        totals[r.timestamp.hour] += r.kwh
    return [totals[hour] / days for hour in range(24)]


def share_in_window(readings: list[Reading], window: Window) -> Decimal:
    """Fraction (0 to 1) of all kWh used inside a time window, e.g. the peak."""
    _require_readings(readings)
    total = sum((r.kwh for r in readings), Decimal(0))
    if total == 0:
        return Decimal(0)
    inside = sum(
        (r.kwh for r in readings if window.contains(r.timestamp.time())), Decimal(0)
    )
    return inside / total
