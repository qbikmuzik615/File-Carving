#!/usr/bin/env python3
import random
import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase_invariant_audit import MIN_RUN, audit, fingerprints

class ExactMatchTests(unittest.TestCase):
    def save(self, root, name, data):
        p = root / name
        p.write_bytes(data)
        return p

    def test_exactly_256_arbitrary_phase(self):
        for seed in range(15):
            rng=random.Random(seed)
            shared=rng.randbytes(256)
            a=rng.randbytes(37+seed)+shared+rng.randbytes(43)
            b=rng.randbytes(71+3*seed)+shared+rng.randbytes(79)
            with tempfile.TemporaryDirectory() as td:
                root=Path(td)
                paths=[self.save(root,'a.mp4',a),self.save(root,'b.mp4',b)]
                result=audit(paths)
                self.assertEqual(result['status'],'complete')
                self.assertTrue(any(r['length']>=256 and r['offset_a']==37+seed and r['offset_b']==71+3*seed for r in result['matches']),seed)

    def test_long_shared_span_and_zero_padding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            paths=[self.save(root,'a.mp4',b'A'*301+b'\0'*2048+b'B'*500),
                   self.save(root,'b.mp4',b'Z'*87+b'\0'*2048+b'Y'*900)]
            result=audit(paths)
            self.assertTrue(any(r['length']==2048 for r in result['matches']))

    def test_identical_at_zero_and_different_offsets(self):
        rng=random.Random(234)
        d=rng.randbytes(4096)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            r=audit([self.save(root,'a.mp4',d),self.save(root,'b.mp4',d)])
            self.assertTrue(any(x['length']==4096 and x['offset_a']==0 and x['offset_b']==0 for x in r['matches']))

    def test_below_256_unable_to_prove(self):
        self.assertEqual(list(fingerprints(b'Q'*255)),[])

    def test_single_file_zero_cross_file_pairs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            r=audit([self.save(root,'a.mp4',b'Z'*512)])
            self.assertEqual(r['match_count'],0)

if __name__=='__main__':
    unittest.main(verbosity=2)
