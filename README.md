# Aegis AI: Simplifying Travel Insurance with Intelligent Recommendations

Navigating the complexities of travel insurance is a major consumer headache, leading to confusion and suboptimal choices.  

This project tackles that challenge head-on with an intelligent workflow powered by Large Language Models (LLMs). We automate the heavy lifting – extracting critical data from dense policy documents and simulated customer interactions – enabling rapid, data-driven comparison and the generation of personalized, justified recommendations. 

This README outlines the workflow consisting of structured data extraction, automated analysis, and rigorous evaluation which unlocks unprecedented efficiency and transparency in insurance selection, paving the way for smarter, unbiased, and transparent recommendations.

The user-facing application for this system is named **Aegis AI**. The name draws inspiration from mythology: the Aegis was the legendary shield of protection carried by Zeus and Athena. This name reflects the project's goal of providing robust protection (like the shield) through intelligent, modern solutions (AI).

## Getting Started

Follow these steps to set up the project environment for running the backend scripts:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/DesmondChoy/mtech-policy-recsys
    cd mtech-policy-recsys
    ```

2.  **Set Up Python Environment**:
    This project requires **Python 3.11 or 3.12** due to specific dependencies (as noted in `pyproject.toml`). Please ensure you have a compatible version installed.

    It's highly recommended to use a virtual environment.

    ### Creating and Activating a Virtual Environment

    **For Windows Users:**

    To create a virtual environment named `.venv` using Python 3.11 (replace `3.11` with your desired version if needed):
    ```bash
    py -3.11 -m venv .venv
    ```
    To activate the virtual environment:
    ```bash
    .venv\Scripts\activate
    ```

    **For macOS and Linux Users:**

    To create a virtual environment named `venv` using Python 3.11 (replace `python3.11` with the command that invokes Python 3.11 on your system if needed):
    ```bash
    python3.11 -m venv venv
    ```
    To activate the virtual environment:
    ```bash
    source venv/bin/activate
    ```

Once the virtual environment is activated, install the Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up API Keys**:
    Create a `.env` file in the project root and add your API keys required for LLM interactions:
    ```dotenv
    GOOGLE_API_KEY="your_google_api_key_here"
    OPENAI_API_KEY="your_openai_api_key_here"
    # OPENAI_MODEL_NAME="gpt-4o" # Optional: Defaults to gpt-4o if not set for CrewAI/Extractor
    ```

    - [Documentation](https://ai.google.dev/gemini-api/docs/api-key) to get GOOGLE_API_KEY
    - [Documentation](https://help.openai.com/en/articles/8867743-assign-api-key-permissions) to get OPENAI_API_KEY



4.  **Install Node.js Dependencies (Optional - for Local Frontend Development)**:
    This project includes a frontend web application component (`ux-webapp/`). **This step is optional** as the application is already deployed and accessible online (see "Online Access" section below).

    If you wish to run or develop the frontend *locally*, navigate to the `ux-webapp/` directory and install the required Node.js dependencies:
    ```bash
    cd ux-webapp
    npm install
    cd .. 
    ```
    *Note: Ensure you have Node.js and npm installed if performing this optional step.*

## Online Access (Aegis AI Web Interface)

The user-friendly **Aegis AI** web application is deployed and accessible online at:
[https://aegis-recsys.netlify.app/](https://aegis-recsys.netlify.app/)

You can use this link to explore the Aegis AI interface and functionality without needing to run the backend scripts or frontend locally.

## How to Run the Demo Workflow (Backend)

For a quick way to see the entire backend recommendation system workflow in action, use the dedicated demo script. This script runs all the main steps automatically and creates a summary report showing what happened.

**1. Basic Run (No Specific Scenario):**

This command runs the workflow without focusing on a specific pre-defined test case. It will generate a conversation, process it, compare policies, and create a recommendation, but it will skip evaluations that require a specific scenario.

```bash
python scripts/run_recsys_demo.py
```

**2. Run with a Specific Scenario:**

You can test the system with specific situations (scenarios). Replace `<scenario_name>` with one of the available scenarios.

```bash
python scripts/run_recsys_demo.py --scenario <scenario_name>
```

*   **Available Scenarios:** `pet_care_coverage`, `golf_coverage`, `public_transport_double_cover`, `uncovered_cancellation_reason`
*   **Optional Flag:** You can add `--skip_scenario_eval` at the end of the command (even if you provided a scenario) to specifically skip the final scenario-based evaluation step if needed.

**What Happens When You Run It?**

*   The script creates a unique ID (UUID) for this specific run.
*   It simulates a customer conversation (or uses the specified scenario).
*   It processes the conversation, extracts needs, compares policies, and generates a final recommendation.
*   It performs various quality checks and evaluations along the way.
*   **Most importantly:** It creates a summary file named `demo_summary_{uuid}.md` in the main project folder.

**Important Cost Note:** Running this demo script involves multiple calls to LLM APIs. Expect approximate costs of **USD $3** for Google Gemini API usage and **a few cents (USD)** for OpenAI API usage per run. Costs may vary based on API pricing changes and specific run complexity.

**Checking the Results:**

*   Look for the `demo_summary_... .md` file in the project's main directory after the script finishes.
*   Open this file to see the status of each step, links to output files (transcript, requirements, comparisons, recommendation), and any errors.

## System Overview
![NUS-project-diagram](https://github.com/DesmondChoy/mtech-policy-recsys/blob/e9aa2d7457650b1c6f675494213e18a724735b60/data/architecture.jpg)

## Key Features

*   **Automated Data Extraction**: Uses LLMs to extract structured data from policy PDFs and customer transcripts.
*   **Scenario-Driven Generation**: Creates realistic synthetic transcripts based on defined scenarios and personalities.
*   **Agent-Based Requirement Extraction**: Employs a CrewAI agent to identify and structure customer needs.
*   **LLM-Powered Comparison & Recommendation**: Generates detailed policy comparisons and justified final recommendations.
*   **Multi-faceted Evaluation**: Includes steps to evaluate transcript quality, extraction accuracy, and recommendation relevance against ground truth data.
*   **Aegis AI Web Interface**: Provides an optional, user-friendly interface (deployed online) for exploring results.

## Command-Line Usage (Individual Scripts)

This section outlines the key commands for running individual parts of the system if you don't want to use the full demo script.

### Setup & Preparation

1.  **Extract Policy Data**: Process policy PDFs into structured JSON.
    ```bash
    # Process a specific policy PDF
    python scripts/extract_policy_tier.py --pdf_path data/policies/raw/fwd_Premium.pdf --output_dir data/policies/processed/

    # Process all policy PDFs in the raw directory
    python scripts/extract_policy_tier.py
    ```

2.  **Generate Personalities** (Optional): Create personality profiles for transcript generation.
    ```bash
    python scripts/data_generation/generate_personalities.py
    ```

### Core Workflow Steps

3.  **Generate Synthetic Transcripts**: Create conversation data.
    ```bash
    # Generate 5 general transcripts
    python scripts/data_generation/generate_transcripts.py -n 5

    # Generate 3 transcripts for a specific scenario (e.g., golf_coverage)
    # Available scenarios: golf_coverage, pet_care_coverage, public_transport_double_cover, uncovered_cancellation_reason
    python scripts/data_generation/generate_transcripts.py -n 3 -s golf_coverage
    ```

4.  **Parse Transcripts**: Convert raw transcripts to a standard processed format.
    ```bash
    python src/utils/transcript_processing.py
    ```

5.  **Extract Requirements**: Use the CrewAI agent to extract needs from processed transcripts.
    ```bash
    python src/agents/extractor.py
    ```

6.  **Generate Policy Comparison Reports**: Compare extracted requirements against processed policies.
    ```bash
    # Generate comparison reports for a specific customer UUID
    python scripts/generate_policy_comparison.py --customer_id <customer_uuid>
    ```

7.  **Generate Final Recommendation**: Create the final recommendation report based on comparisons.
    ```bash
    # Generate recommendation for a specific customer UUID
    python scripts/generate_recommendation_report.py --customer_id <customer_uuid>

    # Force overwrite of existing recommendation
    python scripts/generate_recommendation_report.py --customer_id <customer_uuid> --overwrite
    ```

### Evaluation Tools

8.  **Evaluate Transcripts**: Check the quality of generated transcripts.
    ```bash
    # Evaluate a single transcript
    python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --transcript <path_to_raw_transcript.json>

    # Evaluate all transcripts in the raw synthetic directory
    python scripts/evaluation/transcript_evaluation/eval_transcript_main.py --directory data/transcripts/raw/synthetic/
    ```

9.  **Evaluate PDF Extraction**: Verify the accuracy of policy data extraction.
    ```bash
    # Evaluate all processed policy JSON files
    python scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py

    # Evaluate only specific policies (using file pattern)
    python scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py --file_pattern "fwd_*.json"
    ```

10. **Evaluate Recommendation Coverage (vs. Ground Truth)**: Check how well the recommended policy covers individual requirements.
    ```bash
    # Evaluate coverage for all customers
    python scripts/generate_ground_truth_coverage.py

    # Evaluate coverage for a specific customer UUID with debug output
    python scripts/generate_ground_truth_coverage.py --customer <customer_uuid> --debug 
    ```

11. **Evaluate Scenario Recommendations (vs. Ground Truth)**: Check if the final recommendation matches the expected outcome for a test scenario.
    ```bash
    # Evaluate recommendations for a specific scenario
    python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py --scenario golf_coverage

    # Evaluate recommendations for all scenarios
    python scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py
    ```

12. **Calculate Scenario Pass Rates**: Summarize scenario evaluation results.
    ```bash
    python scripts/calculate_scenario_pass_rates.py
    ```

### End-to-End Workflow (Orchestrator)

13. **Run Complete Pipeline (Alternative to Demo Script)**:
    The `scripts/orchestrate_scenario_evaluation.py` script automates the workflow for *multiple* transcripts per scenario, useful for broader testing.
    ```bash
    # Run the full workflow with 5 transcripts per scenario
    python scripts/orchestrate_scenario_evaluation.py -n 5

    # Skip transcript evaluation for faster processing
    python scripts/orchestrate_scenario_evaluation.py -n 5 --skip_transcript_eval

    # Only run the final evaluation aggregation step on existing results
    python scripts/orchestrate_scenario_evaluation.py --only_aggregate
    ```
    *   **Arguments**: `-n` (num transcripts), `--skip_transcript_eval`, `--only_aggregate`.
    *   **Output**: Creates intermediate files and final reports. Aggregated scenario evaluation results saved in `data/evaluation/scenario_evaluation/`.

### Running the Web Interface Locally (Optional)

If you completed the optional Node.js setup in "Getting Started":

1. **Start the Development Server**:
   ```bash
   cd ux-webapp
   npm run dev
   ```
   Then open your browser to the displayed URL (typically http://localhost:5173).

2. **Build for Production** (Optional):
   ```bash
   cd ux-webapp
   npm run build
   ```
   This creates optimized files in the `ux-webapp/dist` directory.

## Technical Stack

- **Python**: Primary programming language for backend logic and data processing.
- **Google Gemini & OpenAI**: Large Language Models used for various tasks like data generation, extraction, comparison, and evaluation.
- **CrewAI**: Framework used for the requirement extraction agent.
- **React & Material UI**: Used for building the frontend web application.
- **Pydantic**: Used for data validation and defining structured schemas.
- **NLTK**: Used for text preprocessing in embedding utilities.

## Future Enhancements

The current system provides a robust foundation. Future work could include:

- **Functional Feedback System**: Implementing the backend logic to actually collect and process user feedback submitted through the **Aegis AI** web interface.
- **Advanced Orchestration**: Developing a more sophisticated workflow management system beyond the current script-based orchestration.
- **Machine Learning Insights**: Training ML models on the generated data (requirements, recommendations) to uncover deeper insights.
- **Iterative Refinement**: Allowing users to update their needs within the **Aegis AI** web interface and receive refined recommendations.

## Academic Project

This is an academic project focused on applying AI and LLM techniques to solve real-world problems in the insurance domain.
