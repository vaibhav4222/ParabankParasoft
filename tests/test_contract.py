from copy import deepcopy
import pytest
from jsonschema import ValidationError
from framework.api import validate_history

TRANSACTION = {"id": 1, "accountId": 2, "type": "Credit", "date": 1791331200000,
               "amount": 123.45, "description": "Deposit"}


def test_contract_accepts_complete_response():
    validate_history([TRANSACTION])


@pytest.mark.parametrize("mutation", ["extra", "missing", "wrong_type", "invalid_date", "invalid_enum"])
def test_contract_rejects_schema_drift(mutation):
    transaction = deepcopy(TRANSACTION)
    if mutation == "extra":
        transaction["unexpected"] = True
    elif mutation == "missing":
        del transaction["description"]
    elif mutation == "wrong_type":
        transaction["amount"] = "123.45"
    elif mutation == "invalid_date":
        transaction["date"] = "not-a-date"
    else:
        transaction["type"] = "Refund"
    with pytest.raises(ValidationError):
        validate_history([transaction])
