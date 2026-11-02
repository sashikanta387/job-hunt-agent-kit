#!/bin/bash
# Health check: scripts/doctor.sh   Prints what's working and the exact command to fix anything that isn't.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
cd "$REPO"
PROBLEMS=0
ok()   { printf '✅ %s\n' "$*"; }
bad()  { printf '⚠️  %s\n     fix: %s\n' "$1" "$2"; PROBLEMS=$((PROBLEMS + 1)); }
info() { printf '   %s\n' "$*"; }

echo "Job Hunt Agent Kit health check"
[ "$(uname)" = "Darwin" ] && ok "macOS" || bad "Not macOS: the daily resume refresh needs launchd" "use a Mac"

CFG="config/settings.yaml"
if [ ! -f "$CFG" ]; then
  bad "No settings yet" "./start.sh"; echo; echo "1 problem. Run the fix above first."; exit 1
fi
ok "Settings file found"

PY="$KIT/.venv/bin/python"
if [ -x "$PY" ] && "$PY" -c 'import yaml, playwright, docx' 2>/dev/null; then
  ok "Python environment ($KIT/.venv)"
else
  bad "Python environment missing or incomplete" "./setup.sh"; PY=python3
fi

if OUT="$("$PY" scripts/validate_config.py "$CFG" 2>&1)"; then
  ok "Settings are valid: $(tail -1 <<<"$OUT" | sed 's/^Settings OK. //')"
else
  bad "Settings have problems:" "./start.sh (choose Edit) or fix config/settings.yaml, then ./setup.sh"
  grep -E 'ERROR' <<<"$OUT" | sed 's/^ */     /'
fi

if [ -f "$KIT/settings.yaml" ] && cmp -s "$CFG" "$KIT/settings.yaml"; then
  ok "Installed copy of settings is up to date"
else
  bad "Settings changed since the last install" "./setup.sh"
fi

field() { "$PY" - "$CFG" "$1" 2>/dev/null <<'PY'
import sys, yaml
v = yaml.safe_load(open(sys.argv[1])) or {}
for k in sys.argv[2].split("."):
    v = v.get(k) if isinstance(v, dict) else None
print("" if v is None else v)
PY
}
BOARD="$(field board_url)"
if [ -z "$BOARD" ] || [[ "$BOARD" == *your-board-id* ]]; then
  bad "Job Hunt Board link not set" "publish the board (SETUP_WITH_CLAUDE.md step 6 or docs/BOARD.md), add it with ./start.sh"
else
  ok "Board: $BOARD"
fi
[ "$(field test_mode)" = "True" ] && info "Test mode is ON (agents log jobs, never submit)." || info "Test mode is OFF (live)."

if ls build/prompts/*.txt >/dev/null 2>&1; then
  if [ "$CFG" -nt build/prompts/coordinator.txt ]; then
    bad "Agent prompts are older than your settings" "./setup.sh, then paste the new build/prompts/*.txt into the Claude tasks"
  else
    ok "Agent prompts rendered (build/prompts)"
  fi
else
  bad "Agent prompts not rendered yet" "./setup.sh"
fi

if [ -f "$KIT/PAUSED" ]; then
  bad "Resume refresh is PAUSED since $(cat "$KIT/PAUSED")" "./scripts/resume.sh"
fi

LOADED="$(command -v launchctl >/dev/null && launchctl list 2>/dev/null | grep jobhuntkit || true)"
for p in naukri hirist instahyre talent500; do
  [ "$(field "portals.$p.enabled")" = "True" ] || continue
  echo "-- $p"
  if grep -q "com.jobhuntkit.$p-refresh" <<<"$LOADED"; then ok "Daily refresh job loaded"; else bad "Daily refresh job not loaded" "./setup.sh"; fi
  if [ "$p" = talent500 ] && ! grep -q "com.jobhuntkit.talent500-keepalive" <<<"$LOADED"; then
    bad "Talent500 keep-alive job not loaded" "./setup.sh"
  fi
  if [ -s "$KIT/state/${p}_state.json" ]; then ok "Signed in (session saved)"; else bad "Not signed in" "./scripts/login.sh $p"; fi
  if [ -s "$KIT/logs/$p.log" ]; then info "last log: $(tail -1 "$KIT/logs/$p.log")"; else info "no log yet (runs at the first refresh time)"; fi
done

echo
if [ "$PROBLEMS" -eq 0 ]; then echo "All good."; else echo "$PROBLEMS thing(s) to fix. Run the fix commands above, then ./scripts/doctor.sh again."; fi
[ "$PROBLEMS" -eq 0 ]
