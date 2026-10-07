# ParaBank QA Automation Assessment

Playwright **Python** framework implementing the supplied Senior QA assessment.
Python is one of the permitted stacks. The API contract is also declared as a
TypeScript interface in `contracts/transaction.ts`; its exact runtime shape is
enforced by `contracts/transactions.schema.json` (required keys, no extra keys,
field types, enums, nonnegative integer epoch-millisecond timestamps).

## Install (Windows PowerShell)

Requires Python 3.11+ and Git. Tested here with Python 3.14.

```powershell
cd D:\ParabankParasoft
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

On Linux/macOS use `.venv/bin/python` instead, and install the browser with
`python -m playwright install --with-deps chromium`.

## Run and view the custom report

Offline framework validation (no network and no database reset):

```powershell
.\.venv\Scripts\python.exe -m pytest --report-path reports/unit/index.html
```

Full assessment, headless by default:

```powershell
.\.venv\Scripts\python.exe -m pytest --run-integration --allow-reset --browser chromium
```

**The integration command clears the ENTIRE selected ParaBank database and changes
global admin settings.** Use a private deployment or a reserved sandbox. An
explicit `--allow-reset` flag is mandatory. The default target is the public
assessment URL. Override it with `--bank-url http://localhost:8080/parabank/`
or the `PARABANK_URL` environment variable.

The custom HTML dashboard and structured JSON results are automatically written
at session end, including failures and skips. Summary cards use translucent layers,
blur and shadows; headers, active filter buttons and passing statuses use `#F48031`.
No stock Playwright HTML report or Allure is used.

```powershell
Start-Process .\reports\index.html
# Or serve it:
.\.venv\Scripts\python.exe -m http.server 8085 --directory reports
# Open http://localhost:8085
```

Verify the rendered report's exact accent, card blur and working status filters:

```powershell
.\.venv\Scripts\python.exe tools/verify_report.py reports/index.html
```

This also saves desktop and mobile screenshots next to the report.

To run only the browserless API scenario:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_workflows.py -k scenario_c --run-integration --allow-reset
```

This command uses Playwright's HTTP request context and launches no browser.
It still performs the authorized session reset. Registration uses ParaBank's
HTTP registration form because its REST service has no create-customer route;
login, deposit, account and transaction queries use REST JSON endpoints.

## Scenarios and architecture

| Requirement | Implementation |
| --- | --- |
| A: reset, Web Service loan provider, registration, Checking and approved loan | Session API precondition and `loan_customer` fixture; `test_scenario_a_loan_approved_and_funded` verifies $500 in the extracted loan account |
| B: same user, three UI transfers, HTML transaction table and reconciliation | $150.00, $25.50 and $8.99; asserts individual debits, $184.49 sum, source reduction and recipient increase |
| C: API-only registration, deposit, history and exact schema | Independent UUID user, $123.45 deposit, strict contract plus transaction and balance assertions |
| Dynamic dropdowns | Playwright retrying assertions on actual option IDs; no fixed sleeps |
| Bespoke reporter | `framework/reporting.py` and pytest lifecycle hooks in `conftest.py` |
| Decisions | `DECISIONS.md` |

`pages/` owns UI interactions and HTML extraction. `framework/api.py` owns HTTP
setup and API queries. Tests own business assertions. A module fixture expresses
A → B's required user dependency explicitly, so selecting B alone still creates
the required loan user. Scenario C has an independent user. The reset runs once
per integration session, never before each test or during teardown.

The workflow trace is saved to `reports/traces/loan-and-transfers.zip`; fixture
failures save `reports/screenshots/workflow-failure.png`. Test failures using the
standard page fixture are linked directly from their report row.

```powershell
.\.venv\Scripts\python.exe -m playwright show-trace reports/traces/loan-and-transfers.zip
```

Artifacts can contain test credentials and customer data; retain them privately.

## Coordinated CI execution

All workers targeting the same shared instance must use the **same Redis server
and the same canonical base URL**. Redis provides a distributed lease held across
the entire reset and all scenarios, renewed every 30 seconds. Missing Redis in CI
is a configuration error. Parallel pytest workers are rejected.

```powershell
$env:CI = 'true'
$env:PARABANK_REDIS_URL = 'redis://localhost:6379/0'
$env:PARABANK_URL = 'http://your-reserved-parabank:8080/parabank/'
.\.venv\Scripts\python.exe -m pytest --run-integration --allow-reset
```

See `DECISIONS.md` for the unavoidable limit: a client lock cannot control unrelated
public sandbox users. For robust CI, deploy one ParaBank instance per worker.

## Submission

Repository: [vaibhav4222/ParabankParasoft](https://github.com/vaibhav4222/ParabankParasoft).
Submit that repository URL together with this README and `DECISIONS.md`.

## Verified endpoint references

- [ParaBank admin interface](https://parabank.parasoft.com/parabank/admin.htm)
- [ParaBank REST WADL](https://parabank.parasoft.com/parabank/services/bank?_wadl)
- [Playwright Python documentation](https://playwright.dev/python/)
