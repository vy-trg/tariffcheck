from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from tariffcheck.loader import UsageFileError, load_usage
from tariffcheck.tariffs import Reading

SAMPLE = Path(__file__).parent.parent / "data" / "sample_usage.csv"


def write_csv(tmp_path: Path, text: str) -> Path:
    """Write `text` to a temporary CSV file and return its path."""
    path = tmp_path / "usage.csv"
    path.write_text(text)
    return path


# --- Good files ---


def test_loads_the_sample_data():
    readings = load_usage(SAMPLE)
    assert len(readings) == 30 * 48  # 30 days, one reading every 30 minutes
    assert readings[0] == Reading(datetime(2026, 10, 1, 0, 0), Decimal("0.078"))
    assert readings[-1].timestamp == datetime(2026, 10, 30, 23, 30)


def test_keeps_kwh_exact(tmp_path):
    # As floats, 0.1 + 0.2 would be 0.30000000000000004
    text = "timestamp,kwh\n2026-10-01 00:00,0.1\n2026-10-01 00:30,0.2\n"
    readings = load_usage(write_csv(tmp_path, text))
    assert sum(r.kwh for r in readings) == Decimal("0.3")


def test_column_order_does_not_matter(tmp_path):
    path = write_csv(tmp_path, "kwh,timestamp\n0.5,2026-10-01 18:00\n")
    assert load_usage(path) == [Reading(datetime(2026, 10, 1, 18, 0), Decimal("0.5"))]


# --- Broken files: each error names the line and the problem ---


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "the file is empty"),
        ("timestamp,kwh\n", "no readings"),
        ("timestamp,energy\n2026-10-01 00:00,0.1\n", "missing column(s): kwh"),
        ("time,energy\n2026-10-01 00:00,0.1\n", "missing column(s): timestamp, kwh"),
        (
            "timestamp,kwh\n2026-10-01 00:00,0.1\n01/10/2026 00:30,0.1\n",
            "line 3: timestamp '01/10/2026 00:30' should look like",
        ),
        (
            "timestamp,kwh\n2026-10-01 25:00,0.1\n",
            "line 2: timestamp '2026-10-01 25:00'",
        ),
        (
            "timestamp,kwh\n2026-10-01 00:00,0.1\n2026-10-01 00:00,0.2\n",
            "line 3: timestamp 2026-10-01 00:00 appears twice",
        ),
        (
            "timestamp,kwh\n2026-10-01 00:00,-0.5\n",
            "line 2: kWh -0.5 cannot be negative",
        ),
        ("timestamp,kwh\n2026-10-01 00:00,abc\n", "line 2: kWh 'abc' is not a number"),
        ("timestamp,kwh\n2026-10-01 00:00,\n", "line 2: kWh '' is not a number"),
        ("timestamp,kwh\n2026-10-01 00:00,NaN\n", "line 2: kWh 'NaN' is not a number"),
    ],
)
def test_broken_file_gives_a_clear_error(tmp_path, text, message):
    path = write_csv(tmp_path, text)
    with pytest.raises(UsageFileError) as error:
        load_usage(path)
    assert message in str(error.value)
