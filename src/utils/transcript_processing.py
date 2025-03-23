import json
import re
import os
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class TravelInsuranceRequirement(BaseModel):
    """
    A Pydantic model representing travel insurance requirements extracted from customer conversations.
    
    This class structures and validates travel insurance requirements data, making it easier to process
    and analyze customer needs systematically. It captures essential details about travel plans,
    insurance preferences, and specific customer requirements.
    """
    requirement_id: str  # Unique identifier for tracking
    
    requirement_summary: str  # Summary of the customer's insurance needs
    detailed_description: str  # More detailed requirement extracted from transcript

    travel_destination: Optional[str]  # Country or region the user is traveling to
    travel_duration: Optional[str]  # e.g., "7 days", "1 month", "6 months"
    travel_start_date: Optional[date]  # Date when the travel begins
    travel_end_date: Optional[date]  # Date when the travel ends
    
    insurance_coverage_type: Optional[List[str]]  # e.g., ["Medical", "Trip Cancellation", "Baggage Loss"]
    pre_existing_conditions: Optional[List[str]]  # Any health conditions to be covered
    age_group: Optional[str]  # e.g., "18-25", "26-40", "41-60", "Senior"
    travelers_count: Optional[int]  # Number of travelers to be insured
    
    budget_range: Optional[str]  # e.g., "$50-$100", "$100-$200"
    preferred_insurance_provider: Optional[str]  # If the user has a preference
    
    additional_requests: Optional[str]  # Any special requests, like "Coverage for adventure sports"
    
    keywords: Optional[List[str]]  # Important keywords for analytics

def parse_transcript(file_path):
    """
    Parse a transcript file into a list of speaker-dialogue pairs.
    
    Args:
        file_path (str): Path to the transcript file
        
    Returns:
        list: List of dictionaries containing speaker and dialogue
    """
    conversation = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        for line in lines:
            match = re.match(r"^(.*?): (.*)", line.strip())
            if match:
                speaker = match.group(1).strip()
                dialogue = match.group(2).strip()
                conversation.append({"speaker": speaker, "dialogue": dialogue})

        return conversation
    except FileNotFoundError:
        print(f"Error: Could not find the file at {file_path}")
        return None
    except Exception as e:
        print(f"Error occurred while parsing transcript: {str(e)}")
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

def main():
    # Get the absolute path to the project root directory (2 levels up from this script)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Construct absolute paths using os.path.join for cross-platform compatibility
    input_file = os.path.join(project_root, "data", "transcripts", "synthetic", "transcript_05.txt")
    output_file = os.path.join(project_root, "data", "processed_transcript", "parsed_transcript_05.json")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process the transcript in one step
    parsed_data, success = process_transcript(input_file, output_file)
    
    if not success:
        print("Failed to process transcript.")
    elif parsed_data:
        print("Transcript processing completed successfully.")

if __name__ == "__main__":
    main()