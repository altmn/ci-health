# Architecture

`plugin.json` is the canonical portable manifest. The host discovers two skills under `skills/`, each with a `SKILL.md` entrypoint and `agents/openai.yaml` metadata. [CI Health](../skills/ci-health/SKILL.md) handles audits, optimization, baselines, and validation. [CI Health Preflight](../skills/ci-health-preflight/SKILL.md) reviews proposed changes before push. CI Health routes unqualified shipping/change reviews to preflight; explicit broader requests retain their scope. Shared technical references remain under CI Health and are loaded on demand.

Default audits focus on CI performance, avoidable work, feedback latency, and resource cost. The audit procedure bounds discovery and command tracing to that remit, using correctness as a guardrail for changes. Operational checks receive deeper investigation when they materially affect CI or the user requests that scope; scheduled work remains relevant when it consumes substantial resources or supplies required evidence.

Preflight compares the intended base with the candidate, including local staged, unstaged, and relevant untracked changes. It traces only affected execution paths and reports introduced or worsened inefficiency and unnecessary complexity. It excludes unchanged legacy problems and general recommendations unless requested. Confirmed material regressions pause shipping; optional simplification advice does not. Static inspection can complete with timing effects still unknown.

Both entrypoints permit implicit model selection. There is no mandatory ship integration: preflight does not alter gstack or install a push hook. Once selected it runs before the next push, including early PR pushes. Its result does not replace the caller's existing reviews, test evidence, or publication decisions.

`skills/ci-health/scripts/ci_health.py` is an optional Python 3.11+ standard-library helper. It invokes authenticated `gh` only during collection. Raw records and provenance feed normalized physical job accounting; local summaries and comparisons retain incomplete and unknown states. See [helper schema](../skills/ci-health/references/helper-schema.md) for exact contracts.

`scripts/release.py` validates local links and selected privacy patterns, verifies skill link targets are included in its explicit runtime allowlist, and generates `dist/local-plugin/.codex-plugin/plugin.json` for hosts using the compatibility layout. The portable archive carries the canonical manifest; generated staging also carries the translated overlay. Source manifests are never rewritten during installation.

There are no hooks, MCP servers, runtime dependencies to install, background jobs, telemetry endpoints, or publisher authentication. GitHub authentication belongs to the user's GitHub CLI. The plugin marketplace catalog points at local generated staging. [Official plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
