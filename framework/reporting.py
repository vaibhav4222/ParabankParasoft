"""Bespoke standalone HTML dashboard; no stock HTML reporter dependency."""
import html
import json
from datetime import datetime, timezone
from pathlib import Path


def format_duration(seconds: float) -> str:
    if seconds == 0:
        return "0ms"
    if 0 < seconds < 0.00001:
        return "<0.01ms"
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    return f"{seconds:.2f}s"


def write_dashboard(results: list[dict], target: Path, exit_code: int):
    target.parent.mkdir(parents=True, exist_ok=True)
    counts = {status: sum(r["status"] == status for r in results)
              for status in ("passed", "failed", "skipped")}
    cards = ''.join(f'<section class="glass card"><span>{label}</span><strong>{value}</strong></section>'
                    for label, value in [("Total", len(results)), ("Passed", counts["passed"]),
                                         ("Failed", counts["failed"]), ("Skipped", counts["skipped"])])
    rows = []
    for result in results:
        detail = f'<details><summary>Failure details</summary><pre>{html.escape(result["detail"])}</pre></details>' if result.get("detail") else ''
        artifacts = ''.join(f'<a href="{html.escape(link, quote=True)}">{html.escape(label)}</a> '
                            for label, link in result.get("artifacts", []))
        rows.append(f'<tr data-status="{result["status"]}"><td>{html.escape(result["name"])}{detail}{artifacts}</td>'
                    f'<td class="{result["status"]}">{result["status"].upper()}</td><td>{html.escape(format_duration(result["duration"]))}</td></tr>')
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ParaBank QA | Test Dashboard</title>
<style>
:root{--accent:#F48031;--text:#f4f6fb;--muted:#b7bfd1}*{box-sizing:border-box}
body{margin:0;min-height:100vh;font:16px system-ui,sans-serif;color:var(--text);background:radial-gradient(ellipse at 8% 5%,#64391f 0,transparent 45%),radial-gradient(ellipse at 95% 80%,#253354 0,transparent 48%),#111521}
main{max-width:1200px;margin:auto;padding:48px 24px}header{display:flex;justify-content:space-between;gap:20px;align-items:center}h1{color:var(--accent);margin:8px 0;font-size:clamp(28px,4vw,44px)}p,small{color:var(--muted)}
.glass{background:rgba(255,255,255,.075);border:1px solid rgba(255,255,255,.19);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);box-shadow:0 12px 40px #0004;border-radius:20px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:32px 0}.card{padding:24px}.card span{display:block;color:var(--muted)}.card strong{display:block;font-size:40px;color:var(--accent);margin-top:12px}
.panel{padding:24px;overflow:auto}nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px}button{cursor:pointer;background:transparent;border:1px solid #ffffff40;border-radius:9px;padding:9px 16px;color:var(--text);font:inherit}button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#111521}button:focus-visible{outline:3px solid white;outline-offset:3px}
table{width:100%;border-collapse:collapse;text-align:left}th{color:var(--muted);font-size:13px;text-transform:uppercase;letter-spacing:1px}td,th{padding:16px 10px;border-bottom:1px solid #ffffff19}td:first-child{overflow-wrap:anywhere}.passed{color:var(--accent)}.failed{color:#ff8585}.skipped{color:#d5c594}pre{white-space:pre-wrap;font-size:12px;color:#ffd0d0}summary{cursor:pointer;margin-top:12px}a{color:var(--accent)}footer{margin-top:24px;color:var(--muted);font-size:13px}
@media(max-width:640px){.cards{grid-template-columns:repeat(2,1fr)}header{display:block}main{padding:24px 12px}.panel{padding:14px}}
</style></head><body><main><header><div><small>QUALITY ENGINEERING / PARABANK</small><h1>Automation dashboard</h1><p>API &amp; UI hybrid validation</p></div><small>__TIME__<br>Session exit code: __EXIT__</small></header>
<div class="cards">__CARDS__</div><section class="glass panel"><nav aria-label="Filter test results">
<button type="button" aria-pressed="true" data-filter="all">All tests</button><button type="button" aria-pressed="false" data-filter="passed">Passed</button><button type="button" aria-pressed="false" data-filter="failed">Failed</button><button type="button" aria-pressed="false" data-filter="skipped">Skipped</button></nav>
<table><thead><tr><th scope="col">Test / scenario</th><th scope="col">Status</th><th scope="col">Duration</th></tr></thead><tbody>__ROWS__</tbody></table></section>
<footer>Custom pytest reporter · Money reconciled in integer cents · Accent #F48031</footer></main>
<script>document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));document.querySelectorAll('tbody tr').forEach(row=>row.hidden=button.dataset.filter!=='all'&&row.dataset.status!==button.dataset.filter)}));</script></body></html>'''
    for key, value in {"__TIME__": timestamp, "__EXIT__": str(exit_code), "__CARDS__": cards, "__ROWS__": ''.join(rows)}.items():
        document = document.replace(key, value)
    target.write_text(document, encoding="utf-8")
    target.with_suffix(".json").write_text(json.dumps({"generated_at": timestamp, "exit_code": exit_code,
                                                     "counts": counts, "tests": results}, indent=2), encoding="utf-8")
