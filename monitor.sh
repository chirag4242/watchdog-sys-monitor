#!/usr/bin/env bash

#----------------------------------------------------------------
# DevOps Watchdog — System Health Monitor
# Collects CPU, Memory & Disk metrics, fires alerts, logs to JSON
#-----------------------------------------_----------------------

set -euo pipefail 		#Strict Mode

#---------------------------Paths--------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/alerts.conf"
LOG_DIR="${SCRIPT_DIR}/logs"
REPORT_DIR="${SCRIPT_DIR}/reports"
LOG_FILE="${LOG_DIR}/metrics_$(date +%Y-%m-%d).json"

#---------------------------Load config-------------------------
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "[ERROR] Config file not found: $CONFIG_FILE"
  exit 1
fi
source "$CONFIG_FILE"

#----------------Colours (disabled when not a TTY)--------------
if [ -t 1 ]; then
  RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
  RED=''; YELLOW=''; GREEN=''; CYAN=''; BOLD=''; RESET=''
fi

#--------------------------Helpers-------------------------------
log()   { echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${RESET} $*"; }
ok()    { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
alert() { echo -e "${RED}[ALERT]${RESET} $*"; }
sep()   { echo -e "${BOLD}$(printf '─%.0s' {1..60})${RESET}"; }
 
mkdir -p "$LOG_DIR" "$REPORT_DIR"

#------------------------Metric: CPU usage-----------------------
get_cpu_usage() {
  local stat1 stat2 idle1 idle2 total1 total2
  read -ra stat1 < /proc/stat          # first sample
  sleep 1
  read -ra stat2 < /proc/stat          # second sample

  #------------------Metric: CPU usage-----------------------
  local idle1=${stat1[4]} idle2=${stat2[4]}
  local total1=0 total2=0

  for val in "${stat1[@]:1:7}"; do (( total1 += val )) || true; done
  for val in "${stat2[@]:1:7}"; do (( total2 += val )) || true; done
  
  local delta_total=$(( total2 - total1 ))
  local delta_idle=$(( idle2 - idle1 ))

  if (( delta_total == 0 )); then echo "0"; return; fi
 
  awk "BEGIN { printf \"%.1f\", (1 - $delta_idle / $delta_total) * 100 }"
}

#--------------------Metric: Memory usage----------------------
get_mem_usage() {
  local mem_total mem_available
  mem_total=$(awk '/^MemTotal:/  { print $2 }' /proc/meminfo)
  mem_available=$(awk '/^MemAvailable:/ { print $2 }' /proc/meminfo)
  awk "BEGIN { printf \"%.1f\", (1 - $mem_available / $mem_total) * 100 }"
}

get_mem_details() {
  local total_mb used_mb
  local mem_total mem_available
  mem_total=$(awk '/^MemTotal:/     { print $2 }' /proc/meminfo)
  mem_available=$(awk '/^MemAvailable:/ { print $2 }' /proc/meminfo)
  total_mb=$(( mem_total / 1024 ))
  used_mb=$(( (mem_total - mem_available) / 1024 ))
  echo "${used_mb}MB / ${total_mb}MB"
}

#--------------------Metric: Disk usage----------------------
get_disk_usage() {
  df / | awk 'NR==2 { gsub(/%/,""); print $5 }'
}
 
get_disk_details() {
  df -h / | awk 'NR==2 { print $3 " used / " $2 " total" }'
}


#------------------Determine status-----------------------
get_status() {
  local value="$1" warn_thresh="$2" crit_thresh="$3"
  local int_val
  int_val=$(printf "%.0f" "$value")
  if (( int_val >= crit_thresh )); then echo "CRITICAL"
  elif (( int_val >= warn_thresh )); then echo "WARNING"
  else echo "OK"
  fi
}

#------------------Append one record to the daily JSON log--------
write_json_log() {
  local ts="$1" cpu="$2" mem="$3" disk="$4"
  local cpu_status mem_status disk_status
  cpu_status=$(get_status  "$cpu"  "$CPU_WARN_THRESHOLD"  "$CPU_THRESHOLD")
  mem_status=$(get_status  "$mem"  "$MEM_WARN_THRESHOLD"  "$MEM_THRESHOLD")
  disk_status=$(get_status "$disk" "$DISK_WARN_THRESHOLD" "$DISK_THRESHOLD")
 
  cat >> "$LOG_FILE" <<EOF
{"timestamp":"${ts}","cpu":{"usage_pct":${cpu},"status":"${cpu_status}"},"memory":{"usage_pct":${mem},"status":"${mem_status}","detail":"$(get_mem_details)"},"disk":{"usage_pct":${disk},"status":"${disk_status}","detail":"$(get_disk_details)"},"host":"$(hostname)"}
EOF
}

#--------------Print check cycle--------------------------------
run_check() {
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
 
  sep
  log "Watchdog check — ${BOLD}$(hostname)${RESET}  |  $ts"
  sep
 
  log "Sampling CPU (1s interval)..."
  local cpu mem disk
  cpu=$(get_cpu_usage)
  mem=$(get_mem_usage)
  disk=$(get_disk_usage)
 
  local cpu_status mem_status disk_status
  cpu_status=$(get_status  "$cpu"  "$CPU_WARN_THRESHOLD"  "$CPU_THRESHOLD")
  mem_status=$(get_status  "$mem"  "$MEM_WARN_THRESHOLD"  "$MEM_THRESHOLD")
  disk_status=$(get_status "$disk" "$DISK_WARN_THRESHOLD" "$DISK_THRESHOLD")
 
  # CPU
  local cpu_line="CPU Usage:    ${BOLD}${cpu}%${RESET}  (warn≥${CPU_WARN_THRESHOLD}%  crit≥${CPU_THRESHOLD}%)"
  case "$cpu_status" in
    CRITICAL) alert "$cpu_line  → ${RED}CRITICAL${RESET}" ;;
    WARNING)  warn  "$cpu_line  → ${YELLOW}WARNING${RESET}" ;;
    *)        ok    "$cpu_line" ;;
  esac
 
  # Memory
  local mem_line="Memory Usage: ${BOLD}${mem}%${RESET}  ($(get_mem_details))  (warn≥${MEM_WARN_THRESHOLD}%  crit≥${MEM_THRESHOLD}%)"
  case "$mem_status" in
    CRITICAL) alert "$mem_line  → ${RED}CRITICAL${RESET}" ;;
    WARNING)  warn  "$mem_line  → ${YELLOW}WARNING${RESET}" ;;
    *)        ok    "$mem_line" ;;
  esac
 
  # Disk
  local disk_line="Disk Usage:   ${BOLD}${disk}%${RESET}  ($(get_disk_details))  (warn≥${DISK_WARN_THRESHOLD}%  crit≥${DISK_THRESHOLD}%)"
  case "$disk_status" in
    CRITICAL) alert "$disk_line  → ${RED}CRITICAL${RESET}" ;;
    WARNING)  warn  "$disk_line  → ${YELLOW}WARNING${RESET}" ;;
    *)        ok    "$disk_line" ;;
  esac
 
  write_json_log "$ts" "$cpu" "$mem" "$disk"
  log "Logged → $LOG_FILE"
 
  # Generate HTML report after every check
  if command -v python3 &>/dev/null; then
    python3 "${SCRIPT_DIR}/report.py" "$LOG_FILE" "$REPORT_DIR/report.html"
    log "Report → ${REPORT_DIR}/report.html"
  fi
 
  sep
}


#--------------Main Loop--------------------------------
log "DevOps Watchdog starting — interval: ${CHECK_INTERVAL}s"
log "Thresholds → CPU warn/crit: ${CPU_WARN_THRESHOLD}%/${CPU_THRESHOLD}%  |  MEM: ${MEM_WARN_THRESHOLD}%/${MEM_THRESHOLD}%  |  DISK: ${DISK_WARN_THRESHOLD}%/${DISK_THRESHOLD}%"
 
while true; do
  run_check
  sleep "$CHECK_INTERVAL"
done
