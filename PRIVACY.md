# Privacy

CI Health has no publisher-operated backend, analytics, telemetry, or credential store. Its instruction files run within the host you choose; that host and any connected tools have their own data handling policies.

The optional collector invokes your existing `gh` authentication to make GitHub REST GET requests. It does not copy authentication tokens into its output, download logs or artifacts by default, or send captures to the publisher. Summarization and comparison operate on local files. Captures can still contain private repository, workflow, branch, author, runner-label, and URL metadata. Restrict access, retain only as needed, and review summaries before sharing.

Collect evidence outside source control. Ignoring a path does not untrack earlier commits. Review the source tree, reachable history, package members, and public issue attachments before publication. The included automated checks catch selected patterns; they do not certify absence of sensitive data.

Public GitHub issues and pull requests are public. Use synthetic reproductions and remove credentials, personal details, internal URLs, and customer information. Report vulnerabilities through the private channel described in [SECURITY.md](SECURITY.md).
