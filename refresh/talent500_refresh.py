#!/usr/bin/env python3
"""Daily Talent500 resume refresh: re-uploads your resume on talent500.com so the profile
counts as recently updated.  Usage: talent500_refresh.py [--login] [--dry-run]
Needs portals.talent500.profile_url in settings.yaml (passed in as KIT_PROFILE_URL)."""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NeedsHuman, Portal, body_text, log, run  # noqa: E402

LOGIN_URL = "https://talent500.com/signin/"
PAGE_URL = os.getenv("KIT_PROFILE_URL", "")
SEL_FILE = 'input[type="file"][accept*="docx"]'
UPLOAD_API = re.compile(r"/users/candidate/[^/]+/resume/")


def is_logged_in(page) -> bool:
    if not PAGE_URL:
        raise RuntimeError("portals.talent500.profile_url is not set in settings.yaml")
    page.goto(PAGE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(SEL_FILE, state="attached", timeout=30_000)
        return "/auth/" not in page.url and "/signin" not in page.url
    except PWTimeout:
        return False


def wait_signed_in(page, ctx) -> None:
    # signed in = the site has set its authToken cookie (works for OTP and "Continue with Google")
    deadline = time.time() + 300
    while not any(c["name"] == "authToken" and c["value"] for c in ctx.cookies("https://talent500.com")):
        if time.time() > deadline:
            raise NeedsHuman("Sign-in not completed within 5 minutes")
        page.wait_for_timeout(2000)
    page.wait_for_timeout(3000)


def upload(page, resume: Path) -> None:
    with page.expect_response(lambda r: UPLOAD_API.search(r.url) and r.request.method == "POST",
                              timeout=60_000) as info:
        page.set_input_files(SEL_FILE, str(resume))   # uploads as soon as a file is picked
    resp = info.value
    log.info("Upload API status: %s", resp.status)
    if not 200 <= resp.status < 300:
        raise RuntimeError(f"Upload rejected (HTTP {resp.status})")
    page.wait_for_timeout(3000)
    if not is_logged_in(page) or resume.suffix.lower() not in body_text(page).lower():
        raise RuntimeError("Upload not confirmed on the profile page")


PORTAL = Portal(name="talent500", title="Talent500", login_url=LOGIN_URL, is_logged_in=is_logged_in,
                upload=upload, wait_signed_in=wait_signed_in)

if __name__ == "__main__":
    sys.exit(run(PORTAL))
