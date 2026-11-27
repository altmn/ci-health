# Install and manage CI Health

Prefer assistance? Use the [AI setup prompts](../README.md#get-started). This guide gives the direct steps and package choices.

## Choose an installation

| Route | What to use | Requirements |
| --- | --- | --- |
| Codex plugin | Build the source checkout and register its local marketplace below | Current Codex CLI with `codex plugin` support, Git, and Python 3.11+ for building/checking. |
| Compatible plugin import | The installable ZIP and detached checksum on the [release page](https://github.com/altmn/ci-health/releases/latest), if the host offers that route | Host-specific import support; no public OpenAI directory listing is claimed. |
| Standalone skills | Complete `skills/ci-health`, `skills/ci-health-preflight`, and `skills/ci-health-optimize` directories side by side | A host with a documented skills location. Python/`gh` are needed only for the optional measurement helper. |
| Source development | Clone the repository | Tests and maintenance tooling; the automatic source ZIP is not the installable plugin ZIP. |

Choose one form per host to avoid duplicate discovery. Check the package/version and detached SHA-256 checksum before importing. Published releases retain their own bytes; later source changes are not automatically in an older release. A checksum establishes archive integrity, not a publisher signature.

## Install in Codex from source

Clone a reviewed revision, run the offline checks, and build:

```bash
git clone https://github.com/altmn/ci-health.git
cd ci-health
python3 -m unittest discover -s tests -v
python3 scripts/release.py validate
python3 scripts/release.py build
codex plugin marketplace add "$PWD"
codex plugin add ci-health@ci-health-dev
codex plugin list --marketplace ci-health-dev --json
```

The development marketplace points at generated `dist/local-plugin`. Keep the checkout for updates. The portable manifest in root `plugin.json` is canonical; do not edit generated staging or plugin caches by hand. These commands register the local development marketplace with your Codex installation; use the host's supported mechanism if choosing another project/user installation scope.

## Verify first use

1. Start a new session if discovery has not refreshed.
2. Check that **CI Health**, **CI Health Preflight**, and **CI Health Optimize** appear. In Codex use `$ci-health`, `$ci-health-preflight`, or `$ci-health-optimize`, or select the skill through the picker (`/skills` in the CLI).
3. Try one [starter task](../README.md#try-it) with the repository available. Expect a scoped result with findings, evidence, limitations, and a next action. Installation or static inspection does not establish measured savings.

In a supported ChatGPT installation, an available plugin/skill is selected through `@`, including the ChatGPT tab of a desktop app. The Codex tab uses `$` or its picker. This project has not been submitted to a plugin directory; a browser chat can explain setup, but does not gain repository/local-tool access by reading a prompt.

## Optional measurement helper

The bundled helper uses Python 3.11+ with the standard library. Collection needs an existing authenticated GitHub CLI; private repositories require Actions read permission. Do not paste tokens into prompts. Choose an evidence directory outside source control because metadata can contain private names, labels, authors, and internal URLs.

```bash
python3 skills/ci-health/scripts/ci_health.py --help
python3 skills/ci-health/scripts/ci_health.py collect --help
python3 skills/ci-health/scripts/ci_health.py compare --help
```

Read the [measurement contract](../skills/ci-health/references/measurement.md) and [helper schema](../skills/ci-health/references/helper-schema.md) before collection. Collection is read-only GET access; there is no default log or artifact download. Missing observations remain unknown.

## Update, disable, or remove

### Update

Compare the installed version with [Releases](https://github.com/altmn/ci-health/releases). For source-based copies, review the desired revision, preserve local edits, rerun tests/validation/build, then use the current CLI's supported marketplace/plugin update path (`--help`). If removal/re-addition is needed, preserve unrelated installations and configuration. Source edits do not refresh cached installs automatically. Verify all three skills in a fresh session.

For standalone copies, preserve local modifications, replace only the installed project-owned directories through the host's supported route, and verify their relative references. Manage independently imported copies in that host.

### Disable temporarily

Use the installed host's plugin controls. In Codex CLI, open `/plugins` and use its toggle action for the installed entry. Managed installations may require an administrator.

### Remove the documented local plugin

```bash
codex plugin remove ci-health@ci-health-dev
```

If retiring its development marketplace too, remove the registration after uninstalling its plugins:

```bash
codex plugin marketplace remove ci-health-dev
```

This covers the documented local copy, not independent imports or standalone skill folders. Do not delete a shared cache manually. Remove standalone copies using their installation ownership record; keep evidence, user outputs, modified files, and unrelated skills. Verify in a fresh session; uninstalling does not erase instructions already loaded into a conversation.

See [OpenAI's plugin guidance](https://learn.chatgpt.com/docs/plugins) and the [package documentation](https://developers.openai.com/plugins/build/plugins) for the host mechanism. Current UI/version details can vary; use the [maintenance prompts](../README.md#update-or-remove) for guided help.
