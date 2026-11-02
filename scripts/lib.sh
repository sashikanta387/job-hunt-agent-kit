# Sourced by the scripts in this folder. Sets REPO and KIT (the install dir from settings.yaml).
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIT="$(sed -n 's/^install_dir:[[:space:]]*"\{0,1\}\([^"#]*\)"\{0,1\}.*/\1/p' "$REPO/config/settings.yaml" 2>/dev/null | head -1 | sed 's/[[:space:]]*$//')"
KIT="${KIT:-~/.job-hunt-kit}"; KIT="${KIT/#\~/$HOME}"
