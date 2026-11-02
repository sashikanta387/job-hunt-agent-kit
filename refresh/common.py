"""Shared plumbing for the portal refresh scripts.

Each portal script defines a Portal (URLs + three small functions) and calls run(portal).
Settings arrive as environment variables set by run_daily.sh / scripts/login.sh via kit.py:
  KIT_RESUME   resume file to upload today
  KIT_STATE    saved browser session (cookies + local storage); keep it private
  KIT_HEADLESS "0" = visible browser, "1" = headless (falls back to visible if blocked)
  KIT_SHOTS    folder for failure screenshots
  KIT_TZ       IANA timezone used for "today" checks
  KIT_LOCALE   browser locale
  KIT_HOME     install dir; a file named PAUSED there stops scheduled uploads

Exit codes: 0 done, 1 failed, 2 resume missing, 3 needs you (sign in / OTP / captcha), 4 paused.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")

STATE = Path(os.getenv("KIT_STATE", "state.json"))
RESUME = Path(os.getenv("KIT_RESUME", "resume.docx"))
HEADLESS = os.getenv("KIT_HEADLESS", "1") != "0"
SHOTS = Path(os.getenv("KIT_SHOTS", "debug"))
TZ = ZoneInfo(os.getenv("KIT_TZ", "UTC"))
LOCALE = os.getenv("KIT_LOCALE", "en-US")
KIT_HOME = Path(os.getenv("KIT_HOME", str(Path.home() / ".job-hunt-kit")))

log = logging.getLogger("refresh")


class NeedsHuman(RuntimeError):
    """The site wants a sign-in, OTP or captcha. Run scripts/login.sh <portal>."""


def now() -> datetime:
    return datetime.now(TZ)


def body_text(page) -> str:
    return page.locator("body").inner_text()


# --------------------------------------------------------------------------
# New file hash, same visible content
# --------------------------------------------------------------------------
def refresh_metadata(src: Path, out_dir: Path) -> Path:
    """Copy the resume and change only its document metadata (modified time, revision).
    The bytes change so the upload counts as new, but nothing a recruiter or ATS reads
    is altered and no hidden text is added. Keeps the original file name."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dst = out_dir / src.name
    ext = src.suffix.lower()
    if ext == ".docx":
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "docProps/core.xml":
                    xml = data.decode("utf-8")
                    xml = re.sub(r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)", rf"\g<1>{stamp}\g<2>", xml)
                    if "<cp:revision>" in xml:
                        xml = re.sub(r"<cp:revision>(\d+)</cp:revision>",
                                     lambda m: f"<cp:revision>{int(m.group(1)) + 1}</cp:revision>", xml)
                    else:
                        xml = xml.replace("</cp:coreProperties>", "<cp:revision>1</cp:revision></cp:coreProperties>")
                    data = xml.encode("utf-8")
                zout.writestr(item, data)
    elif ext == ".pdf":
        import pikepdf  # optional dependency, only for PDF resumes

        with pikepdf.open(src) as pdf:
            with pdf.open_metadata() as meta:
                meta["xmp:ModifyDate"] = stamp
            pdf.docinfo["/ModDate"] = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
            pdf.save(dst)
    else:
        raise ValueError(f"Unsupported resume type: {ext} (use .docx or .pdf)")
    return dst


# --------------------------------------------------------------------------
# Portal definition + runner
# --------------------------------------------------------------------------
@dataclass
class Portal:
    name: str                                   # matches the key in settings.yaml
    title: str
    login_url: str
    is_logged_in: Callable                      # (page) -> bool; leaves the page on the upload screen
    upload: Callable                            # (page, resume_path) -> None; raise if not confirmed
    wait_signed_in: Callable                    # (page, context) -> None; blocks until you finish signing in
    auto_login: Optional[Callable] = None       # (page) -> None; optional credential login
    describe: Optional[Callable] = None         # (page) -> str; shown on --dry-run


def open_browser(pw, headless: bool):
    browser = pw.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(storage_state=str(STATE) if STATE.exists() else None,
                              locale=LOCALE, timezone_id=str(TZ),
                              viewport={"width": 1366, "height": 900}, user_agent=UA)
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    page = ctx.new_page()
    page.set_default_timeout(30_000)
    return browser, ctx, page


def save_state(ctx) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    ctx.storage_state(path=str(STATE))
    os.chmod(STATE, 0o600)


def screenshot(page, prefix: str) -> Path:
    SHOTS.mkdir(parents=True, exist_ok=True)
    shot = SHOTS / f"{prefix}_{now():%Y%m%d_%H%M%S}.png"
    try:
        page.screenshot(path=str(shot), full_page=True)
    except Exception:  # noqa: BLE001
        pass
    return shot


def run(p: Portal) -> int:
    ap = argparse.ArgumentParser(description=f"Upload your resume to {p.title} once a day.")
    ap.add_argument("--login", action="store_true", help="visible browser; you sign in, the session is saved")
    ap.add_argument("--dry-run", action="store_true", help="check the session only, no upload")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s %(levelname)s [{p.name}] %(message)s")

    if not args.login and (KIT_HOME / "PAUSED").exists():
        log.info("PAUSED file present in %s; nothing to do.", KIT_HOME)
        return 4
    if not RESUME.is_file():
        log.error("Resume not found: %s", RESUME)
        return 2

    with sync_playwright() as pw:
        headless = HEADLESS and not args.login
        browser, ctx, page = open_browser(pw, headless)
        try:
            ok = p.is_logged_in(page)
            if not ok and headless:
                log.info("Headless check failed; retrying in a normal browser window")
                browser.close()
                browser, ctx, page = open_browser(pw, False)
                ok = p.is_logged_in(page)
            if not ok and args.login:
                page.goto(p.login_url, wait_until="domcontentloaded")
                log.info("Sign in to %s in the browser window (OTP/captcha too). Waiting up to 5 minutes...", p.title)
                p.wait_signed_in(page, ctx)
                ok = p.is_logged_in(page)
            if not ok and p.auto_login:
                p.auto_login(page)
                ok = p.is_logged_in(page)
            if not ok:
                screenshot(page, "login")
                raise NeedsHuman(f"{p.title} session expired. Run: scripts/login.sh {p.name}")
            save_state(ctx)
            if args.dry_run:
                log.info("Dry run OK: signed in. %s", p.describe(page) if p.describe else "")
                return 0
            with tempfile.TemporaryDirectory() as tmp:
                p.upload(page, refresh_metadata(RESUME, Path(tmp)))
            save_state(ctx)
            log.info("Done.")
            return 0
        except NeedsHuman as e:
            log.error("%s", e)
            return 3
        except Exception as e:  # noqa: BLE001
            log.error("Failed: %s (screenshot: %s)", e, screenshot(page, "fail"))
            return 1
        finally:
            browser.close()


def wait_for_url(pattern: str):
    """wait_signed_in helper: done when the URL matches pattern."""
    def _wait(page, _ctx):
        page.wait_for_url(re.compile(pattern), timeout=300_000)
        page.wait_for_timeout(2000)
    return _wait


if __name__ == "__main__":
    sys.exit("This module is imported by the portal scripts.")
