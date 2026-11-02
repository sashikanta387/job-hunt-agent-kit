#!/usr/bin/env python3
"""Keep the Talent500 login alive without an OTP.

Talent500 keeps you signed in with two cookies:
  authToken    access token, valid about 1 hour
  refreshToken refresh token, valid about 7 hours; each refresh returns a NEW one
This swaps the saved refresh token for a fresh pair (the same call the website makes) and
writes them back into the saved session file. Run every ~2 hours (launchd) and the session
lasts as long as the Mac isn't asleep/off for longer than the refresh token's lifetime.

Exit codes: 0 refreshed, 3 needs a manual sign-in, 4 paused, 1 other error.
Tokens are never printed or logged.
"""
import base64
import fcntl
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

STATE = Path(os.getenv("KIT_STATE", "talent500_state.json"))
KIT_HOME = Path(os.getenv("KIT_HOME", str(Path.home() / ".job-hunt-kit")))
API = "https://prod-warmachine.talent500.co/api/v2/users/candidate/refresh-token/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "talent500 keepalive:", msg, flush=True)


def jwt_exp(tok):
    try:
        p = tok.split(".")[1]
        return int(json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))["exp"])
    except Exception:  # noqa: BLE001
        return 0


def raw(v):  # cookie value -> bare JWT
    v = urllib.parse.unquote(v or "")
    return v[7:] if v.lower().startswith("bearer ") else v


def main():
    if (KIT_HOME / "PAUSED").exists():
        return 4
    if not STATE.exists():
        log("no saved session; run scripts/login.sh talent500")
        return 3
    with open(STATE, "r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        state = json.load(fh)
        ck = {c["name"]: c for c in state.get("cookies", []) if "talent500" in c.get("domain", "")}
        rc, ac = ck.get("refreshToken"), ck.get("authToken")
        if not rc:
            log("no refresh token saved; run scripts/login.sh talent500")
            return 3
        rt = raw(rc["value"])
        if jwt_exp(rt) - time.time() <= 60:
            log("refresh token already expired; run scripts/login.sh talent500")
            return 3
        req = urllib.request.Request(API, data=json.dumps({"refresh": rt}).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json",
                                              "Origin": "https://talent500.com", "Referer": "https://talent500.com/",
                                              "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            log(f"refresh rejected (HTTP {e.code}); run scripts/login.sh talent500")
            return 3 if e.code in (400, 401, 403) else 1
        except Exception as e:  # noqa: BLE001
            log(f"network error: {type(e).__name__}")
            return 1
        access, refresh = data.get("access"), data.get("refresh")
        if not access or not refresh:
            log("unexpected response (no tokens)")
            return 1
        enc = "%20" in rc["value"]  # keep the cookie encoding the site uses
        fmt = (lambda t: "Bearer%20" + t) if enc else (lambda t: "Bearer " + t)
        exp = jwt_exp(refresh) or int(time.time()) + 6 * 3600
        rc.update(value=fmt(refresh), expires=exp)
        if ac:
            ac.update(value=fmt(access), expires=exp)
        else:
            state["cookies"].append({**rc, "name": "authToken", "value": fmt(access)})
        fh.seek(0)
        json.dump(state, fh)
        fh.truncate()
    os.chmod(STATE, 0o600)
    log(f"session extended until {time.strftime('%H:%M', time.localtime(exp))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
