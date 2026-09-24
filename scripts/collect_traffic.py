# ==================================================================================== #
# Collect public traffic snapshots without treating clone counts as active users.       #
# All API reads must succeed before any output is written. Secrets are never archived.  #
# ==================================================================================== #

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ENDPOINTS = {
    'clones': 'traffic/clones?per=day',
    'views': 'traffic/views?per=day',
    'referrers': 'traffic/popular/referrers',
    'paths': 'traffic/popular/paths',
}


def fetch(repository, token, endpoint):
    request = Request(
        f'https://api.github.com/repos/{repository}/{endpoint}',
        headers={'Authorization': f'Bearer {token}',
                 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2026-03-10',
                 'User-Agent': 'Lophiarch-traffic-archive'},
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def validate(data):
    for key in ('clones', 'views'):
        item = data[key]
        for field in ('count', 'uniques'):
            if type(item[field]) is not int or item[field] < 0:
                raise ValueError('Invalid traffic total')
        if not isinstance(item[key], list):
            raise ValueError('Invalid daily traffic')
        for day in item[key]:
            datetime.fromisoformat(day['timestamp'].replace('Z', '+00:00'))
            for field in ('count', 'uniques'):
                if type(day[field]) is not int or day[field] < 0:
                    raise ValueError('Invalid daily count')
    for key in ('referrers', 'paths'):
        if not isinstance(data[key], list):
            raise ValueError('Invalid referral data')


def publish_output(data, repository, output, now):
    validate(data)
    snapshot = {'schema_version': 1, 'source': 'github_rest_api',
                'repository': repository, 'captured_at': now.isoformat(),
                'window': 'GitHub rolling 14 days; UTC; current day may be partial',
                'data': data}
    output = Path(output)
    archive = output / 'snapshots'
    archive.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n'
    name = now.strftime('%Y-%m-%dT%H-%M-%S-%fZ') + '.json'
    (archive / name).write_text(encoded, encoding='utf-8')
    (output / 'latest.json').write_text(encoded, encoding='utf-8')
    lines = ['# Lophiarch traffic', '',
             f'Last successful capture (UTC): **{now.isoformat()}**', '',
             'GitHub rolling 14-day totals, not lifetime totals.', '',
             '| Metric | Count |', '|---|---:|',
             f"| Views | {data['views']['count']} |",
             f"| Unique visitors | {data['views']['uniques']} |",
             f"| Clones | {data['clones']['count']} |",
             f"| Unique cloners | {data['clones']['uniques']} |", '',
             'Clones may include CI and other automation; unique cloners are not active users.',
             'Do not sum unique counts across days or overlapping snapshots.',
             'For count trends, key daily entries by UTC date and use the newest observation per date.',
             'The current UTC day may be incomplete. Missing dates are unknown, not automatically zero.', '',
             '[Latest raw data](latest.json) · [Snapshot archive](snapshots/) · [Manual baseline](baseline.json)', '',
             'Top referrers and popular paths are included in the raw data.',
             'Check the capture timestamp: a failed or disabled workflow leaves the previous snapshot visible.', '']
    (output / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    repository = os.environ.get('GITHUB_REPOSITORY', '')
    token = os.environ.get('REPO_TRAFFIC_TOKEN', '')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise SystemExit('GITHUB_REPOSITORY must be owner/repository')
    if not token:
        raise SystemExit('Missing REPO_TRAFFIC_TOKEN repository secret')
    try:
        data = {key: fetch(repository, token, endpoint) for key, endpoint in ENDPOINTS.items()}
        publish_output(data, repository, args.output, datetime.now(timezone.utc))
    except HTTPError as error:
        raise SystemExit(f'Traffic API HTTP {error.code}; check token expiry and Administration read permission') from None
    except (URLError, TimeoutError, ValueError, KeyError, TypeError):
        raise SystemExit('Traffic capture failed; no new snapshot should be published') from None


if __name__ == '__main__':
    main()
