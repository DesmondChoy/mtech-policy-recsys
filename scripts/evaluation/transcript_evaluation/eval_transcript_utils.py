"""
Utilities for transcript evaluation.

This module contains utility functions for file operations and other helper functions.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


def ensure_output_directory(output_dir: str) -> None:
    """
    Ensure that the output directory exists.

    Args:
        output_dir (str): Path to the output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")


def get_transcript_name(transcript_path: str) -> str:
    """
    Get the transcript name from the file path.

    Args:
        transcript_path (str): Path to the transcript file

    Returns:
        str: Transcript name without extension
    """
    return os.path.basename(transcript_path).split(".")[0]


def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up logging configuration.

    Args:
        level (int): Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Logging configured")


def load_environment_variables() -> None:
    """
    Load environment variables from .env file.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning(
            "dotenv not installed. Environment variables must be set manually."
        )


def print_evaluation_instructions() -> None:
    """
    Print instructions for manual evaluation.
    """
    print("\nTo evaluate this transcript:")
    print("1. Copy the prompt from the saved file")
    print("2. Submit it to Google Gemini or another LLM")
    print("3. Save the JSON response for analysis")
