# Security Policy

## Supported Versions

Reconnator is currently developed from the `main` branch and does not yet
publish a stable, versioned release series.

| Version | Supported |
| --- | --- |
| Latest commit on `main` | Yes |
| Older commits and snapshots | No |
| Pre-2.0 architecture | No |

This table will be updated when versioned releases are introduced.

## Reporting a Vulnerability

Do not disclose suspected vulnerabilities through a public issue, pull request,
discussion, social-media post, or other public channel.

Use one of these private reporting methods:

1. If the repository displays **Report a vulnerability**, submit a
   [private vulnerability report](https://github.com/amiencoy/Reconnator/security/advisories/new).
2. Otherwise, email the maintainer at
   [mamien131@gmail.com](mailto:mamien131@gmail.com) with the subject
   `[SECURITY][Reconnator] Short description`.

Include as much of the following information as possible:

- The affected commit, component, deployment method, and configuration.
- A clear description of the vulnerability and its potential impact.
- Reproduction steps or a minimal proof of concept.
- Relevant logs with credentials, tokens, target data, and personal information removed.
- Any known mitigations or suggested fixes.
- Your preferred name or handle for attribution, if any.

Use only systems and targets you own or are explicitly authorized to test.
Avoid destructive testing, service disruption, privacy violations, persistence,
or access to data beyond what is necessary to demonstrate the issue.

## What Qualifies as a Reconnator Vulnerability

Examples include:

- Command or argument injection through Reconnator input handling.
- Unauthorized scan execution or bypass of intended authorization controls.
- Exposure of Telegram tokens, Gemini API keys, reports, or target data.
- Unsafe interaction with the mounted Docker socket that expands privileges
  beyond Reconnator's documented behavior.
- A dependency or container supply-chain issue with a demonstrated impact on
  Reconnator users.
- A flaw in report generation, MCP tool routing, or scanner orchestration that
  creates a security boundary violation.

The following should not be reported as Reconnator vulnerabilities:

- Vulnerabilities discovered in a third-party target scanned by Reconnator.
- Normal Nmap, Nuclei, Ffuf, Subfinder, dnsx, or OTX findings.
- General product support requests, configuration mistakes, or feature requests.
- Findings that require unauthorized testing of systems you do not control.
- Vulnerabilities in an outdated third-party component without a demonstrated
  impact on a supported Reconnator version.

## Response and Disclosure Process

The maintainer will aim to:

- Acknowledge a report within five business days.
- Provide an initial assessment or request additional information within ten
  business days.
- Keep the reporter informed when meaningful progress is made.
- Coordinate the release of a fix and public disclosure when appropriate.

Resolution time depends on severity, reproducibility, and maintainer
availability. Please allow a reasonable remediation period before public
disclosure. Reports will be handled confidentially and attribution will be
provided when requested and appropriate.

This policy does not create a bug-bounty program or promise financial
compensation.
