# 🐕 Watchdog — System Health Monitor
 
[![CI](https://github.com/chirag4242/watchdog-sys-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/chirag4242/watchdog-sys-monitor/actions/workflows/ci.yml)
![Shell](https://img.shields.io/badge/Shell-Bash-4EAA25?logo=gnubash&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Alpine-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)
 
A lightweight, containerised system health monitor that tracks **CPU, Memory & Disk** usage, fires colour-coded alerts when thresholds are breached, streams JSON telemetry logs, and generates a self-contained **HTML dashboard** — all in a single Docker container.
 
---
 
## ✨ Features
 
| Feature | Detail |
|---|---|
| 📊 Metric collection | CPU (sampled via `/proc/stat`), Memory (`/proc/meminfo`), Disk (`df`) |
| 🚨 Three-level alerting | **OK → WARNING → CRITICAL** per metric, configurable thresholds |
| 🗂️ JSON logging | One JSON-line record per check, daily rotating files in `logs/` |
| 📄 HTML report | Self-contained dashboard auto-generated after every check into `reports/` |
| 🐳 Dockerised | Alpine-based image (~55 MB), volume-mounted outputs survive restarts |
| ⚙️ Zero-rebuild config | Tune thresholds in `alerts.conf` without touching code |
| 🔁 GitHub Actions CI | ShellCheck lint, flake8, Python unit test, Docker build — on every push |
 
---
 
## 🗂️ Project Structure
 
```
watchdog-sys-monitor/
├── monitor.sh              # Bash orchestrator — collect → alert → log → report
├── report.py               # Python HTML report generator
├── alerts.conf             # Threshold & interval configuration
├── Dockerfile              # python:3.11-alpine image
├── docker-compose.yml      # One-command run with volume mounts
├── .github/
│   └── workflows/
│       └── ci.yml          # CI: lint + test + Docker build
├── logs/                   # JSON telemetry (git-ignored)
└── reports/                # HTML reports  (git-ignored)
```
 
---
 
## 🚀 Quick Start
 
### Option A — Docker Compose (recommended)
 
```bash
git clone https://github.com/chirag4242/watchdog-sys-monitor.git
cd watchdog-sys-monitor
 
docker compose up --build
```
 
Logs appear in `./logs/` and the HTML report in `./reports/report.html`.
 
### Option B — Run directly on Linux
 
```bash
git clone https://github.com/chirag4242/watchdog-sys-monitor.git
cd watchdog-sys-monitor
 
chmod +x monitor.sh
./monitor.sh
```
 
> Requires: `bash`, `python3`, `df`, `awk` (standard on any Linux system)
 
---
 
## ⚙️ Configuration
 
Edit `alerts.conf` — no rebuild required when running via Docker Compose:
 
```bash
# alerts.conf
CPU_WARN_THRESHOLD=70     # Yellow warning above this %
CPU_THRESHOLD=85          # Red critical above this %
 
MEM_WARN_THRESHOLD=75
MEM_THRESHOLD=90
 
DISK_WARN_THRESHOLD=70
DISK_THRESHOLD=85
 
CHECK_INTERVAL=60         # Seconds between checks
```
 
---
 
## 🖥️ Sample Output
 
```
────────────────────────────────────────────────────────────
[2024-12-01 14:32:05] Watchdog check — docker-desktop  |  2024-12-01 14:32:05
────────────────────────────────────────────────────────────
[2024-12-01 14:32:05] Sampling CPU (1s interval)...
[OK]    CPU Usage:    12.4%  (warn≥70%  crit≥85%)
[OK]    Memory Usage: 58.3%  (4666MB / 8000MB)  (warn≥75%  crit≥90%)
[WARN]  Disk Usage:   72.0%  (72GB used / 100GB total)  (warn≥70%  crit≥85%)  → WARNING
[2024-12-01 14:32:06] Logged → logs/metrics_2024-12-01.json
[2024-12-01 14:32:06] Report → reports/report.html
```
 
### JSON log entry
 
```json
{
  "timestamp": "2024-12-01 14:32:06",
  "cpu":    { "usage_pct": 12.4, "status": "OK" },
  "memory": { "usage_pct": 58.3, "status": "OK",      "detail": "4666MB / 8000MB" },
  "disk":   { "usage_pct": 72.0, "status": "WARNING",  "detail": "72GB used / 100GB total" },
  "host": "docker-desktop"
}
```
 
---
 
## 🛠️ Tech Stack
 
| Tool | Role |
|---|---|
| **Bash** | Metric collection, alerting logic, main loop |
| **Python 3** | HTML report generation from JSON logs |
| **Docker** | Containerisation, portability |
| **Git + GitHub Actions** | Version control & CI pipeline |
 
---
 
## 🔭 Roadmap
 
- [ ] Email / Slack alert notifications
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] Per-process CPU/memory breakdown
- [ ] Multi-host support via SSH
---
 
## 📜 License
 
MIT — free to use and adapt.
