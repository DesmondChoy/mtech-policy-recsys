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
4.  **Final Evaluation (Async)**: Runs the final scenario-based evaluation in
    parallel for each target scenario using
    `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`.

Usage:
    python scripts/orchestrate_scenario_evaluation.py [-n NUM_TRANSCRIPTS] [--skip_transcript_eval]

Arguments:
    -n, --num_transcripts     Number of transcripts to generate per scenario (default: 5).
    --skip_transcript_eval  If set, skips the transcript evaluation step. All generated
                              transcripts will proceed to report generation.

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


def _parse_transcript_evaluation_results(all_uuids: List[str]) -> Set[str]:
    """
    Parses transcript evaluation JSON files to determine which transcripts passed.
    Placeholder implementation: Assumes a simple pass/fail structure.
    """
    passed_uuids = set()
    # TODO: Define actual pass criteria based on the structure of evaluation JSONs
    # Example placeholder logic: Check if a summary score exists and is above a threshold
    # For now, just log that we need to implement this and assume all generated transcripts
    # for which an eval file exists are potentially passable if the script ran.
    # A more robust check would be needed in reality.
    logging.warning("Parsing transcript evaluation results - Using placeholder logic.")
    eval_files = glob.glob(str(TRANSCRIPT_EVAL_DIR / "transcript_eval_*.json"))
    evaluated_uuids = set()
    for f_path_str in eval_files:
        f_path = Path(f_path_str)
        # Extract UUID from filename like transcript_eval_{scenario}_{uuid}.json
        parts = f_path.stem.split("_")
        if len(parts) >= 4 and parts[0] == "transcript" and parts[1] == "eval":
            uuid = parts[-1]
            evaluated_uuids.add(uuid)
            # Placeholder: Assume pass if file exists and belongs to this run's UUIDs
            if uuid in all_uuids:
                # Add actual check here based on JSON content, e.g.:
                # try:
                #     with open(f_path, 'r') as f:
                #         data = json.load(f)
                #     if data.get("evaluation_summary", {}).get("overall_rating", "").lower() == "pass":
                #         passed_uuids.add(uuid)
                # except Exception as e:
                #     logging.warning(f"Could not parse or evaluate {f_path.name}: {e}")
                passed_uuids.add(
                    uuid
                )  # Placeholder: Add if file exists for a generated UUID

    logging.info(
        f"Found {len(evaluated_uuids)} evaluation files. Determined {len(passed_uuids)} passing UUIDs (placeholder)."
    )
    return passed_uuids


def run_pipeline(
    all_uuids: List[str], skip_transcript_eval: bool
) -> Optional[Set[str]]:
    """Runs the sequential batch processing pipeline: Evaluation, Parsing, Extraction."""
    logging.info("--- Starting Pipeline Processing ---")
    passed_uuids: Optional[Set[str]] = None

    # Step 2.1: Transcript Evaluation (Conditional)
    # --------------------------------------------
    if not skip_transcript_eval:
        logging.info("Step 2.1: Running Transcript Evaluation...")
        if run_script(EVAL_TRANSCRIPTS_SCRIPT, []):
            logging.info("Transcript Evaluation script finished. Parsing results...")
            passed_uuids = _parse_transcript_evaluation_results(all_uuids)
        else:
            logging.error(
                "Transcript Evaluation script failed. Cannot determine passing transcripts."
            )
            # Treat as if none passed if the script fails
            passed_uuids = set()
    else:
        logging.info("Step 2.1: Skipping Transcript Evaluation.")
        # If skipped, all generated UUIDs are considered "passed" for subsequent steps
        passed_uuids = set(all_uuids)

    # Step 2.2: Transcript Parsing
    # ----------------------------
    # This script processes all raw transcripts found, including potentially failed ones.
    # Downstream steps will filter based on passed_uuids if evaluation ran.
    logging.info("Step 2.2: Running Transcript Parsing...")
    if not run_script(PARSE_TRANSCRIPTS_SCRIPT, []):
        logging.error("Transcript Parsing script failed. Critical step. Exiting.")
        sys.exit(1)
    logging.info("Transcript Parsing finished.")

    # Step 2.3: Requirement Extraction
    # --------------------------------
    # This script processes all *processed* transcripts found.
    # Downstream steps will filter based on passed_uuids if evaluation ran.
    logging.info("Step 2.3: Running Requirement Extraction...")
    if not run_script(EXTRACT_REQ_SCRIPT, []):
        logging.error("Requirement Extraction script failed. Critical step. Exiting.")
        sys.exit(1)
    logging.info("Requirement Extraction finished.")

    logging.info("--- Pipeline Processing Finished ---")
    # Return the set of UUIDs that passed evaluation, or all UUIDs if eval was skipped
    # Note: If eval failed, passed_uuids will be an empty set.
    return passed_uuids if not skip_transcript_eval else set(all_uuids)


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

    try:
        # Use context manager for the pool
        # Adjust process count as needed, report generation might be I/O bound or CPU bound depending on scripts
        with multiprocessing.Pool(
            processes=min(len(tasks), (os.cpu_count() or 1) * 2)
        ) as pool:
            pool.starmap(_generate_reports_for_uuid, tasks)
        logging.info(f"Asynchronous report generation complete for {len(tasks)} UUIDs.")
    except Exception as e:
        logging.error(
            f"An error occurred during multiprocessing report generation: {e}"
        )

    logging.info("--- Report Generation Finished ---")


def _evaluate_scenario(scenario: str):
    """Helper function to run final evaluation for a single scenario."""
    logging.info(f"Running final evaluation for scenario: {scenario}...")
    args = ["--scenario", scenario]
    # The evaluation script prints summary to stdout/log, run_script captures it on failure
    # We might want to enhance run_script to always capture/return stdout for logging summaries
    success = run_script(EVAL_SCENARIO_SCRIPT, args)
    if success:
        logging.info(f"Final evaluation completed for scenario: {scenario}")
    else:
        logging.error(f"Final evaluation failed for scenario: {scenario}")


def run_final_evaluation_async(scenarios: List[str]):
    """Runs the final scenario evaluation asynchronously per scenario."""
    logging.info("--- Starting Final Scenario Evaluation ---")
    if not scenarios:
        logging.warning("No scenarios provided for final evaluation.")
        logging.info("--- Final Scenario Evaluation Finished ---")
        return

    logging.info(
        f"Starting asynchronous final evaluation for {len(scenarios)} scenarios..."
    )

    try:
        # Use context manager for the pool
        with multiprocessing.Pool(
            processes=min(len(scenarios), os.cpu_count() or 1)
        ) as pool:
            # Use map as the helper function only takes one argument (scenario)
            pool.map(_evaluate_scenario, scenarios)
        logging.info(
            f"Asynchronous final evaluation complete for {len(scenarios)} scenarios."
        )
    except Exception as e:
        logging.error(f"An error occurred during multiprocessing final evaluation: {e}")

    logging.info("--- Final Scenario Evaluation Finished ---")


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
    args = parser.parse_args()

    logging.info("--- Starting Scenario Evaluation Orchestration ---")
    logging.info(f"Target Scenarios: {', '.join(TARGET_SCENARIOS)}")
    logging.info(f"Transcripts per scenario: {args.num_transcripts}")
    logging.info(f"Skip transcript evaluation: {args.skip_transcript_eval}")

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
    passed_uuids = run_pipeline(all_uuids, args.skip_transcript_eval)

    # Step 3: Generate Reports (Async)
    # Pass the dictionary mapping scenarios to lists of UUIDs
    generate_reports_async(scenario_uuids, passed_uuids)

    # Step 4: Run Final Evaluation (Async)
    run_final_evaluation_async(TARGET_SCENARIOS)

    logging.info("--- Scenario Evaluation Orchestration Finished ---")


if __name__ == "__main__":
    # Ensure the script is run from the project root for consistent pathing?
    # Or rely on Path objects resolving correctly. Let's rely on Path objects.
    main()
