from datetime import date

from paa.api.routes._shared import since_date
from paa.etl.util import norm_postcode, to_decimal_or_none


def test_norm_postcode() -> None:
    assert norm_postcode(" n11 2ab ") == "N112AB"
    assert norm_postcode("") is None
    assert norm_postcode(None) is None


def test_to_decimal_or_none() -> None:
    assert to_decimal_or_none("98.5") == "98.5"
    assert to_decimal_or_none("") is None
    assert to_decimal_or_none("n/a") is None


def test_since_date_rolls_years() -> None:
    assert since_date(date(2026, 8, 31), 24) == date(2024, 8, 28)
    assert since_date(date(2026, 1, 15), 12) == date(2025, 1, 15)
    assert since_date(date(2026, 3, 1), 60) == date(2021, 3, 1)
