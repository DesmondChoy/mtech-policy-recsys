"""
Generates a list of common insurance customer service personality types using
the Google Gemini LLM (specifically gemini-2.5-pro-exp-03-25).

Purpose:
- Calls the Gemini API with a specific prompt to identify 10 distinct personalities.
- Validates the LLM's JSON response against predefined Pydantic models.
- Saves the validated list of personalities as a JSON file.

Requirements:
- Python 3.x
- `google-generativeai` library (`pip install google-generativeai`)
- `pydantic` library (`pip install pydantic`)
- `python-dotenv` library (`pip install python-dotenv`)
- A `.env` file in the project root containing the `GEMINI_API_KEY`.

Usage:
1. Ensure all requirements are installed and the .env file is configured.
2. Run the script from the project root directory:
   ```bash
   python scripts/data_generation/generate_personalities.py
   ```
3. The script will output progress messages to the console.
4. Upon successful completion, the generated data will be saved to:
   `data/transcripts/personalities.json`
"""

import google.generativeai as genai
import pydantic
import json
import os
import re
from dotenv import load_dotenv
from typing import List, Dict, Any

# --- Configuration ---
OUTPUT_DIR = "data/transcripts"
OUTPUT_FILENAME = "personalities.json"
MODEL_NAME = "gemini-2.5-pro-exp-03-25"


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


# --- Helper Function to Extract JSON ---
def extract_json_from_response(text: str) -> Dict[str, Any] | None:
    """Extracts JSON object from LLM response, handling potential markdown."""
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
            else:
                print("Error: Could not find JSON object in the response.")
                return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON: {e}")
        print(f"Attempted to parse: {json_str[:500]}...")  # Print first 500 chars
        return None


# --- Main Generation Function ---
def generate_personalities():
    """Generates, validates, and saves the personality list."""
    print("Loading environment variables...")
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    print(f"Configuring Gemini with model: {MODEL_NAME}...")
    genai.configure(api_key=api_key)

    generation_config = genai.types.GenerationConfig(
        # Ensure JSON output if the model supports it directly
        # response_mime_type="application/json", # Uncomment if model supports direct JSON output
        temperature=0.7  # Adjust temperature for creativity vs consistency
    )

    # Safety settings - adjust as needed
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
    ]

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    print("Sending prompt to Gemini...")
    try:
        response = model.generate_content(PROMPT)
        response_text = response.text
        print("Received response from Gemini.")
        # print(f"Raw response:\n{response_text[:500]}...") # Optional: print raw response start

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        # print(f"Candidate: {response.candidates[0]}") # Debugging info if available
        # print(f"Prompt Feedback: {response.prompt_feedback}") # Debugging info if available
        return

    print("Extracting JSON from response...")
    json_data = extract_json_from_response(response_text)

    if not json_data:
        print("Failed to extract JSON data. Aborting.")
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
