# Policy Comparison Workflow Changes: Insurer-Level Analysis

**Status:** Completed

---

This document outlines planned major changes to the policy comparison workflow, shifting from tier-level analysis to insurer-level analysis.

## Current Implementation & Pain Points

**Current Process:**
- The `scripts/generate_policy_comparison.py` script currently performs policy comparison.
- **Input:** Takes one customer requirements JSON file and *multiple* processed policy JSON files (potentially across different insurers and tiers).
- **Logic:** It iterates through each policy JSON file provided. For each policy tier, it makes a separate LLM call to compare that single tier against the customer's requirements.
- **Output:** Generates individual Markdown reports for *each policy tier* compared (e.g., `policy_comparison_{provider}_{tier}_{timestamp}.md`). (Note: Customer ID is not part of the current filename format).

**Pain Points:**
- **High LLM Usage:** This approach requires one LLM call *per policy tier*. With multiple insurers and multiple tiers per insurer (e.g., 3 insurers x 3 tiers = 9 calls), this becomes computationally expensive and slow.
- **Fragmented Analysis:** The comparison results are spread across multiple files, requiring a separate consolidation step (manual or automated) to determine the single best recommendation across all insurers and tiers.

## Proposed Changes: Insurer-Level Analysis

**Goal:** To significantly reduce LLM calls while still producing a comparable analysis by comparing all tiers of a single insurer within one LLM call, and providing a detailed breakdown of how the recommended tier meets requirements.

**New Process Overview:**
1.  **Input:** The script will take a single customer UUID as input via `--customer_id`.
2.  **Data Discovery:** It will locate the corresponding requirements file (`requirements_*_{uuid}.json`) and dynamically identify all available insurers and their processed policy JSON files (`data/policies/processed/`).
3.  **Insurer-Level Prompt:** For each identified insurer, construct a single, comprehensive prompt containing:
    -   The customer's requirements (from the located requirements JSON).
    -   The details of *all* policy tiers for that specific insurer (from their processed policy JSON files).
    -   The predefined price ranking of the insurer's tiers (from `data/policies/pricing_tiers/tier_rankings.py`).
4.  **LLM Task:** Instruct the LLM (via the detailed prompt) to:
    -   Analyze how well each tier (within that insurer) meets the requirements holistically.
    -   Understand that coverages cannot be mixed and matched.
    -   Select the *single best tier* for that insurer, using the price ranking as a tie-breaker.
    -   Provide justification for the choice.
    -   **Perform a detailed analysis:** For the *chosen tier only*, iterate through each customer requirement and detail how the tier covers it, using granular data from the policy JSON (limits, source details, etc.).
5.  **Output:** Generate one Markdown report *per insurer*, containing the recommendation, justification, and detailed requirement analysis. Save to a customer-specific directory using the UUID and including the UUID in the filename (e.g., `results/{uuid}/policy_comparison_report_{insurer}_{uuid}.md`).

**Rationale:**
-   **Reduced LLM Calls:** One call per insurer instead of per tier.
-   **Integrated Decision:** LLM performs tier selection and tie-breaking.
-   **Clearer Output:** One comprehensive report per insurer, showing both the recommendation rationale and detailed coverage alignment.
-   **Improved Organization:** Reports organized by customer UUID.

## Future Considerations: Quantifying Recommendation Suitability

(This section remains unchanged)

### LLM-Based Metrics
...

### Programmatic (Non-LLM) Metrics
...

---

*Implementation Plan:*

## 1. Prerequisite: Add Customer ID to Filenames (Completed)

-   **Status:** Completed.
-   **Implementation:**
    - [x] The `scripts/data_generation/generate_transcripts.py` script now generates a UUID for each transcript.
    - [x] The output filename format is: `transcript_{scenario_name_or_no_scenario}_{customer_id}.json`. This uses the scenario name if provided, "no_scenario" otherwise, and includes the generated UUID (`customer_id`).
-   **Downstream Impact:**
    - [x] Evaluation scripts (`scripts/evaluation/transcript_evaluation/`) read the scenario name from *within* the JSON file, not the filename, so they were unaffected by this change.
    - [x] Parsing scripts (`src/utils/transcript_processing.py`) handle the JSON content, outputting `parsed_transcript_{scenario_name}_{customer_id}.json`.
    - [x] Extractor script (`src/agents/extractor.py`) uses the input filename to generate its output filename, outputting `requirements_{scenario_name}_{customer_id}.json`.
    - [x] The new comparison script (this plan) will use the `customer_id` (UUID) for its input discovery and output naming.

## 2. Coverage Requirements & Scenario Integration (Completed)

(This section remains unchanged)
...

## 3. Pricing Tier Ranking Data (Completed)

(This section remains unchanged)
...

## 4. New Policy Comparison Logic (Insurer-Level) (Completed)

-   [x] **Modify/Replace Comparison Script (`scripts/generate_policy_comparison.py`)**:
    -   [x] **Input Handling**:
        -   [x] Modify script to accept a single mandatory command-line argument: `--customer_id` (expecting the UUID).
        -   [x] Use `customer_id` (UUID) and `glob` to find the specific requirements file: `data/extracted_customer_requirements/requirements_*_{customer_id}.json`. Handle errors if not found or multiple found.
        -   [x] Scan `data/policies/processed/` to dynamically identify available insurers (e.g., 'fwd', 'income') and group their corresponding policy JSON file paths.
    -   [x] **Data Loading**:
        -   [x] Load the customer requirements JSON content.
        -   [x] Import and load the `INSURER_TIER_RANKING` dictionary from `data/policies/pricing_tiers/tier_rankings.py`.
    -   [x] **Processing Loop (Per Insurer)**:
        -   [x] Iterate through each identified insurer.
        -   [x] Load the content of all policy JSON files for the current insurer.
        -   [x] Retrieve the price ranking list for the insurer from `INSURER_TIER_RANKING`. Handle missing insurers gracefully.
        -   [x] **Construct LLM Prompt**: Build a single prompt using the updated template below, filling in dynamic content.
        -   [x] **LLM Call**: Use `LLMService.generate_content` to execute the prompt. Consider using asynchronous execution (`asyncio`) to process multiple insurers concurrently.
        -   [x] **Output Handling**:
            -   [x] Create the customer-specific output directory: `results/{customer_id}/` (using the UUID).
            -   [x] Save the LLM's Markdown response to `results/{customer_id}/policy_comparison_report_{insurer}_{customer_id}.md` (using the UUID).
    -   [x] **LLM Prompt Template (Updated)**:
        ```text
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
            *   After providing the justification, create a new section titled: `## Detailed Coverage Analysis for Recommended Tier: {Recommended Tier Name}` (replace `{Recommended Tier Name}` with the actual name of the tier you selected).
            *   Inside this section, iterate through *each requirement* listed in the customer's `insurance_coverage_type` array.
            *   For each customer requirement, create a subsection: `### Requirement: {Requirement Name}`.
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
                *   This requirement is not explicitly covered under the {Recommended Tier Name} tier based on the provided policy details.
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
            *   After the detailed coverage analysis, create a final section titled: `## Summary for Recommended Tier: {Recommended Tier Name}`.
            *   Provide a brief, balanced summary (e.g., 2-3 bullet points for strengths, 2-3 for weaknesses/gaps) highlighting the most important ways the *recommended tier* aligns well with the customer's key requirements, and any significant areas where it falls short or doesn't provide coverage based on the requirements. This summary should help in comparing this tier against recommendations from other insurers.

        # Output Format:
        Provide your response in Markdown format using the following structure:
        1. Start with the recommended tier name (pre-filled below).
        2. Provide your detailed justification (Task 5).
        3. Include the detailed coverage analysis section (Task 6).
        4. Include the summary section (Task 7).

        **Recommended Tier:** :
        ```
    -   [x] **Refactoring**: Remove old tier-level comparison logic. Update docstrings and comments.
    -   [x] **Error Handling**: Add checks for missing files/data and handle potential LLM errors. (Includes fixes for prompt formatting KeyErrors).

## Rationale for Change

-   Reduce the number of LLM calls required for policy comparison by analyzing all tiers of an insurer simultaneously, rather than one tier per call.
-   Maintain a clear comparison and justification process focused on selecting the best overall tier for the customer.
-   Provide a detailed, transparent breakdown of how the recommended policy aligns with specific customer needs.
-   Improve organization of output reports.
