from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Reading:
    """Energy used in one 30-minute interval, starting at `timestamp`."""

    timestamp: datetime
    kwh: Decimal


@dataclass(frozen=True)
class FlatPlan:
    """One price for every kWh, plus a daily supply charge. Prices in cents."""

    name: str
    rate_c: Decimal
    supply_c: Decimal

def flat_bill(readings: list[Reading], plan: FlatPlan) -> Decimal:
    """Cost of the readings under a flat plan, in dollars (not rounded)."""
    total_kwh = sum((r.kwh for r in readings), Decimal(0))
    energy_c = total_kwh * plan.rate_c
    days = {r.timestamp.date() for r in readings}
    supply_c = len(days) * plan.supply_c
    return (energy_c + supply_c) / 100