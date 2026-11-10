from datetime import datetime
from decimal import Decimal

import pytest

from tariffcheck.tariffs import (
    Block,
    BlockPlan,
    FlatPlan,
    Reading,
    block_bill,
    flat_bill,
)

# Real plans from docs/design.md
NECTR_FLAT = FlatPlan(
    "Nectr Power Perks", Decimal("24.48"), Decimal("164.87")
)  # NTR1154691MRE1
GLOBIRD_BLOCK = (
    BlockPlan(  # GLO1212438MRE1: 22.44c for the first 15 kWh a day, then 25.30c
        "GloBird GLOHOME",
        (Block(Decimal(15), Decimal("22.44")), Block(None, Decimal("25.30"))),
        Decimal("148.50"),
    )
)


def reading(day: int, hhmm: str, kwh: str) -> Reading:
    """A reading on `day` October 2026 at `hhmm`, e.g. reading(1, "18:00", "10")."""
    hour, minute = map(int, hhmm.split(":"))
    return Reading(datetime(2026, 10, day, hour, minute), Decimal(kwh))


# --- Flat ---


def test_flat_bill_one_day():
    # 10 kWh x 24.48c = 244.80c, plus 1 day supply 164.87c = 409.67c = $4.0967
    assert flat_bill([reading(1, "18:00", "10")], NECTR_FLAT) == Decimal("4.0967")


def test_flat_bill_zero_usage_still_pays_supply():
    # 0 kWh, 1 day supply 164.87c = $1.6487
    assert flat_bill([reading(1, "18:00", "0")], NECTR_FLAT) == Decimal("1.6487")


def test_flat_bill_charges_supply_once_per_day():
    # 4 + 6 kWh on day 1, 10 kWh on day 2 = 20 kWh x 24.48c = 489.60c
    # 2 days supply = 2 x 164.87c = 329.74c; total 819.34c = $8.1934
    readings = [
        reading(1, "08:00", "4"),
        reading(1, "19:00", "6"),
        reading(2, "19:00", "10"),
    ]
    assert flat_bill(readings, NECTR_FLAT) == Decimal("8.1934")


# --- Block ---


@pytest.mark.parametrize(
    "kwh, expected",
    [
        ("0", "1.485"),  # supply only: 148.50c
        ("10", "3.729"),  # 10 x 22.44 = 224.40c + 148.50c = 372.90c
        ("15", "4.851"),  # exactly the threshold: 15 x 22.44 = 336.60c + 148.50c
        ("15.01", "4.85353"),  # 336.60c + 0.01 x 25.30 = 0.253c, + 148.50c = 485.353c
        ("20", "6.116"),  # 336.60c + 5 x 25.30 = 126.50c, + 148.50c = 611.60c
    ],
)
def test_block_bill_one_day(kwh, expected):
    assert block_bill([reading(1, "18:00", kwh)], GLOBIRD_BLOCK) == Decimal(expected)


def test_block_threshold_resets_each_day():
    # Day 1: 20 kWh = 15 x 22.44 + 5 x 25.30 = 463.10c
    # Day 2:  5 kWh =  5 x 22.44           = 112.20c
    # Supply 2 x 148.50c = 297.00c; total 872.30c = $8.723
    # (If the threshold did NOT reset, 25 kWh would cost 589.60c and this would fail.)
    readings = [reading(1, "18:00", "20"), reading(2, "18:00", "5")]
    assert block_bill(readings, GLOBIRD_BLOCK) == Decimal("8.723")


def test_block_adds_up_readings_within_a_day():
    # Two readings on the same day add up to 20 kWh: $6.116, same as 20 kWh in one reading
    readings = [reading(1, "08:00", "10"), reading(1, "19:00", "10")]
    assert block_bill(readings, GLOBIRD_BLOCK) == Decimal("6.116")


def test_block_with_three_steps():
    # 0-10 kWh at 20c, 10-20 kWh at 30c, rest at 40c; 25 kWh in one day, no supply
    # 10 x 20 + 10 x 30 + 5 x 40 = 200 + 300 + 200 = 700c = $7
    plan = BlockPlan(
        "Three steps",
        (
            Block(Decimal(10), Decimal(20)),
            Block(Decimal(20), Decimal(30)),
            Block(None, Decimal(40)),
        ),
        Decimal(0),
    )
    assert block_bill([reading(1, "18:00", "25")], plan) == Decimal(7)


# --- Invalid input ---


def test_negative_kwh_is_rejected():
    with pytest.raises(ValueError, match="kWh cannot be negative"):
        reading(1, "18:00", "-1")


def test_negative_rate_is_rejected():
    with pytest.raises(ValueError, match="usage rate"):
        FlatPlan("Bad plan", Decimal(-1), Decimal(100))


def test_negative_supply_is_rejected():
    with pytest.raises(ValueError, match="supply charge"):
        FlatPlan("Bad plan", Decimal(20), Decimal(-1))


def test_block_thresholds_out_of_order_are_rejected():
    with pytest.raises(ValueError, match="must increase"):
        BlockPlan(
            "Bad plan",
            (
                Block(Decimal(15), Decimal(22)),
                Block(Decimal(10), Decimal(24)),
                Block(None, Decimal(26)),
            ),
            Decimal(100),
        )


def test_block_last_block_must_cover_the_rest():
    # Without a final "rest of usage" block, kWh above 15 would have no price
    with pytest.raises(ValueError, match="last block"):
        BlockPlan("Bad plan", (Block(Decimal(15), Decimal(22)),), Decimal(100))


def test_block_needs_at_least_one_block():
    with pytest.raises(ValueError, match="at least one block"):
        BlockPlan("Bad plan", (), Decimal(100))


def test_block_negative_rate_is_rejected():
    with pytest.raises(ValueError, match="block rate"):
        BlockPlan("Bad plan", (Block(None, Decimal(-1)),), Decimal(100))


def test_block_negative_supply_is_rejected():
    with pytest.raises(ValueError, match="supply charge"):
        BlockPlan("Bad plan", (Block(None, Decimal(20)),), Decimal(-1))
