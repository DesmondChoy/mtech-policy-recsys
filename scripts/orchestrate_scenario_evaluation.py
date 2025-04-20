"""
Orchestrates the end-to-end process for evaluating recommendation scenarios.

This script automates the following workflow:
1. Generating synthetic transcripts for specified scenarios (in parallel).
2. Running the transcripts through the processing pipeline (evaluation, parsing, extraction).
3. Generating comparison and recommendation reports for each transcript (in parallel).
4. Evaluating the final recommendations against ground truth for each scenario (in parallel).

Intermediate files generated during the process are preserved for debugging purposes.

Workflow Steps:
1.  **Transcript Generation (Async)**: Generates a specified number of synthetic
    transcripts for each target scenario in parallel using
    `scripts/data_generation/generate_transcripts.py`.
2.  **Pipeline Execution (Sequential Batch)**:
    a.  **(Optional) Transcript Evaluation**: Runs
        `scripts/evaluation/transcript_evaluation/eval_transcript_main.py`
        to evaluate the quality of generated transcripts. Parses results to
        identify passing transcripts (Note: Pass/fail logic is currently a placeholder).
    b.  **Transcript Parsing**: Runs `src/utils/transcript_processing.py` to
        parse raw transcripts into a processed format.
    c.  **Requirement Extraction**: Runs `src/agents/extractor.py` to extract
        structured requirements from processed transcripts.
3.  **Report Generation (Async)**: For each transcript that passed evaluation (or
    all transcripts if evaluation is skipped), generates comparison and
    recommendation reports in parallel using
    `scripts/generate_policy_comparison.py` and
    `scripts/generate_recommendation_report.py`.
4.  **Final Evaluation & Aggregation**: Runs the standard scenario evaluation script
    for each scenario, then filters the latest results file to include only
    UUIDs generated in the current run, saving the filtered data to a new
    aggregated file.

Usage:
    python scripts/orchestrate_scenario_evaluation.py [-n NUM_TRANSCRIPTS] [--skip_transcript_eval] [--only_aggregate]

Arguments:
    -n, --num_transcripts     Number of transcripts to generate per scenario (default: 5).
    --skip_transcript_eval  If set, skips the transcript evaluation step. All generated
                              transcripts will proceed to report generation.
    --only_aggregate        If set, skips steps 1-3 (generation, pipeline, reports) and
                              only runs step 4 (final evaluation and aggregation).

Prerequisites:
-   Python environment set up with dependencies from `requirements.txt`.
-   Required API keys configured in `.env` file.
-   Necessary input data present (scenarios, coverage requirements, personalities, policies).
-   All dependent scripts must be functional.
"""

import argparse
import glob
import json
import logging
import multiprocessing
import os
import subprocess
import sys
from datetime import datetime  # Import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# --- Configuration ---

# Add the project root to the Python path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Define constants for paths relative to the project root
# Ensure correct path separators for the OS (using Path objects handles this)
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
RESULTS_DIR = PROJECT_ROOT / "results"

RAW_TRANSCRIPT_DIR = DATA_DIR / "transcripts" / "raw" / "synthetic"
PROCESSED_TRANSCRIPT_DIR = DATA_DIR / "transcripts" / "processed"
EXTRACTED_REQ_DIR = DATA_DIR / "extracted_customer_requirements"
TRANSCRIPT_EVAL_DIR = DATA_DIR / "evaluation" / "transcript_evaluations"
SCENARIO_EVAL_DIR = DATA_DIR / "evaluation" / "scenario_evaluation"

# Define target scenarios
TARGET_SCENARIOS = [
    "golf_coverage",
    "pet_care_coverage",
    "public_transport_double_cover",
    "uncovered_cancellation_reason",
]

# Script paths
GEN_TRANSCRIPTS_SCRIPT = SCRIPTS_DIR / "data_generation" / "generate_transcripts.py"
EVAL_TRANSCRIPTS_SCRIPT = (
    SCRIPTS_DIR / "evaluation" / "transcript_evaluation" / "eval_transcript_main.py"
)
PARSE_TRANSCRIPTS_SCRIPT = PROJECT_ROOT / "src" / "utils" / "transcript_processing.py"
EXTRACT_REQ_SCRIPT = PROJECT_ROOT / "src" / "agents" / "extractor.py"
GEN_COMPARISON_SCRIPT = SCRIPTS_DIR / "generate_policy_comparison.py"
GEN_RECOMMENDATION_SCRIPT = SCRIPTS_DIR / "generate_recommendation_report.py"
EVAL_SCENARIO_SCRIPT = (
    SCRIPTS_DIR
    / "evaluation"
    / "scenario_evaluation"
    / "evaluate_scenario_recommendations.py"
)


# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# --- Helper Functions ---


def run_script(script_path: Path, args: List[str], cwd: Path = PROJECT_ROOT) -> bool:
    """Runs a Python script using subprocess and logs the outcome."""
    command = [sys.executable, str(script_path)] + args
    logging.info(f"Running command: {' '.join(command)}")
    try:
        # Use shell=True on Windows if needed, but try without first for security
        # Pass cwd to ensure script runs in the correct project context
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            encoding="utf-8",
            errors="ignore",  # Ignore decoding errors in stdout/stderr
        )
        logging.info(f"Script {script_path.name} completed successfully.")
        logging.debug(f"Stdout:\n{result.stdout}")
        if result.stderr:
            logging.debug(f"Stderr:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Script {script_path.name} failed with exit code {e.returncode}."
        )
        logging.error(f"Stderr:\n{e.stderr}")
        logging.error(f"Stdout:\n{e.stdout}")
        return False
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while running {script_path.name}: {e}"
        )
        return False


# --- Core Functions ---


def _extract_uuid_from_filename(filename: Path) -> Optional[str]:
    """Extracts UUID from transcript filename (transcript_{scenario}_{uuid}.json)."""
    parts = filename.stem.split("_")
    if len(parts) >= 3 and parts[0] == "transcript":
        return parts[-1]
    return None


def _generate_for_scenario(scenario: str, num_transcripts: int) -> List[str]:
    """Helper function to generate transcripts for a single scenario."""
    logging.info(
        f"Generating {num_transcripts} transcripts for scenario: {scenario}..."
    )
    args = ["--scenario", scenario, "-n", str(num_transcripts)]
    # Track files before running to identify newly created ones
    existing_files = set(RAW_TRANSCRIPT_DIR.glob(f"transcript_{scenario}_*.json"))

    if run_script(GEN_TRANSCRIPTS_SCRIPT, args):
        # Find newly created files
        current_files = set(RAW_TRANSCRIPT_DIR.glob(f"transcript_{scenario}_*.json"))
        new_files = current_files - existing_files
        uuids = []
        for f in new_files:
            uuid = _extract_uuid_from_filename(f)
            if uuid:
                uuids.append(uuid)
            else:
                logging.warning(f"Could not extract UUID from generated file: {f.name}")

        if len(uuids) == num_transcripts:
            logging.info(
                f"Successfully generated {len(uuids)} transcripts for scenario: {scenario}"
            )
        else:
            logging.warning(
                f"Expected {num_transcripts} transcripts for {scenario}, but found {len(uuids)} new files with valid UUIDs."
            )
        return uuids
    else:
        logging.error(f"Transcript generation failed for scenario: {scenario}")
        return []


def generate_transcripts_async(
    scenarios: List[str], num_transcripts: int
) -> Tuple[Dict[str, List[str]], List[str]]:
    """Generates transcripts asynchronously for each scenario using multiprocessing."""
    logging.info(
        f"Starting asynchronous transcript generation for {len(scenarios)} scenarios..."
    )
    all_generated_uuids: List[str] = []
    scenario_uuids: Dict[str, List[str]] = {scenario: [] for scenario in scenarios}

    pool_args = [(scenario, num_transcripts) for scenario in scenarios]

    try:
        # Use context manager for the pool
        with multiprocessing.Pool(
            processes=min(len(scenarios), os.cpu_count() or 1)
        ) as pool:
            # starmap preserves the order corresponding to the input scenarios list
            results = pool.starmap(_generate_for_scenario, pool_args)

        # Process results
        total_generated = 0
        for i, scenario in enumerate(scenarios):
            generated_uuids_for_scenario = results[i]
            scenario_uuids[scenario] = generated_uuids_for_scenario
            all_generated_uuids.extend(generated_uuids_for_scenario)
            total_generated += len(generated_uuids_for_scenario)

        logging.info(
            f"Asynchronous transcript generation complete. Generated {total_generated} total transcripts."
        )

    except Exception as e:
        logging.error(
            f"An error occurred during multiprocessing transcript generation: {e}"
        )
        # Return empty lists/dicts to indicate failure
        return {}, []

    return scenario_uuids, all_generated_uuids


# Helper function for parallel transcript evaluation
def _evaluate_transcript_task(transcript_path: Path) -> Optional[str]:
    """
    Runs the evaluation script for a single transcript file.

    Args:
        transcript_path: Path to the raw transcript JSON file.

    Returns:
        The UUID of the transcript if evaluation was successful, otherwise None.
    """
    uuid = _extract_uuid_from_filename(transcript_path)
    if not uuid:
        logging.error(
            f"Could not extract UUID from {transcript_path.name} for evaluation."
        )
        return None

    logging.debug(f"Starting evaluation task for: {transcript_path.name}")
    # Use the modified eval script that accepts --transcript and exits with status code
    eval_args = ["--transcript", str(transcript_path)]
    # We don't need to specify output dir/format, use defaults from eval script

    if run_script(EVAL_TRANSCRIPTS_SCRIPT, eval_args):
        logging.info(f"Evaluation successful for UUID: {uuid}")
        return uuid
    else:
        logging.error(
            f"Evaluation failed for UUID: {uuid} (Transcript: {transcript_path.name})"
        )
        # The failure is already logged by run_script


def run_pipeline(
    scenario_uuids: Dict[str, List[str]], skip_transcript_eval: bool
) -> Optional[Set[str]]:
    """
    Runs the processing pipeline: Parallel Evaluation (optional), Sequential Parsing, Sequential Extraction.

    Args:
        scenario_uuids: Dictionary mapping scenario names to lists of generated UUIDs.
        skip_transcript_eval: Boolean indicating whether to skip evaluation.

    Returns:
        A set of UUIDs that passed evaluation (or all generated UUIDs if skipped),
        or None if a critical error occurred.
    """
    logging.info("--- Starting Pipeline Processing ---")
    passed_uuids_set: Set[str] = set()
    all_generated_uuids_list: List[str] = [
        uuid for uuids in scenario_uuids.values() for uuid in uuids
    ]

    # Step 2.1: Transcript Evaluation (Conditional & Parallel)
    # -------------------------------------------------------
    if not skip_transcript_eval:
        logging.info("Step 2.1: Running Parallel Transcript Evaluation...")

        # Find all generated raw transcript files based on scenario_uuids
        transcript_files_to_evaluate: List[Path] = []
        for scenario, uuids in scenario_uuids.items():
            for uuid in uuids:
                # Construct expected filename
                file_path = RAW_TRANSCRIPT_DIR / f"transcript_{scenario}_{uuid}.json"
                if file_path.is_file():
                    transcript_files_to_evaluate.append(file_path)
                else:
                    logging.warning(
                        f"Raw transcript file not found for evaluation: {file_path.name}"
                    )

        if not transcript_files_to_evaluate:
            logging.error(
                "No raw transcript files found to evaluate. Stopping pipeline."
            )
            return None

        logging.info(
            f"Found {len(transcript_files_to_evaluate)} transcripts to evaluate in parallel."
        )
        successful_eval_uuids: List[str] = []
        try:
            # Use context manager for the pool
            # Adjust process count as needed
            with multiprocessing.Pool(
                processes=min(
                    len(transcript_files_to_evaluate), (os.cpu_count() or 1) * 2
                )
            ) as pool:
                # map returns results in order, filter out None results (failures)
                results = pool.map(
                    _evaluate_transcript_task, transcript_files_to_evaluate
                )
                successful_eval_uuids = [uuid for uuid in results if uuid is not None]

            passed_uuids_set = set(successful_eval_uuids)
            logging.info(
                f"Parallel transcript evaluation complete. {len(passed_uuids_set)} transcripts passed."
            )
            failed_count = len(transcript_files_to_evaluate) - len(passed_uuids_set)
            if failed_count > 0:
                logging.warning(f"{failed_count} transcripts failed evaluation.")

        except Exception as e:
            logging.error(
                f"An error occurred during multiprocessing transcript evaluation: {e}"
            )
            # Treat as if none passed if the pool fails catastrophically
            passed_uuids_set = set()

    else:
        logging.info("Step 2.1: Skipping Transcript Evaluation.")
        # If skipped, all generated UUIDs are considered "passed" for subsequent steps
        passed_uuids_set = set(all_generated_uuids_list)

    # Step 2.2: Transcript Parsing (Sequential)
    # -----------------------------------------
    # This script processes all raw transcripts found in its input dir.
    # It needs to run regardless of evaluation pass/fail, as downstream
    # report generation filters based on passed_uuids_set.
    logging.info("Step 2.2: Running Transcript Parsing (Sequential)...")
    if not run_script(PARSE_TRANSCRIPTS_SCRIPT, []):
        logging.error("Transcript Parsing script failed. Critical step. Exiting.")
        return None  # Indicate critical failure
    logging.info("Transcript Parsing finished.")

    # Step 2.3: Requirement Extraction (Sequential)
    # ---------------------------------------------
    # This script processes all *processed* transcripts found in its input dir.
    # Report generation step will filter based on passed_uuids_set later.
    logging.info("Step 2.3: Running Requirement Extraction (Sequential)...")
    if not run_script(EXTRACT_REQ_SCRIPT, []):
        logging.error("Requirement Extraction script failed. Critical step. Exiting.")
        return None  # Indicate critical failure
    logging.info("Requirement Extraction finished.")

    logging.info("--- Pipeline Processing Finished ---")
    # Return the set of UUIDs that passed evaluation (or all if skipped)
    return passed_uuids_set


def _generate_reports_for_uuid(uuid: str, scenario: str):
    """Helper function to generate reports for a single UUID."""
    logging.debug(f"Generating reports for UUID: {uuid} (Scenario: {scenario})")

    # Check for prerequisite files
    processed_transcript_file = (
        PROCESSED_TRANSCRIPT_DIR / f"parsed_transcript_{scenario}_{uuid}.json"
    )
    extracted_req_file = EXTRACTED_REQ_DIR / f"requirements_{scenario}_{uuid}.json"

    if not processed_transcript_file.is_file():
        logging.error(
            f"Prerequisite file missing for UUID {uuid}: {processed_transcript_file.name}. Skipping report generation."
        )
        return
    if not extracted_req_file.is_file():
        logging.error(
            f"Prerequisite file missing for UUID {uuid}: {extracted_req_file.name}. Skipping report generation."
        )
        return

    # Run Comparison Report Script
    logging.info(f"Running comparison report generation for UUID: {uuid}")
    comparison_success = run_script(GEN_COMPARISON_SCRIPT, ["--customer_id", uuid])
    if not comparison_success:
        logging.error(f"Comparison report generation failed for UUID: {uuid}")
        # Continue to recommendation report? Or stop? Let's continue for now.

    # Run Recommendation Report Script
    # Check if comparison created the results dir, although the script should handle it
    uuid_results_dir = RESULTS_DIR / uuid
    if not uuid_results_dir.is_dir():
        logging.warning(
            f"Results directory {uuid_results_dir} not found before recommendation generation for UUID {uuid}. The script might create it."
        )
        # The recommendation script depends on comparison reports being present in results/{uuid}/

    logging.info(f"Running recommendation report generation for UUID: {uuid}")
    recommendation_success = run_script(
        GEN_RECOMMENDATION_SCRIPT, ["--customer_id", uuid]
    )
    if not recommendation_success:
        logging.error(f"Recommendation report generation failed for UUID: {uuid}")

    logging.debug(f"Finished report generation attempt for UUID: {uuid}")


def generate_reports_async(
    scenario_uuids: Dict[str, List[str]], passed_uuids: Optional[Set[str]]
):
    """Generates comparison and recommendation reports asynchronously per UUID."""
    logging.info("--- Starting Report Generation ---")

    tasks = []
    valid_uuids_count = 0
    skipped_uuids_count = 0

    for scenario, uuids in scenario_uuids.items():
        for uuid in uuids:
            # Check if evaluation was run and if this UUID passed
            if passed_uuids is not None and uuid not in passed_uuids:
                logging.info(
                    f"Skipping report generation for UUID {uuid} (Scenario: {scenario}) as it did not pass evaluation."
                )
                skipped_uuids_count += 1
                continue
            tasks.append((uuid, scenario))
            valid_uuids_count += 1

    if not tasks:
        logging.warning("No valid UUIDs found to generate reports for.")
        logging.info("--- Report Generation Finished ---")
        return

    logging.info(
        f"Starting asynchronous report generation for {len(tasks)} valid UUIDs..."
    )
    if skipped_uuids_count > 0:
        logging.info(
            f"Skipped {skipped_uuids_count} UUIDs that did not pass evaluation."
        )

    # --- Sequential Processing ---
    logging.info(
        f"Starting sequential report generation for {len(tasks)} valid UUIDs..."
    )
    processed_count = 0
    failed_count = 0
    for i, (uuid, scenario) in enumerate(tasks):
        logging.info(
            f"Processing task {i + 1}/{len(tasks)}: UUID {uuid} (Scenario: {scenario})"
        )
        try:
            # Directly call the helper function for each task sequentially
            _generate_reports_for_uuid(uuid, scenario)
            # Note: _generate_reports_for_uuid handles its own internal errors and logging
            # We could add a return value to _generate_reports_for_uuid if we need to track success/failure here
            processed_count += 1  # Assume processed if no exception bubbles up
        except Exception as e:
            # Catch unexpected errors during the call itself, though _generate_reports_for_uuid should handle most
            logging.error(f"Unexpected error processing task for UUID {uuid}: {e}")
            failed_count += 1

    logging.info(f"Sequential report generation complete.")
    logging.info(f"Attempted processing for {processed_count} UUIDs.")
    if failed_count > 0:
        logging.warning(
            f"Encountered unexpected errors during {failed_count} task executions."
        )
    # --- End Sequential Processing ---

    logging.info("--- Report Generation Finished ---")


def aggregate_and_filter_evaluations(scenario_uuids: Dict[str, List[str]]):
    """
    Runs final scenario evaluation and aggregates results for the current run.

    For each scenario:
    1. Runs the standard scenario evaluation script.
    2. Finds the latest result file generated by that script.
    3. Filters the results to include only UUIDs from the current orchestration run.
    4. Saves the filtered results to a new aggregated file.
    """
    logging.info("--- Starting Final Evaluation & Aggregation ---")
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scenarios_to_evaluate = list(scenario_uuids.keys())

    if not scenarios_to_evaluate:
        logging.warning("No scenarios with generated UUIDs to evaluate.")
        logging.info("--- Final Evaluation & Aggregation Finished ---")
        return

    for scenario in scenarios_to_evaluate:
        logging.info(f"Running final evaluation for scenario: {scenario}...")
        args = ["--scenario", scenario]
        # Run the evaluation script - it saves its own timestamped file
        success = run_script(EVAL_SCENARIO_SCRIPT, args)

        if not success:
            logging.error(
                f"Final evaluation script failed for scenario: {scenario}. Skipping aggregation."
            )
            continue

        # Find the latest result file for this scenario
        try:
            list_of_files = SCENARIO_EVAL_DIR.glob(f"results_{scenario}_*.json")
            # Filter out potential aggregated files from previous runs
            non_aggregated_files = [
                f for f in list_of_files if "_aggregated_" not in f.name
            ]
            if not non_aggregated_files:
                logging.warning(
                    f"No standard evaluation result files found for scenario {scenario} after running the script."
                )
                continue
            latest_file = max(non_aggregated_files, key=os.path.getctime)
            logging.info(
                f"Found latest evaluation file for {scenario}: {latest_file.name}"
            )
        except Exception as e:
            logging.error(
                f"Error finding latest evaluation file for scenario {scenario}: {e}"
            )
            continue

        # Read the latest results
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                all_results = json.load(f)
            if not isinstance(all_results, list):
                logging.warning(
                    f"Evaluation file {latest_file.name} does not contain a list. Skipping aggregation."
                )
                continue
        except Exception as e:
            logging.error(
                f"Error reading or parsing evaluation file {latest_file.name}: {e}"
            )
            continue

        # --- Filtering step removed ---
        # uuids_for_this_scenario = set(scenario_uuids.get(scenario, []))
        # filtered_results = [
        #     result
        #     for result in all_results
        #     if isinstance(result, dict)
        #     and result.get("uuid") in uuids_for_this_scenario
        # ]
        # logging.info(
        #     f"Filtered {len(all_results)} results down to {len(filtered_results)} for scenario {scenario} based on current run UUIDs."
        # )
        logging.info(
            f"Loaded {len(all_results)} results for scenario {scenario} from latest evaluation file."
        )

        # Save the complete (unfiltered) results to a new file with the specified name
        try:
            output_filename = (
                SCENARIO_EVAL_DIR
                / f"results_{scenario}_all_transcripts_{run_timestamp}.json"  # New filename format
            )
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(
                    all_results, f, indent=2
                )  # Save all_results, not filtered_results
            logging.info(
                f"Saved complete evaluation results for {scenario} to: {output_filename.name}"
            )
        except Exception as e:
            logging.error(
                f"Error saving aggregated results for scenario {scenario}: {e}"
            )

    logging.info("--- Final Evaluation & Aggregation Finished ---")


# --- Main Execution ---


def main():
    """Main function to orchestrate the evaluation process."""
    parser = argparse.ArgumentParser(
        description="Orchestrate scenario evaluation pipeline."
    )
    parser.add_argument(
        "-n",
        "--num_transcripts",
        type=int,
        default=5,
        help="Number of transcripts to generate per scenario (default: 5).",
    )
    parser.add_argument(
        "--skip_transcript_eval",
        action="store_true",
        help="Skip the transcript evaluation step.",
    )
    parser.add_argument(
        "--only_aggregate",
        action="store_true",
        help="Skip transcript generation, pipeline processing, and report generation, and only run the final aggregation step.",
    )
    args = parser.parse_args()

    logging.info("--- Starting Scenario Evaluation Orchestration ---")
    logging.info(f"Target Scenarios: {', '.join(TARGET_SCENARIOS)}")
    logging.info(f"Transcripts per scenario: {args.num_transcripts}")
    logging.info(f"Skip transcript evaluation: {args.skip_transcript_eval}")
    logging.info(f"Only aggregate: {args.only_aggregate}")  # Log the new flag

    if not args.only_aggregate:
        # Step 1: Generate Transcripts (Async)
        scenario_uuids, all_uuids = generate_transcripts_async(
            TARGET_SCENARIOS, args.num_transcripts
        )
        if not all_uuids:
            logging.error("Transcript generation failed or produced no UUIDs. Exiting.")
            sys.exit(1)
        logging.info(
            f"Generated {len(all_uuids)} total transcripts across {len(TARGET_SCENARIOS)} scenarios."
        )

        # Step 2: Run Pipeline (Eval, Parse, Extract)
        # Pass scenario_uuids dict instead of flat list all_uuids
        passed_uuids = run_pipeline(scenario_uuids, args.skip_transcript_eval)
        if passed_uuids is None:  # Handle potential critical failure in pipeline
            logging.error("Pipeline execution failed. Exiting.")
            sys.exit(1)

        # Step 3: Generate Reports (Async)
        # Pass the dictionary mapping scenarios to lists of UUIDs
        generate_reports_async(scenario_uuids, passed_uuids)

        # Step 4: Run Final Evaluation and Aggregate Results (using generated UUIDs)
        aggregate_and_filter_evaluations(scenario_uuids)

    else:
        logging.info("Skipping steps 1-3 due to --only_aggregate flag.")
        # Step 4: Run Final Evaluation and Aggregate Results (using target scenarios directly)
        # The function only needs the scenario names (keys)
        scenario_map_for_aggregation = {scenario: [] for scenario in TARGET_SCENARIOS}
        aggregate_and_filter_evaluations(scenario_map_for_aggregation)

    logging.info("--- Scenario Evaluation Orchestration Finished ---")


if __name__ == "__main__":
    # Ensure the script is run from the project root for consistent pathing?
    # Or rely on Path objects resolving correctly. Let's rely on Path objects.
    main()
