import unittest
from mcp_sequential_thinking.models import RiskLevel, ThoughtData, ThoughtStage
from mcp_sequential_thinking.analysis import ThoughtAnalyzer


class TestThoughtAnalyzer(unittest.TestCase):
    """Test cases for the ThoughtAnalyzer class."""
    
    def setUp(self):
        """Set up test data."""
        self.thought1 = ThoughtData(
            thought="First thought about climate change",
            thought_number=1,
            total_thoughts=5,
            next_thought_needed=True,
            stage=ThoughtStage.SCOPING,
            tags=["climate", "global"],
            files_touched=["README.md"],
        )

        self.thought2 = ThoughtData(
            thought="Research on emissions data",
            thought_number=2,
            total_thoughts=5,
            next_thought_needed=True,
            stage=ThoughtStage.RESEARCH_SPIKE,
            tags=["climate", "data", "emissions"],
            dependencies=["epa-api"],
        )

        self.thought3 = ThoughtData(
            thought="Implementation of policy impacts",
            thought_number=3,
            total_thoughts=5,
            next_thought_needed=True,
            stage=ThoughtStage.IMPLEMENTATION,
            tags=["policy", "impact"],
            files_touched=["policy.py"],
            tests_to_run=["pytest tests/test_policy.py"],
            risk_level=RiskLevel.HIGH,
        )

        self.thought4 = ThoughtData(
            thought="Another scoping thought",
            thought_number=4,
            total_thoughts=5,
            next_thought_needed=True,
            stage=ThoughtStage.SCOPING,
            tags=["problem", "definition"],
            dependencies=["stakeholder-alignment"],
        )
        
        self.all_thoughts = [self.thought1, self.thought2, self.thought3, self.thought4]
    
    def test_find_related_thoughts_by_stage(self):
        """Test finding related thoughts by stage."""
        related = ThoughtAnalyzer.find_related_thoughts(self.thought1, self.all_thoughts)
        
        # Should find thought4 which is in the same stage
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0], self.thought4)
    
    def test_find_related_thoughts_by_tags(self):
        """Test finding related thoughts by tags."""
        # Create a new thought with tags that match thought1 and thought2
        new_thought = ThoughtData(
            thought="New thought with climate tag",
            thought_number=5,
            total_thoughts=5,
            next_thought_needed=False,
            stage=ThoughtStage.REVIEW,
            tags=["climate", "synthesis"],
            dependencies=["epa-api"],
        )
        
        all_thoughts = self.all_thoughts + [new_thought]
        
        related = ThoughtAnalyzer.find_related_thoughts(new_thought, all_thoughts)
        
        # Should find thought1 and thought2 which have the "climate" tag
        self.assertEqual(len(related), 2)
        self.assertTrue(self.thought1 in related)
        self.assertTrue(self.thought2 in related)
    
    def test_generate_summary_empty(self):
        """Test generating summary with no thoughts."""
        summary = ThoughtAnalyzer.generate_summary([])
        
        self.assertEqual(summary, {"summary": "No thoughts recorded yet"})
    
    def test_generate_summary(self):
        """Test generating summary with thoughts."""
        summary = ThoughtAnalyzer.generate_summary(self.all_thoughts)
        
        self.assertEqual(summary["summary"]["totalThoughts"], 4)
        self.assertEqual(summary["summary"]["stages"]["Scoping"], 2)
        self.assertEqual(summary["summary"]["stages"]["Research & Spike"], 1)
        self.assertEqual(summary["summary"]["stages"]["Implementation"], 1)
        self.assertEqual(len(summary["summary"]["timeline"]), 4)
        self.assertIn("topTags", summary["summary"])
        self.assertIn("riskProfile", summary["summary"])
    
    def test_analyze_thought(self):
        """Test analyzing a thought."""
        analysis = ThoughtAnalyzer.analyze_thought(self.thought1, self.all_thoughts)
        
        self.assertEqual(analysis["thoughtAnalysis"]["currentThought"]["thoughtNumber"], 1)
        self.assertEqual(analysis["thoughtAnalysis"]["currentThought"]["stage"], "Scoping")
        self.assertEqual(analysis["thoughtAnalysis"]["analysis"]["relatedThoughtsCount"], 1)
        self.assertEqual(analysis["thoughtAnalysis"]["analysis"]["progress"], 20.0)  # 1/5 * 100
        self.assertTrue(analysis["thoughtAnalysis"]["analysis"]["isFirstInStage"])
        self.assertEqual(analysis["thoughtAnalysis"]["context"]["thoughtHistoryLength"], 4)
        self.assertIn("stageCoverage", analysis["thoughtAnalysis"]["analysis"])
        self.assertIn("insights", analysis)


if __name__ == "__main__":
    unittest.main()
