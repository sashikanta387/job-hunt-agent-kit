# Job search playbook

Lessons from running this system through a real search, written as advice. Copy this file
somewhere private and add your own notes as you go.

## 1. Restart checklist

1. **Facts first.** Update `config/settings.yaml`: current role, years per skill, notice period,
   compensation, never-claim list. The agents use nothing else.
2. **Resumes.** Keep two to four master versions for the role families you target (e.g. lead vs.
   hands-on). Current role on top, official designation as the title. Let `tailor_resume.py` make
   JD-specific copies instead of hand-editing.
3. **Profiles.** Use the same headline on every portal and LinkedIn. Mark yourself actively looking,
   set notice period and preferred locations.
4. **Refresh jobs.** `./scripts/resume.sh` if paused, then `./scripts/login.sh <portal>` for each.
5. **Agents.** Re-enable the three scheduled tasks (disable them when you stop; don't delete).
6. **Board.** Reset `agent/strategy` from `build/strategy.json` and check the goal is still right.

## 2. Positioning

- Pick the title you want next and frame the headline around it, not around your current level.
  A clearer headline did more for callbacks than any amount of applying.
- Lead with three or four things you've actually done that the target role cares about, with numbers.
- Be exact about your stack. If you used a tool's JavaScript flavour, don't let a resume say
  TypeScript. Interviewers find out quickly.
- Have one calm, forward-looking answer for "why are you looking?" and use it everywhere.
- A side project you built (this one counts) makes a good interview story if you can explain the
  design decisions and the failures.

## 3. Channels

What tends to work, roughly in order:

1. **Inbound recruiter calls**, which come from a fresh profile (daily refresh) plus a sharp headline.
2. **Direct applies to jobs posted in the last day or two**, in small batches.
3. **Referrals**, but only with a short note that includes the job link. Many go unanswered; if
   nothing happens in five days, apply directly.
4. **Mass applying** to old postings: low return, and it fills your inbox with noise.

Track the source of every interview on the board. The weekly review uses it.

## 4. Daily routine

1. Morning: refresh jobs run on their own; the inbox agent turns invites into calendar events.
2. One focused applying session (or let the coordinator do it), small batch, fresh jobs only.
3. Send any referral notes and follow-ups the agents drafted, after reading them.
4. Evening: read tomorrow's prep brief, rehearse two stories out loud.
5. Follow up after three quiet working days, politely, once.

## 5. Interview prep

- Expect several technical rounds, sometimes a client round, then HR. Ask the recruiter for the
  sequence early.
- Prepare a few STAR stories with numbers (time saved, defects caught, people mentored). Reuse them.
- For gaps, say what you have instead and how fast you picked up the last new tool. Don't bluff.
- Bring three real questions about the team: how quality is owned, what "good" looks like in six
  months, what's breaking today.
- If two interviews clash, ask the one earlier in the process to move, and ask early.

## 6. Offers and negotiation

- Get the full breakup in writing before you accept: fixed vs. variable, what's bundled into the
  headline number (retirement, gratuity, insurance), leave policy.
- Compare offers on fixed pay and monthly take-home after tax, not on the headline figure.
  Variable pay isn't guaranteed.
- Competing offers help only when they're written. A company's budget isn't your expectation.
- Don't hold a signed offer hostage to a verbal one. Once you sign, withdraw from other processes
  politely.
- Read the appointment letter line by line: work location (get "remote" in writing if it matters),
  notice period, training-bond or recovery clauses, IP clause (list your prior personal projects),
  non-compete.

## 7. Onboarding checklist

- Collect documents early: education certificates and mark sheets, relieving and experience
  letters, recent payslips, tax forms, ID proofs, photos, medical certificate if asked.
- Email size limits are real: compress scans instead of splitting them across mails.
- Background verification: submit within the deadline, list only real employers, don't list the
  new employer as current.
- After joining: `./scripts/pause.sh`, disable the agents, set portals to "not looking", turn off
  open-to-work, update your headline.
- Keep work and personal tools separate: no employer code or data in personal AI accounts, repos
  or drives.
