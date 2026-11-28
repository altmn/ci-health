# Releasing

A request to "get to production" includes publishing a new versioned release and updating and verifying existing installed copies without another confirmation. This includes documentation-only releases. Follow [project instructions](../AGENTS.md#getting-to-production); local package preparation alone does not request production.

1. Work on a new feature branch. Update the canonical package version in `plugin.json` and `CHANGELOG.md` for each new release, including a documentation-only production request. The helper's collector version tracks helper changes; change schema/definition identifiers only with deliberate compatibility handling.
2. Run offline tests, package validation, and relevant independent behavior trials. Review source changes and all intended Git refs for sensitive data, including author metadata. Do not push backup refs or raw evidence.
3. Open a pull request, require the `Validate and test` check, and merge reviewed changes. Verify both CodeQL language analyses uploaded successfully and review any alerts. Do not reuse the merged branch. Maintain minimal job permissions, pinned actions, and bounded execution; CodeQL alone needs `security-events: write` to upload analysis.
4. From the clean merged revision, run `python3 scripts/release.py build --require-clean`. Inspect the runtime member list and `dist/build-info.json`; compare ZIP bytes across repeated builds if packaging changed. The `.sha256` file records archive integrity, not a publisher signature.
5. Tag the reviewed commit and publish the archive and checksum through a GitHub release when a release is intended. Do not attach local captures, test workspaces, or generated files outside the runtime allowlist. Do not submit to a plugin directory without a separate decision.
6. Build local staging and install through supported commands:

```bash
codex plugin marketplace add "$PWD"
codex plugin add ci-health@ci-health-dev
codex plugin list --marketplace ci-health-dev --json
```

Verify the installed version and bundled skills, including their relative references. Test `$ci-health`, `$ci-health-preflight`, and `$ci-health-optimize` discovery in a new session if needed. Evaluate implicit selection, UI behavior, and real-world savings separately. Resolve installation issues through the supported host commands.

For updates, use the current CLI's documented marketplace/plugin update path (`--help`); if removal/re-addition is required, preserve unrelated installations and user configuration. The source archive is reproducible from runtime file bytes, not dependent on an absolute local path or checkout time.
