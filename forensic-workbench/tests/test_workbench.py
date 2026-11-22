import hashlib, json, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from workbench import Engine, sha256
from ai_triage import review
from scripts.image_scan import scan

class WorkbenchTests(unittest.TestCase):
 def test_sha_is_stable_and_nonmutating(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.mp4';p.write_bytes(b'forensic-evidence-immutable')
   self.assertEqual(sha256(p),hashlib.sha256(p.read_bytes()).hexdigest())
   self.assertEqual(p.read_bytes(),b'forensic-evidence-immutable')
 def test_raw_image_signature_offset(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'image.dd';p.write_bytes(bytes(512)+bytes.fromhex('0000001866747970')+b'isom0000isomavc1'+bytes(12))
   hits=list(scan(p))
   self.assertEqual(hits[0]['offset'],512)
   self.assertEqual(hits[0]['type'],'ftyp')
 def test_opt_in_is_mandatory(self):
  with self.assertRaises(PermissionError):review(Path('.'),explicit_consent=False)
 def test_real_e2e_empty_and_corrupt_file(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);inp=root/'input';inp.mkdir();out=root/'out'
   s=inp/'test.mp4';s.write_bytes(b'\x00'*1024)
   firsthash=sha256(s)
   e=Engine();job=e.create(str(inp),str(out),extract=False)
   for _ in range(100):
    if job.status not in ('queued','running'):break
    time.sleep(.2)
   self.assertEqual(job.status,'completed',job.error)
   self.assertEqual(sha256(s),firsthash)
   report=Path(job.output)
   self.assertTrue((report/'REPORT.md').is_file())
   self.assertTrue((report/'metadata/manifest.json').is_file())
   self.assertTrue((report/'reconstruction/crossfile_moov_mdat_matches.json').is_file())
   self.assertFalse([x for x in report.rglob('*.mp4') if x.is_file()])

if __name__=='__main__':unittest.main()