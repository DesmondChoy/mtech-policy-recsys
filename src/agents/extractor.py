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

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Extract travel insurance requirements from a transcript JSON file."
    )
    parser.add_argument(
        "transcript_path", help="Path to the parsed transcript JSON file."
    )
    args = parser.parse_args()

    # Validate input file path
    if not os.path.exists(args.transcript_path):
        print(f"Error: Transcript file not found at {args.transcript_path}")
        return

    # Read and parse the JSON transcript
    try:
        with open(args.transcript_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {args.transcript_path}")
        return
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        return

    # Convert the transcript data to a string format for the agent
    # Assuming transcript_data is a list of dicts like [{'speaker': 'X', 'dialogue': '...'}, ...]
    if isinstance(transcript_data, list) and all(
        isinstance(item, dict) and "speaker" in item and "dialogue" in item
        for item in transcript_data
    ):
        formatted_transcript = "\n".join(
            [f"{msg['speaker']}: {msg['dialogue']}" for msg in transcript_data]
        )
    else:
        print(
            "Error: Transcript data is not in the expected format (list of {'speaker': ..., 'dialogue': ...} dictionaries)."
        )
        # Attempt to handle if it's already a string or other format if needed
        if isinstance(transcript_data, str):
            formatted_transcript = transcript_data  # Assume it's already formatted
        else:
            # Fallback or specific handling for other formats if necessary
            print("Attempting to convert transcript data to string.")
            formatted_transcript = str(transcript_data)

    # Prepare inputs for the crew
    input_data = {"parsed_transcripts": formatted_transcript}

    # Execute the crew to process the transcript
    print("Kicking off the crew...")
    result = insurance_recommendation_crew.kickoff(inputs=input_data)

    # Print the result
    print("\nExtraction Result:")
    pprint(result)

    # --- Save the result to a dynamic file path ---
    if result:
        try:
            # Get the base name of the input transcript file
            base_name = os.path.basename(args.transcript_path)
            # Remove the .json extension and add _requirements.json
            output_filename = os.path.splitext(base_name)[0] + "_requirements.json"

            # Define the output directory
            output_dir = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "data",
                "extracted_customer_requirements",
            )

            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Construct the full output path
            output_path = os.path.join(output_dir, output_filename)

            # Save the result dictionary as JSON
            with open(output_path, "w", encoding="utf-8") as f:
                # Convert the Pydantic model (result) to a dictionary before saving
                json.dump(result.model_dump(), f, indent=4, ensure_ascii=False)

            print(f"\nSuccessfully saved extraction results to: {output_path}")

        except Exception as e:
            print(f"\nError saving extraction results: {e}")
    else:
        print("\nNo result generated, skipping save.")


if __name__ == "__main__":
    main()
