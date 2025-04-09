import argparse
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add src directory to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

try:
    from src.models.llm_service import LLMService
except ImportError:
    print("Error: Could not import LLMService. Ensure src is in the Python path.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
POLICY_DIR = project_root / "data" / "policies" / "processed"
RESULTS_DIR = project_root / "results"
LLM_MODEL = "gemini-2.5-pro-preview-03-25"  # As specified by user
BATCH_SIZE = 5

# Note: Placeholders like {{Policy Source Info}} are escaped with double braces
# so they are ignored by the f-string formatting but passed to the LLM.
PROMPT_TEMPLATE_BASE = """
**Role:** You are an expert insurance policy analyst. Your task is to compare a customer's insurance requirements against a specific insurance policy tier and generate a detailed comparison report in Markdown format.

**Inputs:**

1.  **Customer Requirements JSON:**
    ```json
    {customer_req_str}
    ```
2.  **Policy Document JSON ({provider_cap} - {tier_cap} Tier):**
    ```json
    {policy_doc_str}
    ```

**Instructions:**

1.  **Identify Core Requirements:** Focus on the values listed in the `insurance_coverage_type` array within the Customer Requirements JSON.
2.  **Compare Against Policy:** For each requirement in `insurance_coverage_type`, search the Policy Document JSON for matching or relevant coverages. Look primarily at `coverage_name` but also consider `details` and `category_name` for relevance.
3.  **Generate Markdown Report:** Structure the output exactly as follows:

    ```markdown
    # Policy Comparison Report: {provider_cap} - {tier_cap} vs. Customer Requirements ({customer_id})

    This report compares the customer's stated insurance requirements against the {provider_cap} {tier_cap} travel insurance policy.

    ## Customer Requirement: [Requirement Name 1]

    ### Policy Coverage Match(es)

    *   **Coverage Name:** [Matched Policy Coverage Name 1]
        *   **Category:** [Policy Category Name]
        *   **Limits:**
            *   [Limit Type 1]: [Limit Value 1] ([Basis 1, if any])
            *   [Limit Type 2]: [Limit Value 2] ([Basis 2, if any])
            *   ... (List all limits for this coverage)
        *   **Details:** [Policy Coverage Details]
        *   **Source:** [{{Policy Source Info}}, {provider_cap}_{tier_cap} document]

    *   **Coverage Name:** [Matched Policy Coverage Name 2 (if multiple matches)]
        *   **Category:** ...
        *   **Limits:** ...
        *   **Details:** ...
        *   **Source:** [{{Policy Source Info}}, {provider_cap}_{tier_cap} document]
        *   ... (Include all relevant matches)

    ### Match Certainty

    *   **Certainty:** [Certain / Uncertain]
    *   **Justification:** [Explain why the match is certain or uncertain. Consider semantic similarity, keyword overlap, and context provided in 'details'. If uncertain, explain the ambiguity.]

    ---

    ## Customer Requirement: [Requirement Name 2]

    ### Policy Coverage Match(es)

    *   ... (Details as above)

    ### Match Certainty

    *   **Certainty:** [Certain / Uncertain]
    *   **Justification:** ...

    ---

    ... (Repeat for all requirements in `insurance_coverage_type`)

    ## Summary of Unmatched Requirements

    *   [List any customer requirements from `insurance_coverage_type` for which NO relevant policy coverage was found. If all requirements have at least one potential match, state "All customer requirements had at least one potential policy coverage match identified."]
    ```

4.  **Formatting Notes:**
    *   Ensure the output is valid Markdown.
    *   Use the exact section titles provided (e.g., "Policy Coverage Match(es)", "Match Certainty").
    *   Format the `Source` line exactly as: `[{{Policy Source Info}}, {provider_cap}_{tier_cap} document]`. Replace `{{Policy Source Info}}` with the value from the JSON, and `{provider_cap}_{tier_cap}` with the actual provider and tier names. (Note: This instruction is for the LLM).
    *   If no matches are found for a requirement, state "No relevant policy coverage found." under "Policy Coverage Match(es)" and explain the lack of match under "Match Certainty".
    *   Handle multiple policy coverages matching a single requirement by listing all of them under "Policy Coverage Match(es)".
    *   Be concise but thorough in the `Details` and `Justification`.
    *   For the 'Limits' section, iterate through the 'limits' array in the policy JSON and list each limit clearly. If 'basis' is null or empty, omit it.
"""


def parse_requirements_filename(filename: str) -> Tuple[str, str]:
    """Extracts customer_id and timestamp from the requirements filename."""
    # Example: requirements_the_confused_novice_20250403_175921.json
    match = re.match(r"requirements_(.+)_(\d{8}_\d{6})\.json", filename)
    if match:
        customer_id = match.group(1)
        timestamp = match.group(2)
        return customer_id, timestamp
    else:
        logger.warning(
            f"Could not parse customer ID and timestamp from {filename}. Using defaults."
        )
        return "unknown_customer", "unknown_timestamp"


def parse_policy_filename(filename: str) -> Tuple[str, str]:
    """Extracts provider and tier from the policy filename."""
    # Example: fwd_{Business}.json
    match = re.match(r"([^_]+)_\{([^}]+)\}\.json", filename)
    if match:
        provider = match.group(1)
        tier = match.group(2)
        return provider, tier
    else:
        logger.warning(
            f"Could not parse provider and tier from {filename}. Using defaults."
        )
        # Attempt fallback for filenames without {}
        parts = filename.replace(".json", "").split("_")
        if len(parts) >= 2:
            return parts[0], "_".join(parts[1:])
        return "unknown_provider", "unknown_tier"


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Loads data from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {file_path}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {file_path}: {e}")
        raise


async def generate_report(
    llm_service: LLMService,
    customer_req_data: Dict[str, Any],
    policy_file_path: Path,
    customer_id: str,
    output_dir: Path,
    timestamp: str,
) -> None:
    """Generates and saves a single policy comparison report."""
    policy_filename = policy_file_path.name
    provider, tier = parse_policy_filename(policy_filename)
    logger.info(f"Processing policy: {provider} - {tier}")

    prompt = ""  # Initialize prompt variable outside try block
    try:
        policy_data = load_json_file(policy_file_path)

        # Prepare data for formatting
        customer_req_str = json.dumps(customer_req_data, indent=2)
        policy_doc_str = json.dumps(policy_data, indent=2)
        provider_cap = provider.capitalize()
        tier_cap = tier.capitalize()
        # Extract summary and description safely using .get()
        req_summary = customer_req_data.get("requirement_summary", "Not provided")
        req_description = customer_req_data.get("detailed_description", "Not provided")

        # --- Start: Added specific error handling for prompt formatting ---
        try:
            # Format the prompt using f-string
            prompt = f"""
**Role:** You are an expert insurance policy analyst. Your task is to compare a customer's insurance requirements against a specific insurance policy tier and generate a detailed comparison report in Markdown format.

**Inputs:**

1.  **Customer Requirements JSON:**
    ```json
    {customer_req_str}
    ```
2.  **Policy Document JSON ({provider_cap} - {tier_cap} Tier):**
    ```json
    {policy_doc_str}
    ```

**Instructions:**

1.  **Identify Core Requirements:** Focus on the values listed in the `insurance_coverage_type` array within the Customer Requirements JSON.
2.  **Compare Against Policy:** For each requirement in `insurance_coverage_type`, search the Policy Document JSON for matching or relevant coverages. Look primarily at `coverage_name` but also consider `details` and `category_name` for relevance.
3.  **Generate Markdown Report:** Structure the output exactly as follows:

    ```markdown
    # Policy Comparison Report: {provider_cap} - {tier_cap} vs. Customer Requirements ({customer_id})

    This report compares the customer's stated insurance requirements against the {provider_cap} {tier_cap} travel insurance policy.

    ## Customer Requirement Summary

    {req_summary}

    ## Detailed Customer Description

    {req_description}

    ---

    ## Customer Requirement: [Requirement Name 1]

    ### Policy Coverage Match(es)

    *   **Coverage Name:** [Matched Policy Coverage Name 1]
        *   **Category:** [Policy Category Name]
        *   **Limits:**
            *   [Limit Type 1]: [Limit Value 1] ([Basis 1, if any])
            *   [Limit Type 2]: [Limit Value 2] ([Basis 2, if any])
            *   ... (List all limits for this coverage)
        *   **Details:** [Policy Coverage Details]
        *   **Source:** [{{Policy Source Info}}, {provider_cap}_{tier_cap} document]

    *   **Coverage Name:** [Matched Policy Coverage Name 2 (if multiple matches)]
        *   **Category:** ...
        *   **Limits:** ...
        *   **Details:** ...
        *   **Source:** [{{Policy Source Info}}, {provider_cap}_{tier_cap} document]
        *   ... (Include all relevant matches)

    ### Match Certainty

    *   **Certainty:** [Certain / Uncertain]
    *   **Justification:** [Explain why the match is certain or uncertain. Consider semantic similarity, keyword overlap, and context provided in 'details'. If uncertain, explain the ambiguity.]

    ---

    ## Customer Requirement: [Requirement Name 2]

    ### Policy Coverage Match(es)

    *   ... (Details as above)

    ### Match Certainty

    *   **Certainty:** [Certain / Uncertain]
    *   **Justification:** ...

    ---

    ... (Repeat for all requirements in `insurance_coverage_type`)

    ## Summary of Unmatched Requirements

    *   [List any customer requirements from `insurance_coverage_type` for which NO relevant policy coverage was found. If all requirements have at least one potential match, state "All customer requirements had at least one potential policy coverage match identified."]
    ```

4.  **Formatting Notes:**
    *   Ensure the output is valid Markdown.
    *   Use the exact section titles provided (e.g., "Policy Coverage Match(es)", "Match Certainty").
    *   Format the `Source` line exactly as: `[{{Policy Source Info}}, {provider_cap}_{tier_cap} document]`. Replace `{{Policy Source Info}}` with the value from the JSON, and `{provider_cap}_{tier_cap}` with the actual provider and tier names. (Note: This instruction is for the LLM).
    *   If no matches are found for a requirement, state "No relevant policy coverage found." under "Policy Coverage Match(es)" and explain the lack of match under "Match Certainty".
    *   Handle multiple policy coverages matching a single requirement by listing all of them under "Policy Coverage Match(es)".
    *   Be concise but thorough in the `Details` and `Justification`.
    *   For the 'Limits' section, iterate through the 'limits' array in the policy JSON and list each limit clearly. If 'basis' is null or empty, omit it.
"""
        except KeyError as ke:
            logger.error(
                f"KeyError during prompt formatting for {policy_filename}: Missing key {ke}"
            )
            logger.exception("Traceback for prompt formatting KeyError:")
            return  # Stop processing this report if prompt formatting fails
        except Exception as fmt_e:
            logger.error(
                f"Unexpected error during prompt formatting for {policy_filename}: {fmt_e}"
            )
            logger.exception("Traceback for prompt formatting error:")
            return  # Stop processing this report
        # --- End: Added specific error handling for prompt formatting ---

        # Generate content using LLMService
        # Note: generate_content expects 'prompt' or 'contents'. We use 'prompt'.
        logger.debug(f"Attempting LLM call for {policy_filename}")
        response = await asyncio.to_thread(
            llm_service.generate_content,
            prompt=prompt,
            model=LLM_MODEL,
            # Add other parameters if needed, e.g., max_output_tokens
        )

        # Extract the generated text
        report_content = response.text

        # Define output filename
        output_filename = (
            f"policy_comparison_{provider}_{tier}_{customer_id}_{timestamp}.md"
        )
        output_path = output_dir / output_filename

        # Save the report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.info(f"Successfully generated report: {output_path.name}")

    except Exception as e:
        # --- Start: Added more detailed logging for general exceptions ---
        import traceback

        logger.error(
            f"Failed to generate report for {policy_filename}. Error Type: {type(e).__name__}, Message: {e}"
        )
        # Log traceback for unexpected errors during LLM call or file writing
        if not isinstance(
            e, KeyError
        ):  # Avoid logging traceback again if it was already logged above
            logger.exception("Traceback for report generation error:")
        # --- End: Added more detailed logging for general exceptions ---


async def main(requirements_file: str):
    """Main function to orchestrate report generation."""
    req_path = Path(requirements_file)
    if not req_path.is_file():
        logger.error(f"Requirements file not found: {requirements_file}")
        sys.exit(1)

    # Parse requirements filename
    customer_id, timestamp = parse_requirements_filename(req_path.name)

    # Create output directory
    output_dir = RESULTS_DIR / f"{customer_id}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Load requirements data
    try:
        customer_req_data = load_json_file(req_path)
        # Ensure the specific key exists if needed, e.g., customer_req_data['json_dict']
        # Adjust based on actual structure if the read_file result showed nesting
        if "json_dict" in customer_req_data:
            customer_req_data_for_prompt = customer_req_data["json_dict"]
        else:
            customer_req_data_for_prompt = (
                customer_req_data  # Assume flat structure if no json_dict
            )

    except Exception as e:
        logger.error(f"Failed to load requirements data: {e}")
        sys.exit(1)

    # Discover policy files
    policy_files = list(POLICY_DIR.glob("*.json"))
    if not policy_files:
        logger.error(f"No policy JSON files found in {POLICY_DIR}")
        sys.exit(1)
    logger.info(f"Found {len(policy_files)} policy files to process.")

    # Initialize LLM Service
    try:
        # Assuming API key is handled by GeminiConfig or environment variables
        llm_service = LLMService()
    except Exception as e:
        logger.error(f"Failed to initialize LLM Service: {e}")
        sys.exit(1)

    # Process policies in batches
    for i in range(0, len(policy_files), BATCH_SIZE):
        batch = policy_files[i : i + BATCH_SIZE]
        logger.info(f"Processing batch {i // BATCH_SIZE + 1}...")

        tasks = [
            generate_report(
                llm_service,
                customer_req_data_for_prompt,  # Pass the potentially nested data
                policy_file,
                customer_id,
                output_dir,
                timestamp,
            )
            for policy_file in batch
        ]
        await asyncio.gather(*tasks)
        logger.info(f"Batch {i // BATCH_SIZE + 1} completed.")

    logger.info("All reports generated successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate policy comparison reports based on customer requirements."
    )
    parser.add_argument(
        "requirements_file",
        type=str,
        help="Path to the customer requirements JSON file.",
    )
    args = parser.parse_args()

    asyncio.run(main(args.requirements_file))
