# Migrating to Lophiarch

The repository, application branding, MCP server identity, PDF report names, Helm chart,
and scanner image defaults now use Lophiarch. Historical Git tags are unchanged.
The README header intentionally retains “Formerly Reconnator, v2.2.2”.

## Git and containers

Update your Git remote to `https://github.com/amiencoy/lophiarch.git`.
Build the scanner workers on each Docker host before starting the new runtime:

```bash
docker build -f Dockerfile.nmap -t lophiarch-nmap:latest .
docker build -f Dockerfile.ffuf -t lophiarch-ffuf:latest .
docker build -f Dockerfile.nuclei -t lophiarch-nuclei:latest .
docker build -t lophiarch:local .
```

The main-branch publish workflow targets `ghcr.io/amiencoy/lophiarch:latest` and
`sha-<commit>` tags. Verify a successful publish before pulling; no new SemVer
release is created by this rename. Prefer a verified immutable image digest for
production. Older published version images stay in their original registry path.

## Kubernetes

The Deployment name and selector change with the brand. This requires a planned
migration rather than an in-place selector patch. Save your Helm values and
back up any reports you need from the old pod before removing it (reports use
`emptyDir`). Stop the old bot before starting the replacement to avoid two
Telegram polling instances. Reinstall the updated chart using your saved secrets,
values and Docker socket group ID. Keep the old image and chart available for rollback.
The chart defaults to `latest` during this transition; pin a verified digest or
published tag for production. No workloads are migrated automatically.

## Integrations

Update integrations that match the MCP identity to `LophiarchCore`, scanner image
names to `lophiarch-*`, and PDF filename patterns to `Lophiarch_Report_*.pdf`.
Existing report files, secrets, scope approvals, and Git release tags are not renamed.
