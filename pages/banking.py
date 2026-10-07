import re
from playwright.sync_api import Page, expect
from framework.data import Customer
from framework.money import cents


class BankingPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base = base_url.rstrip("/") + "/"

    def visit(self, path: str):
        self.page.goto(self.base + path)

    def register(self, customer: Customer):
        self.visit("register.htm")
        for name, value in customer.form().items():
            self.page.locator(f'[name="{name}"]').fill(value)
        self.page.get_by_role("button", name="Register", exact=True).click()
        expect(self.page.locator("#rightPanel")).to_contain_text("Your account was created successfully")

    def overview_accounts(self) -> list[str]:
        self.visit("overview.htm")
        links = self.page.locator('#accountTable tbody a[href*="activity.htm"]')
        expect(links.first).to_have_text(re.compile(r"^\d+$"))
        return links.all_text_contents()

    def select_account(self, selector: str, account: str):
        option = self.page.locator(f'{selector} option[value="{account}"]')
        expect(option).to_have_count(1)
        expect(option).to_have_text(re.compile(r"^\d+$"))
        self.page.locator(selector).select_option(account)

    def open_checking(self, funding_account: str) -> str:
        self.visit("openaccount.htm")
        self.page.locator("#type").select_option(label="CHECKING")
        self.select_account("#fromAccountId", funding_account)
        self.page.get_by_role("button", name="Open New Account", exact=True).click()
        account = self.page.locator("#newAccountId")
        expect(account).to_have_text(re.compile(r"^\d+$"))
        return account.inner_text().strip()

    def request_loan(self, source: str, amount: str, down_payment: str) -> str:
        self.visit("requestloan.htm")
        self.page.locator("#amount").fill(amount)
        self.page.locator("#downPayment").fill(down_payment)
        self.select_account("#fromAccountId", source)
        self.page.get_by_role("button", name="Apply Now", exact=True).click()
        expect(self.page.locator("#loanStatus")).to_have_text("Approved")
        account = self.page.locator("#newAccountId")
        expect(account).to_have_text(re.compile(r"^\d+$"))
        return account.inner_text().strip()

    def balance(self, account: str) -> int:
        self.visit(f"activity.htm?id={account}")
        expect(self.page.locator("#accountId")).to_have_text(account)
        balance = self.page.locator("#balance")
        expect(balance).to_have_text(re.compile(r"^-?\$[\d,]+\.\d{2}$"))
        return cents(balance.inner_text())

    def transfer(self, origin: str, destination: str, amount: str):
        self.visit("transfer.htm")
        self.page.locator("#amount").fill(amount)
        self.select_account("#fromAccountId", origin)
        self.select_account("#toAccountId", destination)
        self.page.get_by_role("button", name="Transfer", exact=True).click()
        expect(self.page.locator("#rightPanel")).to_contain_text("Transfer Complete!")
        expect(self.page.locator("#rightPanel")).to_contain_text(f"${amount}")

    def find_transactions(self, account: str) -> list[dict]:
        self.visit("findtrans.htm")
        self.select_account("#accountId", account)
        # Cover a midnight boundary and server/client timezone differences.
        dates = self.page.evaluate("""() => [-1, 1].map(offset => {
            const date = new Date(); date.setUTCDate(date.getUTCDate() + offset);
            return [String(date.getUTCMonth()+1).padStart(2,'0'),
                    String(date.getUTCDate()).padStart(2,'0'), date.getUTCFullYear()].join('-');
        })""")
        self.page.locator("#fromDate").fill(dates[0])
        self.page.locator("#toDate").fill(dates[1])
        self.page.locator("#findByDateRange").click()
        # Results header appears only after the asynchronous query completes.
        expect(self.page.get_by_role("heading", name="Transaction Results", exact=True)).to_be_visible()
        rows = self.page.locator("#transactionTable tbody tr")
        expect(rows.first).to_be_visible()
        headers = [h.strip().lower() for h in self.page.locator("#transactionTable thead th").all_text_contents()]
        result = []
        for row in rows.all():
            cells = row.locator("td").all_text_contents()
            assert len(cells) == len(headers), "Transaction table header/cell mismatch"
            result.append(dict(zip(headers, (cell.strip() for cell in cells))))
        return result
