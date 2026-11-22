"""Purely synthetic unit tests; no network requests or evidence."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"scripts"/"research_radar.py"
spec=importlib.util.spec_from_file_location("research_radar",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ResearchRadarTests(unittest.TestCase):
    def test_reject_injected_repo_name(self):
        for bad in ("../", "owner/foo/bar", "example/repo?x=1", "no-slash"):
            with self.assertRaises(ValueError):m.sanitize({"repo":bad})

    def test_public_only_and_no_extra_fields(self):
        called=[]
        def fetch(path,token=None):
            called.append(path)
            return {"private":False,"html_url":"https://github.com/a/b",
                    "description":"A tool","stargazers_count":5,"license":{"spdx_id":"MIT"}}
        result=m.snapshot([{"repo":"a/b","domain":"audio"}],fetch)
        self.assertEqual(called,["/repos/a/b"])
        self.assertEqual(result[0]["license_spdx"],"MIT")
        self.assertNotIn("token",result[0])

    def test_no_private_metadata(self):
        def fetch(path,token=None):return {"private":True,"description":"PRIVATE DESCRIPTION"}
        out=m.snapshot([{"repo":"a/b"}],fetch)
        self.assertEqual(out,[{"repo":"a/b","status":"skipped_nonpublic"}])

if __name__=="__main__":unittest.main()
