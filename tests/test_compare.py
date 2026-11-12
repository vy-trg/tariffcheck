from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from tariffcheck.compare import PlanCost, compare_plans, to_cents
from tariffcheck.loader import load_usage
from tariffcheck.plans import GLOBIRD_BLOCK, NECTR_FLAT, NECTR_TOU, REAL_PLANS
from tariffcheck.tariffs import FlatPlan, Reading

SAMPLE = Path(__file__).parent.parent / "data" / "sample_usage.csv"

# One day, 10 kWh at 18:00 (peak). Exact costs worked out by hand:
#   GloBird block: 10 x 22.44 = 224.40c + supply 148.50c = $3.729
#   Nectr flat:    10 x 24.48 = 244.80c + supply 164.87c = $4.0967
#   Nectr TOU:     10 x 35.86 = 358.60c + supply 140.17c = $4.9877
ONE_DAY = [Reading(datetime(2026, 10, 1, 18, 0), Decimal(10))]


def test_rows_are_cheapest_first_with_energy_supply_and_total():
    result = compare_plans(ONE_DAY, list(REAL_PLANS))
    assert result.rows == (
        PlanCost(
            "GloBird GLOHOME (block)",
            Decimal("2.24"),
            Decimal("1.49"),
            Decimal("3.73"),
            Decimal("1361.09"),  # 3.729 x 365 = 1361.085
        ),
        PlanCost(
            "Nectr Power Perks (flat)",
            Decimal("2.45"),
            Decimal("1.65"),
            Decimal("4.10"),
            Decimal("1495.30"),  # 4.0967 x 365 = 1495.2955
        ),
        PlanCost(
            "Nectr Power Perks TOU",
            Decimal("3.59"),
            Decimal("1.40"),
            Decimal("4.99"),
            Decimal("1820.51"),  # 4.9877 x 365 = 1820.5105
        ),
    )


def test_cheapest_plan_and_saving():
    result = compare_plans(ONE_DAY, list(REAL_PLANS))
    assert result.cheapest == ("GloBird GLOHOME (block)",)
    assert result.saving == Decimal("1.26")  # 4.9877 - 3.729 = 1.2587
    assert result.yearly_saving == Decimal("459.43")  # 1.2587 x 365 = 459.4255
    assert result.days == 1


def test_order_of_plans_given_does_not_matter():
    a = compare_plans(ONE_DAY, [NECTR_TOU, NECTR_FLAT, GLOBIRD_BLOCK])
    b = compare_plans(ONE_DAY, [GLOBIRD_BLOCK, NECTR_FLAT, NECTR_TOU])
    assert a == b


def test_two_plans_with_the_same_price_are_both_cheapest():
    twin_a = FlatPlan("Twin A", Decimal(25), Decimal(100))
    twin_b = FlatPlan("Twin B", Decimal(25), Decimal(100))
    result = compare_plans(ONE_DAY, [twin_b, twin_a])
    assert result.cheapest == ("Twin A", "Twin B")
    assert result.saving == Decimal("0.00")
    assert [row.name for row in result.rows] == ["Twin A", "Twin B"]  # ties by name


def test_one_plan_is_the_cheapest_with_no_saving():
    result = compare_plans(ONE_DAY, [NECTR_FLAT])
    assert result.cheapest == ("Nectr Power Perks (flat)",)
    assert result.saving == Decimal("0.00")


def test_no_plans_is_an_error():
    with pytest.raises(ValueError, match="at least one plan"):
        compare_plans(ONE_DAY, [])


def test_no_readings_is_an_error():
    with pytest.raises(ValueError, match="No readings"):
        compare_plans([], list(REAL_PLANS))


def test_unknown_plan_type_is_an_error():
    with pytest.raises(TypeError, match="Unknown plan type"):
        compare_plans(ONE_DAY, ["not a plan"])


def test_sample_month_with_real_plans():
    # 30 days of sample data; yearly estimates are close to Energy Made Easy's
    # "medium usage, no discounts" figures ($1,750 GloBird, $1,920 Nectr flat)
    result = compare_plans(load_usage(SAMPLE), list(REAL_PLANS))
    assert result.days == 30
    assert [row.name for row in result.rows] == [
        "GloBird GLOHOME (block)",
        "Nectr Power Perks (flat)",
        "Nectr Power Perks TOU",
    ]
    assert result.rows[0].yearly == Decimal("1752.14")
    assert result.saving == Decimal("17.80")


@pytest.mark.parametrize(
    "dollars, cents",
    [("4.0967", "4.10"), ("1.485", "1.49"), ("1.4017", "1.40"), ("3", "3.00")],
)
def test_to_cents_rounds_halves_up(dollars, cents):
    assert to_cents(Decimal(dollars)) == Decimal(cents)
