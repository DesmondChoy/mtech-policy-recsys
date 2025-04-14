import json
import os
import glob
import re
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
TRANSCRIPT_DIR = Path("data/transcripts/raw/synthetic")
# Updated path for the ground truth file
GROUND_TRUTH_PATH = Path(
    "data/evaluation/scenario_evaluation/scenario_ground_truth.json"
)
RECOMMENDATION_REPORT_PATTERN = "recommendation_report_*.md"
RECOMMENDED_POLICY_REGEX = (
    r"\*\*([a-zA-Z\s]+)\s*-\s*([a-zA-Z\s!]+)\*\*"  # Matches **INSURER - Tier**
)


def find_transcript_filename(uuid_str: str) -> Path | None:
    """Finds the transcript filename corresponding to a UUID."""
    # Search for transcript_{scenario_name}_{uuid_str}.json
    pattern = TRANSCRIPT_DIR / f"transcript_*_{uuid_str}.json"
    matches = list(TRANSCRIPT_DIR.glob(f"transcript_*_{uuid_str}.json"))
    if matches:
        return matches[0]
    logging.warning(f"Could not find transcript file for UUID: {uuid_str}")
    return None


def extract_scenario_from_filename(filename: Path) -> str | None:
    """Extracts the scenario name from the transcript filename."""
    # Expected format: transcript_{scenario_name}_{uuid}.json
    parts = filename.stem.split("_")
    if len(parts) >= 3 and parts[0] == "transcript":
        # Join parts between 'transcript_' and the UUID
        scenario_name = "_".join(parts[1:-1])
        # Handle potential variations like 'no_scenario' if needed
        return scenario_name
    logging.warning(f"Could not extract scenario name from filename: {filename.name}")
    return None


def parse_recommendation_report(report_path: Path) -> tuple[str | None, str | None]:
    """Parses the recommended insurer and tier from the Markdown report."""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(RECOMMENDED_POLICY_REGEX, content)
            if match:
                insurer = match.group(1).strip().lower()
                tier = match.group(2).strip().lower()
                return insurer, tier
            else:
                logging.warning(
                    f"Could not find recommended policy pattern in {report_path.name}"
                )
                return None, None
    except FileNotFoundError:
        logging.error(f"Report file not found: {report_path}")
        return None, None
    except Exception as e:
        logging.error(f"Error reading or parsing report {report_path.name}: {e}")
        return None, None


def evaluate_recommendation(
    recommended_insurer: str, recommended_tier: str, ground_truth_entry: dict
) -> tuple[str, str | None]:
    """Compares the recommendation against the ground truth."""
    status = ground_truth_entry.get("status", "unknown")
    expected_policies = ground_truth_entry.get("expected_policies", [])

    is_match = False
    match_justification = None

    for expected in expected_policies:
        if (
            recommended_insurer == expected.get("insurer", "").lower()
            and recommended_tier == expected.get("tier", "").lower()
        ):
            is_match = True
            match_justification = expected.get("justification")
            break

    if status == "full_cover_available":
        result = "PASS" if is_match else "FAIL"
    elif status == "partial_cover_only":
        result = (
            "PASS (Partial Cover)" if is_match else "FAIL (Partial)"
        )  # Fail means didn't even find the partial
    else:
        result = (
            "UNKNOWN_STATUS_PASS" if is_match else "UNKNOWN_STATUS_FAIL"
        )  # Handle unexpected status

    return result, match_justification


def main(results_dir: str, output_file: str | None):
    """Main function to run the evaluation."""
    results_path = Path(results_dir)
    if not results_path.is_dir():
        logging.error(f"Results directory not found: {results_dir}")
        return

    # Use the updated GROUND_TRUTH_PATH constant
    if not GROUND_TRUTH_PATH.is_file():
        logging.error(f"Ground truth file not found: {GROUND_TRUTH_PATH}")
        return

    # Load ground truth
    try:
        # Use the updated GROUND_TRUTH_PATH constant
        with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
            ground_truth_data = json.load(f)
        logging.info(f"Loaded ground truth from {GROUND_TRUTH_PATH}")
    except Exception as e:
        logging.error(f"Error loading ground truth file: {e}")
        return

    evaluation_results = []
    report_files = list(results_path.rglob(RECOMMENDATION_REPORT_PATTERN))
    logging.info(f"Found {len(report_files)} recommendation reports in {results_dir}")

    processed_count = 0
    pass_count = 0
    fail_count = 0
    partial_pass_count = 0
    skipped_count = 0

    for report_path in report_files:
        logging.info(f"Processing report: {report_path.name}")
        processed_count += 1

        # Extract UUID from directory name (assuming results/{uuid}/report...)
        uuid_str = report_path.parent.name
        if not uuid_str:
            logging.warning(
                f"Could not determine UUID for report: {report_path}. Skipping."
            )
            skipped_count += 1
            continue

        # Find transcript and scenario
        transcript_file = find_transcript_filename(uuid_str)
        if not transcript_file:
            logging.warning(
                f"Skipping evaluation for {report_path.name} due to missing transcript file."
            )
            skipped_count += 1
            continue

        scenario_name = extract_scenario_from_filename(transcript_file)
        if not scenario_name or scenario_name == "no_scenario":
            logging.info(
                f"Skipping evaluation for {report_path.name} as it has no specific scenario ('{scenario_name}')."
            )
            skipped_count += 1
            continue  # Only evaluate reports linked to specific scenarios in ground truth

        # Check if scenario exists in ground truth
        if scenario_name not in ground_truth_data:
            logging.warning(
                f"Scenario '{scenario_name}' not found in ground truth data. Skipping {report_path.name}."
            )
            skipped_count += 1
            continue

        ground_truth_entry = ground_truth_data[scenario_name]

        # Parse recommendation
        recommended_insurer, recommended_tier = parse_recommendation_report(report_path)
        if not recommended_insurer or not recommended_tier:
            logging.warning(
                f"Could not parse recommendation from {report_path.name}. Skipping."
            )
            skipped_count += 1
            continue

        # Evaluate
        result, match_justification = evaluate_recommendation(
            recommended_insurer, recommended_tier, ground_truth_entry
        )

        # Store result
        evaluation_results.append(
            {
                "report_file": str(report_path.relative_to(results_path)),
                "uuid": uuid_str,
                "scenario": scenario_name,
                "recommended_policy": f"{recommended_insurer} - {recommended_tier}",
                "ground_truth_status": ground_truth_entry.get("status"),
                "expected_policies": ground_truth_entry.get("expected_policies"),
                "evaluation_result": result,
                "match_justification": match_justification
                if result != "FAIL" and result != "FAIL (Partial)"
                else None,
            }
        )

        # Update counts
        if result == "PASS":
            pass_count += 1
        elif result == "PASS (Partial Cover)":
            partial_pass_count += 1
        else:  # FAIL or FAIL (Partial) or UNKNOWN_STATUS_FAIL
            fail_count += 1

    # Print Summary
    logging.info("\n--- Evaluation Summary ---")
    logging.info(f"Total Reports Found: {len(report_files)}")
    logging.info(
        f"Reports Processed (with scenario): {processed_count - skipped_count}"
    )
    logging.info(
        f"Reports Skipped (no scenario/transcript/parse error): {skipped_count}"
    )
    logging.info(f"PASS: {pass_count}")
    logging.info(f"PASS (Partial Cover): {partial_pass_count}")
    logging.info(f"FAIL: {fail_count}")
    logging.info("------------------------\n")

    # Output detailed results if requested
    if output_file:
        output_path = Path(output_file)
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(evaluation_results, f, indent=2)
            logging.info(f"Detailed evaluation results saved to: {output_path}")
        except Exception as e:
            logging.error(f"Error writing results to {output_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate scenario-based recommendation reports against ground truth."
    )
    parser.add_argument(
        "-d",
        "--results_dir",
        default="results",
        help="Directory containing the recommendation report results (e.g., 'results/').",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        default=None,
        # Updated help text to reflect new default location idea
        help="Optional path to save detailed evaluation results in JSON format (e.g., data/evaluation/scenario_evaluation/scenario_evaluation_results.json).",
    )
    args = parser.parse_args()
    main(args.results_dir, args.output_file)
