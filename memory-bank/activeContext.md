# Active Context

## Current Work Focus

The project is in the initial setup and planning phase. The current focus is on:

1. **Memory Bank Initialization**:
   - Creating and populating the core memory bank files
   - Establishing documentation structure for the project

2. **Project Structure Setup**:
   - Organizing directories and files according to the defined structure
   - Setting up the development environment

3. **Data Collection and Preparation**:
   - Gathering insurance policy documents
   - Creating synthetic conversation transcripts
   - Processing raw data into usable formats

4. **Agent Prototyping**:
   - Developing initial prototypes for each agent
   - Experimenting with prompt engineering for LLM-based agents

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

## Next Steps

1. **Agent Development**:
   - Implement CS Agent prototype
     - Develop conversation handling capabilities
     - Create prompt templates for guiding user interactions
     - Integrate with LLM service for natural language understanding

   - Implement Analyzer Agent prototype
     - Develop policy analysis capabilities (Note: Notebook prototype was found to be blank and can be removed)
     - Input will be the structured JSON from the Extractor step (`data/extracted_customer_requirements/`) and processed policy JSON (`data/policies/processed/`).
     - Could potentially leverage or adapt the output format from `scripts/generate_policy_comparison.py`.
     - Create structured analysis report schema.
     - Leverage LLM service for policy comparison.

   - Implement Voting System prototype
     - Develop consensus mechanism (Leveraging LLM service batch generation)
     - Create aggregation algorithms
     - Implement confidence scoring

   - Implement Recommender Agent prototype
     - Develop recommendation generation
     - Create email formatting templates
     - Use LLM service for justification generation

2. **Data Processing Pipeline**:
   - Complete policy document processing
   - Standardize policy data format
   - Create additional synthetic conversation scenarios

3. **Integration Testing**:
   - Test agent interactions (Extractor -> Analyzer)
   - Validate end-to-end workflow
   - Measure system performance

4. **ML Model Development**:
   - Create supervised learning dataset using extracted requirements
   - Train initial models
   - Evaluate feature importance

## Active Decisions and Considerations

1. **LLM Selection & Configuration**:
   - Primarily using Google Gemini via the centralized `LLMService`.
   - Default Gemini model (`gemini-2.5-pro-exp-03-25`) and parameters (e.g., `max_output_tokens=10000`) are now set in `src/models/gemini_config.py` and used by `LLMService`.
   - Specific models or parameters can still be overridden per call if needed (e.g., `generate_structured_content` uses deterministic parameters).
   - The Extractor Agent (`src/agents/extractor.py`) still uses OpenAI via `crewai`, configured through `.env` variables.

2. **Agent Architecture**:
   - Using `crewai` framework for agent definition and task execution (as seen in Extractor).
   - Determining optimal level of modularity vs. monolithic crew.
   - Considering whether to implement agents as separate services or within a single application.
   - Evaluating synchronous vs. asynchronous communication between agents.

3. **Data Representation**:
   - Using Pydantic models (`TravelInsuranceRequirement`) for structured agent output (Extractor).
   - Designing schemas for analysis reports (Analyzer).
   - Determining level of structure vs. flexibility in data formats.
   - Considering how to handle edge cases and unusual requirements.

4. **Evaluation Metrics**:
   - Defining success criteria for recommendations
   - Developing evaluation framework for system performance
   - Creating benchmarks for comparison

5. **User Experience**:
   - Determining the optimal conversation flow for the CS Agent
   - Designing the format and content of recommendation emails
   - Balancing comprehensiveness with clarity in recommendations

6. **Deployment Strategy**:
   - Current execution via CLI script (`src/web/app.py`).
   - Considering deployment options (local, cloud-based).
   - Evaluating scalability requirements.
   - Planning for potential production use cases.

## Current Challenges

1. **Policy Extraction Accuracy**:
   - While `scripts/extract_policy_tier.py` automates extraction, ensuring the LLM accurately interprets complex policy documents and adheres strictly to the JSON schema remains crucial.
   - Requires careful prompt engineering and potentially fine-tuning or few-shot examples.

2. **Requirement Extraction Accuracy**:
   - Ensuring the Extractor Agent accurately captures all nuances, including implicit needs.
   - Validating the structured output against the transcript.
   - Handling ambiguous or contradictory statements effectively.

3. **Recommendation Justification**:
   - Providing clear, understandable explanations (Recommender task)
   - Linking recommendations directly to policy clauses (Analyzer/Recommender task)
   - Balancing detail with readability

4. **Performance Optimization**:
   - Managing latency from multiple LLM calls
   - Optimizing prompt design for efficiency
   - Implementing appropriate caching strategies
   - Added retry logic and error handling in LLM service
   - Batch processing capabilities for parallel operations

5. **LLM Output Limits**:
   - Challenge: LLM settings (like `max_output_tokens`) can cause unexpected truncation of generated content.
   - Mitigation: Default `max_output_tokens` is now centrally managed in `src/models/gemini_config.py` (currently 10000). `LLMService` allows overriding this default per call if a specific task requires a different limit. Continuous monitoring for potential truncation is still advised.
