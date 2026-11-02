#!/bin/bash
# Started by launchd every keepalive_minutes: extends the Talent500 session.
# Notifies (once a day) only when a manual sign-in is needed.
APP="$(cd "$(dirname "$0")" && pwd)"; KIT="$(dirname "$APP")"; PY="$KIT/.venv/bin/python"
[ -f "$KIT/PAUSED" ] && exit 0
eval "$("$PY" "$APP/kit.py" env talent500)" || exit 1
[ "$KIT_ENABLED" = "1" ] || exit 0
mkdir -p "$(dirname "$KIT_LOG")"
"$PY" "$APP/talent500_keepalive.py" >> "$KIT_LOG" 2>&1; code=$?
FLAG="$KIT/state/.talent500_notified_$(date +%F)"
if [ $code -eq 3 ] && [ ! -f "$FLAG" ]; then
  touch "$FLAG"
  /usr/bin/osascript -e 'display notification "Session ended. Run scripts/login.sh talent500" with title "Talent500 sign-in needed"' >/dev/null 2>&1
fi
exit $code
