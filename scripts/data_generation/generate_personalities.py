"""
Generates a list of common insurance customer service personality types using
the centralized LLMService (which utilizes Google Gemini, specifically
gemini-2.5-pro-preview-03-25 by default or as specified).

Purpose:
- Calls the LLMService with a specific prompt to identify 10 distinct personalities.
- Validates the LLM's JSON response against predefined Pydantic models.
- Saves the validated list of personalities as a JSON file.

Requirements:
- Python 3.x
- Project dependencies installed (`pip install -r requirements.txt`), including:
  - `google-generativeai` (used by LLMService)
  - `pydantic`
  - `python-dotenv` (used by LLMService/GeminiConfig)
- A `.env` file in the project root containing the `GOOGLE_API_KEY` (used by LLMService).

Usage:
1. Ensure all requirements are installed and the .env file is configured with GOOGLE_API_KEY.
2. Run the script from the project root directory:
   ```bash
   python scripts/data_generation/generate_personalities.py
   ```
3. The script will output progress messages to the console.
4. Upon successful completion, the generated data will be saved to:
   `data/transcripts/personalities.json`
"""

# import google.generativeai as genai # Replaced by LLMService
import pydantic
import json
import os
import re
import sys  # Added for path manipulation

# from dotenv import load_dotenv # Handled by LLMService
from typing import List, Dict, Any

# --- Add project root to sys.path ---
# Assumes the script is run from the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up two levels: data_generation -> scripts -> project_root
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Local Imports ---
from src.models.llm_service import LLMService  # Import LLMService

# --- Configuration ---
OUTPUT_DIR = "data/transcripts"
OUTPUT_FILENAME = "personalities.json"
MODEL_NAME = "gemini-2.5-pro-preview-03-25"


# --- Pydantic Models for Validation ---
class Personality(pydantic.BaseModel):
    """Represents a single personality type."""

    name: str = pydantic.Field(..., description="Descriptive name of the personality.")
    characteristics: List[str] = pydantic.Field(
        ..., description="Key defining characteristics."
    )


class PersonalityList(pydantic.BaseModel):
    """Represents the list of personalities, matching the expected JSON root."""

    personalities: List[Personality] = pydantic.Field(
        ..., description="List of personality objects."
    )


# --- Prompt Definition ---
PROMPT = """
Identify the ten most common, distinct (non-overlapping) personalities that insurance customer service representatives typically encounter. Ensure categories avoid significant overlap; for example, refine or combine concepts like 'impatient' and 'demanding' into distinct types if necessary, or ensure their definitions are clearly separate.

For each of these ten personalities:

1.  Assign a descriptive name.
2.  List its key defining characteristics as an array of strings.

Present the entire output as a single, valid JSON object. This JSON object should be an array under a root key named "personalities", where each element in the array is an object representing one personality type, containing the "name" (string) and "characteristics" (array of strings) keys.

Example structure:
{
  "personalities": [
    {
      "name": "Example Personality 1",
      "characteristics": ["Characteristic A", "Characteristic B"]
    },
    {
      "name": "Example Personality 2",
      "characteristics": ["Characteristic C", "Characteristic D"]
    }
    // ... up to 10 personalities
  ]
}
"""


# --- Helper Function to Extract/Verify JSON ---
def extract_and_verify_json(data: Any) -> Dict[str, Any] | None:
    """
    Verifies if the input is a dict (already parsed JSON) or extracts JSON
    from text, handling potential markdown.
    """
    if isinstance(data, dict):
        print("LLMService returned a dictionary (already parsed JSON).")
        return data
    elif isinstance(data, str):
        print("LLMService returned text, attempting to extract JSON...")
        text = data
        json_str = None
        # Look for JSON within markdown code blocks
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            json_str = match.group(1)
        else:
            # If no markdown block, assume the whole text might be JSON or contain it
            # Find the first '{' and last '}'
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = text[start : end + 1]
            else:
                # Fallback: try parsing the whole text if it looks like JSON
                if text.strip().startswith("{") and text.strip().endswith("}"):
                    json_str = text.strip()

        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Error: Failed to decode extracted JSON string: {e}")
                print(
                    f"Attempted to parse: {json_str[:500]}..."
                )  # Print first 500 chars
                return None
        else:
            print(
                "Error: Could not find or extract JSON object from the response text."
            )
            return None
    else:
        print(f"Error: Unexpected data type received from LLMService: {type(data)}")
        return None


# --- Main Generation Function ---
def generate_personalities():
    """Generates, validates, and saves the personality list using LLMService."""
    print("Initializing LLM Service...")
    try:
        # API key handled internally by LLMService/GeminiConfig
        llm_service = LLMService()
    except ValueError as e:
        print(f"Error initializing LLM Service: {e}")
        return
    except Exception as e:
        print(f"Unexpected error initializing LLM Service: {e}")
        return

    print(f"Sending prompt to LLM Service (Model: {MODEL_NAME})...")
    try:
        # Use generate_structured_content which aims for JSON output
        # Pass the specific model name if needed, otherwise it uses the default from config
        response_data = llm_service.generate_structured_content(
            prompt=PROMPT, model=MODEL_NAME
        )
        print("Received response from LLM Service.")

    except ValueError as e:  # Catch JSON parsing errors from LLMService
        print(f"Error: LLM Service failed to return valid JSON: {e}")
        return
    except Exception as e:
        print(f"Error during LLM Service API call: {e}")
        return

    print("Verifying/Extracting JSON from response...")
    # generate_structured_content should return a dict, but we double-check
    json_data = extract_and_verify_json(response_data)

    if not json_data:
        print("Failed to get valid JSON data. Aborting.")
        return

    print("Validating JSON data with Pydantic...")
    try:
        validated_data = PersonalityList.model_validate(json_data)
        print("Validation successful!")
        # print(validated_data.model_dump_json(indent=2)) # Optional: print validated data

    except pydantic.ValidationError as e:
        print(f"Error: Pydantic validation failed:\n{e}")
        print("Aborting.")
        return

    # --- Save to File ---
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    print(f"Saving validated data to {output_path}...")
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            # Use model_dump_json for clean Pydantic output
            f.write(validated_data.model_dump_json(indent=2))
        print("Successfully saved personality data.")

    except IOError as e:
        print(f"Error: Failed to write to file {output_path}: {e}")


# --- Execution ---
if __name__ == "__main__":
    generate_personalities()
