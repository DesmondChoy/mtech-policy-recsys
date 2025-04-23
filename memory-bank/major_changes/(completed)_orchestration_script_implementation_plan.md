# Implementation Plan: Scenario Evaluation Orchestration Script

**Date:** 2025-04-15

**Author:** Cline

**Status:** ✅ Completed  

## 1. Goal

Create a Python script (`scripts/orchestrate_scenario_evaluation.py`) to automate the end-to-end process of generating synthetic transcripts for specific scenarios, processing them through the existing pipeline, and evaluating the final recommendations against ground truth. Intermediate files will be preserved for debugging.

## 2. Background

Currently, generating scenario-specific data, running it through the various processing scripts (evaluation, parsing, extraction, comparison, recommendation), and evaluating the final output requires manual execution of multiple steps. This process is time-consuming and prone to errors, especially when testing multiple scenarios or variations. An orchestration script will streamline this workflow, improve efficiency, and ensure consistency. Key steps like transcript generation, report generation, and final evaluation will be parallelized.

## 3. Proposed Solution

Develop a new Python script (`scripts/orchestrate_scenario_evaluation.py`) that performs the following steps:

1.  **Configuration & Setup**:
    *   Import necessary libraries (`os`, `subprocess`, `glob`, `logging`, `argparse`, `pathlib`, `json`, `multiprocessing`).
    *   Define constants for paths (data directories, results, scripts).
    *   Define the list of target scenario names (`golf_coverage`, `pet_care_coverage`, `public_transport_double_cover`, `uncovered_cancellation_reason`).
    *   Set up logging.
    *   Implement command-line argument parsing (`argparse`) for:
        *   `--num_transcripts` (default: 5)
        *   `--skip_transcript_eval` (default: False)

2.  **Transcript Generation (Asynchronous)**:
    *   Implement a function `generate_transcripts_async(scenarios, num_transcripts)`:
        *   Define a helper function `_generate_for_scenario(scenario, num_transcripts)` that calls the generation script via `subprocess.run` and returns the list of generated UUIDs for that scenario.
        *   Use `multiprocessing.Pool` to run `_generate_for_scenario` for each scenario in parallel.
        *   Collect and consolidate results into a dictionary mapping scenarios to UUID lists and a master list of all generated UUIDs.

3.  **Pipeline Execution (Sequential Batch)**:
    *   Implement a function `run_pipeline(all_uuids, skip_transcript_eval)`:
        *   **Transcript Evaluation (Conditional)**:
            *   If not `skip_transcript_eval`: Call `scripts/evaluation/transcript_evaluation/eval_transcript_main.py`.
            *   Parse the generated evaluation JSON results (`data/evaluation/transcript_evaluations/`) to determine passed UUIDs based on defined criteria:
                *   All individual evaluations in the `evaluations` list must have `"result": "PASS"`.
                *   The count of evaluations must match `summary.total_requirements`.
            *   Return the set of passed UUIDs.
        *   **Transcript Parsing**: Call `src/utils/transcript_processing.py`. Check errors.
        *   **Requirement Extraction**: Call `src/agents/extractor.py`. Check errors.

4.  **Report Generation (Asynchronous per UUID)**:
    *   Implement a function `generate_reports_async(all_uuids, passed_uuids)`:
        *   Define a helper function `_generate_reports_for_uuid(uuid)`:
            *   Check if evaluation was run and if the UUID passed (if applicable).
            *   Check for prerequisite files (processed transcript, requirements).
            *   Call `scripts/generate_policy_comparison.py --customer_id {uuid}`.
            *   Call `scripts/generate_recommendation_report.py --customer_id {uuid}`.
        *   Filter `all_uuids` based on `passed_uuids` if evaluation was run.
        *   Use `multiprocessing.Pool` to run `_generate_reports_for_uuid` for each valid UUID in parallel.

5.  **Final Evaluation & Aggregation**:
    *   Implement a function `aggregate_and_filter_evaluations(scenario_uuids)`:
        *   Loop through each scenario and its associated list of generated UUIDs (`scenario_uuids`).
        *   For each scenario, call `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario {scenario}` using `subprocess.run`. This script saves its own timestamped output file.
        *   Find the latest evaluation result file generated for that scenario.
        *   Read the JSON content of the latest result file.
        *   Filter the results, keeping only entries whose UUIDs are present in the `scenario_uuids` list for that scenario (i.e., only results from the current orchestration run).
        *   Save the filtered list to a new aggregated JSON file (e.g., `results_{scenario}_aggregated_{run_timestamp}.json`).
        *   **Note:** This step intentionally creates two files per scenario in the output directory (`data/evaluation/scenario_evaluation/`). The first (`results_{scenario}_{timestamp}.json`) is the raw output from `evaluate_scenario_recommendations.py` (which might include results from previous runs if not cleaned). The second (`results_{scenario}_aggregated_{run_timestamp}.json`) is created by this orchestrator step and contains *only* the filtered results relevant to the transcripts generated in the current orchestration run. The `_aggregated_` file is the primary output to consider for the results of a specific orchestration execution.

6.  **Main Orchestration Logic**:
    *   Implement the `main` function to call the steps sequentially: `generate_transcripts_async`, `run_pipeline`, `generate_reports_async`, `aggregate_and_filter_evaluations`. Log progress and errors.

## 4. Implementation Steps

1.  **[X] Create Script File**: `scripts/orchestrate_scenario_evaluation.py`.
2.  **[X] Basic Structure**: Imports, constants, args, logging, main block.
3.  **[X] Implement `generate_transcripts_async`**: Parallel generation using `multiprocessing.Pool`.
4.  **[X] Implement `run_pipeline` - Refactor Evaluation Call**: Modified the execution of the transcript evaluation step (Step 2.1) within this function to call `eval_transcript_main.py` in parallel for each transcript using `multiprocessing.Pool`.
5.  **[X] Implement `generate_reports_async`**: **Modified** to process report generation (comparison + recommendation) **sequentially** per UUID to mitigate potential API rate limits. Removed `multiprocessing.Pool`.
6.  **[X] Implement `aggregate_and_filter_evaluations`**: Implemented the final evaluation execution and result aggregation logic. (Replaced the previous `run_final_evaluation_async`).
7.  **[X] Add Error Handling**: Basic `subprocess.run` and `multiprocessing` error handling and logging added.
8.  **[X] Refactor `eval_transcript_main.py` for Single File Input**: Modified `scripts/evaluation/transcript_evaluation/eval_transcript_main.py` to accept `--transcript` argument, process only that file, and return appropriate exit codes for parallel execution by the orchestrator. Retained `--directory` functionality for standalone use.
9.  **[X] Refine & Test**:
    *   Test the complete workflow with larger numbers.
    *   Verify transcript evaluation pass/fail logic (if implementing strict criteria beyond script success/fail).
    *   Test aggregation logic thoroughly.
    *   Test robustness of sequential report generation.
    *   **[X]** Add detailed logging before/after the `llm_service.generate_content` call in `scripts/generate_policy_comparison.py` (within `generate_insurer_report`) to pinpoint failures for specific insurers. **(Completed)**
    *   Consider adding exponential backoff/retry logic specifically around the LLM call in `generate_policy_comparison.py` if intermittent failures persist despite sequential processing.
10. **[X] Documentation**: Comprehensive docstring added to orchestrator.
11. **[X] Update Memory Bank**: Update `activeContext.md` and `progress.md`. Check if other files need to be updated too in memory-bank.

## 4.1 Debugging Findings & Revised Plan (2025-04-15)

*   **Pain Point:** Inconsistent number of policy comparison reports generated per UUID (sometimes 2, 3, or 4 instead of the expected 4). This leads to incomplete data for recommendation generation and inaccurate final evaluations.
*   **Diagnosis:** The high level of concurrency during report generation is the likely cause. The orchestrator's `generate_reports_async` uses `multiprocessing.Pool` to process multiple UUIDs in parallel. Simultaneously, the called `generate_policy_comparison.py` script uses `asyncio.gather` to process all insurers for a single UUID concurrently. This combined parallelism likely leads to exceeding LLM API rate limits, causing intermittent failures in generating reports for specific insurers.
*   **Proposed Solution (Revised Step 4):** Modify the orchestrator's `generate_reports_async` function to remove the `multiprocessing.Pool`. Instead, iterate through the valid UUIDs sequentially and call the helper function `_generate_reports_for_uuid` for one UUID at a time. This will significantly reduce the peak number of concurrent LLM API calls (down to the number of insurers, likely 4), mitigating rate limit issues at the cost of longer overall execution time for the report generation step. The internal `asyncio` concurrency within `generate_policy_comparison.py` for insurers will remain.

## 5. Dependencies

*   Existing project scripts.
*   Python standard libraries (`os`, `subprocess`, `glob`, `logging`, `argparse`, `pathlib`, `json`, `multiprocessing`).

## 6. Open Questions / Decisions

*   **Transcript Evaluation Pass/Fail Criteria**: Defined as: All individual evaluations have `"result": "PASS"` AND `len(evaluations) == summary.total_requirements`. Implementation pending in `_parse_transcript_evaluation_results`.
*   **Error Handling Strategy**: Confirm continue-on-error is acceptable. (Assuming continue).

## 7. Rollback Plan

*   Delete `scripts/orchestrate_scenario_evaluation.py`. Individual scripts remain usable manually.
