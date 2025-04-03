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
- LLM Service API Key: Must be configured correctly for the LLMService, typically
  via environment variables (e.g., GOOGLE_API_KEY) as handled by
  src.models.gemini_config.

Output:
- A JSON file named `transcript_{personality_name}_{YYYYMMDD_HHMMSS}.json` (e.g.,
  `transcript_the_skeptic_20250403_151200.json`) saved in the
  `data/transcripts/raw/synthetic/` directory.
- The JSON file contains:
    - "personality": The full dictionary of the randomly selected personality.
    - "transcript": A list of objects, each with "speaker" and "dialogue".

How to Run:
1. Ensure you are in the project's root directory (mtech-policy-recsys).
2. Make sure all dependencies are installed (`pip install -r requirements.txt`).
3. Ensure your LLM API key (e.g., Google Gemini API key) is configured
   (usually via environment variables).
4. Execute the script using the Python interpreter. You can optionally specify
   the number of transcripts to generate using the `-n` or `--num_transcripts`
   argument (default is 1):
   ```bash
   # Generate 1 transcript (default)
   python scripts/data_generation/generate_transcripts.py

   # Generate 10 transcripts
   python scripts/data_generation/generate_transcripts.py -n 10
   # or
   python scripts/data_generation/generate_transcripts.py --num_transcripts 10
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
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "transcripts", "raw", "synthetic")
MODEL_NAME = "gemini-2.5-pro-exp-03-25"

PROMPT_TEMPLATE = """
Generate a realistic synthetic conversation transcript between a customer service agent at ISS Insurance Ltd (Singapore) and a customer inquiring about travel insurance.

# Customer Personality
{personality_details}

# REQUIRED CUSTOMER REQUIREMENTS
{coverage_requirements}

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


def generate_transcript():
    """Generates a single transcript."""
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

    # 2. Select Personality
    selected_personality = random.choice(personalities)
    personality_name = selected_personality.get("name", "unknown_personality")
    logging.info(f"Selected personality: {personality_name}")

    # 3. Format Data for Prompt
    formatted_personality = format_personality(selected_personality)
    # Use pprint for readable dictionary formatting in the prompt
    formatted_requirements = pprint.pformat(coverage_reqs, indent=2)
    formatted_context_options = pprint.pformat(
        context_options, indent=2
    )  # Format context options

    # 4. Construct Prompt
    final_prompt = PROMPT_TEMPLATE.format(
        personality_details=formatted_personality,
        coverage_requirements=formatted_requirements,
        context_options_details=formatted_context_options,  # Add formatted context options
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
        response = llm.generate_content(
            prompt=final_prompt, model=MODEL_NAME, max_output_tokens=10000
        )  # Added max_output_tokens
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
    output_data = {"personality": selected_personality, "transcript": transcript_output}

    # 8. Save Output
    formatted_name = format_filename(personality_name)
    # Add timestamp to filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"transcript_{formatted_name}_{timestamp}.json"
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
    args = parser.parse_args()

    if args.num_transcripts < 1:
        logging.error("Number of transcripts must be at least 1.")
        sys.exit(1)

    logging.info(f"Starting generation of {args.num_transcripts} transcript(s)...")

    for i in range(args.num_transcripts):
        logging.info(f"--- Generating transcript {i + 1} of {args.num_transcripts} ---")
        try:
            generate_transcript()
        except Exception as e:
            # Log the error for this specific transcript generation but continue
            logging.error(f"Failed to generate transcript {i + 1}: {e}")
            # Optionally add a small delay here if needed

    logging.info(f"Script finished generating {args.num_transcripts} transcript(s).")
