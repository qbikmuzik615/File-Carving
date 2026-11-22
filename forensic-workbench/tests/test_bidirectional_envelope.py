"""Synthetic unit tests for the read-only MP4 auditor. Never use real case bytes."""
import importlib.util
import struct
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"wyze_bidirectional_audit.py"
spec=importlib.util.spec_from_file_location("wyze_bidirectional_audit",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FormatTests(unittest.TestCase):
    def test_one_nal(self):
        data=(3).to_bytes(4,"big")+b"\x65\xaa\xbb"
        self.assertEqual(m.validate_video(data,0,len(data),4)[0],"valid_avcc")
    def test_multi_nal(self):
        data=b"\x00\x00\x00\x01\x09"+b"\x00\x00\x00\x02\x65\xab"
        st,_,types=m.validate_video(data,0,len(data),4)
        self.assertEqual(st,"valid_avcc")
        self.assertEqual(types,[9,5])
    def test_malformed_prefix(self):
        self.assertEqual(m.validate_video(b"\xff\xff\xff\xff\x65",0,5,4)[0],"bad_nal_length")
    def test_full_box_bounds(self):
        data=struct.pack(">I4s",12,b"free")+b"abcd"
        self.assertEqual(len(list(m.boxes(data,0,len(data)))),1)
        with self.assertRaises(m.ParseError):
            list(m.boxes(data[:-1],0,len(data)-1))
    def test_full_frame_cannot_be_established_by_envelope(self):
        data=b"\x00\x00\x00\x03\x65\xff\xff"
        self.assertEqual(m.validate_video(data,0,len(data),4)[0],"valid_avcc")
        # Syntactic envelope pass deliberately does not imply bitstream integrity.

if __name__=="__main__":
    unittest.main()
