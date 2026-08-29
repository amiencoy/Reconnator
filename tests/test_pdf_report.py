import os
import tempfile
import unittest
from pathlib import Path

from modules.report_generator import generate_scan_report


class PDFReportTests(unittest.IsolatedAsyncioTestCase):
    async def test_reportlab_generates_a_nonempty_pdf(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                report = await generate_scan_report(
                    {
                        "_metadata": {"duration": "1s"},
                        "nmap_example.com": ["443/tcp open https"],
                    }
                )
                artifact = Path(report)
                self.assertTrue(artifact.is_file())
                self.assertGreater(artifact.stat().st_size, 100)
                self.assertEqual(artifact.read_bytes()[:4], b"%PDF")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()

