import hashlib, json, struct, subprocess, sys, tempfile, time, unittest, zipfile
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
 def test_cross_file_scanning_deterministic(self):
  from scripts.crossfile_reconstructor import scan_one
  root=Path('/mnt/data/wyze_0820_0840_source_links/30.mp4')
  if not root.exists():return
  record=scan_one(root)
  self.assertTrue(any(z.get('ftyp_offset')==540160 for z in record['mdat']))

 def test_zip_backup_e2e(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);src=root/'raw.zip'
   with zipfile.ZipFile(src,'w') as z:z.writestr('record/20220621/08/20.mp4',b'\x00'*1024)
   h=sha256(src);e=Engine();j=e.create(str(src),str(root/'reports'))
   for _ in range(120):
    if j.status not in ('queued','running'):break
    time.sleep(.2)
   self.assertEqual(j.status,'completed',j.error)
   self.assertEqual(j.results['source_count'],1)
   self.assertEqual(j.results['timeline']['number_matched'],1)
   self.assertEqual(sha256(src),h)
 def test_image_only_e2e(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);src=root/'card.img'
   src.write_bytes(bytes(512)+struct.pack('>I',24)+b'ftyp'+b'isom0000isomavc1'+bytes(3000))
   h=sha256(src);e=Engine();j=e.create(str(src),str(root/'reports'))
   for _ in range(120):
    if j.status not in ('queued','running'):break
    time.sleep(.2)
   self.assertEqual(j.status,'completed',j.error)
   self.assertEqual(j.results['source_count'],0)
   self.assertGreaterEqual(j.results['image']['ftyp_count'],1)
   self.assertEqual(sha256(src),h)
 def test_zip_traversal_rejected(self):
  from workbench import extract_zip_media
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'bad.zip';tmp=root/'scratch';tmp.mkdir()
   with zipfile.ZipFile(p,'w') as z:z.writestr('../evil.mp4',b'bad')
   with self.assertRaises(ValueError):extract_zip_media(p,tmp)

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