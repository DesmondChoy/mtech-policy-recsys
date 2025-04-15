# Implementation Plan: Scenario Evaluation Orchestration Script

**Date:** 2025-04-15

**Author:** Cline

**Status:** Proposed (Revised 2)

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

6.  **Main Orchestration Logic**:
    *   Implement the `main` function to call the steps sequentially: `generate_transcripts_async`, `run_pipeline`, `generate_reports_async`, `aggregate_and_filter_evaluations`. Log progress and errors.

## 4. Implementation Steps

1.  **[X] Create Script File**: `scripts/orchestrate_scenario_evaluation.py`.
2.  **[X] Basic Structure**: Imports, constants, args, logging, main block.
3.  **[X] Implement `generate_transcripts_async`**: Parallel generation using `multiprocessing.Pool`.
4.  **[X] Implement `run_pipeline` - Parse Results Logic**: Implemented the defined pass/fail logic within `_parse_transcript_evaluation_results`, replacing the placeholder. (Script calls were already implemented).
5.  **[X] Implement `generate_reports_async`**: Parallel report generation per UUID using `multiprocessing.Pool`.
6.  **[X] Implement `aggregate_and_filter_evaluations`**: Implemented the final evaluation execution and result aggregation logic. (Replaced the previous `run_final_evaluation_async`).
7.  **[X] Add Error Handling**: Basic `subprocess.run` and `multiprocessing` error handling and logging added.
8.  **[ ] Refine & Test**: Test with small numbers, test aggregation, test parallelism, add detailed logging.
9.  **[X] Documentation**: Comprehensive docstring added.
10. **[ ] Update Memory Bank**: Update `activeContext.md` and `progress.md`.

## 5. Dependencies

*   Existing project scripts.
*   Python standard libraries (`os`, `subprocess`, `glob`, `logging`, `argparse`, `pathlib`, `json`, `multiprocessing`).

## 6. Open Questions / Decisions

*   **Transcript Evaluation Pass/Fail Criteria**: Defined as: All individual evaluations have `"result": "PASS"` AND `len(evaluations) == summary.total_requirements`. Implementation pending in `_parse_transcript_evaluation_results`.
*   **Error Handling Strategy**: Confirm continue-on-error is acceptable. (Assuming continue).

## 7. Rollback Plan

*   Delete `scripts/orchestrate_scenario_evaluation.py`. Individual scripts remain usable manually.
