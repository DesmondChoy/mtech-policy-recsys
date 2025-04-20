# Implementation Plan: Include Transcript Analysis in Recommendation Logic

**Objective:** Enhance the Stage 2 recommendation re-ranking process in `scripts/generate_recommendation_report.py` to consider potential requirement prioritization cues derived directly from the customer's conversation transcript, **and provide the extracted requirements summary for additional context**.

**Date:** 2025-04-20
**Author:** Cline
**Status:** Completed (Revised)

---

## 1. Pain Point

The current recommendation system generates insurer-level comparison reports and then uses a Stage 2 LLM call (`scripts/generate_recommendation_report.py`) to re-rank the top candidates and select the final recommendation. However, this Stage 2 process only considers the comparison reports as input. It lacks awareness of the original customer conversation (transcript).

This leads to two potential issues:
1.  **Misaligned Recommendations:** The LLM might misinterpret the relative importance of different requirements based solely on the comparison report text (e.g., prioritizing pre-existing condition coverage mentioned in a report over a specific scenario benefit like 'public transport double cover').
2.  **Evaluation Failures:** Recommendations might fail scenario evaluations (`evaluate_scenario_recommendations.py`) because the chosen policy doesn't match the ground truth, even if the ground truth policy was highly ranked in Stage 1, due to the LLM prioritizing other factors in Stage 2 without transcript context.

## 2. Diagnosis

The root cause lies in the inputs and instructions provided to the Stage 2 LLM re-ranking prompt (`PROMPT_TEMPLATE_STAGE2` within `scripts/generate_recommendation_report.py`):

-   **Missing Input:** The prompt currently only accepts the comparison reports of the top candidates. It does not receive the customer's transcript.
-   **Lack of Prioritization Instruction:** The prompt asks the LLM to perform a "nuanced comparison" and consider "most critical" requirements but provides no mechanism or data (like the transcript) for the LLM to determine *which* requirements *are* most critical from the customer's perspective. It relies on the LLM's interpretation of the comparison reports alone or assumes equal weighting.

## 3. Proposed Solution (Revised)

Modify the `scripts/generate_recommendation_report.py` script and its Stage 2 prompt to incorporate the parsed customer transcript:

1.  **Input Enhancement:**
    *   Pass the content of the relevant parsed transcript (`data/transcripts/processed/parsed_transcript_*_{uuid}.json`) to the Stage 2 LLM prompt.
    *   **(Revision):** The extracted requirements summary (`json_dict`) was initially included but subsequently removed to simplify the prompt and rely solely on the transcript for prioritization cues.
2.  **Instruction Enhancement:** Update the prompt to explicitly instruct the LLM to:
    *   Analyze the provided transcript dialogue for any cues indicating customer prioritization of specific requirements (e.g., emphasis, repetition, direct statements like "this is non-negotiable").
    *   If prioritization cues are detected, use this understanding to inform the re-ranking of candidate policies and the justification.
    *   If no clear prioritization cues are found in the transcript, default to assuming all requirements carry equal weight when performing the re-ranking.

This will allow the Stage 2 re-ranking to be more context-aware, potentially leading to recommendations that better reflect the customer's actual priorities and improve alignment with scenario evaluation ground truths.

## 4. Implementation Steps

-   [x] **1. Modify Script Logic (`scripts/generate_recommendation_report.py`)**:
    *   [x] Update the main execution flow (e.g., `main` async function) to:
        *   Define path to processed transcripts (`data/transcripts/processed/`).
        *   Construct the expected transcript filename pattern (`parsed_transcript_*_{customer_uuid}.json`) using the `customer_uuid`.
        *   Use `glob` to find the specific transcript file. Handle cases where file is not found or multiple files match (log warning, take first match).
        *   Read the content of the found transcript file (JSON list). Handle file reading errors.
        *   **(Revision):** Removed logic for loading requirements file and extracting `json_dict`.
    *   [x] Modify the call to `run_stage2_reranking` to pass only the loaded transcript data (list).

-   [x] **2. Update `run_stage2_reranking` Function**:
    *   [x] Modify the function signature to accept the transcript data parameter (`parsed_transcript_data: Optional[List[Dict[str, str]]] = None`).
    *   [x] **(Revision):** Removed the `customer_requirements_summary` parameter.
    *   [x] **Inside the function, format the `parsed_transcript_data` into a JSON string using `json.dumps()` (handle `None`).**
    *   [x] **(Revision):** Removed formatting logic for the requirements summary.
    *   [x] Update the `PROMPT_TEMPLATE_STAGE2.format(...)` call to include only the formatted transcript string (for `{parsed_transcript_json}`).

-   [x] **3. Modify `PROMPT_TEMPLATE_STAGE2`**:
    *   [x] Add a new section to the prompt template specifically for the transcript content (`# Parsed Customer Transcript:`).
    *   [x] Add a new instruction block within the `# Analysis and Recommendation Task:` section detailing the transcript analysis requirement:
        *   Instruct the LLM to review the transcript for prioritization cues.
        *   Explain how to apply these cues (or the default equal weighting) during the comparison and justification.
    *   [x] **(Revision):** Removed the `# Customer Requirements Summary:` section and updated instructions to focus solely on transcript and comparison reports. See the final prompt template below.

-   [x] **4. Testing**: (User confirmed testing completed)
    *   [x] Test the modified script with UUIDs where prioritization might be inferred from the transcript (e.g., the 'public transport double cover' case `8d447b59-6d4d-4a32-9335-fbfb8934ac63`).
    *   [x] Test with UUIDs where no clear prioritization is expected in the transcript.
    *   [x] Verify that the LLM output (recommendation and justification) reflects the transcript analysis (or lack thereof) as instructed.
    *   [x] Re-run scenario evaluations for affected scenarios to check if the results align better with the ground truth.

-   [x] **5. Update Memory Bank**:
    *   [x] Update this plan document (`include_transcript_w_rec_logic.md`) with completion status.
    *   [x] Update `recommender_logic.md` to reflect this change in the Stage 2 process.
    *   [x] Update `activeContext.md`, `progress.md`, and `systemPatterns.md` to document the change.

## 5. Final Prompt Template (`PROMPT_TEMPLATE_STAGE2` in script)

```python
# Define Prompt Template for Stage 2
PROMPT_TEMPLATE_STAGE2 = """
# Role: Expert Travel Insurance Advisor

# Goal:
Review the detailed comparison reports for the top {num_candidates} candidate policies AND the provided **customer transcript**. Select the SINGLE best overall policy (Insurer + Tier) for the customer based on a nuanced comparison of their strengths, weaknesses, alignment with customer needs (using the transcript for prioritization cues), AND any prioritization cues identified in the transcript. Provide a comprehensive justification for your final choice.

# Parsed Customer Transcript:
(This is the conversation history)
```json
{parsed_transcript_json}
```

# Candidate Policy Reports:
Here are the full comparison reports for the finalist policies identified in Stage 1:

{candidate_reports_markdown}

# Analysis and Recommendation Task:

1.  **Review Transcript:** Carefully read the provided **Parsed Customer Transcript**. Identify if the customer expressed any explicit or implicit prioritization among their requirements in the dialogue. Look for cues like:
    *   Direct statements ("This is non-negotiable", "The most important thing is...", "I'm really worried about X").
    *   Repetition or emphasis on certain topics.
    *   Emotional language associated with specific concerns.
    *   The order in which requirements were mentioned (though less reliable).
    *   If no clear prioritization cues are found, assume all requirements carry equal weight.

2.  **Review Comparison Reports:** Carefully read and understand each provided comparison report. Pay attention to the recommended tier, the detailed requirement analysis (including 'Coverage Assessment'), and the summary strengths/weaknesses for each candidate.

3.  **Compare Candidates (Informed by Transcript):** Compare the candidate policies *relative to each other*. Consider:
    *   How well does each policy meet the customer's needs, giving weight to any priorities identified in the transcript analysis (Step 1)?
    *   What are the key trade-offs between the candidates, especially concerning prioritized requirements?
    *   Which policy offers the best overall value proposition considering coverage, potential gaps, AND the customer's likely priorities based on the transcript?

4.  **Select Single Best Policy:** Based on your comparative analysis (informed by transcript prioritization), determine the single best policy (Insurer + Tier) from the candidates provided.

5.  **Provide Justification:** Write a clear, comprehensive justification explaining your final choice. This justification MUST:
    *   Explicitly state the chosen Insurer and Tier.
    *   Reference any prioritization cues identified in the transcript (Step 1) and explain how they influenced the decision. If no prioritization was found and equal weighting was assumed, state this.
    *   Compare the chosen policy against the *other finalist(s)*, highlighting the key reasons for its selection, particularly in relation to prioritized requirements (if any).
    *   Reference specific strengths, weaknesses, or coverage details from the reports to support your reasoning. Where relevant, include key source references (e.g., page or section numbers from the policy documents mentioned in the reports) to substantiate important comparison points.
    *   Explain the trade-offs considered.

6.  **Output Format:** Provide your response as a JSON object matching the following Pydantic schema:

```json
{{
  "recommended_insurer": "string",
  "recommended_tier": "string",
  "justification": "string"
}}
```

**Final Instruction:** Generate ONLY the JSON object containing the final recommendation and justification, adhering strictly to the schema provided. Do not include any introductory text, markdown formatting, or other content outside the JSON structure.
"""
```

---
