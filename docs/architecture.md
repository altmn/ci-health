# Architecture

`plugin.json` is the canonical portable manifest. The host discovers `skills/ci-health/SKILL.md`; its UI metadata lives in `agents/openai.yaml`. The entrypoint routes to measurement, orchestration, execution, selection/reuse, experiments, and the pinned OpenClaw case study. References are loaded on demand.

`skills/ci-health/scripts/ci_health.py` is an optional Python 3.11+ standard-library helper. It invokes authenticated `gh` only during collection. Raw records and provenance feed normalized physical job accounting; local summaries and comparisons retain incomplete and unknown states. See [helper schema](../skills/ci-health/references/helper-schema.md) for exact contracts.

`scripts/release.py` validates local links and selected privacy patterns, packages an explicit file allowlist, and generates `dist/local-plugin/.codex-plugin/plugin.json` for hosts using the compatibility layout. The portable archive carries the canonical manifest; generated staging also carries the translated overlay. Source manifests are never rewritten during installation.

There are no hooks, MCP servers, runtime dependencies to install, background jobs, telemetry endpoints, or publisher authentication. GitHub authentication belongs to the user's GitHub CLI. The plugin marketplace catalog points at local generated staging. [Official plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
