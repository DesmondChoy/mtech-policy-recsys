# Project Progress

## Current Status

The project is in the **initial setup and planning phase**. We are currently establishing the foundation for development by setting up the project structure, collecting data, and creating documentation.

## What Works

1.  **Project Structure**: Core directory structure is established.
2.  **Data Collection**: Initial policy PDFs and synthetic transcripts collected. Coverage requirements defined.
3.  **Documentation**: Core Memory Bank files initialized, README updated. (Undergoing update now).
4.  **LLM Service (Gemini)**: Reusable service (`src/models/llm_service.py`) for Gemini API interaction, including configuration, retries, and enhanced JSON parsing.
5.  **Data Generation Scripts**:
    *   `scripts/data_generation/generate_personalities.py`: Generates personality types.
    *   `scripts/data_generation/generate_transcripts.py`: Generates synthetic transcripts using scenarios, requirements, personalities, and `LLMService`.
6.  **Transcript Evaluation**: Script (`scripts/evaluation/transcript_evaluation/`) evaluates generated transcript quality using `LLMService`. Acts as a quality gate.
7.  **Transcript Parsing**: Utility (`src/utils/transcript_processing.py`) parses evaluated transcripts into a standard format.
8.  **Extractor Agent (CrewAI/OpenAI)**: Functional agent (`src/agents/extractor.py`) extracts structured requirements from processed transcripts using OpenAI via `crewai`. Includes batch processing.
9.  **Policy Extraction Script**: Script (`scripts/extract_policy_tier.py`) extracts structured policy details from PDFs using `LLMService`. Includes detailed extraction logic (base/conditional limits, source details).
10. **Policy Comparison Script**: Script (`scripts/generate_policy_comparison.py`) generates insurer-level Markdown comparison reports using `LLMService`, extracted requirements, and processed policies.
11. **PDF Extraction Evaluation Script**: Script (`scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py`) compares processed policy JSON against source PDF using multi-modal LLM (`LLMService`) for accuracy/completeness checks. Enhanced with `--file_pattern` argument for flexible input filtering.
12. **Recommendation Report Script**: Script (`scripts/generate_recommendation_report.py`) orchestrates the two-stage recommendation process: parses comparison reports, applies Stage 1 scoring, calls `LLMService` for Stage 2 re-ranking (prompt updated to use transcript context for prioritization and request source references), and generates/saves a final customer-friendly Markdown report. (Note: Requirements summary context removed from Stage 2). Includes unit tests for parser, scoring, and Markdown generation.
13. **Ground Truth Data**: Curated ground truth (`data/ground_truth/ground_truth.json`) defining expected outcomes for specific scenarios.
14. **Embedding Utilities**: `EmbeddingMatcher` class (`src/embedding/embedding_utils.py`) for semantic comparison using OpenAI embeddings, including caching (`src/embedding/cache/`).
15. **Scenario Recommendation Evaluation Script**: Script (`scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`) evaluates final recommendations against ground truth using semantic matching via `EmbeddingMatcher`.
16. **Ground Truth Coverage Script**: Script (`scripts/generate_ground_truth_coverage.py`) likely uses `EmbeddingMatcher` to analyze coverage against ground truth (exact function TBC).
17. **Node.js/Frontend Setup**: After cloning, run `npm install` to install Node.js dependencies if you intend to use any web or supporting scripts.

## What's Left to Build

1.  **Test & Refine PDF Extraction Evaluation**:
    *   [ ] Run the new `eval_pdf_extraction.py` script with sample data.
    *   [ ] Analyze results and refine the script/prompt as needed.
    *   [ ] Define clear metrics for this evaluation (potentially derived from the script's JSON output).
2.  **Test & Refine Scenario Recommendation Evaluation**:
    *   [ ] Run `evaluate_scenario_recommendations.py` with diverse sample data.
    *   [ ] Analyze results, refine `EmbeddingMatcher` logic/thresholds, and improve `ground_truth.json` as needed.
3.  **Implement Comparison Report Evaluation**:
    *   [ ] Design and implement the evaluation script/process for `scripts/generate_policy_comparison.py` output.
    *   [ ] Define metrics for report quality, accuracy, and justification clarity.
4.  **Orchestration Script**: Script (`scripts/orchestrate_scenario_evaluation.py`) automates the end-to-end workflow (generation, evaluation, parsing, extraction, comparison, recommendation, final evaluation). Includes parallel transcript evaluation, sequential report generation, and flags (`--skip_transcript_eval`, `--only_aggregate`) to control execution.
5.  **Refine Core Logic**:
    *   [ ] Iteratively improve prompts, models, and processing logic within existing scripts based on evaluation results and testing.
4.  **Develop Recommendation Logic**:
    *   [ ] Define the process for generating final recommendations (e.g., selecting top insurers/tiers from comparison reports).
    *   [ ] Implement this logic, potentially as a new script or a simple agent (`src/agents/recommender.py` is currently empty).
    *   [ ] Determine the desired output format for recommendations.
5.  **Plan Integration/Workflow V1**:
    *   [ ] Design a basic workflow to connect the key steps (e.g., Extraction -> Comparison -> Recommendation).
    *   [ ] Consider orchestration methods (script chaining, `crewai`, etc.).
6.  **ML Model Development (Later Phase)**:
    *   [ ] Prepare dataset using extracted requirements and comparison results.
    *   [ ] Train initial models to derive insights.
7.  **Define Future Architecture**:
    *   [ ] Solidify the plan for integrating components and decide on the final architecture (script-based, agent-based, or hybrid) based on refined goals and the performance of the current approach.

## Implementation Progress

| Component                          | Status      | Priority | Notes                                                                                                |
| :--------------------------------- | :---------- | :------- | :--------------------------------------------------------------------------------------------------- |
| Project Structure                  | 100%        | High     | Core structure established.                                                                          |
| Data Collection                    | 60%         | High     | More diverse policies and scenarios needed.                                                          |
| LLM Service (Gemini)               | 100%        | High     | `src/models/llm_service.py` - Centralized Gemini access.                                             |
| Data Generation Scripts            | 100%        | High     | `scripts/data_generation/` - Personalities & Transcripts.                                            |
| Transcript Evaluation Script       | 100%        | High     | `scripts/evaluation/transcript_evaluation/` - Quality gate for transcripts.                          |
| Transcript Parsing Utility         | 100%        | High     | `src/utils/transcript_processing.py` - Includes Pydantic model.                                      |
| Extractor Agent (CrewAI/OpenAI)    | 100%        | High     | `src/agents/extractor.py` - Extracts requirements. Uses OpenAI.                                      |
| Policy Extraction Script           | 100%        | High     | `scripts/extract_policy_tier.py` - Extracts structured policy data. Uses Gemini.                     |
| Policy Comparison Script           | 100%        | High     | `scripts/generate_policy_comparison.py` - Generates insurer-level reports. Uses Gemini.              |
| **PDF Extraction Evaluation**      | **100%**    | **High** | **Script implemented (`eval_pdf_extraction.py`) with `--file_pattern` enhancement. Testing/Refinement pending.** |
| Policy Comparison Evaluation       | Planned     | High     | Design and implement evaluation for `generate_policy_comparison.py`.                                 |
| **Recommender Logic Script**       | **100%**    | **High** | **`scripts/generate_recommendation_report.py` implemented (parser, score, re-rank with transcript context, MD report, efficient overwrite check, improved logging).** |
| **Ground Truth Data**              | **100%**    | **High** | **`data/ground_truth/ground_truth.json` created and refined.**                                       |
| **Embedding Utilities**            | **100%**    | **High** | **`src/embedding/embedding_utils.py` implemented with `EmbeddingMatcher`.**                          |
| **Scenario Rec. Evaluation**       | **100%**    | **High** | **`scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py` implemented, uses embeddings. Testing/Refinement pending.** |
| **Ground Truth Coverage Script**   | **100%**    | **Medium** | **`scripts/generate_ground_truth_coverage.py` added. Functionality/Testing pending.**                |
| **Orchestration Script**           | **100%**    | **High** | **`scripts/orchestrate_scenario_evaluation.py` implemented and debugged. Parallel eval, sequential reports. Final evaluation includes all reports. Added `--only_aggregate` flag.** |
| **Component Integration**          | **20%**     | **Medium** | **Internal Stage 1/2 integration done. Full pipeline orchestration pending.**                        |
| **Frontend Deployment (Netlify)**  | **100%**    | **High** | **`ux-webapp` deployed. Required fixes to `netlify.toml`, `requirements.txt`, and `ux-webapp/package.json` build script for asset syncing.** |
| **Frontend UX Enhancements**       | **100%**    | **Medium** | **Fixed report loading, dynamic dropdowns, requirements/transcript display formats, animation speeds.** |
| **Frontend Landing Page Updates**  | **100%**    | **Medium** | **Fixed mobile dropdown visibility, updated text content, rebranded to "Aegis AI" with custom shield icon.** |
| Testing Framework                  | 20%         | Medium   | Unit tests added for recommender parser/scorer/MD report. More needed.                               |
| ML Models                          | 0%          | Low      | Later phase.                                                                                         |
| Documentation (Memory Bank)        | **100%**    | High     | **Updated core files for Ground Truth feature, Netlify deployment, and recent frontend changes.**    |

## Known Issues

1.  **LLM Accuracy & Consistency**:
    *   Ensuring high accuracy and consistent formatting from LLMs for extraction (policy, requirements) and comparison tasks remains a challenge. Requires ongoing prompt tuning and potentially model updates.
    *   Adherence to complex JSON schemas (e.g., policy extraction) needs careful validation.
2.  **Evaluation Gaps/Refinements**:
    *   PDF extraction evaluation needs testing/validation.
    *   Scenario recommendation evaluation depends on `EmbeddingMatcher` accuracy and ground truth quality; requires ongoing refinement.
    *   Lack of automated evaluation for *comparison report* quality. Manual review is currently required for that step.
3.  **Synthetic Data Limitations**:
    *   Generated transcripts might not fully capture the nuances of real user interactions.
4.  **LLM Constraints**:
    *   API rate limits, costs, and potential output token limits need management. `LLMService` helps mitigate some aspects (retries, central config).
5.  **Lack of Integration**:
    *   Current components are largely standalone scripts. No automated workflow connects them end-to-end. Manual execution is required for each step.
6.  **Extractor Agent Dependency**:
    *   The Extractor Agent relies on OpenAI/CrewAI, separate from the Gemini-based `LLMService` used elsewhere. `EmbeddingMatcher` also uses OpenAI. This adds complexity to configuration and potential cost management across multiple components.
7.  **Orchestrator Evaluation Scope**:
    *   The final evaluation step in the orchestrator now includes results for *all* reports found, not just the current run. Need to be mindful of this when interpreting the `*_all_transcripts_*.json` files.
8.  **Orchestrator Flexibility**:
    *   Added `--only_aggregate` flag to allow running only the final evaluation step.
9.  **Frontend Data Sync**: The `sync-public-assets.cjs` script copies necessary data to `ux-webapp/public` but relies on the build process triggering it for deployment.
10. **Frontend Landing Page Fixes & Rebranding**: Fixed mobile visibility of the demo dropdown, updated various text elements (tagline, helper text, captions), and rebranded the app to "Aegis AI" (titles, copyright, custom shield icon).

## Recent Achievements (Summary - See `activeContext.md` for full detail)

1.  **Core Infrastructure**: Project setup, Memory Bank init, LLM Service (Gemini).
2.  **Data Pipelines**: Scripts for generating personalities, transcripts (with scenarios), evaluating transcripts, parsing transcripts, extracting policy details (PDF to structured JSON), and generating comparison reports.
3.  **Extractor Agent**: Implemented using CrewAI/OpenAI for requirement extraction.
4.  **Recommender Script**: Implemented `scripts/generate_recommendation_report.py` with Stage 1 scoring, Stage 2 LLM re-ranking (updated to use transcript context), and Markdown report generation. Added unit tests.
5.  **Refinements**: Centralized Gemini config, improved policy extraction detail, standardized filenames, refactored comparison script for insurer-level analysis, enhanced evaluation robustness, added file pattern filtering to PDF eval script.
6.  **Orchestration Script**: Implemented and debugged `scripts/orchestrate_scenario_evaluation.py` to automate the end-to-end workflow. Refactored transcript evaluation for parallel processing and report generation for sequential processing (per UUID) to improve reliability. Final evaluation step modified to include all reports found for a scenario. Added `--only_aggregate` flag for flexibility.
7.  **Recommendation Script Efficiency/Logging**: Improved `scripts/generate_recommendation_report.py` to check for existing files before LLM calls and corrected summary logging. Added default values to docstrings.
8.  **Scenario Evaluation Ground Truth Refinement**: Analyzed failing cases for `uncovered_cancellation_reason` scenario and relaxed the ground truth in `data/evaluation/scenario_evaluation/scenario_ground_truth.json` to include additional valid policy tiers (GELS Gold, FWD Business, FWD First), improving evaluation accuracy.
9.  **Ground Truth Evaluation Feature**: Integrated ground truth data (`data/ground_truth/ground_truth.json`), embedding utilities (`src/embedding/embedding_utils.py`), and evaluation scripts (`scripts/generate_ground_truth_coverage.py`, updated `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`) for semantic evaluation of recommendations.
10. **Netlify Frontend Deployment**: Successfully debugged and deployed the `ux-webapp` frontend to Netlify, including configuration changes to `netlify.toml`, `requirements.txt`, and `ux-webapp/package.json` to handle build commands, dependencies, and static asset synchronization.
11. **Frontend Landing Page Updates**: Completed fixes for mobile dropdown visibility, updated text content (tagline, helper text, captions), and rebranded to "Aegis AI" using a custom shield image.
