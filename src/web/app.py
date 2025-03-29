import os
import json
import time
from dotenv import load_dotenv

# Import the LLM service
from ..models import LLMService
from ..agents import *
from ..agents.extractor import insurance_recommendation_crew

from crewai import Agent, Crew, Task

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment variables.")
        exit(1)

    # Initialize the LLM service
    llm_service = LLMService()
    print("LLM service initialized successfully.")

    current_dir = os.getcwd()
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

    # TODO: remove this hardcoding
    # Update the path to point to the JSON transcript
    sample_transcript = os.path.join(project_root, "data", "processed_transcript", "parsed_transcript_05.json")

    # Read and parse the JSON transcript
    with open(sample_transcript, 'r') as f:
        transcript_data = json.load(f)

    # Convert the transcript data to a string format for the agent
    formatted_transcript = "\n".join([f"{msg['speaker']}: {msg['dialogue']}" for msg in transcript_data])

    input_transcript = {
        'parsed_transcripts': formatted_transcript
    }

    # Run the insurance recommendation crew
    result = insurance_recommendation_crew.kickoff(inputs=input_transcript)
    print("Result:", result)

if __name__ == "__main__":
    main()


