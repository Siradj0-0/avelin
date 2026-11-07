# Contributing

Avelin is an early-stage Linux desktop application. Focused issues and pull requests are welcome, including documentation, accessibility, tests, packaging research and code. Please be respectful and describe what you tested without overstating platform support.

## Before starting

- Search existing issues and pull requests for related work. For a substantial change, describe your proposed scope in an issue or pull request early so contributors can coordinate and avoid duplicate work.
- For bugs, use the bug-report form and include the Avelin version or commit, distribution and version, desktop, installation method, steps to reproduce, expected behavior and actual behavior. Sanitize logs and screenshots first: remove usernames, paths, tokens, personal files and other private information.
- **Do not disclose a vulnerability or exploitable details in a public issue.** Follow [SECURITY.md](SECURITY.md) to report it privately.
- Back up important data and avoid critical systems when testing. Do not run the application as root. Review the effects of any system-changing test before running it.

## Development and tests

See [running from source](docs/source-setup.md) for prerequisites, launch instructions and troubleshooting. From the repository root, run the unit suite and compile check:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q avelin
```

On Debian or Ubuntu, use `/usr/bin/python3` if the system GTK bindings are not available to your default Python. The source setup guide also describes the GTK smoke test. Report the interpreter, commands, results, skipped tests and any missing dependencies. A headless smoke test is not a substitute for testing on a real desktop, by keyboard or with assistive technology.

Never run a real destructive action merely to make a test pass. Prefer isolated tests and mocks for commands that change settings or remove data; separately document any real-system testing, its scope and recovery plan. Do not treat mocks or a single successful distribution test as proof of broad compatibility.

## Opening a pull request

Keep changes focused and explain the problem, approach, limitations, linked issue if there is one, and exact test results. Identify any behavior changes and update relevant documentation. For system-changing actions, document prerequisites, distribution and desktop scope, exact commands and side effects, how changes are verified, undo or recovery steps, risks and authoritative references.

Do not invoke a shell with interpolated input, delete user data by default, or run system changes without informed consent. Be clear when a feature is experimental, unavailable or irreversible. Reviewers may ask for additional evidence or changes; passing CI does not by itself establish release readiness. See the [release and quality policy](docs/release-policy.md).
