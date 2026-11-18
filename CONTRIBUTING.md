# Contributing

Use a new feature branch and a pull request. Explain the concrete failure or missing capability, the resulting behavior, and meaningful validation. Keep changes proportional to evidence; do not turn one scenario into a universal restriction.

The runtime skills are under `skills/ci-health` and `skills/ci-health-preflight`. Keep audit and change-review scope distinct; shared technical references live under CI Health. Avoid duplicating manuals or loading all references for every request. Preserve distinctions among resource demand, elapsed feedback, actual eligibility, logical proof, and unknown observations.

Python helpers support 3.11+ with the standard library. Use synthetic, offline fixtures. Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/release.py validate
python3 scripts/release.py build
```

For material instruction changes, run an independent realistic trial in an isolated temporary workspace, with the skill and raw artifacts but no intended answer. Record tested file hashes, observed result, limitations, and any corrections in `docs/validation.md`. Structural checks alone do not validate model behavior.

Use the source checkout's [skill evaluation suite](https://github.com/altmn/ci-health/blob/master/docs/skill-evaluations.md) to repeat activation and scope checks. Live model runs are explicit and separate from the offline unit suite. Review the generated answers and traces against the held-out rubrics before recording behavioral success; command completion alone is insufficient.

Do not submit private captures, host paths, customer identifiers, credentials, or unrelated personal information. Review commit author metadata; GitHub noreply addresses can protect contributor email privacy. Use a minimal synthetic reproduction for bugs. Contributions are under the MIT license.
