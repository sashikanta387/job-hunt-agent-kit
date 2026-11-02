#!/usr/bin/env python3
"""Daily Naukri resume refresh: uploads your resume on naukri.com/mnjuser/profile once a day
so the profile's "last updated" date stays current in recruiter searches.

  python naukri_refresh.py --login     # first run: visible browser, you finish OTP/captcha
  python naukri_refresh.py             # daily run, reuses the saved session
  python naukri_refresh.py --dry-run   # check the session only, no upload
Optional: NAUKRI_EMAIL / NAUKRI_PASSWORD (run_daily.sh reads them from the macOS Keychain,
service "jobhuntkit-naukri") let it sign in again when the session expires and no OTP is asked.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NeedsHuman, Portal, log, now, run, wait_for_url  # noqa: E402

LOGIN_URL = "https://www.naukri.com/nlogin/login"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
SEL_FILE_INPUT = "input#attachCV"
SEL_UPLOADED_ON = ".updateOn"            # "Uploaded on Oct 02, 2026"
SEL_FILE_NAME = ".truncate.exten"        # current resume file name
SEL_USER = "#usernameField, input[placeholder*='Email' i]"
SEL_PASS = "#passwordField, input[type='password']"
SEL_SUBMIT = "button[type='submit']"
SEL_OTP_OR_CAPTCHA = "input[name*='otp' i], input[id*='otp' i], iframe[src*='captcha' i], iframe[title*='captcha' i]"
SIGNED_IN = r"naukri\.com/(mnjuser|myapply|recommendedjobs|home)"


def is_logged_in(page) -> bool:
    page.goto(PROFILE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(SEL_FILE_INPUT, state="attached", timeout=15_000)
        return True
    except PWTimeout:
        return False


def auto_login(page) -> None:
    email, password = os.getenv("NAUKRI_EMAIL"), os.getenv("NAUKRI_PASSWORD")
    if not (email and password):
        return
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.locator(SEL_USER).first.fill(email, timeout=20_000)
    page.locator(SEL_PASS).first.fill(password)
    page.locator(SEL_SUBMIT).first.click()
    try:
        page.wait_for_url(re.compile(SIGNED_IN), timeout=30_000)
    except PWTimeout:
        if page.locator(SEL_OTP_OR_CAPTCHA).count():
            raise NeedsHuman("Naukri wants an OTP or captcha. Run: scripts/login.sh naukri")
        raise RuntimeError(f"Login did not complete (still on {page.url}).")


def upload(page, resume: Path) -> None:
    page.goto(PROFILE_URL, wait_until="domcontentloaded")
    page.wait_for_selector(SEL_FILE_INPUT, state="attached", timeout=30_000)
    log.info("Before: %s", page.locator(SEL_UPLOADED_ON).first.inner_text(timeout=10_000).strip())
    page.set_input_files(SEL_FILE_INPUT, str(resume))
    toast = page.get_by_text(re.compile(r"(successfully uploaded|uploaded successfully|success)", re.I)).first
    try:
        toast.wait_for(state="visible", timeout=30_000)
        log.info("Naukri confirmed the upload.")
    except PWTimeout:
        log.warning("No success toast seen; checking the page instead.")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector(SEL_UPLOADED_ON, timeout=30_000)
    after = page.locator(SEL_UPLOADED_ON).first.inner_text().strip()
    name = page.locator(SEL_FILE_NAME).first.inner_text().strip()
    log.info("After: %s | file: %s", after, name)
    if now().strftime("%b %d, %Y") not in after or name != resume.name:
        raise RuntimeError(f"Upload not confirmed (stamp '{after}', file '{name}').")


PORTAL = Portal(name="naukri", title="Naukri", login_url=LOGIN_URL, is_logged_in=is_logged_in,
                upload=upload, wait_signed_in=wait_for_url(SIGNED_IN), auto_login=auto_login)

if __name__ == "__main__":
    sys.exit(run(PORTAL))
