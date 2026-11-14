"""Read half-hourly usage from a CSV file into Reading objects."""

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import IO

import pandas as pd

from tariffcheck.tariffs import Reading

REQUIRED_COLUMNS = ("timestamp", "kwh")
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"


class UsageFileError(ValueError):
    """The usage CSV can't be used. The message says which line and why."""


def load_usage(source: str | Path | IO) -> list[Reading]:
    """Read a `timestamp,kwh` CSV. Raise UsageFileError with a clear message if it is wrong.

    `source` is a file path, or an open file such as a Streamlit upload.
    """
    if isinstance(source, (str, Path)):
        source = Path(source)
    name = Path(getattr(source, "name", "upload.csv")).name
    try:
        # Read everything as text: kWh goes straight into Decimal, never through float
        df = pd.read_csv(source, dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        raise UsageFileError(f"{name}: the file is empty") from None

    # "Timestamp", " kWh " and "kwh" all mean the same column
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise UsageFileError(f"{name}: missing column(s): {', '.join(missing)}")
    if df.empty:
        raise UsageFileError(f"{name}: no readings, only a header line")

    # Line numbers as people see them in the file: the header is line 1
    def line(i: int) -> str:
        return f"{name}, line {i + 2}"

    times = pd.to_datetime(df["timestamp"], format=TIMESTAMP_FORMAT, errors="coerce")
    bad_time = times.isna()
    if bad_time.any():
        i = bad_time.idxmax()
        raise UsageFileError(
            f"{line(i)}: timestamp {df.at[i, 'timestamp']!r} should look like 2026-10-01 18:30"
        )

    duplicate = times.duplicated()
    if duplicate.any():
        i = duplicate.idxmax()
        raise UsageFileError(
            f"{line(i)}: timestamp {df.at[i, 'timestamp']} appears twice"
        )

    readings = []
    for i, (timestamp, kwh_text) in enumerate(zip(times, df["kwh"], strict=True)):
        try:
            kwh = Decimal(kwh_text)
        except InvalidOperation:
            raise UsageFileError(
                f"{line(i)}: kWh {kwh_text!r} is not a number"
            ) from None
        if not kwh.is_finite():
            raise UsageFileError(f"{line(i)}: kWh {kwh_text!r} is not a number")
        if kwh < 0:
            raise UsageFileError(f"{line(i)}: kWh {kwh_text} cannot be negative")
        readings.append(Reading(timestamp.to_pydatetime(), kwh))
    return readings
