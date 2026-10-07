import json
from decimal import Decimal
from pathlib import Path
from bs4 import BeautifulSoup
from jsonschema import Draft202012Validator
from playwright.sync_api import APIRequestContext
from framework.data import Customer


class BankAPI:
    def __init__(self, request: APIRequestContext, base_url: str):
        self.request = request
        self.base = base_url.rstrip("/") + "/"

    def url(self, path: str) -> str:
        return self.base + path.lstrip("/")

    @staticmethod
    def checked(response):
        assert response.ok, f"HTTP {response.status}: {response.text()[:500]}"
        return response

    def get(self, path: str):
        response = self.checked(self.request.get(self.url("services/bank/" + path)))
        return json.loads(response.text(), parse_float=Decimal)

    def post(self, path: str, params: dict):
        return self.checked(self.request.post(self.url("services/bank/" + path), params=params))

    def reset_and_configure(self):
        # Same HTTP form endpoints used by the administration interface; no browser.
        self.checked(self.request.post(self.url("db.htm"), form={"action": "CLEAN"}))
        html = self.checked(self.request.get(self.url("admin.htm"))).text()
        form = BeautifulSoup(html, "html.parser").select_one("#adminForm")
        assert form, "Admin settings form missing"
        values = {}
        for field in form.select("input[name]"):
            kind = field.get("type", "text")
            if kind in ("submit", "button") or (kind in ("radio", "checkbox") and not field.has_attr("checked")):
                continue
            values[field["name"]] = field.get("value", "")
        for select in form.select("select[name]"):
            option = select.select_one("option[selected]") or select.select_one("option")
            values[select["name"]] = option["value"]
        # Predictable funding and approval, independent of previous sandbox users.
        values.update(loanProvider="ws", loanProcessor="down", loanProcessorThreshold="10",
                      initialBalance="1000.00", minimumBalance="100.00",
                      accessMode="jdbc", endpoint="", soapEndpoint="", restEndpoint="")
        self.checked(self.request.post(self.url("admin.htm"), form=values))
        saved = BeautifulSoup(self.checked(self.request.get(self.url("admin.htm"))).text(), "html.parser")
        for name, expected in values.items():
            field = saved.select_one(f'[name="{name}"]')
            assert field, f"Missing setting {name}"
            if field.name == "select":
                actual = field.select_one("option[selected]")["value"]
            elif field.get("type") == "radio":
                actual = saved.select_one(f'input[name="{name}"][checked]')["value"]
            else:
                actual = field.get("value", "")
            assert actual == expected, f"Admin setting {name} was not persisted"

    def register(self, customer: Customer):
        # ParaBank exposes registration as an HTTP form, not a REST create-customer route.
        self.checked(self.request.get(self.url("register.htm")))
        response = self.checked(self.request.post(self.url("register.htm"), form=customer.form()))
        assert "Your account was created successfully" in response.text(), "API registration failed"
        return self.get(f"login/{customer.username}/{customer.password}")

    def accounts(self, customer_id: int):
        return self.get(f"customers/{customer_id}/accounts")

    def account(self, account_id: str | int):
        return self.get(f"accounts/{account_id}")

    def deposit(self, account_id: int, amount: str):
        return self.post("deposit", {"accountId": account_id, "amount": amount})

    def transactions(self, account_id: int):
        return self.get(f"accounts/{account_id}/transactions")


def validate_history(history):
    schema_path = Path(__file__).resolve().parents[1] / "contracts/transactions.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(history)
