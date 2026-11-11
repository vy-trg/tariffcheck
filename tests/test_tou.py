from datetime import datetime, time
from decimal import Decimal

import pytest

from tariffcheck.tariffs import Reading, TOUPlan, Window, tou_bill

# Real plan from docs/design.md (NTR1154695MRE1), all week
NECTR_TOU = TOUPlan(
    "Nectr Power Perks TOU",
    (
        Window("peak", time(16, 0), time(21, 0), Decimal("35.86")),
        Window("off-peak", time(11, 0), time(16, 0), Decimal("14.42")),
        Window("shoulder", time(21, 0), time(11, 0), Decimal("20.75")),
    ),
    Decimal("140.17"),
)
SHOULDER = NECTR_TOU.windows[2]


def reading(day: int, hhmm: str, kwh: str) -> Reading:
    """A reading on `day` October 2026 at `hhmm`, e.g. reading(1, "18:00", "10")."""
    hour, minute = map(int, hhmm.split(":"))
    return Reading(datetime(2026, 10, day, hour, minute), Decimal(kwh))


# --- A window that crosses midnight (21:00-11:00) ---


@pytest.mark.parametrize(
    "t, inside",
    [
        (time(21, 0), True),  # start is included
        (time(23, 59), True),  # just before midnight
        (time(0, 0), True),  # midnight
        (time(10, 59), True),  # just before the end
        (time(11, 0), False),  # end is not included
        (time(20, 59), False),  # just before the start
        (time(14, 0), False),  # middle of the day
    ],
)
def test_window_crossing_midnight(t, inside):
    assert SHOULDER.contains(t) is inside


# --- Price of one reading at each boundary ---


@pytest.mark.parametrize(
    "hhmm, expected",
    [
        ("10:30", "1.6092"),  # shoulder: 20.75c + supply 140.17c = 160.92c
        ("11:00", "1.5459"),  # off-peak starts: 14.42c + 140.17c = 154.59c
        ("15:30", "1.5459"),  # last off-peak half-hour
        ("16:00", "1.7603"),  # peak starts: 35.86c + 140.17c = 176.03c
        ("20:30", "1.7603"),  # last peak half-hour
        ("21:00", "1.6092"),  # shoulder starts again
        ("23:30", "1.6092"),  # shoulder before midnight
        ("00:00", "1.6092"),  # shoulder after midnight
    ],
)
def test_tou_bill_one_kwh(hhmm, expected):
    assert tou_bill([reading(1, hhmm, "1")], NECTR_TOU) == Decimal(expected)


def test_tou_bill_several_days():
    # Day 1: 2 kWh peak (18:00) = 71.72c, 4 kWh shoulder (03:00) = 83.00c
    # Day 2: 3 kWh off-peak (12:00) = 43.26c
    # Energy 197.98c + supply 2 x 140.17c = 280.34c; total 478.32c = $4.7832
    readings = [
        reading(1, "18:00", "2"),
        reading(1, "03:00", "4"),
        reading(2, "12:00", "3"),
    ]
    assert tou_bill(readings, NECTR_TOU) == Decimal("4.7832")


# --- Invalid plans ---


def test_tou_overlapping_windows_are_rejected():
    with pytest.raises(ValueError, match="overlap at 15:00"):
        TOUPlan(
            "Bad plan",
            (
                Window("day", time(7, 0), time(16, 0), Decimal(30)),
                Window("evening", time(15, 0), time(7, 0), Decimal(20)),
            ),
            Decimal(100),
        )


def test_tou_gap_between_windows_is_rejected():
    with pytest.raises(ValueError, match="no window covers 16:00"):
        TOUPlan(
            "Bad plan",
            (
                Window("day", time(7, 0), time(16, 0), Decimal(30)),
                Window("night", time(17, 0), time(7, 0), Decimal(20)),
            ),
            Decimal(100),
        )


def test_tou_needs_at_least_one_window():
    with pytest.raises(ValueError, match="at least one time window"):
        TOUPlan("Bad plan", (), Decimal(100))


def test_tou_window_with_same_start_and_end_is_rejected():
    with pytest.raises(ValueError, match="same time"):
        TOUPlan(
            "Bad plan",
            (Window("all", time(0, 0), time(0, 0), Decimal(30)),),
            Decimal(100),
        )


def test_tou_negative_rate_is_rejected():
    with pytest.raises(ValueError, match="rate cannot be negative"):
        TOUPlan(
            "Bad plan",
            (
                Window("day", time(7, 0), time(19, 0), Decimal(-1)),
                Window("night", time(19, 0), time(7, 0), Decimal(20)),
            ),
            Decimal(100),
        )


def test_tou_negative_supply_is_rejected():
    with pytest.raises(ValueError, match="supply charge"):
        TOUPlan(
            "Bad plan",
            (
                Window("day", time(7, 0), time(19, 0), Decimal(30)),
                Window("night", time(19, 0), time(7, 0), Decimal(20)),
            ),
            Decimal(-1),
        )
