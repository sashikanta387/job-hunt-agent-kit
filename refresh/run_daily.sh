#!/bin/bash
# Daily resume refresh for one portal, started by launchd:  run_daily.sh <portal>
# - Exactly one upload a day: a later launchd slot exits at once if today's upload is done.
# - A failed attempt retries every 10 minutes until the portal's retry_until time.
# - First attempt headless (unless the portal needs a visible browser), later ones visible.
# - A file named PAUSED in the install dir stops everything (scripts/pause.sh).
# FORCE=1 runs one attempt now, ignoring the "already done today" stamp (used by login.sh).

PORTAL="${1:?usage: run_daily.sh <portal>}"
APP="$(cd "$(dirname "$0")" && pwd)"            # <install_dir>/refresh
KIT="$(dirname "$APP")"
PY="$KIT/.venv/bin/python"

[ -f "$KIT/PAUSED" ] && [ "${FORCE:-0}" != "1" ] && exit 0
eval "$("$PY" "$APP/kit.py" env "$PORTAL")" || exit 1
mkdir -p "$(dirname "$KIT_LOG")" "$(dirname "$KIT_STATE")"
TODAY="$(date +%Y-%m-%d)"

notify() { /usr/bin/osascript -e "display notification \"$1\" with title \"$KIT_TITLE resume refresh\"" >/dev/null 2>&1; }
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$KIT_LOG"; }

if [ "$KIT_ENABLED" != "1" ] && [ "${FORCE:-0}" != "1" ]; then
  log "$PORTAL is disabled in settings.yaml; skipping."; exit 0
fi
if [ "$(cat "$KIT_STAMP" 2>/dev/null)" = "$TODAY" ] && [ "${FORCE:-0}" != "1" ]; then
  log "Scheduled run fired; today's upload is already done, so skipping."; exit 0
fi
if [ -z "$KIT_RESUME" ]; then
  log "No resume file found for $PORTAL"; notify "No resume file found. Check resumes in settings.yaml."; exit 1
fi
log "Today's resume: $(basename "$KIT_RESUME")"

# Optional fallback credentials (Naukri only) from the macOS Keychain, never from a file:
#   security add-generic-password -s jobhuntkit-naukri -a you@example.com -w
if [ "$PORTAL" = "naukri" ]; then
  NAUKRI_EMAIL="$(security find-generic-password -s jobhuntkit-naukri 2>/dev/null | sed -n 's/.*"acct"<blob>="\(.*\)"/\1/p')"
  NAUKRI_PASSWORD="$(security find-generic-password -s jobhuntkit-naukri -w 2>/dev/null)"
  export NAUKRI_EMAIL NAUKRI_PASSWORD
fi

# Talent500: extend the login first (no OTP needed while the refresh token is valid).
[ "$PORTAL" = "talent500" ] && "$PY" "$APP/talent500_keepalive.py" >> "$KIT_LOG" 2>&1

[ "${FORCE:-0}" = "1" ] || sleep $((RANDOM % 120))   # don't hit the site at the same second every day

now_min() { echo $(( 10#$(date +%H)*60 + 10#$(date +%M) )); }
attempt=1
while :; do
  if [ "${FORCE:-0}" != "1" ] && [ "$(now_min)" -gt "$KIT_CUTOFF_MIN" ]; then
    log "Past the $KIT_CUTOFF cutoff; no more attempts today."; exit 0
  fi
  if [ $attempt -eq 1 ]; then export KIT_HEADLESS="$KIT_HEADLESS_DEFAULT"; else export KIT_HEADLESS=0; fi
  log "Run started (attempt $attempt)"
  "$PY" "$APP/${PORTAL}_refresh.py" >> "$KIT_LOG" 2>&1
  code=$?
  if [ $code -eq 0 ]; then
    echo "$TODAY" > "$KIT_STAMP"; log "Upload confirmed"; notify "Resume uploaded to $KIT_TITLE for $TODAY."; exit 0
  elif [ $code -eq 4 ]; then
    log "Paused."; exit 0
  elif [ $code -eq 3 ]; then
    log "Needs a manual sign-in (attempt $attempt)"
    notify "$KIT_TITLE needs you to sign in: run scripts/login.sh $PORTAL"
  else
    log "Run failed (exit $code, attempt $attempt)"
  fi
  [ "${FORCE:-0}" = "1" ] && exit $code                 # manual run: one attempt only
  if [ $(( $(now_min) + 10 )) -gt "$KIT_CUTOFF_MIN" ]; then
    log "No retry slot left before $KIT_CUTOFF; today's upload missed."
    notify "$KIT_TITLE upload failed today. See $KIT_LOG"
    exit $code
  fi
  [ $code -ne 3 ] && notify "$KIT_TITLE upload failed (attempt $attempt). Retrying in 10 minutes."
  log "Retrying in 10 minutes"; sleep 600; attempt=$((attempt + 1))
done
