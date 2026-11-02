# Contributing

Bug fixes and new portals are welcome. Keep changes small and keep personal data out of commits
(run `git status` before committing; `config/settings.yaml`, sessions and resumes are git-ignored).

## Adding a new portal

1. Copy `refresh/portal_template.py` to `refresh/<portal>_refresh.py` and fill in the TODOs:
   login URL, the page with the resume `<input type=file>`, and how to prove the upload worked
   (a new "last updated" stamp, a success toast, or the upload API response). If you can't
   confirm it, raise - a false "done" is worse than a retry.
2. Register it in `refresh/kit.py`: add the key to `REFRESH_PORTALS` and a display name to `TITLES`.
3. Add a `portals.<portal>` block to `config/settings.example.yaml` (copy an existing one).
4. Add one line of apply rules to `APPLY_RULES` in `scripts/render_prompts.py` and the portal to
   `PLATFORMS` in `board/index.html`.
5. Add it to the `case` list in `scripts/login.sh` and the loop in `setup.sh`.
6. Test: `./setup.sh`, `./scripts/login.sh <portal>`, then check `~/.job-hunt-kit/logs/<portal>.log`.

## Before opening a pull request

```bash
bash -n setup.sh scripts/*.sh refresh/*.sh
python3 -m py_compile refresh/*.py scripts/*.py tools/*.py
python3 scripts/validate_config.py config/settings.example.yaml
python3 scripts/render_prompts.py config/settings.example.yaml
```

Site layouts change often. When you fix a selector, note the date you checked it in a comment.
