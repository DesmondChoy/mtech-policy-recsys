# Multi-Agent System for Insurance Policy Recommendations

A multi-agent system that transforms the complex process of buying travel insurance into a simple, personalized, and transparent experience.

## Project Overview

This system addresses common pain points in insurance purchasing by providing personalized, transparent, and objective recommendations through a conversational interface.

### Key Features

- **Conversational Interface**: Natural interaction with a Customer Service agent
- **Personalized Analysis**: Tailored recommendations based on individual needs
- **Multi-Agent Voting**: Consensus-based recommendations for increased reliability
- **Transparent Justifications**: Clear explanations linked to policy clauses
- **Iterative Refinement**: Ability to update requirements and receive new recommendations

# How To Use

## Transcript Processing and Requirement Extraction Workflow

This diagram illustrates the current workflow for processing call transcripts, evaluating them against coverage requirements, and extracting structured customer requirements:

```mermaid
flowchart TD
    subgraph Inputs
        T[Raw Call Transcripts <br> (data/transcripts/raw/*)]
        CR[Coverage Requirements <br> (data/coverage_requirements/coverage_requirements.py)]
    end

    subgraph Evaluation ["Transcript Evaluation (Automated Check)"]
        EVAL{Evaluate Transcript vs Requirements <br> using `scripts/evaluation/eval_transcript_main.py`}
    end

    subgraph Processing_Extraction ["Requirement Extraction (If Evaluation Passes)"]
        PARSE[Parse Raw Transcript to JSON <br> using `src/utils/transcript_processing.py`]
        EXTRACT[Extract Structured Requirements from JSON <br> using logic in `notebooks/agent_development/extractor/extractor_prototype.ipynb`]
        RESULT[Structured Requirements JSON <br> (e.g., insurance_requirement.json)]
    end

    T --> EVAL
    CR --> EVAL

    EVAL -->|Pass| PARSE
    EVAL -->|Fail| REGENERATE(Regenerate Transcript <br> *Future Step - Not Implemented*)

    PARSE --> EXTRACT
    EXTRACT --> RESULT

```

**Explanation:**

1.  **Inputs:** The workflow starts with Raw Call Transcripts (from `data/transcripts/raw/`) and the defined Coverage Requirements (from `data/coverage_requirements/coverage_requirements.py`).
2.  **Evaluation:** The `scripts/evaluation/eval_transcript_main.py` script automatically evaluates the transcript against the coverage requirements.
3.  **Decision:**
    *   If the evaluation **passes**, the transcript proceeds to the processing stage.
    *   If it **fails**, the ideal next step (currently not implemented) would be to regenerate or revise the transcript.
4.  **Processing & Extraction:**
    *   Passed transcripts are parsed into a structured JSON format by `src/utils/transcript_processing.py`.
    *   The logic within `notebooks/agent_development/extractor/extractor_prototype.ipynb` then extracts the final structured requirements from this JSON.
5.  **Output:** The result is a structured JSON file containing the extracted customer requirements (e.g., `insurance_requirement.json`).

## Policy Data Workflow

1.  **Input**: Raw insurance policy documents, typically in PDF format, are stored in the `data/raw_policies/` directory. These documents contain the detailed terms, conditions, and coverage information for various insurance products.
2.  **Processing (Potential)**: These raw PDFs often require processing to extract relevant text and structure the information for analysis. While a specific script isn't designated solely for this in `src/utils/`, notebooks like `notebooks/pdf_parsing/pdf_to_md.ipynb` explore methods for converting PDFs to more usable formats (like Markdown or plain text). Processed versions might be stored in `data/processed_policies/`.
3.  **Usage**: The structured information extracted from these policies is essential for downstream tasks, particularly for the Analyzer and Recommender agents, which need to compare customer requirements against actual policy details to provide accurate and justified recommendations.



# Project Structure

```
/
├── memory-bank/             # Cline's memory bank
├── notebooks/               # Jupyter notebooks for experimentation
│   ├── exploratory/         # Initial data exploration
│   ├── agent_development/   # Agent-specific experiments
│   ├── integration/         # Testing agent interactions
│   ├── evaluation/          # Performance metrics
│   └── demos/               # Demo notebooks
├── data/                    # Data storage
│   ├── coverage_requirements/ # Standardized coverage requirements
│   ├── raw_policies/        # Raw insurance policy documents
│   ├── processed_policies/  # Processed policy documents
│   ├── transcripts/         # Conversation transcripts
│   └── processed_transcript/ # Processed transcript data
├── src/                     # Source code
│   ├── agents/              # Agent implementations
│   ├── models/              # LLM configurations and services
│   ├── prompts/             # Prompts for LLM tasks
│   ├── utils/               # Utility functions
│   └── web/                 # Web interface components
├── tests/                   # Test cases
├── scripts/                 # Utility scripts
└── tutorials/               # Tutorial scripts and examples
```

## Technical Stack

- **Python**: Primary programming language
- **Google Gemini**: LLM for natural language processing
- **Jupyter Notebooks**: Development environment
- **LLM Service**: Reusable interface to Google Gemini API

## Components

### LLM Service

The project includes a reusable LLM service that provides a unified interface to the Google Gemini API:

- **Configuration**: Environment-based configuration with support for different models and parameter sets
- **Features**: Content generation, structured output (JSON), streaming responses, batch processing
- **Error Handling**: Retry logic, validation, and comprehensive error management
- **Tutorial**: Example usage in `tutorials/llm_service_tutorial.py`

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your Google Gemini API key:
   ```
   # In .env file or environment variables
   GOOGLE_API_KEY=your_api_key_here
   ```
4. Explore the notebooks in the `notebooks/` directory
5. Check out the LLM service tutorial: `python tutorials/llm_service_tutorial.py`

## Academic Project

This is an academic project focused on applying multi-agent AI systems to solve real-world problems in the insurance domain.
