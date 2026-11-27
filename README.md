# CI Health

A Codex plugin for auditing CI, reviewing proposed changes before push, and implementing targeted pipeline improvements. CI Health audits look across the repository for avoidable execution and feedback bottlenecks. CI Health Preflight follows proposed changes to find new waste. CI Health Optimize tackles a specific bottleneck or latency goal in an existing pipeline.

The goal is fast, trustworthy feedback and sustainable throughput. Cost is a supporting metric. CI Health includes provider-neutral guidance and an optional read-only GitHub Actions measurement helper; it does not operate a hosted service or collect telemetry for its publisher.

Operational checks belong in the investigation when they materially affect CI demand or useful feedback, or when the user requests an operational review. Scheduled work can be a substantial CI cost or required validation source. An unrelated cleanup or recovery failure does not by itself take priority over CI optimization.

## Use it

Invoke `$ci-health` in a Codex session with access to the relevant repository:

```text
Use $ci-health to audit our overloaded CI. Establish a baseline, investigate
suspected redundant work, and recommend changes with acceptance evidence.
```

```text
Use $ci-health to validate this CI optimization against the baseline.
Check workload and capacity changes, missing coverage, retries, and queue age.
```

CI Health supports audits, baselines, diagnosis, and post-change validation. It distinguishes suspected, supported, confirmed, and resolved findings. See the [skill entrypoint](skills/ci-health/SKILL.md) and [case study](skills/ci-health/references/openclaw-case-study.md).

For a targeted improvement to existing CI, invoke Optimize:

```text
Use $ci-health-optimize to shorten push-to-staging. Find and implement the
highest-impact local change that preserves the checks required for staging,
and show how to verify the staging and production gates.
```

Optimize investigates work that can be removed, reused, rebalanced, or moved to a different validation stage. It edits when the request authorizes implementation. The [optimization playbook](skills/ci-health/references/optimization.md) includes a [Bun recipe](skills/ci-health/references/bun-ci.md) for applicable JavaScript and TypeScript repositories.

Audits trace material commands and delivery gates, including inner test operations and preparation that test counts can hide. Optimize carries a [scenario acceptance ledger](skills/ci-health/references/experiments.md#scenario-acceptance-ledger) through implementation: fast PR, reuse, cold fallback, staging and release-publication results qualify their own conditions. Failed, retried and over-budget attempts remain evidence; implementation completion and performance acceptance are reported separately.

For a branch review or shipping, invoke the separate preflight skill:

```text
Use $ci-health-preflight before pushing these changes. Check added CI work
and unnecessary complexity; keep recommendations specific to this change.
```

```text
Ship these changes, using $ci-health for the CI review before the first push.
```

In shipping context, an unqualified `$ci-health` invocation routes to [CI Health Preflight](skills/ci-health-preflight/SKILL.md). Explicit requests for a repository audit, diagnosis, or baseline retain their scope. Targeted improvement requests route to [CI Health Optimize](skills/ci-health-optimize/SKILL.md). Preflight follows changes through tests, scripts, fixtures, configuration, and application inputs that affect CI, including changes outside workflow files. Confirmed material regressions pause shipping for resolution or explicit acceptance.

For materially affected expensive paths, preflight retains a compact before/after impact receipt bound to the reviewed candidate. It keeps supported risks and unverified budget conditions visible, refreshes affected inspection after relevant edits, and distinguishes completed static review from timing qualification. Independent copy with no execution impact stays brief.

CI Health and Optimize support implicit selection. Preflight disables direct implicit invocation: request it explicitly or let CI Health route a CI-specific change review after ordinary inspection establishes changed CI execution. Generic review or shipping alone does not select Preflight for independent copy. Source-scanned or otherwise consumed content can still affect CI. Once selected during shipping, preflight belongs before the next origin push, including an early draft-PR push. The ship workflow retains ownership of fixes, tests, and publication.

## Install in Codex

Use a current Codex CLI with `codex plugin` support, Git, and Python 3.11+. Clone a reviewed version, validate, and build the local package:

```bash
git clone https://github.com/altmn/ci-health.git
cd ci-health
python3 -m unittest discover -s tests -v
python3 scripts/release.py build
codex plugin marketplace add "$PWD"
codex plugin add ci-health@ci-health-dev
codex plugin list --marketplace ci-health-dev --json
```

The repository's local marketplace points to generated `dist/local-plugin`. Keep the clone available for future updates. Rebuild from a reviewed revision and use the supported Codex plugin commands to refresh installation; do not edit plugin cache files. Start a new session if the host does not refresh discovery immediately. This project has not been submitted to a plugin directory.

For standalone skill hosts, copy the complete `skills/ci-health`, `skills/ci-health-preflight`, and `skills/ci-health-optimize` directories side by side into the host's documented skills location so their relative links resolve. Python and `gh` are needed only for the optional measurement helper. Choose one installation form per host to avoid duplicate discovery.

## Measurement helper

The Python standard-library CLI provides `collect`, `summarize`, and `compare`. Collection uses an existing authenticated GitHub CLI and makes GET requests only. Private repositories require Actions read permission. It writes to an explicitly supplied evidence directory, not into the source package by default. See [commands and schemas](skills/ci-health/references/helper-schema.md) and the [measurement contract](skills/ci-health/references/measurement.md).

```bash
python3 skills/ci-health/scripts/ci_health.py --help
python3 skills/ci-health/scripts/ci_health.py collect --help
python3 skills/ci-health/scripts/ci_health.py compare --help
```

Keep captures private and outside source control: run metadata can contain private names, labels, authors, and internal URLs. There is no default log or artifact download. Do not paste tokens into prompts or issue reports.

## Limits

GitHub REST job intervals are execution proxies. They do not establish exact eligible queue time, actual checkout identity, required-verdict history, provider charges, or complete calendar-period activity. The helper collects run-created cohorts; older runs retried during a period need supplemental ingestion. Incomplete captures and unknown rate mappings remain visible. Before/after comparison does not establish causality without compatible workloads and suitable experimental evidence.

The skill is a research and engineering aid. Human review and a representative observation window remain necessary for changes to required checks, selection, runner capacity, and production workflows. No real-world savings are claimed for this new project.

## Development and attribution

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/release.py validate`. Packaging uses a fixed runtime allowlist and reproducible ZIP metadata. See [architecture](docs/architecture.md), [validation](docs/validation.md), [release procedure](docs/releasing.md), and [contributing](CONTRIBUTING.md).

The source checkout also includes an opt-in [skill evaluation suite](https://github.com/altmn/ci-health/blob/master/docs/skill-evaluations.md) for optimization discovery and prioritization, activation, missing inputs, and scope preservation. Behavioral runs use an authenticated Codex CLI and keep traces outside Git; ordinary CI runs only offline tests. CodeQL scans Python and GitHub Actions on pull requests, master updates, and a weekly schedule.

The original investigation was prompted by [Vincent Koc's OpenClaw article](https://vincent.build/openclaw-ci-cost-reduction/) and checked against a pinned implementation and additional primary sources. The skill generalizes the diagnosis and validation practices; it is not affiliated with OpenClaw, GitHub, or OpenAI. [MIT license](LICENSE), © 2026 Alex Allen. [Privacy](PRIVACY.md) · [Security](SECURITY.md) · [Support](SUPPORT.md).
