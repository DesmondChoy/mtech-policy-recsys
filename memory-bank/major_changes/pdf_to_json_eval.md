# Implementation Plan: Policy Extraction Evaluation (PDF vs. JSON)

**Objective:** Implement an automated evaluation process to verify the accuracy of the structured JSON data extracted from policy PDFs by the `scripts/extract_policy_tier.py` script. This addresses a key evaluation gap identified in the project's progress tracking.

**Date:** 2025-04-13
**Author:** Cline
**Status:** Completed

---

## 1. Pain Point

The `scripts/extract_policy_tier.py` script uses an LLM to extract structured information (coverages, limits, details, source references) from raw policy PDFs into JSON format (`data/policies/processed/`). Currently, there is no automated way to verify if this extraction is accurate and complete for a given policy tier. Manual verification is time-consuming and prone to inconsistency. This lack of automated evaluation hinders rapid iteration and objective assessment of the extraction script's performance and prompt effectiveness.

## 2. Initial User Prompt

The user provided the following initial prompt to define the evaluation task:

```text
**Input:**
1. A json document (JSON)
2. A travel insurance policy document (PDF)
**Your Task:**
Act as a meticulous data extraction assistant.
In the JSON document, pick 10 of the **coverage_categories** at random and verify the **coverage_name**, **limits**, **details** and **source_info** matches the information provided in the PDF document. You should process the provided travel insurance policy document and extract specific coverage information for the **`[POLICY TIER NAME]`** plan/tier.
**Output Format (Strict JSON):**
Your output **MUST** be a single, valid JSON object conforming to the following structure. Do **NOT** include any text before or after the JSON code block.
```json
{{
    "result": "match",
    "coverage_name": "War Cover"
}},
{{
    "result": "match",
    "coverage_name": "Flight Deviation"
}},
{{
    "result": "no match",
    "coverage_name": "Medical Expenses",
    "json_detail": "listed activites - fishing, dancing, jogging",
    "pdf_detail": "listed activites - swimming, flying",
}},
{{
    "result": "no match",
    "coverage_name": "INCONVENIENCE / LIABILITY COVERS",
    "json_detail": "limit for per family is 200",
    "pdf_detail": "limit per family is 180",
}}
```
**Crucial Instructions:**
1.  **Tier Specificity:** Extract data *only* for the `[POLICY TIER NAME]` tier. If limits are shared across tiers, use the value specified for this tier.
2.  **Placeholder:** In the JSON, if placeholder text like "Refer to Section X" is observed, you **MUST** read the relevant section(s) in the policy text within the PDF for each coverage and include the key applicable conditions, definitions, major inclusions/exclusions, or other pertinent information for that coverage and specified tier. If a benefit is not covered for a specific tier, explicitly state that if mentioned.
3.  **Currency:** Identify and include the correct currency code (e.g., "SGD").
4.  **Source Info: ** `source_info` show additional info related to the **coverage_name**, all details from the source page also should be studied for no match, missing info or extra info
5.  **Display Error: ** display clearly why the JSON document is different from the PDF document under `json_detail` and `pdf_detail`
---
Please process the provided policy document for the **`[POLICY TIER NAME]`** tier and generate the JSON output according to these instructions.
"""
```

## 3. Prompt Refinement Suggestions

Based on the initial prompt and project context, the following refinements were suggested:

1.  **Output Format Correction:** The example output showed multiple JSON objects, while the description required a single object. Suggested changing to a single JSON object containing an array (e.g., `evaluation_results`).
2.  **Handling Missing/Extra Information:** Explicitly handle cases where information is present in one source but not the other (e.g., `missing_in_pdf`, `missing_in_json`).
3.  **Clarify "Random" Selection:** Specify the sampling method (e.g., simple random sampling).
4.  **Source Info Verification:** Leverage the granular `source_specific_details` extracted by the policy script for more precise verification.
5.  **Refine "Details" Verification:** Emphasize checking key conditions, definitions, inclusions/exclusions, etc.
6.  **Error Handling:** Add instructions for handling unreadable PDFs, malformed JSON, or unidentifiable tiers.

## 4. Agreed Scope & Final Prompt (Revised for Always Including Details)

Following discussion, the scope was expanded and finalized:

*   **Two-Way Verification:** The evaluation must perform both:
    *   **JSON-to-PDF:** Verify 10 randomly selected items from the JSON against the PDF.
    *   **PDF-to-JSON:** Identify significant coverages mentioned in the PDF (for the specific tier) that are missing from the JSON.
*   **Random Selection:** Simple random sampling of 10 items from the JSON is sufficient.
*   **Output Structure:** A single JSON object containing:
    *   Metadata (`policy_tier_evaluated`, `json_source`, `pdf_source`).
    *   `evaluation_results` array (for JSON-to-PDF results, max 10 items). Possible results: `"match"`, `"no_match"`, `"missing_in_pdf"`. **Crucially, all items in this array MUST include `json_detail` and `pdf_detail` fields.**
    *   `pdf_only_findings` array (for PDF-to-JSON results).
*   **Input Method:** Use multi-modal input, sending the PDF file directly to the LLM instead of pre-extracted text.

The refined prompt incorporating these elements is:

```text
**Input:**
1. A json document (JSON) - Output from policy extraction.
2. A travel insurance policy document (PDF) - Provided directly as input, not text.

**Your Task:**
Act as a meticulous data extraction validation assistant. Your goal is to perform a two-way comparison between the provided JSON document and the provided PDF document for the **`{policy_tier_name}`** plan/tier.

**Verification Steps:**

1.  **JSON-to-PDF Verification:**
    *   From the input JSON document (content provided below), select 10 `coverage_categories` using simple random sampling.
    *   For each selected category, verify that the `coverage_name`, `limits`, `details`, and `source_info` in the JSON accurately match the information provided in the **PDF document** *for the specified `{policy_tier_name}` tier*.
    *   Record the result for each of these 10 items in the `evaluation_results` array of the output. Possible results are "match", "no_match", or "missing_in_pdf".
    *   **Crucially, for ALL results ("match", "no_match", "missing_in_pdf"), you MUST include the `json_detail` and `pdf_detail` fields.**

2.  **PDF-to-JSON Verification:**
    *   Thoroughly review the **provided PDF document**, focusing on the benefits and coverages applicable to the **`{policy_tier_name}`** tier.
    *   Identify any *significant* coverage benefits mentioned in the PDF that are *missing* from the input JSON document's `coverage_categories`.
    *   Record these findings in the `pdf_only_findings` array of the output. Focus on distinct benefits, not minor variations of existing ones.

**Input JSON Content:**
```json
{json_content}
```

**(Note: The PDF content is provided directly to the LLM as a file input, not embedded as text here.)**

**Output Format (Strict JSON):**
Your output **MUST** be a single, valid JSON object conforming to the following structure. Do **NOT** include any text before or after the JSON code block.

```json
{{
  "policy_tier_evaluated": "{policy_tier_name}",
  "json_source": "{json_path_placeholder}", // To be replaced by script
  "pdf_source": "{pdf_path_placeholder}",   // To be replaced by script
  "evaluation_results": [
    // Array for results of JSON-to-PDF verification (max 10 items)
    // Example structure for EACH item (json_detail/pdf_detail ALWAYS present):
    // {{ "result": "match", "coverage_name": "...", "json_detail": "Summary of matching details from JSON", "pdf_detail": "Summary of matching details from PDF" }}
    // {{ "result": "no_match", "coverage_name": "...", "discrepancy": "Reason for mismatch", "json_detail": "Details from JSON", "pdf_detail": "Details from PDF" }}
    // {{ "result": "missing_in_pdf", "coverage_name": "...", "json_detail": "Details from JSON", "pdf_detail": "Description of why it's missing in PDF" }}
  ],
  "pdf_only_findings": [
    // Array for results of PDF-to-JSON verification (significant missing items)
    // Example structure for each item:
    // {{ "coverage_name": "...", "pdf_detail": "...", "pdf_source_location": "..." }}
  ]
}}
```

**Crucial Instructions:**

1.  **Tier Specificity:** Extract and verify data *only* for the `{policy_tier_name}` tier by analyzing the provided PDF. If limits/details are shared, use the value specified for this tier. If a benefit is explicitly excluded for this tier in the PDF, it should not be listed in `pdf_only_findings`.
2.  **Placeholder Handling:** In the JSON, if placeholder text like "Refer to Section X" is observed during JSON-to-PDF verification, you **MUST** locate and read the relevant section(s) in the **provided PDF document** for that coverage and verify against the *actual* details found there. Include key applicable conditions, definitions, major inclusions/exclusions, or other pertinent information.
3.  **Currency:** Identify and include the correct currency code (e.g., "SGD") within the `json_detail` or `pdf_detail` fields when reporting discrepancies related to monetary limits.
4.  **Source Info Verification (JSON-to-PDF):** Verify `source_info`. If the JSON includes specific source references (like page numbers or section titles within `source_specific_details`), verify that the information *does* originate from that specific location in the **provided PDF document**. Check for missing, extra, or mismatched details originating from the cited source when reporting `no_match`.
5.  **Detail Fields (json_detail / pdf_detail):**
    *   **ALWAYS Include:** You MUST include both `json_detail` and `pdf_detail` fields for every item in the `evaluation_results` array, regardless of the `result` value ("match", "no_match", "missing_in_pdf").
    *   **Content for "match":** Populate `json_detail` with a summary of the key details found in the JSON for the matched coverage. Populate `pdf_detail` with a summary of the corresponding key details found in the PDF. These should represent the information confirmed to be consistent.
    *   **Content for "no_match":** Populate `json_detail` with the specific details found in the JSON that caused the mismatch. Populate `pdf_detail` with the specific details found in the PDF that contradict the JSON. Also include the `discrepancy` field explaining the mismatch type (e.g., "Limit value differs", "Details differ").
    *   **Content for "missing_in_pdf":** Populate `json_detail` with the details found in the JSON. Populate `pdf_detail` with a statement indicating the coverage/details were not found in the PDF for the specified tier (e.g., "Coverage not mentioned for Premium tier in PDF").
    *   **Detail Focus:** Pay attention to key conditions, definitions, inclusions/exclusions, sub-limits, etc., when populating these fields.
6.  **Missing Findings (PDF-to-JSON):** For the `pdf_only_findings` array, include the `coverage_name` as identified in the PDF, a concise `pdf_detail` summarizing the benefit, and if possible, a `pdf_source_location` (e.g., "Section 5.a, Page 12"). Focus on genuinely missing *significant* coverages.
7.  **Error Handling:** If the PDF is unreadable/unusable by the LLM, the JSON is malformed, or the specified `{policy_tier_name}` cannot be clearly identified in the PDF, report this inability as the primary result, potentially using a top-level "error" field in the JSON output structure (e.g. `{{"error": "Could not identify tier in PDF"}}`).

---
Please process the provided policy document (PDF) and JSON content for the **`{policy_tier_name}`** tier and generate the JSON output according to these instructions.
```

## 5. Implementation Steps

The following steps outline the creation of the new evaluation script:

- [x] **1. Create Script File & Directory Structure:**
    - [x] Create directory: `scripts/evaluation/pdf_extraction_evaluation/`
    - [x] Create file: `scripts/evaluation/pdf_extraction_evaluation/eval_pdf_extraction.py`
    - [x] Create output directory: `data/evaluation/pdf_extraction_evaluations/`
    - [x] Add `__init__.py` to the new evaluation directory if needed for imports.

- [x] **2. Script Setup (`eval_pdf_extraction.py`):**
    - [x] Add standard imports (`os`, `json`, `argparse`, `random`, `logging`, `sys`, `pathlib`, `re`). (Removed `mimetypes`)
    - [x] Import necessary components from the project (e.g., `LLMService` from `src.models.llm_service`).
    - [x] Set up logging.
    - [x] Define constants (e.g., output directory path - update default if changed above).

- [x] **3. Command-Line Arguments (Batch Mode):**
    - [x] Use `argparse` to accept input arguments:
        - [x] `--input_json_dir` (optional): Path to the directory containing processed policy JSON files (default: `data/policies/processed/`).
        - [x] `--input_pdf_dir` (optional): Path to the directory containing raw policy PDF files (default: `data/policies/raw/`).
        - [x] `--output_dir` (optional): Directory to save the evaluation results (default: `data/evaluation/pdf_extraction_evaluations/`).

- [x] **4. Core Logic (Batch Mode):**
    - [x] **Find Files:** Get a list of all `.json` files in `input_json_dir`.
    - [x] **Loop & Match:** Iterate through each JSON file found.
        - [x] **Parse Filename:** Extract insurer and tier name from the JSON filename (e.g., `fwd_{Premium}.json`). Handle potential parsing errors.
        - [x] **Construct PDF Path:** Create the expected corresponding PDF filename (e.g., `fwd_{Premium}.pdf`) and its full path within `input_pdf_dir`.
        - [x] **Check PDF Existence:** Verify if the constructed PDF path exists. If not, log a warning and skip to the next JSON file.
        - [x] **Load Inputs:** If both files exist, load the JSON content and read the PDF file bytes. Handle potential errors.
        - [x] **Prepare LLM Input:**
            - [x] Instantiate `LLMService`.
            - [x] Format the refined prompt (from Section 4) replacing placeholders like `{policy_tier_name}`.
            - [x] Prepare the multi-modal input list for `LLMService`:
                - Part 1: The formatted text prompt.
                - Part 2: The input JSON content as a string (e.g., `json.dumps(json_data)`).
                - Part 3: The input PDF file data (bytes) with hardcoded `mime_type` as `application/pdf`.
            - [x] Ensure `LLMService`'s `generate_structured_content` method accepts and correctly formats this list for the Gemini API call.
        - [x] **Execute LLM Call:**
            - [x] Use `LLMService.generate_structured_content` to get the evaluation result, passing the prepared multi-modal input list.
            - [x] Retry logic is handled within `LLMService`.
            - [x] Handle potential LLM errors or empty/invalid responses gracefully (e.g., log error, potentially save an error JSON).
        - [x] **Process Output:**
            - [x] Validate the LLM output against the expected JSON structure.
            - [x] If valid, add the actual input file paths (`json_path`, `pdf_path`) to the `json_source` and `pdf_source` fields in the final output JSON.
        - [x] **Save Output:**
            - [x] Construct the output filename (e.g., `eval_fwd_{Premium}.json`).
            - [x] Save the final evaluation JSON (or error JSON) to the specified `output_dir`.
    - [x] **Add Summary Logging:** Log total files found, processed, skipped (missing PDF), and errors encountered.

- [x] **5. Add Documentation:**
    - [x] Add/Update the comprehensive docstring in `eval_pdf_extraction.py` explaining its purpose, arguments (including batch mode defaults), input/output formats, and usage examples for batch processing.
    - [x] Update the `README.md` in `scripts/evaluation/pdf_extraction_evaluation/` to reflect the batch processing capability.

- [x] **6. Testing:**
    - [x] Run the script without arguments to test batch processing with default directories.
    - [x] Verify multiple output JSON files are created correctly.
    - [x] Test edge cases (e.g., empty input directories, JSON file with no matching PDF).
    - [x] Qualitatively review a few LLM evaluation outputs for accuracy.

- [x] **7. Update Memory Bank & Progress:**
    - [x] Update `memory-bank/progress.md` to mark this task as in progress/completed.
    - [x] Update `memory-bank/activeContext.md` with details about the batch processing capability.
    - [x] Update `memory-bank/systemPatterns.md` to reflect the batch processing nature of the script.

---
