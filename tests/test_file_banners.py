# ==================================================================================== #
# These tests verify that the repository banner validator accepts and rejects files.  #
# They keep the style gate deterministic without depending on the working tree state. #
# ==================================================================================== #

import tempfile
import unittest
from pathlib import Path

from scripts.check_file_banners import has_feature_banner, missing_banners


class FileBannerTests(unittest.TestCase):
    def test_accepts_reconnator_banner(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.py"
            path.write_text(
                "# ==================== #\nprint('valid')\n",
                encoding="utf-8",
            )

            self.assertTrue(has_feature_banner(path))
            self.assertEqual(missing_banners([path]), [])

    def test_reports_file_without_banner(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text("enabled: true\n", encoding="utf-8")

            self.assertFalse(has_feature_banner(path))
            self.assertEqual(missing_banners([path]), [path])


if __name__ == "__main__":
    unittest.main()
