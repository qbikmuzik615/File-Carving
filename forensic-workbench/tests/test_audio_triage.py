"""Synthetic test cases only: no real evidence is read."""
import importlib.util
import math
import shutil
import struct
import tempfile
import unittest
import wave
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"scripts"/"audio_triage.py"
spec=importlib.util.spec_from_file_location("audio_triage",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class AudioTriageTests(unittest.TestCase):
    def test_sample_rates(self):
        self.assertEqual(m.dsp_lowpass(48000),12000)
        self.assertEqual(m.dsp_lowpass(8000),3200)
        with self.assertRaises(ValueError):m.dsp_lowpass(0)
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Requires FFmpeg installed")
    def test_readonly_audio_extract(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/"source"/"synthetic.wav";src.parent.mkdir()
            with wave.open(str(src),"wb") as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000)
                w.writeframes(b"".join(struct.pack("<h",int(900*math.sin(2*math.pi*200*i/8000)))
                                      for i in range(800)))
            digest=m.sha256(src)
            report=m.run(src,root/"report",dsp=True,spectrogram=False,label="synthetic")
            self.assertEqual(report["source"]["sha256"],digest)
            self.assertEqual(m.sha256(src),digest)
            self.assertTrue((root/"report"/"synthetic_decoded_reference_f32.wav").is_file())
            self.assertTrue((root/"report"/"audio_triage_private_report.json").is_file())
            self.assertEqual(len(report["derivatives"]),4)
    def test_output_source_parent_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"test.txt";src.write_bytes(b"test")
            with self.assertRaises(ValueError):m.run(src,d)
if __name__=="__main__":unittest.main()
