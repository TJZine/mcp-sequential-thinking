import tempfile
import unittest

from mcp_sequential_thinking import server
from mcp_sequential_thinking.storage import ThoughtStorage


class TestProcessThoughtLegacyPayload(unittest.TestCase):
    """Ensure legacy camelCase payloads remain compatible."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_storage = server.storage
        server.storage = ThoughtStorage(self.temp_dir.name)

    def tearDown(self):
        server.storage = self.original_storage
        self.temp_dir.cleanup()

    def test_process_thought_accepts_camelcase_arguments(self):
        """Legacy clients can send camelCase metadata without errors."""
        result = server.process_thought(
            thought="Legacy payload",
            thoughtNumber=1,
            totalThoughts=1,
            nextThoughtNeeded=False,
            stage="Scoping",
            filesTouched=["README.md"],
            testsToRun=["pytest"],
            riskLevel="high",
            confidenceScore=0.9,
            projectId="legacy-project",
        )

        self.assertIn("thoughtAnalysis", result)

        stored_thoughts = server.storage.get_all_thoughts(project_id="legacy-project")
        self.assertEqual(len(stored_thoughts), 1)
        stored = stored_thoughts[0]

        self.assertEqual(stored.files_touched, ["README.md"])
        self.assertEqual(stored.tests_to_run, ["pytest"])
        self.assertEqual(stored.risk_level.value, "high")
        self.assertAlmostEqual(stored.confidence_score, 0.9)


if __name__ == "__main__":
    unittest.main()
