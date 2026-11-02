#!/usr/bin/env python3
"""Template for a new portal refresh job. Copy to refresh/<portal>_refresh.py and fill in the
TODOs. See CONTRIBUTING.md for the other places to register the portal.

  python <portal>_refresh.py --login     # visible browser, you sign in once
  python <portal>_refresh.py --dry-run   # check the saved session
  python <portal>_refresh.py             # daily upload
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Portal, body_text, log, now, run, wait_for_url  # noqa: E402,F401

LOGIN_URL = "https://example-portal.com/login"         # TODO
PAGE_URL = "https://example-portal.com/profile"         # TODO: page with the resume upload input
SEL_FILE = "input[type=file]"                           # TODO: the resume <input type=file>
STAMP_RE = re.compile(r"Updated on (.+)")               # TODO: the "last updated" text, if shown
SIGNED_IN_URL = r"example-portal\.com/(profile|jobs)"   # TODO: URL you land on after signing in


def stamp(page) -> str:
    m = STAMP_RE.search(body_text(page))
    return m.group(1).strip() if m else ""


def is_logged_in(page) -> bool:
    """Open the upload page; True if the file input is there (i.e. not bounced to login)."""
    page.goto(PAGE_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(SEL_FILE, state="attached", timeout=20_000)
        return "login" not in page.url
    except PWTimeout:
        return False


def upload(page, resume: Path) -> None:
    """Pick the file, then PROVE it worked (new stamp, success toast or API response).
    Raise RuntimeError if you can't confirm it, so the job retries."""
    before = stamp(page)
    page.set_input_files(SEL_FILE, str(resume))
    page.wait_for_timeout(5000)                         # TODO: wait for something specific
    is_logged_in(page)                                  # reload
    after = stamp(page)
    log.info("Before: %s | After: %s", before, after)
    if not after or after == before:
        raise RuntimeError(f"Upload not confirmed (stamp '{after}')")


PORTAL = Portal(name="example", title="Example Portal", login_url=LOGIN_URL,   # TODO: name = settings key
                is_logged_in=is_logged_in, upload=upload, wait_signed_in=wait_for_url(SIGNED_IN_URL))

if __name__ == "__main__":
    sys.exit(run(PORTAL))
