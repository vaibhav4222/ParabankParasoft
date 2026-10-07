# Validation evidence

Verified on 7 October 2026 with Python 3.14.6, Playwright 1.63.0 and Chromium 153.

```powershell
.\.venv\Scripts\python.exe -m pytest --run-integration --allow-reset --browser chromium --browser-channel chromium
```

Result: **21 passed in 44.08 seconds**. Includes 18 local currency/contract checks
and all three live ParaBank assessment scenarios. The run reset the database and
read back the required global settings before any browser interaction.

```powershell
.\.venv\Scripts\python.exe tools/verify_report.py reports/index.html
```

Result: passed. Checks rendered orange headers and passing status, orange active
filters, 18px card backdrop blur, visible row counts for all status filters, and
restoration of all rows. Desktop and mobile previews are generated under `reports/`.

The browserless API-only run also passed independently. The successful loan/user
workflow trace is available at `reports/traces/loan-and-transfers.zip` locally.
Generated report files are intentionally ignored by Git.

No fixed browser sleeps were found in framework, page objects or tests. Redis
lease behavior was implemented and documented but not exercised against a Redis
service in this workspace. Distributed lock guarantees apply only to cooperating
clients; a private deployment is required to exclude unrelated sandbox resets.
