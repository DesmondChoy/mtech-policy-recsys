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
│   ├── insurance_policies/  # Insurance policy documents
│   ├── transcripts/         # Conversation transcripts
│   ├── processed/           # Processed data
│   └── evaluation/          # Evaluation data
├── src/                     # Source code
│   ├── agents/              # Agent implementations
│   ├── models/              # LLM configurations
│   ├── prompts/             # Prompts for LLM tasks
│   ├── utils/               # Utility functions
│   └── web/                 # Web interface components
├── tests/                   # Test cases
└── scripts/                 # Utility scripts
```

## Technical Stack

- **Python**: Primary programming language
- **Google Gemini**: LLM for natural language processing
- **Jupyter Notebooks**: Development environment

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
3. Explore the notebooks in the `notebooks/` directory

## Academic Project

This is an academic project focused on applying multi-agent AI systems to solve real-world problems in the insurance domain.
