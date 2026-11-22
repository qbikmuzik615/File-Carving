"""Offline synthetic-only regression tests: never copy evidence here."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "staircase_overlap.py"
spec = importlib.util.spec_from_file_location("staircase_overlap", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class StaircaseTests(unittest.TestCase):
    def test_exact_32k_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "00.mp4").write_bytes(b"A" * 32768 + b"B" * 32768)
            (p / "01.mp4").write_bytes(b"B" * 32768)
            report = module.analyze(p)
            self.assertTrue(report["adjacent_pairs"][0]["exact_suffix_shift_32768"])

    def test_no_overlap_same_step_sizes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "00.mp4").write_bytes(b"A" * 65536)
            (p / "01.mp4").write_bytes(b"B" * 32768)
            report = module.analyze(p)
            self.assertFalse(report["adjacent_pairs"][0]["exact_suffix_shift_32768"])
            self.assertEqual(report["adjacent_pairs"][0]["size_delta"], -32768)

    def test_160_byte_fragment_does_not_imply_mp4(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "32.mp4").write_bytes(b"A" * 16384)
            (p / "33.mp4").write_bytes(b"\xc1" * 160)
            report = module.analyze(p)
            self.assertEqual(report["files"][-1]["size"], 160)
            self.assertEqual(report["files"][-1]["signatures"]["ftyp"], 0)
            self.assertEqual(len(report["terminal_fragment_hits"]), 0)

if __name__ == "__main__":
    unittest.main()
