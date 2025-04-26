import argparse
import json
import logging
from pathlib import Path
import sys
import re
import glob
import time  # Added for retry delay
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

# Add project root to sys.path to allow importing modules from src
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from src.models.llm_service import LLMService
from data.policies.pricing_tiers.tier_rankings import get_insurer_tier_ranking

"""
Evaluates generated policy comparison reports against source policy PDFs
and customer requirements using a multi-modal LLM.

Purpose:
- Validates the factual accuracy of claims made in the comparison report.
- Assesses the soundness of the report's justifications based on the policy document.
- Checks if the report correctly addresses customer requirements.

Inputs:
- Customer UUID (--uuid): Identifies the specific customer case.
- Insurer Name (--insurer, optional): Specifies which insurer's report section to evaluate. If omitted, evaluates all insurers for the UUID.
- Comparison Report (.md): Located in results/{uuid}/policy_comparison_report_{insurer}_{uuid}.md
- Policy PDF (.pdf): Located in data/policies/raw/{insurer}_{{{recommended_tier}}}.pdf (tier parsed from report) <- Note braces in example
- Customer Requirements (.json): Located in data/extracted_customer_requirements/requirements_{scenario}_{uuid}.json

Output:
- Evaluation Result (.json): Saved to data/evaluation/comparison_report_evaluations/eval_comparison_{insurer}_{uuid}.json
                             Contains detailed validation results per requirement and summary statement,
                             plus an overall PASS/FAIL assessment.

Usage:
Single Insurer:
python scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py --uuid <customer_uuid> --insurer <insurer_name> [--overwrite]

All Insurers for UUID:
python scripts/evaluation/comparison_report_evaluation/eval_comparison_report.py --uuid <customer_uuid> [--overwrite]
"""

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Define Constants ---
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR.parent
SCRIPTS_DIR = EVAL_DIR.parent
PROJECT_ROOT = SCRIPTS_DIR.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"
REQUIREMENTS_DIR = DATA_DIR / "extracted_customer_requirements"
POLICIES_DIR = DATA_DIR / "policies" / "raw"
OUTPUT_DIR = DATA_DIR / "evaluation" / "comparison_report_evaluations"


# --- Pydantic Models ---
class AnalysisItem(BaseModel):
    requirement: str
    report_has_analysis: str  # Yes/No
    found_in_pdf: str  # Yes/No
    pdf_location: str  # Page(s), Section(s) / N/A
    justification_supported_by_pdf: str  # Yes/No/Purchase of add-on required
    validated: bool


class SummaryValidationItem(BaseModel):
    statement: str
    validated: bool
    explanation: str
    pdf_location: str  # Page(s), Section(s) / N/A


class OverallAssessment(BaseModel):
    pass_fail: str  # PASS/FAIL
    explanation: str


class EvaluationResult(BaseModel):
    filename: str
    recommended_tier: str
    analysis: List[AnalysisItem]
    summary_validation: List[SummaryValidationItem]
    overall_assessment: OverallAssessment


# --- Prompt Template ---
# NOTE: Using deferred f-string formatting {{ }} for JSON examples inside the main f-string
PROMPT_TEMPLATE = """
## Input Context:
1. A specific **comparison report section** for insurer '{insurer}' and recommended tier '{recommended_tier_name}'.
2. A list of **customer requirements**.
3. The corresponding **policy document** (provided as PDF input).

## Customer Requirements List:
```json
{requirements_json_str}
```

## Comparison Report Section for {recommended_tier_name}:
```markdown
{report_section_markdown}
```

## Important Context: Tier Ranking Logic & Data
1.  **Tier Ranking Purpose:** The comparison report generation process uses an external mechanism (`data/policies/pricing_tiers/tier_rankings.py`) to break ties between policy tiers from the SAME insurer. If multiple tiers from one insurer meet the customer's requirements equally well based *solely* on the policy document (PDF), the system is designed to recommend the tier ranked as cheaper/lower according to this external ranking.
2.  **Provided Ranking Data:** The known tier ranking for insurer '{insurer}' (ordered from cheapest to most expensive) is:
    ```json
    {insurer_ranking_list_str}
    ```
3.  **Evaluation Rule:** Justifications or summary statements in the report referencing price, budget, or tier preference *as a tie-breaker between otherwise equivalent tiers* should be considered valid **only if** the chosen tier correctly matches the cheapest option according to the **Provided Ranking Data** above among the tiers verified as equivalent based on the PDF. Focus first on validating coverage claims against the PDF; only consider the tier ranking valid if used correctly as a tie-breaker.

## Your Task 1 :
**Examine Each Coverage Section:** For each of the **customer requirements** listed above, perform the following checks by comparing the **comparison report section** claims against the **policy document** (PDF input).
**Report Content Check:** Does the **comparison report section** provide an analysis (e.g., under a heading like "Requirement: [Coverage Name]") for this specific coverage type? Answer Yes/No.
**Information Found in PDF:** Does the **policy document** contain relevant terms, conditions, benefits, limits, or exclusions specifically pertaining to this coverage type? Answer Yes/No.
**Coverage Assessment Validation:** Carefully read the "Coverage Assessment" section (including "Base Limits", "Conditional Limits" and "Source Specific Details" fields) for this coverage type within the **comparison report section**. Based only on the provided **policy document** (recognizing it may be a summary), determine if the **comparison report section** justification is factually supported by the **policy document** terms, conditions, limits, and exclusions. Is the **comparison report section** reasoning sound given the **policy document** content?
    - If the justification relies *solely* on price/ranking without establishing equivalent coverage from the PDF, mark `justification_supported_by_pdf` as 'No'.
    - If coverage is equivalent based on the PDF and the justification *additionally* mentions price/ranking as a tie-breaker (consistent with the Tier Ranking Logic context above), verify that the chosen tier ('{recommended_tier_name}') is indeed the cheapest among the equivalent tiers according to the **Provided Ranking Data** above. If both conditions (PDF equivalence AND correct ranking application) are met, mark `justification_supported_by_pdf` as 'Yes'. Otherwise (if PDF coverage isn't equivalent OR the ranking was applied incorrectly), mark 'No'.
    - Otherwise (no tie-breaker mentioned), mark `justification_supported_by_pdf` based purely on PDF evidence ('Yes' or 'No').
**Specific Instruction for Medical Coverage:** When assessing Medical Coverage and the customer requirement involves pre-existing conditions, apply a stricter standard due to potential limitations of the summary PDF. If the PDF summary only confirms pre-existing condition coverage under specific sections like 'Emergency Evacuation' (e.g., Sec 4) but lacks explicit confirmation under the main 'Medical Expenses Overseas' section (e.g., Sec 2), then report `justification_supported_by_pdf` as ‘yes’ and ‘purchase of add-on required’.

## Your Task 2 :
**Verify Summary Statements:** Verify the statements in the final summary section of the **comparison report section** (strengths & weaknesses for the recommended tier '{recommended_tier_name}') based on the **policy document** (PDF input) and the **Provided Ranking Data**.
**Determine:** In the last section of the **comparison report section** (denoted by the last ##), there is a summary for the recommended tier '{recommended_tier_name}'. Determine the truth in each statement (both strengths & weakness) by referencing information provided in the **policy document** and considering the **Tier Ranking Logic/Data**. Give the answer in 'True' or 'False' under 'validated'. Statements about price/value are considered 'True' if they accurately reflect the correct application of the **Provided Ranking Data** as a tie-breaker between tiers previously verified as equivalent based on the PDF.
**Explain:** Explain why "True" or "False" under `explanation`, referencing evidence from the **policy document** and/or the correct application of the **Provided Ranking Data** and list page number under `page` (if applicable from PDF).

## Crucial Instructions:
1. **Recommended Tier Focus:** Focus your analysis on the '{recommended_tier_name}' tier within the provided **policy document**.
2. **PDF Location:** In `pdf_location`, if relevant information is found in the PDF, provide the specific Page Number(s) and Section Heading(s) where the most pertinent details are located. If multiple relevant sections exist, list the primary ones. If not found, state "N/A".
3. **Placeholder:** In the **policy document**, if placeholder text like "Refer to Section X" is observed, you **MUST** read the relevant section(s) in the policy text within the **policy document** for each coverage and include the key applicable conditions, definitions, major inclusions/exclusions, or other pertinent information for that coverage and specified tier. If a benefit is not covered for a specific tier, explicitly state that if mentioned.
4. **Currency:** Identify and include the correct currency code (e.g., "SGD") if mentioned in the PDF context.
5. **Focus:** Concentrate strictly on whether the PDF text substantiates the claims made in the report. Do not introduce outside knowledge. Pay close attention to limits, maximum amounts, specific exclusions, and conditions mentioned in the PDF and compare them to the report's justification.
6. **JSON Output:** Generate only a JSON object containing the validation results for each report analysed, using the following exact structure. Replace bracketed placeholders [...] with your findings based on the instructions above.

## Output Format (Strict JSON):
```json
{{
    "filename": "{report_identifier}",
    "recommended_tier": "{recommended_tier_name}",
     // task 1 output
    "analysis": [
        {{
          "requirement": "[Requirement Coverage]", // Add the specific requirement coverage here
          "report_has_analysis": "[Yes/No]",
          "found_in_pdf": "[Yes/No]",
          "pdf_location": "[Page(s), Section(s) / N/A]",
          "justification_supported_by_pdf": "[Yes/No/Purchase of add-on required]", // Updated possible values
          "validated": "[true/false]"  // returns True if justification_supported_by_pdf is yes or purchase of add-on required, otherwise false
        }} // Repeat this structure for each requirement coverage analysed
    ],
    // task 2 output
    "summary_validation": [ // Renamed from "summary" to avoid conflict
        {{
            "statement": "[Statement from report summary]",
            "validated": "[true/false]", // returns True if statement is supported by pdf, False otherwise
            "explanation": "[Explanation referencing PDF evidence]",
            "pdf_location": "[Page(s), Section(s) / N/A]"
        }} // Repeat this structure for each statement in the summary
    ],
     "overall_assessment": {{
      "pass_fail": "[PASS/FAIL]",  // PASS if all 'validated' fields in 'analysis' and 'summary_validation' are true. FAIL otherwise.
      "explanation": "[Provide a brief (2-3 sentences) summary of the validation findings for this specific report. Assign PASS if all justifications/statements are reasonably supported by the PDF *and*, where applicable, correctly apply the provided **Insurer Tier Ranking Data** as a tie-breaker according to instructions. Assign FAIL if there are one or more significant claims or discrepancies unsupported by the PDF *and* not explained by the correct application of the Tier Ranking Logic/Data.]"
    }}
}}
```
"""


# --- Helper Functions ---
def find_recommended_tier(report_content: str) -> str | None:
    """Parses the comparison report to find the recommended tier using multiple patterns."""
    # List of regex patterns to try, ordered by specificity or common formats
    patterns = [
        r"\*\*Recommended Tier:\*\*\s*:\s*([a-zA-Z0-9\s!]+)",  # Format: **Recommended Tier:** : Tier Name
        r"Recommended Tier:\s*\*\*?([a-zA-Z0-9\s!]+)\*\*?",  # Format: Recommended Tier: **Tier Name** or Tier Name
        r"##\s*Summary and Recommendation for .+?\s*-\s*([a-zA-Z0-9\s!]+)",  # Format: ## Summary and Recommendation for Insurer - Tier Name
    ]

    for pattern in patterns:
        match = re.search(pattern, report_content, re.IGNORECASE)
        if match:
            tier = match.group(1).strip()
            # More aggressive cleanup: remove potential markdown and keep only letters, numbers, spaces
            tier = re.sub(
                r"[^\w\s-]", "", tier
            ).strip()  # Keep word chars, spaces, hyphens
            # Remove potential leading/trailing hyphens just in case
            tier = tier.strip("-")
            return tier

    logging.warning(
        "Could not parse recommended tier from report using known patterns."
    )
    return None


def find_requirements_file(uuid: str) -> tuple[Path | None, str | None]:
    """Finds the requirements file for a given UUID and extracts the scenario name."""
    search_pattern = str(REQUIREMENTS_DIR / f"requirements_*_{uuid}.json")
    matching_files = glob.glob(search_pattern)
    if not matching_files:
        logging.error(
            f"No requirements file found for UUID: {uuid} using pattern: {search_pattern}"
        )
        return None, None
    if len(matching_files) > 1:
        logging.warning(
            f"Multiple requirements files found for UUID: {uuid}. Using the first one: {matching_files[0]}"
        )
    req_file_path = Path(matching_files[0])
    match = re.match(r"requirements_(.+)_" + uuid + r"\.json", req_file_path.name)
    scenario_name = match.group(1) if match else "unknown_scenario"
    return req_file_path, scenario_name


# --- Core Evaluation Logic ---
def evaluate_single_insurer(
    uuid: str, insurer: str, overwrite: bool, llm_service: LLMService
) -> bool:
    """Handles the evaluation process for a single insurer report. Returns True on success/skip, False on failure."""
    logging.info(f"--- Evaluating Insurer: {insurer} for UUID: {uuid} ---")

    report_path = RESULTS_DIR / uuid / f"policy_comparison_report_{insurer}_{uuid}.md"
    # Construct output path with UUID as a subdirectory
    output_dir_for_uuid = OUTPUT_DIR / uuid
    output_path = output_dir_for_uuid / f"eval_comparison_{insurer}.json"

    # Check if output exists and handle overwrite
    if output_path.exists() and not overwrite:
        logging.info(
            f"Output file already exists and --overwrite not specified. Skipping: {output_path}"
        )
        return True  # Indicate skipped success

    if not report_path.exists():
        logging.error(f"Comparison report file not found: {report_path}")
        return False  # Indicate failure

    # Read Report Content
    try:
        report_content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        logging.error(f"Error reading report file {report_path}: {e}")
        return False

    # Find Recommended Tier
    recommended_tier = find_recommended_tier(report_content)
    if not recommended_tier:
        logging.error(
            f"Could not determine recommended tier for {insurer} in report {report_path}"
        )
        return False
    logging.info(f"Identified recommended tier: {recommended_tier}")

    # Find Policy PDF - Construct path with curly braces AND LOWERCASE
    # Convert insurer and tier to lowercase for path construction
    insurer_lower = insurer.lower()
    tier_lower = recommended_tier.lower()
    policy_pdf_path = POLICIES_DIR / f"{insurer_lower}_{{{tier_lower}}}.pdf"
    logging.info(f"Checking for policy PDF at: {policy_pdf_path}")
    if not policy_pdf_path.exists():
        logging.error(f"Policy PDF not found at expected path: {policy_pdf_path}")
        # Attempt fallback with original casing just in case (less likely)
        policy_pdf_path_orig_case = (
            POLICIES_DIR / f"{insurer}_{{{recommended_tier}}}.pdf"
        )
        logging.info(
            f"Checking for policy PDF at original case path: {policy_pdf_path_orig_case}"
        )
        if policy_pdf_path_orig_case.exists():
            policy_pdf_path = policy_pdf_path_orig_case  # Use original case if found
        else:
            logging.error(
                f"Policy PDF also not found at original case path: {policy_pdf_path_orig_case}"
            )
            return False  # Exit if neither found
    logging.info(f"Using policy PDF: {policy_pdf_path}")

    # Find and Read Requirements File
    requirements_path, scenario_name = find_requirements_file(uuid)
    if not requirements_path:
        return False  # Error logged in function
    logging.info(
        f"Found requirements file: {requirements_path} (Scenario: {scenario_name})"
    )
    try:
        with open(requirements_path, "r", encoding="utf-8") as f:
            requirements_data = json.load(f)
    except Exception as e:
        logging.error(
            f"Error reading or parsing requirements file {requirements_path}: {e}"
        )
        return False

    # Load Tier Ranking Data
    all_rankings = get_insurer_tier_ranking()
    insurer_ranking_list = all_rankings.get(insurer.lower())
    insurer_ranking_list_str = (
        json.dumps(insurer_ranking_list) if insurer_ranking_list else "N/A"
    )
    if insurer_ranking_list is None:
        logging.warning(
            f"No tier ranking found for insurer: {insurer}. Evaluation of tie-breaking logic may be limited."
        )

    # Prepare Prompt
    report_section_match = re.search(
        rf"##\s*Summary and Recommendation for {re.escape(insurer)}\s*-\s*{re.escape(recommended_tier)}.*?(?=##\s*Summary and Recommendation for|$)",
        report_content,
        re.DOTALL | re.IGNORECASE,
    )
    report_section_markdown = (
        report_section_match.group(0).strip()
        if report_section_match
        else report_content
    )
    if not report_section_match:
        logging.warning(
            f"Could not extract specific section for {insurer} - {recommended_tier}. Using full report content."
        )

    try:
        core_requirements = requirements_data.get("json_dict", requirements_data)
        requirements_json_str = json.dumps(core_requirements, indent=2)
    except Exception as e:
        logging.error(f"Error formatting requirements data: {e}")
        return False

    report_identifier = report_path.name
    prompt_inputs = {
        "insurer": insurer,  # Keep original case for prompt display if needed
        "recommended_tier_name": recommended_tier,  # Keep original case for prompt display
        "requirements_json_str": requirements_json_str,
        "report_section_markdown": report_section_markdown,
        "report_identifier": report_identifier,
        "insurer_ranking_list_str": insurer_ranking_list_str,  # Add ranking list string
    }
    try:
        final_prompt = PROMPT_TEMPLATE.format(**prompt_inputs)
    except Exception as e:
        logging.error(f"Error formatting prompt: {e}")
        return False

    # Multi-modal LLM Call with Retry Logic
    logging.info(f"Attempting LLM evaluation for {report_identifier}...")

    max_retries = 3
    base_delay = 5  # seconds
    validated_result = None  # Initialize before loop

    for attempt in range(max_retries):
        logging.info(
            f"LLM Evaluation Attempt {attempt + 1}/{max_retries} for {report_identifier}"
        )
        try:
            # Read PDF content as bytes (inside loop in case of file read issues)
            try:
                with open(policy_pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
            except Exception as e:
                logging.error(
                    f"Error reading policy PDF file {policy_pdf_path} on attempt {attempt + 1}: {e}"
                )
                # If PDF read fails, retrying the LLM call won't help
                return False  # Exit function if PDF cannot be read

            # Prepare multi-modal content list correctly
            pdf_content_part = {"mime_type": "application/pdf", "data": pdf_bytes}
            multi_modal_content = [
                final_prompt,
                pdf_content_part,
            ]

            evaluation_result_dict = llm_service.generate_structured_content(
                prompt=None,
                contents=multi_modal_content,
            )
            if not evaluation_result_dict:
                # Consider this a failure scenario worth retrying
                raise ValueError("LLM returned empty or invalid response.")

            # Validate the dictionary returned by the LLM service here:
            validated_result = EvaluationResult.model_validate(evaluation_result_dict)
            logging.info(
                f"Successfully received and validated evaluation result from LLM on attempt {attempt + 1}."
            )
            break  # Exit retry loop on success

        except ValidationError as e:
            logging.error(
                f"Pydantic validation failed for LLM response on attempt {attempt + 1}: {e}"
            )
            # Don't retry validation errors, treat as final failure for this attempt.
            validated_result = None  # Ensure it's None on validation failure
            break  # Exit retry loop on validation failure
        except Exception as e:
            logging.warning(
                f"Error during LLM call or processing on attempt {attempt + 1}: {e}"
            )
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(
                    f"LLM call failed after {max_retries} attempts for {report_identifier}."
                )
                validated_result = None  # Ensure it's None on final failure
                # Loop will end, validated_result is None

    # --- End Retry Logic ---

    # Check if validation was successful after the loop
    if validated_result is None:
        logging.error(
            f"Failed to get a valid evaluation result for {report_identifier} after retries."
        )
        return False  # Indicate failure for this insurer

    # Save Output (only if validated_result is not None)
    try:
        output_path.parent.mkdir(
            parents=True, exist_ok=True
        )  # Ensure output dir exists
        with open(output_path, "w", encoding="utf-8") as f:
            # If validated_result is a Pydantic model:
            f.write(validated_result.model_dump_json(indent=2))
            # If validated_result is already a dict:
            # json.dump(validated_result, f, indent=2)
        logging.info(f"Evaluation result saved successfully to: {output_path}")
        return True  # Indicate success
    except Exception as e:
        logging.error(f"Error saving evaluation result to {output_path}: {e}")
        return False


# --- Main Execution ---
def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate policy comparison reports against policy documents."
    )
    parser.add_argument(
        "--uuid", required=True, help="Customer UUID for the report(s) to evaluate."
    )
    parser.add_argument(
        "--insurer",
        required=False,
        help="Insurer name for a specific report. If omitted, evaluate all insurers for the UUID.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing evaluation results if found.",
    )
    return parser.parse_args()


def main():
    """Main function to orchestrate the evaluation."""
    args = parse_arguments()
    logging.info(f"Starting evaluation run for UUID: {args.uuid}")

    # Initialize LLM Service
    try:
        # Ensure LLMService is configured for a multi-modal model
        llm_service = LLMService()
        logging.info("LLM Service initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize LLM Service: {e}")
        sys.exit(1)

    # Ensure base output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.insurer:
        # --- Single Insurer Mode ---
        logging.info(f"Evaluating single insurer: {args.insurer}")
        success = evaluate_single_insurer(
            args.uuid, args.insurer, args.overwrite, llm_service
        )
        if success:
            logging.info(
                f"Evaluation complete for UUID: {args.uuid}, Insurer: {args.insurer}"
            )
        else:
            logging.error(
                f"Evaluation failed for UUID: {args.uuid}, Insurer: {args.insurer}"
            )
            sys.exit(1)  # Exit with error if single specified insurer fails
    else:
        # --- Batch Mode (All Insurers for UUID) ---
        logging.info(
            f"No specific insurer provided. Evaluating all comparison reports for UUID: {args.uuid}"
        )
        uuid_results_dir = RESULTS_DIR / args.uuid
        if not uuid_results_dir.is_dir():
            logging.error(f"Results directory not found for UUID: {uuid_results_dir}")
            sys.exit(1)

        report_files = list(uuid_results_dir.glob("policy_comparison_report_*.md"))
        if not report_files:
            logging.warning(f"No comparison reports found in {uuid_results_dir}")
            sys.exit(0)  # Exit gracefully if no reports to process

        logging.info(f"Found {len(report_files)} comparison reports to evaluate.")
        success_count = 0
        fail_count = 0

        for report_file in report_files:
            # Extract insurer name: policy_comparison_report_{insurer}_{uuid}.md
            match = re.match(
                rf"policy_comparison_report_(.+)_{args.uuid}\.md", report_file.name
            )
            if match:
                insurer_name = match.group(1)
                # Clean up potential double underscores or formatting issues if needed
                insurer_name = insurer_name.replace("__", "_")  # Example cleanup
                if evaluate_single_insurer(
                    args.uuid, insurer_name, args.overwrite, llm_service
                ):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                logging.warning(
                    f"Could not parse insurer name from filename: {report_file.name}. Skipping."
                )
                fail_count += (
                    1  # Count skipped files due to parsing error as failure for summary
                )

        logging.info(f"--- Batch Evaluation Summary for UUID: {args.uuid} ---")
        logging.info(f"Successfully processed/skipped: {success_count}")
        logging.info(f"Failed/Skipped due to error: {fail_count}")
        if fail_count > 0:
            logging.warning(
                "One or more evaluations failed. Check logs above for details."
            )
            # Decide if batch failure should cause non-zero exit code
            # sys.exit(1) # Optionally exit with error on batch failures


if __name__ == "__main__":
    main()
