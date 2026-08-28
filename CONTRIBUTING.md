# Contributing to Reconnator

Thank you for helping improve Reconnator. Contributions can include code,
documentation, tests, bug reports, integration proposals, and reviews.

By participating, you agree to follow the
[Code of Conduct](CODE_OF_CONDUCT.md). Security vulnerabilities must be reported
privately according to the [Security Policy](SECURITY.md).

## Security and Authorization

Reconnator is a security reconnaissance tool. Develop and test only against
systems you own or are explicitly authorized to assess.

Do not include real credentials, API keys, private reports, customer data,
unauthorized target information, exploit payloads intended for harm, or
destructive behavior in issues, pull requests, fixtures, examples, or logs.

## Ways to Contribute

- Fix reproducible bugs.
- Improve documentation and deployment instructions.
- Add tests or strengthen error handling.
- Propose or implement scanner and MCP tool integrations.
- Improve container builds, Helm resources, reporting, and observability.
- Review issues and pull requests.

For substantial architecture changes, new scanners, or changes to security
boundaries, open an issue before writing the implementation.

## Development Setup

Prerequisites:

- Git
- Python 3.11 or later
- Docker Engine
- Helm, only when modifying the Helm chart

Fork the repository and prepare a local environment:

```bash
git clone https://github.com/<your-username>/Reconnator.git
cd Reconnator
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Use development-only Telegram and Gemini credentials. Never commit the resulting
`.env` file.

The main container can be built with:

```bash
docker build -t reconnator:test .
```

When modifying a scanner worker, build only the affected image:

```bash
docker build -f Dockerfile.nmap -t reconnator-nmap:latest .
docker build -f Dockerfile.ffuf -t reconnator-ffuf:latest .
docker build -f Dockerfile.nuclei -t reconnator-nuclei:latest .
```

## Branches and Commits

Create a focused branch from the latest `main`:

```bash
git switch main
git pull --ff-only
git switch -c fix/short-description
```

Recommended branch prefixes are `feat/`, `fix/`, `docs/`, `test/`,
`refactor/`, and `security/`.

Write concise, imperative commit messages. Conventional Commit-style prefixes
such as `feat:`, `fix:`, `docs:`, `test:`, and `chore:` are encouraged
but not required.

## Code Expectations

- Keep changes focused and avoid unrelated rewrites.
- Follow existing Python structure and asynchronous patterns.
- Prefer explicit error handling and structured logging.
- Preserve container isolation and authorization boundaries.
- Avoid adding dependencies without explaining the need and security impact.
- Never log secrets, full credentials, or unnecessary target data.
- Update documentation when behavior, configuration, or deployment changes.

## Validation

There is not yet a complete automated test suite. Before opening a pull request,
run the checks relevant to your change and document the results:

```bash
python -m compileall src
docker build -t reconnator:test .
```

For Helm changes:

```bash
helm lint deploy/helm
```

For scanner changes, build the affected worker image and test it only against an
authorized, non-production target. Add automated tests when practical. If a
change cannot be tested locally, explain why in the pull request.

## Opening a Pull Request

Before submitting:

1. Rebase or update your branch from the latest `main`.
2. Keep the pull request limited to one coherent change.
3. Link the relevant issue, or explain why no issue is needed.
4. Complete the pull request template.
5. Describe security implications and authorization assumptions.
6. Include validation commands and results.
7. Update documentation and examples when necessary.

Maintainers may request changes, close out-of-scope proposals, or ask that a
large pull request be split into smaller changes.

## Licensing

Reconnator is available under your choice of the
[MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE).

Unless you explicitly state otherwise, contributions intentionally submitted for
inclusion in Reconnator are provided under the same dual-license expression:
`MIT OR Apache-2.0`, without additional terms or conditions.
