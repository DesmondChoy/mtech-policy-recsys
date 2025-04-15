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
            *   If not `skip_transcript_eval`: Call `scripts/evaluation/transcript_evaluation/eval_transcript_main.py`. Parse results to determine passed UUIDs. **(Note: Pass/fail criteria TBD).**
            *   Return set of passed UUIDs or `None`.
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

5.  **Final Evaluation (Asynchronous per Scenario)**:
    *   Implement a function `run_final_evaluation_async(scenarios)`:
        *   Define a helper function `_evaluate_scenario(scenario)` that calls `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario {scenario}` and captures/logs the summary.
        *   Use `multiprocessing.Pool` to run `_evaluate_scenario` for each scenario in parallel.

6.  **Main Orchestration Logic**:
    *   Implement the `main` function to call the steps sequentially: `generate_transcripts_async`, `run_pipeline`, `generate_reports_async`, `run_final_evaluation_async`. Log progress and errors.

## 4. Implementation Steps

1.  **[X] Create Script File**: `scripts/orchestrate_scenario_evaluation.py`.
2.  **[X] Basic Structure**: Imports, constants, args, logging, main block.
3.  **[X] Implement `generate_transcripts_async`**: Parallel generation using `multiprocessing.Pool`.
4.  **[X] Implement `run_pipeline`**: Sequential calls to batch scripts (eval, parse, extract). Placeholder for eval pass/fail logic.
5.  **[X] Implement `generate_reports_async`**: Parallel report generation per UUID using `multiprocessing.Pool`.
6.  **[X] Implement `run_final_evaluation_async`**: Parallel final evaluation per scenario using `multiprocessing.Pool`.
7.  **[X] Add Error Handling**: Basic `subprocess.run` and `multiprocessing` error handling and logging added.
8.  **[ ] Refine & Test**: Test with small numbers, refine eval pass/fail logic, test parallelism, add detailed logging.
9.  **[X] Documentation**: Comprehensive docstring added.
10. **[ ] Update Memory Bank**: Update `activeContext.md` and `progress.md`.

## 5. Dependencies

*   Existing project scripts.
*   Python standard libraries (`os`, `subprocess`, `glob`, `logging`, `argparse`, `pathlib`, `json`, `multiprocessing`).

## 6. Open Questions / Decisions

*   **Transcript Evaluation Pass/Fail Criteria**: How to determine? (Deferring detailed implementation).
*   **Error Handling Strategy**: Confirm continue-on-error is acceptable. (Assuming continue).

## 7. Rollback Plan

*   Delete `scripts/orchestrate_scenario_evaluation.py`. Individual scripts remain usable manually.
