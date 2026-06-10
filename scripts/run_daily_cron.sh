#!/usr/bin/env bash
# Local/cloud daily runner (GitHub Secrets 권한 없을 때 대체)
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi
unset GOOGLE_ADS_LOGIN_CUSTOMER_ID
python3 scripts/daily_report.py >> reports/cron.log 2>&1
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] daily report done" >> reports/cron.log
