#!/bin/bash
# Job Hunt Agent Kit - one-time setup (macOS). Safe to run again after editing settings.yaml.
#   1. creates config/settings.yaml from the example (then stops so you can fill it in)
#   2. validates it
#   3. builds a Python venv in install_dir with Playwright + Chromium
#   4. copies the refresh scripts there and loads launchd jobs for the enabled portals
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CFG="$REPO/config/settings.yaml"
say() { printf '\n==> %s\n' "$*"; }

[ "$(uname)" = "Darwin" ] || echo "Warning: the scheduled refresh jobs use launchd and only run on macOS."
command -v python3 >/dev/null || { echo "python3 not found. Install it (e.g. 'xcode-select --install' or python.org) and re-run."; exit 1; }

if [ ! -f "$CFG" ]; then
  cp "$REPO/config/settings.example.yaml" "$CFG"
  say "Created config/settings.yaml"
  echo "Open it, replace the example values with your own, then run ./setup.sh again."
  exit 0
fi

# Read install_dir with plain python (PyYAML may not be installed yet).
KIT="$(python3 - "$CFG" <<'PY'
import os, re, sys
m = re.search(r'^install_dir:\s*"?([^"#\n]+)"?', open(sys.argv[1]).read(), re.M)
print(os.path.expanduser((m.group(1) if m else "~/.job-hunt-kit").strip()))
PY
)"
say "Install dir: $KIT"
mkdir -p "$KIT"/{refresh,state,logs,debug,resumes}
chmod 700 "$KIT" "$KIT/state"

if [ ! -x "$KIT/.venv/bin/python" ]; then
  say "Creating Python virtual environment"
  python3 -m venv "$KIT/.venv"
fi
PY="$KIT/.venv/bin/python"
say "Installing Python packages"
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r "$REPO/requirements.txt"
say "Installing Chromium for Playwright (skipped if already there)"
"$PY" -m playwright install chromium >/dev/null

say "Validating settings"
"$PY" "$REPO/scripts/validate_config.py" "$CFG"

say "Copying refresh scripts and settings"
cp "$REPO"/refresh/*.py "$REPO"/refresh/*.sh "$KIT/refresh/"
cp "$CFG" "$KIT/settings.yaml"
chmod 600 "$KIT/settings.yaml"
chmod +x "$KIT"/refresh/*.sh
"$PY" "$KIT/refresh/kit.py" sync-resumes >/dev/null

say "Scheduling launchd jobs"
AGENTS="$HOME/Library/LaunchAgents"; mkdir -p "$AGENTS"
load() {  # load <name> <template>
  local label="com.jobhuntkit.$1" plist="$AGENTS/com.jobhuntkit.$1.plist"
  "$PY" "$KIT/refresh/kit.py" plist "$1" "$2" "$label" > "$plist"
  if command -v launchctl >/dev/null; then
    launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$plist"
  fi
  echo "  loaded $label"
}
unload() {
  local plist="$AGENTS/com.jobhuntkit.$1.plist"
  [ -f "$plist" ] || return 0
  command -v launchctl >/dev/null && launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
  rm -f "$plist"; echo "  removed com.jobhuntkit.$1 (disabled in settings)"
}
ENABLED="$("$PY" "$KIT/refresh/kit.py" enabled)"
for p in naukri hirist instahyre talent500; do
  if grep -qx "$p" <<<"$ENABLED"; then
    load "$p-refresh" "$REPO/refresh/launchd/refresh.plist.template"
    [ "$p" = "talent500" ] && load "talent500-keepalive" "$REPO/refresh/launchd/keepalive.plist.template"
  else
    unload "$p-refresh"; [ "$p" = "talent500" ] && unload "talent500-keepalive"
  fi
done

say "Rendering agent prompts"
"$PY" "$REPO/scripts/render_prompts.py" "$CFG"

cat <<MSG

Done. Next steps:
  1. Sign in once per portal (a browser window opens; you type the OTP, not the script):
$(for p in $ENABLED; do echo "       ./scripts/login.sh $p"; done)
  2. Publish the Job Hunt Board and put its URL in settings.yaml  -> docs/BOARD.md
  3. Create the three Claude scheduled tasks from build/prompts/   -> docs/AGENTS.md
  Logs: $KIT/logs    Pause everything: ./scripts/pause.sh
After any change to settings.yaml, run ./setup.sh again.
MSG
