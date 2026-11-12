"""The real Queensland plans from docs/design.md (Energy Made Easy, 9 Nov 2026)."""

from datetime import time
from decimal import Decimal

from tariffcheck.tariffs import Block, BlockPlan, FlatPlan, TOUPlan, Window

NECTR_FLAT = FlatPlan(
    "Nectr Power Perks (flat)", Decimal("24.48"), Decimal("164.87")
)  # NTR1154691MRE1

GLOBIRD_BLOCK = BlockPlan(
    "GloBird GLOHOME (block)",
    (Block(Decimal(15), Decimal("22.44")), Block(None, Decimal("25.30"))),
    Decimal("148.50"),
)  # GLO1212438MRE1

NECTR_TOU = TOUPlan(
    "Nectr Power Perks TOU",
    (
        Window("peak", time(16, 0), time(21, 0), Decimal("35.86")),
        Window("off-peak", time(11, 0), time(16, 0), Decimal("14.42")),
        Window("shoulder", time(21, 0), time(11, 0), Decimal("20.75")),
    ),
    Decimal("140.17"),
)  # NTR1154695MRE1

REAL_PLANS = (NECTR_FLAT, GLOBIRD_BLOCK, NECTR_TOU)
