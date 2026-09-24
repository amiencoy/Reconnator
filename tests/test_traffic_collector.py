# ==================================================================================== #
# Verify traffic archives preserve API uniques and reject incomplete or invalid data.   #
# Tests use fixtures only and never call GitHub or require a token.                      #
# ==================================================================================== #

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'collect_traffic', Path(__file__).resolve().parents[1] / 'scripts/collect_traffic.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class TrafficTests(unittest.TestCase):
    def fixture(self):
        return {key: {'count': 8, 'uniques': 3, key: [
            {'timestamp': '2026-09-01T00:00:00Z', 'count': 4, 'uniques': 3},
            {'timestamp': '2026-09-02T00:00:00Z', 'count': 4, 'uniques': 3},
        ]} for key in ('clones', 'views')} | {'referrers': [], 'paths': []}

    def test_preserves_window_uniques_and_multiple_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            for day in (3, 4):
                collector.publish_output(self.fixture(), 'amiencoy/lophiarch', folder,
                                         datetime(2026, 9, day, tzinfo=timezone.utc))
            self.assertEqual(len(list((Path(folder) / 'snapshots').glob('*.json'))), 2)
            latest = json.loads((Path(folder) / 'latest.json').read_text())
            self.assertEqual(latest['data']['views']['uniques'], 3)
            self.assertIn('| Unique visitors | 3 |', (Path(folder) / 'README.md').read_text())

    def test_invalid_data_does_not_replace_previous_output(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'latest.json'
            target.write_text('previous snapshot')
            invalid = self.fixture()
            invalid['clones']['count'] = -1
            with self.assertRaises(ValueError):
                collector.publish_output(invalid, 'amiencoy/lophiarch', folder,
                                         datetime.now(timezone.utc))
            self.assertEqual(target.read_text(), 'previous snapshot')
            self.assertFalse((Path(folder) / 'snapshots').exists())


if __name__ == '__main__':
    unittest.main()
