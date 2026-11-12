from datetime import datetime, time
from decimal import Decimal

import pytest

from tariffcheck.tariffs import Reading, Window
from tariffcheck.usage import (
    average_daily_kwh,
    days_covered,
    hourly_profile,
    share_in_window,
)

PEAK = Window("peak", time(16, 0), time(21, 0), Decimal("35.86"))


def reading(day: int, hhmm: str, kwh: str) -> Reading:
    hour, minute = map(int, hhmm.split(":"))
    return Reading(datetime(2026, 10, day, hour, minute), Decimal(kwh))


# Day 1: 2 kWh at 08:00, 3 kWh at 18:00. Day 2: 1 kWh at 08:30, 4 kWh at 18:30.
TWO_DAYS = [
    reading(1, "08:00", "2"),
    reading(1, "18:00", "3"),
    reading(2, "08:30", "1"),
    reading(2, "18:30", "4"),
]


def test_days_covered():
    assert days_covered(TWO_DAYS) == 2


def test_average_daily_kwh():
    assert average_daily_kwh(TWO_DAYS) == Decimal(5)  # 10 kWh over 2 days


def test_hourly_profile_averages_each_hour_over_the_days():
    profile = hourly_profile(TWO_DAYS)
    assert len(profile) == 24
    assert profile[8] == Decimal("1.5")  # (2 + 1) / 2 days
    assert profile[18] == Decimal("3.5")  # (3 + 4) / 2 days
    assert profile[0] == Decimal(0)


def test_share_in_peak_window():
    assert share_in_window(TWO_DAYS, PEAK) == Decimal("0.7")  # 7 of 10 kWh


def test_share_is_zero_when_nothing_was_used():
    assert share_in_window([reading(1, "18:00", "0")], PEAK) == Decimal(0)


@pytest.mark.parametrize("summary", [days_covered, average_daily_kwh, hourly_profile])
def test_no_readings_is_an_error(summary):
    with pytest.raises(ValueError, match="No readings"):
        summary([])


def test_share_with_no_readings_is_an_error():
    with pytest.raises(ValueError, match="No readings"):
        share_in_window([], PEAK)
