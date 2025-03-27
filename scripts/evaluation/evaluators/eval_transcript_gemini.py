"""
Gemini-based evaluator for transcript evaluation.

This module contains functions for evaluating transcripts using Google Gemini.
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Import Google Gemini API
try:
    from google import genai
    from google.genai import types
    from pydantic import BaseModel

    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI SDK not installed. Will save prompts only.")
    GEMINI_AVAILABLE = False


# Define Pydantic models for the evaluation response structure
class CoverageEvaluation(BaseModel):
    coverage_type: str
    name: str
    result: str
    justification: str
    customer_quote: str
    agent_performance: str
    agent_performance_justification: str
    agent_quote: str


class EvaluationSummary(BaseModel):
    total_requirements: int
    requirements_met: int
    overall_assessment: str


class TranscriptEvaluation(BaseModel):
    evaluations: List[CoverageEvaluation]
    summary: EvaluationSummary


def check_gemini_availability() -> bool:
    """
    Check if the Google Gemini API is available.

    Returns:
        bool: True if Gemini is available, False otherwise
    """
    return GEMINI_AVAILABLE


def initialize_gemini_client(api_key: Optional[str] = None) -> Any:
    """
    Initialize the Google Gemini client.

    Args:
        api_key (str, optional): The API key to use. If not provided, it will be loaded from environment variables.

    Returns:
        Any: The initialized Gemini client

    Raises:
        ValueError: If the API key is not set
        ImportError: If the Gemini SDK is not installed
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("Google Generative AI SDK not installed.")

    # Get API key from environment if not provided
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set.")

    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)
    return client


def generate_gemini_evaluation(
    prompt: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an evaluation using Google Gemini with schema-based JSON response.

    Args:
        prompt (str): The prompt to send to Gemini
        api_key (str, optional): The API key to use. If not provided, it will be loaded from environment variables.

    Returns:
        dict: The evaluation results as a dictionary

    Raises:
        ImportError: If the Gemini SDK is not installed
        ValueError: If the API key is not set
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("Google Generative AI SDK not installed.")

    # Initialize the client
    client = initialize_gemini_client(api_key)

    # Set up the model name
    model = "gemini-2.0-flash"  # Using flash model which is available

    # Try to generate content with retries
    retry_count = 3
    retry_delay = 1.0

    for attempt in range(retry_count):
        try:
            # Generate content using the client with schema
            response = client.models.generate_content(
                model=model,
                contents=[prompt],
                config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json",
                    "response_schema": TranscriptEvaluation,
                },
            )

            # Use the parsed response directly
            if hasattr(response, "parsed"):
                return response.parsed.dict()
            else:
                # Fallback to manual JSON parsing if parsed attribute is not available
                logger.warning(
                    "Parsed attribute not available, falling back to manual JSON parsing"
                )
                return json.loads(response.text)

        except Exception as e:
            if attempt < retry_count - 1:
                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{retry_count}): {str(e)}. Retrying in {retry_delay} seconds..."
                )
                time.sleep(retry_delay)
                # Increase delay for next retry (exponential backoff)
                retry_delay *= 2
            else:
                logger.error(f"API call failed after {retry_count} attempts: {str(e)}")
                raise
