from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class Reading:
    """Energy used in one 30-minute interval, starting at `timestamp`."""

    timestamp: datetime
    kwh: Decimal

    def __post_init__(self) -> None:
        if self.kwh < 0:
            raise ValueError(
                f"kWh cannot be negative (got {self.kwh} at {self.timestamp})"
            )


@dataclass(frozen=True)
class FlatPlan:
    """One price for every kWh, plus a daily supply charge. Prices in cents."""

    name: str
    rate_c: Decimal
    supply_c: Decimal

    def __post_init__(self) -> None:
        if self.rate_c < 0:
            raise ValueError(f"{self.name}: usage rate cannot be negative")
        if self.supply_c < 0:
            raise ValueError(f"{self.name}: supply charge cannot be negative")


@dataclass(frozen=True)
class Block:
    """One step of a block plan: usage up to `up_to_kwh` a day at `rate_c`.

    `up_to_kwh` is None for the last block, which covers the rest of the day's usage.
    """

    up_to_kwh: Decimal | None
    rate_c: Decimal


@dataclass(frozen=True)
class BlockPlan:
    """Stepped prices that reset every day, plus a daily supply charge. Prices in cents."""

    name: str
    blocks: tuple[Block, ...]
    supply_c: Decimal

    def __post_init__(self) -> None:
        if not self.blocks:
            raise ValueError(f"{self.name}: needs at least one block")
        if self.supply_c < 0:
            raise ValueError(f"{self.name}: supply charge cannot be negative")
        if self.blocks[-1].up_to_kwh is not None:
            raise ValueError(
                f"{self.name}: the last block must cover the rest of the usage"
            )

        previous_limit = Decimal(0)
        for block in self.blocks:
            if block.rate_c < 0:
                raise ValueError(f"{self.name}: block rate cannot be negative")
            if block.up_to_kwh is None:
                continue
            if block.up_to_kwh <= previous_limit:
                raise ValueError(f"{self.name}: block limits must increase")
            previous_limit = block.up_to_kwh


def _daily_kwh(readings: list[Reading]) -> dict[date, Decimal]:
    """Total kWh for each day in the readings."""
    totals = defaultdict(Decimal)
    for r in readings:
        totals[r.timestamp.date()] += r.kwh
    return totals


def flat_bill(readings: list[Reading], plan: FlatPlan) -> Decimal:
    """Cost of the readings under a flat plan, in dollars (not rounded)."""
    total_kwh = sum((r.kwh for r in readings), Decimal(0))
    energy_c = total_kwh * plan.rate_c
    days = {r.timestamp.date() for r in readings}
    supply_c = len(days) * plan.supply_c
    return (energy_c + supply_c) / 100


def _block_energy_c(day_kwh: Decimal, blocks: tuple[Block, ...]) -> Decimal:
    """Energy cost in cents for one day's usage under stepped blocks."""
    cost_c = Decimal(0)
    lower = Decimal(0)
    for block in blocks[:-1]:
        if day_kwh <= block.up_to_kwh:
            return cost_c + (day_kwh - lower) * block.rate_c
        cost_c += (block.up_to_kwh - lower) * block.rate_c
        lower = block.up_to_kwh
    return cost_c + (day_kwh - lower) * blocks[-1].rate_c


def block_bill(readings: list[Reading], plan: BlockPlan) -> Decimal:
    """Cost of the readings under a block plan, in dollars (not rounded)."""
    daily = _daily_kwh(readings)
    energy_c = sum(
        (_block_energy_c(kwh, plan.blocks) for kwh in daily.values()), Decimal(0)
    )
    supply_c = len(daily) * plan.supply_c
    return (energy_c + supply_c) / 100
