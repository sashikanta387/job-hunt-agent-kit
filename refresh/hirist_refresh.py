#!/usr/bin/env python3
"""Daily Hirist resume refresh: re-uploads your resume on hirist.tech so the profile shows a
fresh "Uploaded On" date.  Usage: hirist_refresh.py [--login] [--dry-run]"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Portal, body_text, log, now, run, wait_for_url  # noqa: E402

LOGIN_URL = "https://www.hirist.tech/login"
PAGE_URL = "https://www.hirist.tech/registration/addPersonalDetails"
SEL_FILE = "input[type=file]"
STAMP_RE = re.compile(r"Uploaded On:\s*([0-9-]+ [0-9:]+)")


def stamp(page) -> str:
    m = STAMP_RE.search(body_text(page))
    return m.group(1) if m else ""


def wait_stamp(page, timeout_s: int = 15) -> None:
    for _ in range(timeout_s * 2):           # the date renders a moment after the page
        if STAMP_RE.search(body_text(page)):
            return
        page.wait_for_timeout(500)


def is_logged_in(page) -> bool:
    page.goto(PAGE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(SEL_FILE, state="attached", timeout=20_000)
        wait_stamp(page)
        return "login" not in page.url
    except PWTimeout:
        return False


def upload(page, resume: Path) -> None:
    before = stamp(page)
    log.info("Before: %s", before or "(none)")
    page.set_input_files(SEL_FILE, str(resume))
    today = now().strftime("%d-%m-%Y")
    for _ in range(20):                       # Hirist usually saves on file pick
        page.wait_for_timeout(1000)
        s = stamp(page)
        if s and s != before and s.startswith(today):
            break
    else:                                     # otherwise save the form
        log.info("No new stamp yet; clicking Save")
        page.get_by_role("button", name=re.compile("Save", re.I)).first.click()
        page.wait_for_timeout(4000)
    is_logged_in(page)                        # reload and verify
    after = stamp(page)
    log.info("After: %s", after)
    if not (after and after != before and after.startswith(today)):
        raise RuntimeError(f"Upload not confirmed (stamp '{after}')")


PORTAL = Portal(name="hirist", title="Hirist", login_url=LOGIN_URL, is_logged_in=is_logged_in,
                upload=upload, wait_signed_in=wait_for_url(r"hirist\.tech/(jobfeed|myprofile|registration|j/|$)"),
                describe=lambda page: f"current stamp {stamp(page) or '(none)'}")

if __name__ == "__main__":
    sys.exit(run(PORTAL))
