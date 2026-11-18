# CI Health

A reusable Codex skill for auditing and optimizing overloaded continuous integration. Default audits prioritize avoidable execution, repeated preparation, slow tests and builds, critical paths, queueing, caching, and resource cost. Correctness checks preserve required validation while evaluating improvements.

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

The skill supports audit, baseline, optimization, and validation requests. It distinguishes suspected, supported, confirmed, and resolved findings. See the [skill entrypoint](skills/ci-health/SKILL.md) and [case study](skills/ci-health/references/openclaw-case-study.md).

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

For standalone skill hosts, copy the complete `skills/ci-health` directory into the host's documented skills location. Python and `gh` are needed only for the optional measurement helper; the instructions work without them. Do not install both forms into the same host unless you intend duplicate discovery.

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
