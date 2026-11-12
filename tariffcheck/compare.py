"""Price the same usage under several plans and find the cheapest."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from tariffcheck.tariffs import (
    BlockPlan,
    FlatPlan,
    Reading,
    TOUPlan,
    block_bill,
    flat_bill,
    tou_bill,
)

Plan = FlatPlan | BlockPlan | TOUPlan
CENT = Decimal("0.01")
DAYS_PER_YEAR = 365


def to_cents(dollars: Decimal) -> Decimal:
    """Round dollars to whole cents, halves rounded up (e.g. 4.0967 -> 4.10)."""
    return dollars.quantize(CENT, rounding=ROUND_HALF_UP)


def bill(readings: list[Reading], plan: Plan) -> Decimal:
    """Exact cost in dollars under any kind of plan."""
    if isinstance(plan, FlatPlan):
        return flat_bill(readings, plan)
    if isinstance(plan, BlockPlan):
        return block_bill(readings, plan)
    if isinstance(plan, TOUPlan):
        return tou_bill(readings, plan)
    raise TypeError(f"Unknown plan type: {type(plan).__name__}")


@dataclass(frozen=True)
class PlanCost:
    """One row of the comparison table. Money in dollars, rounded to cents."""

    name: str
    energy: Decimal
    supply: Decimal
    total: Decimal
    yearly: Decimal


@dataclass(frozen=True)
class Comparison:
    rows: tuple[PlanCost, ...]  # cheapest first
    cheapest: tuple[str, ...]  # more than one name if plans tie
    saving: Decimal  # cheapest vs most expensive, for the period in the data
    yearly_saving: Decimal
    days: int


def compare_plans(readings: list[Reading], plans: list[Plan]) -> Comparison:
    """Cost of the same readings under each plan, cheapest first."""
    if not readings:
        raise ValueError("No readings to compare")
    if not plans:
        raise ValueError("Choose at least one plan")

    days = len({r.timestamp.date() for r in readings})
    exact = []  # (exact total, plan) so ranking and savings are not affected by rounding
    for plan in plans:
        exact.append((bill(readings, plan), plan))
    exact.sort(key=lambda pair: (pair[0], pair[1].name))

    rows = []
    for total, plan in exact:
        supply = days * plan.supply_c / 100
        rows.append(
            PlanCost(
                name=plan.name,
                energy=to_cents(total - supply),
                supply=to_cents(supply),
                total=to_cents(total),
                yearly=to_cents(total / days * DAYS_PER_YEAR),
            )
        )

    lowest = exact[0][0]
    highest = exact[-1][0]
    return Comparison(
        rows=tuple(rows),
        cheapest=tuple(plan.name for total, plan in exact if total == lowest),
        saving=to_cents(highest - lowest),
        yearly_saving=to_cents((highest - lowest) / days * DAYS_PER_YEAR),
        days=days,
    )
