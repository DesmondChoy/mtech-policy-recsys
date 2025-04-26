# Orchestration Script for Presentation Demo (`run_recsys_demo.py`)

## Objective

The existing orchestration script (`scripts/orchestrate_scenario_evaluation.py`) is designed for comprehensive scenario testing and evaluation during development. Its output can be verbose, and it doesn't easily showcase the results of *intermediate* evaluation steps (like comparison report quality) alongside the main pipeline flow in a single, clear run suitable for a presentation to professors. Running multiple separate scripts would be cumbersome and less impactful for a demo.

*   Presenting the system effectively requires a streamlined way to demonstrate the entire pipeline, including key evaluation checkpoints, from a single command.
*   The current main orchestrator focuses on final scenario outcomes rather than illustrating the step-by-step process and intermediate quality checks.
*   A dedicated script is needed to provide a curated, easy-to-follow execution flow specifically for demonstration purposes.

## Solution

Create a dedicated Python script (`scripts/run_recsys_demo.py`) that provides a clear, sequential, and easy-to-run demonstration of the core recommendation system pipeline. This script will:
1.  Accept an optional `--scenario` argument. If omitted, a generic transcript is generated, and scenario-specific evaluation is skipped.
2.  Accept an optional `--skip_scenario_eval` flag to explicitly skip scenario evaluation even if a scenario is provided.
3.  Generate **one** new transcript (either for the specified scenario or a generic one) with a unique UUID generated internally by `generate_transcripts.py`.
4.  Robustly extract the actual UUID used by `generate_transcripts.py` from the generated filename.
5.  Execute the core pipeline steps sequentially using the extracted UUID for path calculations.
6.  Execute relevant *intermediate* evaluation steps (transcript quality, comparison report quality, ground truth coverage) within the same flow.
7.  Execute the final scenario recommendation evaluation *only if* a scenario was provided and the `--skip_scenario_eval` flag was not set.
8.  Print clear console messages indicating progress and status for each step.
9.  Generate a final Markdown summary report (`demo_summary_{uuid}.md` in the root directory) documenting the run details, steps, status, and output file paths.
10. Continue processing subsequent steps even if one step fails, noting the failure in the console and summary report.

## Implementation Plan

*   [x] **Task 1: Create Script File**
    *   [x] Create `scripts/run_recsys_demo.py`.
*   [x] **Task 2: Imports and Setup**
    *   [x] Add necessary imports (`argparse`, `subprocess`, `uuid`, `os`, `pathlib`, `datetime`, `logging`, `sys`).
    *   [x] Add project root to `sys.path`.
    *   [x] Configure basic logging.
    *   [x] Define script/directory path constants using `pathlib.Path`.
*   [x] **Task 3: Argument Parsing (Revised)**
    *   [x] Implement `argparse` for optional `--scenario` argument (defaulting to `None`).
    *   [x] Add `--skip_scenario_eval` flag (defaulting to `False`).
    *   [x] Add validation for scenario file existence *only if* a scenario is provided.
*   [x] **Task 4: UUID Handling & Initial Output (Revised)**
    *   [x] Generate an initial `uuid.uuid4()` for logging/reporting.
    *   [x] Implement logic to find the most recently generated transcript file after Step 1.
    *   [x] Implement helper function `_extract_uuid_from_filename` to parse the UUID from the actual transcript filename.
    *   [x] Update the run's `uuid_str` variable with the extracted UUID.
    *   [x] Print initial console message about the run and summary report location.
*   [x] **Task 5: Implement Helper Function (`run_step`)**
    *   [x] Define `run_step(step_name: str, script_path: Path, args: List[str],    results_tracker: dict) -> bool`.
    *   [x] Implement subprocess execution (`subprocess.run`) with `check=False`, output capture, and CWD set.
    *   [x] Implement logging for command, status, stdout/stderr.
    *   [x] Implement recording of success/failure and output paths to `results_tracker`.
    *   [x] Implement console start/finish messages.
    *   [x] Return `True`/`False` based on `returncode`.
*   [x] **Task 6: Implement Main Pipeline Logic**
    *   [x] Initialize `run_results = {}`.
    *   [x] Call `run_step` sequentially for:
        *   [x] Generate Transcript (`generate_transcripts.py`) - Capture raw transcript path.
        *   [x] Evaluate Transcript (`eval_transcript_main.py`) - Capture eval result path.
        *   [x] Parse Transcript (`transcript_processing.py`) - Capture processed transcript path. (Verify args/method).
        *   [x] Extract Requirements (`extractor.py`) - Capture requirements JSON path. (Verify args).
        *   [x] Generate Comparison Reports (`generate_policy_comparison.py`) - Capture results dir path.
        *   [x] Evaluate Comparison Reports (`eval_comparison_report.py`) - Capture comparison eval path(s).
        *   [x] Generate Recommendation Report (`generate_recommendation_report.py`) - Capture recommendation report path.
        *   [x] Evaluate Scenario Recommendation (`evaluate_scenario_recommendations.py`) - Capture scenario eval path. (Verify args). **(Conditional Execution)**: Only run if a scenario was provided and `--skip_scenario_eval` is false.
        *   [x] Generate Ground Truth Coverage (`generate_ground_truth_coverage.py`) - Capture coverage eval path.
    *   [x] Ensure correct arguments are passed to `generate_transcripts.py` (omit `-s` if no scenario).
    *   [x] Ensure subsequent path calculations use the potentially updated `uuid_str` extracted from the generated transcript.
    *   [x] Add file existence checks where prudent before running dependent steps.
*   [x] **Task 7: Implement Summary Generation**
    *   [x] Define `generate_summary_markdown(run_results: dict, scenario: str, uuid_str: str)`.
    *   [x] This function will format the data stored in the `run_results` dictionary (which tracks the status and output paths of each step) into a Markdown string.
    *   [x] **Markdown Structure:**
            *   **Title:** `# RecSys Demo Run Summary`
            *   **Run Details Section:**
                *   `## Run Details`
                *   `- **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
                *   `- **Scenario Used:** {scenario}`
                *   `- **Generated UUID:** {uuid_str}`
            *   **Step Summary Section:**
                *   `## Pipeline Step Summary`
                *   Use a Markdown table or a formatted list to detail each step executed.
                *   **Columns/Info per Step:**
                    *   `Step Name`: The descriptive name of the pipeline step (e.g., "Generate Transcript", "Evaluate Transcript").
                    *   `Status`: Indicate `Success` or `Failure`. If failed, potentially add a note about the error (optional, depending on complexity).
                    *   `Output File(s)`: List the relative path(s) to the primary output file(s) generated by this step. Make these paths clickable links if possible in Markdown (`[filename](./path/to/filename)`). Handle cases where a step might produce multiple outputs (e.g., comparison reports) or directory outputs.
                    *   `Description`: A brief explanation of what the output file(s) contain or represent (e.g., "Raw synthetic conversation transcript", "Structured customer requirements", "Final recommendation report").
    *   [x] Ensure relative paths are used for all file links, assuming the summary report is in the project root.
    *   [x] Write the generated Markdown string to `./demo_summary_{uuid_str}.md`.
*   [x] **Task 8: Finalize**
    *   [x] Add final "Demo run complete" console message.
    *   [x] Add script-level docstring.
    *   [x] Review and refine error handling and logging.

## Debugging and Resolution (Post-Implementation)

During testing of `run_recsys_demo.py`, several issues were identified and resolved:

1.  **Issue:** "Parse Transcript" step failed because `src/utils/transcript_processing.py` was only designed for batch processing and didn't create the specific output file expected by the demo script when called without arguments.
    *   **Resolution:** Modified `src/utils/transcript_processing.py` to accept `--input` and `--output` arguments for single-file processing. Updated `run_recsys_demo.py` to call it with these arguments, passing the specific raw transcript path and the expected parsed output path.
2.  **Issue:** "Evaluate Transcript" step failed due to an incorrect argument name (`--transcript_path` instead of `--transcript`) being passed to `scripts/evaluation/transcript_evaluation/eval_transcript_main.py`.
    *   **Resolution:** Corrected the argument name to `--transcript` in the `run_recsys_demo.py` script call.
3.  **Issue:** "Extract Requirements" step processed the entire directory instead of the single generated transcript because `src/agents/extractor.py` only supported batch mode.
    *   **Resolution:** Modified `src/agents/extractor.py` to accept `--input` and `--output` arguments for single-file processing. Updated `run_recsys_demo.py` to call it with these arguments, passing the specific processed transcript path and the expected requirements output path.
4.  **Issue:** "Evaluate Comparison Reports" step failed due to an incorrect argument name (`--customer_id` instead of `--uuid`) being passed to `scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py`.
    *   **Resolution:** Corrected the argument name to `--uuid` in the `run_recsys_demo.py` script call.
5.  **Issue:** "Generate Ground Truth Coverage" step initially failed with `ModuleNotFoundError` for `nltk` and then `sklearn`.
    *   **Resolution:** Confirmed with the user that both `nltk` and `scikit-learn` are installed in the active virtual environment (`.venv`), resolving the dependency issues.

**Current Status:** The `run_recsys_demo.py` script is now expected to run successfully end-to-end, processing a single transcript and generating all intermediate and final outputs as designed.

6.  **Issue:** Script hangs during import on macOS (specifically involving `nltk` -> `sklearn` imports).
    *   **Cause:** Potential parallelism issue with underlying libraries (like NumPy/SciPy used by scikit-learn) on macOS, especially Apple Silicon.
    *   **Resolution:** Set the `OMP_NUM_THREADS` environment variable to `1` before running the script to force single-threaded execution: `export OMP_NUM_THREADS=1; python scripts/run_recsys_demo.py`.
7.  **Issue:** "Generate Ground Truth Coverage" step overwrote existing summary files (`coverage_evaluation_summary.json`, `coverage_evaluation_summary.md`) on subsequent runs.
    *   **Resolution:** Modified `scripts/generate_ground_truth_coverage.py` to include an `--overwrite` flag (defaulting to `False`). The script now checks this flag before writing summary files, preventing accidental overwrites unless explicitly requested. The calling script (`run_recsys_demo.py`) does not pass this flag, ensuring the default non-overwriting behavior.
8.  **Issue:** Intermittent missing comparison report evaluation files (e.g., 3 evaluation files generated for 4 comparison reports).
    *   **Cause:** The `eval_comparison_report.py` script processes reports sequentially. An intermittent error during the multi-modal LLM call for a single insurer (likely due to API rate limits or temporary glitches) caused that specific evaluation to fail silently (from the perspective of the demo script's orchestrator), but the script continued and exited successfully, leading to a mismatch.
    *   **Resolution:** Added retry logic (up to 3 attempts with exponential backoff) around the `llm_service.generate_structured_content` call within the `evaluate_single_insurer` function in `scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py` to make the evaluation of individual reports more resilient to transient LLM API errors.
9.  **Issue:** Running the demo script on macOS required manually setting `export OMP_NUM_THREADS=1` to prevent hangs.
    *   **Cause:** Potential parallelism conflicts in underlying libraries (NumPy/SciPy via NLTK/Sklearn) on macOS.
    *   **Resolution:** Modified `scripts/run_recsys_demo.py` to automatically detect if running on macOS (`sys.platform == "darwin"`) and set `os.environ['OMP_NUM_THREADS'] = '1'` at the start of the script if it's not already set. This removes the need for manual export by the user.
10. **Enhancement:** The "Evaluate Comparison Reports" step (`scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py`), called by the demo script, was enhanced to provide more accurate evaluations.
    *   **Context:** The original evaluation prompt didn't account for the valid use of external tier ranking data (`data/policies/pricing_tiers/tier_rankings.py`) for tie-breaking when comparing policies.
    *   **Resolution:** Updated the evaluation script to load the specific insurer's tier ranking list and include it directly in the prompt for the LLM evaluator. Refined prompt instructions guide the LLM to correctly validate the use of this ranking data during tie-breaking, in addition to checking claims against the policy PDF. This prevents incorrect failures due to valid price/preference justifications.
11. **Enhancement:** The demo summary report (`demo_summary_{uuid}.md`) format was changed for better readability.
    *   **Context:** The previous Markdown table format did not handle long file paths well, making the summary difficult to read.
    *   **Resolution:** Modified the `generate_summary_markdown` function in `scripts/run_recsys_demo.py` to use a structured list format (headings for each step, bullet points for details like status, duration, output links, and description). This improves readability, especially for the output file paths.
