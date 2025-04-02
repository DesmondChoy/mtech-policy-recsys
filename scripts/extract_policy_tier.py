"""
Extract Policy Tier Information from PDFs using Google Gemini.

Purpose:
This script processes travel insurance policy PDF documents located in a specified
input directory. It uses the Google Gemini API (specifically, a model capable of
handling PDF input) to extract coverage details for specific
policy tiers, as indicated by the PDF filename format. The extracted information
is validated against a Pydantic model and saved as structured JSON files in a
specified output directory.

Prerequisites:
1.  Python Environment: Ensure you have a Python environment set up.
2.  Dependencies: Install required packages by running:
    pip install -r requirements.txt
3.  API Key: Create a `.env` file in the project root directory and add your
    Google API key like this:
    GOOGLE_API_KEY=YOUR_API_KEY_HERE
    Alternatively, you can pass the API key via the `--api-key` command-line argument.
4.  Input Files: Place the raw policy PDF files in the input directory
    (default: `data/policies/raw/`). Files MUST follow the naming convention:
    `insurer_{policy_tier}.pdf` (e.g., `allianz_{gold_plan}.pdf`).

Usage:
Run the script from the project root directory.

Basic Usage (using defaults and .env for API key):
    python scripts/extract_policy_tier.py

Specify Input/Output Directories:
    python scripts/extract_policy_tier.py --input-dir path/to/your/pdfs --output-dir path/to/save/json

Provide API Key via Command Line:
    python scripts/extract_policy_tier.py --api-key YOUR_API_KEY_HERE

Combine Options:
    python scripts/extract_policy_tier.py --input-dir pdfs/ --output-dir processed_policies/ --api-key YOUR_KEY

Error Handling:
- The script uses exponential backoff for retriable API errors.
- It validates the JSON structure received from the API using Pydantic.
- If an output JSON file already exists for a PDF, that PDF will be skipped, and an error logged.
- Files not matching the expected naming pattern will be skipped.
- Errors during file reading, API calls, JSON parsing, or validation are logged.
"""

import os
import re
import json
import time
import logging
import argparse
from datetime import datetime
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator

# --- Configuration ---
INPUT_DIR_DEFAULT = "data/policies/raw/"
OUTPUT_DIR_DEFAULT = "data/policies/processed/"
GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"
FILENAME_PATTERN = re.compile(r"(.+)_\{(.+)\}\.pdf")
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Validation ---


class LimitDetail(BaseModel):
    type: str
    limit: Any  # Can be number or string like "Unlimited"
    basis: Optional[str] = None


class CoverageDetail(BaseModel):
    coverage_name: str
    limits: List[LimitDetail]
    details: str
    source_info: str


class CoverageCategory(BaseModel):
    category_name: str
    coverages: List[CoverageDetail]


class PolicyExtraction(BaseModel):
    provider_name: str
    policy_name: str
    tier_name: str
    extraction_date: Optional[str] = None  # Will be added by the script
    currency: str
    coverage_categories: List[CoverageCategory]

    @field_validator("extraction_date", mode="before")
    @classmethod
    def check_extraction_date(cls, v):
        # Allow None during initial parsing, will be set later
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("extraction_date must be in YYYY-MM-DD format or None")


# --- Prompt Template ---
# Note: Using f-string deferred formatting {{ }} for json examples inside the main f-string
PROMPT_TEMPLATE = """
[POLICY TIER NAME]: {policy_tier}
---
**Your Task:**
Act as a meticulous data extraction assistant. Your goal is to process the provided travel insurance policy document (or OCR text) and extract specific coverage information for the **`[POLICY TIER NAME]`** plan/tier. You must structure the extracted data precisely according to the nested JSON format specified below.
**Input:**
A travel insurance policy document (or text derived from OCR).
**Policy Tier to Extract:**
Focus *exclusively* on the benefits, limits, and details applicable to the **`[POLICY TIER NAME]`** tier specified in the policy document.
**Output Format (Strict JSON):**
Your output **MUST** be a single, valid JSON object conforming to the following structure. Do **NOT** include any text before or after the JSON code block.
```json
{{
  "provider_name": "Name of the Insurance Company",
  "policy_name": "Name of the Insurance Policy",
  "tier_name": "[POLICY TIER NAME]", // The tier you extracted for
  "extraction_date": "YYYY-MM-DD", // Date of extraction
  "currency": "Currency Code (e.g., SGD, USD)",
  "coverage_categories": [
    {{
      "category_name": "Name of the Benefit Category (e.g., Personal Accident Benefits)",
      "coverages": [
        {{
          "coverage_name": "Specific Name of the Coverage (e.g., Accidental Death and Permanent Disability)",
          "limits": [
            // Array of limit objects. Each object represents a specific limit variation.
            {{
              "type": "Description of the limit scope (e.g., 'Adult under 70 years', 'Maximum Limit for Family Cover', 'Per Person', 'Per item')",
              "limit": "Numerical_Limit_Value_Or_String_Like_Actual_cost_or_Unlimited",
              // Optional: Add 'basis' key if limit is calculated (e.g., per X hours)
              // "basis": "Description of basis (e.g., 'S$100 every 6 hours')"
            }}
            // ... more limit objects if applicable (e.g., different ages, child, family)
          ],
          "details": "Summarized key conditions, definitions, inclusions, or exclusions for THIS specific coverage from the policy text relevant to the specified tier. DO NOT just write 'Refer to Section X'.",
          "source_info": "Brief location identifier from the document (e.g., 'Page 3, Section 1', 'Page 4, Travel Delay table', 'Page 5, COVID-19 Extension')"
        }}
        // ... more coverage objects within this category
      ]
    }}
    // ... more category objects
  ]
}}
```
**Crucial Instructions:**
1.  **Tier Specificity:** Extract data *only* for the `[POLICY TIER NAME]` tier. If limits are shared across tiers, use the value specified for this tier.
2.  **`details` Field Content:** This is critical. **DO NOT** use placeholder text like "Refer to Section X". You **MUST** read the relevant section(s) in the policy text referenced (or identifiable) for each coverage and **summarize** the key applicable conditions, definitions, major inclusions/exclusions, or other pertinent information for that coverage and specified tier. If a benefit is not covered for a specific tier, explicitly state that if mentioned. If no specific additional details are found beyond the benefit name and limit, state `No specific additional details found for this tier beyond the benefit description.`
3.  **`source_info` Field:** For each `coverage` object, include a `source_info` string briefly indicating where the data (name, limit, details) was primarily found in the document (e.g., Page number, Section number, Table name).
4.  **`limits` Array:** Capture all relevant limits shown for the specific coverage and tier. Use the `type` field to clarify the scope (e.g., 'Adult under 70', 'Child', 'Family Cover', 'Per Person', 'Per day max'). Ensure the `limit` value is the numerical amount (or appropriate string like "Unlimited" or "Actual cost"). If a limit has a specific basis (e.g., "$100 per 6 hours"), include this information, potentially within the `details` or as a separate `basis` key within the limit object.
5.  **Currency:** Identify and include the correct currency code (e.g., "SGD").
6.  **Completeness:** Extract all distinct coverage categories and the specific coverages listed under them for the specified tier.
7.  **Accuracy:** Ensure benefit names, limits, and summarized details accurately reflect the policy document for the specified tier.
8.  **JSON Only:** Your entire output must be just the JSON object, starting with `{{` and ending with `}}`.
**Positive Example (Illustrative Snippet for Great Eastern TravelSmart Premier - Elite Plan):**
```json
{{
  "provider_name": "Great Eastern",
  "policy_name": "TravelSmart Premier",
  "tier_name": "Elite",
  "extraction_date": "2024-07-26",
  "currency": "SGD",
  "coverage_categories": [
    {{
      "category_name": "Personal Accident Benefits",
      "coverages": [
        {{
          "coverage_name": "Accidental Death and Permanent Disability",
          "limits": [
            {{"type": "Adult under 70 years", "limit": 500000}},
            {{"type": "Adult age 70 years or above", "limit": 150000}},
            {{"type": "Child", "limit": 100000}},
            {{"type": "Maximum Limit for Family Cover", "limit": 1200000}}
          ],
          "details": "Provides lump sum payment in the event of accidental death or permanent disablement occurring during the trip, subject to the scale of compensation. Excludes disablement from illness.",
          "source_info": "Page 3, Section 1"
        }}
      ]
    }},
    {{
      "category_name": "Travel Inconvenience Benefits",
      "coverages": [
         {{
          "coverage_name": "Travel Delay While Overseas",
          "limits": [
            {{"type": "Per Person Max", "limit": 1200, "basis": "S$100 every 6 hours"}}
          ],
          "details": "Payable for delay of scheduled public conveyance for every full 6 consecutive hours of delay while overseas. Requires written confirmation from carrier stating duration and reason for delay. Excludes delays known before booking/purchase.",
          "source_info": "Page 4, Section 21A"
        }}
      ]
    }}
    // ... other categories and coverages
  ]
}}
```
**Negative Examples (Mistakes to Avoid):**
1.  **Incorrect `details` Field (Placeholder Text):**
    ```json
    // ... inside a coverage object ...
    {{
        "coverage_name": "Trip Cancellation",
        // ... limits ...
        "details": "Refer to Section 15.", // <-- WRONG: Should summarize Section 15 content.
        "source_info": "Page 4, Section 15"
    }}
    ```
2.  **Missing `source_info` Field:**
    ```json
    // ... inside a coverage object ...
    {{
        "coverage_name": "Baggage Loss",
        // ... limits ...
        "details": "Covers loss of baggage due to theft or misdirection by carrier, up to per item limits and overall maximum. Depreciation applies.",
        // <-- WRONG: Missing the source_info field entirely.
    }}
    ```
3.  **Incorrect `limits` Structure (Flat values instead of array of objects):**
    ```json
    // ... inside a coverage object ...
    {{
        "coverage_name": "Medical Expenses While Overseas",
        "limits": {{ // <-- WRONG: Should be an array [{{ "type": "...", "limit": ...}}, ...]
            "Adult under 70 years": 500000,
            "Child": 300000
        }},
        "details": "Covers necessary medical treatment incurred overseas due to accident or illness during the trip.",
        "source_info": "Page 3, Section 3"
    }}
    ```
4.  **Missing Tier-Specific Data:** Extracting data generally without confirming it applies specifically to the requested `[POLICY TIER NAME]`.
---
Please process the provided policy document for the **`[POLICY TIER NAME]`** tier and generate the JSON output according to these instructions.
"""

# --- Helper Functions ---


def load_environment_variables():
    """Loads environment variables from .env file."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning(
            "GOOGLE_API_KEY not found in environment variables or .env file."
        )
    return api_key


def ensure_output_directory(directory_path: str):
    """Creates the output directory if it doesn't exist."""
    os.makedirs(directory_path, exist_ok=True)


def call_gemini_with_retry(
    model_name: str,
    prompt: str,
    pdf_data: bytes,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Calls the Gemini API with exponential backoff on retriable errors.

    Args:
        model_name: The name of the Gemini model to use.
        prompt: The text prompt for the model.
        pdf_data: The raw bytes of the PDF file.
        api_key: Optional Google API key.

    Returns:
        The generated text content from the model, or None if the call fails after retries.
    """
    if api_key:
        genai.configure(api_key=api_key)
    elif not os.getenv("GOOGLE_API_KEY"):
        logger.error(
            "API key must be provided either via --api-key or GOOGLE_API_KEY env var."
        )
        return None  # Cannot proceed without API key

    model = genai.GenerativeModel(model_name)
    retries = 0
    backoff_time = INITIAL_BACKOFF

    while retries <= MAX_RETRIES:
        try:
            logger.info(f"Attempting API call (Retry {retries}/{MAX_RETRIES})...")
            response = model.generate_content(
                contents=[
                    {"mime_type": "application/pdf", "data": pdf_data},
                    prompt,
                ],
                generation_config=genai.types.GenerationConfig(
                    # Ensure JSON output if model supports it (some models might need specific instructions)
                    # response_mime_type="application/json" # Uncomment if using a model version that supports this directly
                ),
            )
            # Clean potential markdown code block fences
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            return cleaned_text

        except (
            google_exceptions.ResourceExhausted,
            google_exceptions.ServiceUnavailable,
            google_exceptions.InternalServerError,
            google_exceptions.DeadlineExceeded,
            # Add other potentially retriable exceptions if needed
        ) as e:
            logger.warning(
                f"Retriable API error: {e}. Retrying in {backoff_time} seconds..."
            )
            time.sleep(backoff_time)
            retries += 1
            backoff_time *= 2  # Exponential backoff
        except Exception as e:
            logger.error(f"Non-retriable API error: {e}")
            return None  # Non-retriable error

    logger.error("API call failed after maximum retries.")
    return None


# --- Main Processing Function ---


def process_policies(input_dir: str, output_dir: str, api_key: Optional[str]):
    """
    Processes PDF policy files in the input directory, extracts tier-specific
    information using Gemini, validates, and saves as JSON.
    """
    logger.info(f"Starting policy processing from: {input_dir}")
    ensure_output_directory(output_dir)

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for filename in os.listdir(input_dir):
        match = FILENAME_PATTERN.match(filename)
        if match:
            input_path = os.path.join(input_dir, filename)
            insurer_name, policy_tier = (
                match.groups()
            )  # Insurer name might need refinement later
            output_filename = f"{filename.rsplit('.', 1)[0]}.json"
            output_path = os.path.join(output_dir, output_filename)

            logger.info(f"Processing: {filename} (Tier: {policy_tier})")

            # Check if output file already exists
            if os.path.exists(output_path):
                logger.error(f"Output file already exists, skipping: {output_path}")
                skipped_count += 1
                continue

            # Read PDF content
            try:
                with open(input_path, "rb") as f:
                    pdf_data = f.read()
            except Exception as e:
                logger.error(f"Failed to read PDF file {input_path}: {e}")
                error_count += 1
                continue

            # Format the prompt
            formatted_prompt = PROMPT_TEMPLATE.format(policy_tier=policy_tier)

            # Call Gemini API
            response_text = call_gemini_with_retry(
                GEMINI_MODEL, formatted_prompt, pdf_data, api_key
            )

            if not response_text:
                logger.error(f"Failed to get response from Gemini for {filename}")
                error_count += 1
                continue

            # Parse and Validate JSON
            try:
                extracted_data = json.loads(response_text)
                # Add extraction date before validation if missing
                if "extraction_date" not in extracted_data:
                    extracted_data["extraction_date"] = datetime.now().strftime(
                        "%Y-%m-%d"
                    )

                # Validate with Pydantic
                validated_data = PolicyExtraction(**extracted_data)
                # Use model_dump for serialization to ensure correct types
                output_json = validated_data.model_dump(mode="json")

                # Write JSON output
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(output_json, f, indent=2, ensure_ascii=False)
                    logger.info(f"Successfully processed and saved: {output_path}")
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to write JSON file {output_path}: {e}")
                    error_count += 1

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response for {filename}: {e}")
                logger.debug(f"Raw response for {filename}:\n{response_text}")
                error_count += 1
            except ValidationError as e:
                logger.error(f"JSON validation failed for {filename}: {e}")
                logger.debug(
                    f"Invalid JSON data for {filename}:\n{extracted_data}"
                )  # Log data before validation error
                error_count += 1
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during processing {filename}: {e}"
                )
                error_count += 1

        else:
            if filename != ".gitkeep":  # Ignore .gitkeep
                logger.warning(f"Skipping file with non-matching format: {filename}")

    logger.info(
        f"Processing complete. Processed: {processed_count}, Skipped (exists): {skipped_count}, Errors: {error_count}"
    )


# --- Script Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract policy tier information from PDFs using Gemini."
    )
    parser.add_argument(
        "--input-dir",
        default=INPUT_DIR_DEFAULT,
        help=f"Directory containing raw policy PDFs (default: {INPUT_DIR_DEFAULT})",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR_DEFAULT,
        help=f"Directory to save processed JSON files (default: {OUTPUT_DIR_DEFAULT})",
    )
    parser.add_argument(
        "--api-key",
        help="Google Gemini API key (overrides GOOGLE_API_KEY environment variable)",
    )

    args = parser.parse_args()

    # Load API key from .env first, then allow override from args
    loaded_api_key = load_environment_variables()
    final_api_key = args.api_key if args.api_key else loaded_api_key

    if not final_api_key:
        logger.error(
            "Google API Key is required. Set GOOGLE_API_KEY environment variable or use --api-key argument."
        )
    else:
        process_policies(args.input_dir, args.output_dir, final_api_key)
