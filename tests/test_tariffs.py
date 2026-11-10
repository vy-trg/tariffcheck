from datetime import datetime
from decimal import Decimal

import pytest

from tariffcheck.tariffs import FlatPlan, Reading, flat_bill

# Real plan from docs/design.md (NTR1154691MRE1)
NECTR_FLAT = FlatPlan("Nectr Power Perks", Decimal("24.48"), Decimal("164.87"))


def reading(day: int, hhmm: str, kwh: str) -> Reading:
    """A reading on `day` October 2026 at `hhmm`, e.g. reading(1, "18:00", "10")."""
    hour, minute = map(int, hhmm.split(":"))
    return Reading(datetime(2026, 10, day, hour, minute), Decimal(kwh))


def test_flat_bill_one_day():
    # 10 kWh x 24.48c = 244.80c, plus 1 day supply 164.87c = 409.67c = $4.0967
    assert flat_bill([reading(1, "18:00", "10")], NECTR_FLAT) == Decimal("4.0967")
    
def test_flat_bill_zero_usage_still_pays_supply():
    # 0 kWh, 1 day supply 164.87c = $1.6487
    assert flat_bill([reading(1, "18:00", "0")], NECTR_FLAT) == Decimal("1.6487")


def test_flat_bill_charges_supply_once_per_day():
    # 4 + 6 kWh on day 1, 10 kWh on day 2 = 20 kWh x 24.48c = 489.60c
    # 2 days supply = 2 x 164.87c = 329.74c; total 819.34c = $8.1934
    readings = [reading(1, "08:00", "4"), reading(1, "19:00", "6"), reading(2, "19:00", "10")]
    assert flat_bill(readings, NECTR_FLAT) == Decimal("8.1934")