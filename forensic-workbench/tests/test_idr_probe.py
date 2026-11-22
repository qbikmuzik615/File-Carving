#!/usr/bin/env python3
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from idr_probe import extract_avcc

class AvccTests(unittest.TestCase):
    def test_avcc_extracts_sps_pps_and_nal_prefix_width(self):
        payload = bytes.fromhex(
            '01 4d 40 28 ff e1 00 16'
            ' 67 4d 40 28 9d a8 1e 00 89 f9 61 00 00 03 00 01 00 00 03 00 1e 84'
            ' 01 00 04 68 ee 3c 80')
        blob = (len(payload)+8).to_bytes(4,'big')+b'avcC'+payload
        v=extract_avcc(blob,0)
        self.assertEqual(v['nal_length_size'],4)
        self.assertEqual(v['sps'][0][0],0x67)
        self.assertEqual(v['pps'][0][0],0x68)
        self.assertEqual(v['avcc_offset'],0)

    def test_rejects_invalid_avcc(self):
        with self.assertRaises(ValueError):
            extract_avcc(b'not-an-avcc')

if __name__=='__main__':
    unittest.main(verbosity=2)
