"""
Orchestration Script for Presentation Demo (`run_recsys_demo.py`)

Objective:
Provide a clear, sequential, and easy-to-run demonstration of the core
recommendation system pipeline for a specific scenario, suitable for presentations.
This script generates one transcript, runs the main pipeline steps and intermediate
evaluations sequentially for the generated UUID, and produces a Markdown summary report.

Workflow:
1.  Parse `--scenario` argument.
2.  Generate a unique UUID for the run.
3.  Execute pipeline steps sequentially using `run_step`:
    - Generate Transcript
    - Evaluate Transcript
    - Parse Transcript
    - Extract Requirements
    - Generate Comparison Reports
    - Evaluate Comparison Reports
    - Generate Recommendation Report
    - Evaluate Scenario Recommendation
    - Generate Ground Truth Coverage
4.  Generate a final Markdown summary report (`demo_summary_{uuid}.md`) in the project root.

Usage:
python scripts/run_recsys_demo.py --scenario <scenario_name>

Example:
python scripts/run_recsys_demo.py --scenario pet_care_coverage
"""

import argparse
import subprocess
import uuid
import os
import sys
import logging
import re  # Added for regex
import glob  # Added for file searching
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Check for optional dependencies ---
NLTK_AVAILABLE = False
try:
    import nltk

    NLTK_AVAILABLE = True
except ModuleNotFoundError:
    logging.warning(
        "Optional dependency 'nltk' not found. Ground truth coverage step will be skipped."
    )

# --- Path Setup ---
# Add project root to sys.path to allow importing modules from src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# --- macOS Specific Environment Setting ---
# Addresses potential hangs related to NLTK/Sklearn imports on macOS
# Must be set before subprocesses are called if they import problematic libraries
if sys.platform == "darwin":
    if "OMP_NUM_THREADS" not in os.environ:
        # Use logging once it's configured, but set the variable immediately
        os.environ["OMP_NUM_THREADS"] = "1"
        # We'll log this message after logging is configured
        _log_omp_set = True
    else:
        # Log this message after logging is configured
        _log_omp_already_set = True
        _existing_omp_val = os.environ["OMP_NUM_THREADS"]
else:
    _log_omp_set = False
    _log_omp_already_set = False


# Define key directories and script paths relative to PROJECT_ROOT
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
SCENARIOS_DIR = DATA_DIR / "scenarios"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to console
    ],
)

# Log the OMP_NUM_THREADS setting status now that logging is configured
if "_log_omp_set" in locals() and _log_omp_set:
    logging.info(
        "Detected macOS, automatically set OMP_NUM_THREADS=1 to prevent potential hangs."
    )
if "_log_omp_already_set" in locals() and _log_omp_already_set:
    logging.info(
        f"Detected macOS, but OMP_NUM_THREADS already set to: {_existing_omp_val}. Skipping automatic setting."
    )


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a streamlined RecSys demo pipeline for a specific scenario."
    )
    parser.add_argument(
        "--scenario",
        required=False,  # Make scenario optional
        default=None,  # Default to None if not provided
        help="Name of the scenario file (without .json extension) located in data/scenarios/. If omitted, evaluation steps requiring a scenario will be skipped.",
    )
    parser.add_argument(
        "--skip_scenario_eval",
        action="store_true",  # Sets to True if flag is present
        default=False,
        help="If set, skip the 'Evaluate Scenario Recommendation' step.",
    )
    args = parser.parse_args()

    # Validate scenario file existence only if scenario is provided
    if args.scenario:
        scenario_file = SCENARIOS_DIR / f"{args.scenario}.json"
        if not scenario_file.is_file():
            logging.error(f"Scenario file not found: {scenario_file}")
            sys.exit(1)  # Exit if scenario file doesn't exist

    return args


# --- Helper Function for UUID Extraction ---
def _extract_uuid_from_filename(filename: Path) -> Optional[str]:
    """Extracts UUID from transcript filename (transcript_{scenario}_{uuid}.json)."""
    # Example: transcript_no_scenario_c675e5b2-f9c2-4202-b4d7-a744aeb381f7.json
    # Example: transcript_golf_coverage_1cd04b1c-3dbd-458b-857e-ae193381ab81.json
    match = re.search(r"transcript_.*_([a-f0-9-]+)\.json$", filename.name)
    if match:
        return match.group(1)
    logging.warning(f"Could not extract UUID from filename: {filename.name}")
    return None


def run_step(
    step_name: str, script_path: Path, args: List[str], results_tracker: Dict[str, Any]
) -> bool:
    """
    Runs a single step of the pipeline using subprocess.

    Args:
        step_name: A descriptive name for the step (e.g., "Generate Transcript").
        script_path: The Path object pointing to the Python script to execute.
        args: A list of command-line arguments for the script.
        results_tracker: A dictionary to store the results (status, outputs) of each step.

    Returns:
        True if the step executed successfully (return code 0), False otherwise.
    """
    full_command = [sys.executable, str(script_path)] + args
    command_str = " ".join(map(str, full_command))  # For logging purposes

    logging.info(f"--- Starting Step: {step_name} ---")
    logging.info(f"Executing command: {command_str}")

    start_time = datetime.now()
    success = False
    stdout_log = ""
    stderr_log = ""
    env_vars = os.environ.copy()  # Start with current environment

    # Set PYTHONUTF8=1 specifically for Windows subprocesses (without logging here)
    if sys.platform == "win32":
        env_vars["PYTHONUTF8"] = "1"

    try:
        # Execute the script as a subprocess
        process = subprocess.run(
            full_command,
            env=env_vars,  # Pass the potentially modified environment
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit code
            cwd=PROJECT_ROOT,  # Ensure script runs from project root
            encoding="utf-8",  # Specify encoding
            errors="ignore",  # Ignore decoding errors to prevent UnicodeDecodeError
        )

        stdout_log = process.stdout.strip()
        stderr_log = process.stderr.strip()

        if process.returncode == 0:
            logging.info(f"Step '{step_name}' completed successfully.")
            success = True
        else:
            logging.error(
                f"Step '{step_name}' failed with return code {process.returncode}."
            )
            if stdout_log:
                logging.error(f"Stdout:\n{stdout_log}")
            if stderr_log:
                logging.error(f"Stderr:\n{stderr_log}")

    except Exception as e:
        logging.error(f"An exception occurred while running step '{step_name}': {e}")
        stderr_log += f"\nException during execution: {e}"

    end_time = datetime.now()
    duration = end_time - start_time

    # Record results
    results_tracker[step_name] = {
        "status": "Success" if success else "Failure",
        "command": command_str,
        "return_code": process.returncode if "process" in locals() else None,
        "stdout": stdout_log,
        "stderr": stderr_log,
        "duration": str(duration),
        "output_files": [],  # Placeholder, specific paths added in Task 6 logic
    }

    logging.info(
        f"--- Finished Step: {step_name} (Status: {'Success' if success else 'Failure'}, Duration: {duration}) ---"
    )
    return success


def generate_summary_markdown(
    run_results: Dict[str, Any], scenario: str, uuid_str: str, report_path: Path
):
    """
    Generates a Markdown summary report of the demo run and saves it to a file.

    Args:
        run_results: Dictionary containing the status and details of each pipeline step.
        scenario: The name of the scenario used for the run.
        uuid_str: The UUID string identifying the run.
        report_path: The Path object where the report should be saved.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown_lines = [
        "# RecSys Demo Run Summary",
        "",
        "## Run Details",
        f"- **Timestamp:** {now}",
        f"- **Scenario Used:** {scenario}",
        f"- **Generated UUID:** {uuid_str}",
        "",
        "## Pipeline Step Summary",
        "",
    ]

    # Define descriptions for each step's output (can be expanded)
    output_descriptions = {  # Keep this for reference if needed later
        "Generate Transcript": "Raw synthetic conversation transcript (JSON).",
        "Evaluate Transcript": "Transcript quality evaluation results (JSON).",
        "Parse Transcript": "Parsed transcript structure (JSON).",
        "Extract Requirements": "Extracted customer requirements (JSON).",
        "Generate Comparison Reports": "Directory containing insurer-level comparison reports (Markdown).",
        "Evaluate Comparison Reports": "Directory containing comparison report evaluations (JSON).",
        "Generate Recommendation Report": "Final recommendation report (Markdown).",
        "Evaluate Scenario Recommendation": "Scenario-based recommendation evaluation results (JSON).",
        "Generate Ground Truth Coverage": "Requirement coverage evaluation results (JSON).",
    }

    # Generate structured list instead of table
    for step_name, results in run_results.items():
        markdown_lines.append("---")  # Separator
        markdown_lines.append(f"### {step_name}")

        status = results.get("status", "Unknown")
        duration = results.get("duration", "N/A")
        outputs = results.get("output_files", [])
        description = output_descriptions.get(step_name, "No description available.")

        markdown_lines.append(f"*   **Status:** {status}")
        markdown_lines.append(f"*   **Duration:** {duration}")

        if outputs:
            output_links = []
            for output_path_str in outputs:
                # Ensure path is relative for linking
                rel_path = Path(output_path_str)
                # Create Markdown link format [filename](./path/to/filename)
                link_text = rel_path.name
                link_target = (
                    f"./{rel_path.as_posix()}"  # Use forward slashes for Markdown links
                )
                output_links.append(f"[`{link_text}`]({link_target})")
            markdown_lines.append(f"*   **Output:** {', '.join(output_links)}")
        else:
            markdown_lines.append(f"*   **Output:** N/A")

        markdown_lines.append(f"*   **Description:** {description}")
        markdown_lines.append("")  # Add a blank line for spacing

    # Add Stdout/Stderr details for failed steps
    markdown_lines.append("---\n")  # Separator before error details
    markdown_lines.append("## Error Details (for Failed Steps)\n")
    failed_steps_found = False
    for step_name, results in run_results.items():
        if results.get("status") == "Failure":
            failed_steps_found = True
            markdown_lines.append(f"### {step_name}\n")
            markdown_lines.append(
                f"**Command:**\n```\n{results.get('command', 'N/A')}\n```\n"
            )
            if results.get("stdout"):
                markdown_lines.append(
                    f"**Stdout:**\n```\n{results.get('stdout')}\n```\n"
                )
            if results.get("stderr"):
                markdown_lines.append(
                    f"**Stderr:**\n```\n{results.get('stderr')}\n```\n"
                )
    if not failed_steps_found:
        markdown_lines.append("No steps failed during this run.")

    # Write to file
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(markdown_lines))
        logging.info(f"Summary report generated successfully: {report_path}")
    except IOError as e:
        logging.error(f"Failed to write summary report to {report_path}: {e}")


def main():
    """Main function to orchestrate the demo run."""
    args = parse_arguments()

    # Determine scenario name and if evaluation should be skipped
    if args.scenario is None:
        scenario_name = "no_scenario"
        skip_scenario_specific_eval = True
        logging.info(
            "No scenario provided. Scenario-specific evaluation steps will be skipped."
        )
    else:
        scenario_name = args.scenario
        skip_scenario_specific_eval = (
            args.skip_scenario_eval
        )  # Use the flag if scenario is provided

    # --- Task 4: UUID Generation & Initial Output ---
    run_uuid = uuid.uuid4()
    # This initial UUID might be overwritten by the one from the generated transcript filename
    uuid_str = str(run_uuid)
    # summary_report_path will be defined later using the final uuid_str

    logging.info("-" * 60)
    logging.info(f"Starting RecSys Demo Run")
    logging.info(f"  Scenario: {scenario_name}")
    logging.info(
        f"  Initial UUID: {uuid_str} (may change based on transcript generation)"
    )
    # Log the final path later
    logging.info("-" * 60)

    # --- Windows Specific Environment Setting ---
    # Log once if we are on Windows and will be setting PYTHONUTF8 for subprocesses
    if sys.platform == "win32":
        logging.info("Detected Windows, setting PYTHONUTF8=1 for subprocesses.")

    # --- Task 6: Implement Main Pipeline Logic ---
    run_results: Dict[str, Any] = {}  # Initialize results tracker

    # Define script paths (adjust subdirs as needed based on final structure)
    generate_transcript_script = (
        SCRIPTS_DIR / "data_generation" / "generate_transcripts.py"
    )
    eval_transcript_script = (
        SCRIPTS_DIR / "evaluation" / "transcript_evaluation" / "eval_transcript_main.py"
    )
    parse_transcript_script = (
        PROJECT_ROOT / "src" / "utils" / "transcript_processing.py"
    )  # Assuming it's runnable
    extract_requirements_script = (
        PROJECT_ROOT / "src" / "agents" / "extractor.py"
    )  # Assuming it's runnable
    generate_comparison_script = SCRIPTS_DIR / "generate_policy_comparison.py"
    eval_comparison_script = (
        SCRIPTS_DIR
        / "evaluation"
        / "comparison_report_evaluation"
        / "eval_comparison_report.py"
    )
    generate_recommendation_script = SCRIPTS_DIR / "generate_recommendation_report.py"
    eval_scenario_script = (
        SCRIPTS_DIR
        / "evaluation"
        / "scenario_evaluation"
        / "evaluate_scenario_recommendations.py"
    )
    generate_coverage_script = SCRIPTS_DIR / "generate_ground_truth_coverage.py"

    # --- Step 1: Generate Transcript ---
    step_name_gen_transcript = "Generate Transcript"
    raw_transcript_path = (
        DATA_DIR
        / "transcripts"
        / "raw"
        / "synthetic"
        # Define the expected pattern, but the actual file might have a different UUID
        # We will update raw_transcript_path after generation if needed
        / f"transcript_{scenario_name}_{uuid_str}.json"
    )

    # --- Get existing files before generation ---
    transcript_dir = DATA_DIR / "transcripts" / "raw" / "synthetic"
    try:
        existing_files = set(transcript_dir.glob("transcript_*.json"))
    except Exception as e:
        logging.warning(f"Could not list existing transcripts: {e}")
        existing_files = set()

    # Adjust args based on whether scenario was provided
    # generate_transcripts.py only accepts -n and -s
    if args.scenario:
        gen_transcript_args = ["-s", scenario_name, "-n", "1"]
    else:
        # If no scenario, just specify the number of transcripts
        gen_transcript_args = ["-n", "1"]

    success_gen_transcript = run_step(
        step_name_gen_transcript,
        generate_transcript_script,
        gen_transcript_args,
        run_results,
    )

    # --- Find the actual generated file and UUID ---
    actual_transcript_path: Optional[Path] = None
    if success_gen_transcript:
        try:
            current_files = set(transcript_dir.glob("transcript_*.json"))
            new_files = current_files - existing_files
            if new_files:
                # Find the most recent new file
                newest_file = max(new_files, key=os.path.getctime)
                extracted_uuid = _extract_uuid_from_filename(newest_file)

                if extracted_uuid:
                    # Update UUID and path if successfully extracted
                    uuid_str = extracted_uuid  # IMPORTANT: Update the run's UUID
                    actual_transcript_path = newest_file  # Use the actual path found
                    logging.info(f"Found generated transcript: {newest_file.name}")
                    logging.info(f"Updated run UUID to: {uuid_str}")
                    # Update the expected raw_transcript_path for consistency downstream
                    raw_transcript_path = actual_transcript_path
                else:
                    logging.error(
                        f"Could not extract UUID from newest generated file: {newest_file.name}. Pipeline may fail."
                    )
                    # Keep original uuid_str and raw_transcript_path, but log error
                    actual_transcript_path = (
                        raw_transcript_path  # Fallback to expected path
                    )
            else:
                logging.error(
                    "Transcript generation reported success, but no new transcript file found!"
                )
                success_gen_transcript = False  # Mark as failed if file not found
        except Exception as e:
            logging.error(f"Error finding/processing generated transcript file: {e}")
            success_gen_transcript = False  # Mark as failed on error

    # Update results tracker with the actual path found (or expected path if failed)
    if actual_transcript_path:
        run_results[step_name_gen_transcript]["output_files"] = [
            str(actual_transcript_path.relative_to(PROJECT_ROOT))
        ]
    elif success_gen_transcript:  # If success but path finding failed somehow
        run_results[step_name_gen_transcript]["output_files"] = [
            "Error finding output file"
        ]

    # --- Re-calculate subsequent paths based on potentially updated uuid_str ---
    # These paths depend on the UUID identified from the generated transcript
    transcript_eval_path = (
        DATA_DIR
        / "evaluation"
        / "transcript_evaluations"
        / f"transcript_eval_{scenario_name}_{uuid_str}.json"
    )
    processed_transcript_path = (
        DATA_DIR
        / "transcripts"
        / "processed"
        / f"parsed_transcript_{scenario_name}_{uuid_str}.json"
    )
    requirements_path = (
        DATA_DIR
        / "extracted_customer_requirements"
        / f"requirements_{scenario_name}_{uuid_str}.json"
    )
    comparison_results_dir = RESULTS_DIR / uuid_str
    compare_eval_dir = (
        DATA_DIR / "evaluation" / "comparison_report_evaluations" / uuid_str
    )
    recommendation_report_path = (
        comparison_results_dir / f"recommendation_report_{uuid_str}.md"
    )
    scenario_eval_path = (
        DATA_DIR
        / "evaluation"
        / "scenario_evaluation"
        / f"results_{scenario_name}_{uuid_str}.json"
    )
    coverage_eval_path = (
        DATA_DIR
        / "evaluation"
        / "ground_truth_evaluation"
        / f"coverage_evaluation_{uuid_str}.json"
    )

    # --- Step 2: Evaluate Transcript ---
    step_name_eval_transcript = "Evaluate Transcript"
    # Use the potentially updated raw_transcript_path
    if success_gen_transcript and raw_transcript_path.exists():
        eval_transcript_args = [
            "--transcript",
            str(raw_transcript_path),
        ]  # Corrected argument name
        success_eval_transcript = run_step(
            step_name_eval_transcript,
            eval_transcript_script,
            eval_transcript_args,
            run_results,
        )
        if success_eval_transcript:
            run_results[step_name_eval_transcript]["output_files"] = [
                str(transcript_eval_path.relative_to(PROJECT_ROOT))
            ]
    else:
        logging.warning(
            f"Skipping step '{step_name_eval_transcript}' due to previous step failure or missing input file."
        )
        run_results[step_name_eval_transcript] = {
            "status": "Skipped",
            "output_files": [],
        }

    # --- Step 3: Parse Transcript ---
    # Assuming transcript_processing.py processes all files in the raw dir.
    # We still check for the specific expected output file based on our (potentially updated) uuid_str.
    step_name_parse_transcript = "Parse Transcript"
    # Use the potentially updated processed_transcript_path
    if (
        success_gen_transcript
        and actual_transcript_path
        and actual_transcript_path.exists()
    ):  # Check if raw transcript exists
        # Pass explicit input and output paths to the modified script
        parse_transcript_args = [
            "--input",
            str(actual_transcript_path),
            "--output",
            str(processed_transcript_path),
        ]
        success_parse_transcript = run_step(
            step_name_parse_transcript,
            parse_transcript_script,
            parse_transcript_args,
            run_results,
        )
        # Check if the specific file we need was created by the batch process
        if processed_transcript_path.exists():
            run_results[step_name_parse_transcript]["output_files"] = [
                str(processed_transcript_path.relative_to(PROJECT_ROOT))
            ]
            if (
                not success_parse_transcript
            ):  # If script failed but file exists, mark success based on file existence
                run_results[step_name_parse_transcript]["status"] = (
                    "Success (Output Found)"
                )
                success_parse_transcript = True
        else:
            # If the script ran but didn't create the file, mark failure
            success_parse_transcript = False
            run_results[step_name_parse_transcript]["status"] = (
                "Failure (Output Not Found)"
            )
            logging.error(
                f"Expected output file not found after running '{step_name_parse_transcript}': {processed_transcript_path}"
            )
    else:
        logging.warning(
            f"Skipping step '{step_name_parse_transcript}' due to previous step failure."
        )
        run_results[step_name_parse_transcript] = {
            "status": "Skipped",
            "output_files": [],
        }
        success_parse_transcript = False  # Ensure dependent steps are skipped

    # --- Step 4: Extract Requirements ---
    step_name_extract_reqs = "Extract Requirements"
    # Use the potentially updated requirements_path and processed_transcript_path
    if success_parse_transcript and processed_transcript_path.exists():
        # Pass the specific processed transcript path to the modified extractor script
        extract_reqs_args = [
            "--input",
            str(processed_transcript_path),
            "--output",
            str(requirements_path),  # Provide the expected output path
        ]
        success_extract_reqs = run_step(
            step_name_extract_reqs,
            extract_requirements_script,
            extract_reqs_args,
            run_results,
        )
        if success_extract_reqs:
            run_results[step_name_extract_reqs]["output_files"] = [
                str(requirements_path.relative_to(PROJECT_ROOT))
            ]
    else:
        logging.warning(
            f"Skipping step '{step_name_extract_reqs}' due to previous step failure or missing input file."
        )
        run_results[step_name_extract_reqs] = {"status": "Skipped", "output_files": []}
        success_extract_reqs = False

    # --- Step 5: Generate Comparison Reports ---
    step_name_gen_compare = "Generate Comparison Reports"
    # Use the potentially updated uuid_str and requirements_path
    if success_extract_reqs and requirements_path.exists():
        gen_compare_args = [
            "--customer_id",
            uuid_str,
        ]  # Pass the potentially updated UUID
        success_gen_compare = run_step(
            step_name_gen_compare,
            generate_comparison_script,
            gen_compare_args,
            run_results,
        )
        if success_gen_compare:
            # List actual report files generated? Or just the dir? Let's list the dir.
            run_results[step_name_gen_compare]["output_files"] = [
                str(comparison_results_dir.relative_to(PROJECT_ROOT))
            ]
    else:
        logging.warning(
            f"Skipping step '{step_name_gen_compare}' due to previous step failure or missing input file."
        )
        run_results[step_name_gen_compare] = {"status": "Skipped", "output_files": []}
        success_gen_compare = False

    # --- Step 6: Evaluate Comparison Reports ---
    step_name_eval_compare = "Evaluate Comparison Reports"
    # Use the potentially updated uuid_str and comparison_results_dir
    if success_gen_compare and comparison_results_dir.exists():
        eval_compare_args = [
            "--uuid",  # Corrected argument name
            uuid_str,  # Pass the potentially updated UUID
        ]
        success_eval_compare = run_step(
            step_name_eval_compare,
            eval_comparison_script,
            eval_compare_args,
            run_results,
        )
        if success_eval_compare:
            run_results[step_name_eval_compare]["output_files"] = [
                str(compare_eval_dir.relative_to(PROJECT_ROOT))
            ]
    else:
        logging.warning(
            f"Skipping step '{step_name_eval_compare}' due to previous step failure or missing input directory."
        )
        run_results[step_name_eval_compare] = {"status": "Skipped", "output_files": []}
        success_eval_compare = False  # Ensure dependent steps know

    # --- Step 7: Generate Recommendation Report ---
    step_name_gen_rec = "Generate Recommendation Report"
    # Use the potentially updated uuid_str and recommendation_report_path
    if success_gen_compare:
        gen_rec_args = ["--customer_id", uuid_str]  # Pass the potentially updated UUID
        success_gen_rec = run_step(
            step_name_gen_rec, generate_recommendation_script, gen_rec_args, run_results
        )
        if success_gen_rec:
            run_results[step_name_gen_rec]["output_files"] = [
                str(recommendation_report_path.relative_to(PROJECT_ROOT))
            ]
    else:
        logging.warning(
            f"Skipping step '{step_name_gen_rec}' due to previous step failure."
        )
        run_results[step_name_gen_rec] = {"status": "Skipped", "output_files": []}
        success_gen_rec = False

    # --- Step 8: Evaluate Scenario Recommendation ---
    step_name_eval_scenario = "Evaluate Scenario Recommendation"
    # Use the potentially updated uuid_str and scenario_eval_path

    # Skip if no scenario was provided OR if the flag was explicitly set
    # Note: scenario_name is 'no_scenario' if args.scenario was None
    if skip_scenario_specific_eval:
        skip_reason = "(No Scenario)" if args.scenario is None else "(Flag)"
        logging.info(f"Skipping step '{step_name_eval_scenario}' due to {skip_reason}.")
        run_results[step_name_eval_scenario] = {
            "status": f"Skipped {skip_reason}",
            "output_files": [],
        }
    elif success_gen_rec and recommendation_report_path.exists():
        # This part only runs if a scenario was provided (args.scenario is not None) AND the skip flag was NOT set
        eval_scenario_args = [
            "--scenario",
            scenario_name,
            "-o",  # Output file argument to specify where to save results
            str(
                scenario_eval_path
            ),  # Path where the orchestrator expects the output file
            "--target-uuid",  # Target UUID argument to focus on just this UUID
            uuid_str,  # Pass the UUID for the current run
        ]
        success_eval_scenario = run_step(
            step_name_eval_scenario,
            eval_scenario_script,
            eval_scenario_args,
            run_results,
        )
        if success_eval_scenario:
            # Check if the expected output file exists after running
            if scenario_eval_path.exists():
                run_results[step_name_eval_scenario]["output_files"] = [
                    str(scenario_eval_path.relative_to(PROJECT_ROOT))
                ]
            else:
                # If script succeeded but file doesn't exist (maybe saved elsewhere?)
                logging.warning(
                    f"Scenario evaluation script succeeded but expected output file not found: {scenario_eval_path}"
                )
                run_results[step_name_eval_scenario]["output_files"] = [
                    "Output path unknown or missing"
                ]
                # Keep status as Success since script returned 0

    else:
        logging.warning(
            f"Skipping step '{step_name_eval_scenario}' due to previous step failure or missing input file."
        )
        run_results[step_name_eval_scenario] = {
            "status": "Skipped (Dependency)",
            "output_files": [],
        }

    # --- Step 9: Generate Ground Truth Coverage ---
    step_name_gen_coverage = "Generate Ground Truth Coverage"
    # Use the potentially updated uuid_str, requirements_path, recommendation_report_path, coverage_eval_path
    if (
        success_gen_rec
        and success_extract_reqs
        and recommendation_report_path.exists()
        and requirements_path.exists()
    ):
        gen_coverage_args = ["--customer", uuid_str]  # Corrected argument name
        success_gen_coverage = run_step(
            step_name_gen_coverage,
            generate_coverage_script,
            gen_coverage_args,
            run_results,
        )
        if success_gen_coverage:
            run_results[step_name_gen_coverage]["output_files"] = [
                str(coverage_eval_path.relative_to(PROJECT_ROOT))
            ]  # Adjust if script saves differently
    else:
        logging.warning(
            f"Skipping step '{step_name_gen_coverage}' due to previous step failure or missing input files."
        )
        run_results[step_name_gen_coverage] = {"status": "Skipped", "output_files": []}

    # --- Task 7: Implement Summary Generation ---
    # Define final summary path using the potentially updated uuid_str
    summary_report_path = PROJECT_ROOT / f"demo_summary_{uuid_str}.md"
    logging.info(
        f"Final Summary Report will be saved to: {summary_report_path.relative_to(PROJECT_ROOT)}"
    )  # Log the final path here
    generate_summary_markdown(run_results, scenario_name, uuid_str, summary_report_path)

    logging.info("Demo pipeline execution finished.")
    logging.info(
        f"Summary report saved to: {summary_report_path.relative_to(PROJECT_ROOT)}"
    )
    logging.info("-" * 60)
    logging.info("Demo run complete.")
    logging.info("-" * 60)


if __name__ == "__main__":
    main()
