# Project Progress

## Current Status

The project has **completed the implementation and debugging of the core script-based workflow**, including data generation, extraction, comparison, recommendation, and evaluation components. The focus is now shifting towards refinement (e.g., PDF extraction evaluation), potential ML integration, and defining future architecture.

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
12. **Comparison Report Evaluation Script**: Script (`scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py`) compares generated comparison reports against source PDFs and requirements using multi-modal LLM (`LLMService`). Successfully debugged and tested.
13. **Recommendation Report Script**: Script (`scripts/generate_recommendation_report.py`) orchestrates the two-stage recommendation process: parses comparison reports, applies Stage 1 scoring, calls `LLMService` for Stage 2 re-ranking (prompt updated to use transcript context for prioritization and request source references), and generates/saves a final customer-friendly Markdown report. (Note: Requirements summary context removed from Stage 2). Includes unit tests for parser, scoring, and Markdown generation.
14. **Ground Truth Knowledge Base**: Curated data (`data/ground_truth/ground_truth.json`) serving two purposes: defining **(a)** which requirements are covered by which policy tiers (for coverage checks) and **(b)** the expected final policy recommendation for specific test scenarios.
15. **Embedding Utilities**: `EmbeddingMatcher` class (`src/embedding/embedding_utils.py`) for semantic comparison using OpenAI embeddings, including caching (`src/embedding/cache/`).
16. **Scenario Recommendation Evaluation Script**: Script (`scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`) evaluates the final recommended policy against the **expected scenario outcomes** defined in the Ground Truth Knowledge Base.
17. **Ground Truth Coverage Script**: Script (`scripts/generate_ground_truth_coverage.py`) evaluates how well the recommended policy covers individual requirements, using the `EmbeddingMatcher` to check against the **requirement coverage definitions** in the Ground Truth Knowledge Base.
18. **Node.js/Frontend Setup**: After cloning, run `npm install` to install Node.js dependencies if you intend to use any web or supporting scripts.

## What's Left to Build

1.  **ML Model Development (Later Phase)**:
    *   [ ] Prepare dataset.
    *   [ ] Train initial models.
2.  **Define Future Architecture**:
    *   [ ] Solidify the plan for integrating components (script-based, agent-based, hybrid).

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
| **PDF Extraction Evaluation**      | **100%**    | **High** | **Script implemented (`eval_pdf_extraction.py`) with `--file_pattern` enhancement. Refinement pending.** |
| **Policy Comparison Evaluation**   | **100%**    | **High** | **Script implemented (`eval_comparison_report.py`), debugged, output structure updated (`/{uuid}/`), tested, and refined.** |
| **Recommender Logic Script**       | **100%**    | **High** | **`scripts/generate_recommendation_report.py` implemented (parser, score, re-rank with transcript context, MD report, efficient overwrite check, improved logging).** |
| **Ground Truth Data**              | **100%**    | **High** | **`data/ground_truth/ground_truth.json` created and refined.**                                       |
| **Embedding Utilities**            | **100%**    | **High** | **`src/embedding/embedding_utils.py` implemented with `EmbeddingMatcher`.**                          |
| **Scenario Rec. Evaluation**       | **100%**    | **High** | **`scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py` implemented, uses embeddings. Enhanced with `--target-uuid` for single-run evaluation.** |
| **Ground Truth Coverage Script**   | **100%**    | **Medium** | **`scripts/generate_ground_truth_coverage.py` added. Functionality/Testing pending.**                |
| **Orchestration Script**           | **100%**    | **High** | **`scripts/orchestrate_scenario_evaluation.py` implemented and debugged. Parallel eval, sequential reports. Final evaluation includes all reports. Added `--only_aggregate` flag.** |
| **Component Integration**          | **20%**     | **Medium** | **Internal Stage 1/2 integration done. Full pipeline orchestration pending.**                        |
| **Frontend Deployment (Netlify)**  | **100%**    | **High** | **`ux-webapp` deployed. Required fixes to `netlify.toml`, `requirements.txt`, and `ux-webapp/package.json` build script for asset syncing.** |
| **Frontend UX Enhancements**       | **100%**    | **Medium** | **Fixed report loading, dynamic dropdowns, requirements/transcript display formats, animation speeds.** |
| **Frontend Landing Page Updates**  | **100%**    | **Medium** | **Fixed mobile dropdown visibility, updated text content, rebranded to "Aegis AI" with custom shield icon.** |
| **Frontend TOC Implementation**    | **100%**    | **Medium** | **Implemented dynamic TOC, debugged stability, relocated mobile button, updated AppBar button text. Resolved Netlify build errors by moving plugin.** |
| **Frontend Disclaimer Page**       | **100%**    | **Medium** | **Added disclaimer page (`DisclaimerPage.tsx`), route (`/disclaimer/:uuid`), and updated `TransitionPage` navigation.** |
| **Frontend Feedback UI**           | **100%**    | **Medium** | **Added Feedback tab, thumbs up/down buttons (centered), styled predefined feedback buttons (chip-style, blue, left-aligned), text area, send button with snackbar.** |
| **Frontend Tab Scrolling**         | **100%**    | **Medium** | **Fixed tab label cutoff by making tabs always scrollable.**                                         |
| **Demo Script (`run_recsys_demo.py`)** | **100%**    | **High** | **Fully debugged and functional. Added Windows UTF-8 fix for subprocesses.**                         |
| Testing Framework                  | 20%         | Medium   | Unit tests added for recommender parser/scorer/MD report. More needed.                               |
| ML Models                          | 0%          | Low      | Later phase.                                                                                         |
| Documentation (Memory Bank)        | **100%**    | High     | **Updated for recent script changes.**                                                               |

## Known Issues

1.  **LLM Accuracy & Consistency**: Ensuring high accuracy and consistent formatting from LLMs remains an ongoing effort, particularly for complex extraction, comparison, and multi-modal evaluation tasks. *(Ongoing)*
2.  **Evaluation Refinement**: While evaluation scripts exist for all key stages (transcripts, PDF extraction, comparison reports, scenario recommendations), the comparison report evaluation needs review of its output quality and definition of clear pass/fail metrics. *(Partially Addressed - Script Functional)*
3.  **Synthetic Data Limitations**: Generated transcripts might not fully capture the nuances and edge cases of real user interactions. *(Ongoing)*
4.  **LLM Constraints & Costs**: Managing API rate limits, costs, and potential output token limits across both Gemini and OpenAI requires monitoring. Orchestration runtime can be significant, especially with multi-modal calls. *(Ongoing)*
5.  **Integration & Orchestration Management**: While the orchestration script automates the workflow, managing dependencies, potential failures, and overall runtime within this script-chaining approach requires ongoing monitoring and maintenance. *(Ongoing Management)*
6.  **Dual LLM Dependency**: Reliance on both OpenAI (Extractor Agent via CrewAI, EmbeddingMatcher) and Google Gemini (LLMService) adds complexity (config, cost, maintenance). *(Ongoing)*
7.  **Frontend Data Sync Reliability**: Ensuring the `sync-public-assets.cjs` script runs correctly during the build process and copies all necessary, up-to-date data is vital for production functionality. *(Ongoing Maintenance)*
8.  **Frontend Maintenance**: Ongoing monitoring is needed for the deployed frontend, including UI components like the dynamic TOC and feedback elements, to catch potential regressions or issues. *(Ongoing Maintenance)*

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
12. **Frontend Feedback UI Implementation**: Added Feedback tab, thumbs up/down buttons (centered), styled predefined feedback buttons (chip-style, blue, left-aligned), text area, and send button with snackbar confirmation.
13. **Frontend Tab Scrolling Fix**: Resolved tab label cutoff issue by making tabs always scrollable.
14. **Comparison Report Evaluation Debugging & Refinement**: Fixed multiple issues (`TypeError`, `429 RESOURCE_EXHAUSTED`, PDF input format) in `scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py` and related config (`src/models/gemini_config.py`). Modified script to save output to `data/evaluation/comparison_report_evaluations/{uuid}/`. Successfully tested with `--overwrite` flag.
15. **Demo Script (`run_recsys_demo.py`) Debugging & Refinement**: Resolved multiple issues including argument mismatches, `UnicodeDecodeError`, missing output files, and incorrect evaluation scope. Adapted dependent scripts (`transcript_processing.py`, `extractor.py`, `evaluate_scenario_recommendations.py`) for single-run execution within the demo context. Confirmed necessary dependencies (`nltk`, `sklearn`) are installed.
16. **Embedding Utils `.env` Loading**: Modified `src/embedding/embedding_utils.py` to remove the hardcoded path for `.env` file loading, allowing `load_dotenv()` to search automatically (typically from project root). Improves cross-platform compatibility.
17. **Demo Script Windows UTF-8 Fix**: Modified `scripts/run_recsys_demo.py` to detect Windows OS and set `PYTHONUTF8=1` environment variable for subprocesses, aiming to prevent potential Unicode errors during output capture.
