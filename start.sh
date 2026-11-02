#!/bin/bash
# Job Hunt Agent Kit - the one command for new users. Safe to run again any time.
#   1. checks your Mac has what it needs
#   2. asks you a few questions and writes config/settings.yaml (scripts/wizard.py)
#   3. installs everything (setup.sh)
#   4. signs you in to each job site, one at a time
#   5. shows what's next and copies each agent prompt to the clipboard when you're ready
set -uo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
CFG="$REPO/config/settings.yaml"
cd "$REPO"
hr() { printf '\n----- %s -----\n' "$*"; }
yn() {  # yn "question" Y|N  -> returns 0 for yes
  local def="$2" a; read -r -p "$1 $([ "$def" = Y ] && echo '[Y/n]' || echo '[y/N]') " a || a=""
  a="${a:-$def}"; [[ "$a" =~ ^[Yy] ]]
}

hr "Checking your Mac"
if [ "$(uname)" != "Darwin" ] && [ -z "${JHK_ALLOW_NON_MAC:-}" ]; then
  echo "This kit runs on macOS only (it schedules jobs with launchd)."; exit 1
fi
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  echo "Python 3.9 or newer is needed. Install it with:"
  echo "    xcode-select --install"
  echo "or download it from https://www.python.org/downloads/macos/ , then run ./start.sh again."; exit 1
fi
if ! command -v git >/dev/null; then
  echo "git is missing. Install Apple's developer tools with:  xcode-select --install"
  echo "then run ./start.sh again."; exit 1
fi
echo "OK: $(python3 --version), $(git --version | cut -d' ' -f1-3)"

# PyYAML for the wizard: use the kit's own venv (setup.sh reuses it), else a --user install.
VENV="$HOME/.job-hunt-kit/.venv"
WPY=python3
if ! python3 -c 'import yaml' 2>/dev/null; then
  if [ ! -x "$VENV/bin/python" ]; then
    echo "Preparing a private Python environment (one time)..."
    mkdir -p "$HOME/.job-hunt-kit" && chmod 700 "$HOME/.job-hunt-kit"
    python3 -m venv "$VENV" || true
  fi
  if [ -x "$VENV/bin/python" ] && { "$VENV/bin/python" -c 'import yaml' 2>/dev/null || "$VENV/bin/python" -m pip install --quiet pyyaml; }; then
    WPY="$VENV/bin/python"
  elif ! python3 -m pip install --quiet --user pyyaml; then
    echo "Couldn't install PyYAML. Check your internet connection and run ./start.sh again."; exit 1
  fi
fi

hr "Your settings"
if [ ! -f "$CFG" ]; then
  "$WPY" scripts/wizard.py || { echo "Settings were not saved. Run ./start.sh again when ready."; exit 1; }
elif yn "You already have settings. Edit them?" N; then
  "$WPY" scripts/wizard.py --edit || { echo "Fix the items above (./start.sh again), then continue."; exit 1; }
else
  echo "Keeping config/settings.yaml."
fi

hr "Installing (a few minutes the first time)"
./setup.sh || { echo; echo "Setup stopped. Read the message above, fix it, then run ./start.sh again."; exit 1; }

source "$REPO/scripts/lib.sh"
PY="$KIT/.venv/bin/python"
ENABLED="$("$PY" "$KIT/refresh/kit.py" enabled 2>/dev/null)"
if [ -n "$ENABLED" ]; then
  hr "Sign in to your job sites"
  echo "A browser window opens for each site. YOU type the password and OTP; nothing is stored except the session."
  for p in $ENABLED; do
    if [ -f "$KIT/state/${p}_state.json" ]; then
      yn "Already signed in to $p. Sign in again?" N || continue
    else
      yn "Sign in to $p now?" Y || { echo "  Later:  ./scripts/login.sh $p"; continue; }
    fi
    ./scripts/login.sh "$p" || echo "  Not finished. Try again later:  ./scripts/login.sh $p"
  done
fi

hr "Next: the board and the three Claude agents"
BOARD="$("$PY" "$KIT/refresh/kit.py" get board_url 2>/dev/null)"
TZ_NAME="$("$PY" "$KIT/refresh/kit.py" get timezone 2>/dev/null)"
if [ -z "$BOARD" ] || [[ "$BOARD" == *your-board-id* ]]; then
  cat <<MSG
1. Publish the Job Hunt Board: easiest is to paste the prompt in SETUP_WITH_CLAUDE.md into the
   Claude desktop app (it does steps 6-9 for you). By hand: docs/BOARD.md.
2. Run ./start.sh again and paste the board link when asked (choose "Edit" settings).
3. Then this script copies each agent prompt for you, or let Claude create the tasks.
Health check any time: ./scripts/doctor.sh
MSG
  exit 0
fi
echo "Board: $BOARD"
echo "Create one Claude scheduled task per prompt (details: docs/AGENTS.md), or let Claude do it"
echo "(SETUP_WITH_CLAUDE.md steps 7-9). Connect Gmail and Google Calendar to each task."
while IFS='|' read -r -u 3 file name cron; do
  [ -f "build/prompts/$file.txt" ] || continue
  printf '\n%s\n  schedule: CRON_TZ=%s %s\n' "$name" "$TZ_NAME" "$cron"
  if command -v pbcopy >/dev/null; then
    read -r -p "  Press Enter to copy the $name prompt (s = skip) " a || a=s
    [ "$a" = s ] && continue
    pbcopy < "build/prompts/$file.txt" && echo "  Copied. Paste it into a new scheduled task in Claude."
  else
    echo "  prompt file: build/prompts/$file.txt"
  fi
done 3<<'LIST'
coordinator|Job hunt coordinator|26 10 * * 1-5
inbox_interview|Inbox & interview agent|27 8,18 * * *
strategist|Weekly job hunt review|55 18 * * 0
LIST
printf '\nAll set. Keep test mode on for a week, then see docs/GETTING_STARTED.md step 11.\nHealth check: ./scripts/doctor.sh\n'
