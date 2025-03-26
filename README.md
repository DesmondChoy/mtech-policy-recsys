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

## Project Structure

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

### Agents

The system uses multiple specialized agents:

1. **CS Agent**: Handles user conversations
2. **Extractor**: Processes transcripts to extract requirements
3. **Analyzer**: Evaluates policies against requirements
4. **Voting System**: Aggregates multiple independent evaluations
5. **Recommender**: Delivers final recommendations with justifications

## Workflow

1. Customer interacts with CS Agent to express needs
2. Conversation is processed to extract key requirements
3. Requirements are compared against insurance policies
4. Multiple LLM instances vote on the most suitable policy
5. Results are consolidated and recommendations are delivered
6. Customer can provide feedback for refined recommendations

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your Google Gemini API key:
   ```
   # In .env file or environment variables
   GEMINI_API_KEY=your_api_key_here
   ```
4. Explore the notebooks in the `notebooks/` directory
5. Check out the LLM service tutorial: `python tutorials/llm_service_tutorial.py`

## Academic Project

This is an academic project focused on applying multi-agent AI systems to solve real-world problems in the insurance domain.
