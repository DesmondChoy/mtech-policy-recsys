"""
Generates a final policy recommendation using a two-stage process.

Stage 1: Parses all insurer-level comparison reports for a given customer UUID,
         calculates a quantitative score based on requirement assessments
         ("Fully Met", "Partially Met", "Not Met"), and ranks the policies.

Stage 2: Takes the top N policies from Stage 1, feeds their full comparison
         reports to an LLM for nuanced re-ranking, and obtains a final
         recommendation with justification (including relevant source references).

Output: Generates a customer-friendly Markdown report summarizing the final
        recommendation, justification, Stage 1 ranking details, and scoring method.
        Saves the report to `results/{customer_uuid}/recommendation_report_{customer_uuid}.md`.
        Also saves the intermediate Stage 2 JSON output to
        `results/{customer_uuid}/final_recommendation_{customer_uuid}.json`.

Prerequisites:
- Insurer-level comparison reports must exist in the relevant
  `results/{customer_uuid}/` directory, generated by
  `scripts/generate_policy_comparison.py`.
- `LLMService` must be configured.

Usage:
    python scripts/generate_recommendation_report.py --customer_id <customer_uuid> [--top_n <N>]

Example:
    python scripts/generate_recommendation_report.py --customer_id 6aef8846-aed1-4a6e-8115-d5ca7d6d0abf --top_n 3
"""

import argparse
import asyncio  # Import asyncio
import glob
import json  # Keep json import just in case
import logging
import os
import re
import sys
from pathlib import Path
import typing
from typing import Dict, List, Optional, Tuple, Any

# Add Pydantic for structured output in Stage 2
from pydantic import BaseModel, Field

# Add LLMService import for Stage 2
try:
    from src.models.llm_service import LLMService
except ImportError:
    # Attempt relative import if src path setup fails or isn't needed directly
    try:
        # Assuming llm_service is in ../src/models relative to scripts/
        project_root_for_import = Path(__file__).resolve().parents[1]
        sys.path.append(str(project_root_for_import))
        from src.models.llm_service import LLMService
    except ImportError as e:
        print(f"Error: Could not import LLMService: {e}. Ensure src is in Python path.")
        LLMService = None  # Set to None to indicate it's unavailable

# Add src directory to Python path if needed for other modules (though not strictly for this task)
# project_root = Path(__file__).resolve().parents[1]
# sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants (Define project root and results dir relative to this script)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"


# --- Task 1: Markdown Report Parser ---


def parse_comparison_report(report_content: str) -> Dict[str, Any]:
    """
    Parses the content of a Markdown comparison report.

    Extracts:
        - Recommended Tier name.
        - Requirement details:
            - Name
            - Full analysis text block.
            - Specific 'Coverage Assessment' statement.
        - Summary Weaknesses: List of tuples `(requirement_name, description)`.

    Args:
        report_content: The full Markdown content of the report as a string.

    Returns:
        A dictionary containing the parsed information, e.g.:
        {
            "recommended_tier": "Tier Name",
            "requirements": {
                "Requirement Name 1": {
                    "analysis_text": "Full text block...",
                    "assessment": "Fully Met / Partially Met / Not Met..."
                },
                # ... other requirements
            },
            "summary_weaknesses": [
                ("Requirement Name A", "Description of gap 1"),
                ("Requirement Name B", "Description of gap 2")
            ]
        }
        Returns an empty dictionary if parsing fails significantly.
    """
    parsed_data: Dict[str, Any] = {
        "recommended_tier": None,
        "requirements": {},
        "summary_weaknesses": [],  # Now stores tuples: (req_name, description)
    }

    try:
        # 1. Extract Recommended Tier
        tier_match = re.search(
            r"^\*\*Recommended Tier:\*\* : (.*?)$", report_content, re.MULTILINE
        )
        if tier_match:
            parsed_data["recommended_tier"] = tier_match.group(1).strip()

        # 2. Extract Requirement Sections and Assessments
        # Regex to find each requirement block until the next requirement or the summary
        # (?s) is equivalent to re.DOTALL, making . match newlines
        # (?:...) is a non-capturing group
        req_pattern = re.compile(
            r"^### Requirement: (.*?)\n(.*?)(?=\n^### Requirement:|\n^## Summary for Recommended Tier:)",
            re.MULTILINE | re.DOTALL,
        )
        # Updated regex to capture only the specific required phrases
        assessment_pattern = re.compile(
            r"^\*   \*\*Coverage Assessment:\*\* (Fully Met|Partially Met|Not Met)",
            re.MULTILINE,
        )

        for match in req_pattern.finditer(report_content):
            req_name = match.group(1).strip()
            analysis_text = match.group(2).strip()
            assessment = "Assessment phrase not found"  # Default if pattern fails

            assessment_match = assessment_pattern.search(analysis_text)
            if assessment_match:
                # Group 1 now contains only "Fully Met", "Partially Met", or "Not Met"
                assessment = assessment_match.group(1).strip()
            else:
                # Add a log or print statement if the assessment line itself isn't found
                print(
                    f"Warning: Could not find Coverage Assessment line for requirement: {req_name}"
                )

            parsed_data["requirements"][req_name] = {
                "analysis_text": analysis_text,
                "assessment": assessment,
            }

        # 3. Extract Summary Weaknesses
        # Find the summary section first
        summary_match = re.search(
            r"^## Summary for Recommended Tier:.*?$(.*)",
            report_content,
            re.MULTILINE | re.DOTALL,
        )
        if summary_match:
            summary_content = summary_match.group(1)
            # Find the Weaknesses/Gaps block within the summary
            weakness_block_match = re.search(
                r"^\*   \*\*Weaknesses/Gaps:\*\*(.*?)(?=\n^\*   \*\*|$)",
                summary_content,
                re.MULTILINE | re.DOTALL,
            )
            if weakness_block_match:
                weakness_block = weakness_block_match.group(1)
                # Extract structured weaknesses: * [Req Name]: Description
                # Regex captures Req Name inside [] and the description after :
                weakness_pattern = re.compile(
                    r"^\s*\*\s+\[(.*?)\]:\s*(.*?)$", re.MULTILINE
                )
                parsed_weaknesses = []
                for weak_match in weakness_pattern.finditer(weakness_block):
                    req_name = weak_match.group(1).strip()
                    description = weak_match.group(2).strip()
                    parsed_weaknesses.append((req_name, description))
                parsed_data["summary_weaknesses"] = parsed_weaknesses

    except Exception as e:
        # Basic error handling, could be more specific
        print(f"Error parsing report: {e}")
        # Return partially parsed data or empty dict depending on desired robustness
        return {}  # Or return parsed_data to see partial results on error

    # Basic validation: Check if essential parts were found
    if not parsed_data["recommended_tier"] or not parsed_data["requirements"]:
        print(
            "Warning: Could not parse essential parts of the report (Tier or Requirements)."
        )
        # Decide whether to return partial data or indicate failure
        # return {} # Indicate failure

    return parsed_data


# --- Task 2: Stage 1 Scoring Logic ---


def calculate_stage1_score(parsed_report_data: Dict[str, Any]) -> float:
    """
    Calculates the Stage 1 score based *only* on the exact assessment phrases
    extracted from the comparison report.

    Scoring Logic:
    - Iterates through requirements parsed by `parse_comparison_report`.
    - Checks the exact 'assessment' string:
        - "Fully Met": Adds 1.0 point.
        - "Partially Met": Adds 0.5 points.
        - "Not Met": Adds 0.0 points.
    - Ignores summary sections or other text.

    Args:
        parsed_report_data: The dictionary output from parse_comparison_report,
                            expected to contain an 'requirements' dictionary
                            where each value has an 'assessment' key.

    Returns:
        The calculated float score. Returns 0.0 if input is invalid or
        no requirements are found.
    """
    if not parsed_report_data or "requirements" not in parsed_report_data:
        print(
            "Warning: Invalid or empty parsed data provided to calculate_stage1_score."
        )
        return 0.0

    requirements = parsed_report_data.get("requirements", {})
    if not requirements:
        print("Warning: No requirements found in parsed data for scoring.")
        return 0.0

    score = 0.0
    for req_name, req_data in requirements.items():
        assessment = req_data.get("assessment", "")

        if assessment == "Fully Met":
            score += 1.0
        elif assessment == "Partially Met":
            score += 0.5
        elif assessment == "Not Met":
            score += 0.0
        else:
            # This case handles unexpected assessment strings, including the default
            # "Assessment phrase not found" from the parser if the regex failed.
            print(
                f"Warning: Unknown assessment phrase '{assessment}' for requirement '{req_name}'. Assigning 0 points."
            )
            score += 0.0  # Assign 0 points for unknown/missing assessments

    # print(f"Debug: Calculated Stage 1 score: {score}") # Optional debug
    return score


# --- Task 4: Stage 2 LLM Re-ranking ---


# Define Pydantic model for structured Stage 2 output
class FinalRecommendation(BaseModel):
    """Structure for the final recommendation output from Stage 2."""

    recommended_insurer: str = Field(description="The name of the recommended insurer.")
    recommended_tier: str = Field(
        description="The name of the recommended policy tier from the chosen insurer."
    )
    justification: str = Field(
        description="Detailed justification explaining why this policy was chosen over the other finalists, comparing strengths, weaknesses, and alignment with customer needs."
    )


# Define Prompt Template for Stage 2
PROMPT_TEMPLATE_STAGE2 = """
# Role: Expert Travel Insurance Advisor

# Goal:
Review the detailed comparison reports for the top {num_candidates} candidate policies identified in Stage 1. Select the SINGLE best overall policy (Insurer + Tier) for the customer based on a nuanced comparison of their strengths, weaknesses, and alignment with the original customer requirements. Provide a comprehensive justification for your final choice.

# Customer Requirements Summary:
(Optional but recommended: Include key customer requirements summary here if available)
```json
{customer_requirements_summary_json}
```

# Candidate Policy Reports:
Here are the full comparison reports for the finalist policies:

{candidate_reports_markdown}

# Re-ranking and Final Selection Task:

1.  **Review Reports:** Carefully read and understand each provided comparison report. Pay attention to the recommended tier, the detailed requirement analysis (including 'Coverage Assessment'), and the summary strengths/weaknesses for each candidate.
2.  **Compare Candidates:** Compare the candidate policies *relative to each other*. Consider:
    *   How well does each policy meet the most critical customer requirements?
    *   What are the key trade-offs between the candidates (e.g., better coverage vs. higher cost, specific benefit differences)?
    *   Which policy offers the best overall value proposition considering both coverage and potential gaps?
3.  **Select Single Best Policy:** Based on your comparative analysis, determine the single best policy (Insurer + Tier) from the candidates provided.
4.  **Provide Justification:** Write a clear, comprehensive justification explaining your final choice. This justification MUST:
    *   Explicitly state the chosen Insurer and Tier.
    *   Compare the chosen policy against the *other finalist(s)*, highlighting the key reasons for its selection.
    *   Reference specific strengths, weaknesses, or coverage details from the reports to support your reasoning. **Where relevant, include key source references (e.g., page or section numbers from the policy documents mentioned in the reports) to substantiate important comparison points.**
    *   Explain the trade-offs considered.
5.  **Output Format:** Provide your response as a JSON object matching the following Pydantic schema:

```json
{{
  "recommended_insurer": "string",
  "recommended_tier": "string",
  "justification": "string"
}}
```

**Final Instruction:** Generate ONLY the JSON object containing the final recommendation and justification, adhering strictly to the schema provided. Do not include any introductory text, markdown formatting, or other content outside the JSON structure.
"""


# Placeholder function for Stage 2 logic
async def run_stage2_reranking(
    top_candidates: List[Dict[str, Any]],
    customer_requirements_summary: Optional[Dict[str, Any]] = None,  # Optional summary
) -> Optional[FinalRecommendation]:
    """
    Takes the top candidate reports from Stage 1, prepares a prompt for Stage 2
    LLM re-ranking, calls the LLM, and returns the structured final recommendation.

    Args:
        top_candidates: A list of dictionaries, where each dictionary represents
                        a candidate from Stage 1 and must contain at least
                        'report_path' or 'report_content'.
        customer_requirements_summary: Optional dictionary containing key customer
                                       requirements to provide context to the LLM.

    Returns:
        A FinalRecommendation Pydantic object, or None if an error occurs.
    """
    if not top_candidates:
        logger.warning("No top candidates provided for Stage 2 re-ranking.")
        return None

    if LLMService is None:
        logger.error("LLMService is not available. Cannot perform Stage 2 re-ranking.")
        return None

    llm_service = LLMService()  # Initialize LLM Service

    # Prepare candidate reports markdown block
    candidate_reports_markdown = ""
    for i, candidate in enumerate(top_candidates):
        report_content = ""
        report_path_str = candidate.get("report_path")
        if report_path_str:
            try:
                report_path = Path(report_path_str)
                with open(report_path, "r", encoding="utf-8") as f:
                    report_content = f.read()
                logger.debug(f"Read report content from: {report_path.name}")
            except Exception as e:
                logger.error(
                    f"Error reading report file {report_path_str} for Stage 2: {e}"
                )
                report_content = f"Error reading report: {report_path_str}"  # Include error in prompt input
        elif candidate.get("report_content"):  # Allow passing content directly
            report_content = candidate.get("report_content")
        else:
            logger.warning(f"Candidate {i + 1} missing report_path or report_content.")
            report_content = f"Report content missing for candidate {i + 1}."

        candidate_reports_markdown += f"--- Candidate {i + 1} Start ---\n"
        candidate_reports_markdown += f"Insurer: {candidate.get('insurer', 'N/A')}\n"
        candidate_reports_markdown += f"Recommended Tier (from Stage 1): {candidate.get('recommended_tier', 'N/A')}\n"
        candidate_reports_markdown += (
            f"Stage 1 Score: {candidate.get('score', 'N/A'):.1f}\n\n"
        )
        candidate_reports_markdown += f"{report_content}\n"
        candidate_reports_markdown += f"--- Candidate {i + 1} End ---\n\n"

    # Prepare customer requirements summary JSON string
    customer_req_summary_str = "{}"  # Default empty JSON
    if customer_requirements_summary:
        try:
            customer_req_summary_str = json.dumps(
                customer_requirements_summary, indent=2
            )
        except Exception as e:
            logger.warning(f"Could not serialize customer requirements summary: {e}")
            customer_req_summary_str = (
                '{"error": "Could not serialize requirements summary"}'
            )

    # Format the Stage 2 prompt
    prompt = ""  # Initialize
    try:
        prompt = PROMPT_TEMPLATE_STAGE2.format(
            num_candidates=len(top_candidates),
            customer_requirements_summary_json=customer_req_summary_str,
            candidate_reports_markdown=candidate_reports_markdown.strip(),
        )
        logger.debug(f"Stage 2 Prompt prepared (length: {len(prompt)} chars).")
        # logger.debug(f"Stage 2 Prompt Snippet:\n{prompt[:1000]}...") # Optional: Log prompt snippet

        # Call LLMService to get structured dictionary output
        # Note: Using asyncio.to_thread as generate_structured_content might be blocking
        structured_dict_result = await asyncio.to_thread(
            llm_service.generate_structured_content,
            prompt=prompt,
            # No output_schema argument here
        )

        if structured_dict_result:
            # Attempt to validate the dictionary using the Pydantic model
            try:
                final_recommendation = FinalRecommendation(**structured_dict_result)
                logger.info(
                    "Successfully received and validated structured recommendation from Stage 2 LLM."
                )
                # Log details of the recommendation
                logger.info(
                    f"  Recommended Insurer: {final_recommendation.recommended_insurer}"
                )
                logger.info(
                    f"  Recommended Tier: {final_recommendation.recommended_tier}"
                )
                logger.info(
                    f"  Justification: {final_recommendation.justification[:200]}..."
                )  # Log snippet
                return final_recommendation
            except (
                Exception
            ) as pydantic_error:  # Catch Pydantic's ValidationError and others
                logger.error(
                    f"Failed to validate LLM response against FinalRecommendation schema: {pydantic_error}"
                )
                logger.error(f"LLM returned dictionary: {structured_dict_result}")
                return None
        else:
            logger.error("Stage 2 LLM call did not return a valid dictionary.")
            return None

    except KeyError as ke:
        logger.error(f"KeyError during Stage 2 prompt formatting: Missing key {ke}")
        logger.debug(f"Stage 2 Prompt Snippet:\n{prompt[:1000]}...")
        return None
    except Exception as e:
        logger.error(f"An error occurred during Stage 2 re-ranking: {e}", exc_info=True)
        logger.debug(f"Stage 2 Prompt Snippet:\n{prompt[:1000]}...")
        return None


# --- Task 6: Final Markdown Report Generation ---


def generate_markdown_report(
    customer_uuid: str,
    stage1_results: List[Dict[str, Any]],
    stage2_recommendation: FinalRecommendation,
    top_n: int = 3,  # To know how many were considered top
):
    """
    Generates a customer-friendly Markdown report summarizing the recommendation.

    Args:
        customer_uuid: The UUID of the customer.
        stage1_results: The full list of dictionaries containing ranked results
                        from Stage 1 (including 'insurer', 'recommended_tier', 'score').
        stage2_recommendation: The FinalRecommendation object from Stage 2.
        top_n: The number of candidates passed from Stage 1 to Stage 2.
    """
    logger.info(f"Generating Markdown recommendation report for {customer_uuid}")

    report_lines = []
    report_lines.append(
        f"# Travel Insurance Recommendation for Customer {customer_uuid}"
    )
    report_lines.append("\n---\n")  # Separator

    # 1. Final Recommendation
    report_lines.append("## Final Recommendation")
    report_lines.append(
        f"Based on a detailed analysis of your requirements against available policies, the recommended policy is:"
    )
    report_lines.append(
        f"\n**{stage2_recommendation.recommended_insurer.upper()} - {stage2_recommendation.recommended_tier}**\n"
    )

    # 2. Justification (from Stage 2)
    report_lines.append("### Justification")
    report_lines.append(stage2_recommendation.justification)
    report_lines.append("\n---\n")  # Separator

    # 3. Stage 1 Ranking Details
    report_lines.append("## Analysis Summary (How we got here)")
    report_lines.append(
        "To narrow down the options, we first performed an initial ranking based on how well each insurer's best policy explicitly met your stated requirements."
    )
    report_lines.append("\n**Scoring Method:**")
    report_lines.append("- Requirement **Fully Met**: +1.0 point")
    report_lines.append("- Requirement **Partially Met**: +0.5 points")
    report_lines.append("- Requirement **Not Met**: +0.0 points")
    report_lines.append(
        "\nThis score helps quickly identify policies that cover more of your needs based on the initial comparison."
    )

    # Top N Candidates
    report_lines.append(f"\n**Top {top_n} Candidates (Based on Initial Score):**")
    if stage1_results:
        for i, report in enumerate(stage1_results[:top_n]):
            report_lines.append(
                f"{i + 1}. **{report['insurer'].upper()} - {report['recommended_tier']}**: Score {report['score']:.1f}"
            )
    else:
        report_lines.append("No policies were ranked in Stage 1.")

    # Other Policies Analyzed
    other_policies = stage1_results[top_n:]
    if other_policies:
        report_lines.append("\n**Other Policies Analyzed (Lower Initial Score):**")
        for report in other_policies:
            report_lines.append(
                f"- **{report['insurer'].upper()} - {report['recommended_tier']}**: Score {report['score']:.1f}"
            )
    elif len(stage1_results) > top_n:
        # This case shouldn't happen if top_n >= len(stage1_results), but good to cover
        pass
    elif len(stage1_results) <= top_n and stage1_results:
        report_lines.append(
            "\n*All analyzed policies were included in the top candidates.*"
        )
    else:
        # Handles case where stage1_results was empty initially
        pass  # Already covered by "No policies were ranked"

    report_lines.append("\n---\n")
    report_lines.append(
        "The top candidates listed above were then reviewed in more detail by our AI advisor to provide the final recommendation and justification presented at the beginning of this report."
    )
    report_lines.append(
        "\n*Note: For full details on how each requirement was assessed for a specific policy, please refer to the individual comparison reports.*"
    )

    # 4. Save the report
    output_filename = f"recommendation_report_{customer_uuid}.md"
    customer_results_dir = RESULTS_DIR / customer_uuid
    customer_results_dir.mkdir(parents=True, exist_ok=True)  # Ensure dir exists
    output_path = customer_results_dir / output_filename

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        logger.info(f"Markdown recommendation report saved to: {output_path}")
    except Exception as e:
        logger.error(
            f"Failed to save Markdown recommendation report to {output_path}: {e}"
        )


# --- Placeholder for future Tasks ---

# Task 5: Integration within Orchestration
# Task 6: Final Output Formatting (Now Implemented Above)


# --- Task 3: Orchestration Logic ---


def run_stage1_ranking(customer_uuid: str):
    """
    Finds comparison reports for a customer, parses them, calculates Stage 1
    scores, ranks them, and prints the results.
    """
    logger.info(f"Starting Stage 1 ranking for customer UUID: {customer_uuid}")

    customer_results_dir = RESULTS_DIR / customer_uuid
    if not customer_results_dir.is_dir():
        logger.error(
            f"Results directory not found for customer: {customer_results_dir}"
        )
        return None  # Return None or empty list to indicate failure

    # Find all comparison reports for this customer
    report_pattern = str(
        customer_results_dir / f"policy_comparison_report_*_{customer_uuid}.md"
    )
    report_files = glob.glob(report_pattern)

    if not report_files:
        logger.warning(
            f"No comparison reports found matching pattern: {report_pattern}"
        )
        return []  # Return empty list if no reports found

    logger.info(f"Found {len(report_files)} comparison reports.")

    scored_reports = []
    for report_path_str in report_files:
        report_path = Path(report_path_str)
        # Extract insurer name reliably from filename format: policy_comparison_report_{insurer}_{uuid}.md
        insurer_match = re.search(
            r"policy_comparison_report_(.*?)_" + re.escape(customer_uuid) + r"\.md$",
            report_path.name,
        )
        insurer_name = insurer_match.group(1) if insurer_match else "unknown_insurer"

        logger.debug(f"Processing report: {report_path.name}")
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()

            parsed_data = parse_comparison_report(content)

            if (
                not parsed_data
                or not parsed_data.get("recommended_tier")
                or not parsed_data.get("requirements")
            ):
                logger.warning(
                    f"Skipping report due to parsing issues: {report_path.name}"
                )
                continue

            score = calculate_stage1_score(parsed_data)
            recommended_tier = parsed_data.get("recommended_tier", "N/A")

            scored_reports.append(
                {
                    "insurer": insurer_name,
                    "recommended_tier": recommended_tier,
                    "score": score,
                    "report_path": str(
                        report_path
                    ),  # Store path for potential Stage 2 use
                }
            )
            logger.debug(
                f"  Insurer: {insurer_name}, Tier: {recommended_tier}, Score: {score}"
            )

        except Exception as e:
            logger.error(
                f"Error processing report {report_path.name}: {e}", exc_info=True
            )  # Log traceback

    if not scored_reports:
        logger.warning("No reports were successfully scored.")
        return []  # Return empty list

    # Sort reports by score descending
    scored_reports.sort(key=lambda x: x["score"], reverse=True)

    logger.info("--- Stage 1 Ranking Results ---")
    for i, report in enumerate(scored_reports):
        logger.info(
            f"{i + 1}. Insurer: {report['insurer']}, Tier: {report['recommended_tier']}, Score: {report['score']:.1f}"
        )  # Use .1f for 0.5 increments

    # Select top candidates (e.g., top 3) - For now, just log them
    # In a real scenario, this function might return the top N candidates
    top_n = 3
    top_candidates = scored_reports[:top_n]
    logger.info(f"\n--- Top {top_n} Candidates for Stage 2 (Based on Score) ---")
    if top_candidates:
        for candidate in top_candidates:
            logger.info(
                f"  - Insurer: {candidate['insurer']}, Tier: {candidate['recommended_tier']}, Score: {candidate['score']:.1f}"
            )
            # logger.info(f"    Report: {candidate['report_path']}") # Optional: log path
    else:
        logger.info("  No candidates found.")

    # Return the ranked list for potential further processing
    return scored_reports


# --- Task 5: Integration Logic ---


async def main(
    customer_uuid: str, top_n: int = 3
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[FinalRecommendation]]:
    """
    Orchestrates the full recommendation process: Stage 1 ranking followed by
    Stage 2 re-ranking.

    Returns:
        A tuple containing:
        - The full list of ranked results from Stage 1 (or None if failed).
        - The FinalRecommendation object from Stage 2 (or None if failed).
    """
    # --- Stage 1 ---
    # Run Stage 1 ranking (synchronous)
    ranked_results = run_stage1_ranking(customer_uuid)

    # Handle Stage 1 failure or empty results
    if ranked_results is None:
        logger.error("Stage 1 ranking failed. Aborting.")
        return ranked_results, None
    if not ranked_results:
        logger.warning(
            "Stage 1 ranking returned no results. Cannot proceed to Stage 2."
        )
        return ranked_results, None

    # --- Stage 2 ---
    # Select top candidates for Stage 2
    top_candidates = ranked_results[:top_n]
    if not top_candidates:
        logger.warning(
            f"No top candidates found after Stage 1 (requested top {top_n}). Cannot proceed to Stage 2."
        )
        return ranked_results, None

    logger.info(
        f"\nProceeding to Stage 2 re-ranking with {len(top_candidates)} candidates..."
    )

    # Optional: Load customer requirements summary if needed for Stage 2 prompt
    # customer_req_summary = load_customer_requirements_summary(customer_uuid) # Placeholder
    customer_req_summary = None  # Set to None for now

    final_recommendation = await run_stage2_reranking(
        top_candidates=top_candidates,
        customer_requirements_summary=customer_req_summary,
    )

    if final_recommendation:
        logger.info("\n--- Final Recommendation (Stage 2) ---")
        logger.info(f"Recommended Insurer: {final_recommendation.recommended_insurer}")
        logger.info(f"Recommended Tier: {final_recommendation.recommended_tier}")
        logger.info(
            f"Justification (Snippet):\n{final_recommendation.justification[:500]}..."
        )  # Log snippet

        # Return results from both stages
        return ranked_results, final_recommendation
    else:
        logger.error("Stage 2 re-ranking failed to produce a final recommendation.")
        # Return Stage 1 results even if Stage 2 failed
        return ranked_results, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a policy recommendation report by running Stage 1 ranking and Stage 2 re-ranking."
    )
    parser.add_argument(
        "--customer_id",
        type=str,
        required=True,
        help="The unique UUID of the customer.",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=3,
        help="Number of top candidates from Stage 1 to pass to Stage 2.",
    )
    args = parser.parse_args()

    # Run the main async function and get results
    stage1_results, stage2_recommendation = asyncio.run(
        main(args.customer_id, args.top_n)
    )

    # --- Call Task 6: Generate Markdown Report ---
    if stage1_results is not None and stage2_recommendation is not None:
        generate_markdown_report(
            customer_uuid=args.customer_id,
            stage1_results=stage1_results,
            stage2_recommendation=stage2_recommendation,
            top_n=args.top_n,
        )
        # Optional: Keep the print statement for CLI confirmation
        print(
            f"\nRecommendation process completed. Final recommendation generated and saved."
        )
        print(f"  Recommended Insurer: {stage2_recommendation.recommended_insurer}")
        print(f"  Recommended Tier: {stage2_recommendation.recommended_tier}")
        print(
            f"  Markdown report saved in: results/{args.customer_id}/recommendation_report_{args.customer_id}.md"
        )

    else:
        logger.warning(
            "Markdown report generation skipped due to incomplete results from previous stages."
        )
        print(
            "\nRecommendation process completed, but failed to generate final recommendation."
        )
