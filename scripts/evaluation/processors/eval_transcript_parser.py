"""
Transcript parser for evaluation.

This module contains functions for parsing and processing conversation transcripts.
"""

import re
import json  # Added import
import logging
from typing import List, Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)


def parse_transcript(file_path: str) -> Optional[List[Dict[str, str]]]:
    """
    Parse a JSON transcript file into a list of speaker-dialogue pairs.
    Assumes the JSON file has a top-level key "transcript" containing the list.

    Args:
        file_path (str): Path to the transcript JSON file

    Returns:
        list: List of dictionaries containing speaker and dialogue, or None if parsing fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Assuming the conversation list is under the key "transcript"
        # based on generate_transcripts.py context
        conversation = data.get("transcript")

        if conversation is None:
            logger.error(f"Error: 'transcript' key not found in JSON file: {file_path}")
            return None
        if not isinstance(conversation, list):
            logger.error(
                f"Error: 'transcript' value is not a list in JSON file: {file_path}"
            )
            return None

        # Basic validation of list items (optional but good practice)
        for i, item in enumerate(conversation):
            if (
                not isinstance(item, dict)
                or "speaker" not in item
                or "dialogue" not in item
            ):
                logger.warning(
                    f"Invalid item format at index {i} in {file_path}: {item}"
                )
                # Decide if this should be an error or just a warning
                # return None # Uncomment to make it an error

        return conversation

    except FileNotFoundError:
        logger.error(f"Error: Could not find the file at {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error: Failed to decode JSON from file: {file_path}")
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while parsing transcript {file_path}: {str(e)}"
        )
        return None


def validate_transcript(transcript: List[Dict[str, str]]) -> bool:
    """
    Validate a parsed transcript to ensure it has the expected structure.

    Args:
        transcript (list): List of dictionaries containing speaker and dialogue

    Returns:
        bool: True if the transcript is valid, False otherwise
    """
    if not transcript:
        logger.error("Transcript is empty")
        return False

    for i, entry in enumerate(transcript):
        if "speaker" not in entry or "dialogue" not in entry:
            logger.error(f"Invalid transcript entry at index {i}: {entry}")
            return False

        if not entry["speaker"] or not entry["dialogue"]:
            logger.warning(f"Empty speaker or dialogue at index {i}: {entry}")

    return True


def find_transcript_files(directory_path: str) -> List[str]:
    """
    Find all JSON transcript files in a directory.

    Args:
        directory_path (str): Path to the directory to search

    Returns:
        list: List of paths to JSON transcript files
    """
    import os

    transcript_files = []
    try:
        for file in os.listdir(directory_path):
            # Search for .json files specifically
            if file.endswith(".json") and "transcript" in file.lower():
                transcript_files.append(os.path.join(directory_path, file))
    except FileNotFoundError:
        logger.error(f"Error: Directory not found at {directory_path}")
    except Exception as e:
        logger.error(f"Error listing files in {directory_path}: {str(e)}")

    return transcript_files
