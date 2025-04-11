# Implementation Plan: Transcript Generation Scenarios

**Objective:** Modify the `scripts/data_generation/generate_transcripts.py` script to support generating transcripts based on predefined scenarios, allowing for more targeted evaluation of the recommendation system.

**Date:** 2025-04-09

**Author:** Cline

---

## Steps

- [x] 1.  **Create Scenario Directory Structure:**
    *   Create a new directory: `data/scenarios/`.
    *   This directory will house individual scenario definition files.

- [x] 2.  **Define Scenario File Format (JSON):**
    *   Each scenario will be defined in its own `.json` file within `data/scenarios/`.
    *   **Required Fields:**
        *   `scenario_name` (string): Unique identifier (e.g., "unfulfillable\_pet\_coverage"). Should match the filename without the extension.
        *   `description` (string): Brief explanation of the scenario's purpose.
        *   `additional_requirements` (list of strings): Specific requirement text(s) to be added to the standard list for this scenario.
    *   **Optional Fields:**
        *   `prompt_instructions` (string): Extra instructions for the LLM specific to this scenario, potentially added to the prompt's guidelines section.
    *   **Scenario 1 (`data/scenarios/uncovered_cancellation_reason.json`):**
        ```json
        {
          "scenario_name": "uncovered_cancellation_reason",
          "description": "Customer needs trip cancellation coverage for a personal family event (e.g., important wedding), which is typically excluded.",
          "additional_requirements": [
            "Coverage if I have to cancel my trip for an important family event, like my sister's wedding."
          ],
          "prompt_instructions": "The customer should explicitly ask about coverage for trip cancellation due to a personal family event, providing specific details (e.g., 'I need to know if I'm covered if I have to cancel my trip for my sister's wedding'). The agent should clearly acknowledge this specific request, note it as a requirement, and indicate that this might not be a standard covered reason for cancellation."
        }
        ```

    *   **Scenario 2 (`data/scenarios/pet_care_coverage.json`):**
        ```json
        {
          "scenario_name": "pet_care_coverage",
          "description": "Customer needs coverage for pet accommodation costs if their return is delayed.",
          "additional_requirements": [
            "Coverage for additional pet accommodation costs in a pet hotel or kennel if my return to Singapore is delayed."
          ],
          "prompt_instructions": "The customer should explicitly ask about coverage for pet accommodation costs if their return is delayed. The customer should provide specific details (e.g., 'I have a cat that would need to stay in a pet hotel if my flight is delayed'). The agent should clearly acknowledge this specific request and note it as a requirement."
        }
        ```

    *   **Scenario 3 (`data/scenarios/golf_coverage.json`):**
        ```json
        {
          "scenario_name": "golf_coverage",
          "description": "Customer needs comprehensive golf-related coverage including equipment, hole-in-one, green fees, and buggy damage.",
          "additional_requirements": [
            "Coverage for my golf equipment, reimbursement for unused green fees if I can't play, and coverage if I damage a golf buggy.",
            "A special benefit if I get a hole-in-one during my trip."
          ],
          "prompt_instructions": "The customer should explicitly ask about comprehensive golf coverage, mentioning specific aspects like equipment protection, hole-in-one achievement benefit, unused green fees, and golf buggy damage. The agent should clearly acknowledge these specific requests and note them as requirements."
        }
        ```

    *   **Scenario 4 (`data/scenarios/public_transport_double_cover.json`):**
        ```json
        {
          "scenario_name": "public_transport_double_cover",
          "description": "Customer wants doubled accidental death coverage when traveling on public transport.",
          "additional_requirements": [
            "Double payout for accidental death if it occurs while traveling on public transport."
          ],
          "prompt_instructions": "The customer should explicitly ask about doubled coverage for accidental death specifically when traveling on public transport. The customer should be clear about wanting this specific benefit (e.g., 'I want to know if the policy provides extra coverage if an accident happens while I'm on a bus or train'). The agent should clearly acknowledge this specific request and note it as a requirement."
        }
        ```

- [x] 3.  **Create Initial Scenario Files:**
    *   Create the following scenario files in `data/scenarios/` based on the defined format:
        * `uncovered_cancellation_reason.json`
        * `pet_care_coverage.json`
        * `golf_coverage.json`
        * `public_transport_double_cover.json`

- [x] 4.  **Modify `scripts/data_generation/generate_transcripts.py`:**
    *   **Add CLI Argument:**
        *   Use `argparse` to add an optional argument: `--scenario` (short form `-s`).
        *   This argument will accept the `scenario_name` (string) corresponding to a scenario file.
    *   **Constants:**
        *   Define `SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "data", "scenarios")`.
    *   **Scenario Loading Logic (within `generate_transcript` or called from `main`):**
        *   Check if the `scenario` argument was provided.
        *   If yes:
            *   Construct the full path: `os.path.join(SCENARIOS_DIR, f"{scenario_name}.json")`.
            *   Load the JSON data using a helper function (similar to `load_json`). Include error handling for `FileNotFoundError` and `json.JSONDecodeError`.
            *   Store the loaded scenario data (or `None` if no scenario specified).
    *   **Prompt Construction Logic (within `generate_transcript`):**
        *   Load standard `coverage_reqs` using `get_coverage_requirements()`.
        *   Format standard requirements using `pprint.pformat()`.
        *   If scenario data is loaded:
            *   Retrieve `additional_requirements` from the scenario data.
            *   Format these additional requirements (e.g., as a bulleted list string: `\n- Requirement 1\n- Requirement 2`).
            *   Modify the `# REQUIRED CUSTOMER REQUIREMENTS` section in `PROMPT_TEMPLATE` to clearly indicate both standard and scenario-specific requirements. Example placeholder update:
                ```
                # REQUIRED CUSTOMER REQUIREMENTS
                ## Standard Requirements:
                {standard_coverage_requirements}

                ## Scenario-Specific Requirements:
                {scenario_requirements}
                ```
            *   Update the `.format()` call to include `standard_coverage_requirements` and `scenario_requirements` (which would be an empty string if no scenario is loaded).
            *   *(Optional)* If `prompt_instructions` exist in the scenario, append them to the `# Transcript Generation Guidelines and Requirements` section of the prompt.
    *   **Output Data Modification (within `generate_transcript`):**
        *   Add a new key `"scenario"` to the `output_data` dictionary. Its value should be the `scenario_name` (string) if a scenario was used, otherwise `None`.
    *   **Output Filename Modification (within `generate_transcript`):**
        *   Update the filename generation logic:
            *   The final implemented format is `transcript_{scenario_name_or_no_scenario}_{customer_id}.json`.
            *   This uses the scenario name if provided, or the literal string "no_scenario" otherwise.
            *   It replaces the timestamp with a unique `customer_id` (UUID).
            *   The personality name is no longer included in the filename.
    *   **Main Execution Logic (`if __name__ == "__main__":`)**
        *   Parse the new `--scenario` argument.
        *   Pass the parsed `scenario_name` (or `None`) to the `generate_transcript` function within the loop. The same scenario will apply to all transcripts generated in a single run if specified.

- [x] 5.  **Update Script Documentation (`generate_transcripts.py` Docstring):**
    *   Explain the new scenario feature.
    *   Document the `--scenario` command-line argument and its usage.
    *   Mention the expected location and format of scenario files (`data/scenarios/*.json`).
    *   Update the "How to Run" section with examples using the scenario argument.

- [x] 6.  **Testing:**
    *   Run the script without the `--scenario` argument to ensure default behavior is unchanged.
    *   Run the script *with* the `--scenario` argument pointing to the created example scenario file.
    *   Verify:
        *   The correct scenario data is loaded.
        *   The prompt includes the additional requirements.
        *   The output JSON file includes the `"scenario"` key.
        *   The output filename includes the scenario name.
    *   The generated transcript reflects the scenario's intent (qualitative check).

- [x] 7.  **Update Memory Bank:**
    *   Update `memory-bank/activeContext.md` to reflect the current focus on implementing scenarios.
    *   Update `memory-bank/progress.md` to note the addition of this feature.
    *   Consider if `memory-bank/systemPatterns.md` needs updating regarding data flow for scenarios.

---

## Status

**COMPLETED:** All steps of this implementation plan have been successfully executed and tested. The scenario-based transcript generation feature is now fully functional.

- ✅ Scenario directory structure created
- ✅ Scenario file format defined and example files created
- ✅ Script modified to support scenario-based generation
- ✅ Documentation updated
- ✅ Testing completed with verification of all requirements
- ✅ Memory Bank updated

The implementation allows for generating synthetic conversation transcripts based on predefined scenarios, enabling more targeted evaluation of the recommendation system's ability to handle specific coverage requirements.

---
