# Policy Comparison Workflow Changes: Insurer-Level Analysis

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

**Goal:** To significantly reduce LLM calls while still producing a comparable analysis by comparing all tiers of a single insurer within one LLM call.

**New Process Overview:**
1.  **Group Policies:** Group the processed policy JSON files by insurer.
2.  **Insurer-Level Prompt:** For each insurer, construct a single, comprehensive prompt containing:
    -   The customer's requirements (from the extracted requirements JSON).
    -   The details of *all* policy tiers for that specific insurer (from their processed policy JSON files, e.g., `fwd_First.json`, `fwd_Premium.json`, etc.).
    -   A predefined ranking of the insurer's tiers by price (cheapest to most expensive).
3.  **LLM Task:** Instruct the LLM to:
    -   Analyze how well each tier (within that insurer) meets the requirements holistically.
    -   Explicitly state that coverages cannot be mixed and matched.
    -   Select the *single best tier* for that insurer, using the price ranking as a tie-breaker (choose the cheapest among equally suitable tiers).
    -   Provide justification for the choice.
4.  **Output:** Generate one Markdown report *per insurer*, summarizing the analysis and identifying the recommended tier for that insurer (e.g., `policy_comparison_report_{insurer}_{customer_id}.md`).

**Rationale:**
-   **Reduced LLM Calls:** Instead of one call per tier, this requires only one call per *insurer* (e.g., 3 insurers = 3 calls), drastically reducing cost and latency.
-   **Integrated Decision:** The LLM performs the tier selection and tie-breaking within the single call for each insurer.
-   **Clearer Output:** Produces one report per insurer, simplifying the subsequent step of comparing the top recommendation from each insurer.

---

*Implementation Plan:*

## 1. Prerequisite: Add Customer ID to Filenames (Completed)

-   **Status:** Completed.
-   **Implementation:**
    -   The `scripts/data_generation/generate_transcripts.py` script now generates a UUID for each transcript.
    -   The output filename format is: `transcript_{scenario_name_or_no_scenario}_{customer_id}.json`. This uses the scenario name if provided, "no_scenario" otherwise, and includes the generated UUID (`customer_id`).
-   **Downstream Impact:**
    -   Evaluation scripts (`scripts/evaluation/transcript_evaluation/`) read the scenario name from *within* the JSON file, not the filename, so they were unaffected by this change.
    -   Parsing scripts (`src/utils/transcript_processing.py`) handle the JSON content.
    -   Extractor script (`src/agents/extractor.py`) uses the input filename to generate its output filename, so it implicitly handles the `customer_id`.
    -   The new comparison script (this plan) will use the `customer_id` for its output naming.

## 2. Coverage Requirements & Scenario Integration

-   [ ] **Update Coverage Requirements Logic**:
    -   [ ] **(Placeholder)**: The logic in `data/coverage_requirements/coverage_requirements.py` will be updated by another team member to integrate scenario definitions from `data/scenarios/*.json`. The exact mechanism (addition, prioritization, context influence) is TBD.
    -   [ ] Document the final integration approach here once merged.

## 3. Pricing Tier Ranking Data

-   [ ] **Manual Data Creation**:
    -   [ ] Create a Python dictionary or similar structure (e.g., in a new config file or within the comparison script) to store the relative price ranking of tiers for *each insurer*.
    -   [ ] Format Example:
        ```python
        INSURER_TIER_RANKING = {
            "fwd": ["First", "Premium", "Business"], # Cheapest to Most Expensive
            "income": ["Classic", "Deluxe", "Preferred"],
            "sompo": ["Vital", "Deluxe", "Elite", "GO Japan!"] 
            # Note: GO Japan! position needs confirmation based on price/value
        }
        ```
    -   [ ] This ranking will be manually determined by reviewing policy documents/pricing information.

## 4. New Policy Comparison Logic (Insurer-Level)

-   [ ] **Modify/Replace Comparison Script (`scripts/generate_policy_comparison.py` or new script)**:
    -   [ ] **Input**:
        -   Customer requirements JSON (e.g., `data/extracted_customer_requirements/requirements_{customer_id}.json`).
        -   *All* processed policy JSON files for a *single insurer* (e.g., `fwd_First.json`, `fwd_Premium.json`, `fwd_Business.json`).
        -   The `INSURER_TIER_RANKING` data structure (from step 3).
    -   [ ] **Processing**:
        -   [ ] Group processed policy JSONs by insurer.
        -   [ ] For each insurer:
            -   [ ] Construct a single prompt for the LLM.
            -   [ ] Include the customer requirements JSON content.
            -   [ ] Include the content of *all* policy tiers for that insurer.
            -   [ ] Include the `INSURER_TIER_RANKING` for that insurer.
            -   [ ] **Prompt Instructions**:
                -   Analyze how well *each tier* meets the customer requirements holistically.
                -   Explicitly state that coverages *cannot* be mixed and matched between tiers.
                -   Select the *single most suitable tier* based on the overall fit with requirements.
                -   **Tie-breaking rule**: If multiple tiers are equally suitable, select the tier that appears earlier in the provided `INSURER_TIER_RANKING` list (i.e., the cheaper one).
                -   Provide a clear justification for the chosen tier, explaining why it's the best fit and how the tie-breaking rule was applied if necessary.
    -   [ ] **Output**:
        -   [ ] Generate a Markdown report summarizing the analysis and the final chosen tier for the insurer.
        -   [ ] Use the new filename convention: `policy_comparison_report_{insurer}_{customer_id}.md`.
        -   [ ] Save the report to the `results/` directory (or a subdirectory structure based on `customer_id`).

## Rationale for Change

-   Reduce the number of LLM calls required for policy comparison by analyzing all tiers of an insurer simultaneously, rather than one tier per call.
-   Maintain a clear comparison and justification process focused on selecting the best overall tier for the customer.
