import os
from pathlib import Path
import pytest
from framework.api import BankAPI
from framework.locking import sandbox_lock
from framework.reporting import write_dashboard


def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true", help="Run live ParaBank scenarios")
    parser.addoption("--allow-reset", action="store_true", help="Authorize global database reset")
    parser.addoption("--report-path", default="reports/index.html")
    parser.addoption("--bank-url", default=os.getenv("PARABANK_URL", "https://parabank.parasoft.com/parabank/"))


def pytest_configure(config):
    config._bank_results = {}
    if config.getoption("run_integration"):
        if not config.getoption("allow_reset"):
            raise pytest.UsageError("Integration setup resets all sandbox data. Supply --allow-reset on an authorized sandbox.")
        if os.getenv("CI") and not os.getenv("PARABANK_REDIS_URL"):
            raise pytest.UsageError("CI integration requires PARABANK_REDIS_URL for a shared sandbox lease.")
        if hasattr(config, "workerinput") or getattr(config.option, "numprocesses", None):
            raise pytest.UsageError("Global sandbox workflow must run serially; remove xdist workers.")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("run_integration"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Use --run-integration --allow-reset for live scenarios"))


@pytest.fixture(scope="session")
def bank_url(pytestconfig):
    return pytestconfig.getoption("bank_url")


@pytest.fixture(scope="session")
def sandbox(playwright, bank_url):
    with sandbox_lock(bank_url, os.getenv("PARABANK_REDIS_URL")) as assert_owned:
        request = playwright.request.new_context(extra_http_headers={"Accept": "application/json"}, timeout=30000)
        try:
            api = BankAPI(request, bank_url)
            assert_owned()
            api.reset_and_configure()
            yield assert_owned
        finally:
            request.dispose()


@pytest.fixture
def api(playwright, bank_url, sandbox):
    sandbox()
    request = playwright.request.new_context(extra_http_headers={"Accept": "application/json"}, timeout=30000)
    try:
        yield BankAPI(request, bank_url)
        sandbox()
    finally:
        request.dispose()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1440, "height": 1000}}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    results = item.config._bank_results
    entry = results.setdefault(item.nodeid, {"name": item.nodeid, "status": "passed", "duration": 0,
                                             "detail": "", "artifacts": []})
    entry["duration"] += report.duration
    if report.failed:
        entry["status"] = "failed"
        entry["detail"] += f"{report.when}: {report.longrepr}\n"
        page = item.funcargs.get("page")
        if page and not page.is_closed():
            try:
                target = Path(item.config.getoption("report_path")).resolve().parent
                artifact = target / "screenshots" / (item.name + ".png")
                artifact.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(artifact), full_page=True)
                entry["artifacts"].append(("Failure screenshot", f"screenshots/{artifact.name}"))
            except Exception:
                pass  # A closed/crashed page must not mask the original test failure.
    elif report.skipped and entry["status"] != "failed":
        entry["status"] = "skipped"
        entry["detail"] = str(report.longrepr)
    if "integration" in item.keywords and "scenario_c" not in item.name:
        root = Path(item.config.getoption("report_path")).resolve().parent
        for label, artifact in [("Workflow trace", Path("reports/traces/loan-and-transfers.zip")),
                                ("Workflow failure screenshot", Path("reports/screenshots/workflow-failure.png"))]:
            if artifact.exists():
                link = (label, Path(os.path.relpath(artifact.resolve(), root)).as_posix())
                if link not in entry["artifacts"]:
                    entry["artifacts"].append(link)


def pytest_sessionfinish(session, exitstatus):
    target = Path(session.config.getoption("report_path")).resolve()
    trace = Path("reports/traces/loan-and-transfers.zip")
    if session.config.getoption("run_integration") and trace.exists():
        link = ("Workflow trace", Path(os.path.relpath(trace.resolve(), target.parent)).as_posix())
        for entry in session.config._bank_results.values():
            if "test_workflows.py::test_scenario_" in entry["name"] and "scenario_c" not in entry["name"]:
                if link not in entry["artifacts"]:
                    entry["artifacts"].append(link)
    write_dashboard(list(session.config._bank_results.values()),
                    target, int(exitstatus))
