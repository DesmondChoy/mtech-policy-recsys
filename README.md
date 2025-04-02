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

## Data Generation and Processing Workflow

1.  **Synthetic Transcript Generation (Optional)**: To create synthetic training or testing data, use the prompts provided in `scripts/data_generation/prompts.md`. These prompts guide the generation of diverse customer personalities and then use those personalities to create realistic conversation transcripts between a customer and a service agent. The generated raw transcripts are typically saved in `data/transcripts/synthetic/`.
2.  **Input**: Raw conversation transcripts (either synthetically generated or real) are stored as text files (e.g., `.txt`) in the `data/transcripts/synthetic/` or `data/transcripts/real/` directories. These transcripts typically follow a format like `Speaker Name: Dialogue text`.
3.  **Processing**: The script `src/utils/transcript_processing.py` is used to parse these raw text files.
    *   It reads each line of the transcript.
    *   It uses regular expressions to identify the speaker and their corresponding dialogue.
    *   It structures the conversation into a list of speaker-dialogue pairs.
4.  **Output**: The script outputs a structured JSON file for each processed transcript (e.g., `parsed_transcript_01.json`) into the `data/processed_transcript/` directory. This JSON format is used as input for downstream tasks, such as the requirement extraction agent (`notebooks/agent_development/extractor/extractor_prototype.ipynb`).

To process a specific transcript (e.g., `transcript_05.txt`), you can modify and run the `main()` function within `src/utils/transcript_processing.py` or import and use the `process_transcript` function elsewhere.

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
