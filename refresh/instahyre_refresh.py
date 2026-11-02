#!/usr/bin/env python3
"""Daily Instahyre resume refresh: re-uploads your resume on instahyre.com so the profile shows
a fresh "Last updated" date.  Usage: instahyre_refresh.py [--login] [--dry-run]
Instahyre sits behind Cloudflare, which often blocks headless browsers; the runner then
retries in a visible window automatically."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Portal, body_text, log, now, run, wait_for_url  # noqa: E402

LOGIN_URL = "https://www.instahyre.com/login/"
PAGE_URL = "https://www.instahyre.com/candidate/profile/"
SEL_FILE = "#resume-input"
STAMP_RE = re.compile(r"Last updated on ([A-Z][a-z]{2} \d{1,2}, \d{4} at [0-9:]+ [AP]M)")


def stamp(page) -> str:
    m = STAMP_RE.search(body_text(page))
    return m.group(1) if m else ""


def wait_stamp(page, timeout_s: int = 15) -> None:
    for _ in range(timeout_s * 2):
        if STAMP_RE.search(body_text(page)):
            return
        page.wait_for_timeout(500)


def is_logged_in(page) -> bool:
    page.goto(PAGE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(SEL_FILE, state="attached", timeout=25_000)
        wait_stamp(page)
        return "login" not in page.url
    except PWTimeout:
        return False


def upload(page, resume: Path) -> None:
    before = stamp(page)
    log.info("Before: %s", before or "(none)")
    page.set_input_files(SEL_FILE, str(resume))   # uploads as soon as a file is picked
    d = now()
    today = f"{d:%b} {d.day}, {d.year}"            # e.g. "Oct 13, 2026"
    for _ in range(30):
        page.wait_for_timeout(1000)
        s = stamp(page)
        if s and s != before and s.startswith(today):
            break
    page.wait_for_timeout(2000)
    is_logged_in(page)                            # reload and verify on a fresh page
    after = stamp(page)
    log.info("After: %s", after)
    if not (after and after != before and after.startswith(today)):
        raise RuntimeError(f"Upload not confirmed (stamp '{after}')")


PORTAL = Portal(name="instahyre", title="Instahyre", login_url=LOGIN_URL, is_logged_in=is_logged_in,
                upload=upload, wait_signed_in=wait_for_url(r"instahyre\.com/candidate/"),
                describe=lambda page: f"current stamp {stamp(page) or '(none)'}")

if __name__ == "__main__":
    sys.exit(run(PORTAL))
