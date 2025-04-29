# System Patterns

## System Architecture

The project follows a workflow orchestrated by `scripts/orchestrate_scenario_evaluation.py`. This script manages data generation (parallel scenarios), processing (parallel transcript evaluation, sequential parsing/extraction), sequential report generation (per UUID), and final evaluation aggregation. It includes flags like `--skip_transcript_eval` and `--only_aggregate` to control execution flow. A single agent (Extractor) is used within this workflow. The original multi-agent concept is not implemented.

## System Architecture Overview

The system follows a primarily script-driven workflow, orchestrated by `scripts/orchestrate_scenario_evaluation.py` for end-to-end scenario testing. Key process flows include:

*   **Orchestration Flow (`orchestrate_scenario_evaluation.py`):**
    *   1. Generate Transcripts (Parallel Scenarios)
    *   2a. Evaluate Transcripts (Parallel Transcripts, Optional)
    *   2b. Parse Transcripts (Sequential Batch)
    *   2c. Extract Requirements (Sequential Batch)
    *   3. Generate Comparison & Recommendation Reports (Sequential per UUID)
    *   4. Final Scenario Evaluation & Aggregation

*   **Data Generation:**
    *   Inputs: Personalities (`personalities.json`), Coverage Requirements (`coverage_requirements.py`), Scenarios (`scenarios/*.json`).
    *   Process: `generate_transcripts.py` uses inputs and LLMService.
    *   Output: Raw synthetic transcripts (`data/transcripts/raw/synthetic/*.json`).

*   **Transcript Processing & Extraction:**
    *   Input: Raw transcripts.
    *   Processes:
        *   `eval_transcript_main.py` evaluates quality (optional gate).
        *   `transcript_processing.py` parses raw transcripts.
        *   `extractor.py` (CrewAI/OpenAI agent) extracts requirements from processed transcripts.
    *   Outputs: Passed UUIDs (from eval), Processed transcripts (`data/transcripts/processed/*.json`), Extracted requirements (`data/extracted_customer_requirements/*.json`).

*   **Policy Processing (Standalone):**
    *   Input: Raw policy PDFs (`data/policies/raw/*.pdf`).
    *   Process: `extract_policy_tier.py` uses LLMService.
    *   Output: Processed policy JSON (`data/policies/processed/*.json`).

*   **Reporting & Analysis:**
    *   Inputs: Extracted requirements, Processed policies, Processed transcripts, Passed UUIDs (if evaluation run).
    *   Processes:
        *   `generate_policy_comparison.py` compares requirements and policies.
        *   `generate_recommendation_report.py` scores comparisons and generates final recommendation.
    *   Outputs: Comparison reports (`results/{uuid}/*.md`), Final recommendation report (`results/{uuid}/recommendation_report_{uuid}.md`).

*   **Evaluation Components:**
    *   Transcript Evaluation (`eval_transcript_main.py`) -> `data/evaluation/transcript_evaluations/*.json`
    *   PDF Extraction Evaluation (`eval_pdf_extraction.py`) -> `data/evaluation/pdf_extraction_evaluations/*.json`
    *   Comparison Report Evaluation (`eval_comparison_report.py`) -> `data/evaluation/comparison_report_evaluations/*.json`
    *   Scenario Recommendation Evaluation (`evaluate_scenario_recommendations.py`) -> `data/evaluation/scenario_evaluation/results_*.json` (Aggregated by orchestrator to `results_*_all_transcripts_*.json`)
    *   Coverage Ground Truth Evaluation (`generate_ground_truth_coverage.py`) -> `data/evaluation/ground_truth_evaluation/*.json`

*   **Ground Truth & Embeddings:**
    *   `ground_truth.json` is used by `embedding_utils.py`.
    *   `embedding_utils.py` uses OpenAI API and creates cache files.

*   **Frontend (`ux-webapp`):**
    *   React app displaying reports fetched from the `public/` directory.
    *   Includes landing page, disclaimer, report viewer with tabs (Recommendation, Comparison, Requirements, Transcript, Feedback), TOC, etc.

*   **Build Time Sync (`sync-public-assets.cjs`):**
    *   Copies necessary results, requirements, and transcript data to `ux-webapp/public/` for frontend access during the build process.
    *   Generates index files (`index.json`, `transcripts_index.json`) for dynamic loading in the frontend.

## Key Technical Decisions

1.  **Script-Driven Workflow**:
    *   Decision: Implement core logic (data generation, policy extraction, comparison) as standalone Python scripts.
    *   Rationale: Allows for modular development and testing of individual components before full agent integration. Enables batch processing.
    *   Implementation: Various scripts in `scripts/` directory (e.g., `generate_transcripts.py`, `extract_policy_tier.py`, `generate_policy_comparison.py`).

2.  **Single Agent Implementation (Extractor)**:
    *   Decision: Implement the Extractor using the `crewai` framework with OpenAI.
    *   Rationale: Leverages existing agent framework for a specific, well-defined task (requirement extraction). Allows experimentation with agent-based approaches.
    *   Implementation: `src/agents/extractor.py`.

3.  **Centralized LLM Service (Gemini)**:
    *   Decision: Create a reusable service (`LLMService`) for interacting with Google Gemini.
    *   Rationale: Standardizes API calls, configuration, error handling, and retry logic for most LLM tasks.
    *   Implementation: `src/models/llm_service.py` used by most scripts. Note: Extractor agent uses OpenAI directly via `crewai`.

4.  **Emphasis on Evaluation**:
    *   Decision: Integrate evaluation steps at key points in the workflow.
    *   Rationale: Ensures data quality and component performance before proceeding to downstream tasks. Provides metrics for improvement.
    *   Implementation: Dedicated evaluation scripts for transcripts, PDF extraction, and scenario recommendations. Planned evaluation for comparison reports.

5.  **Structured Knowledge Representation**:
    *   Decision: Transform unstructured policy documents and conversations into structured data using Pydantic models.
    *   Rationale: Enables systematic comparison, analysis, and validation.
    *   Implementation: Pydantic models (`TravelInsuranceRequirement`, policy extraction models) for validated JSON outputs.

6.  **Semantic Evaluation (Ground Truth)**:
    *   Decision: Use semantic matching via embeddings (OpenAI) to compare system outputs against curated ground truth data.
    *   Rationale: Provides a more robust evaluation of recommendation accuracy beyond simple string matching, understanding the meaning behind requirements.
    *   Implementation: `src/embedding/embedding_utils.py` (handles embedding generation, caching, and matching logic), `data/ground_truth/ground_truth.json` (curated data). This includes: a) comparing the final recommended policy against expected outcomes for specific scenarios (`evaluate_scenario_recommendations.py`), and b) checking if individual requirements are covered by the recommended policy using the ground truth as a knowledge base (`generate_ground_truth_coverage.py`).

7.  **Hybrid Approach (Planned)**:
    *   Decision: Combine LLM-based reasoning with traditional ML (Future Goal).
    *   Rationale: Leverages strengths of both approaches (LLM for reasoning, ML for pattern recognition).
    *   Implementation: LLMs used in scripts/agent. Supervised ML for insights is planned for a later phase.

## Design Patterns

1.  **Pipeline Pattern**:
    *   Sequential processing of data through specialized scripts/stages (e.g., Generation -> Evaluation -> Parsing -> Extraction).
    *   Each stage transforms or enriches the data.
    *   Implementation: Current script execution order forms pipelines.

2.  **Agent Pattern**:
    *   Used for the Extractor Agent (`src/agents/extractor.py`).
    *   A specialized entity with specific responsibilities.
    *   Implementation: Managed by `crewai` framework.

3.  **Service Layer Pattern**:
    *   The `LLMService` acts as a service layer abstracting direct Gemini API calls.
    *   Provides a consistent interface for LLM interactions.
    *   Implementation: `src/models/llm_service.py`.

4.  **Composite Pattern**:
    *   Complex customer requirements and policy details composed of simpler components.
    *   Hierarchical organization of data.
    *   Implementation: Nested JSON structures validated by Pydantic models.

## Component Relationships

### LLM Service (`src/models/llm_service.py`)
- **Purpose**: Centralized interface for Google Gemini API calls.
- **Inputs**: Prompts, parameters (model, tokens, etc.), content (text/multi-modal).
- **Outputs**: Generated content (text, structured JSON).
- **Dependencies**: Google Gemini API, `src/models/gemini_config.py`.
- **Consumers**: `scripts/extract_policy_tier.py`, `scripts/generate_policy_comparison.py`, `scripts/data_generation/*`, `scripts/evaluation/*`.

### Transcript Generation (`scripts/data_generation/generate_transcripts.py`)
- **Purpose**: Generates synthetic transcripts based on scenarios, requirements, and personalities.
- **Inputs**: `data/scenarios/*.json`, `data/coverage_requirements/coverage_requirements.py`, `data/transcripts/personalities.json`.
- **Outputs**: Raw transcript JSON files (`data/transcripts/raw/synthetic/*.json`).
- **Dependencies**: `LLMService`.

### Transcript Parsing (`src/utils/transcript_processing.py`)
- **Purpose**: Parses evaluated raw transcripts into a simpler list format. Defines `TravelInsuranceRequirement` model.
- **Inputs**: Raw transcript JSON (`data/transcripts/raw/synthetic/*.json`).
- **Outputs**: Processed transcript JSON (`data/transcripts/processed/*.json`).
- **Dependencies**: None (when run for parsing).

### Extractor Agent (`src/agents/extractor.py`)
- **Purpose**: Extracts structured customer requirements from processed transcripts.
- **Inputs**: Processed transcript JSON (`data/transcripts/processed/*.json`).
- **Outputs**: Extracted requirements JSON (`data/extracted_customer_requirements/*.json`) conforming to `TravelInsuranceRequirement`.
- **Dependencies**: `crewai` framework, OpenAI API (via `.env`), `src/utils/transcript_processing.py` (for model definition).

### Policy Extraction Script (`scripts/extract_policy_tier.py`)
- **Purpose**: Extracts structured policy details from raw PDFs.
- **Inputs**: Raw policy PDFs (`data/policies/raw/*.pdf`).
- **Outputs**: Processed policy JSON (`data/policies/processed/*.json`) with detailed structure (base/conditional limits, source details).
- **Dependencies**: `LLMService`, Pydantic models defined within the script.

### Policy Comparison Script (`scripts/generate_policy_comparison.py`)
- **Purpose**: Generates Markdown reports comparing extracted requirements against processed policies at the insurer level.
- **Inputs**: Extracted requirements JSON (`data/extracted_customer_requirements/*.json`), Processed policy JSON (`data/policies/processed/*.json`), `data/policies/pricing_tiers/tier_rankings.py`.
- **Outputs**: Markdown comparison reports (`results/{uuid}/*.md`).
- **Dependencies**: `LLMService`, Extractor Agent output, Policy Extraction Script output.

### Recommendation Report Script (`scripts/generate_recommendation_report.py`)
- **Purpose**: Parses comparison reports, performs Stage 1 scoring, calls LLM for Stage 2 re-ranking (using transcript context), generates a final Markdown report, and saves it. Checks for existing report and `--overwrite` flag before processing to avoid redundant work.
- **Inputs**:
    - Markdown comparison reports (`results/{uuid}/*.md`).
    - Processed transcript JSON (`data/transcripts/processed/parsed_transcript_*_{uuid}.json`).
    - Command-line arguments (`--customer_id`, `--top_n`, `--overwrite`).
- **Outputs**: Final recommendation Markdown report (`results/{uuid}/recommendation_report_{uuid}.md`), potentially skipped if exists and `overwrite=False`.
- **Dependencies**: `LLMService`, Comparison Report Script output, Processed Transcript data, Pydantic (`FinalRecommendation` model).

### ML Models (Future)
- **Purpose**: Uncover insights from data.
- **Inputs**: Extracted requirements JSON, potentially comparison results or final recommendations.
- **Outputs**: Insights on feature importance, product positioning.
- **Dependencies**: Extractor Agent output, potentially other data sources.

### Ground Truth Data (`data/ground_truth/ground_truth.json`)
- **Purpose**: Stores curated ground truth data defining both **(a)** which specific requirements are covered by which policy tiers (acting as a knowledge base for coverage checks) and **(b)** the expected final policy recommendations for specific test scenarios.
- **Inputs**: Manually curated based on scenario definitions and policy analysis.
- **Outputs**: Consumed by evaluation scripts.
- **Dependencies**: Scenario definitions (`data/scenarios/`).

### Embedding Utilities (`src/embedding/embedding_utils.py`)
- **Purpose**: Provides the `EmbeddingMatcher` class for semantic comparison using OpenAI embeddings, primarily against the requirement coverage definitions in the ground truth data.
- **Inputs**: Query text (e.g., a customer requirement), `ground_truth.json` path.
- **Outputs**: Best matching ground truth key, similarity score, policy values (list of policies covering the requirement). Generates/uses cache files (`src/embedding/cache/*.pkl`).
- **Dependencies**: OpenAI API (via `.env`), `ground_truth.json`, NLTK (for preprocessing).
- **Consumers**: `scripts/generate_ground_truth_coverage.py`, `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`.

### Evaluation Components

#### Transcript Evaluation
-   **Purpose**: To evaluate the quality, relevance, and coverage of synthetically generated raw transcripts (`data/transcripts/raw/synthetic/*.json`) against the intended scenario and coverage requirements before they are used for requirement extraction. Acts as a quality gate.
-   **Scripts**: Primarily `scripts/evaluation/transcript_evaluation/eval_transcript_main.py`, which orchestrates helpers in the same directory (`eval_transcript_parser.py`, `eval_transcript_prompts.py`, `eval_transcript_gemini.py`, `eval_transcript_results.py`, `eval_transcript_utils.py`).
-   **Inputs**:
    -   Raw Transcript JSON: `data/transcripts/raw/synthetic/transcript_{scenario}_{uuid}.json`.
    -   Coverage Requirements: `data/coverage_requirements/coverage_requirements.py`.
    -   Scenario Definitions: `data/scenarios/{scenario}.json` (used to provide context).
-   **Workflow**:
    1.  Parses the raw transcript JSON.
    2.  Extracts the scenario name from the transcript filename or content.
    3.  Loads the corresponding scenario definition and coverage requirements.
    4.  Constructs a detailed prompt (`eval_transcript_prompts.py`) instructing the LLM to assess the transcript based on criteria like requirement coverage, scenario relevance, realism, and conversational flow.
    5.  Calls the LLM (`eval_transcript_gemini.py` via `LLMService`) to perform the evaluation.
    6.  The LLM is expected to return a structured JSON response (defined by Pydantic models like `TranscriptEvaluation`, `EvaluationSummary`, `CoverageEvaluation`).
    7.  Saves the structured evaluation results to `data/evaluation/transcript_evaluations/transcript_eval_{scenario}_{uuid}.json`.
-   **Evaluation Logic**: Relies on the LLM's assessment based on the provided prompt and criteria. The structured output includes scores and justifications for different aspects of the transcript quality. A simple "PASS"/"FAIL" might be inferred based on thresholds (though this threshold logic isn't explicitly in the script currently, the detailed JSON output allows for it).
-   **Dependencies**: `LLMService`, Scenario Definitions, Coverage Requirements.

#### PDF Extraction Evaluation
-   **Purpose**: To evaluate the accuracy and completeness of the structured policy data extracted by `scripts/extract_policy_tier.py` by comparing the processed JSON (`data/policies/processed/*.json`) against the original source PDF (`data/policies/raw/*.pdf`).
-   **Script**: `scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py`
-   **Inputs**:
    -   Processed Policy JSON: `data/policies/processed/{insurer}_{tier}.json`. Can be filtered using `--file_pattern`.
    -   Raw Policy PDF: `data/policies/raw/{insurer}_{tier}.pdf` (path inferred from JSON filename).
-   **Workflow**:
    1.  Iterates through specified processed policy JSON files.
    2.  For each JSON, finds the corresponding raw PDF.
    3.  Constructs multi-modal prompts for the LLM, asking it to perform two-way verification:
        *   Verify JSON content against the PDF.
        *   Verify PDF content against the JSON.
    4.  Calls the LLM (`LLMService`, using a multi-modal model like Gemini Pro Vision) with both the text prompt and the PDF image/content.
    5.  The LLM returns a structured JSON evaluation result assessing consistency, accuracy, and completeness.
    6.  Saves the evaluation results to `data/evaluation/pdf_extraction_evaluations/eval_{insurer}_{tier}.json`.
-   **Evaluation Logic**: Relies on the multi-modal LLM's ability to compare the structured text data (JSON) with the visual and textual content of the PDF document based on the verification prompts.
-   **Dependencies**: `LLMService` (multi-modal model), Processed Policy JSON, Raw Policy PDF.

#### Coverage Ground Truth Evaluation
-   **Purpose**: To evaluate how well the recommended policy covers the customer's individual requirements, atomizing compound requirements and enhancing based on activities.
-   **Script**: `scripts/generate_ground_truth_coverage.py`
-   **Inputs**: Extracted Customer Requirements (`data/extracted_customer_requirements/`), Recommendation Reports (`results/{uuid}/`), Ground Truth Knowledge Base (`data/ground_truth/ground_truth.json` via `EmbeddingMatcher`).
-   **Workflow**: Extracts requirements and recommended policy, atomizes requirements, uses `EmbeddingMatcher` to check coverage of each requirement against the ground truth knowledge base for the recommended policy.
-   **Evaluation Logic**: Determines coverage status (COVERED, NOT_COVERED, NOT_EXIST) for each requirement based on the ground truth lookup. Calculates overall 'Total Coverage' and 'Valid Coverage' metrics.
-   **Dependencies**: Recommendation Reports, Extracted Customer Requirements, `src/embedding/embedding_utils.py`, `data/ground_truth/ground_truth.json`.

#### Scenario Recommendation Evaluation
-   **Purpose**: To evaluate the final recommendation generated by `scripts/generate_recommendation_report.py` against a predefined ground truth for specific test scenarios. This verifies if the system recommends an appropriate policy given the scenario's constraints and expected outcomes. Can evaluate all UUIDs for a scenario or a single `--target-uuid`.
-   **Script**: `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`
-   **Inputs**:
    -   Ground Truth: `data/evaluation/scenario_evaluation/scenario_ground_truth.json` (defines `status` like `"full_cover_available"` or `"partial_cover_only"` and a list of `expected_policies` with `insurer`, `tier`, `justification` for each scenario key).
    -   Recommendation Reports: `results/{uuid}/recommendation_report_*.md` (output from `generate_recommendation_report.py`).
    -   Transcripts: `data/transcripts/raw/synthetic/transcript_{scenario}_{uuid}.json` (used only when evaluating all scenarios or determining scenario for a target UUID).
    -   Optional `--target-uuid` argument to focus on a single run.
-   **Workflow**:
    1.  Identifies target UUID(s) either via `--target-uuid` argument, or via the `--scenario` argument (filtering transcripts), or by iterating through all `results/{uuid}` directories and finding the corresponding scenario from transcript filenames (if neither target UUID nor scenario is specified).
    2.  Loads the ground truth entry for the relevant scenario(s).
    3.  For each targeted UUID, finds the corresponding recommendation report (`recommendation_report_*.md`).
    4.  Parses the recommended policy from the report.
    5.  Compares the parsed policy against the ground truth.
    6.  Outputs results to console and optionally to a JSON file (defaulting to `data/evaluation/scenario_evaluation/results_{scenario}_{timestamp}.json`).
-   **Parsing Logic & Pattern Enforcement**:
    -   The script uses a specific regular expression (`r"\*\*([a-zA-Z\s]+)\s*-\s*([a-zA-Z\s!]+)\*\*"`) within the `parse_recommendation_report` function to extract the recommended policy.
    -   This regex strictly expects the format `**INSURER - Tier**`. It captures the insurer name *before* the hyphen and the tier name *after* it.
    -   This parsing is reliable because the report generation script (`scripts/generate_recommendation_report.py`) explicitly creates this exact pattern in the final report using the line: `f"\n**{stage2_recommendation.recommended_insurer.upper()} - {stage2_recommendation.recommended_tier}**\n"`.
-   **Evaluation Logic (`evaluate_recommendation` function)**:
    1.  Takes the parsed recommended insurer/tier (converted to lowercase) and the ground truth entry for the scenario.
    2.  Checks the ground truth `status` (`"full_cover_available"` or `"partial_cover_only"`).
    3.  Compares the recommended policy against each entry in the ground truth's `expected_policies` list.
    4.  Assigns a result based on the match and the status:
        -   `status="full_cover_available"` & Match -> `"PASS"`
        -   `status="full_cover_available"` & No Match -> `"FAIL"`
        -   `status="partial_cover_only"` & Match -> `"PASS (Partial Cover)"` (Recommended an acceptable partial solution)
        -   `status="partial_cover_only"` & No Match -> `"FAIL (Partial)"` (Failed to recommend even an acceptable partial solution)
-   **Dependencies**: `data/ground_truth/ground_truth.json`, Recommendation Reports, Raw Transcripts (for scenario mapping), `src/embedding/embedding_utils.py`.

## Data Flow Summary

1.  **Ground Truth Embedding (Prep):** `EmbeddingUtil` generates and caches embeddings for ground truth keys using the OpenAI Embedding API.
2.  **Transcript Generation:** `GenT` script uses `LLM_Gemini` to create raw transcripts, saved to `data/transcripts/raw/synthetic/`.
3.  **Transcript Evaluation:** `EvalT` script uses `LLM_Gemini` to evaluate raw transcripts. Results saved to `data/evaluation/transcript_evaluations/`.
4.  **Transcript Processing (if Eval passes):**
    *   `ParseT` script parses raw transcript JSON, saving to `data/transcripts/processed/`.
    *   `Extractor` agent uses `LLM_OpenAI` (via CrewAI) to extract requirements from processed transcripts, saving to `data/extracted_customer_requirements/`.
5.  **Policy Processing (Independent Path):**
    *   `ExtractP` script uses `LLM_Gemini` to extract details from policy PDFs, saving to `data/policies/processed/`.
    *   `EvalPDF` script uses `LLM_Gemini` (multi-modal) to evaluate the extracted policy JSON against the source PDF, saving results to `data/evaluation/pdf_extraction_evaluations/`.
6.  **Comparison Report Generation:** `CompareP` script uses `LLM_Gemini`, extracted requirements, and processed policies to generate comparison reports, saved to `results/{uuid}/`.
7.  **Comparison Report Evaluation:** `EvalCompare` script uses `LLM_Gemini` (multi-modal) to evaluate comparison reports against source PDFs and requirements, saving results to `data/evaluation/comparison_report_evaluations/`.
8.  **Recommendation Generation:**
    *   `RecommendR` script parses comparison reports and processed transcripts.
    *   It performs Stage 1 scoring.
    *   It uses `LLM_Gemini` for Stage 2 re-ranking (using transcript context).
    *   It generates the final Markdown report, saved to `results/{uuid}/`.
9.  **Scenario Evaluation:** `ScenarioEval` script reads the final recommendation report and the `GroundTruth` data (expected policies), potentially uses `EmbeddingUtil` for matching, and outputs a PASS/FAIL result.
10. **Coverage Evaluation (Implicit):** Although not shown as a separate step in the original sequence diagram, `generate_ground_truth_coverage.py` would typically run after step 8, using the final recommendation, extracted requirements, `EmbeddingUtil`, and `GroundTruth` to produce its evaluation JSON files.

## Error Handling and Resilience

1.  **Input Validation**:
    *   Scripts often validate input paths and file formats.
    *   Pydantic models enforce schema validation for structured JSON outputs (Extractor, Policy Extraction).
    *   `LLMService` includes robustness checks for JSON parsing.

2.  **Fallback Mechanisms**:
    *   Some scripts include basic fallbacks (e.g., saving raw text if JSON parsing fails during transcript generation).
    *   `LLMService` implements retry logic for API calls.

3.  **Logging**:
    *   Some scripts incorporate logging for debugging (e.g., transcript generation prompt).

4.  **Evaluation Gates**:
    *   Transcript evaluation acts as a quality gate before extraction.
    *   Planned evaluations will add further checks.
