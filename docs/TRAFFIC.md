# Public repository traffic

[Open the traffic dashboard](https://github.com/amiencoy/lophiarch/tree/traffic-data)
after the first successful collection. That public branch contains a generated
README, latest.json, timestamped snapshots, and the manual baseline.

## Setup and first run

1. Store a fine-grained PAT as the repository Actions secret REPO_TRAFFIC_TOKEN.
   Select only Lophiarch and grant Administration: read. Do not give it write access.
2. Merge the collector workflow into main.
3. Open Actions > Archive repository traffic > Run workflow, selecting main.
4. Verify both collection and publication succeeded, then open traffic-data.

Scheduled collection is at 02:17 UTC (09:17 WIB); GitHub may delay scheduled runs.
The workflow does not run for pull requests or fork repositories.
GITHUB_TOKEN with contents: write publishes the archive. The PAT only reads traffic.
If branch rules disallow that write, the run fails; configure an approved publishing
route rather than disabling main protections. Rotate the PAT when it expires.
Check Actions if captures become stale; GitHub may disable inactive scheduled workflows.

## Data interpretation

The four endpoints return rolling 14-day clones/views, top referrers and popular paths.
All four reads and basic validation must succeed before publication. API failures
leave the last successful public snapshot unchanged, with its original timestamp.
No token or request headers are written to the archive.

Each capture is kept separately. To derive a daily series, use the newest observation
for each UTC date; never add overlapping window totals. Current-day counts may be
partial. Missing observations must not be filled as zero without evidence.
Daily or overlapping-window unique counts cannot be summed into lifetime uniques.
Clones include possible automation and are not proof of active users or installations.
The collector itself uses checkout, so measurement can contribute background activity.

The baseline in traffic-baseline.json was manually transcribed from owner-supplied
screenshots covering August 23–September 5, 2026. It is kept separate from API snapshots.
It has no referrer data, and its exact capture time is unknown. It is not lifetime traffic.

All archived traffic, including referrers and popular paths, is public by design.
Source: https://docs.github.com/en/rest/metrics/traffic

---

<p align="center"><sub>Built with code, coffee, and a healthy dislike of repetitive work.</sub></p>
