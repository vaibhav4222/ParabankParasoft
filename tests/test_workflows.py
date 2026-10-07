from collections import Counter
import pytest
from framework.api import validate_history
from framework.data import Customer
from framework.money import cents
from pages.banking import BankingPage

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def loan_customer(browser, bank_url, sandbox):
    """Scenario A is explicit fixture setup; B reuses its user and account IDs."""
    sandbox()
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.set_default_timeout(20000)
    bank = BankingPage(page, bank_url)
    customer = Customer()
    try:
        bank.register(customer)
        initial = bank.overview_accounts()[0]
        checking = bank.open_checking(initial)
        assert checking != initial
        loan = bank.request_loan(checking, "500.00", "50.00")
        assert loan not in (initial, checking)
        assert bank.balance(loan) == cents("500.00")
        yield {"bank": bank, "customer": customer, "checking": checking, "loan": loan}
    except Exception:
        from pathlib import Path
        Path("reports/screenshots").mkdir(parents=True, exist_ok=True)
        page.screenshot(path="reports/screenshots/workflow-failure.png", full_page=True)
        raise
    finally:
        from pathlib import Path
        Path("reports/traces").mkdir(parents=True, exist_ok=True)
        context.tracing.stop(path="reports/traces/loan-and-transfers.zip")
        context.close()


def test_scenario_a_loan_approved_and_funded(loan_customer, sandbox):
    sandbox()
    assert loan_customer["bank"].balance(loan_customer["loan"]) == 50000


def test_scenario_b_transfer_table_reconciles(loan_customer, sandbox):
    sandbox()
    bank = loan_customer["bank"]
    origin, destination = loan_customer["loan"], loan_customer["checking"]
    before = bank.balance(origin)
    recipient_before = bank.balance(destination)
    amounts = ["150.00", "25.50", "8.99"]
    for amount in amounts:
        sandbox()
        bank.transfer(origin, destination, amount)
    after = bank.balance(origin)
    recipient_after = bank.balance(destination)
    expected = sum(cents(amount) for amount in amounts)
    rows = bank.find_transactions(origin)
    debits = [cents(row["debit (-)"]) for row in rows
              if row.get("debit (-)") and row.get("transaction", "") == "Funds Transfer Sent"]
    assert Counter(debits) == Counter(cents(amount) for amount in amounts), rows
    assert sum(debits) == expected == before - after
    assert recipient_after - recipient_before == expected


def test_scenario_c_api_contract_and_deposit(api, sandbox):
    # No page/browser fixture: all interactions are Playwright APIRequestContext.
    customer = api.register(Customer())
    accounts = api.accounts(customer["id"])
    assert accounts, "Registration did not create an account"
    account_id = accounts[0]["id"]
    before = cents(api.account(account_id)["balance"])
    previous = api.transactions(account_id)
    validate_history(previous)
    old_ids = {transaction["id"] for transaction in previous}
    sandbox()
    api.deposit(account_id, "123.45")
    history = api.transactions(account_id)
    validate_history(history)
    added = [transaction for transaction in history if transaction["id"] not in old_ids]
    assert len(added) == 1
    assert added[0]["accountId"] == account_id
    assert added[0]["type"] == "Credit"
    assert cents(added[0]["amount"]) == 12345
    assert cents(api.account(account_id)["balance"]) - before == 12345
