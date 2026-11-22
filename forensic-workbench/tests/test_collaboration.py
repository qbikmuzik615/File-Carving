"""Synthetic offline test for the local public-safe collaboration status API."""
import unittest
from app import collaboration

class CollaborationTests(unittest.TestCase):
    def test_public_metadata_only(self):
        result=collaboration()
        self.assertIn("agent_connections",result)
        self.assertIn("Gemini",result["agent_connections"])
        self.assertIn("Claude",result["agent_connections"])
        self.assertNotIn("original_video_bytes",result)
        self.assertEqual(result["evidence_policy"],"PRIVATE_LOCAL_OR_DEDICATED_PRIVATE_REPO")
        self.assertIsInstance(result["recent_handoffs"],list)

if __name__=="__main__":
    unittest.main()
