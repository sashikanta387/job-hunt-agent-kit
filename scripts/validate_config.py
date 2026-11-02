#!/usr/bin/env python3
"""Check config/settings.yaml before setup or after edits.
Usage: python3 scripts/validate_config.py [path/to/settings.yaml]
Exit 0 = OK (warnings are printed but don't fail), 1 = errors to fix."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "refresh"))
import kit  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
    try:
        s = kit.load(path)
    except FileNotFoundError:
        print(f"Not found: {path}. Run ./setup.sh to create it.")
        return 1
    except Exception as e:  # noqa: BLE001  (YAML syntax errors etc.)
        print(f"Could not read {path}: {e}")
        return 1
    errs, warns = kit.validate(s), kit.warnings(s)
    for w in warns:
        print(f"  warning: {w}")
    for e in errs:
        print(f"  ERROR: {e}")
    if errs:
        print(f"{len(errs)} problem(s) in {path}. Fix them and run again.")
        return 1
    mode = "TEST MODE (search + log only)" if s.get("test_mode") else "LIVE (agents may submit applications)"
    portals = ", ".join(p for p, c in (s.get("portals") or {}).items() if (c or {}).get("enabled")) or "none"
    print(f"Settings OK. Mode: {mode}. Enabled portals: {portals}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
