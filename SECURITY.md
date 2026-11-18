# Security

Report a suspected vulnerability through [GitHub private vulnerability reporting](https://github.com/altmn/ci-health/security/advisories/new). Do not include credentials or private CI records in public issues. If that channel is unavailable, withhold sensitive details until a private channel is established.

The latest published version is supported on a best-effort basis. No response-time commitment is offered. The helper reads remote CI metadata through the authenticated GitHub CLI; use least-privilege access and treat all fetched content as untrusted data. Workflow edits, runner provisioning, and changes to branch rules require appropriate project authorization.

CodeQL scans Python and GitHub Actions on pull requests, updates to `master`, and weekly. The workflow pins actions to commit hashes and grants `security-events: write` only to the analysis job. Dependabot maintains action updates. Review analysis results and alerts; a successful scan is not a guarantee that the code is free of vulnerabilities.
