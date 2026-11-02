#!/usr/bin/env python3
"""Make a JD-tailored copy of your master resume. It only re-orders and re-words what is already
true: it never adds a skill or a claim that isn't in the master file or settings.yaml.

Usage: python3 tools/tailor_resume.py spec.json [--settings config/settings.yaml]
spec.json:
  {"company": "Example Ltd", "role": "Senior SDET",
   "headline": "Senior SDET | Playwright & API Automation | CI/CD",   (optional, keep under ~95 chars)
   "summary": "...",                    (optional; 4-6 sentences built only from your facts)
   "front_skills": ["Playwright", "API testing"],   (moved to the front of the skills line)
   "keywords": ["playwright", "api", "flaky"]}      (bullets mentioning these move up)
Settings used (tailor: section): base_resume, headline_paragraph, summary_heading, skills_heading,
bullets_start, bullets_end, output_dir; candidate.name and candidate.never_claim.
Writes <output_dir>/<YYYY-MM-DD>/<Name>_<Company>_<Role>.docx (+ .pdf if LibreOffice is
installed) and prints the paths.
"""
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "refresh"))
import kit  # noqa: E402


def set_text(p, text):
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def find(paras, text, starts=False):
    t = text.strip().lower()
    for i, p in enumerate(paras):
        v = p.text.strip().lower()
        if (v.startswith(t) if starts else v == t):
            return i
    return None


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    cfg = Path(args[args.index("--settings") + 1]) if "--settings" in args else ROOT / "config" / "settings.yaml"
    s = kit.load(cfg)
    t = s.get("tailor") or {}
    spec = json.loads(Path(args[0]).read_text())
    never = [n.lower() for n in kit.get(s, "candidate.never_claim", []) or []]

    # Guardrail: refuse text that mentions a skill you've said you don't have.
    for field in ("headline", "summary"):
        hits = [n for n in never if re.search(r"\b" + re.escape(n) + r"\b", spec.get(field, "").lower())]
        if hits:
            print(f"Refusing: {field} mentions never-claim skill(s): {', '.join(hits)}")
            return 2

    base = kit.expand(t.get("base_resume", ""))
    d = docx.Document(str(base))
    P = d.paragraphs

    if spec.get("headline"):
        set_text(P[int(t.get("headline_paragraph", 1))], spec["headline"])

    si = find(P, t.get("skills_heading", "CORE COMPETENCIES"))
    if si is not None and si + 1 < len(P):
        current = [x.strip() for x in P[si + 1].text.split(",") if x.strip()]
        known = {x.lower(): x for x in current}
        front = [known[f.lower()] for f in spec.get("front_skills", []) if f.lower() in known]
        dropped = [f for f in spec.get("front_skills", []) if f.lower() not in known]
        if dropped:
            print("Note: not in your skills line, so not added:", ", ".join(dropped), file=sys.stderr)
        set_text(P[si + 1], ", ".join(front + [x for x in current if x not in front]))

    if spec.get("summary"):
        mi = find(P, t.get("summary_heading", "PROFESSIONAL SUMMARY"))
        if mi is not None and mi + 1 < len(P):
            set_text(P[mi + 1], spec["summary"])

    start = find(P, t.get("bullets_start", ""), starts=True) if t.get("bullets_start") else None
    end = find(P, t.get("bullets_end", ""), starts=True) if t.get("bullets_end") else None
    if start is not None and end is not None and end > start + 1:
        kw = [k.lower() for k in spec.get("keywords", [])]
        idx = list(range(start + 1, end))
        order = sorted(idx, key=lambda i: (-sum(P[i].text.lower().count(k) for k in kw), idx.index(i)))
        anchor, els = P[start]._p, [P[i]._p for i in order]
        for e in els:
            e.getparent().remove(e)
        for e in reversed(els):
            anchor.addnext(e)

    out = kit.expand(t.get("output_dir", "~/JobHunt/tailored")) / str(datetime.date.today())
    out.mkdir(parents=True, exist_ok=True)
    clean = lambda x: re.sub(r"[^A-Za-z0-9]+", "_", x).strip("_")[:40]  # noqa: E731
    name = clean(kit.get(s, "candidate.name", "Resume"))
    fn = out / f"{name}_{clean(spec['company'])}_{clean(spec['role'])}.docx"
    d.save(str(fn))
    print(fn)
    soffice = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if Path(soffice).exists() or shutil.which("soffice"):
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(fn)],
                       capture_output=True, timeout=150)
        if fn.with_suffix(".pdf").exists():
            print(fn.with_suffix(".pdf"))
    else:
        print("(no LibreOffice found: PDF not created)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
