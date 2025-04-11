"""
Script: generate_transcripts.py

Purpose:
Generates realistic synthetic conversation transcripts between a customer
service agent (ISS Insurance Ltd, Singapore) and a customer inquiring about
travel insurance. The script automates the process of:
1. Loading customer personality profiles from a JSON file.
2. Loading standard travel insurance coverage requirements from a Python module.
3. Randomly selecting one personality profile.
4. Constructing a detailed prompt for a Large Language Model (LLM) that includes
   the selected personality, all coverage requirements, context, guidelines,
   and desired conversation format.
5. Calling the LLM service (configured via src.models.llm_service) to generate
   the transcript text based on the prompt.
6. Parsing the generated text into a structured list of speaker turns.
7. Saving the structured transcript along with the details of the selected
   personality into a timestamped JSON file in the specified output directory.

Inputs:
- data/transcripts/personalities.json: Contains a list of customer personality
  profiles with names and characteristics.
- data/coverage_requirements/coverage_requirements.py: Contains a dictionary
  defining standard travel insurance coverage types and details.
- data/scenarios/*.json: (Optional) Contains scenario-specific requirements and
  instructions for generating transcripts with specific coverage needs.
- LLM Service API Key: Must be configured correctly for the LLMService, typically
  via environment variables (e.g., GOOGLE_API_KEY) as handled by
  src.models.gemini_config.

Output:
- A JSON file named `transcript_{scenario_or_personality}_{customer_id}.json`
  (e.g., `transcript_uncovered_cancellation_reason_uuid-goes-here.json` or
  `transcript_the_anxious_inquirer_uuid-goes-here.json`), saved in the
  `data/transcripts/raw/synthetic/` directory.
- The JSON file contains:
    - "customer_id": A unique identifier (UUID) for this transcript/customer interaction.
    - "personality": The full dictionary of the randomly selected personality.
    - "transcript": A list of objects, each with "speaker" and "dialogue", or the raw text if parsing failed.
    - "scenario": (If a scenario was used) The name of the scenario used (e.g., "uncovered_cancellation_reason").

How to Run:
1. Ensure you are in the project's root directory (mtech-policy-recsys).
2. Make sure all dependencies are installed (`pip install -r requirements.txt`).
3. Ensure your LLM API key (e.g., Google Gemini API key) is configured
   (usually via environment variables).
4. Execute the script using the Python interpreter. You can optionally specify
   the number of transcripts to generate using the `-n` or `--num_transcripts`
   argument (default is 1) and/or a specific scenario using the `-s` or `--scenario`
   argument:
   ```bash
   # Generate 1 transcript (default, no scenario used)
   python scripts/data_generation/generate_transcripts.py

   # Generate 10 transcripts
   python scripts/data_generation/generate_transcripts.py -n 10
   # or
   python scripts/data_generation/generate_transcripts.py --num_transcripts 10

   # Generate 1 transcript with a specific scenario
   python scripts/data_generation/generate_transcripts.py -s golf_coverage
   python scripts/data_generation/generate_transcripts.py -s pet_care_coverage
   python scripts/data_generation/generate_transcripts.py -s public_transport_double_cover
   python scripts/data_generation/generate_transcripts.py -s uncovered_cancellation_reason

   # Generate 5 transcripts with a specific scenario
   python scripts/data_generation/generate_transcripts.py -n 5 -s golf_coverage
   ```
5. Check the `data/transcripts/raw/synthetic/` directory for the output JSON file(s).

Note:
- The script currently uses the MODEL_NAME constant defined within it. You might
  need to adjust this depending on available models or desired quality/cost.
- Error handling is included for file loading and LLM generation, with logs
  printed to the console. If transcript parsing fails, the raw text is saved.
"""

import json
import random
import os
import sys
import pprint
import logging
import argparse
import re
import datetime  # Added for timestamp
import uuid  # Added for customer ID

# Adjust sys.path to include project root for imports
# Assumes the script is run from the 'scripts/data_generation' directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to get the project root (scripts/data_generation -> scripts -> project_root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)

try:
    from src.models.llm_service import LLMService

    # Assuming coverage_requirements.py is structured to be importable
    from data.coverage_requirements.coverage_requirements import (
        get_coverage_requirements,
        get_customer_context_options,
    )
except ImportError as e:
    logging.error(f"Error importing modules: {e}")
    logging.error(f"PROJECT_ROOT: {PROJECT_ROOT}")
    logging.error(f"sys.path: {sys.path}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
PERSONALITIES_PATH = os.path.join(
    PROJECT_ROOT, "data", "transcripts", "personalities.json"
)
SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "data", "scenarios")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "transcripts", "raw", "synthetic")
MODEL_NAME = "gemini-2.5-pro-preview-03-25"

PROMPT_TEMPLATE = """
Generate a realistic synthetic conversation transcript between a customer service agent at ISS Insurance Ltd (Singapore) and a customer inquiring about travel insurance.

# Customer Personality
{personality_details}

# REQUIRED CUSTOMER REQUIREMENTS
## Standard Requirements:
{standard_coverage_requirements}

## Scenario-Specific Requirements:
{scenario_requirements}

# REQUIRED CUSTOMER CONTEXT
{context_options_details}

# Transcript Generation Guidelines and Requirements

## Core Mandates & Verification
- **CRITICAL REQUIREMENT:** The conversation MUST explicitly discuss or mention EVERY SINGLE requirement listed in # REQUIRED CUSTOMER REQUIREMENTS. No requirement should be omitted.
- Actively incorporate relevant details or specific examples inspired by # REQUIRED CUSTOMER CONTEXT into the dialogue.
- **Verification:** Before finalizing the transcript, mentally double-check that every requirement from # REQUIRED CUSTOMER REQUIREMENTS has been mentioned (primarily initiated by the customer) and that relevant details from # REQUIRED CUSTOMER CONTEXT have been woven into the dialogue (potentially initiated by the agent).

## Conversation Flow & Realism
- The customer's personality should naturally influence their responses throughout the conversation.
- The customer's specific coverage requirements (from # REQUIRED CUSTOMER REQUIREMENTS) should arise naturally from the customer's dialogue, influenced by their personality and travel plans.
- Maintain realistic conversational style appropriate for a customer service scenario in Singapore.

## Agent Role & Behavior
- The agent should NOT directly ask "Do you need [specific coverage type]?".
- Instead, the agent should focus on understanding the customer's trip details and concerns (using # REQUIRED CUSTOMER CONTEXT as a guide for questions), allowing the customer to mention their coverage needs organically. The agent may ask clarifying questions related to these context options to understand the customer's situation.
- The customer service agent's role is strictly limited to gathering the customer's requirements. They do NOT provide recommendations or advice.
- Once all requirements are clearly gathered and confirmed, the agent should politely and naturally close the conversation.

# Conversation Format

Customer Service Agent: [Greeting and opening line]
Customer: [Response influenced by personality]
...
Customer Service Agent: [Clarifying question about trip context/plans (leading to requirement reveal)]
Customer: [Explicit mention or clarification of requirement]
...
Customer Service Agent: [Summarizes and confirms requirements]
Customer: [Final confirmation or clarification]
Customer Service Agent: [Polite and natural closure of conversation]
Customer: [Acknowledgment and natural end of conversation]

# Output Format
Provide ONLY the raw conversation transcript text, starting with "Customer Service Agent:" and ending with the final customer line. Do not include any introductory text, explanations, or markdown formatting around the transcript itself.
"""

# --- Helper Functions ---


def parse_transcript_text(text: str) -> list[dict[str, str]]:
    """Parses raw transcript text into a list of speaker turns."""
    turns = []
    # Regex to capture speaker (Customer Service Agent or Customer) and their dialogue
    # Handles potential variations in spacing and the colon
    pattern = re.compile(r"^(Customer Service Agent|Customer)\s*:\s*(.*)", re.MULTILINE)
    matches = pattern.finditer(text)
    for match in matches:
        speaker = match.group(1).strip()
        dialogue = match.group(2).strip()
        if speaker and dialogue:  # Ensure both parts were captured
            turns.append({"speaker": speaker, "dialogue": dialogue})
        else:
            # Log lines that don't match the expected format
            logging.warning(f"Could not parse line: {match.group(0)}")
    if not turns and text:  # Log if parsing failed completely but text was present
        logging.warning(
            f"Failed to parse any turns from transcript text:\n{text[:500]}..."
        )  # Log first 500 chars
    return turns


def load_json(file_path: str) -> dict:
    """Loads JSON data from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Error: Personalities file not found at {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from {file_path}")
        sys.exit(1)


def format_personality(personality: dict) -> str:
    """Formats the personality details for the prompt."""
    details = f"Name: {personality.get('name', 'N/A')}\n"
    details += "Characteristics:\n"
    for char in personality.get("characteristics", []):
        details += f"- {char}\n"
    return details.strip()


def format_filename(name: str) -> str:
    """Formats a name into a safe filename string."""
    return name.lower().replace(" ", "_").replace("&", "and").replace("/", "_")


def save_json(data: dict, file_path: str) -> None:
    """Saves data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved transcript to {file_path}")
    except IOError as e:
        logging.error(f"Error saving file to {file_path}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during saving: {e}")


# --- Main Generation Logic ---


def generate_transcript(scenario_name=None):
    """
    Generates a single transcript.

    Args:
        scenario_name (str, optional): Name of the scenario to use. If provided,
                                      loads scenario-specific requirements from the
                                      corresponding JSON file in data/scenarios/.
    """
    logging.info("Starting transcript generation...")

    # 1. Load Data
    personalities_data = load_json(PERSONALITIES_PATH)
    personalities = personalities_data.get("personalities")
    if not personalities:
        logging.error(
            "Error: 'personalities' key not found or empty in personalities JSON."
        )
        sys.exit(1)

    coverage_reqs = get_coverage_requirements()
    if not coverage_reqs:
        logging.error("Error: Could not retrieve coverage requirements.")
        sys.exit(1)

    context_options = get_customer_context_options()  # Load context options
    if not context_options:
        logging.error("Error: Could not retrieve customer context options.")
        # Decide if this is critical enough to exit
        # sys.exit(1)
        # Or just log a warning and continue without them
        logging.warning("Proceeding without customer context options.")
        context_options = {}  # Use empty dict to avoid formatting errors

    # Load scenario data if specified
    scenario_data = None
    if scenario_name:
        scenario_path = os.path.join(SCENARIOS_DIR, f"{scenario_name}.json")
        try:
            scenario_data = load_json(scenario_path)
            logging.info(f"Loaded scenario: {scenario_name}")
        except FileNotFoundError:
            logging.error(f"Error: Scenario file not found at {scenario_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            logging.error(f"Error: Could not decode JSON from {scenario_path}")
            sys.exit(1)

    # 2. Select Personality
    selected_personality = random.choice(personalities)
    personality_name = selected_personality.get("name", "unknown_personality")
    logging.info(f"Selected personality: {personality_name}")

    # 3. Format Data for Prompt
    formatted_personality = format_personality(selected_personality)
    # Use pprint for readable dictionary formatting in the prompt
    formatted_standard_requirements = pprint.pformat(coverage_reqs, indent=2)
    formatted_context_options = pprint.pformat(
        context_options, indent=2
    )  # Format context options

    # Format scenario-specific requirements if available
    formatted_scenario_requirements = ""
    scenario_instructions = ""
    if scenario_data:
        # Format additional requirements as a bulleted list
        if "additional_requirements" in scenario_data:
            formatted_scenario_requirements = "\n".join(
                [f"- {req}" for req in scenario_data.get("additional_requirements", [])]
            )

        # Get scenario-specific instructions if available
        if "prompt_instructions" in scenario_data:
            scenario_instructions = f"\n\n## Scenario-Specific Instructions:\n{scenario_data['prompt_instructions']}"

    # 4. Construct Prompt
    final_prompt = PROMPT_TEMPLATE.format(
        personality_details=formatted_personality,
        standard_coverage_requirements=formatted_standard_requirements,
        scenario_requirements=formatted_scenario_requirements,
        context_options_details=formatted_context_options,
    )

    # Add scenario-specific instructions if available
    if scenario_instructions:
        # Insert scenario instructions after the core mandates section
        insert_point = final_prompt.find("## Conversation Flow & Realism")
        if insert_point != -1:
            final_prompt = (
                final_prompt[:insert_point]
                + scenario_instructions
                + "\n\n"
                + final_prompt[insert_point:]
            )
    # --- START GENERATE TRANSCRIPT PROMPT ---
    print("--- START GENERATE TRANSCRIPT PROMPT ---")
    print(final_prompt)
    print("--- END GENERATE TRANSCRIPT PROMPT ---")
    # Optional: Log the prompt for debugging (can be long)
    # logging.debug(f"Generated Prompt:\n{final_prompt}")

    # 5. Generate Transcript using LLM
    logging.info(f"Generating transcript using model: {MODEL_NAME}...")
    try:
        llm = LLMService()  # Assumes API key is handled by GeminiConfig/environment
        # Get creative parameters
        parameters = llm.GeminiConfig.get_parameters("creative")
        response = llm.generate_content(
            prompt=final_prompt, model=MODEL_NAME, parameters=parameters
        )
        generated_text = response.text
        logging.info("Transcript generation complete.")
        # --- START RAW LLM RESPONSE ---
        print("--- START RAW LLM RESPONSE ---")
        print(generated_text)
        print("--- END RAW LLM RESPONSE ---")
        # Optional: Log the raw response text
        # logging.debug(f"Raw LLM Response:\n{generated_text}")

    except Exception as e:
        logging.error(f"Error during LLM generation: {e}")
        # Decide if you want to exit or just log the error and potentially retry/skip
        return  # Exit this attempt if generation fails

    # 6. Parse Transcript Text
    parsed_transcript = parse_transcript_text(generated_text)
    if not parsed_transcript:
        logging.warning(
            f"Could not parse transcript for personality: {personality_name}. Saving raw text instead."
        )
        # Fallback to saving raw text if parsing fails
        transcript_output = generated_text.strip()
    else:
        transcript_output = parsed_transcript

    # 7. Prepare Output
    customer_id = str(uuid.uuid4())  # Generate customer ID
    output_data = {
        "customer_id": customer_id,  # Add customer ID to output
        "personality": selected_personality,
        "transcript": transcript_output,
        "scenario": scenario_data.get("scenario_name") if scenario_data else None,
    }

    # 8. Save Output
    # customer_id was generated in step 7

    # Determine the base name part (scenario or "no_scenario")
    if scenario_name:
        base_name_part = format_filename(scenario_name)
    else:
        # Use "no_scenario" if no scenario is specified
        base_name_part = "no_scenario"

    # Construct filename using base name part and customer_id
    output_filename = f"transcript_{base_name_part}_{customer_id}.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    save_json(output_data, output_path)


# --- Script Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic conversation transcripts."
    )
    parser.add_argument(
        "-n",
        "--num_transcripts",
        type=int,
        default=1,
        help="Number of transcripts to generate (default: 1)",
    )
    parser.add_argument(
        "-s",
        "--scenario",
        type=str,
        help="Name of the scenario to use (without .json extension). Loads scenario-specific requirements from data/scenarios/<scenario>.json",
    )
    args = parser.parse_args()

    if args.num_transcripts < 1:
        logging.error("Number of transcripts must be at least 1.")
        sys.exit(1)

    logging.info(f"Starting generation of {args.num_transcripts} transcript(s)...")
    if args.scenario:
        logging.info(f"Using scenario: {args.scenario}")

    for i in range(args.num_transcripts):
        logging.info(f"--- Generating transcript {i + 1} of {args.num_transcripts} ---")
        try:
            generate_transcript(scenario_name=args.scenario)
        except Exception as e:
            # Log the error for this specific transcript generation but continue
            logging.error(f"Failed to generate transcript {i + 1}: {e}")
            # Optionally add a small delay here if needed

    logging.info(f"Script finished generating {args.num_transcripts} transcript(s).")
