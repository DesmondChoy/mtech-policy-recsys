import os
import json
import time
import argparse
from dotenv import load_dotenv
from typing import Dict, Any
from datetime import datetime

# Import the LLM service and transcript processing
from src.models import LLMService
from src.agents import *
from src.agents.extractor import insurance_recommendation_crew
from src.utils.transcript_processing import process_transcript, parse_transcript

from crewai import Agent, Crew, Task

def process_customer_requirements(raw_transcript_path: str, output_dir: str, requirements_dir: str) -> Dict[str, Any]:
    """
    Process a customer's raw transcript and extract their insurance requirements.
    
    Args:
        raw_transcript_path (str): Path to the raw transcript file
        output_dir (str): Directory to store processed transcript
        requirements_dir (str): Directory to store extracted requirements
        
    Returns:
        Dict[str, Any]: The extracted customer requirements
    """
    # Load environment variables
    load_dotenv()

    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Initialize the LLM service
    llm_service = LLMService()
    print("LLM service initialized successfully.")

    # Create output directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(requirements_dir, exist_ok=True)
    
    # Generate filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_filename = f"parsed_transcript_{timestamp}.json"
    requirements_filename = f"customer_requirements_{timestamp}.json"
    
    transcript_path = os.path.join(output_dir, transcript_filename)
    requirements_path = os.path.join(requirements_dir, requirements_filename)
    
    # Process the transcript
    parsed_data, success = process_transcript(raw_transcript_path, transcript_path)
    if not success or not parsed_data:
        raise ValueError("Failed to process transcript")
    
    # Convert the transcript data to a string format for the agent
    formatted_transcript = "\n".join([f"{msg['speaker']}: {msg['dialogue']}" for msg in parsed_data])
    
    input_transcript = {
        'parsed_transcripts': formatted_transcript
    }
    
    # Run the insurance recommendation crew
    result = insurance_recommendation_crew.kickoff(inputs=input_transcript)
    
    # Convert CrewOutput to dict if needed
    if hasattr(result, 'raw'):
        result_dict = json.loads(result.raw)
    else:
        result_dict = result
    
    # Save the extracted requirements
    with open(requirements_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    return result_dict

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process customer call transcript and extract insurance requirements')
    parser.add_argument('transcript_path', help='Path to the raw transcript file')
    parser.add_argument('--output-dir', default='data/processed_transcript',
                      help='Directory to store processed transcript (default: data/processed_transcript)')
    parser.add_argument('--requirements-dir', default='data/extracted_customer_requirements',
                      help='Directory to store extracted requirements (default: data/extracted_customer_requirements)')
    
    args = parser.parse_args()
    
    try:
        # Get absolute paths for directories
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))  # Go up two levels from src/web to project root
        output_dir = os.path.join(project_root, args.output_dir)
        requirements_dir = os.path.join(project_root, args.requirements_dir)
        
        # Process the transcript
        result = process_customer_requirements(args.transcript_path, output_dir, requirements_dir)
        print("\nExtracted Requirements:", json.dumps(result, indent=2))
        print(f"\nProcessed transcript saved to: {output_dir}")
        print(f"Extracted requirements saved to: {requirements_dir}")
    except Exception as e:
        print(f"Error processing requirements: {str(e)}")

if __name__ == "__main__":
    main()


