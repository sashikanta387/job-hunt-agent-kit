#!/usr/bin/env python3
"""Settings loader and small helpers shared by setup.sh, the refresh jobs and scripts/*.py.

CLI (used by the shell scripts):
  kit.py env <portal>        print shell exports for one portal's daily run (picks today's resume)
  kit.py enabled             list portals with a resume refresh that are enabled
  kit.py plist <portal> <template> <label>   render a launchd plist template to stdout
  kit.py sync-resumes        copy master resumes into <install_dir>/resumes
  kit.py get <dotted.key>    print one setting (e.g. install_dir)

Settings file lookup: $KIT_SETTINGS, then <install_dir>/settings.yaml next to this file,
then ../config/settings.yaml (when run from the repo).
"""
from __future__ import annotations

import datetime as dt
import os
import shlex
import shutil
import sys
from pathlib import Path

import yaml

REFRESH_PORTALS = ["naukri", "hirist", "instahyre", "talent500"]   # have a resume-refresh job
ALL_PORTALS = REFRESH_PORTALS + ["linkedin"]
TITLES = {"naukri": "Naukri", "hirist": "Hirist", "instahyre": "Instahyre",
          "talent500": "Talent500", "linkedin": "LinkedIn"}
HERE = Path(__file__).resolve().parent


def expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(p))))


def settings_path() -> Path:
    if os.getenv("KIT_SETTINGS"):
        return expand(os.environ["KIT_SETTINGS"])
    for cand in (HERE.parent / "settings.yaml", HERE.parent / "config" / "settings.yaml"):
        if cand.exists():
            return cand
    return HERE.parent / "config" / "settings.yaml"


def load(path: Path | None = None) -> dict:
    path = path or settings_path()
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return data


def get(s: dict, dotted: str, default=None):
    cur = s
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def install_dir(s: dict) -> Path:
    return expand(s.get("install_dir") or "~/.job-hunt-kit")


def portal(s: dict, name: str) -> dict:
    return (s.get("portals") or {}).get(name) or {}


def enabled_refresh_portals(s: dict) -> list[str]:
    return [p for p in REFRESH_PORTALS if portal(s, p).get("enabled")]


def hhmm(v: str) -> tuple[int, int]:
    h, m = str(v).split(":")
    h, m = int(h), int(m)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(v)
    return h, m


# --- validation ---------------------------------------------------------------------------
def validate(s: dict) -> list[str]:
    errs: list[str] = []
    need = ["candidate.name", "candidate.email", "candidate.home_city", "candidate.headline",
            "search.target_roles", "search.locations", "search.salary_floor.amount",
            "search.salary_floor.currency", "search.notice_period", "timezone", "board_url"]
    for k in need:
        if get(s, k) in (None, "", []):
            errs.append(f"missing: {k}")
    if "@" not in str(get(s, "candidate.email", "")):
        errs.append("candidate.email does not look like an email address")
    if not isinstance(get(s, "candidate.facts"), list) or not get(s, "candidate.facts"):
        errs.append("candidate.facts must be a non-empty list (agents only use what is listed)")
    if not isinstance(get(s, "candidate.never_claim", []), list):
        errs.append("candidate.never_claim must be a list")
    years = get(s, "candidate.years", {})
    if not isinstance(years, dict) or not all(isinstance(v, (int, float)) for v in years.values()):
        errs.append("candidate.years must map skill -> number")
    if not isinstance(get(s, "search.salary_floor.amount"), (int, float)):
        errs.append("search.salary_floor.amount must be a number")
    if not isinstance(s.get("test_mode"), bool):
        errs.append("test_mode must be true or false")
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(str(s.get("timezone")))
    except Exception:
        errs.append(f"timezone '{s.get('timezone')}' is not a valid IANA name (e.g. Asia/Kolkata)")
    portals = s.get("portals") or {}
    for name, cfg in portals.items():
        if name not in ALL_PORTALS:
            errs.append(f"portals.{name}: unknown portal (supported: {', '.join(ALL_PORTALS)})")
            continue
        if not isinstance(cfg, dict) or not cfg.get("enabled") or name == "linkedin":
            continue
        times = cfg.get("refresh_times") or []
        if not times:
            errs.append(f"portals.{name}.refresh_times is empty")
        for t in times + [cfg.get("retry_until", "12:00")]:
            try:
                hhmm(t)
            except Exception:
                errs.append(f"portals.{name}: bad time '{t}' (use \"HH:MM\")")
        fam = cfg.get("resume_family")
        if fam not in (get(s, "resumes.families") or {}):
            errs.append(f"portals.{name}.resume_family '{fam}' is not in resumes.families")
        if name == "talent500" and "your-profile-id" in str(cfg.get("profile_url", "your-profile-id")):
            errs.append("portals.talent500.profile_url: paste your own profile URL")
    for fam, files in (get(s, "resumes.families") or {}).items():
        if not isinstance(files, list) or not files:
            errs.append(f"resumes.families.{fam} must be a non-empty list of file paths")
            continue
        for f in files:
            if Path(str(f)).suffix.lower() not in (".docx", ".pdf"):
                errs.append(f"resumes.families.{fam}: {f} must be .docx or .pdf")
    return errs


def warnings(s: dict) -> list[str]:
    out = []
    for fam, files in (get(s, "resumes.families") or {}).items():
        for f in files or []:
            msg = f"resume file not found (yet): {f}"
            if not expand(f).exists() and msg not in out:
                out.append(msg)
    if "your-board-id" in str(s.get("board_url", "")):
        out.append("board_url is still the example value; publish the board first (docs/BOARD.md)")
    return out


# --- resumes ------------------------------------------------------------------------------
def sync_resumes(s: dict) -> Path:
    """Copy master resumes into the install dir. launchd jobs often can't read ~/Desktop or
    ~/Documents (macOS privacy), so the jobs fall back to these copies."""
    dest = install_dir(s) / "resumes"
    dest.mkdir(parents=True, exist_ok=True)
    for files in (get(s, "resumes.families") or {}).values():
        for f in files or []:
            src = expand(f)
            try:
                tmp = dest / (src.name + ".tmp")
                shutil.copy2(src, tmp)
                tmp.replace(dest / src.name)
            except OSError:
                pass   # unreadable right now: keep the saved copy
    return dest


def todays_resume(s: dict, name: str) -> str:
    files = get(s, f"resumes.families.{portal(s, name).get('resume_family')}") or []
    if not files:
        return ""
    dest = sync_resumes(s)
    offset = REFRESH_PORTALS.index(name) if name in REFRESH_PORTALS else 0
    day = dt.date.today().timetuple().tm_yday + int(os.getenv("DAY_OFFSET", "0"))
    n = len(files)
    for k in range(n):
        cand = dest / expand(files[(day + offset + k) % n]).name
        if cand.exists():
            return str(cand)
    return ""


# --- CLI ----------------------------------------------------------------------------------
def cmd_env(s: dict, name: str) -> None:
    if name not in REFRESH_PORTALS:
        sys.exit(f"unknown refresh portal: {name}")
    cfg = portal(s, name)
    home = install_dir(s)
    h, m = hhmm(cfg.get("retry_until", "12:00"))
    pairs = {
        "KIT_HOME": str(home),
        "KIT_PORTAL": name,
        "KIT_TITLE": TITLES[name],
        "KIT_ENABLED": "1" if cfg.get("enabled") else "0",
        "KIT_RESUME": todays_resume(s, name),
        "KIT_STATE": str(home / "state" / f"{name}_state.json"),
        "KIT_SHOTS": str(home / "debug" / name),
        "KIT_LOG": str(home / "logs" / f"{name}.log"),
        "KIT_STAMP": str(home / "state" / f"{name}_last_success"),
        "KIT_HEADLESS_DEFAULT": "0" if cfg.get("headless") is False else "1",
        "KIT_CUTOFF_MIN": str(h * 60 + m),
        "KIT_CUTOFF": f"{h:02d}:{m:02d}",
        "KIT_TZ": str(s.get("timezone", "UTC")),
        "KIT_LOCALE": str(s.get("browser_locale", "en-US")),
        "KIT_PROFILE_URL": str(cfg.get("profile_url", "")),
    }
    for k, v in pairs.items():
        print(f"export {k}={shlex.quote(v)}")


def cmd_plist(s: dict, name: str, template: str, label: str) -> None:
    home = install_dir(s)
    if name.endswith("-keepalive"):
        minutes = int(portal(s, name.split("-")[0]).get("keepalive_minutes", 120))
        schedule = f"<key>StartInterval</key><integer>{minutes * 60}</integer>\n  <key>RunAtLoad</key><true/>"
    else:
        rows = []
        for t in portal(s, name).get("refresh_times", []):
            h, m = hhmm(t)
            rows.append(f"    <dict><key>Hour</key><integer>{h}</integer><key>Minute</key><integer>{m}</integer></dict>")
        schedule = "<key>StartCalendarInterval</key><array>\n" + "\n".join(rows) + "\n  </array>"
    text = Path(template).read_text()
    for k, v in {"LABEL": label, "KIT_HOME": str(home), "PORTAL": name.split("-")[0],
                 "SCHEDULE": schedule, "LOG_DIR": str(home / "logs")}.items():
        text = text.replace("{{" + k + "}}", v)
    sys.stdout.write(text)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    s = load()
    cmd = argv[0]
    if cmd == "env" and len(argv) == 2:
        cmd_env(s, argv[1])
    elif cmd == "enabled":
        print("\n".join(enabled_refresh_portals(s)))
    elif cmd == "plist" and len(argv) == 4:
        cmd_plist(s, argv[1], argv[2], argv[3])
    elif cmd == "sync-resumes":
        print(sync_resumes(s))
    elif cmd == "get" and len(argv) == 2:
        v = install_dir(s) if argv[1] == "install_dir" else get(s, argv[1], "")
        print(v)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
