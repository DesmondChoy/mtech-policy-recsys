# Introduction

- This project proposes an intelligent reasoning system to address these challenges, providing personalized travel insurance recommendations using hybrid machine reasoning techniques.
- The system integrates Decision Automation, Business Resource Optimization, Knowledge Discovery, and Cognitive Techniques to deliver unbiased, transparent, and efficient recommendations.

# Project Background

- Consumers find insurance policies complex due to technical jargon, information overload, cognitive biases, emotional decision-making, and limited time for thorough comparison.
- Current market lacks personalized, transparent tools that effectively empower consumers to make informed decisions.
- Insurance companies require deeper insights into customer preferences and competitive product positioning.

# Market Research

- Existing market solutions are often biased and don't adequately address iterative refinement based on evolving customer needs.
- Personalization Of Travel Insurance Plans Are More Important For Generation Y Travelers
- Intelligent reasoning systems using LLMs have been identified as effective solutions in knowledge discovery, decision automation, and cognitive systems.

# Project Scope - Key Features

- **Knowledge Extraction & Processing**: LLMs are used extensively to:
    - Generate synthetic customer service transcripts based on defined scenarios and requirements (`scripts/data_generation/generate_transcripts.py`).
    - Evaluate the quality and coverage of generated transcripts (`scripts/evaluation/transcript_evaluation/`).
    - Extract structured customer requirements from processed transcripts using an agent (`src/agents/extractor.py` with CrewAI/OpenAI).
    - Extract structured policy details (coverage, limits, conditions) from raw PDF documents (`scripts/extract_policy_tier.py` with LLMService/Gemini).
- **Policy Comparison & Reporting**: LLMs compare extracted customer requirements against structured policy data to generate detailed comparison reports (`scripts/generate_policy_comparison.py` with LLMService/Gemini).
- **Evaluation Focus**: Significant emphasis on evaluating the outputs of LLM-driven steps (transcript generation, planned: policy extraction, planned: comparison reports) to ensure quality and accuracy.
- **Knowledge Discovery & Data Mining (Future)**: Planned use of supervised ML models trained on customer data (e.g., extracted requirements) and potentially comparison results to uncover insights on product/market positioning.
- **Cognitive Techniques/Tools**: Use of structured knowledge bases (processed policies, extracted requirements) and planned transparent justification in comparison reports.

# Project Scope - Technical Architecture (Current Implementation)

- **Data Generation Pipeline**: Scripts generate synthetic transcripts (`generate_transcripts.py`) using personalities, scenarios, and coverage requirements.
- **Transcript Processing Pipeline**:
    - **Evaluation**: Transcripts are evaluated for quality (`scripts/evaluation/transcript_evaluation/`).
    - **Parsing**: Passed transcripts are parsed into a standard format (`src/utils/transcript_processing.py`).
    - **Extraction**: An Extractor Agent (`src/agents/extractor.py` using CrewAI/OpenAI) processes parsed transcripts to produce structured customer requirement JSON files.
- **Policy Processing Pipeline**: A script (`scripts/extract_policy_tier.py` using LLMService/Gemini) extracts detailed structured information from policy PDFs into JSON format.
- **Comparison Reporting**: A script (`scripts/generate_policy_comparison.py` using LLMService/Gemini) takes extracted requirements and processed policies to generate insurer-level comparison reports in Markdown format.
- **Evaluation Framework**: Includes transcript evaluation; planned evaluations for policy extraction and comparison report quality.
- **Machine Learning (Future)**: Supervised ML models planned for analyzing extracted requirements and comparison outcomes.
- **Feedback Loop (Conceptual)**: While direct user interaction agents (CS Agent, Recommender) are not implemented, the script-based workflow allows for iterative refinement by modifying inputs (scenarios, requirements) and re-running the pipeline.

# Data Collection and Preparation

- Structured Knowledge Base: Publicly available travel insurance policies.
- Dynamic Knowledge Base: User-generated conversation transcripts.
    - Initially synthetically generated via LLMs for diverse scenario coverage.
    - Potential inclusion of real human-AI conversational data
- Ground Truth Labels: Derived from clearly defined user needs and expected recommendation outcomes.
