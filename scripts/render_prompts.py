#!/usr/bin/env python3
"""Fill the agent prompt templates and the starting strategy from settings.yaml.

Usage: python3 scripts/render_prompts.py [path/to/settings.yaml]
Writes build/prompts/{coordinator,inbox_interview,strategist}.txt  (paste into Claude scheduled tasks)
and    build/strategy.json  (load into the board's agent/strategy doc, see docs/BOARD.md).
Fails if any {{placeholder}} is left unfilled."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "refresh"))
import kit  # noqa: E402

TITLES = kit.TITLES
APPLY_RULES = {
    "naukri": 'Naukri: direct "Apply" only (never "Apply on company site" - treat those as career-site jobs); answer chatbot questions from FACTS; confirm the success page before logging Applied.',
    "hirist": "Hirist: apply and answer screening questions from FACTS; confirm the applied/success page.",
    "instahyre": "Instahyre: use \"Interested\"/apply on matching opportunities; answer from FACTS.",
    "talent500": "Talent500: apply and answer screening questions from FACTS.",
    "linkedin": 'LinkedIn: Easy Apply only; untick "follow company"; answer from FACTS.',
}
BOARD_PLATFORMS = ["Career site", "Referral", "Recruiter / email", "Agency"]
PH = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def bullets(items) -> str:
    return "\n".join(f"- {x}" for x in items if str(x).strip())


def money(s: dict) -> str:
    amt, cur = kit.get(s, "search.salary_floor.amount"), kit.get(s, "search.salary_floor.currency", "")
    return f"{amt:,} {cur} per year".strip() if isinstance(amt, (int, float)) else str(amt)


def context(s: dict) -> dict:
    c = s.get("candidate") or {}
    srch = s.get("search") or {}
    name = c.get("name", "")
    enabled = [p for p in kit.ALL_PORTALS if kit.portal(s, p).get("enabled")]
    roles = srch.get("target_roles") or []
    locs = srch.get("locations") or []
    loc_text = " / ".join(locs) + " (onsite or hybrid)"
    if srch.get("remote_ok"):
        loc_text += f" or remote within {srch.get('remote_region') or 'your country'}"
    years = c.get("years") or {}
    links = [c.get(k) for k in ("linkedin_url", "github_url", "portfolio_url") if c.get(k)]
    facts = [f"{c.get('current_role')} at {c.get('current_company')}, {c.get('home_city')}, {c.get('current_role_period')}."]
    facts += list(c.get("facts") or [])
    facts += [f"Notice period: {srch.get('notice_period')}. Current CTC: {srch.get('current_ctc')}; expected: {srch.get('expected_ctc')}.",
              f"Headline: {c.get('headline')}"]
    if links:
        facts.append("Links: " + ", ".join(links))
    screening = ["Years: " + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in years.items()),
                 f"Notice period: {srch.get('notice_period')}; location: {c.get('home_city')}"]
    screening += list(c.get("screening_extra") or [])
    test_mode = bool(s.get("test_mode", True))
    drive = (s.get("google_drive_folder_url") or "").strip()
    ws = Path(str(s.get("workspace_folder") or "~/JobHunt")).name
    sub = str(s.get("repo_subpath") or "").strip("/")
    mount = f"~/mnt/{ws}" + (f"/{sub}" if sub else "")
    mac_repo = str(s.get("workspace_folder") or "~/JobHunt").rstrip("/") + (f"/{sub}" if sub else "")
    role_map = kit.get(s, "resumes.role_map") or {}
    fams = kit.get(s, "resumes.families") or {}
    rm_text = "; ".join(f"{k} -> {Path(str((fams.get(v) or ['?'])[0])).name}" for k, v in role_map.items()) or "use the default master resume"

    if test_mode:
        test_rule = ("TEST MODE IS ON. Search and evaluate jobs exactly as described, but NEVER click a final "
                     "submit/apply button on any job site. "
                     'Log each matching job on the board with status "To apply" and notes starting "[test mode]". '
                     "Everything else (reading mail, drafts, tailored resumes, the email to the candidate, logging, the report) runs normally.")
        auth = "none while test mode is on - log matches instead of applying."
    else:
        test_rule = "LIVE MODE: applications may be submitted under the standing authorization below."
        auth = (f"{name} has set test_mode to false in their settings, which authorizes you to SUBMIT applications, "
                f"without asking first, to Easy Apply / direct-apply jobs on {', '.join(TITLES[p] for p in enabled)} "
                "that match the profile, rules and guardrails below. Applying to matching jobs is the main purpose of this run.")
    if drive:
        drive_step = (f"F) GOOGLE DRIVE: upload today's tailored resumes (.pdf + .docx) to the folder {drive} inside a subfolder "
                      f"\"Tailored_Resumes_<YYYY-MM-DD>\" (create it once, reuse if it exists). Stage the files with device_stage_files "
                      f"(ToolSearch \"select:mcp__remote-devices__device_stage_files\"; {mount}/X in device_bash is {mac_repo}/X on the Mac), "
                      "then follow docs/GOOGLE_DRIVE.md in the repo: Claude in Chrome, confirm the signed-in account, temporary file input + "
                      "drop event, verify each file appears exactly once, close the tab. Only create folders and upload files there; never delete, "
                      "move, rename or share anything in Drive, and never upload files containing passwords, ID numbers or salary slips. "
                      'If Chrome or Google is not available, skip and log blocker "Drive upload skipped".')
        drive_ref, drive_note = "Do step F (Drive upload) for these files. ", ", plus the Drive folder link for today's resumes"
    else:
        drive_step, drive_ref, drive_note = "(Google Drive upload is not configured; skip it.)", "", ""

    return {
        "name": name,
        "first_name": name.split()[0] if name else "the candidate",
        "email": c.get("email", ""),
        "home_city": c.get("home_city", ""),
        "target_roles": " / ".join(roles),
        "locations_text": loc_text,
        "salary_floor": money(s),
        "current_ctc": str(srch.get("current_ctc", "")),
        "expected_ctc": str(srch.get("expected_ctc", "")),
        "notice_period": str(srch.get("notice_period", "")),
        "min_years": str(srch.get("min_years_required", 0)),
        "skip_companies": ", ".join(srch.get("skip_companies") or []) or "(none)",
        "timezone": str(s.get("timezone", "")),
        "board_url": str(s.get("board_url", "")),
        "apply_portals": ", ".join(TITLES[p] for p in enabled) or "(none enabled)",
        "portal_apply_rules": "\n".join(f"   - {APPLY_RULES[p]}" for p in enabled),
        "board_platforms": ", ".join([TITLES[p] for p in kit.ALL_PORTALS] + BOARD_PLATFORMS),
        "role_map": rm_text,
        "facts_block": bullets(facts),
        "screening_block": bullets(screening),
        "achievements": bullets(c.get("achievements") or c.get("facts") or []),
        "never_claim": ", ".join(c.get("never_claim") or []) or "anything not listed in FACTS",
        "why_change": str(c.get("why_change", "")),
        "test_mode_rule": test_rule,
        "authorization": auth,
        "tailor_cmd": f"{mount}/tools/tailor_resume.py",
        "drive_step": drive_step,
        "drive_ref": drive_ref,
        "drive_email_note": drive_note,
    }


def fill(text: str, ctx: dict) -> str:
    return PH.sub(lambda m: ctx.get(m.group(1), m.group(0)), text)


def strategy(s: dict, ctx: dict) -> dict:
    srch = s.get("search") or {}
    enabled = [p for p in kit.ALL_PORTALS if kit.portal(s, p).get("enabled")]
    weights = {TITLES[p]: round(1 / len(enabled), 2) for p in enabled}
    if weights:   # make them sum to exactly 1
        first = next(iter(weights))
        weights[first] = round(1 - sum(v for k, v in weights.items() if k != first), 2)
    roles, locs = srch.get("target_roles") or [], srch.get("locations") or []
    loc_q = ", ".join(locs + (["remote"] if srch.get("remote_ok") else []))
    searches = {TITLES[p]: [f"{r} | {loc_q} | posted last 2 days" for r in roles] for p in enabled}
    fams = kit.get(s, "resumes.families") or {}
    resume_map = {k: Path(str((fams.get(v) or ["?"])[0])).name for k, v in (kit.get(s, "resumes.role_map") or {}).items()}
    resume_map["career-site jobs"] = "tailor with tools/tailor_resume.py"
    avoid = [f"pay clearly below {ctx['salary_floor']}",
             f"roles hard-requiring: {ctx['never_claim']}",
             f"junior roles (under {ctx['min_years']} years)", "reposts / already applied"] + list(srch.get("skip_companies") or [])
    goal = (f"Land interviews (and an offer) for {ctx['target_roles']} roles paying at least {ctx['salary_floor']}, "
            f"{ctx['locations_text']}. Target: 3+ new interview calls per week.")
    values = {"goal": goal, "platform_weights": weights, "searches": searches,
              "resume_map": resume_map, "avoid": avoid}
    seed = json.loads((ROOT / "board" / "seed" / "strategy.json").read_text())

    def walk(v):
        if isinstance(v, str):
            m = PH.fullmatch(v.strip())
            return values[m.group(1)] if m and m.group(1) in values else fill(v, {**ctx, **{k: str(x) for k, x in values.items()}})
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        return v
    return walk(seed)


def main() -> int:
    cfg = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "config" / "settings.yaml"
    s = kit.load(cfg)
    ctx = context(s)
    out = ROOT / "build" / "prompts"
    out.mkdir(parents=True, exist_ok=True)
    left = []
    for tpl in sorted((ROOT / "agents" / "templates").glob("*.md")):
        text = fill(tpl.read_text(), ctx)
        left += [f"{tpl.name}: {m}" for m in PH.findall(text)]
        (out / f"{tpl.stem}.txt").write_text(text)
    strat = json.dumps(strategy(s, ctx), indent=2, ensure_ascii=False)
    left += [f"strategy.json: {m}" for m in PH.findall(strat)]
    (ROOT / "build" / "strategy.json").write_text(strat + "\n")
    if left:
        print("Unfilled placeholders:\n  " + "\n  ".join(left))
        return 1
    tz = s.get("timezone")
    print(f"Wrote {out}/*.txt and build/strategy.json")
    print("Suggested schedules (see docs/AGENTS.md):")
    print(f"  Job hunt coordinator    CRON_TZ={tz} 26 10 * * 1-5   (weekdays 10:26)")
    print(f"  Inbox & interview agent CRON_TZ={tz} 27 8,18 * * *   (daily 08:27 and 18:27)")
    print(f"  Weekly job hunt review  CRON_TZ={tz} 55 18 * * 0     (Sundays 18:55)")
    if s.get("test_mode"):
        print("  test_mode is ON: the coordinator will log matches but not submit applications.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
