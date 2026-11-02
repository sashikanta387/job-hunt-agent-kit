# Getting started: a complete step-by-step guide

This guide takes you from zero to a running job-hunt system. It assumes no prior setup. Follow it
in order; each step says what you should see when it worked. Plan about **60–90 minutes** the first
time, plus a week in test mode before going live.

> Short on time? [SETUP.md](SETUP.md) is the condensed version of the same steps.

---

## What you'll end up with

| Piece | What it does | Runs where |
|---|---|---|
| **Resume refresh jobs** | Re-upload your resume on Naukri / Hirist / Instahyre / Talent500 every morning so recruiters see an "active today" profile | Your Mac (launchd), automatically |
| **Job Hunt Board** | A kanban page of every job: to apply, applied, interview, offer… Also the agents' memory | A private Claude artifact |
| **Coordinator agent** | Weekdays: plans the day, finds fresh matching jobs, applies (or only logs them in test mode), tailors resumes, drafts follow-ups | Claude scheduled task + your Mac |
| **Inbox & interview agent** | Twice a day: reads your mail, puts interview invites on your calendar, updates the board, emails you prep briefs | Claude scheduled task |
| **Strategist agent** | Sundays: measures what's working and adjusts the plan, emails you a weekly report | Claude scheduled task |

You stay in control: the agents never message recruiters, never type passwords or OTPs, never
accept offers, and never claim a skill you didn't list.

---

## Step 0. Check you have everything

**Accounts**
- [ ] A **Claude** paid plan that includes scheduled tasks and the **Claude desktop app**.
- [ ] A **Gmail** account and **Google Calendar** (the ones recruiters email).
- [ ] Accounts on the job sites you'll use (Naukri, Hirist, Instahyre, Talent500, LinkedIn).
- [ ] A **GitHub** account (to fork this repo).

**Computer**
- [ ] A **Mac** (macOS 13 or later). The refresh jobs use macOS launchd; Windows/Linux aren't supported yet.
- [ ] The Mac is on and online in the mornings (the refresh jobs run around 08:15–12:45).

**Files**
- [ ] 1–3 versions of your resume as **.docx** (e.g. "QA Lead" and "Senior SDET" versions).

---

## Step 1. Install the basic tools on your Mac

Open **Terminal** (Spotlight → "Terminal") and run these one at a time.

1. Apple's developer tools (gives you `git`):
   ```bash
   xcode-select --install
   ```
   A pop-up appears; click **Install**. If it says "already installed", that's fine.

2. Check Python 3 (needs 3.9 or newer):
   ```bash
   python3 --version
   ```
   You should see `Python 3.x.y`. If not, install it from https://www.python.org/downloads/macos/.

3. Optional, only if you want PDF versions of tailored resumes: install LibreOffice from
   https://www.libreoffice.org/download/.

---

## Step 2. Fork and download the repo

1. On GitHub, open this repo and click **Fork** → **Create fork**. Keep the fork **private**
   (it will hold your settings later, even though they're git-ignored).
2. Make a home folder for everything and clone your fork into it:
   ```bash
   mkdir -p ~/JobHunt/resumes
   cd ~/JobHunt
   git clone https://github.com/<your-github-username>/job-hunt-agent-kit.git
   ```
3. Copy your resume .docx files into `~/JobHunt/resumes/`.

✅ You should now have `~/JobHunt/job-hunt-agent-kit/` and `~/JobHunt/resumes/` with your files.

> Why `~/JobHunt`? The coordinator agent needs to reach the repo's tools on your Mac through the
> Claude desktop app, so the repo must sit inside a folder you'll connect to Claude in Step 8.

---

## Step 3. Answer the setup questions

> Prefer to let Claude do Steps 3–9 for you? Paste the prompt from
> [SETUP_WITH_CLAUDE.md](../SETUP_WITH_CLAUDE.md) into the Claude desktop app instead.

```bash
cd ~/JobHunt/job-hunt-agent-kit
./start.sh
```

`start.sh` checks your Mac has Python 3 and git (and tells you the exact install command if not),
then asks you plain questions: your name and email, a few true facts about your experience, the
jobs and cities you want, salary floor, CTC and notice period, which job sites to use, and where
your resume files are. Press **Enter** to accept the suggestion in `[brackets]`. It detects your
timezone, copies the resumes you pick into `~/JobHunt/resumes`, shows a summary, and only writes
`config/settings.yaml` after you say yes. Test mode stays **on**.

Tips:
- **Facts** are the only things the agents may say about you. Keep them short and true, e.g.
  "7 years in QA, 5 in automation".
- **Tools you have NOT used** (e.g. `Cypress, Python`): jobs that require them are skipped.
- The board link question comes up at the end; just press Enter for now (Step 6).

To change answers later, run `./start.sh` again and choose **Edit** (your current answers become the
defaults). `python3 scripts/wizard.py --reset` starts over.

### Advanced: edit settings by hand

Everything the wizard writes lives in `config/settings.yaml`; every field is explained in
`config/settings.example.yaml`. Open it with `open -e config/settings.yaml`, then run `./setup.sh`.
The wizard covers the common fields; edit by hand for `achievements`, `refresh_times`, the
`tailor` section and `google_drive_folder_url`.

Fill it in **top to bottom**. Every field has a comment; here is what matters most.

#### 3a. `candidate` — facts about you (the agents may only say what's here)
| Field | Example | Tip |
|---|---|---|
| `name`, `email` | Your name; the Gmail the agents email reports to | Reports go **only** to this address |
| `headline` | `Senior SDET \| QA Automation Lead \| Playwright \| API & CI/CD` | Same headline you'll use on every job site |
| `current_role`, `current_company`, `current_role_period` | Your official designation | Use the exact title on your offer/relieving letter |
| `facts` | Short, true statements: years, tools, scope, education | Be specific. Anything not here, the agents won't claim |
| `achievements` | Numbers: "regression 4 days → 2 days" | These become interview and resume talking points |
| `never_claim` | Tools you haven't used: `["Cypress","Python"]` | Jobs that **require** these are skipped |
| `years` | Years per skill for screening forms | Use the same numbers everywhere |
| `why_change` | One positive sentence | Used in screening answers and prep briefs |

#### 3b. `search` — what you're looking for
- `target_roles`, `locations`, `remote_ok`, `remote_region`
- `salary_floor` (yearly amount + currency) — roles clearly below it are skipped
- `current_ctc`, `expected_ctc`, `notice_period` — written exactly as you want them on forms
- `min_years_required`, `skip_companies`

#### 3c. `timezone`, `test_mode`
- `timezone`: your IANA zone, e.g. `Asia/Kolkata`.
- **Keep `test_mode: true` for the first week.** In test mode the coordinator finds and logs jobs
  but never submits an application.

#### 3d. `portals` — which job sites
For each site set `enabled: true/false`. You can keep the default `refresh_times`. For Talent500,
paste your own profile URL into `profile_url` (open your profile in the browser and copy the address).

#### 3e. `resumes` — which file goes where
- `families`: group your resume files, e.g. `lead:` and `sdet:`. If you list 2–3 files in a family,
  they rotate by day.
- Each portal's `resume_family` says which family it uploads.
- `role_map`: which family the coordinator uses for which kind of role.

#### 3f. `tailor` — only if you want per-job tailored resumes
Point `base_resume` at your main .docx and tell the tool where its sections are:
`headline_paragraph`, `summary_heading`, `skills_heading`, `bullets_start`, `bullets_end`
(the exact heading text in **your** resume). Skip this section if you don't need tailoring.

#### 3g. Folders and links
- `install_dir`: leave as `~/.job-hunt-kit`.
- `workspace_folder`: `~/JobHunt`; `repo_subpath`: `job-hunt-agent-kit`.
- `board_url`: leave for now — you'll fill it in Step 6.
- `google_drive_folder_url`: optional (see [GOOGLE_DRIVE.md](GOOGLE_DRIVE.md)).

---

## Step 4. Install

`start.sh` continues straight into the install (it runs `./setup.sh` for you). This:
1. checks your settings (any error names the exact key to fix: run `./start.sh` again and choose Edit),
2. creates a Python environment in `~/.job-hunt-kit` and installs Playwright + Chromium (a few minutes the first time),
3. copies the refresh scripts and your resumes into `~/.job-hunt-kit`,
4. registers one morning job per enabled portal (`com.jobhuntkit.<portal>-refresh`),
5. writes your ready-to-paste agent prompts into `build/prompts/`.

✅ A warning about `board_url` is expected at this point. After any later settings change, run
`./setup.sh` (or `./start.sh`) again. Check everything with:
```bash
./scripts/doctor.sh
```

---

## Step 5. Sign in to each job site once

`start.sh` offers to do this for you, one site at a time. To do it yourself, for every portal you enabled:
```bash
./scripts/login.sh naukri
./scripts/login.sh hirist
./scripts/login.sh instahyre
./scripts/login.sh talent500
```

A browser window opens. **Sign in yourself**, including any OTP. When the script detects you're
signed in, it saves the session on your Mac and runs today's resume upload once.

✅ You'll see a success line and today's upload in the site's "resume updated" date.

Test any single upload later with:
```bash
FORCE=1 ~/.job-hunt-kit/refresh/run_daily.sh hirist
```

> Sessions are stored only on your Mac (`~/.job-hunt-kit`) and are never committed to git.
> If a site logs you out later, just run its `login.sh` again.

---

## Step 6. Create your Job Hunt Board

1. Open the **Claude desktop app** and start a new conversation.
2. Attach `board/index.html` (drag it into the chat) and say:
   > *Publish this file as an artifact titled "Job Hunt Board" with the `db` and `user` capabilities.*
3. Claude replies with a link like `https://claude.ai/artifact/...`. Open it — you should see empty
   columns (To apply, Applied, Interview, …).
4. Add that link to your settings: run `./start.sh`, choose **Edit**, press Enter through the
   questions and paste the link at the board question (or put it into `board_url` in
   `config/settings.yaml` by hand and run `./setup.sh`).
5. Load the starting plan into the board. In the same conversation, attach `build/strategy.json` and say:
   > *Write this file into the Job Hunt Board's database as collection `agent`, document `strategy`,
   > and create document `log` in collection `agent` with `{"entries": []}`.*
6. Reload the board. ✅ An "Agent focus this week" box appears.

Tip: pin the board in the Claude sidebar. Details: [BOARD.md](BOARD.md).

---

## Step 7. Connect Gmail and Google Calendar to Claude

In Claude → **Settings → Connectors**, connect **Gmail** and **Google Calendar** with the same
Google account recruiters email. The agents only read mail, create calendar events for interview
invites, create drafts, and email *you*.

---

## Step 8. Connect your Mac folder and browser

The coordinator works on your Mac through the desktop app:
1. In the Claude desktop app, add the folder **`~/JobHunt`** to your workspace (so it can run `tools/tailor_resume.py`).
2. Open the **built-in browser** pane in the desktop app and sign in to the job sites there too
   (Naukri, Hirist, Instahyre, Talent500, LinkedIn). The coordinator applies through this browser.
3. Optional: install **Claude in Chrome** if you want tailored resumes uploaded to Google Drive.

---

## Step 9. Create the three scheduled agents

Your filled-in prompts are in `build/prompts/`:
- `coordinator.txt`
- `inbox_interview.txt`
- `strategist.txt`

Once the board link is set, `./start.sh` shows each task's schedule and copies each prompt to your
clipboard when you press Enter. Or ask Claude to create the tasks for you (steps 7–9 of
[SETUP_WITH_CLAUDE.md](../SETUP_WITH_CLAUDE.md)). By hand, in Claude create a **new scheduled task** for each:

| Task name | Paste this prompt | Schedule |
|---|---|---|
| Job hunt coordinator | `coordinator.txt` | Weekdays ~10:30 (e.g. `CRON_TZ=Asia/Kolkata 26 10 * * 1-5`) |
| Inbox & interview agent | `inbox_interview.txt` | Twice a day (e.g. `CRON_TZ=Asia/Kolkata 27 8,18 * * *`) |
| Weekly job hunt review | `strategist.txt` | Sundays evening (e.g. `CRON_TZ=Asia/Kolkata 55 18 * * 0`) |

`setup.sh` prints these cron lines in **your** timezone. For each task:
1. Paste the **entire** prompt text.
2. Attach the **Gmail** and **Google Calendar** connectors.
3. Coordinator only: make sure it can use your Mac (desktop app open, `~/JobHunt` connected).
4. Click **Run now** once and read the result before leaving it on the schedule.

✅ After the coordinator's first run, the board shows new cards in **To apply**, and you get one
email listing career-site jobs (with tailored resumes, if you set up `tailor`).

More detail: [AGENTS.md](AGENTS.md).

---

## Step 10. One week in test mode

For about a week, just **check the board and your inbox each day**:
- Are the "To apply" jobs ones you'd really apply to? If not, tighten `search` and `never_claim`,
  run `./setup.sh`, and paste the new prompts into the tasks.
- Are recruiter mails and interview invites showing up on the board and calendar?
- Do the evening prep briefs look useful?

Apply to the good ones yourself during this week — that's still progress.

---

## Step 11. Go live

1. Set `test_mode: false` in `config/settings.yaml`.
2. Run `./setup.sh`.
3. Paste the new `build/prompts/coordinator.txt` into the coordinator task.

From now on the coordinator submits up to **5 applications per run** on direct-apply / Easy Apply
jobs that match your rules. If your Claude workspace asks for approval on actions, approve them
from the notification, or allow the task to approve automatically if your plan permits.

---

## Your daily routine (5–10 minutes)

| When | What to do |
|---|---|
| Morning | Open the board → **Due soon** strip. Handle anything marked "Action needed" |
| After the coordinator runs | Read its summary. Approve or edit any LinkedIn referral notes (they're never sent for you) |
| Any time | Send the follow-up **drafts** in Gmail that you agree with |
| Evening | Read tomorrow's interview prep brief email |
| Sunday | Read the weekly report and make the decisions it lists (only you change roles, salary floor or locations) |

Useful habits that worked for the original author: one sharp headline on every site, fresh
(≤ 2 days old) jobs only, small daily batches, and honest answers. See
[PLAYBOOK_TEMPLATE.md](PLAYBOOK_TEMPLATE.md) for interview, offer-negotiation and onboarding checklists.

---

## When you get the job

1. `./scripts/pause.sh` — stops all resume refreshes (they check for a `PAUSED` file).
2. In Claude, **disable** the three scheduled tasks (don't delete them — you'll want them next time).
3. Update every job site: add the new role, set "not actively looking", turn off LinkedIn Open to Work.
4. Write down what worked in your own copy of `docs/PLAYBOOK_TEMPLATE.md`.

## Starting again later

1. Run `./start.sh`, choose **Edit**, and update your role, years, CTC, notice period and resumes.
2. `./scripts/resume.sh`.
3. `./scripts/login.sh <portal>` for any site that logged you out.
4. Paste the re-rendered prompts into the three tasks and **enable** them.

## Removing everything
```bash
./scripts/uninstall.sh          # removes the morning jobs, keeps your data
./scripts/uninstall.sh --purge  # also deletes sessions and logs in ~/.job-hunt-kit
```
Then delete the three scheduled tasks in Claude and, if you like, the board artifact.

---

## Troubleshooting

First, run `./scripts/doctor.sh`. It checks the Python environment, your settings, the morning jobs,
saved sign-ins, the last log line per site, paused state and the board link, and prints the fix
command for anything that's wrong.

| Problem | Fix |
|---|---|
| `setup.sh` says a key is invalid | It names the key. Fix it in `config/settings.yaml` and rerun |
| A morning upload didn't happen | Check `~/.job-hunt-kit/logs/<portal>.log`. Usually the login expired → run `./scripts/login.sh <portal>` |
| "Login required" every day on one site | The site changed its sign-in flow. Log in again; if it repeats, see SETUP.md → Troubleshooting |
| Upload fails after a site redesign | Selectors in `refresh/<portal>_refresh.py` need updating. See [CONTRIBUTING.md](../CONTRIBUTING.md) |
| Board says "Sign in to claude.ai to load your jobs" | It was published without the `db` capability. Republish with `db` and `user` |
| Coordinator says it can't reach your Mac or browser | Open the Claude desktop app, connect `~/JobHunt`, open the browser pane, run the task again |
| Agents apply to jobs you don't want | Tighten `search`, `skip_companies`, `never_claim`; rerun `./setup.sh`; update the task prompts |
| Nothing is applied in live mode | Check `test_mode: false` was rendered (reopen `build/prompts/coordinator.txt`) and the task was updated |
| Too many emails | Lower the coordinator's run frequency or set only the evening inbox run |

---

## Privacy and fair use

- Your settings, sessions, logs and resumes are **git-ignored** and stay on your Mac. Keep your fork private anyway.
- Never put passwords, OTPs, PAN/Aadhaar or bank details in settings or board notes.
- Automating job sites may break their terms of use. Use modest volumes, keep test mode on until
  you trust the results, and you are responsible for how you use this kit.
