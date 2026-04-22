#!/usr/bin/env python3
"""
DevOps Watchdog — HTML Report Generator
Reads the JSON-lines log file and produces a self-contained HTML report.

Usage:
    python3 report.py <log_file> <output_html>
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# Status helpers
STATUS_COLOUR = {
    "OK": ("#22c55e", "#f0fdf4", "✅"),
    "WARNING": ("#f59e0b", "#fffbeb", "⚠️"),
    "CRITICAL": ("#ef4444", "#fef2f2", "🔴"),
}


def badge(status: str) -> str:
    colour, _, icon = STATUS_COLOUR.get(
        status, ("#6b7280", "#f9fafb", "❓")
    )
    return (
        f'<span style="background:{colour};color:#fff;'
        f'padding:2px 10px;border-radius:12px;'
        f'font-size:0.78rem;font-weight:600;'
        f'letter-spacing:0.04em">'
        f'{icon} {status}</span>'
    )


def pct_bar(value: float, status: str) -> str:
    colour = STATUS_COLOUR.get(status, ("#6b7280",))[0]
    capped = min(float(value), 100)
    return (
        '<div style="background:#e5e7eb;border-radius:6px;'
        'height:10px;width:120px;display:inline-block;'
        'vertical-align:middle">'
        f'<div style="background:{colour};width:{capped}%;'
        'height:100%;border-radius:6px"></div>'
        '</div>'
    )


def load_records(log_path: str) -> list[dict]:
    records: list[dict] = []
    with open(log_path, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def compute_summary(records: list[dict]) -> dict:
    if not records:
        return {}

    cpu_vals = [r["cpu"]["usage_pct"] for r in records]
    mem_vals = [r["memory"]["usage_pct"] for r in records]
    disk_vals = [r["disk"]["usage_pct"] for r in records]

    status_counts: dict[str, int] = defaultdict(int)

    for record in records:
        for metric in ("cpu", "memory", "disk"):
            status = record[metric]["status"]
            if status != "OK":
                status_counts[status] += 1

    return {
        "total_checks": len(records),
        "cpu": {
            "avg": sum(cpu_vals) / len(cpu_vals),
            "max": max(cpu_vals),
            "min": min(cpu_vals),
        },
        "mem": {
            "avg": sum(mem_vals) / len(mem_vals),
            "max": max(mem_vals),
            "min": min(mem_vals),
        },
        "disk": {
            "avg": sum(disk_vals) / len(disk_vals),
            "max": max(disk_vals),
            "min": min(disk_vals),
        },
        "alerts_warning": status_counts["WARNING"],
        "alerts_critical": status_counts["CRITICAL"],
    }


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Watchdog — System Health Report</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a; color: #e2e8f0; padding: 2rem;
  }}
  h1 {{ color: #f8fafc; }}
  .card {{
    background: #1e293b; border-radius: 12px;
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 0.6rem; border-bottom: 1px solid #334155; }}
</style>
</head>
<body>

<h1>🐕 DevOps Watchdog</h1>
<p>Generated: {generated_at} | Host: {host} | Log: {log_file}</p>

<div class="card">
  <strong>Checks:</strong> {total_checks} |
  CPU avg: {cpu_avg}% |
  Memory avg: {mem_avg}% |
  Disk avg: {disk_avg}%
</div>

<div class="card">
<table>
<thead>
<tr>
<th>Timestamp</th>
<th>CPU</th>
<th>Status</th>
<th>Memory</th>
<th>Status</th>
<th>Disk</th>
<th>Status</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</div>

</body>
</html>
"""


ROW_TEMPLATE = """\
<tr>
<td>{ts}</td>
<td>{cpu}%</td>
<td>{cpu_badge}</td>
<td>{mem}%</td>
<td>{mem_badge}</td>
<td>{disk}%</td>
<td>{disk_badge}</td>
</tr>
"""


def generate_report(log_path: str, output_path: str) -> None:
    records = load_records(log_path)

    if not records:
        print("[report.py] No records found — skipping report.")
        return

    summary = compute_summary(records)
    host = records[-1].get("host", "unknown")

    rows_html = "\n".join(
        ROW_TEMPLATE.format(
            ts=r["timestamp"],
            cpu=r["cpu"]["usage_pct"],
            cpu_badge=badge(r["cpu"]["status"]),
            mem=r["memory"]["usage_pct"],
            mem_badge=badge(r["memory"]["status"]),
            disk=r["disk"]["usage_pct"],
            disk_badge=badge(r["disk"]["status"]),
        )
        for r in reversed(records)
    )

    html = HTML_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        host=host,
        log_file=Path(log_path).name,
        total_checks=summary["total_checks"],
        cpu_avg=f'{summary["cpu"]["avg"]:.1f}',
        mem_avg=f'{summary["mem"]["avg"]:.1f}',
        disk_avg=f'{summary["disk"]["avg"]:.1f}',
        rows=rows_html,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")

    print(f"[report.py] Report written → {output_path}")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <log_file.json> <output.html>")
        sys.exit(1)

    generate_report(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
