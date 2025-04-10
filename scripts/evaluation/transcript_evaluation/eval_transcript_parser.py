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


def parse_transcript(
    file_path: str,
) -> tuple[Optional[List[Dict[str, str]]], Optional[str]]:
    """
    Parse a JSON transcript file into a list of speaker-dialogue pairs and extract scenario name.
    Assumes the JSON file has a top-level key "transcript" containing the list and may have a "scenario" key.

    Args:
        file_path (str): Path to the transcript JSON file

    Returns:
        tuple: (conversation_list, scenario_name) where:
            - conversation_list is a list of dictionaries containing speaker and dialogue, or None if parsing fails
            - scenario_name is a string with the scenario name or None if no scenario was used
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Extract the conversation list from the "transcript" key
        conversation = data.get("transcript")

        # Extract the scenario name (if present)
        scenario_name = data.get(
            "scenario"
        )  # Will be None if key doesn't exist or value is null

        if conversation is None:
            logger.error(f"Error: 'transcript' key not found in JSON file: {file_path}")
            return None, scenario_name
        if not isinstance(conversation, list):
            logger.error(
                f"Error: 'transcript' value is not a list in JSON file: {file_path}"
            )
            return None, scenario_name

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
                # return None, scenario_name # Uncomment to make it an error

        return conversation, scenario_name

    except FileNotFoundError:
        logger.error(f"Error: Could not find the file at {file_path}")
        return None, None
    except json.JSONDecodeError:
        logger.error(f"Error: Failed to decode JSON from file: {file_path}")
        return None, None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while parsing transcript {file_path}: {str(e)}"
        )
        return None, None


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
