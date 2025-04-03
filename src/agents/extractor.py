"""
Extractor Agent Script

Purpose:
This script defines and runs the Extractor Agent using the CrewAI framework.
The agent's primary goal is to analyze processed call transcripts (JSON format)
and extract key customer requirements for travel insurance, structuring them
into a validated JSON object based on the TravelInsuranceRequirement Pydantic model.

Input:
- Reads processed transcript JSON files from a specified directory. Each JSON file
  should contain a list of dictionaries, where each dictionary has 'speaker' and
  'dialogue' keys.
- Default input directory: data/transcripts/processed/

Output:
- Generates structured customer requirement JSON files.
- Saves output files to a specified directory.
- Default output directory: data/extracted_customer_requirements/
- Output filename format: requirements_{original_transcript_name_part}.json
  (e.g., requirements_the_anxious_inquirer_20250403_152253.json)

Dependencies:
- Requires a .env file in the project root containing OpenAI API keys:
  - OPENAI_API_KEY
  - OPENAI_MODEL_NAME (optional, defaults to gpt-4o)
- Relies on the TravelInsuranceRequirement model from src.utils.transcript_processing.

Usage:
Run from the project root directory:
  python src/agents/extractor.py

Optional arguments:
  --input_dir PATH   : Specify a different input directory for processed transcripts.
  --output_dir PATH  : Specify a different output directory for requirement files.
"""

import os
import json
import argparse
from pprint import pprint
from dotenv import load_dotenv
from crewai import Agent, Crew, Task
from src.utils.transcript_processing import TravelInsuranceRequirement

# Step 1: Requirement Extraction Agent - Processes Call Transcripts
transcript_analyst = Agent(
    role="Call Transcript Analyst",
    goal="Extract and structure travel insurance customer requirements from call transcripts into a validated JSON object.",
    backstory=(
        "A seasoned customer service analyst specializing in extracting travel insurance requirements from call transcripts. "
        "This agent listens to conversations between customers and service staff, identifies key requirements, and formats "
        "the insights into a structured JSON output that conforms to the TravelInsuranceRequirement model for accurate policy matching."
    ),
    allow_delegation=False,
    verbose=True,
)

# Define the agent task
transcript_analyst_task = Task(
    description="""Analyze the travel insurance call transcript below and extract key customer requirements.
Step 1: Read the transcript carefully and extract all relevant details. For each field in the schema, provide a brief annotation or reference to the specific portion(s) of the transcript where the detail was found.
Step 2: Review your annotations to verify that every extracted detail directly matches the transcript. Resolve any discrepancies or conflicts in the data.
Step 3: Produce a final, validated JSON object that adheres exactly to the TravelInsuranceRequirement schema with the following fields:
- requirement_id (str): A unique identifier.
- requirement_summary (str): A concise summary of the customer's insurance needs.
- detailed_description (str): A detailed narrative extracted from the transcript.
- travel_destination (Optional[str]): The destination (country or region) mentioned.
- travel_duration (Optional[str]): Duration of the trip (e.g., "7 days", "1 month").
- travel_start_date (Optional[date]): The travel start date.
- travel_end_date (Optional[date]): The travel end date.
- insurance_coverage_type (Optional[List[str]]): The types of insurance coverage requested (e.g., ["Medical", "Trip Cancellation"]).
- pre_existing_conditions (Optional[List[str]]): Any pre-existing conditions mentioned.
- age_group (Optional[str]): Age bracket of the travelers (e.g., "26-40").
- travelers_count (Optional[int]): Number of travelers.
- budget_range (Optional[str]): Budget constraints (e.g., "$100-$200").
- preferred_insurance_provider (Optional[str]): Preferred insurance provider, if any.
- additional_requests (Optional[str]): Any special requests or concerns.
- keywords (Optional[List[str]]): Important keywords or terms for further analysis.

If a field is not mentioned in the transcript, use null.

Transcript:
{parsed_transcripts}
""",
    expected_output="A JSON object that matches the TravelInsuranceRequirement model.",
    agent=transcript_analyst,
    output_json=TravelInsuranceRequirement,
)

# Define the crew with agents and tasks
insurance_recommendation_crew = Crew(
    agents=[transcript_analyst], tasks=[transcript_analyst_task], verbose=True
)


def main():
    # Load environment variables from .env file
    load_dotenv()

    # Check for OpenAI API Key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is not set. Please add it to your .env file.")

    # Set environment variables for CrewAI (optional if already set globally, but good practice)
    os.environ["OPENAI_API_KEY"] = openai_api_key
    # Ensure the desired model is set, matching the notebook if necessary
    os.environ["OPENAI_MODEL_NAME"] = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

    # --- Determine Project Root ---
    # Assuming this script is in src/agents/, project root is two levels up
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # --- Set up argument parser ---
    parser = argparse.ArgumentParser(
        description="Extract travel insurance requirements from transcript JSON files in a directory."
    )
    parser.add_argument(
        "--input_dir",
        default=os.path.join(project_root, "data", "transcripts", "processed"),
        help="Path to the directory containing parsed transcript JSON files.",
    )
    parser.add_argument(
        "--output_dir",
        default=os.path.join(project_root, "data", "extracted_customer_requirements"),
        help="Path to the directory where extracted requirements JSON files will be saved.",
    )
    args = parser.parse_args()

    # --- Validate input directory ---
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found at {args.input_dir}")
        return

    # --- Ensure output directory exists ---
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Starting batch extraction from: {args.input_dir}")
    print(f"Output will be saved to: {args.output_dir}")

    processed_count = 0
    failed_count = 0

    # --- Iterate through files in the input directory ---
    for filename in os.listdir(args.input_dir):
        if filename.lower().endswith(".json"):
            input_file_path = os.path.join(args.input_dir, filename)
            print(f"\n--- Processing file: {filename} ---")

            # --- Read and parse the JSON transcript ---
            try:
                with open(input_file_path, "r", encoding="utf-8") as f:
                    transcript_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {input_file_path}")
                failed_count += 1
                continue  # Skip to next file
            except Exception as e:
                print(f"Error reading transcript file {input_file_path}: {e}")
                failed_count += 1
                continue  # Skip to next file

            # --- Convert the transcript data to a string format for the agent ---
            formatted_transcript = ""
            if isinstance(transcript_data, list) and all(
                isinstance(item, dict) and "speaker" in item and "dialogue" in item
                for item in transcript_data
            ):
                formatted_transcript = "\n".join(
                    [f"{msg['speaker']}: {msg['dialogue']}" for msg in transcript_data]
                )
            else:
                print(
                    f"Error: Transcript data in {filename} is not in the expected format (list of {{'speaker': ..., 'dialogue': ...}} dictionaries)."
                )
                # Attempt to handle if it's already a string or other format if needed
                if isinstance(transcript_data, str):
                    print("Attempting to use raw string data.")
                    formatted_transcript = (
                        transcript_data  # Assume it's already formatted
                    )
                else:
                    # Fallback or specific handling for other formats if necessary
                    print(
                        "Attempting to convert transcript data to string as fallback."
                    )
                    try:
                        formatted_transcript = str(transcript_data)
                    except Exception as str_e:
                        print(f"Could not convert transcript data to string: {str_e}")
                        failed_count += 1
                        continue  # Skip to next file

            if not formatted_transcript:
                print(f"Error: Could not format transcript from {filename}. Skipping.")
                failed_count += 1
                continue  # Skip to next file

            # --- Prepare inputs for the crew ---
            input_data = {"parsed_transcripts": formatted_transcript}

            # --- Execute the crew to process the transcript ---
            print("Kicking off the crew...")
            result = None  # Initialize result
            try:
                result = insurance_recommendation_crew.kickoff(inputs=input_data)
                # Print the result
                print("\nExtraction Result:")
                pprint(result)

            except Exception as crew_e:
                print(f"Error during CrewAI kickoff for {filename}: {crew_e}")
                failed_count += 1
                continue  # Skip to next file

            # --- Save the result to a dynamic file path ---
            if result:
                try:
                    # Get the base name of the input transcript file
                    base_name = os.path.basename(input_file_path)
                    # Construct the desired output filename: requirements_{original_name}.json
                    name_part = os.path.splitext(base_name)[0]
                    if name_part.startswith("parsed_"):
                        name_part = name_part[len("parsed_") :]
                    if name_part.startswith("transcript_"):
                        name_part = name_part[len("transcript_") :]
                    output_filename = f"requirements_{name_part}.json"

                    output_path = os.path.join(args.output_dir, output_filename)

                    # Save the result dictionary as JSON
                    with open(output_path, "w", encoding="utf-8") as f:
                        # Convert the Pydantic model (result) to a dictionary before saving
                        # Check if result is already a dict (sometimes crewai might return dict)
                        if isinstance(result, dict):
                            json.dump(result, f, indent=4, ensure_ascii=False)
                        elif hasattr(
                            result, "model_dump"
                        ):  # Check if it's a Pydantic model
                            json.dump(
                                result.model_dump(), f, indent=4, ensure_ascii=False
                            )
                        else:
                            print(
                                f"Warning: Result for {filename} is not a dict or Pydantic model. Attempting to save raw result."
                            )
                            json.dump(
                                str(result), f, indent=4, ensure_ascii=False
                            )  # Save string representation as fallback

                    print(f"\nSuccessfully saved extraction results to: {output_path}")
                    processed_count += 1

                except Exception as save_e:
                    print(f"\nError saving extraction results for {filename}: {save_e}")
                    failed_count += 1
            else:
                print(f"\nNo result generated for {filename}, skipping save.")
                failed_count += 1  # Count as failed if no result

    print(f"\n--- Batch Extraction Finished ---")
    print(f"Successfully processed: {processed_count} files.")
    print(f"Failed attempts: {failed_count} files.")


if __name__ == "__main__":
    main()
