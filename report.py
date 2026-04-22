#!/usr/bin/env python3


import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

#status helper

STATUS_COLOUR = {
    "OK":       ("#22c55e", "#f0fdf4", "✅"),
    "WARNING":  ("#f59e0b", "#fffbeb", "⚠️"),
    "CRITICAL": ("#ef4444", "#fef2f2", "🔴"),
}


def badge(status: str) -> str:
    colour, _, icon = STATUS_COLOUR.get(status, ("#6b7280", "#f9fafb", "❓"))
    return (
        f'<span style="background:{colour};color:#fff;'
        f'padding:2px 10px;border-radius:12px;font-size:0.78rem;'
        f'font-weight:600;letter-spacing:0.04em">'
        f'{icon} {status}</span>'
    )


def pct_bar(value: float, status: str) -> str:
    colour = STATUS_COLOUR.get(status, ("#6b7280",))[0]
    capped = min(float(value), 100)
    return (
        f'<div style="background:#e5e7eb;border-radius:6px;height:10px;width:120px;display:inline-block;vertical-align:middle">'
        f'<div style="background:{colour};width:{capped}%;height:100%;border-radius:6px"></div>'
        f'</div>'
    )


def load_records(log_path: str) -> list[dict]:
    records = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records



def compute_summary(records: list[dict]) -> dict:
    if not records:
        return {}
 
    cpu_vals  = [r["cpu"]["usage_pct"]  for r in records]
    mem_vals  = [r["memory"]["usage_pct"] for r in records]
    disk_vals = [r["disk"]["usage_pct"] for r in records]
 
    status_counts: dict[str, int] = defaultdict(int)
    for r in records:
        for metric in ("cpu", "memory", "disk"):
            s = r[metric]["status"]
            if s != "OK":
                status_counts[s] += 1
 
    return {
        "total_checks": len(records),
        "cpu":  {"avg": sum(cpu_vals)/len(cpu_vals),  "max": max(cpu_vals),  "min": min(cpu_vals)},
        "mem":  {"avg": sum(mem_vals)/len(mem_vals),  "max": max(mem_vals),  "min": min(mem_vals)},
        "disk": {"avg": sum(disk_vals)/len(disk_vals),"max": max(disk_vals), "min": min(disk_vals)},
        "alerts_warning":  status_counts["WARNING"],
        "alerts_critical": status_counts["CRITICAL"],
    }


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DevOps Watchdog — Health Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem;
  }}
  h1 {{ font-size: 1.6rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.25rem; }}
  .subtitle {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 2rem; }}
  .card {{
    background: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  .card-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: #64748b; font-weight: 600; margin-bottom: 1rem; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; }}
  .stat {{ text-align: center; }}
  .stat-value {{ font-size: 2rem; font-weight: 700; color: #f8fafc; line-height: 1; }}
  .stat-label {{ font-size: 0.75rem; color: #64748b; margin-top: 0.3rem; }}
  .stat-warn  {{ color: #f59e0b; }}
  .stat-crit  {{ color: #ef4444; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  th {{
    text-align: left; padding: 0.6rem 0.8rem;
    background: #0f172a; color: #64748b;
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
    border-bottom: 1px solid #334155;
  }}
  td {{ padding: 0.55rem 0.8rem; border-bottom: 1px solid #1e293b; vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #0f172a; }}
  .mono {{ font-family: 'SF Mono', 'Fira Code', monospace; }}
  .footer {{ text-align: center; color: #475569; font-size: 0.75rem; margin-top: 2rem; }}
  .dog {{ font-size: 1.3rem; }}
</style>
</head>
<body>
 
<h1><span class="dog">🐕</span> DevOps Watchdog</h1>
<p class="subtitle">Generated: {generated_at} &nbsp;|&nbsp; Host: {host} &nbsp;|&nbsp; Log: {log_file}</p>
 
<!-- Summary -->
<div class="card">
  <div class="card-title">Summary — {total_checks} checks recorded</div>
  <div class="stats-grid">
    <div class="stat">
      <div class="stat-value">{cpu_avg}%</div>
      <div class="stat-label">CPU avg</div>
    </div>
    <div class="stat">
      <div class="stat-value">{cpu_max}%</div>
      <div class="stat-label">CPU peak</div>
    </div>
    <div class="stat">
      <div class="stat-value">{mem_avg}%</div>
      <div class="stat-label">Memory avg</div>
    </div>
    <div class="stat">
      <div class="stat-value">{mem_max}%</div>
      <div class="stat-label">Memory peak</div>
    </div>
    <div class="stat">
      <div class="stat-value">{disk_avg}%</div>
      <div class="stat-label">Disk avg</div>
    </div>
    <div class="stat">
      <div class="stat-value {warn_class}">{alerts_warning}</div>
      <div class="stat-label">⚠️ Warnings</div>
    </div>
    <div class="stat">
      <div class="stat-value {crit_class}">{alerts_critical}</div>
      <div class="stat-label">🔴 Criticals</div>
    </div>
  </div>
</div>
 
<!-- Raw log table -->
<div class="card">
  <div class="card-title">Check History (newest first)</div>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>CPU %</th>
        <th>CPU Status</th>
        <th>Memory %</th>
        <th>Mem Detail</th>
        <th>Mem Status</th>
        <th>Disk %</th>
        <th>Disk Detail</th>
        <th>Disk Status</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</div>
 
<div class="footer">DevOps Watchdog &nbsp;·&nbsp; github.com/yourusername/devops-watchdog</div>
 
</body>
</html>
"""

ROW_TEMPLATE = """\
      <tr>
        <td class="mono">{ts}</td>
        <td>{cpu_bar} <strong>{cpu}%</strong></td>
        <td>{cpu_badge}</td>
        <td>{mem_bar} <strong>{mem}%</strong></td>
        <td style="color:#94a3b8">{mem_detail}</td>
        <td>{mem_badge}</td>
        <td>{disk_bar} <strong>{disk}%</strong></td>
        <td style="color:#94a3b8">{disk_detail}</td>
        <td>{disk_badge}</td>
      </tr>"""
 
# Build & write report 
def generate_report(log_path: str, output_path: str) -> None:
    records = load_records(log_path)
    if not records:
        print("[report.py] No records found — skipping report generation.")
        return
 
    summary = compute_summary(records)
    host = records[-1].get("host", "unknown")
 
    rows_html = "\n".join(
        ROW_TEMPLATE.format(
            ts          = r["timestamp"],
            cpu         = r["cpu"]["usage_pct"],
            cpu_bar     = pct_bar(r["cpu"]["usage_pct"],    r["cpu"]["status"]),
            cpu_badge   = badge(r["cpu"]["status"]),
            mem         = r["memory"]["usage_pct"],
            mem_bar     = pct_bar(r["memory"]["usage_pct"], r["memory"]["status"]),
            mem_detail  = r["memory"].get("detail", ""),
            mem_badge   = badge(r["memory"]["status"]),
            disk        = r["disk"]["usage_pct"],
            disk_bar    = pct_bar(r["disk"]["usage_pct"],   r["disk"]["status"]),
            disk_detail = r["disk"].get("detail", ""),
            disk_badge  = badge(r["disk"]["status"]),
        )
        for r in reversed(records)
    )
 
    warn_class = "stat-warn" if summary["alerts_warning"] > 0 else ""
    crit_class = "stat-crit" if summary["alerts_critical"] > 0 else ""
 
    html = HTML_TEMPLATE.format(
        generated_at     = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        host             = host,
        log_file         = Path(log_path).name,
        total_checks     = summary["total_checks"],
        cpu_avg          = f'{summary["cpu"]["avg"]:.1f}',
        cpu_max          = f'{summary["cpu"]["max"]:.1f}',
        mem_avg          = f'{summary["mem"]["avg"]:.1f}',
        mem_max          = f'{summary["mem"]["max"]:.1f}',
        disk_avg         = f'{summary["disk"]["avg"]:.1f}',
        alerts_warning   = summary["alerts_warning"],
        alerts_critical  = summary["alerts_critical"],
        warn_class       = warn_class,
        crit_class       = crit_class,
        rows             = rows_html,
    )
 
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"[report.py] Report written → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <log_file.json> <output.html>")
        sys.exit(1)
    generate_report(sys.argv[1], sys.argv[2])
