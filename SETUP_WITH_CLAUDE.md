# Set up with Claude (easiest)

Claude does almost all of the setup for you: it reads your resume, asks a few short questions,
writes your settings, publishes your Job Hunt Board and creates the three scheduled agents. You
only run two short commands in Terminal and sign in to your job sites yourself.

Takes about 30–45 minutes. Prefer doing it without Claude? Run `./start.sh` instead (see the README).

## Before you start (10 minutes, once)

1. **Claude desktop app** installed and signed in, on a paid plan that includes scheduled tasks.
2. **Get the kit onto your Mac** in a folder called `JobHunt` in your home folder:
   - Open **Terminal** (Spotlight → "Terminal"), run `xcode-select --install` (click Install; if it
     says already installed, that's fine), then:
     ```bash
     mkdir -p ~/JobHunt && cd ~/JobHunt
     git clone https://github.com/<your-github-username>/job-hunt-agent-kit.git
     ```
     (Use your own private fork. No GitHub? Download the ZIP from the repo page, unzip it, rename
     the folder to `job-hunt-agent-kit` and move it into `~/JobHunt`.)
3. In the Claude desktop app, **connect the folder `~/JobHunt`** (Add folder) so Claude can read
   and write files there.
4. In Claude **Settings → Connectors**, connect **Gmail** and **Google Calendar** (the account
   recruiters email).
5. Have your resume file(s) (.docx) somewhere easy, e.g. Downloads.

## Paste this into a new Claude conversation

Copy everything inside the box and paste it as your first message.

```text
Please set up the Job Hunt Agent Kit for me. The repo is in my connected folder at
~/JobHunt/job-hunt-agent-kit. I'm not technical: keep messages short, explain each step in plain
words, and do the work yourself wherever you can.

FIRST, read these files in the repo so you know how it works: README.md,
config/settings.example.yaml, docs/BOARD.md, docs/AGENTS.md and scripts/render_prompts.py.

GUARDRAILS (follow throughout):
- Never ask me for, or type, passwords, OTPs, PAN/Aadhaar or other ID numbers, or bank details.
- Never send any message, email or application on my behalf during setup.
- Ask me before anything that can't be undone (deleting or overwriting files, changing an
  existing scheduled task or artifact).
- Never invent experience, numbers or skills. Only use what is in my resume or what I confirm.
- Keep test_mode: true.

STEPS (tell me which step you're on, e.g. "Step 3 of 10"):

1. RESUME. Ask me to attach my resume file(s) or tell you where they are (e.g. ~/Downloads).
   Read them. If I have more than one, ask which is for lead/manager roles and which is for
   hands-on (SDET/engineer) roles.

2. INTERVIEW. Ask me short questions, one screen at a time (use the AskUserQuestion tool where
   available, with sensible options plus "Other"), only for what the resume doesn't tell you:
   target job titles, cities, remote OK (and which country), lowest yearly salary I'd accept and
   currency, current CTC and expected CTC as I'd write them on forms, notice period, which job
   sites to use (Naukri, Hirist, Instahyre, Talent500, LinkedIn), tools I have NOT used
   (never_claim), companies to skip, and my timezone. If Talent500 is on, ask me to paste my
   Talent500 profile link. Then propose 3-8 short "facts" and a years-per-skill list drawn from
   my resume, and let me correct them.

3. SETTINGS. Build config/settings.yaml from config/settings.example.yaml, replacing every
   example value with my confirmed answers (remove example facts/achievements I didn't confirm).
   Set workspace_folder "~/JobHunt", repo_subpath "job-hunt-agent-kit", resume paths under
   ~/JobHunt/resumes/, test_mode: true, and leave board_url as the example for now. Show me a
   short plain-language summary and wait for my "yes" before writing the file. After writing,
   check it with: python3 scripts/validate_config.py config/settings.yaml (if you can run
   commands in the folder) and fix any errors with me.

4. RESUMES. Copy my resume file(s) into ~/JobHunt/resumes/ (keep the original names).

5. INSTALL. You can't type in my Terminal, so ask me to open Terminal and run exactly:
       cd ~/JobHunt/job-hunt-agent-kit && ./setup.sh
   Tell me it takes a few minutes the first time and to paste you the last ~15 lines when it
   finishes. Wait. If it shows an error, help me fix it and run it again.

6. BOARD. Publish board/index.html as an artifact titled "Job Hunt Board" with capabilities
   {"db": {}, "user": {}}. Put its link into board_url in config/settings.yaml. Ask me to run
   ./setup.sh again (same command as step 5) and wait. Then write the contents of
   build/strategy.json into the board's database: collection "agent", document "strategy"; and
   create document "log" in collection "agent" as {"entries": []}. Give me the board link and
   offer to pin it.

7. AGENTS. Create the three scheduled tasks yourself with the scheduled-task tools
   (create_trigger): "Job hunt coordinator" with build/prompts/coordinator.txt, "Inbox & interview
   agent" with build/prompts/inbox_interview.txt, "Weekly job hunt review" with
   build/prompts/strategist.txt. Use the full file text as the prompt and the CRON_TZ schedule
   lines that setup.sh printed (from render_prompts) in my timezone. The coordinator needs my Mac
   (requires_local_device: true, with ~/JobHunt); the other two run in the cloud. Make sure each
   task has Gmail and Google Calendar connected; if you can't attach them, tell me exactly where to
   click. Check my existing scheduled tasks first so you don't create duplicates. Tell me which
   approval setting each task got.

8. SIGN-INS. For each enabled site except LinkedIn, ask me to run in Terminal:
       ./scripts/login.sh <site>      (e.g. ./scripts/login.sh naukri)
   one at a time. A browser opens; I sign in myself, including the OTP. Wait for me after each.
   Also ask me to sign in to my job sites (and LinkedIn) in the Claude desktop app's built-in
   browser, because the coordinator applies through it.

9. TEST RUN. Run each scheduled task once now and show me a short summary of what each did
   (test mode: it should only log jobs on the board). Fix anything that failed with me.

10. DONE. Finish with a checklist: what's set up, the board link, when each agent runs, and what
    happens next: one week in test mode (I check the board daily), then I set test_mode: false,
    run ./setup.sh, and you update the coordinator task with the new build/prompts/coordinator.txt.
    Mention ./scripts/doctor.sh for health checks and ./scripts/pause.sh to stop everything.
```

## If something goes wrong

- Claude can't see the repo: make sure `~/JobHunt` is connected in the desktop app and the repo is
  at `~/JobHunt/job-hunt-agent-kit`.
- Setup or a sign-in failed: run `./scripts/doctor.sh` in Terminal and paste the output to Claude.
- You'd rather answer the questions in Terminal: run `./start.sh`, then come back and ask Claude to
  continue from step 6.
