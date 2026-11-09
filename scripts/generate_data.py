"""Generate fake household electricity usage for testing TariffCheck.

Writes data/sample_usage.csv: one row every 30 minutes for 30 days,
columns timestamp,kwh. The random seed is fixed, so every run produces
exactly the same file.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
DAYS = 30
START = datetime(2026, 10, 1, 0, 0)  # local time, Brisbane (no daylight saving)
INTERVAL = timedelta(minutes=30)
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_usage.csv"


def typical_kwh(hour: int) -> float:
    """Average kWh for one 30-minute interval at this hour of the day."""
    if 0 <= hour < 6:     # night: fridge and standby only
        return 0.10
    if 6 <= hour < 9:     # morning: kettle, shower, breakfast
        return 0.40
    if 9 <= hour < 16:    # day: house mostly empty
        return 0.18
    if 16 <= hour < 21:   # evening peak: cooking, aircon, TV
        return 0.70        
    return 0.25           # late evening


def main() -> None:
    rng = random.Random(SEED)  # own generator, so nothing else changes the numbers
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "kwh"])
        t = START
        for _ in range(DAYS * 48):  # 48 half-hours per day
            if t.hour == 0 and t.minute == 0:
                # Some days use more (hot day, guests), some less
                day_factor = rng.uniform(0.8, 1.25)
            kwh = typical_kwh(t.hour) * day_factor * rng.uniform(0.7, 1.3)
    print(f"Wrote {DAYS * 48} rows to {OUTPUT}")


if __name__ == "__main__":
    main()