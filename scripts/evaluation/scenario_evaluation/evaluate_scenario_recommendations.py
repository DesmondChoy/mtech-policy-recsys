"""
Evaluates generated recommendation reports against a predefined ground truth
for specific scenarios.

This script compares recommendation reports against a ground truth JSON file.
It can operate in two modes:

1.  **Evaluate All Scenarios (Default):** Iterates through all UUID subdirectories
    in the results folder. For each UUID, it finds the corresponding transcript,
    determines the scenario, and if the scenario is in the ground truth,
    evaluates the recommendation report found in the UUID's directory.

2.  **Evaluate Specific Scenario (using --scenario argument):** Finds all
    transcripts matching the specified scenario, extracts their UUIDs, and then
    only processes the recommendation reports found in the results subdirectories
    corresponding to those specific UUIDs.

Results are summarized in the console, and detailed results can optionally be
saved to a JSON file.

Usage:
  # Evaluate all scenarios
  python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py [-d RESULTS_DIR] [-o OUTPUT_FILE]

  # Evaluate only a specific scenario (e.g., 'golf_coverage')
  python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario golf_coverage
  python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario pet_care_coverage
  python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario public_transport_double_cover
  python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario uncovered_cancellation_reason

Arguments:
  -d, --results_dir  Directory containing recommendation reports (default: 'results').
                     Expected structure: results/{uuid}/recommendation_report_*.md
  -o, --output_file  Optional path to save detailed evaluation results as JSON.
                     If omitted, defaults to data/evaluation/scenario_evaluation/
                     results_{scenario}_{timestamp}.json where {scenario} is the target
                     scenario or 'all_scenarios'.
  -s, --scenario     Optional specific scenario name to evaluate. If omitted,
                     evaluates all scenarios found in the results directory that
                     are also present in the ground truth.

Input Files:
  - Ground Truth: data/evaluation/scenario_evaluation/scenario_ground_truth.json
  - Recommendation Reports: results/{uuid}/recommendation_report_*.md
  - Transcripts (for scenario mapping): data/transcripts/raw/synthetic/transcript_{scenario}_{uuid}.json

Output:
  - Console summary of evaluation results (PASS, FAIL, PASS (Partial Cover)).
  - Optional detailed JSON output file.
"""

import json
import os
import glob
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime

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
DEFAULT_OUTPUT_DIR = Path("data/evaluation/scenario_evaluation")
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


def extract_uuid_from_filename(filename: Path) -> str | None:
    """Extracts the UUID from the transcript filename."""
    # Expected format: transcript_{scenario_name}_{uuid}.json
    parts = filename.stem.split("_")
    if len(parts) >= 3 and parts[0] == "transcript":
        return parts[-1]  # UUID is the last part
    logging.warning(f"Could not extract UUID from filename: {filename.name}")
    return None


def main(
    results_dir: str,
    output_file: str | None,
    target_scenario: str | None,
    target_uuid: str | None,
):
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

    target_uuids = None

    # If a specific target UUID is provided, use only that UUID
    if target_uuid:
        logging.info(f"Focusing evaluation on specific UUID: {target_uuid}")
        target_uuids = {target_uuid}

        # We still need to know the scenario for this UUID to get the ground truth
        if not target_scenario:
            # Try to find the scenario from transcript files
            transcript_pattern = TRANSCRIPT_DIR / f"transcript_*_{target_uuid}.json"
            matching_transcripts = list(
                TRANSCRIPT_DIR.glob(f"transcript_*_{target_uuid}.json")
            )
            if matching_transcripts:
                scenario_name = extract_scenario_from_filename(matching_transcripts[0])
                if scenario_name and scenario_name in ground_truth_data:
                    target_scenario = scenario_name
                    logging.info(
                        f"Determined scenario '{target_scenario}' from transcript filename"
                    )
                else:
                    logging.error(
                        f"Could not determine valid scenario for UUID {target_uuid}"
                    )
                    return
            else:
                logging.error(f"No transcript found for UUID {target_uuid}")
                return
    # Otherwise, if only a scenario is provided, find all UUIDs for that scenario
    elif target_scenario:
        logging.info(f"Filtering evaluation for scenario: {target_scenario}")
        target_uuids = set()
        transcript_pattern = TRANSCRIPT_DIR / f"transcript_{target_scenario}_*.json"
        matching_transcripts = list(
            TRANSCRIPT_DIR.glob(f"transcript_{target_scenario}_*.json")
        )
        if not matching_transcripts:
            logging.warning(
                f"No transcript files found for scenario '{target_scenario}' in {TRANSCRIPT_DIR}"
            )
        else:
            for transcript_file in matching_transcripts:
                uuid = extract_uuid_from_filename(transcript_file)
                if uuid:
                    target_uuids.add(uuid)
            logging.info(
                f"Found {len(target_uuids)} UUIDs for scenario '{target_scenario}'"
            )
        if not target_uuids:
            logging.warning(
                f"Could not find any UUIDs for target scenario '{target_scenario}'. No reports will be processed."
            )
            # Still print summary table headers etc.
            pass  # Allow loop to run but it will skip everything

    evaluation_results = []
    # Instead of finding all reports first, iterate through result directories
    # report_files = list(results_path.rglob(RECOMMENDATION_REPORT_PATTERN))
    # logging.info(f"Found {len(report_files)} recommendation reports in {results_dir}")
    total_reports_found_count = 0  # Count all potential reports

    processed_count = 0  # Count reports actually evaluated
    pass_count = 0
    fail_count = 0
    partial_pass_count = 0
    skipped_count = 0  # Count reports skipped for various reasons

    # Iterate through UUID directories in the results path
    for uuid_dir in results_path.iterdir():
        if not uuid_dir.is_dir():
            continue

        uuid_str = uuid_dir.name

        # --- Filtering Logic ---
        scenario_name_for_eval = None
        if target_scenario:
            # If filtering by scenario, check if this UUID is relevant
            if target_uuids is None or uuid_str not in target_uuids:
                # logging.debug(f"Skipping UUID {uuid_str} as it doesn't match target scenario '{target_scenario}'.")
                skipped_count += 1  # Count as skipped due to scenario filter
                continue
            scenario_name_for_eval = target_scenario  # We know the scenario
        else:
            # If not filtering, find the scenario for this UUID
            transcript_file = find_transcript_filename(uuid_str)
            if not transcript_file:
                logging.warning(
                    f"Skipping UUID {uuid_str} due to missing transcript file."
                )
                skipped_count += 1
                continue
            extracted_scenario = extract_scenario_from_filename(transcript_file)
            if not extracted_scenario or extracted_scenario == "no_scenario":
                logging.info(
                    f"Skipping UUID {uuid_str} as it has no specific scenario ('{extracted_scenario}')."
                )
                skipped_count += 1
                continue
            if extracted_scenario not in ground_truth_data:
                logging.warning(
                    f"Scenario '{extracted_scenario}' for UUID {uuid_str} not found in ground truth data. Skipping."
                )
                skipped_count += 1
                continue
            scenario_name_for_eval = extracted_scenario
        # --- End Filtering Logic ---

        # Find the recommendation report file within the UUID directory
        report_search_pattern = uuid_dir / RECOMMENDATION_REPORT_PATTERN
        report_files_in_dir = list(uuid_dir.glob(RECOMMENDATION_REPORT_PATTERN))

        if not report_files_in_dir:
            logging.warning(f"No recommendation report found in directory: {uuid_dir}")
            skipped_count += 1
            continue
        if len(report_files_in_dir) > 1:
            logging.warning(
                f"Multiple recommendation reports found in {uuid_dir}, using the first one: {report_files_in_dir[0].name}"
            )

        report_path = report_files_in_dir[0]
        total_reports_found_count += 1  # Count reports found within relevant UUID dirs
        logging.info(
            f"Processing report: {report_path.name} for scenario: {scenario_name_for_eval}"
        )

        ground_truth_entry = ground_truth_data[scenario_name_for_eval]

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
        processed_count += 1  # Increment only if evaluation happens

        # Store result
        evaluation_results.append(
            {
                "report_file": str(
                    report_path.relative_to(results_path)
                ),  # Keep relative path for readability
                "uuid": uuid_str,
                "scenario": scenario_name_for_eval,  # Use the determined scenario
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
    if target_scenario:
        logging.info(f"Scenario Filter Applied: '{target_scenario}'")
    # logging.info(f"Total Reports Found: {total_reports_found_count}") # Less relevant now
    logging.info(f"Reports Evaluated: {processed_count}")
    logging.info(
        f"Reports Skipped (filter/no scenario/transcript/parse error): {skipped_count}"
    )
    logging.info(f"PASS: {pass_count}")
    logging.info(f"PASS (Partial Cover): {partial_pass_count}")
    logging.info(f"FAIL: {fail_count}")
    logging.info("------------------------\n")

    # Determine final output path
    final_output_path = None
    if output_file:
        # User provided a specific path
        final_output_path = Path(output_file)
    else:
        # Generate default path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scenario_part = target_scenario if target_scenario else "all_scenarios"
        default_filename = f"results_{scenario_part}_{timestamp}.json"
        final_output_path = DEFAULT_OUTPUT_DIR / default_filename

    # Output detailed results if a path was determined
    if final_output_path:
        # Ensure parent directory exists
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(final_output_path, "w", encoding="utf-8") as f:
                json.dump(evaluation_results, f, indent=2)
            logging.info(f"Detailed evaluation results saved to: {final_output_path}")
        except Exception as e:
            logging.error(f"Error writing results to {final_output_path}: {e}")


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
        help=(
            "Optional path to save detailed evaluation results in JSON format. "
            "If omitted, defaults to data/evaluation/scenario_evaluation/"
            "results_{scenario}_{timestamp}.json where {scenario} is the target "
            "scenario or 'all_scenarios'."
        ),
    )
    # Add scenario argument
    parser.add_argument(
        "-s",
        "--scenario",
        default=None,
        help="Optional specific scenario name to evaluate. If not provided, evaluates all scenarios found.",
    )
    # Add target UUID argument
    parser.add_argument(
        "-u",
        "--target-uuid",
        default=None,
        help="Optional specific UUID to evaluate. If provided, only evaluates the recommendation for this UUID.",
    )
    args = parser.parse_args()
    main(args.results_dir, args.output_file, args.scenario, args.target_uuid)
