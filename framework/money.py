"""Strict US currency parsing; all assertions and aggregation use integer cents."""
import re
from decimal import Decimal


def cents(value: str | int | Decimal) -> int:
    raw = str(value).strip()
    if not re.fullmatch(r"-?\$?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?", raw):
        raise ValueError(f"Invalid USD amount: {value!r}")
    return int(Decimal(raw.replace("$", "").replace(",", "")) * 100)


def dollars(value: int) -> str:
    return f"{Decimal(value) / 100:.2f}"
