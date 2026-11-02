# Setup (about 30 minutes)

## 1. Get the code into a connected folder

The coordinator runs `tools/tailor_resume.py` on your Mac through the Claude desktop app, so the
repo has to sit inside a folder you connect to Claude.

```bash
mkdir -p ~/JobHunt/resumes && cd ~/JobHunt
git clone https://github.com/<you>/job-hunt-agent-kit.git
```

Put your master resumes in `~/JobHunt/resumes/` (or anywhere; you'll list the paths in settings).

## 2. First run: create your settings

```bash
cd ~/JobHunt/job-hunt-agent-kit
./setup.sh            # creates config/settings.yaml and stops
```

Open `config/settings.yaml` and work through it top to bottom. The parts that matter most:

- `candidate.facts` and `candidate.years`: the agents may only say what's here. Be specific and honest.
- `candidate.never_claim`: tools you haven't used. Jobs that require them get skipped.
- `search`: roles, locations, salary floor, notice period.
- `portals`: turn on the ones you use; adjust `refresh_times` if you like.
- `resumes.families`: at least one file per family. Two or three versions rotate by day.
- `workspace_folder` / `repo_subpath`: where the repo lives, so the agents can find the tailor tool.
- Leave `test_mode: true` for the first week.

## 3. Second run: install

```bash
./setup.sh
```

This validates the file (errors tell you which key to fix), creates a venv in `~/.job-hunt-kit`,
installs Playwright and Chromium, copies the refresh scripts and your resumes there, loads one
launchd job per enabled portal (`com.jobhuntkit.<portal>-refresh`), and writes your prompts to
`build/prompts/`. Run it again any time you change settings.

## 4. Sign in to each portal once

```bash
./scripts/login.sh naukri
./scripts/login.sh hirist
```

A Chromium window opens. Sign in yourself, including any OTP. When the script sees you're in, it
saves the session and runs today's upload once. Optional for Naukri: store your password in the
Keychain so it can sign in again without you when no OTP is asked:

```bash
security add-generic-password -s jobhuntkit-naukri -a you@example.com -w
```

## 5. Board and agents

- Publish the board and copy its URL into `board_url`: [BOARD.md](BOARD.md). Run `./setup.sh` again.
- Create the three scheduled tasks: [AGENTS.md](AGENTS.md).
- Optional: Google Drive storage for tailored resumes: [GOOGLE_DRIVE.md](GOOGLE_DRIVE.md).

## 6. Going live

After a week in test mode, check the board: are the "To apply" cards ones you'd actually apply to?
Tune `search`, `never_claim` and the strategy's searches until they are. Then set
`test_mode: false`, run `./setup.sh`, and paste the new `build/prompts/coordinator.txt` into the
coordinator task.

## Day to day

| Want to | Do |
|---|---|
| Stop everything (got an offer, on holiday) | `./scripts/pause.sh` and disable the three tasks in Claude |
| Start again | `./scripts/resume.sh`, re-enable the tasks, re-login where notified |
| Remove the launchd jobs | `./scripts/uninstall.sh` (add `--purge` to delete sessions and logs too) |
| Test one upload now | `FORCE=1 ~/.job-hunt-kit/refresh/run_daily.sh hirist` |

## Troubleshooting

**"<Portal> needs you to sign in" notification.** The saved session expired or the site asked for
an OTP. Run `./scripts/login.sh <portal>`. Naukri and Instahyre sessions usually last weeks;
Talent500 relies on the keep-alive job, so a Mac that was off overnight may need a fresh sign-in.

**Upload "not confirmed" in the log.** The site's layout probably changed. Look at the screenshot in
`~/.job-hunt-kit/debug/<portal>/`, open the portal yourself, and update the selector or the
"last updated" text pattern at the top of `refresh/<portal>_refresh.py`. Then `./setup.sh`.

**Nothing happens at the scheduled time.** launchd only runs while you're logged in and the Mac is
awake; the later `refresh_times` are there to catch up. Check:

```bash
launchctl list | grep jobhuntkit                 # loaded jobs (exit status in column 2)
tail -20 ~/.job-hunt-kit/logs/naukri.log         # what the job did
cat ~/.job-hunt-kit/logs/naukri-launchd.err      # errors before the script started
ls ~/.job-hunt-kit/PAUSED                        # paused?
```

**"No resume file found".** launchd can't always read `~/Desktop`, `~/Documents` or iCloud folders.
setup.sh copies your resumes into `~/.job-hunt-kit/resumes`; run it again after replacing a resume.

**Headless browser blocked.** Some portals block headless Chrome. The job retries in a visible
window automatically; for Naukri it's visible from the start (`headless: false`).

**Agents can't find the board or tools.** Check that `board_url` is right and the task has
Gmail/Calendar connected and access to your Mac (see AGENTS.md). Re-render prompts after edits.
