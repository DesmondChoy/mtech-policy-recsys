"""
Gemini-based evaluator for transcript evaluation.

This module contains functions for evaluating transcripts using Google Gemini via LLMService.
"""

# import os # No longer needed directly
# import time # No longer needed directly
import json
import logging
import os  # Added for path manipulation
import sys  # Added for path manipulation
import re  # Added for regex-based JSON fixing
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# --- Add project root to sys.path ---
# Assumes the script is run from the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up three levels: evaluators -> evaluation -> scripts -> project_root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import Pydantic and LLMService
from pydantic import BaseModel, ValidationError
from src.models.llm_service import LLMService  # Import LLMService


# Define Pydantic models for the evaluation response structure
# (Keep these as they are used for validation)
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


def check_gemini_availability():
    """
    Check if the Google Gemini API is available via LLMService.

    Returns:
        bool: True if LLMService can be imported, False otherwise
    """
    try:
        # We've already imported LLMService at the top of the file
        # Just check if it's accessible
        return True
    except Exception as e:
        logger.error(f"Error checking Gemini availability: {e}")
        return False


def generate_gemini_evaluation(prompt: str) -> Dict[str, Any]:
    """
    Generate an evaluation using Google Gemini via LLMService.

    Args:
        prompt (str): The prompt to send to Gemini.

    Returns:
        dict: The validated evaluation results as a dictionary.

    Raises:
        Exception: If the LLMService call fails or validation fails.
        ValueError: If the response cannot be parsed or validated.
    """
    try:
        # Instantiate LLM Service (API key handled internally)
        llm_service = LLMService()

        # Call LLM Service to get structured content (JSON)
        # This uses deterministic parameters by default
        logger.info("Calling LLM Service for transcript evaluation...")

        # The updated generate_structured_content method now handles:
        # - Markdown code blocks
        # - JSON formatting issues
        result_dict = llm_service.generate_structured_content(prompt=prompt)

        # Validate the received dictionary against the Pydantic model
        try:
            validated_data = TranscriptEvaluation(**result_dict)
            logger.info("LLM response successfully validated against schema.")
            # Return the validated data as a dictionary
            return validated_data.model_dump()
        except ValidationError as e:
            logger.error(f"LLM response validation failed: {e}")
            logger.debug(f"Invalid data received: {result_dict}")
            raise ValueError(f"LLM response validation failed: {e}")
        except Exception as e:  # Catch other potential errors during validation/dumping
            logger.error(f"Error processing LLM response after validation: {e}")
            raise ValueError(f"Error processing LLM response: {e}")

    except Exception as e:
        # Log errors from LLMService call (e.g., API errors after retries)
        logger.error(f"LLM Service call failed during evaluation generation: {e}")
        # Re-raise the exception to be handled by the calling script
        raise
