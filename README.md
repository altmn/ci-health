# CI Health

Find what slows down CI and improve feedback without losing required checks. Audit an overloaded pipeline, review a proposed change, or tackle a specific bottleneck.

[Try it](#try-it) · [Get started](#get-started) · [Get help](#get-help) · [Update or remove](#update-or-remove) · [Technical details](#technical-details)

| A pipeline review, from question to evidence | Example |
| --- | --- |
| **Observe** | Two jobs appear to rebuild the same test bundle. |
| **Investigate** | Compare their inputs, outputs, and required checks. |
| **Improve** | Reuse the bundle if its identity and coverage match. |
| **Verify** | Check warm reuse, cold fallback, failures, and time to a useful result. |

*Illustrative example using a made-up pipeline. A proposed reuse path needs evidence before it becomes an accepted improvement; no measured savings are claimed.*

<a id="use-it"></a>

## Try it

Choose the task that matches your goal. In **Codex**, use the exact `$` name below or select the skill from the picker (`/skills` in the CLI).

| I want to… | Choose | What it does |
| --- | --- | --- |
| Understand an existing CI problem | **CI Health** — `$ci-health` | Establish a baseline, investigate, and prioritize findings. |
| Review changes before pushing | **CI Health Preflight** — `$ci-health-preflight` | Follow the changed work and identify added inefficiency. |
| Improve a specific bottleneck | **CI Health Optimize** — `$ci-health-optimize` | Design or implement a targeted improvement and validate it. |

**Audit — paste into Codex with the repository open:**

```text
$ci-health Review this repository's CI for slow feedback and avoidable work.
Establish a baseline, prioritize findings, and explain the evidence and
trade-offs before proposing changes.
```

**Review a change — paste into Codex on the branch you want to review:**

```text
$ci-health-preflight Review these changes before I push them. Identify
added CI work, unnecessary duplication, and effects on required checks.
Keep the recommendation specific to this change and show the evidence.
```

**Improve a pipeline — paste into Codex with implementation authorized:**

```text
$ci-health-optimize Shorten the time from a push to staging in this
repository. Find and implement the highest-impact suitable change, preserve
the required checks, and show how to validate it against a baseline.
```

Need to check an optimization already made? Ask `$ci-health` to validate it against the baseline, including workload, capacity, missing coverage, retries, and queue age. See [workflow details](docs/workflows.md) for routing, evidence, and acceptance.

<a id="install-in-codex"></a>

## Get started

Ask a coding agent to help, or follow the [manual installation guide](docs/getting-started.md). The [latest release](https://github.com/altmn/ci-health/releases/latest) includes the **installable plugin ZIP** and its **SHA-256 checksum**; GitHub's automatic source archives are a separate download.

**Set up for me — paste into Codex or another agent with local tools:**

```text
Set up CI Health for Codex using its current instructions:
https://github.com/altmn/ci-health

Check what is already installed and help me choose the installation scope.
Use the supported package and process, preserve existing personal changes,
and verify that CI Health, Preflight, and Optimize are available in a fresh
session. Then give me a small first-use example for this repository.
```

<details>
<summary>Starting from ChatGPT in your browser?</summary>

An ordinary browser chat can help you choose a setup route. The complete workflow needs access to the repository and the tools relevant to your investigation; this project has not been submitted to an OpenAI plugin directory.

**Paste into a chat at [chatgpt.com](https://chatgpt.com/):**

```text
I want to use CI Health to improve my repository's CI:
https://github.com/altmn/ci-health

I'm using ChatGPT in a browser. Read the current project instructions and
explain which parts I can use here and whether I need Codex or another tool
with repository access. Guide me to the appropriate setup and tell me what
information to provide first.
```

ChatGPT uses `@` selection for an installed, available plugin or skill, including in the **ChatGPT tab** of the desktop app. The **Codex tab** uses `$` or its skill picker. Pasting a setup prompt or an unselected name does not install or activate a missing plugin.

</details>

## Get help

If a skill does not appear, check installation and start a fresh session. If collection fails, check the optional helper's requirements and repository access rather than treating missing data as zero.

**Paste into the AI tool where you are using CI Health:**

```text
Help me troubleshoot CI Health:
https://github.com/altmn/ci-health

I'm using [AI tool and surface]. I expected [result], but got [actual
result or short error]. Check installation and skill selection first,
then the access or helper requirements relevant to my task. Use the
smallest useful diagnostic and explain the next step.
```

[Get support](SUPPORT.md) or [report a problem](https://github.com/altmn/ci-health/issues/new/choose) with a minimal synthetic example. Keep private captures, internal URLs, and credentials out of reports. Report vulnerabilities through the [security policy](SECURITY.md).

## Update or remove

**Ask the coding agent that manages your installation:**

```text
Check whether my CI Health installation is up to date:
https://github.com/altmn/ci-health

Identify the installed version and installation method, compare it with the
latest published release, and follow the documented update process. Preserve
local changes, refresh the cached plugin if needed, and verify that all three
skills remain available. Explain any step I need to complete myself.
```

```text
Help me temporarily disable or uninstall CI Health from [my AI tool].
Identify the installation method, follow the project's removal guidance,
keep my CI evidence and unrelated settings, and help me confirm the result
in a fresh session.
```

Prefer direct steps? See [updates and removal](docs/getting-started.md#update-disable-or-remove). A source edit does not automatically refresh a cached plugin.

<a id="limits"></a>

## Where it works

- **Codex:** the primary plugin route, using a current client with local plugin support and access to the relevant repository. This project has not been submitted to a plugin directory.
- **Standalone skill hosts:** copy all three complete skill directories side by side through the host's supported mechanism. See [installation choices](docs/getting-started.md#choose-an-installation).
- **Measurement:** the optional GitHub Actions helper needs Python 3.11+ and an authenticated GitHub CLI with the required read access. Provider-neutral investigation does not require that helper.

CI Health is an engineering aid. Required-check, runner-capacity, and production-workflow changes need human review and representative acceptance evidence. A green workflow or before/after chart alone does not establish a causal improvement. [Known issues](docs/known-issues.md) retain discovery limitations and open work; no real-world savings are claimed for this new project.

<a id="measurement-helper"></a>

## Technical details

The optional helper provides `collect`, `summarize`, and `compare`. Collection makes GET requests through the user's existing GitHub CLI and writes to an explicitly chosen evidence directory. It does not download logs or artifacts by default. The plugin operates no hosted service and collects no telemetry for its publisher.

```bash
python3 skills/ci-health/scripts/ci_health.py --help
python3 skills/ci-health/scripts/ci_health.py collect --help
python3 skills/ci-health/scripts/ci_health.py compare --help
```

| I want to… | Read this |
| --- | --- |
| Install or manage the plugin | [Getting started](docs/getting-started.md) |
| Understand workflow selection and acceptance | [Workflow guide](docs/workflows.md) |
| Measure and compare CI | [Measurement contract](skills/ci-health/references/measurement.md) · [Commands and schemas](skills/ci-health/references/helper-schema.md) |
| Improve an existing pipeline | [Optimization playbook](skills/ci-health/references/optimization.md) · [Bun recipe](skills/ci-health/references/bun-ci.md) |
| Inspect implementation and limits | [Architecture](docs/architecture.md) · [Validation](docs/validation.md) · [Known issues](docs/known-issues.md) |
| Understand data handling | [Privacy](PRIVACY.md) · [Terms](TERMS.md) |

GitHub job intervals are execution proxies, not exact eligible queue time, checkout identity, required-verdict history, provider invoices, or complete calendar-period activity. The helper collects run-created cohorts; older runs retried during a period need supplemental evidence. Incomplete captures and unknown rate mappings stay visible.

<a id="development-and-attribution"></a>

## Contribute

Documentation, synthetic examples, and focused fixes are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md); use a new feature branch and a pull request against `master`.

Run the offline tests and release validation described there. Maintainers can find [release instructions](docs/releasing.md), the [source-only skill evaluation suite](https://github.com/altmn/ci-health/blob/master/docs/skill-evaluations.md), and the [presentation guide](docs/presentation.md). Ordinary CI uses offline tests; live behavioral evaluations are separate. CodeQL scans Python and GitHub Actions on pull requests, master updates, and a weekly schedule.

The original investigation was prompted by [Vincent Koc's OpenClaw article](https://vincent.build/openclaw-ci-cost-reduction/) and checked against pinned implementation evidence and primary sources; see the [case study](skills/ci-health/references/openclaw-case-study.md). CI Health is independent of OpenClaw, GitHub, and OpenAI.

[MIT license](LICENSE), © 2026 [Alex Allen (@altmn)](https://github.com/altmn). [Notices](NOTICE.md) · [Privacy](PRIVACY.md) · [Security](SECURITY.md) · [Support](SUPPORT.md).
