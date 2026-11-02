#!/bin/bash
# Sign in to a portal once (and again whenever its session expires):  scripts/login.sh <portal>
# A real browser window opens. You type the password/OTP yourself; the session is saved locally
# in <install_dir>/state and then today's upload runs once.
set -uo pipefail
PORTAL="${1:-}"
case "$PORTAL" in naukri|hirist|instahyre|talent500) ;; *) echo "usage: $0 naukri|hirist|instahyre|talent500"; exit 1;; esac
source "$(dirname "$0")/lib.sh"
PY="$KIT/.venv/bin/python"
[ -x "$PY" ] || { echo "Run ./setup.sh first."; exit 1; }
eval "$("$PY" "$KIT/refresh/kit.py" env "$PORTAL")" || exit 1
[ -n "$KIT_RESUME" ] || { echo "No resume found for $PORTAL. Check resumes in settings.yaml and re-run setup.sh."; exit 1; }
mkdir -p "$(dirname "$KIT_STATE")" "$(dirname "$KIT_LOG")"
export KIT_HEADLESS=0
"$PY" "$KIT/refresh/${PORTAL}_refresh.py" --login --dry-run || { echo "Sign-in was not completed."; exit 1; }
echo "Session saved. Running today's upload now..."
FORCE=1 /bin/bash "$KIT/refresh/run_daily.sh" "$PORTAL"
tail -4 "$KIT_LOG"
