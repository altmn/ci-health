# Contributing with an agent

Read `CONTRIBUTING.md` and the relevant skill reference before editing. Work on a new feature branch; do not commit directly to `master` or reuse a merged branch.

Keep the skill entrypoint concise and put conditional detail in references. Preserve the distinction between physical resource consumption and valid logical test evidence. Missing observations must remain unknown.

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/release.py validate` for changes to helpers, packaging, or instructions. Record realistic independent skill trials when behavior changes materially. Use synthetic fixtures; keep raw CI captures, host paths, credentials, and private metadata out of source and release archives.
