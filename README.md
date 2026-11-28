# CI Health

Find CI bottlenecks and improve feedback without losing required checks.

> **A checkout change waits on two builds**
>
> Browser tests and API tests each rebuild the same application before running.
>
> **Candidate improvement:** build once and share the artifact between both test jobs, if their inputs and coverage match.

*A fictional pipeline example, not a measured speedup.*

[Try it](#try-it) · [Get started](#get-started) · [Get help](#get-help) · [Update or remove](#update-or-remove) · [Technical details](#technical-details)

---

<a id="use-it"></a>

## Try it

### Choose a workflow

In **Codex**, use the exact `$` name below or select the skill from the picker (`/skills` in the CLI).

| I want to… | Choose | What it does |
| --- | --- | --- |
| Understand an existing CI problem | **CI Health** — `$ci-health` | Establish a baseline, investigate, and prioritize findings. |
| Review changes before pushing | **CI Health Preflight** — `$ci-health-preflight` | Follow the changed work and identify added inefficiency. |
| Improve a specific bottleneck | **CI Health Optimize** — `$ci-health-optimize` | Design or implement a targeted improvement and validate it. |

### Prompt examples

These examples use the fictional checkout app above. Adapt the workflow details to your repository.

**Audit — paste into Codex with the repository open:**

```text
$ci-health Audit this repository's pull-request CI. Checkout changes wait
for browser and API tests, and both jobs build the app. Find worthwhile
improvements.
```

**Review a change — paste into Codex on the branch you want to review:**

```text
$ci-health-preflight Review this branch before I push it. It adds checkout
browser tests and a staging deployment job. Will it add avoidable CI work?
```

**Improve a pipeline — paste into Codex with implementation authorized:**

```text
$ci-health-optimize Speed up push-to-staging for this checkout app.
Investigate repeated builds and implement a suitable improvement.
```

<details>
<summary>Check an optimization already made</summary>

**In Codex:**

```text
$ci-health Validate the CI optimization on this branch against the baseline.
Has it improved useful feedback without losing coverage?
```

See [workflow details](docs/workflows.md) for routing, evidence, and acceptance.

</details>

---

<a id="install-in-codex"></a>

## Get started

Ask a coding agent to help, or follow the [manual installation guide](docs/getting-started.md). The [latest release](https://github.com/altmn/ci-health/releases/latest) includes the **installable plugin ZIP** and its **SHA-256 checksum**; GitHub's automatic source archives are a separate download.

### Ask a coding agent

**Paste into Codex or another agent with local tools:**

```text
Install CI Health for Codex globally:
https://github.com/altmn/ci-health
```

### Starting from ChatGPT in your browser?

**Paste into a chat at [chatgpt.com](https://chatgpt.com/):**

```text
Guide me on how to set up CI Health for my repository from ChatGPT web:
https://github.com/altmn/ci-health
```

**Current availability:** a browser chat can guide setup; the full workflow needs repository access and the relevant investigation tools. This project has not been submitted to an OpenAI plugin directory.

---

## Get help

If a skill does not appear, check installation and start a fresh session. If collection fails, check the optional helper's requirements and repository access rather than treating missing data as zero.

**Paste into the AI tool where you are using CI Health:**

```text
Help me troubleshoot CI Health:
https://github.com/altmn/ci-health

I'm using [AI tool and surface]. I expected [result], but got [actual result
or short error]. Investigate the issue.
```

[Get support](SUPPORT.md) or [report a problem](https://github.com/altmn/ci-health/issues/new/choose) with a minimal synthetic example. Keep private captures, internal URLs, and credentials out of reports. Report vulnerabilities through the [security policy](SECURITY.md).

---

## Update or remove

Want to update, disable, or remove CI Health? Ask the agent that manages your installation.

### To update

```text
Update CI Health:
https://github.com/altmn/ci-health
```

### To disable

```text
Temporarily disable CI Health in [my AI tool]:
https://github.com/altmn/ci-health
```

### To uninstall

```text
Uninstall CI Health from [my AI tool]:
https://github.com/altmn/ci-health
```

Prefer direct steps? See [updates and removal](docs/getting-started.md#update-disable-or-remove). A source edit does not automatically refresh a cached plugin.

---

<a id="limits"></a>

## Where it works

- **Codex:** the primary plugin route, using a current client with local plugin support and access to the relevant repository. This project has not been submitted to a plugin directory.
- **ChatGPT:** select an installed, available plugin or skill through `@`, including in the **ChatGPT tab** of the desktop app. The **Codex tab** uses `$` or its skill picker. A setup prompt does not install or activate a missing plugin.
- **Standalone skill hosts:** copy all three complete skill directories side by side through the host's supported mechanism. See [installation choices](docs/getting-started.md#choose-an-installation).
- **Measurement:** the optional GitHub Actions helper needs Python 3.11+ and an authenticated GitHub CLI with the required read access. Provider-neutral investigation does not require that helper.

CI Health is an engineering aid. Required-check, runner-capacity, and production-workflow changes need human review and representative acceptance evidence. A green workflow or before/after chart alone does not establish a causal improvement. [Known issues](docs/known-issues.md) retain discovery limitations and open work; no real-world savings are claimed for this new project.

---

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

---

<a id="development-and-attribution"></a>

## Contribute

Documentation, synthetic examples, and focused fixes are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md); use a new feature branch and a pull request against `master`.

Run the offline tests and release validation described there. Maintainers can find [release instructions](docs/releasing.md), the [source-only skill evaluation suite](https://github.com/altmn/ci-health/blob/master/docs/skill-evaluations.md), and the [presentation guide](docs/presentation.md). Ordinary CI uses offline tests; live behavioral evaluations are separate. CodeQL scans Python and GitHub Actions on pull requests, master updates, and a weekly schedule.

The original investigation was prompted by [Vincent Koc's OpenClaw article](https://vincent.build/openclaw-ci-cost-reduction/) and checked against pinned implementation evidence and primary sources; see the [case study](skills/ci-health/references/openclaw-case-study.md). CI Health is independent of OpenClaw, GitHub, and OpenAI.

[MIT license](LICENSE), © 2026 [Alex Allen (@altmn)](https://github.com/altmn). [Notices](NOTICE.md) · [Privacy](PRIVACY.md) · [Security](SECURITY.md) · [Support](SUPPORT.md).
