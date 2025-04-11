# Technical Context

## Technologies Used

### Core Technologies

1. **Python**:
   - Primary programming language
   - Version: Latest stable (3.x)
   - Used for: All agent implementations, data processing, and API integrations

2. **Google Gemini & OpenAI**:
   - Large Language Models for natural language processing and reasoning
   - Used for: Agent reasoning, text analysis, and generation tasks
   - Implementation:
     - Google Gemini: Used via the centralized `LLMService` (`src/models/llm_service.py`), which loads configuration (default model, parameters like `max_output_tokens`, API key) from `src/models/gemini_config.py`. Handles retries internally.
     - OpenAI: Used by the Extractor agent via the `crewai` framework (configured with `.env` variables).

3. **Jupyter Notebooks**:
   - Interactive development environment
   - Used for: Prototyping, experimentation, and demonstration

4. **JSON**:
   - Data interchange format
   - Used for: Structured data representation, agent communication

### Data Processing

1. **Pandas**:
   - Data manipulation and analysis library
   - Used for: Structured data processing, dataset creation

2. **NumPy**:
   - Numerical computing library
   - Used for: Mathematical operations, array manipulation

3. **Scikit-learn**:
   - Machine learning library
   - Used for: Supervised learning models, evaluation metrics

### Web Components

1. **Flask**:
   - Lightweight web framework
   - Used for: API endpoints, web interface

2. **HTML/CSS/JavaScript**:
   - Frontend technologies
   - Used for: User interface (if applicable)

### Utilities

1. **NLTK/spaCy**:
   - Natural language processing libraries
   - Used for: Text preprocessing, tokenization (Note: PDF text extraction for policy analysis is now handled by the Gemini model via the `LLMService` as used in `scripts/extract_policy_tier.py`)

3. **Matplotlib/Seaborn**:
   - Data visualization libraries
   - Used for: Creating visualizations for analysis and reporting

4. **pytest**:
   - Testing framework
   - Used for: Unit and integration testing

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
│   └── evaluation/             # Evaluation data
│       └── transcript_evaluations/ # Transcript evaluation results
├── src/                        # Source code
│   ├── agents/                 # Agent implementations
│   ├── models/                 # LLM configurations and services
│   ├── prompts/                # Prompts for LLM tasks
│   ├── utils/                  # Utility functions
│   └── web/                    # Web interface components
├── tests/                      # Test cases
├── scripts/                    # Utility scripts
│   ├── extract_policy_tier.py  # Extracts structured policy details (base/conditional limits, source-specific details) from PDFs into JSON.
│   ├── generate_policy_comparison.py # Generates Markdown comparison reports
│   ├── data_generation/        # Scripts specifically for data generation
│   │   ├── generate_personalities.py # Generates personality types
│   │   └── generate_transcripts.py   # Generates synthetic transcripts using LLM
│   └── evaluation/             # Evaluation-related scripts and data
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

## Technical Constraints

### Performance Constraints

1. **LLM Response Time**:
   - Challenge: LLM API calls introduce latency
   - Mitigation: Asynchronous processing, caching where appropriate

2. **Scalability**:
   - Challenge: Multiple LLM calls for voting mechanism
   - Mitigation: Efficient prompt design, parallel processing

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

3. **Output Reliability**:
   - Challenge: Ensuring accurate and appropriate recommendations
   - Mitigation: Voting mechanism, confidence thresholds

## Dependencies

### External Dependencies

1. **Google AI Python SDK**:
   - Purpose: Interface with Google Gemini API
   - Installation: `pip install google-generativeai`
   - Usage: Core dependency for LLM service
   - Version: >=0.3.0

2. **CrewAI**:
   - Purpose: Framework for orchestrating autonomous AI agents
   - Installation: `pip install crewai`
   - Usage: Used for Extractor Agent implementation
   - Version: Check `requirements.txt`

3. **Data Processing Libraries**:
   - Purpose: Data manipulation and analysis
   - Installation: `pip install pandas numpy scikit-learn`

4. **NLP Libraries**:
   - Purpose: Text processing
   - Installation: `pip install nltk spacy`

4. **Pydantic & DotEnv**:
   - Purpose: Data validation and environment variable management
   - Installation: `pip install pydantic python-dotenv` (Included in requirements.txt)
   - Usage: Used extensively by `scripts/extract_policy_tier.py` to define and validate the complex nested JSON structure (including `PolicyExtraction`, `CoverageDetail`, `LimitDetail`, `ConditionalLimit`, `SourceDetail`) extracted by Gemini. Also used for loading API keys via `dotenv`.

5. **Web Framework**:
   - Purpose: API and web interface
   - Installation: `pip install flask`

6. **Visualization**:
   - Purpose: Data visualization
   - Installation: `pip install matplotlib seaborn`

7. **Testing**:
   - Purpose: Unit and integration testing
   - Installation: `pip install pytest`

4. **OpenAI**:
   - Purpose: LLM used by the Extractor agent
   - Installation: `pip install openai` (Likely installed as a dependency of `crewai`)
   - Usage: Accessed implicitly by `crewai` when configured via `.env` variables (`OPENAI_API_KEY`, `OPENAI_MODEL_NAME`).

### Internal Dependencies

1. **LLM Service**:
   - Location: `src/models/llm_service.py`
   - Purpose: Provides a unified interface to Google Gemini, loading configuration (API key, default model, parameters) from `src/models/gemini_config.py`.
   - Features: Content generation (supports text prompts and multi-modal `contents` input), structured JSON output (with markdown/formatting fixes), streaming, batch processing, internal retry logic.
   - Used by: All scripts/agents requiring Gemini capabilities (e.g., `extract_policy_tier.py`, `generate_transcripts.py`, `eval_transcript_gemini.py`, `generate_personalities.py`).

2. **Agent Interdependencies**:
   - CS Agent → Extractor → Analyzer → Voting → Recommender
   - Most agents depend on the internal `LLMService` (Gemini) for reasoning.
   - The Extractor agent depends directly on the OpenAI API via `crewai`.

3. **Transcript Evaluation Modules**:
   - Location: `scripts/evaluation/transcript_evaluation/`
   - Purpose: Evaluate generated transcripts against standard and scenario-specific requirements.
   - Structure: Flat structure containing `eval_transcript_main.py` (entry point), `eval_transcript_parser.py` (reads transcript/scenario), `eval_transcript_prompts.py` (builds LLM prompt), `eval_transcript_gemini.py` (interfaces with LLMService), `eval_transcript_results.py` (saves results), `eval_transcript_utils.py` (helpers).
   - Dependencies: `LLMService`, `data/coverage_requirements/`, `data/scenarios/`.

4. **Utility Modules**:
   - Document processing utilities
   - Transcript processing utilities (`src/utils/transcript_processing.py`)
   - Email service utilities

4. **Data Dependencies**:
   - Insurance policy documents
   - Conversation transcripts (synthetic or real)
   - Evaluation datasets

## Configuration Management

1. **Environment Variables**:
   - API keys and credentials (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`)
   - Environment-specific settings
   - Managed via `python-dotenv` for local development (primarily for OpenAI keys used by `crewai`). Google API key is also loaded via `dotenv` by `GeminiConfig`.

2. **Configuration Files**:
   - Central Gemini LLM configuration: `src/models/gemini_config.py` (defines default model, parameters like temperature, `max_output_tokens`, safety settings). Loaded and used by `LLMService`.
   - Agent-specific configurations (e.g., within `crewai` agent definitions for the Extractor agent).
   - System-wide settings (potentially other config files if needed).

3. **Prompt Templates**:
   - Stored as separate files
   - Parameterized for flexibility
   - Versioned for consistency
