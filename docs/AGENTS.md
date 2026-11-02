# The three Claude agents

`./setup.sh` (or `python3 scripts/render_prompts.py`) fills the templates in `agents/templates/`
with your settings and writes ready-to-paste prompts to `build/prompts/`. Create one Claude
scheduled task per prompt. Re-render and update the task prompt whenever you change settings.

Cron times below are in your own timezone (`CRON_TZ=` + the `timezone` from settings). The odd
minutes are deliberate: lots of tasks start at :00, so these avoid the rush.

| Task name | Prompt file | Schedule (example) | Needs |
|---|---|---|---|
| Job hunt coordinator | `coordinator.txt` | `CRON_TZ=Asia/Kolkata 26 10 * * 1-5` (weekdays 10:26) | Gmail, Google Calendar, your Mac (folder + browser) |
| Inbox & interview agent | `inbox_interview.txt` | `CRON_TZ=Asia/Kolkata 27 8,18 * * *` (08:27 and 18:27) | Gmail, Google Calendar |
| Weekly job hunt review | `strategist.txt` | `CRON_TZ=Asia/Kolkata 55 18 * * 0` (Sundays 18:55) | Gmail, Google Calendar |

## Creating a task

1. In Claude, create a new scheduled task (from the desktop app or claude.ai). Use the name above,
   paste the prompt file's full text, and set the schedule.
2. Connect **Gmail** and **Google Calendar** for the task.
3. For the coordinator only: run it with your **Mac connected** (Claude desktop app open, the
   folder from `workspace_folder` shared with Claude, and the built-in browser pane signed in to
   your portals; Claude in Chrome works as a fallback and is needed for Google Drive uploads).
4. Run each task once by hand and read the result before leaving it on a schedule.

If your Claude workspace asks for approval on actions, a scheduled run may stop and wait. You can
allow the task to approve automatically in its settings if your plan allows it; start in test mode
if you do.

## What each one does

**Coordinator (weekdays).** Loads the strategy, the board, the next 3 days of calendar and recent
recruiter mail, writes a short plan, then works it: applies to fresh matching jobs on enabled
portals (or only logs them while `test_mode` is on), tailors a resume for good career-site-only
jobs and emails you the list, drafts follow-ups in Gmail, drafts LinkedIn referral notes for you,
and logs everything on the board. Budget per run: 5 applications, 4 career-site jobs, 3 follow-ups,
3 referral notes.

**Inbox & Interview (twice a day).** Reads the last day of mail, creates calendar events for new
interview invites (never edits existing ones), moves board cards (Applied, Interview scheduled,
Action needed, Rejected, Offer), and logs outcomes. The evening run emails you a prep brief for
each of tomorrow's interviews.

**Strategist (weekly).** Measures response rates by platform, role type and resume version,
shifts effort toward what's converting (slowly), prunes searches, updates the focus list on the
board, and emails you a one-page report with any decisions only you can make. It never changes
your target roles, locations, salary floor or guardrails; it recommends instead.

## What they will not do

Send messages to recruiters or on LinkedIn, type passwords/OTPs/ID numbers, accept or negotiate
offers, email anyone but you, claim skills outside your facts, change your portal profiles, or
delete board data. If you edit a prompt by hand, keep the GUARDRAILS section.
