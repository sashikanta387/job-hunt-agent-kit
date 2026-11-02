# Job Hunt Board

`board/index.html` is a kanban page that doubles as the agents' memory. It runs as a private
Claude artifact with a small database:

- collection `jobs`: one document per job (company, role, platform, status, due, link, notes, ...)
- collection `agent`: document `strategy` (the plan the coordinator follows) and document `log`
  (what each run did; the strategist learns from it)

You can drag cards between columns, edit them, and add jobs by hand. The agents read and write the
same data.

## Publish it

1. In a Claude conversation (desktop app or Claude Code), share `board/index.html` and ask:
   *"Publish this file as an artifact titled Job Hunt Board with the `db` and `user` capabilities."*
   The capabilities declaration is `{"db": {}, "user": {}}`. `db` is required; without it the page
   shows "Sign in to claude.ai to load your jobs" and can't save.
2. Copy the artifact link (looks like `https://claude.ai/artifact/...`) into `board_url` in
   `config/settings.yaml`, then run `./setup.sh` (or `python3 scripts/render_prompts.py`).
3. Load the starting strategy. In the same conversation ask Claude to write the contents of
   `build/strategy.json` into the board's database as collection `agent`, document `strategy`,
   and to create document `log` in `agent` as `{"entries": []}`.
4. Open the board. It should load with empty columns and an "Agent focus this week" box.

Pin it in the Claude sidebar if you'll check it daily.

## Customising

At the top of the `<script>` in `board/index.html`:

- `PLATFORMS`: where jobs come from, with a short badge and colour. Remove portals you don't use.
- `STATUSES`: the columns. The agents use these exact names, so if you rename one, change it in
  `agents/templates/*.md` too.

Republish to the same artifact after editing; the data stays.

## Sharing

The artifact is private by default. If you share it, anyone you share with can see your job list
and notes. Keep salary details and personal identifiers out of card notes.
