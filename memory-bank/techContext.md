# Technical Context

## Technologies Used

### Core Technologies

1.  **Python**:
    *   Primary programming language
    *   Version: Latest stable (3.x)
    *   Used for: All agent implementations (currently Extractor), utility scripts, data processing, and API integrations.

2.  **Large Language Models (LLMs)**:
    *   **Google Gemini**:
        *   Primary LLM for most tasks (data generation, policy extraction, evaluation, comparison).
        *   Accessed via the centralized `LLMService` (`src/models/llm_service.py`).
        *   Configuration managed in `src/models/gemini_config.py`.
    *   **OpenAI Models (e.g., GPT-4o)**:
        *   Used *specifically* by the Extractor Agent (`src/agents/extractor.py`).
        *   Accessed via the `crewai` framework (for Extractor Agent) and directly via `openai` SDK (for `EmbeddingMatcher`).
        *   Configuration (API Key, Model Name) managed via `.env` file.

3.  **CrewAI**:
    *   Agent framework used for orchestrating the Extractor Agent.
    *   Handles agent definition, task management, and interaction with the configured LLM (OpenAI).
    *   Location: `src/agents/extractor.py`.

4.  **Pydantic**:
    *   Data validation and settings management library.
    *   Used for: Defining and validating structured JSON outputs (e.g., `TravelInsuranceRequirement`, policy extraction schemas), managing configuration.

5.  **NLTK**:
    *   Natural Language Toolkit.
    *   Used for: Text preprocessing (stopwords, stemming) within `src/embedding/embedding_utils.py`.

6.  **Jupyter Notebooks**:
    *   Interactive development environment.
    *   Used for: Initial prototyping, experimentation, and demonstration (though core logic is now in scripts/agents).

6.  **JSON**:
    *   Primary data interchange format.
    *   Used for: Structured data representation (transcripts, requirements, policies, evaluations), configuration.

## Development Setup

### Environment

1. **Virtual Environment**:
   - Tool: venv or conda
   - Purpose: Isolate project dependencies

2. **Version Control**:
   - System: Git
   - Repository: GitHub
   - Branching Strategy: Feature branches with pull requests

3. **IDE/Editor**:
   - Primary: VS Code
   - Extensions: Python, Jupyter, Git integration

### Project Structure

```
/
├── memory-bank/                # Cline's memory bank
├── notebooks/                  # Jupyter notebooks for experimentation
│   ├── exploratory/            # Initial data exploration
│   ├── agent_development/      # Agent-specific experiments
│   ├── integration/            # Testing agent interactions
│   ├── evaluation/             # Performance metrics
│   └── demos/                  # Demo notebooks
├── data/                       # Data storage
│   ├── coverage_requirements/  # Standardized coverage requirements
│   ├── extracted_customer_requirements/ # Extracted requirements (e.g., requirements_{scenario}_{uuid}.json)
│   ├── policies/               # Insurance policy documents
│   │   ├── raw/                # Raw policy PDFs
│   │   └── processed/          # Processed policy JSON files (structured output)
│   ├── transcripts/            # Conversation transcripts
│   │   ├── raw/                # Raw transcripts (e.g., synthetic/, real/)
│   │   └── processed/          # Processed/parsed transcripts (e.g., parsed_transcript_{scenario}_{uuid}.json)
│   ├── evaluation/             # Evaluation data & results
│   │   ├── pdf_extraction_evaluations/ # PDF extraction eval results
│   │   ├── scenario_evaluation/      # Scenario eval results & ground truth
│   │   └── transcript_evaluations/   # Transcript evaluation results
│   └── ground_truth/           # Curated ground truth data
│       └── ground_truth.json
├── src/                        # Source code
│   ├── agents/                 # Agent implementations (currently extractor.py, recommender.py [empty])
│   ├── embedding/              # Embedding related utilities
│   │   ├── __init__.py
│   │   ├── embedding_utils.py
│   │   └── cache/              # Cache for embeddings (*.pkl)
│   ├── models/                 # LLM configurations (gemini_config.py) and services (llm_service.py)
│   ├── utils/                  # Utility functions (transcript_processing.py, etc.)
│   └── web/                    # Basic CLI runner (app.py)
├── tests/                      # Test cases
├── scripts/                    # Utility scripts
│   ├── calculate_scenario_pass_rates.py
│   ├── extract_policy_tier.py
│   ├── generate_coverage_mapping.py
│   ├── generate_ground_truth_coverage.py
│   ├── generate_policy_comparison.py
│   ├── generate_recommendation_report.py
│   ├── orchestrate_scenario_evaluation.py
│   ├── extract_policy_tier.py
│   ├── generate_policy_comparison.py
│   ├── generate_recommendation_report.py
│   ├── data_generation/        # Scripts specifically for data generation
│   │   ├── generate_personalities.py
│   │   └── generate_transcripts.py
│   └── evaluation/             # Evaluation-related scripts and data
│       ├── pdf_extraction_evaluation/
│       │   └── eval_pdf_extraction.py
│       ├── scenario_evaluation/
│       │   └── evaluate_scenario_recommendations.py
│       └── transcript_evaluation/ # Transcript evaluation scripts (flat structure)
│           ├── eval_transcript_main.py
│           ├── eval_transcript_gemini.py
│           ├── eval_transcript_parser.py
│           ├── eval_transcript_prompts.py
│           ├── eval_transcript_results.py
│           └── eval_transcript_utils.py
└── tutorials/                  # Tutorial scripts and examples
```

### Development Workflow

1. **Setup**:
   - Clone repository
   - Create virtual environment
   - Install dependencies from requirements.txt
   - Run `npm install` to install Node.js dependencies

2. **Development Cycle**:
   - Prototype in notebooks
   - Implement in source code
   - Write tests
   - Document changes

3. **Testing**:
   - Unit tests for individual components
   - Integration tests for agent interactions
   - End-to-end tests for complete workflows

4. **Documentation**:
   - Code comments and docstrings
   - README and documentation files
   - Jupyter notebooks for demonstrations

## Node.js/Frontend Dependencies

If you are setting up the project for the first time (or after cloning), you must install Node.js dependencies:

```bash
npm install
```

This installs all necessary packages listed in `package.json` for any web or supporting scripts. Run this before using any Node.js-based features or scripts.

## Technical Constraints

### Performance Constraints

1. **LLM Response Time**:
   - Challenge: LLM API calls introduce latency
   - Mitigation: Asynchronous processing, caching where appropriate

2.  **Scalability**:
    *   Challenge: Multiple LLM calls across the script pipeline (generation, evaluation, extraction, comparison) can lead to long processing times for large batches.
    *   Mitigation: Efficient prompt design, parallel/asynchronous processing (used in comparison script), potential caching.

3. **Resource Usage**:
   - Challenge: Memory requirements for processing large policy documents
   - Mitigation: Chunking strategies, efficient data structures

### Integration Constraints

1. **API Limitations**:
   - Challenge: Rate limits, quotas, and potential output token limits for LLM APIs
   - Mitigation: Request throttling and retry logic handled by `LLMService`. Default `max_output_tokens` set centrally in `src/models/gemini_config.py`, can be overridden per call in `LLMService` methods if needed.

2. **Data Format Variability**:
   - Challenge: Inconsistent formats across insurance policies
   - Mitigation: Robust parsing strategies, standardization pipelines

3. **Email Integration**:
   - Challenge: Email delivery and formatting
   - Mitigation: Reliable email service, templating system

### Security and Privacy Constraints

1. **Data Protection**:
   - Challenge: Handling potentially sensitive user information
   - Mitigation: Data minimization, secure storage practices

2. **LLM Prompt Injection**:
   - Challenge: Potential for prompt manipulation
   - Mitigation: Input validation, prompt engineering best practices

3.  **Output Reliability**:
    *   Challenge: Ensuring accurate and appropriate outputs from LLM-driven steps (extraction, comparison).
    *   Mitigation: Evaluation gates (transcript evaluation), planned evaluations (policy extraction, comparison), prompt engineering, structured output validation (Pydantic).

## Dependencies

### External Dependencies

1. **Google GenAI SDK**:
   - Purpose: Interface with Google Gemini API
   - Installation: `pip install google-genai`
   - Usage: Core dependency for LLM service

2. **CrewAI**:
   - Purpose: Framework for orchestrating autonomous AI agents
   - Installation: `pip install crewai`
   - Usage: Used for Extractor Agent implementation
   - Version: Check `requirements.txt`

3. **Pydantic & DotEnv**:
   - Purpose: Data validation and environment variable management
   - Installation: `pip install pydantic python-dotenv`
   - Usage: Used extensively by `scripts/extract_policy_tier.py` to define and validate the complex nested JSON structure (including `PolicyExtraction`, `CoverageDetail`, `LimitDetail`, `ConditionalLimit`, `SourceDetail`) extracted by Gemini. Also used for loading API keys via `dotenv`.

4. **OpenAI**:
   - Purpose: LLM used by the Extractor agent and for generating embeddings in `EmbeddingMatcher`.
   - Installation: `pip install openai` (Likely installed as a dependency of `crewai`)
   - Usage: Accessed implicitly by `crewai` when configured via `.env` variables (`OPENAI_API_KEY`, `OPENAI_MODEL_NAME`). Accessed directly by `EmbeddingMatcher` (`src/embedding/embedding_utils.py`) using API key from `.env`.

5. **NLTK**:
   - Purpose: Text preprocessing (stopwords, stemming).
   - Installation: `pip install nltk`
   - Usage: Used by `EmbeddingMatcher` (`src/embedding/embedding_utils.py`). Requires downloading stopwords data (`nltk.download('stopwords')`).

### Internal Dependencies

1.  **LLM Service (`src/models/llm_service.py`)**:
    *   Provides a unified interface to **Google Gemini**.
    *   Handles configuration loading (`gemini_config.py`), API calls, retries, and robust JSON parsing.
    *   Consumed by most utility scripts (`extract_policy_tier.py`, `generate_policy_comparison.py`, data generation, evaluation).

2.  **Extractor Agent (`src/agents/extractor.py`)**:
    *   Depends on the **`crewai`** framework and **OpenAI** API (configured via `.env`).
    *   Consumes processed transcripts (`data/transcripts/processed/`).
    *   Uses the `TravelInsuranceRequirement` model from `src/utils/transcript_processing.py`.
    *   Produces extracted requirements (`data/extracted_customer_requirements/`).
    *   *Does not* currently interact with other agents or the `LLMService`.

3.  **Utility Scripts (`scripts/`)**:
    *   **Data Generation (`scripts/data_generation/`)**: Depend on `LLMService`.
    *   **Policy Extraction (`scripts/extract_policy_tier.py`)**: Depends on `LLMService`.
    *   **Transcript Evaluation (`scripts/evaluation/transcript_evaluation/`)**: Depends on `LLMService`.
    *   **Policy Comparison (`scripts/generate_policy_comparison.py`)**: Depends on `LLMService`, Extractor output, and Policy Extraction output.
    *   **Scenario Evaluation (`scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`)**: Depends on Recommendation Report output, `data/ground_truth/ground_truth.json`, and `src/embedding/embedding_utils.py`.
    *   **Ground Truth Coverage Generation (`scripts/generate_ground_truth_coverage.py`)**: Likely depends on `src/embedding/embedding_utils.py` and `data/ground_truth/ground_truth.json`.
    *   **Orchestration Script (`scripts/orchestrate_scenario_evaluation.py`)**: Automates the end-to-end workflow, calling other scripts. Includes flags like `--skip_transcript_eval` and `--only_aggregate` to control execution flow.

4.  **Utility Modules (`src/`)**:
    *   `src/utils/transcript_processing.py`: Defines `TravelInsuranceRequirement` Pydantic model (used by Extractor) and parsing logic.
    *   `src/embedding/embedding_utils.py`: Defines `EmbeddingMatcher` for semantic comparison against ground truth. Depends on OpenAI API and NLTK.
    *   Other utilities as needed.

5.  **Data Dependencies**:
    *   Raw/Processed Policies (`data/policies/`)
    *   Raw/Processed Transcripts (`data/transcripts/`)
    *   Extracted Requirements (`data/extracted_customer_requirements/`)
    *   Ground Truth Data (`data/ground_truth/ground_truth.json`)
    *   Evaluation Results (`data/evaluation/`)
    *   Supporting data (Scenarios, Coverage Requirements, Personalities).
    *   Embedding Cache (`src/embedding/cache/*.pkl`)

## Configuration Management

1.  **Environment Variables (`.env`)**:
    *   Used for **OpenAI** configuration needed by `crewai` (Extractor Agent) and `EmbeddingMatcher`: `OPENAI_API_KEY`, `OPENAI_MODEL_NAME` (optional, defaults to `gpt-4o` for crewai if not set).
    *   Used for `GEMINI_API_KEY` loaded by `GeminiConfig`.
    *   Managed via `python-dotenv`.

2.  **Configuration Files**:
    *   **Netlify Configuration (`netlify.toml`)**: Defines build settings specifically for deploying the `ux-webapp` frontend. Key settings include:
        *   `build.command = "cd ux-webapp && npm install && npm run build"`: Ensures dependencies are installed and the build runs within the frontend directory. Includes the asset sync script via the nested `npm run build` command in `ux-webapp/package.json`.
        *   `build.publish = "ux-webapp/dist"`: Specifies the directory containing the built frontend assets.
        *   Netlify site settings must point to the correct production branch (e.g., `main`).
    *   **Gemini LLM Configuration (`src/models/gemini_config.py`)**: Central configuration for Google Gemini models used by `LLMService`. Defines default model, parameters (temperature, `max_output_tokens`), safety settings, and loads API key from `.env`.
    *   **Agent Configuration (Implicit)**: The Extractor Agent's configuration (role, goal, LLM choice) is defined directly within `src/agents/extractor.py` using `crewai` constructs.
    *   **Frontend Build & Dev Configuration (`ux-webapp/package.json`)**:
        *   The `build` script is configured to run the asset sync script (`node ./scripts/sync-public-assets.cjs`) before compiling TypeScript (`tsc -b`) and running Vite (`vite build`).
        *   The `predev` script hook is configured to automatically run the asset sync script (`npm run sync-public-assets`) *before* the `dev` script (which runs `vite`) executes. This ensures data is synced for local development.

3.  **Prompt Templates**:
    *   Defined as constants or formatted strings within the Python scripts/agents that use them (e.g., `extractor.py`, `generate_policy_comparison.py`, `extract_policy_tier.py`).
    *   Parameterized for dynamic content injection.
