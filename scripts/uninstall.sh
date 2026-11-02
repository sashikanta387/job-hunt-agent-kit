#!/bin/bash
# Remove the launchd jobs. Keeps sessions, logs and the venv unless you pass --purge.
source "$(dirname "$0")/lib.sh"
for plist in "$HOME"/Library/LaunchAgents/com.jobhuntkit.*.plist; do
  [ -f "$plist" ] || continue
  launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
  rm -f "$plist"; echo "removed $(basename "$plist")"
done
if [ "${1:-}" = "--purge" ]; then
  case "$KIT" in "$HOME"/?*) rm -rf "$KIT"; echo "deleted $KIT (sessions, logs, venv)";; *) echo "refusing to delete '$KIT'";; esac
else
  echo "Kept $KIT (saved sessions, logs). Use --purge to delete it."
fi
echo "The Claude scheduled tasks and the board are not touched; disable or delete them in Claude."
