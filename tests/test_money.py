from decimal import Decimal
import pytest
from framework.money import cents, dollars


@pytest.mark.parametrize("value,expected", [("$1,234.56", 123456), ("$25.50", 2550),
                                         ("$8.99", 899), ("-$12.30", -1230), (Decimal("0.10"), 10)])
def test_currency_parsing(value, expected):
    assert cents(value) == expected


@pytest.mark.parametrize("value", ["$1,23.45", "12.345", "NaN", "", "1e3", "USD 5.00"])
def test_currency_rejects_malformed_values(value):
    with pytest.raises(ValueError):
        cents(value)


def test_decimal_transfer_sum_is_exact():
    assert sum(map(cents, ["$150.00", "$25.50", "$8.99"])) == 18449
    assert dollars(18449) == "184.49"
