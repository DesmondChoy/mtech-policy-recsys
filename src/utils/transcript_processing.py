import json
import re
import os
import argparse  # Added argparse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class TravelInsuranceRequirement(BaseModel):
    requirement_id: str = Field(
        ..., description="Unique identifier for tracking the insurance requirement."
    )
    requirement_summary: str = Field(
        ..., description="Concise summary of the customer's insurance needs."
    )
    detailed_description: str = Field(
        ..., description="Detailed narrative extracted from the transcript."
    )
    travel_origin: Optional[str] = Field(
        None, description="Country or region the customer is traveling from."
    )
    travel_destination: Optional[str] = Field(
        None, description="Country or region the customer is traveling to."
    )
    travel_duration: Optional[str] = Field(
        None, description="Duration of the trip (e.g., '7 days', '1 month')."
    )
    insurance_coverage_type: Optional[List[str]] = Field(
        None,
        description="Types of insurance coverage requested (e.g., ['Medical', 'Trip Cancellation']).",
    )
    pre_existing_conditions: Optional[List[str]] = Field(
        None,
        description="Any pre-existing conditions mentioned that might affect coverage.",
    )
    medical_needs: Optional[List[str]] = Field(
        None, description="Specific medical coverage needs or requirements."
    )
    activities_to_cover: Optional[List[str]] = Field(
        None,
        description="Specific activities that need coverage (e.g., 'Skiing', 'Scuba diving').",
    )
    age_group: Optional[str] = Field(
        None, description="Age range of the traveler (e.g., '18-25', '26-35', '36-45')."
    )
    additional_requests: Optional[str] = Field(
        None, description="Any special requests or concerns noted by the customer."
    )
    keywords: Optional[List[str]] = Field(
        None,
        description="Important keywords or terms extracted from the transcript for further analysis.",
    )


def parse_transcript(file_path: str) -> Optional[List[Dict[str, str]]]:
    """
    Parse a transcript file (.txt or .json) into a list of speaker-dialogue pairs.
    Handles both plain text format (Speaker: Dialogue) and the new JSON format
    (extracting the list from the 'transcript' key).

    Args:
        file_path (str): Path to the transcript file.

    Returns:
        Optional[List[Dict[str, str]]]: List of dictionaries containing speaker and dialogue,
                                         or None if parsing fails.
    """
    conversation: List[Dict[str, str]] = []
    _, file_extension = os.path.splitext(file_path)

    try:
        if file_extension.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            # Expecting a structure like {"personality": {...}, "transcript": [...]}
            if (
                isinstance(data, dict)
                and "transcript" in data
                and isinstance(data["transcript"], list)
            ):
                # Basic validation of list items
                for item in data["transcript"]:
                    if (
                        isinstance(item, dict)
                        and "speaker" in item
                        and "dialogue" in item
                    ):
                        conversation.append(
                            {
                                "speaker": str(item["speaker"]),
                                "dialogue": str(item["dialogue"]),
                            }
                        )
                    else:
                        print(
                            f"Warning: Skipping invalid item in JSON transcript list: {item}"
                        )
                if not conversation:  # If the list was empty or all items were invalid
                    print(
                        f"Warning: 'transcript' key found in {file_path}, but it contained no valid speaker/dialogue pairs."
                    )
                    return None  # Or return empty list [] depending on desired behavior
                return conversation
            else:
                print(
                    f"Error: JSON file {file_path} does not contain a valid 'transcript' list."
                )
                return None

        elif file_extension.lower() == ".txt":
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for line in lines:
                match = re.match(r"^(.*?): (.*)", line.strip())
                if match:
                    speaker = match.group(1).strip()
                    dialogue = match.group(2).strip()
                    conversation.append({"speaker": speaker, "dialogue": dialogue})

            if not conversation:
                print(
                    f"Warning: No speaker/dialogue pairs found in text file: {file_path}"
                )
                # Decide if returning None or [] is better here
            return conversation

        else:
            print(
                f"Error: Unsupported file type '{file_extension}' for file: {file_path}"
            )
            return None

    except FileNotFoundError:
        print(f"Error: Could not find the file at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file: {file_path}")
        return None
    except Exception as e:
        print(f"Error occurred while parsing transcript '{file_path}': {str(e)}")
        return None


def export_to_json(data, output_file):
    """
    Export data to a JSON file.

    Args:
        data: The data to be exported
        output_file (str): Path to the output JSON file

    Returns:
        bool: True if export was successful, False otherwise
    """
    try:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        print(f"Data successfully exported to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving JSON file: {str(e)}")
        return False


def process_transcript(input_file_path, output_file_path):
    """
    Process a transcript file by parsing it and exporting to JSON in one step.

    Args:
        input_file_path (str): Path to the input transcript file
        output_file_path (str): Path where the JSON output should be saved

    Returns:
        tuple: (parsed_data, bool) where parsed_data is the parsed transcript data
               and bool indicates if the entire process was successful
    """
    # Parse the transcript
    parsed_data = parse_transcript(input_file_path)

    if parsed_data is None:
        return None, False

    # Export to JSON
    export_success = export_to_json(parsed_data, output_file_path)

    return parsed_data, export_success


def run_batch_processing():
    """Runs the original batch processing logic."""
    # Get the absolute path to the project root directory (2 levels up from this script)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # --- Define input and output directories ---
    input_dir = os.path.join(project_root, "data", "transcripts", "raw", "synthetic")
    output_dir = os.path.join(project_root, "data", "transcripts", "processed")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting batch processing of transcripts from: {input_dir}")
    print(f"Output will be saved to: {output_dir}")

    processed_count = 0
    failed_count = 0

    # Iterate through files in the input directory
    for filename in os.listdir(input_dir):
        input_file_path = os.path.join(input_dir, filename)

        # Check if it's a file and has a supported extension (.txt or .json)
        if os.path.isfile(input_file_path) and filename.lower().endswith(
            (".txt", ".json")
        ):
            print(f"\nProcessing file: {filename}")

            # --- Construct the NEW output filename ---
            output_filename = f"parsed_{filename}"  # Default fallback
            base_name_input = os.path.splitext(filename)[
                0
            ]  # e.g., transcript_golf_coverage_49eb...

            if base_name_input.startswith("transcript_"):
                name_part = base_name_input[
                    len("transcript_") :
                ]  # e.g., golf_coverage_49eb...
                # Find the last underscore to separate scenario and UUID
                last_underscore_index = name_part.rfind("_")
                if last_underscore_index != -1:
                    scenario_name = name_part[
                        :last_underscore_index
                    ]  # e.g., golf_coverage
                    uuid = name_part[last_underscore_index + 1 :]  # e.g., 49eb...
                    # Construct the desired output filename
                    output_filename = f"parsed_transcript_{scenario_name}_{uuid}.json"
                else:
                    # Handle cases where the format might be unexpected (e.g., no underscore)
                    print(
                        f"Warning: Could not parse scenario/UUID from filename '{filename}'. Using fallback name."
                    )
            else:
                # Handle cases where filename doesn't start with 'transcript_'
                print(
                    f"Warning: Input filename '{filename}' doesn't match expected format 'transcript_*'. Using fallback name."
                )

            # Ensure output is always .json (redundant if parsed correctly, but safe fallback)
            if not output_filename.lower().endswith(".json"):
                output_filename = os.path.splitext(output_filename)[0] + ".json"

            output_file_path = os.path.join(output_dir, output_filename)
            # --- End of NEW output filename construction ---

            # Process the transcript
            parsed_data, success = process_transcript(input_file_path, output_file_path)

            if success:
                print(f"Successfully processed and saved to {output_filename}")
                processed_count += 1
            else:
                print(f"Failed to process {filename}")
                failed_count += 1
        # Optionally skip non-supported files silently or log them
        # else:
        #     if os.path.isfile(input_file_path):
        #         print(f"Skipping unsupported file type: {filename}")

    print(f"\nBatch processing finished.")
    print(f"Successfully processed: {processed_count} files.")
    print(f"Failed to process: {failed_count} files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse transcript files (.txt or .json). Runs in batch mode if no arguments are provided."
    )
    parser.add_argument(
        "--input", help="Path to a single input transcript file to process."
    )
    parser.add_argument(
        "--output",
        help="Path to save the parsed output JSON file (required if --input is specified).",
    )
    args = parser.parse_args()

    if args.input and args.output:
        # --- Single File Processing ---
        print(f"Processing single file: {args.input}")
        print(f"Output will be saved to: {args.output}")
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if (
            output_dir
        ):  # Ensure output_dir is not empty (e.g., if output is just a filename)
            os.makedirs(output_dir, exist_ok=True)

        parsed_data, success = process_transcript(args.input, args.output)
        if success:
            print(f"Successfully processed and saved to {args.output}")
        else:
            print(f"Failed to process {args.input}")
            exit(1)  # Exit with error code if single file processing fails
    elif args.input or args.output:
        # Error if only one argument is provided
        parser.error("--input and --output must be specified together.")
    else:
        # --- Batch Processing (Default) ---
        run_batch_processing()
