import json
import re
import os
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class TravelerDetail(BaseModel):
    age: Optional[int] = Field(None, description="Age of the traveler.")
    gender: Optional[str] = Field(None, description="Gender of the traveler (e.g., 'Male', 'Female').")
    citizenship: Optional[str] = Field(None, description="Citizenship of the traveler.")

class TravelInsuranceRequirement(BaseModel):
    requirement_id: str = Field(..., description="Unique identifier for tracking the insurance requirement.")
    requirement_summary: str = Field(..., description="Concise summary of the customer's insurance needs.")
    detailed_description: str = Field(..., description="Detailed narrative extracted from the transcript.")
    
    travel_destination: Optional[str] = Field(None, description="Country or region the customer is traveling to.")
    travel_duration: Optional[str] = Field(None, description="Duration of the trip (e.g., '7 days', '1 month').")
    travel_start_date: Optional[str] = Field(None, description="Start date of the travel.")
    travel_end_date: Optional[str] = Field(None, description="End date of the travel.")
    
    insurance_coverage_type: Optional[List[str]] = Field(
        None, description="Types of insurance coverage requested (e.g., ['Medical', 'Trip Cancellation'])."
    )
    pre_existing_conditions: Optional[List[str]] = Field(
        None, description="Any pre-existing conditions mentioned that might affect coverage."
    )
    age_group: Optional[str] = Field(None, description="Overall age bracket of the travelers (e.g., '26-40').")
    travelers_count: Optional[int] = Field(None, ge=1, description="Number of travelers to be insured (must be at least 1).")
    
    traveler_details: Optional[List[TravelerDetail]] = Field(
        None, description="Detailed demographic information for each traveler."
    )
    
    budget_range: Optional[str] = Field(None, description="Budget constraints (e.g., '$100-$200').")
    preferred_insurance_provider: Optional[str] = Field(None, description="Preferred insurance provider, if any.")
    
    additional_requests: Optional[str] = Field(
        None, description="Any special requests or concerns noted by the customer."
    )
    keywords: Optional[List[str]] = Field(
        None, description="Important keywords or terms extracted from the transcript for further analysis."
    )

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