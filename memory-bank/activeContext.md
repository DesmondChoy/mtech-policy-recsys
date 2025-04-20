# Active Context

## Current Work Focus

The project has moved beyond initial setup and is focused on refining the existing script-based pipelines and planning next steps. The current focus is on:

1.  **Memory Bank Update**: Aligning all Memory Bank documents (`projectbrief.md`, `productContext.md`, `systemPatterns.md`, `techContext.md`, `progress.md`, `activeContext.md`) with the actual codebase and current workflow reality.
2.  **Evaluation Framework Development**: **Testing and refining** the implemented PDF extraction evaluation (`eval_pdf_extraction.py`) and **planning/designing** the evaluation mechanism for comparison reports (`generate_policy_comparison.py`).
3.  **Script Refinement**: Improving existing scripts based on testing and initial results (e.g., prompt engineering, error handling).
4.  **Next Phase Planning**: Defining the implementation strategy for recommendation logic and potential integration of components.

## Recent Changes

1. **Project Initialization**:
   - Created project repository
   - Established basic directory structure
   - Added initial README.md with project overview

2. **Data Collection**:
   - Added raw insurance policy PDFs to data/policies/raw/
   - Created synthetic conversation transcripts in data/transcripts/raw/synthetic/
   - Processed some policy documents to text format in data/policies/processed/

3. **Memory Bank Creation**:
   - Initialized memory bank with core documentation files
   - Created projectbrief.md with project overview and goals
   - Added additional context files (productContext.md, systemPatterns.md, techContext.md)

4. **Coverage Requirements Definition**:
   - Created standardized coverage requirements dictionary in data/coverage_requirements/
   - Defined five critical coverage types: trip cancellation, medical expenses, emergency evacuation, baggage loss/delay, and travel delay
   - Added utility functions for accessing coverage requirements
   - Created example usage script to demonstrate implementation

5. **LLM Service Implementation & Fixes**:
   - Created a reusable LLM service using Google Gemini
   - Implemented configuration settings in src/models/gemini_config.py
   - Developed comprehensive service class in src/models/llm_service.py
   - Added support for content generation, structured output, streaming, and batch operations
   - Created a tutorial script with examples in tutorials/llm_service_tutorial.py
   - Updated requirements.txt with necessary dependencies
   - Fixed issues related to safety settings and deprecated types (Commit 260d7af)

6. **Transcript Evaluation System**:
   - Refactored the evaluation script into a modular system with clear separation of concerns
   - Organized into specialized modules with the `eval_transcript` prefix:
     - `prompts/eval_transcript_prompts.py` - Prompt templates and formatting
     - `processors/eval_transcript_parser.py` - Transcript parsing and processing
     - `processors/eval_transcript_results.py` - Results formatting and saving
     - `evaluators/eval_transcript_gemini.py` - Google Gemini integration
     - `utils/eval_transcript_utils.py` - Helper functions
   - Created a new main entry point `eval_transcript_main.py`
   - Added comprehensive documentation in README.md

7. **Transcript Evaluation Enhancement**:
   - Implemented schema-based JSON responses using Pydantic models in the Gemini evaluator
   - Created structured models for evaluation responses:
     - `CoverageEvaluation` for individual coverage evaluations
     - `EvaluationSummary` for the evaluation summary
     - `TranscriptEvaluation` as the top-level model
   - Updated the Gemini model to use the available "gemini-2.0-flash" model
   - Added fallback mechanism for handling responses without parsed attributes
   - Enhanced documentation with detailed explanation of the schema-based approach
   - Improved reliability and reduced JSON parsing errors

8. **Extractor Agent Implementation**:
   - Implemented the Extractor Agent using `crewai` framework (`src/agents/extractor.py`).
   - Defined agent role, goal, backstory, and task for extracting requirements from transcripts.
   - Utilizes the `TravelInsuranceRequirement` Pydantic model for structured JSON output.
   - Enriched the `TravelInsuranceRequirement` model (`src/utils/transcript_processing.py`) with `TravelerDetail` sub-model and `Field` descriptions (Commits a80c230, 8083da9).
   - Created a command-line runner script (`src/web/app.py`) to execute the extraction process, taking a transcript path as input and saving results to `data/extracted_customer_requirements/` (Commit 28479a4).
   - Added `crewai` to dependencies.

9. **Workflow Documentation Update**:
   - Updated `README.md` and `memory-bank/systemPatterns.md` to accurately reflect the current workflow: Evaluation (`eval_transcript_main.py`) -> Parsing (potentially `transcript_processing.py`) -> Extraction (`src/agents/extractor.py`). This replaces previous references to the notebook prototype (`extractor_prototype.ipynb`) with the actual agent implementation.

10. **Policy Extraction Script**:
    - Created `scripts/extract_policy_tier.py` to automate the extraction of structured policy information from PDFs using the Gemini API (`gemini-2.5-pro-exp-03-25`).
    - This script replaces the previous manual/notebook-based PDF-to-text conversion.
    - Includes Pydantic validation, API retries, and usage documentation.
    - Updated `requirements.txt` and fixed an unrelated linting error in `notebooks/agent_development/extractor/extractor_prototype.ipynb`.

11. **Extractor Agent Script Enhancement**:
    - Refactored `src/agents/extractor.py` to align with the logic prototyped in the notebook.
    - Implemented command-line argument parsing to accept the input transcript JSON path.
    - Configured the agent to use OpenAI (via `crewai` and `.env` variables: `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`).
    - Added logic to dynamically name the output file based on the input transcript (e.g., `parsed_transcript_01_requirements.json`).
    - Ensured output is saved correctly to the `data/extracted_customer_requirements/` directory.
    - Fixed JSON serialization error by converting the Pydantic model output to a dictionary using `.model_dump()` before saving.

12. **Personality Data Generation Script**:
    - Created `scripts/data_generation/generate_personalities.py` to generate a list of 10 common customer service personality types using Gemini (`gemini-2.5-pro-exp-03-25`).
    - The script uses Pydantic for validation and saves the output to `data/transcripts/personalities.json`.
    - Added documentation (docstring) to the script explaining its purpose and usage.

13. **Transcript Generation Script**:
    - Created `scripts/data_generation/generate_transcripts.py` to automate the generation of synthetic transcripts using Gemini (`gemini-2.5-pro-exp-03-25`).
    - The script uses `data/transcripts/personalities.json` and `data/coverage_requirements/coverage_requirements.py` as inputs.
    - It includes command-line arguments (`-n`) to specify the number of transcripts to generate.
    - The output is saved as structured JSON (list of speaker turns) in `data/transcripts/raw/synthetic/` with timestamped filenames (`transcript_{personality}_{YYYYMMDD_HHMMSS}.json`).
    - Includes parsing logic and fallback for raw text saving if parsing fails.

14. **Transcript Processing Enhancements (`src/utils/transcript_processing.py`)**:
    - Modified `parse_transcript` function to handle both `.txt` (original format) and the new nested `.json` format (from `generate_transcripts.py`). It now extracts the relevant `transcript` list from JSON files.
    - Updated the `main` function to perform batch processing: it iterates through all `.txt` and `.json` files in `data/transcripts/raw/synthetic/` and saves the parsed output (JSON list) to `data/transcripts/processed/` with a `parsed_` prefix.

15. **Extractor Agent Batch Processing & Filename Update (`src/agents/extractor.py`)**:
    - Modified the `main` function to perform batch processing: it iterates through all `.json` files in the input directory (defaulting to `data/transcripts/processed/`) and runs the extractor agent on each.
    - Changed the output filename format saved to `data/extracted_customer_requirements/` to `requirements_{original_name_part}.json` (e.g., `requirements_the_anxious_inquirer_20250403_152253.json`).
    - Added a comprehensive docstring explaining the script's purpose, usage, I/O, dependencies, and arguments.

16. **Transcript Evaluation Parser Update**:
    - Modified `scripts/evaluation/processors/eval_transcript_parser.py` to exclusively handle JSON-formatted raw transcripts (output from `generate_transcripts.py`). Removed support for `.txt` format.
    - Updated `find_transcript_files` to search only for `.json` files.
    - Updated `parse_transcript` to load JSON and extract the conversation list from the `"transcript"` key.
    - Updated the docstring and argument help text in `scripts/evaluation/eval_transcript_main.py` to reflect the change to JSON-only input.

17. **Coverage Requirements & Transcript Generation Update**:
    - Modified `data/coverage_requirements/coverage_requirements.py`:
        - Renamed/removed existing coverage keys to: `medical_coverage`, `trip_cancellation`, `travel_delays`, `lost_damaged_luggage`.
        - Added new coverage keys: `sports_adventure`, `war_cover` with detailed content.
        - Retained `customer_context_options` dictionary and helper functions.
    - Modified `scripts/data_generation/generate_transcripts.py`:
        - Imported `get_customer_context_options`.
        - Updated prompt template to include a placeholder for context options.
        - Added logic to load and format `customer_context_options` for inclusion in the final prompt.

18. **Transcript Generation Prompt Refinement (`scripts/data_generation/generate_transcripts.py`)**:
    - Iteratively refined the `PROMPT_TEMPLATE` to improve coverage of requirements and context points in generated transcripts.
    - Clarified instructions regarding agent vs. customer initiation of topics (agent probes context, customer raises specific coverage needs).
    - Updated section headers for clarity (e.g., `# Required Customer Context Points`).
    - Merged `# Context and Guidelines`, `# Requirements for Transcript`, and `# Pre-Output Check` into a single `# Transcript Generation Guidelines and Requirements` section for better structure and reduced redundancy.

19. **Transcript Generation Debugging & Enhancement**:
    - Added logging to `scripts/data_generation/generate_transcripts.py` to print the full prompt used for generation.
    - Added logging to print the raw text response from the LLM before parsing, aiding in debugging truncation issues.
    - Identified potential transcript truncation due to default LLM `max_output_tokens` limit.
    - Modified `src/models/llm_service.py` to accept an optional `max_output_tokens` parameter in `generate_content`.
    - Updated the call in `scripts/data_generation/generate_transcripts.py` to pass `max_output_tokens=10000` to potentially resolve truncation.

20. **Gemini Configuration Centralization & Refactoring**:
    - Updated `src/models/gemini_config.py` to set the default model to `gemini-2.5-pro-exp-03-25` and default `max_output_tokens` to `10000`.
    - Enhanced `src/models/llm_service.py` to support multi-modal `contents` input in `generate_content`.
    - Refactored several scripts (`scripts/extract_policy_tier.py`, `scripts/evaluation/evaluators/eval_transcript_gemini.py`, `scripts/data_generation/generate_personalities.py`) to use the centralized `LLMService` instead of direct `google.generativeai` calls, leveraging the central configuration and retry logic.
    - Removed redundant `max_output_tokens` override from `scripts/data_generation/generate_transcripts.py` as it now matches the default.
    - Updated Memory Bank documentation (`techContext.md`, `activeContext.md`) to reflect these changes.

21. **Policy Comparison Report Script**:
    - Created `scripts/generate_policy_comparison.py` to generate Markdown reports comparing customer requirements (from extracted JSON) against multiple processed policy JSON files.
    - Uses the centralized `LLMService` (`gemini-2.5-pro-exp-03-25`) and processes policies asynchronously in batches.
    - Saves reports to `results/{customer_id}_{timestamp}/`.
    - Fixed initial `KeyError` related to prompt formatting.
    - Added customer summary and description to the report output.

22. **Policy Extraction Refinement (`scripts/extract_policy_tier.py`)**:
    - Updated Pydantic models (`CoverageDetail`, added `SourceDetail`, `ConditionalLimit`) to support a more granular extraction structure.
    - Modified the `PROMPT_TEMPLATE` to instruct the LLM to:
        - Consolidate information for a single conceptual benefit into one `coverage` object.
        - Extract standard limits into `base_limits`.
        - Extract conditional limits (e.g., for add-ons) into an optional `conditional_limits` list, including the condition and source.
        - Extract specific detail snippets and their corresponding source locations into a `source_specific_details` list.
    - Updated prompt examples to reflect the new structure.

23. **Transcript Generation Scenario Support**:
    - Enhanced `scripts/data_generation/generate_transcripts.py` to support scenario-based transcript generation.
    - Created a new directory structure (`data/scenarios/`) to store scenario definitions.
    - Implemented a JSON-based scenario format with fields for scenario name, description, additional requirements, and prompt instructions.
    - Created four scenario files for testing specific coverage types:
      - `uncovered_cancellation_reason.json`: Tests coverage for trip cancellation due to personal family events.
      - `pet_care_coverage.json`: Tests coverage for pet accommodation costs during travel delays.
      - `golf_coverage.json`: Tests comprehensive golf-related coverage.
      - `public_transport_double_cover.json`: Tests doubled accidental death coverage on public transport.
    - Added a new command-line argument (`--scenario` or `-s`) to specify which scenario to use.
    - Modified the prompt template to include scenario-specific requirements and instructions.
    - Updated the output JSON to include scenario information.
    - Changed the output filename format to `transcript_{scenario_name_or_no_scenario}_{customer_id}.json` (using "no_scenario" if no scenario is specified, and replacing the timestamp with a UUID).
    - Updated script documentation to explain the new feature.

24. **Transcript Evaluation Scenario Handling & Refactoring**:
    - Updated `scripts/data_generation/generate_transcripts.py` to always include a `"scenario": null` key in the output JSON when no scenario is specified, ensuring consistent file structure.
    - Refactored the transcript evaluation scripts:
        - Moved all related Python files (`eval_transcript_main.py`, `eval_transcript_gemini.py`, `eval_transcript_parser.py`, `eval_transcript_prompts.py`, `eval_transcript_results.py`, `eval_transcript_utils.py`) into a single flat directory: `scripts/evaluation/transcript_evaluation/`.
        - Updated import statements within these files to use relative imports.
        - Deleted the old `scripts/evaluation/evaluators/`, `processors/`, `prompts/`, and `utils/` subdirectories.
    - Enhanced the evaluation system to handle scenario-based transcripts:
        - Modified `eval_transcript_parser.py` to extract the scenario name from the transcript JSON.
        - Modified `eval_transcript_prompts.py` to include scenario-specific requirements in the evaluation prompt.
        - Modified `eval_transcript_main.py` to load scenario requirements and pass them to the prompt constructor.
    - Improved JSON parsing robustness in `src/models/llm_service.py` (`generate_structured_content` method) to handle markdown code blocks and attempt to fix common formatting errors (like missing commas) before parsing.
    - Updated `README.md` with the new evaluation script location and usage instructions.

25. **Filename Standardization for Processed/Extracted Files**:
    - Modified `src/utils/transcript_processing.py` to generate output files in `data/transcripts/processed/` with the format `parsed_transcript_{scenario_name}_{uuid}.json`, extracting the scenario and UUID from the raw input filename.
    - Confirmed that `src/agents/extractor.py` correctly parses this new input format and generates output files in `data/extracted_customer_requirements/` with the format `requirements_{scenario_name}_{uuid}.json`.
    - Updated `memory-bank/systemPatterns.md` and `memory-bank/techContext.md` to reflect these standardized filename formats.

26. **Insurer-Level Policy Comparison Refactoring (`scripts/generate_policy_comparison.py`)**:
    - Refactored the script to perform insurer-level analysis instead of tier-level.
    - Updated input handling to accept `--customer_id` (UUID) and dynamically find requirements and policy files.
    - Implemented logic to group policies by insurer and use `tier_rankings.py`.
    - Created a new detailed prompt (`PROMPT_TEMPLATE_INSURER`) instructing the LLM to:
        - Select the single best tier per insurer using holistic analysis and price tie-breaking.
        - Provide justification.
        - Perform a detailed requirement-by-requirement analysis for the chosen tier, including granular source details.
        - Include a summary of strengths and weaknesses.
    - Updated output handling to save reports to `results/{uuid}/policy_comparison_report_{insurer}_{uuid}.md`.
    - Incorporated asynchronous processing for insurers.
    - Fixed `KeyError` issues related to prompt formatting placeholders by escaping them (`{{Requirement Name}}`, `{{Recommended Tier Name}}`).
27. **PDF Extraction Evaluation Script**:
    - Created `scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py` to compare processed policy JSON against the source PDF using a multi-modal LLM (`LLMService`).
    - Implements two-way verification (JSON vs. PDF, PDF vs. JSON).
    - Renamed directory and script from `policy_extraction_evaluation` to `pdf_extraction_evaluation`.
    - Updated associated plan document (`memory-bank/major_changes/pdf_to_json_eval.md`).
28. **Recommendation Report Script Revision (Hybrid Approach)**:
    - Updated `scripts/generate_recommendation_report.py` based on revised plan (`memory-bank/major_changes/recommender_logic.md`).
    - Includes:
        - Task 4: Updated Stage 2 prompt (`PROMPT_TEMPLATE_STAGE2`) to request source references in justification.
        - Task 5: Ensured `main` function returns Stage 1 & Stage 2 results.
        - Task 6: Implemented Markdown report generation (`generate_markdown_report`) including justification, Stage 1 ranking, scoring explanation, and saving to `recommendation_report_{uuid}.md`. (Note: Intermediate JSON output was removed).
        - Task 7: Added unit tests for Markdown report generation to `tests/test_generate_recommendation_report.py`.
    - Updated associated plan document (`memory-bank/major_changes/recommender_logic.md`) marking tasks 4, 5, 6, 7 complete.
29. **PDF Extraction Evaluation Script Enhancement**:
    - Modified `scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py` to include a `--file_pattern` command-line argument.
    - This allows specifying a glob pattern (e.g., `"gels_*.json"`) to filter the input JSON files processed by the script, defaulting to `*.json` if not provided.
    - Successfully tested the script by running it with `--file_pattern "gels_*.json"`.
30. **Orchestration Script Debugging & Refinement**:
    - Investigated inconsistent results (missing evaluations, missing/incomplete comparison reports) when running `scripts/orchestrate_scenario_evaluation.py`.
    - Identified root causes:
        - Sequential transcript evaluation causing single failures to halt evaluation for that transcript.
        - High concurrency (orchestrator parallel UUIDs + comparison script parallel insurers) likely exceeding LLM API rate limits, causing intermittent comparison report failures.
    - Implemented fixes:
        - Refactored `scripts/evaluation/transcript_evaluation/eval_transcript_main.py` to support single-file processing with exit codes.
        - Modified `scripts/orchestrate_scenario_evaluation.py` to run transcript evaluations in parallel per file.
        - Modified `scripts/orchestrate_scenario_evaluation.py` to run report generation (comparison + recommendation) sequentially per UUID, reducing peak API load.
        - Added detailed logging around LLM calls in `scripts/generate_policy_comparison.py`.
    - Updated the orchestration implementation plan (`memory-bank/major_changes/orchestration_script_implementation_plan.md`) to reflect changes and mark steps complete.
    - Confirmed successful run of the updated orchestrator script.

31. **Onboarding Instructions Update**:
    - Onboarding/setup instructions updated: README and Memory Bank now specify that new users must run `npm install` after cloning to install Node.js dependencies.

32. **Recommendation Report Script Enhancement (Transcript Context)**:
    - Modified `scripts/generate_recommendation_report.py` to incorporate the parsed customer transcript into the Stage 2 LLM re-ranking prompt (`PROMPT_TEMPLATE_STAGE2`).
    - Updated the `run_stage2_reranking` function to load, format, and pass the transcript data.
    - Updated the prompt instructions to guide the LLM on using transcript cues for prioritization.
    - **Revision:** Subsequently removed the loading and usage of the extracted requirements summary (`json_dict`) from the Stage 2 prompt and logic, simplifying the context to focus solely on the transcript and comparison reports.
33. **Recommendation Report Script Efficiency & Logging (`scripts/generate_recommendation_report.py`)**:
    - Added `--overwrite` flag handling logic.
    - Moved the check for existing report files *before* Stage 1/Stage 2 processing to prevent unnecessary LLM calls when `overwrite=False` (default).
    - Corrected the return value logic in `run_single_customer` to accurately reflect skipped processing in the batch summary.
    - Updated batch summary logging messages for clarity (`Failed or Skipped`).
    - Updated script docstrings (`argparse` help text and main docstring) to clearly state default argument behaviors.
34. **Orchestration Script Evaluation Scope (`scripts/orchestrate_scenario_evaluation.py`)**:
    - Modified the final evaluation step (`aggregate_and_filter_evaluations`) to remove filtering based on current run UUIDs.
    - The script now saves the complete evaluation results for *all* recommendation reports found for a given scenario at the time of execution.
    - Updated the output filename format for this final evaluation step to `results_{scenario}_all_transcripts_{run_timestamp}.json`.
35. **Orchestration Script Enhancement (`--only_aggregate`)**:
    - Added an `--only_aggregate` command-line flag to `scripts/orchestrate_scenario_evaluation.py`.
    - When this flag is used, the script skips steps 1-3 (transcript generation, pipeline processing, report generation) and proceeds directly to step 4 (final evaluation and aggregation) using the `TARGET_SCENARIOS` list.

## Next Steps (Revised Focus)

1.  **Test & Refine PDF Extraction Evaluation**:
    *   Run the `eval_pdf_extraction.py` script with diverse sample data.
    *   Analyze evaluation results and refine the script/prompt as needed for accuracy and completeness.
    *   Define clear, measurable metrics for PDF extraction quality based on the script's JSON output.
2.  **Implement Comparison Report Evaluation**:
    *   Design the evaluation methodology for the Markdown reports generated by `scripts/generate_policy_comparison.py`.
    *   Implement the corresponding evaluation script/process.
    *   Define metrics for assessing report quality, accuracy of tier selection, and justification clarity.
3.  **Refine Core Logic & Prompts**:
    *   Iteratively improve prompts, models (e.g., Gemini versions), and processing logic within existing scripts (generation, extraction, comparison, recommendation) based on ongoing testing and evaluation results.
4.  **Plan End-to-End Integration/Workflow V1**:
    *   Design a basic workflow to connect the key script steps automatically (e.g., Extraction -> Comparison -> Recommendation).
    *   Evaluate potential orchestration methods (simple script chaining, `Makefile`, `luigi`, `prefect`, `crewai` crew, etc.) considering maintainability and ease of execution.
5.  **ML Model Development (Later Phase)**:
    *   Plan the dataset preparation strategy using extracted requirements and potentially comparison/recommendation results.
    *   Outline initial goals for ML models (e.g., identifying key features influencing recommendations, predicting customer segment preferences).
6.  **Define Future Architecture**:
    *   Continue evaluating the effectiveness of the current script-heavy architecture versus potentially expanding the use of agents (`crewai` or other frameworks).
    *   Solidify the architectural plan based on refined project goals, performance analysis, and integration plans.

## Active Decisions and Considerations

1.  **LLM Selection & Configuration**:
    *   Continue primary use of Google Gemini via `LLMService` for most tasks due to centralized control and features.
    *   Maintain OpenAI via `crewai` for the Extractor Agent, but monitor performance and cost implications. Consider potential future migration to `LLMService` if feasible within `crewai` or if the agent is refactored.
    *   Refine default parameters in `gemini_config.py` as needed based on ongoing testing.

2.  **Architecture Strategy**:
    *   The current architecture is script-heavy with only one agent (`Extractor` using `crewai`/OpenAI).
    *   Need to decide whether to:
        *   Continue with a primarily script-based workflow.
        *   Implement future logic (Recommender) as simple scripts or agents.
        *   Adopt `crewai` (or another framework) more broadly if complex agent interactions become necessary.

3.  **Data Representation**:
    *   Continue using Pydantic models (`TravelInsuranceRequirement`, policy extraction schemas) for structured JSON validation and clarity.
    *   Define schema for final recommendation output.
    *   Refine existing schemas based on extraction/comparison needs and edge cases encountered.

4.  **Evaluation Metrics & Strategy**:
    *   Define specific, measurable metrics for the *planned* policy extraction and comparison report evaluations (e.g., F1 score for specific field extraction, ROUGE score for summary quality, human rating for justification clarity).
    *   Determine how evaluation results will feedback into prompt/logic refinement.

5.  **User Experience (Developer vs. End-User)**:
    *   Current UX is developer-focused (running scripts).
    *   If end-user interaction is a future goal, decisions are needed on the interface (conversational AI vs. GUI) and how to integrate it with the backend logic.
    *   Focus comparison report (`generate_policy_comparison.py`) output on clarity and justification for potential end-user consumption, even if delivered via script currently.

6.  **Integration & Orchestration**:
    *   Decide on the mechanism for connecting the different processing steps (manual script execution, simple chaining script, workflow engine, `crewai` crew). This impacts maintainability and ease of execution.

7.  **Deployment Strategy**:
    *   Current execution via CLI scripts is suitable for development.
    *   Re-evaluate deployment options (local application, containerization, cloud functions/services) if the system needs to be accessible to non-developers or scale significantly.

## Current Challenges

1.  **LLM Accuracy & Consistency**:
    *   Ensuring high accuracy and consistent formatting from LLMs for extraction (policy, requirements), comparison, and *evaluation* tasks remains a primary challenge. Requires ongoing prompt tuning.
    *   Strict adherence to complex JSON schemas (policy extraction, evaluation output) needs robust validation.
2.  **Evaluation Gaps**:
    *   The new PDF extraction evaluation script (`eval_pdf_extraction.py`) needs testing and validation.
    *   Lack of automated evaluation for *comparison report* quality hinders rapid iteration. Implementing this is a key next step.
3.  **Lack of Integration**:
    *   Components are disconnected scripts, requiring manual execution and data flow management. This increases complexity and potential for errors.
4.  **Recommendation Logic Evaluation & Refinement**:
    *   Evaluating the effectiveness of the current two-stage recommendation logic and refining prompts/scoring based on results.
5.  **Extractor Agent Dependency**:
    *   The Extractor Agent's reliance on OpenAI/CrewAI introduces a separate dependency and configuration path compared to the Gemini/LLMService used elsewhere.
6.  **Orchestrator Evaluation Scope**:
    *   The final evaluation step in the orchestrator now includes results for *all* reports found, not just the current run. Need to be mindful of this when interpreting the `*_all_transcripts_*.json` files.
7.  **Synthetic Data Limitations**:
    *   Generated transcripts might not fully capture real-world complexities, potentially limiting the robustness of downstream components.
7.  **Performance Optimization**:
    *   Latency of multiple LLM calls (generation, evaluation, extraction, comparison) needs monitoring. Batch processing and the optimized recommendation script (skipping existing reports) help, but overall workflow time can still be significant.
9.  **LLM Constraints**:
    *   Managing API rate limits, costs, and potential output token limits across both Gemini and OpenAI.
