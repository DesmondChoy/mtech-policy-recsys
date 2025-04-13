import unittest
import sys
from pathlib import Path
import os  # Import os for path manipulation if needed, though Path should suffice

# Add project root to Python path to allow importing from scripts/src
# Assumes tests/ is one level down from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import shutil  # Import shutil for directory cleanup

# Now import the functions to be tested
try:
    from scripts.generate_recommendation_report import (
        parse_comparison_report,
        calculate_stage1_score,
        generate_markdown_report,  # Import the new function
        FinalRecommendation,  # Import the Pydantic model
    )

    # Define constants used by the script relative to PROJECT_ROOT
    RESULTS_DIR_TEST = PROJECT_ROOT / "results"
except ImportError as e:
    print(
        f"Failed to import functions/models from scripts.generate_recommendation_report: {e}"
    )

    # Define dummy functions/classes if import fails
    def parse_comparison_report(content):
        return {}

    def calculate_stage1_score(data):
        return 0.0

    def generate_markdown_report(*args, **kwargs):
        pass

    class FinalRecommendation:  # Dummy class
        def __init__(self, **kwargs):
            self.recommended_insurer = kwargs.get("recommended_insurer")
            self.recommended_tier = kwargs.get("recommended_tier")
            self.justification = kwargs.get("justification")

    RESULTS_DIR_TEST = None


# --- Test Data ---

# Sample report content for testing parse_comparison_report
SAMPLE_REPORT_GOOD = """
**Recommended Tier:** : Gold

**Justification:**
Comparison text... Gold is chosen because...

## Detailed Coverage Analysis for Recommended Tier: Gold

### Requirement: Medical Cover

*   **Policy Coverage:** Medical Expenses
    *   **Base Limits:** ...
    *   **Conditional Limits:** null
    *   **Source Specific Details:** ...
*   **Coverage Assessment:** Fully Met

### Requirement: Cancellation Cover

*   **Policy Coverage:** Trip Cancellation
    *   **Base Limits:** ...
    *   **Conditional Limits:** null
    *   **Source Specific Details:** ...
*   **Coverage Assessment:** Partially Met: Limit is $5000, requested $6000.

### Requirement: Baggage Delay

*   **Policy Coverage:** Baggage Delay Benefit
    *   **Base Limits:** ...
    *   **Conditional Limits:** null
    *   **Source Specific Details:** ...
*   **Coverage Assessment:** Not Met

## Summary for Recommended Tier: Gold

*   **Strengths:**
    *   Good medical.
*   **Weaknesses/Gaps:**
    *   [Cancellation Cover]: Limit lower than requested.
    *   [Baggage Delay]: Not covered.
"""

SAMPLE_REPORT_MISSING_ASSESSMENT_LINE = """
**Recommended Tier:** : Silver

**Justification:**
Silver chosen...

## Detailed Coverage Analysis for Recommended Tier: Silver

### Requirement: Medical Cover

*   **Policy Coverage:** Medical Expenses
    *   **Base Limits:** ...
*   **Coverage Assessment:** Fully Met

### Requirement: Cancellation Cover

*   **Policy Coverage:** Trip Cancellation
    *   **Base Limits:** ...
*(Missing Coverage Assessment line entirely)*

## Summary for Recommended Tier: Silver
...
"""

SAMPLE_REPORT_UNKNOWN_ASSESSMENT_PHRASE = """
**Recommended Tier:** : Bronze

**Justification:**
Bronze chosen...

## Detailed Coverage Analysis for Recommended Tier: Bronze

### Requirement: Medical Cover

*   **Policy Coverage:** Medical Expenses
    *   **Base Limits:** ...
*   **Coverage Assessment:** Mostly Covered (Invalid Phrase)

## Summary for Recommended Tier: Bronze
...
"""


# Sample parsed data for testing calculate_stage1_score
PARSED_DATA_MIXED = {
    "recommended_tier": "Gold",
    "requirements": {
        "Medical Cover": {"assessment": "Fully Met", "analysis_text": "..."},
        "Cancellation Cover": {"assessment": "Partially Met", "analysis_text": "..."},
        "Baggage Delay": {"assessment": "Not Met", "analysis_text": "..."},
    },
    "summary_weaknesses": [],  # Not used by new scoring logic
}

PARSED_DATA_ALL_MET = {
    "recommended_tier": "Platinum",
    "requirements": {
        "Medical Cover": {"assessment": "Fully Met", "analysis_text": "..."},
        "Evacuation": {"assessment": "Fully Met", "analysis_text": "..."},
    },
    "summary_weaknesses": [],
}

PARSED_DATA_WITH_UNKNOWN = {
    "recommended_tier": "Silver",
    "requirements": {
        "Medical Cover": {"assessment": "Fully Met", "analysis_text": "..."},
        "Cancellation Cover": {
            "assessment": "Assessment phrase not found",
            "analysis_text": "...",
        },  # Parser default
        "Gadget Cover": {
            "assessment": "Mostly Covered",
            "analysis_text": "...",
        },  # Invalid phrase
    },
    "summary_weaknesses": [],
}


# --- Test Class ---


class TestRecommendationReportScript(unittest.TestCase):
    # --- Tests for parse_comparison_report (Task 1) ---

    def test_parse_report_good(self):
        """Test parsing a well-formed report."""
        parsed = parse_comparison_report(SAMPLE_REPORT_GOOD)
        self.assertEqual(parsed.get("recommended_tier"), "Gold")
        self.assertIn("Medical Cover", parsed.get("requirements", {}))
        self.assertEqual(
            parsed["requirements"]["Medical Cover"]["assessment"], "Fully Met"
        )
        self.assertIn("Cancellation Cover", parsed.get("requirements", {}))
        self.assertEqual(
            parsed["requirements"]["Cancellation Cover"]["assessment"], "Partially Met"
        )
        self.assertIn("Baggage Delay", parsed.get("requirements", {}))
        self.assertEqual(
            parsed["requirements"]["Baggage Delay"]["assessment"], "Not Met"
        )
        # We don't strictly need to test weakness parsing for Task 1/2 focus, but it's good practice
        # self.assertIsInstance(parsed.get("summary_weaknesses"), list)

    def test_parse_report_missing_assessment_line(self):
        """Test parsing when the entire assessment line is missing."""
        parsed = parse_comparison_report(SAMPLE_REPORT_MISSING_ASSESSMENT_LINE)
        self.assertEqual(parsed.get("recommended_tier"), "Silver")
        self.assertIn("Medical Cover", parsed.get("requirements", {}))
        self.assertEqual(
            parsed["requirements"]["Medical Cover"]["assessment"], "Fully Met"
        )
        self.assertIn("Cancellation Cover", parsed.get("requirements", {}))
        # The parser should return the default "Assessment phrase not found"
        self.assertEqual(
            parsed["requirements"]["Cancellation Cover"]["assessment"],
            "Assessment phrase not found",
        )

    def test_parse_report_unknown_assessment_phrase(self):
        """Test parsing when the assessment line has an unknown phrase."""
        parsed = parse_comparison_report(SAMPLE_REPORT_UNKNOWN_ASSESSMENT_PHRASE)
        self.assertEqual(parsed.get("recommended_tier"), "Bronze")
        self.assertIn("Medical Cover", parsed.get("requirements", {}))
        # The regex won't match "Mostly Covered", so it should return the default
        self.assertEqual(
            parsed["requirements"]["Medical Cover"]["assessment"],
            "Assessment phrase not found",
        )

    # --- Tests for calculate_stage1_score (Task 2) ---

    def test_calculate_score_mixed(self):
        """Test score calculation with mixed assessments."""
        # Expected: 1.0 (Medical) + 0.5 (Cancellation) + 0.0 (Baggage) = 1.5
        score = calculate_stage1_score(PARSED_DATA_MIXED)
        self.assertAlmostEqual(score, 1.5)

    def test_calculate_score_all_met(self):
        """Test score calculation with all requirements fully met."""
        # Expected: 1.0 (Medical) + 1.0 (Evacuation) = 2.0
        score = calculate_stage1_score(PARSED_DATA_ALL_MET)
        self.assertAlmostEqual(score, 2.0)

    def test_calculate_score_with_unknown(self):
        """Test score calculation with unknown/missing assessment phrases."""
        # Expected: 1.0 (Medical) + 0.0 (Cancellation - unknown) + 0.0 (Gadget - unknown) = 1.0
        score = calculate_stage1_score(PARSED_DATA_WITH_UNKNOWN)
        self.assertAlmostEqual(score, 1.0)

    def test_calculate_score_empty_input(self):
        """Test score calculation with empty or invalid input."""
        score = calculate_stage1_score({})
        self.assertAlmostEqual(score, 0.0)
        score = calculate_stage1_score({"requirements": {}})
        self.assertAlmostEqual(score, 0.0)
        score = calculate_stage1_score({"recommended_tier": "X", "requirements": {}})
        self.assertAlmostEqual(score, 0.0)

    # --- Tests for generate_markdown_report (Task 6) ---

    def test_generate_markdown_report_output(self):
        """Test the generation and content of the Markdown report."""
        if RESULTS_DIR_TEST is None:
            self.skipTest(
                "Skipping test_generate_markdown_report_output due to import failure."
            )

        test_uuid = "test-markdown-uuid-123"
        test_results_dir = RESULTS_DIR_TEST / test_uuid
        test_output_path = test_results_dir / f"recommendation_report_{test_uuid}.md"

        # Ensure clean state before test
        if test_results_dir.exists():
            shutil.rmtree(test_results_dir)

        mock_stage1_results = [
            {
                "insurer": "alpha",
                "recommended_tier": "Gold",
                "score": 8.5,
                "report_path": "...",
            },
            {
                "insurer": "beta",
                "recommended_tier": "Silver",
                "score": 7.0,
                "report_path": "...",
            },
            {
                "insurer": "gamma",
                "recommended_tier": "Bronze",
                "score": 6.0,
                "report_path": "...",
            },
            {
                "insurer": "delta",
                "recommended_tier": "Basic",
                "score": 4.0,
                "report_path": "...",
            },
        ]
        mock_stage2_recommendation = FinalRecommendation(
            recommended_insurer="alpha",
            recommended_tier="Gold",
            justification="Alpha Gold is chosen due to superior coverage (Ref: Policy Pg. 5) compared to Beta Silver.",
        )

        try:
            generate_markdown_report(
                customer_uuid=test_uuid,
                stage1_results=mock_stage1_results,
                stage2_recommendation=mock_stage2_recommendation,
                top_n=3,
            )

            # 1. Check if file exists
            self.assertTrue(
                test_output_path.exists(),
                f"Markdown report file was not created at {test_output_path}",
            )

            # 2. Check file content (basic checks)
            with open(test_output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn(
                f"# Travel Insurance Recommendation for Customer {test_uuid}", content
            )
            self.assertIn("## Final Recommendation", content)
            self.assertIn(
                "**ALPHA - Gold**", content
            )  # Check recommended policy formatting
            self.assertIn("### Justification", content)
            self.assertIn("Alpha Gold is chosen", content)  # Check justification text
            self.assertIn(
                "(Ref: Policy Pg. 5)", content
            )  # Check source reference inclusion
            self.assertIn("## Analysis Summary", content)
            self.assertIn("**Scoring Method:**", content)
            self.assertIn("Fully Met**: +1.0 point", content)
            self.assertIn("**Top 3 Candidates", content)
            self.assertIn(
                "1. **ALPHA - Gold**: Score 8.5", content
            )  # Check top candidate format
            self.assertIn("2. **BETA - Silver**: Score 7.0", content)
            self.assertIn("3. **GAMMA - Bronze**: Score 6.0", content)
            self.assertIn("**Other Policies Analyzed", content)
            self.assertIn(
                "- **DELTA - Basic**: Score 4.0", content
            )  # Check other policy format

        finally:
            # Clean up created directory and file
            if test_results_dir.exists():
                shutil.rmtree(test_results_dir)


if __name__ == "__main__":
    # Ensure the script can be run directly for testing
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRecommendationReportScript)
    runner = unittest.TextTestRunner()
    runner.run(suite)
