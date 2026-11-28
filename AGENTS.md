# Contributing with an agent

Read `CONTRIBUTING.md` and the relevant skill reference before editing. Work on a new feature branch; do not commit directly to `master` or reuse a merged branch.

Keep the skill entrypoint concise and put conditional detail in references. Preserve the distinction between physical resource consumption and valid logical test evidence. Missing observations must remain unknown.

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/release.py validate` for changes to helpers, packaging, or instructions. Record realistic independent skill trials when behavior changes materially. Use synthetic fixtures; keep raw CI captures, host paths, credentials, and private metadata out of source and release archives.

## Getting to production

A request to "get to production", or a clearly equivalent request to ship or deploy this project, authorizes the complete workflow below. Do not ask for confirmation again for steps already covered by that request. Honor any explicit narrower scope.

1. Prepare a new version, changelog entry, and release notes on a fresh feature branch, including for README-only or other documentation-only changes. Preserve project behavior unless the requested change explicitly changes it, and synchronize canonical and generated release metadata.
2. Commit, push, open a pull request, complete the required checks, and merge through the project's protected-branch workflow.
3. Build from the clean, reviewed merged revision. Inspect the package contents, publish a new GitHub release with the required installable assets and checksums, and verify the published version and artifact integrity using this project's release procedure.
4. Discover and update the project's existing installed copies through supported host mechanisms, including Codex and any other known installed hosts. For an existing ChatGPT cloud plugin, update that same plugin once and verify availability and selection in Chrome and Safari when those browsers are in use. Preserve installation scope, local modifications, unrelated files, ownership, and sharing; do not create duplicate installations or edit host caches by hand.
5. Verify and report the GitHub release and each installed target separately, using installed versions or file identities and actual skill discovery or selection. A merged PR, local build, or unchanged runtime is not completion of a production request. Discovery alone is not behavioral acceptance.

If a required step is blocked, complete independent work and report the exact blocker. Request only the missing input or manual action needed to proceed, rather than asking for authorization again.

Source-only edits, reviews, and local package preparation do not by themselves trigger this workflow. New installations, changes to sharing, and public plugin-directory submission remain outside it unless requested. Follow [the release instructions](docs/releasing.md) and retain all required validation and evidence checks.
