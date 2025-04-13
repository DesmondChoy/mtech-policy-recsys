# Multi-Agent System for Insurance Policy Recommendations

A multi-agent system that transforms the complex process of buying travel insurance into a simple, personalized, and transparent experience.

## Project Overview

This system addresses common pain points in insurance purchasing by providing personalized, transparent, and objective recommendations through a conversational interface.

### Key Features

- **Automated Policy Extraction**: Uses LLMs to parse policy PDFs, extracting tier-specific coverage into structured JSON, including base/conditional limits and source-linked details.
- **Synthetic Transcript Generation**: Creates realistic, scenario-driven customer conversations using LLMs, incorporating personalities and specific coverage requirements.
- **LLM-Based Transcript Evaluation**: Assesses generated transcripts for requirement coverage completeness (standard and scenario-specific) using LLMs, providing JSON results with quote-based justifications.
- **Structured Requirement Extraction**: Employs an AI agent (using the CrewAI framework) to analyze transcripts and convert customer needs into validated, structured JSON based on a predefined schema.
- **Insurer-Level Policy Comparison**: Generates Markdown reports via LLMs comparing customer requirements against all policy tiers for an insurer, recommending the best-fit tier with justification and detailed coverage analysis.
- **Final Recommendation Report Generation**: Processes comparison reports, applies scoring, uses an LLM for re-ranking, and generates a final customer-friendly Markdown recommendation report.
- **PDF Extraction Evaluation**: Compares processed policy JSON against the source PDF using a multi-modal LLM to verify extraction accuracy and completeness.
- **(Planned) Conversational Interface**: Future goal for natural language interaction.
- **(Planned) Multi-Agent Voting & Recommendation**: Future goal for consensus-based recommendations.
- **(Planned) Iterative Refinement**: Future goal for users to update needs and receive refined recommendations.

## How To Use

This section outlines the primary workflows for preparing data, processing transcripts, and generating comparison reports within the system.

## 1. Data Preparation and Processing Pipeline

This section describes the end-to-end workflow for preparing policy data and generating/processing transcript data to extract customer requirements.

1.  **Extract Policy Data**:
    *   **Input**: Place raw insurance policy documents (PDF) into `data/policies/raw/` following the naming convention `insurer_{policy_tier}.pdf`.
    *   **Action**: Run `python scripts/extract_policy_tier.py`.
    *   **Process**: Uses Gemini API to extract structured coverage details for the specified tier, validates output using Pydantic.
    *   **Output**: Structured JSON files (`insurer_{policy_tier}.json`) saved in `data/policies/processed/`.

2.  **Generate Personalities (Optional)**:
    *   **Action**: If `data/transcripts/personalities.json` is missing or needs updating, run `python scripts/data_generation/generate_personalities.py`.
    *   **Process**: Uses Gemini API to generate a list of customer personalities.
    *   **Output**: `data/transcripts/personalities.json`.

3.  **Generate Synthetic Transcripts**:
    *   **Input**: `data/transcripts/personalities.json`, `data/coverage_requirements/coverage_requirements.py`. Optionally, specify a scenario file from `data/scenarios/` using `-s`.
    *   **Action**: Run `python scripts/data_generation/generate_transcripts.py -n <number_of_transcripts> [-s <scenario_name>]`.
    *   **Process**: Uses Gemini API to create synthetic conversation transcripts based on inputs.
    *   **Output**: Structured JSON transcript files saved in `data/transcripts/raw/synthetic/`. Filenames follow the format `transcript_{scenario_name}_{timestamp}.json` (if scenario used) or `transcript_{timestamp}.json` (if no scenario). Example: `transcript_golf_coverage_20250410_220036.json`.

4.  **Evaluate Raw Transcripts**:
    *   **Input**: Raw synthetic transcripts from `data/transcripts/raw/synthetic/`.
    *   **Action**: Run `python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --directory data/transcripts/raw/synthetic/`.
    *   **Process**: Evaluates if the raw transcripts adequately cover standard and scenario-specific requirements using Gemini API.
    *   **Output**: Evaluation results saved in `data/evaluation/transcript_evaluations/`. (Note: The pipeline proceeds regardless of pass/fail currently).

5.  **Parse Raw Transcripts (Batch)**:
    *   **Input**: Raw synthetic transcripts (`.json`) from `data/transcripts/raw/synthetic/`.
    *   **Action**: Run `python src/utils/transcript_processing.py`.
    *   **Process**: Batch-processes all raw transcripts, parsing them into a standardized JSON list format.
    *   **Output**: Parsed JSON files saved in `data/transcripts/processed/` with a `parsed_` prefix (e.g., `parsed_transcript_golf_coverage_20250410_220036.json`).

6.  **Extract Requirements (Batch)**:
    *   **Input**: Parsed transcript JSON files from `data/transcripts/processed/`.
    *   **Action**: Run `python src/agents/extractor.py`. (Optionally specify `--input_dir` or `--output_dir`).
    *   **Process**: Batch-processes all parsed transcripts using the Extractor Agent (CrewAI with OpenAI) to extract structured requirements.
    *   **Output**: Structured requirements JSON files saved in `data/extracted_customer_requirements/`. Filenames follow the format `requirements_{original_name_part}.json` (e.g., `requirements_the_confused_novice_20250403_175921.json`), conforming to the `TravelInsuranceRequirement` Pydantic model.

This sequence takes you from raw data to structured policy information and customer requirements, ready for downstream analysis and comparison.

## 2. Policy Comparison Report Generation (Insurer-Level)

This step uses the structured requirements and policy data to generate detailed Markdown comparison reports **for each insurer** against a specific customer's needs. This script implements the insurer-level analysis approach, comparing all tiers of an insurer in a single LLM call.

1.  **Input**: Requires structured requirements JSON from step 6 (`data/extracted_customer_requirements/`) and processed policy JSON files from step 1 (`data/policies/processed/`). Also uses tier rankings from `data/policies/pricing_tiers/tier_rankings.py`.
2.  **Processing**: Run the `scripts/generate_policy_comparison.py` script, providing the **customer UUID** via the `--customer_id` argument.
    ```bash
    # Example using a specific customer UUID
    python scripts/generate_policy_comparison.py --customer_id 49eb20af-32b0-46e0-a14e-0dbe3e3c6e73
    ```
    The script finds the corresponding requirements file (`requirements_*_{uuid}.json`), identifies all available insurers and their tiers from `data/policies/processed/`, and uses the Gemini API via `LLMService` to generate a report for each insurer. It processes insurers asynchronously.
3.  **Output**: Markdown reports are saved to a subdirectory within `results/` named after the customer UUID (e.g., `results/49eb20af-32b0-46e0-a14e-0dbe3e3c6e73/`). Each report file is named `policy_comparison_report_{insurer}_{customer_uuid}.md` and contains:
    *   The recommended tier for that insurer.
    *   Justification for the recommendation.
    *   A detailed requirement-by-requirement analysis of the recommended tier's coverage.
    *   A summary of the recommended tier's strengths and weaknesses.

## 3. Final Recommendation Report Generation

This step takes the insurer-level comparison reports generated in the previous step and produces a single, final recommendation report for the customer. It uses a two-stage process: initial scoring/ranking followed by LLM-based re-ranking and justification.

1.  **Input**: Requires the Markdown comparison reports generated by `scripts/generate_policy_comparison.py` located in the `results/{uuid}/` directory.
2.  **Processing**: Run the `scripts/generate_recommendation_report.py` script, providing the **customer UUID** via the `--customer_id` argument.
    ```bash
    # Example using a specific customer UUID
    python scripts/generate_recommendation_report.py --customer_id 49eb20af-32b0-46e0-a14e-0dbe3e3c6e73
    ```
    The script parses the comparison reports, performs Stage 1 scoring based on requirement matching, selects top candidates, and then uses the Gemini API via `LLMService` for Stage 2 re-ranking and justification generation.
3.  **Output**:
    *   A final Markdown recommendation report saved to `results/{uuid}/recommendation_report_{uuid}.md`. This report includes the final ranked list of recommended policies, detailed justifications with source references, and an explanation of the scoring.

## 4. Evaluation Scripts

This section describes the available scripts for evaluating the quality and accuracy of different pipeline stages.

### 4.1 Transcript Evaluation

- **Component**: `scripts/evaluation/transcript_evaluation/eval_transcript_main.py`
- **Purpose**: Evaluates if raw generated transcripts contain all required coverage information (standard and scenario-specific) using the Gemini API.
- **Input**: Raw transcript JSON files (e.g., from `data/transcripts/raw/synthetic/`). Can process a single file or a directory.
- **Output**: Evaluation results saved in `data/evaluation/transcript_evaluations/` (by default) in specified formats (JSON, TXT, CSV summary).
- **Usage Examples**:
  ```bash
  # Evaluate a single transcript
  python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --transcript data/transcripts/raw/synthetic/transcript_golf_coverage_6aef8846-aed1-4a6e-8115-d5ca7d6d0abf.json

  # Evaluate all transcripts in a directory
  python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --directory data/transcripts/raw/synthetic/

  # Specify output directory and formats
  python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --directory data/transcripts/raw/synthetic/ --output-dir custom/eval_results --format json,csv
  ```

### 4.2 PDF Extraction Evaluation

- **Component**: `scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py`
- **Purpose**: Compares the structured JSON extracted from a policy PDF (`data/policies/processed/`) against the original source PDF (`data/policies/raw/`) using a multi-modal Gemini model to assess extraction accuracy and completeness. Performs two-way verification.
- **Input**: Processed policy JSON files (`data/policies/processed/`) and corresponding raw policy PDFs (`data/policies/raw/`). Can filter input JSON files using a glob pattern.
- **Output**: Evaluation results saved as JSON files in `data/evaluation/pdf_extraction_evaluations/`.
- **Usage Examples**:
  ```bash
  # Evaluate all processed policy JSON files
  python scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py

  # Evaluate only FWD policies
  python scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py --file_pattern "fwd_*.json"

  # Evaluate only GELS Gold policy
  python scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py --file_pattern "gels_{Gold}.json"
  ```

## 5. Future Enhancements

The outputs from the current pipeline (Structured Policy JSON, Structured Requirements JSON, Comparison Reports, Final Recommendation) provide a solid foundation. Future work may focus on:
- Implementing automated evaluation for comparison report quality.
- Developing a more sophisticated integration/orchestration layer to connect the scripts into a seamless workflow.
- Exploring the use of ML models for deeper insights based on the generated data.
- Potentially developing a conversational interface for end-users.

## Project Structure

```
/
├── data/                       # Data storage
│   ├── coverage_requirements/  # Standardized coverage requirements
│   ├── extracted_customer_requirements/ # Extracted requirements from transcripts
│   ├── policies/               # Insurance policy documents
│   │   ├── raw/                # Original PDF policy documents
│   │   └── processed/          # Processed policy JSON files
│   ├── scenarios/              # Scenario definitions for transcript generation
│   ├── transcripts/            # Conversation transcripts
│   │   ├── raw/                # Original conversation transcripts (synthetic/, real/)
│   │   └── processed/          # Processed JSON transcripts
│   └── evaluation/             # Evaluation data & results
│       └── transcript_evaluations/ # Transcript evaluation results
├── memory-bank/                # Cline's memory bank (documentation)
├── notebooks/                  # Jupyter notebooks for experimentation & prototyping
├── results/                    # Output comparison reports
├── scripts/                    # Utility & automation scripts (data generation, evaluation, etc.)
├── src/                        # Core application source code (agents, models, utils)
├── tests/                      # Test cases
├── tutorials/                  # Guides and example scripts
├── .gitignore                  # Git ignore file
├── README.md                   # This file
└── requirements.txt            # Project dependencies
```

## Key Workflow Components

The project structure supports the workflow illustrated in the diagram above:

1. **Data Inputs**
   - **Policy Documents**: Located in `data/policies/raw/` (PDF format)
   - **Call Transcripts**: Located in `data/transcripts/raw/` (text format)
   - **Coverage Requirements**: Defined in `data/coverage_requirements/coverage_requirements.py`

2. **Transcript Processing**
   - **Component**: `src/utils/transcript_processing.py`
   - **Purpose**: Parses raw transcripts into structured JSON format
   - **Output**: JSON files in `data/transcripts/processed/`

4. **Requirement Extraction**
   - **Component**: `src/agents/extractor.py`
   - **Purpose**: Extracts structured customer requirements from parsed transcript JSON files using a CrewAI agent (configured with OpenAI). Run via CLI for batch processing.
   - **Input**: Directory containing processed transcript JSON files (default: `data/transcripts/processed/`).
   - **Output**: Saves structured requirements JSON to `data/extracted_customer_requirements/` (default). Filenames follow the format `requirements_{original_name_part}.json` (e.g., `requirements_the_confused_novice_20250403_175921.json`), conforming to the `TravelInsuranceRequirement` model.

5. **Policy Processing**
   - **Component**: `scripts/extract_policy_tier.py`
   - **Purpose**: Extracts structured coverage details from policy PDFs using Gemini API for a specific policy tier.
   - **Input**: PDFs from `data/policies/raw/` named `insurer_{policy_tier}.pdf`.
   - **Output**: Structured JSON policy data in `data/policies/processed/` named `insurer_{policy_tier}.json`.

6. **Data Generation Scripts**
   - **Component**: `scripts/data_generation/generate_personalities.py`
   - **Purpose**: Generates a list of common customer service personality types using the Gemini API (`gemini-2.5-pro-preview-03-25`).
   - **Output**: Saves a validated JSON file to `data/transcripts/personalities.json`. See the script's docstring for usage details.
   - **Component**: `scripts/data_generation/generate_transcripts.py`
   - **Purpose**: Generates synthetic conversation transcripts using the Gemini API (`gemini-2.5-pro-exp-03-25`), combining personalities from `personalities.json` and requirements from `coverage_requirements.py`. Can optionally use scenario files (`data/scenarios/`).
   - **Output**: Saves structured JSON transcripts to `data/transcripts/raw/synthetic/`. Filenames follow the format `transcript_{scenario_name_or_no_scenario}_{uuid}.json`. Accepts `-n` and `-s` arguments. See the script's docstring for details.

7. **Policy Comparison Report Generation (Insurer-Level)**
   - **Component**: `scripts/generate_policy_comparison.py`
   - **Purpose**: Generates detailed Markdown reports comparing extracted customer requirements against all tiers for each available insurer, recommending the best tier per insurer.
   - **Input**: Customer UUID (`--customer_id`), requirements JSON (`data/extracted_customer_requirements/requirements_*_{uuid}.json`), processed policy JSONs (`data/policies/processed/`), and tier rankings (`data/policies/pricing_tiers/tier_rankings.py`).
   - **Output**: Saves Markdown reports to `results/{uuid}/policy_comparison_report_{insurer}_{uuid}.md`. Each report includes the recommendation, justification, detailed requirement analysis, and summary. See the script's docstring for more details.

8. **Final Recommendation Report Generation**
   - **Component**: `scripts/generate_recommendation_report.py`
   - **Purpose**: Generates the final customer-facing recommendation report by parsing comparison reports, applying scoring, and using an LLM for re-ranking and justification.
   - **Input**: Customer UUID (`--customer_id`), which determines the directory (`results/{uuid}/`) containing the comparison reports (`policy_comparison_report_*.md`).
   - **Output**: Saves the final Markdown report to `results/{uuid}/recommendation_report_{uuid}.md`. See the script's docstring for more details.

9. **Evaluation Scripts**
   - **Transcript Evaluation**: See Section 4.1 above.
   - **PDF Extraction Evaluation**:
     - **Component**: `scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py`
     - **Purpose**: Compares processed policy JSON against the source PDF for accuracy using a multi-modal LLM.
     - **Input**: Processed policy JSONs (`data/policies/processed/`) and raw PDFs (`data/policies/raw/`). Use `--file_pattern` to filter inputs.
     - **Output**: Evaluation JSON results in `data/evaluation/pdf_extraction_evaluations/`. See Section 4.2 above for usage examples.

## Technical Stack

- **Python**: Primary programming language
- **Google Gemini & OpenAI**: LLMs for natural language processing (Gemini via `LLMService`, OpenAI via `crewai` for Extractor)
- **CrewAI**: Framework for multi-agent orchestration (used by Extractor)
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
   GOOGLE_API_KEY="your_google_api_key_here"
   OPENAI_API_KEY="your_openai_api_key_here"
   # OPENAI_MODEL_NAME="gpt-4o" # Optional: Defaults to gpt-4o if not set
   ```
4. Explore the notebooks in the `notebooks/` directory.
5. Check out the LLM service tutorial: `python tutorials/llm_service_tutorial.py`.
6. Run the Extractor agent (ensure transcript exists):
   ```bash
    # Example using a processed transcript (replace with actual filename)
    python src/agents/extractor.py data/transcripts/processed/parsed_transcript_golf_coverage_6aef8846-aed1-4a6e-8115-d5ca7d6d0abf.json

6. Run the Policy Comparison script (replace UUID with actual):
   ```bash
   python scripts/generate_policy_comparison.py --customer_id 6aef8846-aed1-4a6e-8115-d5ca7d6d0abf
   ```

7. Run the Final Recommendation script (replace UUID with actual):
   ```bash
   python scripts/generate_recommendation_report.py --customer_id 6aef8846-aed1-4a6e-8115-d5ca7d6d0abf
   ```

8. Run Evaluation Scripts (Examples):
   ```bash
   # Evaluate a transcript
   python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --transcript data/transcripts/raw/synthetic/transcript_golf_coverage_6aef8846-aed1-4a6e-8115-d5ca7d6d0abf.json

   # Evaluate PDF extraction for a specific policy
   python scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py --file_pattern "fwd_{Premium}.json"
   ```

## Academic Project

This is an academic project focused on applying multi-agent AI systems to solve real-world problems in the insurance domain.
