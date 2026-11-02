#!/usr/bin/env python3
"""Interactive setup: asks plain questions and writes config/settings.yaml for you.

Usage:  python3 scripts/wizard.py            (start.sh runs this for you)
        python3 scripts/wizard.py --reset    start again from the example file
        python3 scripts/wizard.py --config PATH --resume-dest DIR   (testing)
Press Enter to accept the value in [brackets]."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "refresh"))
try:
    import yaml
    import kit
except ImportError:
    sys.exit("PyYAML is missing. Run ./start.sh (it installs it), or: python3 -m pip install --user pyyaml")

EOF = False
HOME = str(Path.home())


def tilde(p) -> str:
    p = str(p)
    return "~" + p[len(HOME):] if p == HOME or p.startswith(HOME + os.sep) else p


def read(prompt: str) -> str:
    global EOF
    try:
        return input(prompt).strip()
    except EOFError:
        EOF = True
        print()
        return ""


def ask(q: str, default="", required=False, check=None, hint=""):
    """Ask once; Enter keeps the default. check(value) returns (ok, value_or_message)."""
    while True:
        shown = f" [{default}]" if str(default) != "" else ""
        val = read(f"{q}{shown}: ") or str(default)
        if required and not val:
            msg = "This one is needed."
        elif check:
            ok, out = check(val)
            if ok:
                return out
            msg = out
        else:
            return val
        if EOF:
            sys.exit(f"Stopped: '{q}' still needs an answer. Nothing was written.")
        print(f"  {msg} {hint}".rstrip())


def yes(q: str, default=True) -> bool:
    ans = ask(q + (" (Y/n)" if default else " (y/N)"), "", check=lambda v: (True, v.lower()))
    return default if not ans else ans.startswith("y")


def lines(q: str, keep: list, lo=1, hi=8) -> list:
    if keep:
        print(q)
        for x in keep:
            print(f"   - {x}")
        if yes("Keep these?"):
            return keep
    while True:
        print(f"{q} One per line, {lo}-{hi} lines. Leave a line empty to finish.")
        out = []
        while len(out) < hi:
            line = read(f"  {len(out) + 1}. ")
            if not line:
                break
            out.append(line)
        if len(out) >= lo:
            return out
        if EOF:
            sys.exit("Stopped: at least one line is needed. Nothing was written.")
        print(f"  Please add at least {lo}.")


def csv(v: str) -> list:
    return [x.strip() for x in v.split(",") if x.strip()]


def is_email(v):
    return (True, v) if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v) else (False, "That doesn't look like an email address.")


def number(v):
    s = v.lower().replace(",", "").replace(" ", "")
    mult = 100000 if re.search(r"(l|lpa|lakh|lakhs)$", s) else 1
    s = re.sub(r"(lpa|lakhs|lakh|l)$", "", s)
    try:
        n = float(s) * mult
        return True, int(n) if n == int(n) else n
    except ValueError:
        return False, "Please type a number, e.g. 2000000 or 20 LPA."


def zone(v):
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(v)
        return True, v
    except Exception:
        return False, "Not a known timezone name (examples: Asia/Kolkata, Europe/London)."


def detect_tz() -> str:
    try:
        link = os.readlink("/etc/localtime")
        if "zoneinfo/" in link:
            return link.split("zoneinfo/", 1)[1]
    except OSError:
        pass
    try:
        out = subprocess.run(["systemsetup", "-gettimezone"], capture_output=True, text=True, timeout=5).stdout
        if ":" in out:
            return out.split(":", 1)[1].strip()
    except Exception:
        pass
    return "Asia/Kolkata"


def years_text(y: dict) -> str:
    return ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in y.items() if k != "total")


def parse_years(v: str):
    out = {}
    for part in csv(v):
        m = re.fullmatch(r"(.+?)\s+(\d+(?:\.\d+)?)", part)
        if not m:
            return False, f"Couldn't read '{part}'. Use 'skill number', e.g. playwright 3."
        n = float(m.group(2))
        out[re.sub(r"\W+", "_", m.group(1).lower()).strip("_")] = int(n) if n == int(n) else n
    return True, out


def pick_resumes(dest: Path, current: dict):
    """Returns (families, files_to_copy). files_to_copy = [(src, dst)]."""
    if current and not yes("Change your resume files?", default=False):
        return current, []
    while True:
        folder = Path(os.path.expanduser(ask("Folder that has your resume files (.docx)", "~/Downloads"))).resolve()
        found = sorted(p for p in folder.glob("*") if p.suffix.lower() in (".docx", ".pdf") and not p.name.startswith("~$"))
        if found:
            break
        print(f"  No .docx or .pdf files in {folder}.")
        if EOF:
            sys.exit("Stopped: no resume files found. Nothing was written.")
    for i, p in enumerate(found, 1):
        print(f"   {i}. {p.name}")

    def nums(v, allow_blank=False):
        if allow_blank and not v:
            return True, []
        try:
            idx = [int(x) for x in csv(v)]
            if idx and all(1 <= i <= len(found) for i in idx):
                return True, [found[i - 1] for i in idx]
        except ValueError:
            pass
        return False, f"Type numbers from the list, e.g. 1 or 1,2."

    lead = ask("Resume(s) for LEAD / manager roles (numbers, e.g. 1 or 1,2)", "1", check=nums)
    sdet = ask("Resume(s) for SDET / hands-on roles (Enter = use the lead one)", "", check=lambda v: nums(v, True))
    copies, fams = [], {}
    for fam, files in (("lead", lead), ("sdet", sdet or lead[:1])):
        fams[fam] = []
        for src in files:
            dst = dest / src.name
            if (src, dst) not in copies:
                copies.append((src, dst))
            fams[fam].append(tilde(dst))
    return fams, copies


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ROOT / "config" / "settings.yaml"), help="settings file to write")
    ap.add_argument("--reset", action="store_true", help="ignore current settings and start from the example")
    ap.add_argument("--edit", action="store_true", help="edit current settings without asking first")
    ap.add_argument("--resume-dest", default="~/JobHunt/resumes", help="where your resume files get copied")
    a = ap.parse_args()
    cfg = Path(a.config).expanduser()
    example = yaml.safe_load((ROOT / "config" / "settings.example.yaml").read_text())
    editing = cfg.exists() and not a.reset
    if editing and not a.edit and not yes(f"You already have {tilde(cfg)}. Edit it (your answers become the defaults)?"):
        print("Nothing changed. Use --reset to start over.")
        return 0
    s = kit.load(cfg) if editing else example
    old = s if editing else {}          # defaults for personal answers come only from YOUR file
    g = lambda key, fb="": kit.get(old, key, fb) if kit.get(old, key) not in (None, "") else fb  # noqa: E731

    print("\nJob Hunt Agent Kit setup. Press Enter to keep the value in [brackets].\n\n-- About you --")
    c = {**(example["candidate"]), **(s.get("candidate") or {})}
    c["name"] = ask("Your full name", g("candidate.name"), True)
    c["email"] = ask("Email for reports and interview briefs (your Gmail)", g("candidate.email"), True, is_email)
    c["home_city"] = ask("City you live in", g("candidate.home_city"), True)
    c["current_role"] = ask("Current (or last) job title, as on your offer letter", g("candidate.current_role"), True)
    c["current_company"] = ask("Company", g("candidate.current_company"), True)
    c["current_role_period"] = ask("Dates in that role, e.g. Jan 2020 - present", g("candidate.current_role_period"))
    c["headline"] = ask("One-line headline for job sites", g("candidate.headline", c["current_role"]), True)
    c["linkedin_url"] = ask("LinkedIn profile link (optional)", g("candidate.linkedin_url"))
    c["github_url"] = ask("GitHub link (optional)", g("candidate.github_url"))
    c["portfolio_url"] = g("candidate.portfolio_url")
    print("\nFacts: the agents may ONLY claim what you write here. Short and true, e.g.")
    print("   '7 years in QA, 5 in automation'  /  'Built Playwright UI + API suites run in GitHub Actions'")
    c["facts"] = lines("Your facts:", g("candidate.facts", []), 3 if not editing else 1)
    c["achievements"] = g("candidate.achievements", [])
    total = ask("Total years of experience", g("candidate.years.total", ""), True, number)
    yrs = ask("Years per skill, e.g. 'automation 5, playwright 3, api testing 4' (optional)",
              years_text(g("candidate.years", {})), check=lambda v: parse_years(v) if v else (True, {}))
    c["years"] = {"total": total, **yrs}
    c["never_claim"] = csv(ask("Tools you have NOT used (comma-separated; jobs needing them are skipped)",
                               ", ".join(g("candidate.never_claim", []))))
    c["why_change"] = ask("One positive line: why are you looking for a change?",
                          g("candidate.why_change", "Looking for a role with broader ownership and growth."))
    c["screening_extra"] = g("candidate.screening_extra", [f"Willing to work from office in {c['home_city']}", "Open to face-to-face interviews"])

    print("\n-- What you're looking for --")
    sr = {**example["search"], **(s.get("search") or {})}
    sr["target_roles"] = csv(ask("Job titles you want (comma-separated)", ", ".join(g("search.target_roles", [])), True))
    sr["locations"] = csv(ask("Cities you'd work in (comma-separated)", ", ".join(g("search.locations", [c["home_city"]])), True))
    sr["remote_ok"] = yes("Also consider remote jobs?", bool(g("search.remote_ok", True)))
    sr["remote_region"] = ask("Remote within which country/region", g("search.remote_region", "India")) if sr["remote_ok"] else ""
    sr["salary_floor"] = {"currency": ask("Salary currency", g("search.salary_floor.currency", "INR"), True)}
    sr["salary_floor"]["amount"] = ask("Lowest yearly salary you'd accept (e.g. 2000000 or 20 LPA)",
                                       g("search.salary_floor.amount", ""), True, number)
    sr["current_ctc"] = ask("Current CTC, as you write it on forms (e.g. 16 LPA)", g("search.current_ctc"), True)
    sr["expected_ctc"] = ask("Expected CTC (e.g. 21 LPA)", g("search.expected_ctc"), True)
    sr["notice_period"] = ask("Notice period (e.g. Immediate, 30 days)", g("search.notice_period"), True)
    sr["min_years_required"] = ask("Skip jobs asking for fewer years than", g("search.min_years_required", max(int(total) - 3, 0)), check=number)
    sr["skip_companies"] = csv(ask("Companies to never apply to (comma-separated, optional)", ", ".join(g("search.skip_companies", []))))

    print("\n-- Schedule and job sites --")
    tz = ask("Your timezone", g("timezone", detect_tz()), True, zone)
    portals = {**example["portals"], **(s.get("portals") or {})}
    for p in kit.ALL_PORTALS:
        pc = dict(portals.get(p) or {})
        pc["enabled"] = yes(f"Use {kit.TITLES[p]}?", bool(pc.get("enabled")))
        if p == "talent500" and pc["enabled"]:
            cur = str(pc.get("profile_url", ""))
            pc["profile_url"] = ask("Your Talent500 profile link (open your profile, copy the address)",
                                    "" if "your-profile-id" in cur else cur, True)
        portals[p] = pc
    test_mode = yes("Keep TEST MODE on (log jobs, never submit)? Recommended for the first week", bool(s.get("test_mode", True))) if editing else True

    print("\n-- Resumes --")
    dest = Path(os.path.expanduser(a.resume_dest))
    fams, copies = pick_resumes(dest, g("resumes.families", {}))
    for p in kit.REFRESH_PORTALS:
        if portals[p].get("resume_family") not in fams:
            portals[p]["resume_family"] = "lead"
    board = ask("Job Hunt Board link (Enter to skip; you'll add it after publishing the board)",
                "" if "your-board-id" in str(s.get("board_url", "")) else s.get("board_url", ""))

    s = dict(s)
    s.update(candidate=c, search=sr, timezone=tz, portals=portals, test_mode=test_mode,
             board_url=board or "https://claude.ai/artifact/your-board-id",
             workspace_folder=tilde(ROOT.parent), repo_subpath=ROOT.name)
    s.setdefault("resumes", {})
    s["resumes"]["families"] = fams
    if copies or not editing:
        s["resumes"]["role_map"] = {"Lead / Test Lead / Manager": "lead", "SDET / Automation Engineer": "sdet"}
        docx = [f for f in fams["lead"] if f.lower().endswith(".docx")]
        s["tailor"] = {**example["tailor"], **(s.get("tailor") or {}), "base_resume": docx[0] if docx else ""}
    if not editing:
        s["google_drive_folder_url"] = ""

    on = [kit.TITLES[p] for p in kit.ALL_PORTALS if portals[p]["enabled"]]
    print(f"""
-- Please check --
  {c['name']} <{c['email']}>, {c['home_city']}; {c['current_role']} at {c['current_company']}
  Facts: {len(c['facts'])} lines; never claim: {', '.join(c['never_claim']) or '(none)'}
  Looking for: {', '.join(sr['target_roles'])} in {', '.join(sr['locations'])}{' + remote' if sr['remote_ok'] else ''}
  Salary floor: {sr['salary_floor']['amount']:,} {sr['salary_floor']['currency']}; CTC {sr['current_ctc']} -> {sr['expected_ctc']}; notice {sr['notice_period']}
  Timezone: {tz}; job sites: {', '.join(on) or 'none'}; test mode: {'ON' if test_mode else 'OFF (live)'}
  Resumes: lead = {', '.join(Path(f).name for f in fams['lead'])}; sdet = {', '.join(Path(f).name for f in fams['sdet'])}""")
    if not yes("\nSave these settings?"):
        print("Nothing was written.")
        return 1
    if copies:
        dest.mkdir(parents=True, exist_ok=True)
        for src, dst in copies:
            if not (dst.exists() and src.samefile(dst)):
                shutil.copy2(src, dst)
        print(f"Copied {len(copies)} resume file(s) to {tilde(dest)}")
    cfg.parent.mkdir(parents=True, exist_ok=True)
    tmp = cfg.with_suffix(".tmp")
    header = ("# Job Hunt Agent Kit settings, written by scripts/wizard.py. Re-run ./start.sh to change them,\n"
              "# or edit by hand (field notes: config/settings.example.yaml). Never commit this file.\n")
    tmp.write_text(header + yaml.safe_dump(s, sort_keys=False, allow_unicode=True, width=1000))
    tmp.replace(cfg)
    print(f"Saved {tilde(cfg)}")
    errs = kit.validate(kit.load(cfg))
    for w in kit.warnings(kit.load(cfg)):
        print(f"  note: {w}")
    for e in errs:
        print(f"  needs fixing: {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled. Nothing was written.")
        sys.exit(130)
