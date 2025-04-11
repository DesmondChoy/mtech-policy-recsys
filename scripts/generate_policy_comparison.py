"""
Generates insurer-level policy comparison reports.

This script takes a customer UUID, finds the corresponding extracted requirements JSON,
identifies all available insurers and their processed policy tiers, and then uses
an LLM to generate a comparison report for each insurer.

The comparison analyzes all tiers for a single insurer against the customer's
requirements in one LLM call, selects the best tier based on holistic fit and
price ranking, provides justification, performs a detailed requirement-by-requirement
analysis for the recommended tier, and includes a summary of strengths/weaknesses.

Prerequisites:
- Customer requirements must be extracted into JSON files in
  `data/extracted_customer_requirements/` with the format `requirements_*_{uuid}.json`.
- Processed policy tier data must exist as JSON files in
  `data/policies/processed/` with the format `{insurer}_{tier}.json`.
- Insurer tier price rankings must be defined in
  `data/policies/pricing_tiers/tier_rankings.py` in the `INSURER_TIER_RANKING` dict.
- `LLMService` must be configured (e.g., API key via environment variable).

Usage:
    python scripts/generate_policy_comparison.py --customer_id <customer_uuid>

Example:
    python scripts/generate_policy_comparison.py --customer_id 49eb20af-32b0-46e0-a14e-0dbe3e3c6e73

Output:
- Markdown reports are saved to `results/{customer_uuid}/policy_comparison_report_{insurer}_{customer_uuid}.md`.
"""

import argparse
import asyncio
import json
import logging
import os
import glob
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict

# Add src directory to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

try:
    from src.models.llm_service import LLMService

    # Attempt to import the tier ranking
    from data.policies.pricing_tiers.tier_rankings import INSURER_TIER_RANKING
except ImportError as e:
    print(
        f"Error: Could not import required modules: {e}. Ensure src is in the Python path and tier_rankings.py exists."
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
REQUIREMENTS_DIR = project_root / "data" / "extracted_customer_requirements"
POLICY_DIR = project_root / "data" / "policies" / "processed"
RESULTS_DIR = project_root / "results"
# LLM_MODEL can be handled by LLMService default config

# --- New Prompt Template for Insurer-Level Analysis ---
PROMPT_TEMPLATE_INSURER = """
# Role: Travel Insurance Policy Advisor

# Goal:
1. Analyze the provided customer requirements against all available travel insurance policy tiers for the specified insurer ({insurer_name}).
2. Select the SINGLE most suitable tier for this customer based on a holistic assessment and price tie-breaking.
3. Provide a clear justification for your choice.
4. Provide a detailed breakdown of how the *recommended tier* covers each specific customer requirement, using granular data from the policy JSON.

# Customer Requirements:
```json
{customer_requirements_json}
```

# Insurer: {insurer_name}

# Available Policy Tiers for {insurer_name}:

Below are the details for each available policy tier from {insurer_name}. Analyze each one against the customer requirements.

{policy_tiers_details_str}

# Tier Price Ranking (Cheapest to Most Expensive):
{tier_ranking_list}

# Analysis and Recommendation Task:

1.  **Holistic Analysis:** For each policy tier listed above, analyze how well it meets the customer's requirements *as a whole*. Consider all aspects of the requirements and the corresponding coverage details in each tier.
2.  **No Mix-and-Match Rule:** Understand that the customer must choose one complete tier; coverages *cannot* be mixed and matched between different tiers. Factor this rule into your analysis and justification.
3.  **Select Single Best Tier:** Based on your holistic analysis, identify the *single* policy tier from {insurer_name} that provides the best overall fit for the customer's stated requirements.
4.  **Tie-Breaking Rule:** If multiple tiers appear equally suitable after your holistic analysis, you MUST select the tier that appears earliest in the provided 'Tier Price Ranking' list (i.e., the cheapest among the equally suitable options).
5.  **Justification:** Provide a clear and concise justification for your chosen tier. Explain *why* it is the most suitable option compared to the others. If the tie-breaking rule was used, explicitly mention this and explain why the tied tiers were considered equally suitable before applying the price ranking.
6.  **Detailed Coverage Analysis (for Recommended Tier ONLY):**
            *   After providing the justification, create a new section titled: `## Detailed Coverage Analysis for Recommended Tier`.
            *   Inside this section, iterate through *each requirement* listed in the customer's `insurance_coverage_type` array.
            *   For each customer requirement, create a subsection: `### Requirement: {{Requirement Name}}`.
            *   Within this subsection, detail exactly how the *recommended tier* covers this specific requirement. You MUST extract and present the relevant information directly from the recommended tier's JSON data provided earlier. Include:
                *   The specific `coverage_name`(s) from the policy that match the requirement.
        *   All associated `base_limits` (limit_type, value, basis).
        *   Any applicable `conditional_limits` (condition, limit_type, value, basis, source).
        *   Crucially, include *all* relevant `source_specific_details` (detail_snippet, source_description, page_number, section_number). **Do not summarize or omit these details.**
    *   **Formatting Example (Positive):**
        ```markdown
        ### Requirement: Medical Expenses
        *   **Policy Coverage:** Overseas Medical Expenses
            *   **Base Limits:**
                *   Limit Type: Per Insured Person, Value: $500,000
            *   **Source Specific Details:**
                *   Detail: Covers necessary medical treatment overseas. Source: Policy Wording, Page: 15, Section: 3.1
                *   Detail: Includes hospital charges and surgical fees. Source: Policy Wording, Page: 16, Section: 3.1a
        *   **Policy Coverage:** Emergency Medical Evacuation
            *   **Base Limits:**
                *   Limit Type: Per Insured Person, Value: Unlimited
            *   **Conditional Limits:**
                *   Condition: If approved by emergency assistance provider, Limit Type: Per Event, Value: $1,000, Source: Endorsement A, Page: 1, Section: 1
            *   **Source Specific Details:**
                *   Detail: Covers transport to nearest suitable medical facility. Source: Policy Wording, Page: 18, Section: 3.5
        ```
    *   **Formatting Example (Negative/No Coverage):**
        ```markdown
        ### Requirement: Golf Equipment Rental
        *   This requirement is not explicitly covered under the {{Recommended Tier Name}} tier based on the provided policy details.
        ```
    *   **Formatting Example (Incorrect - Missing Details):**
        ```markdown
        ### Requirement: Medical Expenses
        *   **Policy Coverage:** Overseas Medical Expenses
            *   **Base Limits:** $500,000
            *   **Source Specific Details:** Covers necessary medical treatment overseas.
        *   **Policy Coverage:** Emergency Medical Evacuation
            *   **Base Limits:** Unlimited
            *   **Source Specific Details:** Covers transport to nearest suitable medical facility.
        ```
        *(This example is INCORRECT because it omits the limit types, basis, conditional limits, and specific source details like page/section numbers. You MUST include all available granular details.)*
    *   If no relevant coverage is found in the recommended tier for a specific customer requirement, clearly state that.
7.  **Summary of Strengths/Weaknesses (for Recommended Tier ONLY):**
    *   After the detailed coverage analysis, create a final section titled: `## Summary for Recommended Tier`.
    *   Provide a brief, balanced summary (e.g., 2-3 bullet points for strengths, 2-3 for weaknesses/gaps) highlighting the most important ways the *recommended tier* aligns well with the customer's key requirements, and any significant areas where it falls short or doesn't provide coverage based on the requirements. This summary should help in comparing this tier against recommendations from other insurers.

# Output Format:
Provide your response in Markdown format using the following structure:
1. Start with the recommended tier name (pre-filled below).
2. Provide your detailed justification (Task 5).
3. Include the detailed coverage analysis section (Task 6).
4. Include the summary section (Task 7).

**Recommended Tier:** :
"""


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


def get_insurer_from_filename(filename: str) -> str | None:
    """Extracts the insurer name from the policy filename (e.g., fwd_First.json -> fwd)."""
    # Match filenames like fwd_First.json, income_Classic.json, sompo_GO Japan!.json
    # Handles potential variations in tier naming (e.g., with spaces, special chars)
    match = re.match(r"^([a-zA-Z0-9]+)_.*\.json$", filename)
    if match:
        return match.group(1).lower()  # Return lower case for consistency
    logger.warning(f"Could not extract insurer name from filename: {filename}")
    return None


async def generate_insurer_report(
    llm_service: LLMService,
    customer_req_data: Dict[str, Any],
    insurer_name: str,
    policy_file_paths: List[Path],
    tier_ranking: List[str],
    customer_id: str,
    output_dir: Path,
) -> None:
    """Generates and saves a single insurer-level comparison report."""
    logger.info(f"Processing insurer: {insurer_name.upper()}")

    policy_tiers_data = []
    for policy_path in policy_file_paths:
        try:
            policy_data = load_json_file(policy_path)
            policy_tiers_data.append(policy_data)
        except Exception:
            logger.error(
                f"Skipping policy file due to loading error: {policy_path.name}"
            )
            continue  # Skip this file if it can't be loaded

    if not policy_tiers_data:
        logger.warning(
            f"No valid policy data loaded for insurer {insurer_name}. Skipping report generation."
        )
        return

    # Format policy tiers for the prompt
    policy_tiers_details_str = ""
    for policy_data in policy_tiers_data:
        tier_name = policy_data.get("tier_name", "Unknown Tier")
        policy_json_str = json.dumps(policy_data, indent=2)
        policy_tiers_details_str += f"--- Policy Tier Start: {tier_name} ---\n"
        policy_tiers_details_str += f"```json\n{policy_json_str}\n```\n"
        policy_tiers_details_str += f"--- Policy Tier End: {tier_name} ---\n\n"

    # Prepare other prompt components
    customer_req_str = json.dumps(customer_req_data, indent=2)
    tier_ranking_str = (
        ", ".join(tier_ranking) if tier_ranking else "No ranking provided"
    )

    prompt = ""  # Initialize prompt
    try:
        # Format the main prompt
        prompt = PROMPT_TEMPLATE_INSURER.format(
            insurer_name=insurer_name.upper(),
            customer_requirements_json=customer_req_str,
            policy_tiers_details_str=policy_tiers_details_str.strip(),
            tier_ranking_list=tier_ranking_str,
        )

        logger.debug(f"Attempting LLM call for insurer {insurer_name}")
        # Use asyncio.to_thread if LLMService call is blocking
        response = await asyncio.to_thread(
            llm_service.generate_content,
            prompt=prompt,
            # model=LLM_MODEL, # Use default from LLMService config
            # Add other parameters if needed, e.g., max_output_tokens
        )

        report_content = response.text

        # Define output filename including customer_id
        output_filename = f"policy_comparison_report_{insurer_name}_{customer_id}.md"
        output_path = output_dir / output_filename

        # Save the report
        output_dir.mkdir(parents=True, exist_ok=True)  # Ensure dir exists
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.info(f"Successfully generated report: {output_path.name}")

    except KeyError as ke:
        logger.error(
            f"KeyError during prompt formatting for {insurer_name}: Missing key {ke}"
        )
        logger.debug(f"Prompt attempted:\n{prompt[:500]}...")  # Log beginning of prompt
    except Exception as e:
        import traceback

        logger.error(
            f"Failed to generate report for {insurer_name}. Error Type: {type(e).__name__}, Message: {e}"
        )
        logger.exception("Traceback for report generation error:")
        logger.debug(f"Prompt attempted:\n{prompt[:500]}...")  # Log beginning of prompt


async def main(customer_uuid: str):
    """Main function to orchestrate insurer-level report generation."""

    # Find requirements file using UUID, allowing for any scenario prefix
    req_pattern = str(REQUIREMENTS_DIR / f"requirements_*_{customer_uuid}.json")
    matching_req_files = glob.glob(req_pattern)

    if not matching_req_files:
        logger.error(
            f"No requirements file found for customer UUID: {customer_uuid} using pattern: {req_pattern}"
        )
        sys.exit(1)
    if len(matching_req_files) > 1:
        logger.warning(
            f"Multiple requirements files found for customer UUID: {customer_uuid}. Using the first one: {matching_req_files[0]}"
        )
        # Potentially add logic here to choose or error out
    req_path = Path(matching_req_files[0])
    logger.info(f"Using requirements file: {req_path.name}")

    # Create customer-specific output directory using the UUID
    output_dir = RESULTS_DIR / customer_uuid
    # No need to create here, generate_insurer_report will do it.
    logger.info(f"Output directory set to: {output_dir}")

    # Load requirements data
    try:
        customer_req_data = load_json_file(req_path)
    except Exception as e:
        logger.error(f"Failed to load requirements data from {req_path}: {e}")
        sys.exit(1)

    # Discover policy files and group by insurer
    policy_files_by_insurer = defaultdict(list)
    all_policy_files = list(POLICY_DIR.glob("*.json"))

    if not all_policy_files:
        logger.error(f"No policy JSON files found in {POLICY_DIR}")
        sys.exit(1)

    for policy_file in all_policy_files:
        insurer = get_insurer_from_filename(policy_file.name)
        if insurer:
            policy_files_by_insurer[insurer].append(policy_file)

    if not policy_files_by_insurer:
        logger.error("Could not identify any insurers from policy filenames.")
        sys.exit(1)

    logger.info(f"Found policies for insurers: {list(policy_files_by_insurer.keys())}")

    # Initialize LLM Service
    try:
        llm_service = LLMService()
    except Exception as e:
        logger.error(f"Failed to initialize LLM Service: {e}")
        sys.exit(1)

    # Create tasks for each insurer
    tasks = []
    for insurer_name, policy_paths in policy_files_by_insurer.items():
        tier_ranking = INSURER_TIER_RANKING.get(insurer_name)
        if not tier_ranking:
            logger.warning(
                f"No tier ranking found for insurer '{insurer_name}' in tier_rankings.py. Proceeding without ranking."
            )
            tier_ranking = []  # Provide empty list if not found

        tasks.append(
            generate_insurer_report(
                llm_service=llm_service,
                customer_req_data=customer_req_data,
                insurer_name=insurer_name,
                policy_file_paths=policy_paths,
                tier_ranking=tier_ranking,
                customer_id=customer_uuid,  # Pass UUID for logging/reporting if needed
                output_dir=output_dir,
            )
        )

    # Run tasks concurrently
    if tasks:
        logger.info(f"Starting report generation for {len(tasks)} insurers...")
        await asyncio.gather(*tasks)
        logger.info("All insurer reports generation process completed.")
    else:
        logger.info("No tasks to run.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate insurer-level policy comparison reports for a given customer UUID."
    )
    parser.add_argument(
        "--customer_id",  # Keep arg name for consistency, but clarify help text
        type=str,
        required=True,
        help="The unique UUID (e.g., 49eb20af-...) of the customer for whom to generate reports.",
    )
    args = parser.parse_args()

    asyncio.run(main(args.customer_id))  # Pass the UUID from the argument
