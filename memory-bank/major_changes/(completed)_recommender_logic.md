# Recommender Logic Implementation Plan

**Status:** Completed

## 1. Context & Goal

-   **Current Stage**: The system generates detailed insurer-level policy comparison reports (`results/{uuid}/policy_comparison_report_{insurer}_{uuid}.md`) by comparing extracted customer requirements (`data/extracted_customer_requirements/requirements_{scenario_name}_{uuid}.json`) against processed policy data (`data/policies/processed/{insurer}_{tier}.json`).
-   **Need**: After generating these individual insurer reports, a mechanism is required to synthesize the findings and determine the single *most suitable* policy overall for the customer.
-   **Goal**: Implement a recommendation logic that analyzes the comparison reports to select and justify the final recommended policy (Insurer + Tier).

## 2. Proposed Approach: Hybrid (Ranking + LLM Re-ranking)

-   **Overview**: This approach involves two stages:
    1.  **Initial Ranking**: A rule-based scoring system analyzes the comparison reports based on the explicit "Fully Met", "Partially Met", or "Not Met" assessment for each requirement to generate a quantitative score.
    2.  **LLM Re-ranking**: The comparison reports for only the top candidates (based on the Stage 1 score) are fed into a final LLM call, which performs a nuanced comparison and selects the ultimate winner with justification.
-   **Rationale**: Balances objective filtering based on explicit requirement assessments with the nuanced understanding capabilities of an LLM for the final decision, improving efficiency and potentially accuracy compared to a pure LLM or pure rule-based approach.

### Stage Interaction and Rationale Details

-   **Stage 1 Role (Quantitative Filter):**
    -   Provides a fast, objective initial ranking based *solely* on the count and type of requirement assessments ("Fully Met", "Partially Met", "Not Met").
    -   Acts as an efficient filter to identify a small set of promising candidates.
    -   **Limitations:** The score ignores requirement importance (all requirements weighted equally), the degree of partial coverage (all "Partially Met" get 0.5 points), and qualitative details found in the report's justification/summary text.
-   **Stage 2 Role (Qualitative Re-ranking):**
    -   Analyzes the *full text* of the comparison reports for only the top 2-3 candidates from Stage 1.
    -   Performs a holistic, nuanced comparison considering factors missed by the Stage 1 score (e.g., importance of specific requirements, severity of partial limitations, trade-offs mentioned in justifications).
    -   Selects the final recommended policy based on this deeper, qualitative understanding.
-   **Potential for Different Ranking:** It is *expected* and *by design* that the final recommendation from Stage 2 might differ from the strict #1 policy ranked by the Stage 1 score. This occurs when the qualitative analysis reveals nuances (e.g., the #1 policy has a minor flaw in a critical area, while the #2 policy is a better overall fit despite a slightly lower raw score). This reflects the strength of the hybrid approach – combining objective breadth with qualitative depth.
-   **Efficiency:** This two-stage process avoids the need for the LLM to perform slow, expensive, detailed comparisons across *all* policies, focusing its nuanced reasoning only on the most likely candidates identified by the efficient Stage 1 scoring.

## 3. Stage 1: Initial Ranking Logic - Additive Score based on Coverage Assessment

-   **Objective**: To quantitatively rank the recommended tiers from each insurer's comparison report based *solely* on how well they meet each customer requirement, according to the explicit assessment provided in the report.

-   **How it Works**:
    1.  **Parse Reports**: For each insurer's comparison report (`.md` file) associated with the customer `uuid`:
        *   Extract the exact assessment text (expected to be "Fully Met", "Partially Met", or "Not Met") from the `*   **Coverage Assessment:**` line under each `### Requirement:` header.
    2.  **Calculate Score**:
        *   Initialize the score for the policy to 0.0.
        *   For each requirement analyzed in the report:
            *   If the extracted assessment text is exactly "Fully Met", add **1.0 point** to the score.
            *   If the extracted assessment text is exactly "Partially Met", add **0.5 points** to the score.
            *   If the extracted assessment text is exactly "Not Met", add **0.0 points** to the score.
        *   The final score is the sum of points across all requirements.
    3.  **Rank**: Sort the policies based on their final scores (highest first).
    4.  **Select Top Candidates**: Choose the top 2 or 3 policies from this ranking.

-   **Consistency of Requirements**:
    *   **Why it's Consistent**: The `scripts/generate_policy_comparison.py` script uses the *single* customer requirements JSON file (`requirements_{scenario_name}_{uuid}.json`) as the basis for comparison against *all* insurers for that specific customer (`uuid`).
    *   **Implication**: All comparison reports generated for the same `uuid` are prompted to evaluate the exact same set of requirements. The maximum possible score will be equal to the total number of requirements analyzed (`N`). Differences in scores arise solely from the explicit assessments ("Fully Met", "Partially Met", "Not Met") provided for each requirement in the report.

-   **Scoring Rationale**:
    *   This system directly quantifies how well a policy meets the stated requirements based on the explicit assessment generated by the comparison LLM (following strict prompt instructions).
    *   It rewards policies that fully meet more requirements and partially penalizes those that only partially meet them.
    *   Policies that fail to meet requirements receive no points for those specific requirements.
    *   The `Weaknesses/Gaps` summary section is *not* used in this scoring calculation, ensuring the score is based purely on the per-requirement assessment.
    *   This prioritizes policies with the highest degree of explicit requirement fulfillment.

## 4. Stage 2: LLM Re-ranking (Current Implementation)

-   **Input**:
    *   The full Markdown comparison reports for the top 2-3 candidates identified in Stage 1.
    *   The parsed customer transcript (`data/transcripts/processed/parsed_transcript_*_{uuid}.json`).
    *   **(Removed):** The extracted requirements summary (`json_dict`) is no longer passed as input.
-   **Process**: Feed the selected reports and the transcript into a final LLM call (using `LLMService` via `scripts/generate_recommendation_report.py`).
-   **Prompting**: Instruct the LLM to:
    *   Act as an expert insurance advisor.
    *   Carefully review the provided reports for the finalist policies AND the customer transcript.
    *   Analyze the transcript for prioritization cues (emphasis, repetition, direct statements).
    *   Compare the candidates' strengths, weaknesses, coverage details, and justifications *relative to each other*, using the transcript analysis to weight the importance of different needs.
    *   Select the single best policy (Insurer + Tier) based on this context-aware comparison.
    *   Provide a clear, comprehensive justification for the final choice, explaining the trade-offs considered and referencing transcript cues if applicable.
-   **Output**: Structured JSON output (`FinalRecommendation` model) containing the recommended policy (Insurer, Tier) and the textual justification.

## 5. Implementation Tasks

-   [x] **Task 0 (Prerequisite)**: Refine the `PROMPT_TEMPLATE_INSURER` in `scripts/generate_policy_comparison.py`:
    -   Define a strict, consistent Markdown structure for the report output (exact headers, section order, formatting).
    -   Incorporate few-shot examples (positive/negative) and explicit instructions for the structure, including the comparative analysis within the `Justification` section.
    -   **Note:** The `Coverage Assessment:` instruction must be updated to require *only* the exact phrases "Fully Met", "Partially Met", or "Not Met". Examples must be updated to clearly demonstrate this exact usage.
    -   **Proposed Prompt Draft:**
        ```python
        # Placeholder for the actual prompt variable in generate_policy_comparison.py
        PROMPT_TEMPLATE_INSURER = """
        # Role: Travel Insurance Policy Advisor

        # Goal:
        1. Analyze the provided customer requirements against all available travel insurance policy tiers for the specified insurer ({insurer_name}).
        2. Select the SINGLE most suitable tier for this customer based on a holistic assessment, specific rules, and price tie-breaking.
        3. Provide a clear justification for your choice, including a comparison between the tiers.
        4. Provide a detailed breakdown of how the *recommended tier* covers each specific customer requirement, using granular data from the policy JSON.
        5. Provide a concise summary of the recommended tier's strengths and weaknesses relative to the requirements.

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
        2.  **No Mix-and-Match Rule:** You MUST understand that the customer must choose one complete tier; coverages *cannot* be mixed and matched between different tiers. Factor this rule into your analysis and justification.
        3.  **Select Single Best Tier:** Based on your holistic analysis and the No Mix-and-Match Rule, identify the *single* policy tier from {insurer_name} that provides the best overall fit for the customer's stated requirements.
        4.  **Tie-Breaking Rule:** If multiple tiers appear equally suitable after your holistic analysis, you MUST select the tier that appears earliest in the provided 'Tier Price Ranking' list (i.e., the cheapest among the equally suitable options).
        5.  **Generate Report:** Create a detailed Markdown report STRICTLY adhering to the format specified below.

        **Output Report Structure (MUST Follow Exactly):**

        You MUST generate the report using the following Markdown structure. Use the exact headers, formatting (bolding), and section order shown.

        ```markdown
        **Recommended Tier:** : [Insert Recommended Tier Name Here]

        **Justification:**

        [**MUST include a comparison across the different tiers for this insurer ({insurer_name}).** Explain how the tiers differ in relation to key customer requirements (referencing the No Mix-and-Match rule if relevant). THEN, provide a concise explanation for why the recommended tier was chosen over the others from THIS insurer, referencing the comparison points and key customer requirements. If the Tie-Breaking Rule was used, explicitly state this and explain why the tied tiers were considered equally suitable before applying the price ranking.]

        ## Detailed Coverage Analysis for Recommended Tier: [Insert Recommended Tier Name Here]

        ### Requirement: [Insert Requirement Name 1 from Customer Requirements]

        *   **Policy Coverage:** [Extract relevant Policy Benefit Name from Policy Data]
            *   **Base Limits:** [Extract Base Limits details (type, value, basis)]
            *   **Conditional Limits:** [Extract Conditional Limits details (condition, type, value, basis, source) or 'null']
            *   **Source Specific Details:** [Extract ALL Source Specific Details (snippet, source, page, section). Do not summarize or omit.]
        *   [Add more Policy Coverage sections if multiple benefits relate to this requirement]
        *   **Coverage Assessment:** [Explicitly state if this requirement is Fully Met, Partially Met (explain why), or Not Met/Critically Limited based on the policy details above. Be specific about gaps.]

        ### Requirement: [Insert Requirement Name 2 from Customer Requirements]

        *   **Policy Coverage:** [Extract relevant Policy Benefit Name]
            *   ... [Extract ALL Details as above] ...
        *   **Coverage Assessment:** [Explicit statement: Fully Met, Partially Met (explain), or Not Met/Critically Limited]

        [... Repeat the '### Requirement:' section for ALL requirements listed in the customer requirements JSON ...]

        ## Summary for Recommended Tier: [Insert Recommended Tier Name Here]

        *   **Strengths:**
            *   [List key advantages of this tier in meeting the customer's requirements.]
        *   **Weaknesses/Gaps:**
            *   [List key shortcomings or requirements explicitly identified as Not Met or Partially Met/Critically Limited in the Coverage Assessment sections above.]

        ```

        **Examples:**

        **Positive Example (Illustrative - Includes Tier Comparison & Assessment):**

        ```markdown
        **Recommended Tier:** : Elite

        **Justification:**

        Comparing the SOMPO Vital, Deluxe, and Elite tiers against the customer's golfing trip needs: Vital lacks specific golf cover entirely. Deluxe covers equipment loss but misses unused green fees, buggy damage, and hole-in-one benefits (Section 36 N.A.). Elite includes a dedicated 'Golf Cover' section addressing all these specific requirements. While all tiers cover core needs like Medical and Cancellation, Elite offers the highest limits ($1M Medical, $15k Cancellation). Given the No Mix-and-Match rule, only Elite provides the complete package needed.

        Therefore, the Elite tier is recommended as it is the only tier providing the specific, comprehensive golf coverage requested, alongside the highest limits for core requirements, aligning with the customer's stated priorities.

        ## Detailed Coverage Analysis for Recommended Tier: Elite

        ### Requirement: Medical Coverage

        *   **Policy Coverage:** Medical Expenses Incurred Overseas
            *   **Base Limits:** Type: Per Insured Person - 70 years & below, Limit: 1000000, Basis: null ...
            *   **Conditional Limits:** null
            *   **Source Specific Details:** Detail: Covers outpatient and hospitalisation medical expenses... Source: Policy Wording, Page: 3, Section: 2
        *   **Policy Coverage:** Emergency Medical Evacuation & Repatriation...
            *   **Base Limits:** Type: Per Insured Person - up to 70 years, Limit: Unlimited, Basis: null ...
            *   ...
        *   **Coverage Assessment:** Fully Met. Provides high limits ($1M) and unlimited evacuation, meeting the need for comprehensive medical protection.

        ### Requirement: Reimbursement for unused green fees if unable to play due to injury

        *   **Policy Coverage:** Golf Cover
            *   **Base Limits:** Type: Unused green fees, Limit: 250, Basis: null
            *   **Conditional Limits:** null
            *   **Source Specific Details:** Detail: Covers reimbursement of unused green fees due to covered reasons. Source: Policy Wording, Page: 6, Section: 36
        *   **Coverage Assessment:** Fully Met. Section 36 explicitly covers unused green fees up to $250.

        [... Other requirements ...]

        ## Summary for Recommended Tier: Elite

        *   **Strengths:**
            *   Complete coverage for all specific golf requirements via dedicated Golf Cover section.
            *   Highest limits for core medical, cancellation, and baggage needs.
            *   Unlimited medical evacuation for under 70s.
        *   **Weaknesses/Gaps:**
            *   Higher cost compared to other tiers.
            *   Specific limits for some golf benefits (e.g., $250 green fees, $500 buggy damage) might be lower than potential costs.
        ```

        **Negative Example (Illustrative - Lacks Tier Comparison & Assessment):**

        ```markdown
        **Recommended Tier:** : Elite

        **Justification:**

        The Elite tier is recommended because it meets the customer's needs for their golfing trip, including specific golf cover and high limits for medical and cancellation. It aligns with their priorities.

        ## Detailed Coverage Analysis for Recommended Tier: Elite

        ### Requirement: Medical Coverage
        *   **Policy Coverage:** Medical Expenses Incurred Overseas
            *   **Base Limits:** $1,000,000
            *   **Source Specific Details:** Covers medical expenses.
        *   **Policy Coverage:** Emergency Medical Evacuation
            *   **Base Limits:** Unlimited
            *   **Source Specific Details:** Covers evacuation.
        *(Note: Missing Coverage Assessment)*

        ### Requirement: Reimbursement for unused green fees if unable to play due to injury
        *   **Policy Coverage:** Golf Cover
            *   **Base Limits:** $250
            *   **Source Specific Details:** Covers green fees.
        *(Note: Missing Coverage Assessment)*

        [... Other requirements ...]

        ## Summary for Recommended Tier: Elite
        *   **Strengths:** Good coverage.
        *   **Weaknesses/Gaps:** Cost.
        ```
        *(Note how the negative example lacks the initial comparison in the Justification, omits the crucial 'Coverage Assessment' line in the detailed analysis, and provides overly summarized details.)*

        **Final Instruction:** Generate ONLY the Markdown report based on the analysis, strictly following the specified structure, incorporating the tier comparison in the Justification, including the Coverage Assessment for each requirement, and ensuring all granular details are extracted. Do not add any introductory or concluding remarks outside of the defined report structure.
        """
        ```
    -   Test the updated prompt by regenerating sample reports and verifying the improved consistency.
-   [x] **Task 1**: Develop a robust Markdown parser function (`parse_comparison_report` in `scripts/generate_recommendation_report.py`) based on the *refined* report structure from Task 0 to extract:
    -   Recommended Tier name.
    -   For each requirement: Name and the exact text following the `Coverage Assessment:` line.
    -   *(Optional but recommended for context/debugging: Full analysis text block for each requirement, Strengths/Weaknesses summary text)*.
-   [x] **Task 2**: Implement the Stage 1 scoring logic (`calculate_stage1_score` in `scripts/generate_recommendation_report.py`) using the parser output from Task 1.
    -   **Scoring Logic:**
        -   Initialize score = 0.0.
        -   Iterate through the parsed requirements.
        -   For each requirement, check the extracted `assessment` text:
            -   If assessment is exactly "Fully Met", add 1.0 point.
            -   If assessment is exactly "Partially Met", add 0.5 points.
            -   If assessment is exactly "Not Met", add 0.0 points.
        -   Sum the points to get the final score.
    -   **Note:** This scoring method relies *only* on the exact assessment strings ("Fully Met", "Partially Met", "Not Met") and ignores the summary section.
-   [x] **Task 3**: Create a new script or function (in `scripts/generate_recommendation_report.py`) that orchestrates the process:
    -   Takes `customer_id` (`uuid`) as input.
    -   Finds relevant comparison reports (assuming they are generated using the refined prompt from Task 0).
    -   Runs the Stage 1 ranking (Task 2).
    -   Selects top candidates.
-   [x] **Task 4**: Implement the Stage 2 LLM Re-ranking call:
    -   Develop the final comparison prompt (input will be the refined reports for top candidates).
    -   **Update Prompt:** Instruct the LLM to weave key source references (page/section) into the justification where relevant.
    -   Integrate with `LLMService`.
    -   Define the *intermediate* output structure (e.g., Pydantic model `FinalRecommendation` containing insurer, tier, justification).
-   [x] **Task 5**: Integrate Stage 1 and Stage 2 within the orchestrating script/function (Task 3).
    -   Pass necessary data (Stage 1 results, Stage 2 justification) to the new report generation step (Task 6).
-   [x] **Task 6**: Implement the final recommendation output mechanism and format.
    -   **Format:** Customer-friendly Markdown (`.md`).
    -   **Content:**
        -   Clear statement of the final recommended policy (Insurer + Tier).
        -   The detailed justification from the Stage 2 LLM (which should include source references).
        -   A section showing the Top 3 policies from Stage 1 ranking, including their scores.
        -   A brief explanation of the Stage 1 scoring method (Fully Met=1.0, Partially Met=0.5, Not Met=0.0).
        -   A list of other policies analyzed in Stage 1 but not in the Top 3 (Insurer - Tier: Score), or a note if none.
    -   **Mechanism:** Save the generated Markdown report to `results/{uuid}/recommendation_report_{uuid}.md`.
-   [x] **Task 7**: Add/Update tests for the parser (Task 1), scoring logic (Task 2), and the *new* Markdown report generation (Task 6).
-   [x] **Task 8**: Update relevant Memory Bank documents (`activeContext.md`, `systemPatterns.md`, `progress.md`) upon completion of the recommender implementation.
-   [x] **Task 10 (Evaluation): Define Scenario Ground Truth:** Manually determine the expected best policy/policies for each defined scenario (`golf_coverage`, `pet_care_coverage`, `public_transport_double_cover`, `uncovered_cancellation_reason`) based on their specific requirements and available policy data (JSON extracts). Store this mapping in `data/evaluation/scenario_ground_truth.json`.
    *   **Structure:** The JSON should map each `scenario_name` to an object containing:
        *   `status`: Either `"full_cover_available"` (if standard policies fully meet the core need) or `"partial_cover_only"` (if only partial solutions or specific add-ons address the need).
        *   `expected_policies`: A list of objects, where each object contains `insurer`, `tier`, and a brief `justification`. This list can contain multiple entries if several policies are considered equally valid ground truths.
        *   **Rationale:** Provides a structured benchmark, including justifications and status, for evaluating pipeline performance on critical test cases, acknowledging scenarios where full coverage might not be standard.
-   [x] **Task 11 (Evaluation): Implement Scenario Recommendation Evaluation Script:** Create/Update the script `scripts/evaluation/scenario_evaluation/evaluate_scenario_recommendations.py`.
    *   **Update Rationale (2025-04-14):** The initial implementation evaluated all reports and filtered internally. A simpler, more efficient approach is preferred: filter upfront based on scenario if specified.
    *   **Implemented Logic (as of 2025-04-14):**
        *   Added an optional command-line argument `--scenario` (or `-s`) to specify a single scenario name.
        *   If `--scenario` is provided:
            *   Identify all relevant UUIDs by finding transcript files matching `data/transcripts/raw/synthetic/transcript_{scenario_name}_*.json`.
            *   Iterate through subdirectories in `results/`. If a subdirectory name (UUID) matches one of the relevant UUIDs, process the recommendation report within it. Skip non-matching UUIDs.
        *   If `--scenario` is *not* provided:
            *   Iterate through all subdirectories in `results/`.
            *   For each report, find the corresponding transcript, extract the scenario name. If it's a specific scenario (not 'no_scenario') and exists in the ground truth, evaluate it.
        *   **Evaluation Core (Remains the same):**
            *   Load the structured ground truth mapping (from Task 10).
            *   Parse the recommended policy (`insurer`, `tier`) from the report.
            *   Retrieve the `status` and `expected_policies` list from the ground truth.
            *   Check if the recommended policy matches any entry in the `expected_policies` list.
            *   Output evaluation results (summary to console, optional detailed JSON to file), interpreting the results based on the ground truth `status` (PASS, FAIL, PASS (Partial Cover)).
    *   **Original Rationale (Benefits of Evaluation):** Automates checking if the pipeline produces expected outcomes for targeted scenarios. Useful for:
        *   **Regression Detection:** Identify if changes negatively impact performance.
        *   **Faithfulness/Correctness:** Verify adherence to expected behavior.
        *   **Objective Comparison:** Benchmark different models/prompts/logic.
-   [x] **Task 12 (Transcript Context for Justification):** Updated Stage 2 prompt (Task 4) to instruct the LLM to reference transcript context/cues when generating the justification, enabling personalization in the final report (Task 6).
