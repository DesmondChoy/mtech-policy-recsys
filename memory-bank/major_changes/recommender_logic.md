# Recommender Logic Implementation Plan

## 1. Context & Goal

-   **Current Stage**: The system generates detailed insurer-level policy comparison reports (`results/{uuid}/policy_comparison_report_{insurer}_{uuid}.md`) by comparing extracted customer requirements (`data/extracted_customer_requirements/requirements_{scenario_name}_{uuid}.json`) against processed policy data (`data/policies/processed/{insurer}_{tier}.json`).
-   **Need**: After generating these individual insurer reports, a mechanism is required to synthesize the findings and determine the single *most suitable* policy overall for the customer.
-   **Goal**: Implement a recommendation logic that analyzes the comparison reports to select and justify the final recommended policy (Insurer + Tier).

## 2. Proposed Approach: Hybrid (Ranking + LLM Re-ranking)

-   **Overview**: This approach involves two stages:
    1.  **Initial Ranking**: A rule-based scoring system analyzes the comparison reports to identify the top 2-3 candidate policies based on explicit coverage gaps and weaknesses.
    2.  **LLM Re-ranking**: The comparison reports for only the top candidates are fed into a final LLM call, which performs a nuanced comparison and selects the ultimate winner with justification.
-   **Rationale**: Balances objective filtering based on report data with the nuanced understanding capabilities of an LLM for the final decision, improving efficiency and potentially accuracy compared to a pure LLM or pure rule-based approach.

## 3. Stage 1: Initial Ranking Logic - Requirement Coverage Check + Weakness Penalty

-   **Objective**: To quantitatively rank the recommended tiers from each insurer's comparison report based on how well they address the customer's requirements, filtering out policies with significant, explicitly stated shortcomings.

-   **How it Works**:
    1.  **Identify Key Requirements**: Programmatically determine the list of requirements analyzed in the reports (e.g., by parsing `### Requirement: {Requirement Name}` headers from one of the reports for that `uuid`). Let the total number of requirements be `N`.
    2.  **Parse Reports**: For each insurer's comparison report (`.md` file) associated with the customer `uuid`:
        *   Examine the detailed analysis section under each of the `N` `### Requirement:` headers. Look for explicit statements indicating non-coverage or critical limitations (e.g., "not covered", "N.A.", "excludes", specific limiting notes that negate the core need).
        *   Extract the bullet points listed under the `*   **Weaknesses/Gaps:**` section in the final summary.
    3.  **Calculate Score**:
        *   Each policy starts with a potential maximum score of `N` points.
        *   **Deduction 1 (Detailed Analysis)**: For each of the `N` requirements, if its corresponding detailed section contains an explicit statement of non-coverage or a critical limitation, subtract **1 point** from the policy's score.
        *   **Deduction 2 (Summary Weakness)**: For each *unique* key requirement mentioned in the summary's `Weaknesses/Gaps` list, subtract **0.5 points** from the policy's score.
    4.  **Rank**: Sort the policies based on their final scores (highest first).
    5.  **Select Top Candidates**: Choose the top 2 or 3 policies from this ranking.

-   **Consistency of Requirements**:
    *   **Why it's Consistent**: The `scripts/generate_policy_comparison.py` script uses the *single* customer requirements JSON file (`requirements_{scenario_name}_{uuid}.json`) as the basis for comparison against *all* insurers for that specific customer (`uuid`).
    *   **Implication**: All comparison reports generated for the same `uuid` are prompted to evaluate the exact same set of `N` requirements. Therefore, the starting maximum score (`N`) should be identical for all policies being ranked for that customer. Differences arise only from the *deductions* based on how well each policy meets those requirements according to its report.

-   **Scoring Rationale**:
    *   The system rewards policies that appear to cover requirements based on the detailed analysis (fewer -1 deductions).
    *   It penalizes policies where the comparison LLM explicitly identified non-coverage or critical limitations in the details.
    *   It further penalizes policies where weaknesses related to key requirements were significant enough to be highlighted in the final summary (the -0.5 deduction).
    *   This prioritizes policies with fewer identified major flaws.

## 4. Stage 2: LLM Re-ranking (High-Level Plan)

-   **Input**: The full Markdown comparison reports for the top 2-3 candidates identified in Stage 1.
-   **Process**: Feed these selected reports into a final LLM call (using `LLMService`).
-   **Prompting**: Instruct the LLM to:
    *   Act as an expert insurance advisor.
    *   Carefully review the provided reports for the finalist policies.
    *   Compare their strengths, weaknesses, coverage details, and justifications *relative to each other* and the original customer needs (context might need to be provided).
    *   Select the single best policy (Insurer + Tier).
    *   Provide a clear, comprehensive justification for the final choice, explaining the trade-offs considered.
-   **Output**: Structured output (e.g., JSON) containing the recommended policy (Insurer, Tier) and the textual justification.

## 5. Implementation Tasks

-   [ ] **Task 0 (Prerequisite)**: Refine the `PROMPT_TEMPLATE_INSURER` in `scripts/generate_policy_comparison.py`:
    -   Define a strict, consistent Markdown structure for the report output (exact headers, section order, formatting).
    -   Incorporate few-shot examples (positive/negative) and explicit instructions for the structure, including the comparative analysis within the `Justification` section.
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
-   [ ] **Task 1**: Develop a robust Markdown parser function based on the *refined* report structure from Task 0 to extract:
    -   List of requirement names (from `### Requirement:` headers).
    -   Content of each requirement's detailed analysis section (including the `Coverage Assessment` statement).
    -   List of bullet points under the `Weaknesses/Gaps` summary.
-   [ ] **Task 2**: Implement the Stage 1 scoring logic (`Requirement Coverage Check + Weakness Penalty`) using the parser output from Task 1.
    -   Define logic/keywords to identify "explicit non-coverage or critical limitation" based on the `Coverage Assessment` statement and detailed text.
-   [ ] **Task 3**: Create a new script or function (e.g., in `src/agents/recommender.py` or `scripts/generate_recommendation.py`) that orchestrates the process:
    -   Takes `customer_id` (`uuid`) as input.
    -   Finds relevant comparison reports (assuming they are generated using the refined prompt from Task 0).
    -   Runs the Stage 1 ranking (Task 2).
    -   Selects top candidates.
-   [ ] **Task 4**: Implement the Stage 2 LLM Re-ranking call:
    -   Develop the final comparison prompt (input will be the refined reports for top candidates).
    -   Integrate with `LLMService`.
    -   Define the output structure (e.g., Pydantic model).
-   [ ] **Task 5**: Integrate Stage 1 and Stage 2 within the orchestrating script/function (Task 3).
-   [ ] **Task 6**: Define the final recommendation output mechanism and format. The specific format (e.g., JSON, Markdown, HTML) and how it's presented/saved (e.g., file in `results/{uuid}/`, console output, API response) will be decided at a later stage.
-   [ ] **Task 7**: Add tests for the parser (Task 1) and scoring logic (Task 2).
-   [ ] **Task 8**: Update relevant Memory Bank documents (`activeContext.md`, `systemPatterns.md`, `progress.md`) upon completion of the recommender implementation.
