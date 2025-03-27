"""
LLM Service Tutorial

This script demonstrates how to use the LLM service to interact with Google Gemini.
It provides examples of basic content generation, structured output generation,
streaming responses, and error handling.

To run this tutorial:
1. Make sure you have set the GOOGLE_API_KEY environment variable or created a .env file
2. Install the required dependencies: pip install -r requirements.txt
3. Run the script: python tutorials/llm_service_tutorial.py
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the LLM service directly
from src.models.llm_service import LLMService

# Load environment variables from .env file
load_dotenv()

# Check if API key is set
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY environment variable is not set.")
    print("Please set it in your .env file or environment variables.")
    exit(1)

# Initialize the LLM service
llm_service = LLMService()
print("LLM service initialized successfully.")


def separator(title):
    """Print a separator with a title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def example_basic_content_generation():
    """Example of basic content generation."""
    separator("Basic Content Generation")

    prompt = "Explain how AI works in 3 sentences."
    print(f"Prompt: {prompt}\n")

    try:
        response = llm_service.generate_content(prompt)
        print(f"Response:\n{response.text}\n")
    except Exception as e:
        print(f"Error: {str(e)}")


def example_structured_output():
    """Example of structured output generation."""
    separator("Structured Output Generation (JSON)")

    prompt = """
    Create a list of 3 travel insurance policies with the following information:
    - Name
    - Provider
    - Coverage types (medical, trip cancellation, baggage loss)
    - Price range
    """
    print(f"Prompt: {prompt}\n")

    try:
        response = llm_service.generate_structured_content(prompt)
        print(f"Response (as Python dict):\n{json.dumps(response, indent=2)}\n")
    except Exception as e:
        print(f"Error: {str(e)}")


def example_streaming_response():
    """Example of streaming response."""
    separator("Streaming Response")

    prompt = "Write a short story about a traveler who forgot to buy travel insurance."
    print(f"Prompt: {prompt}\n")

    print("Response (streaming):")
    try:
        for chunk in llm_service.stream_content(prompt):
            print(chunk, end="", flush=True)
            time.sleep(0.01)  # Slow down output for demonstration
        print("\n")
    except Exception as e:
        print(f"\nError: {str(e)}")


def example_error_handling_and_retry():
    """Example of error handling and retry logic."""
    separator("Error Handling and Retry Logic")

    # Example with validation function
    prompt = "Generate a number between 1 and 10."
    print(f"Prompt: {prompt}")
    print(
        "With validation to ensure the response contains a number between 1 and 10.\n"
    )

    def validate_number(text):
        """Validate that the text contains a number between 1 and 10."""
        import re

        numbers = re.findall(r"\b([1-9]|10)\b", text)
        return len(numbers) > 0

    try:
        response = llm_service.generate_with_retry(
            prompt=prompt, validation_func=validate_number, max_retries=3
        )
        print(f"Response (validated):\n{response.text}\n")
    except ValueError as e:
        print(f"Validation Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")


def example_different_models():
    """Example of using different models."""
    separator("Using Different Models")

    prompt = "What are the benefits of travel insurance?"
    print(f"Prompt: {prompt}\n")

    try:
        print("Using default model (gemini-2.0-flash):")
        response_default = llm_service.generate_content(prompt)
        print(f"{response_default.text}\n")

        # Using the flash model (gemini-2.0-flash)
        print("Using flash model (gemini-2.0-flash):")
        response_flash = llm_service.generate_content(
            prompt=prompt, model="gemini-2.0-flash"
        )
        print(f"{response_flash.text}\n")
    except Exception as e:
        print(f"Error: {str(e)}")


def example_batch_generation():
    """Example of batch generation."""
    separator("Batch Generation")

    prompts = [
        "What is trip cancellation insurance?",
        "What is medical evacuation coverage?",
        "What is baggage loss protection?",
    ]

    print("Prompts:")
    for i, prompt in enumerate(prompts, 1):
        print(f"{i}. {prompt}")
    print()

    try:
        responses = llm_service.batch_generate(prompts)

        print("Responses:")
        for i, response in enumerate(responses, 1):
            print(f"{i}. {response.text[:100]}...\n")
    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    """Run all examples."""
    print("Welcome to the LLM Service Tutorial!")
    print(
        "This tutorial demonstrates how to use the LLM service to interact with Google Gemini."
    )

    # Run examples
    example_basic_content_generation()
    example_structured_output()
    example_streaming_response()
    example_error_handling_and_retry()
    example_different_models()
    example_batch_generation()

    print("\nTutorial completed successfully!")


if __name__ == "__main__":
    main()
