"""Check actual rendered CSS and accessible dashboard filters in Chromium."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument("path", nargs="?", default="reports/index.html")
args = parser.parse_args()
target = Path(args.path).resolve()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chromium")
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(target.as_uri())
    expect(page.locator("h1")).to_have_css("color", "rgb(244, 128, 49)")
    expect(page.locator(".card").first).to_have_css("backdrop-filter", "blur(18px)")
    expect(page.locator(".passed").first).to_have_css("color", "rgb(244, 128, 49)")
    total = page.locator("tbody tr").count()
    for status in ("passed", "failed", "skipped"):
        button = page.locator(f'[data-filter="{status}"]')
        button.click()
        expect(button).to_have_attribute("aria-pressed", "true")
        expect(button).to_have_css("background-color", "rgb(244, 128, 49)")
        visible = page.locator("tbody tr:visible")
        assert visible.count() == page.locator(f'tbody tr[data-status="{status}"]').count()
    page.locator('[data-filter="all"]').click()
    assert page.locator("tbody tr:visible").count() == total
    page.screenshot(path=str(target.parent / "dashboard-desktop.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    expect(page.locator("h1")).to_be_visible()
    page.screenshot(path=str(target.parent / "dashboard-mobile.png"), full_page=True)
    browser.close()
print(f"Dashboard CSS and filter checks passed: {target}")
