"""
Transcript parser for evaluation.

This module contains functions for parsing and processing conversation transcripts.
"""

import re
import logging
from typing import List, Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)


def parse_transcript(file_path: str) -> Optional[List[Dict[str, str]]]:
    """
    Parse a transcript file into a list of speaker-dialogue pairs.

    Args:
        file_path (str): Path to the transcript file

    Returns:
        list: List of dictionaries containing speaker and dialogue, or None if parsing fails
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
        logger.error(f"Error: Could not find the file at {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error occurred while parsing transcript: {str(e)}")
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
    Find all transcript files in a directory.

    Args:
        directory_path (str): Path to the directory to search

    Returns:
        list: List of paths to transcript files
    """
    import os

    transcript_files = []
    for file in os.listdir(directory_path):
        if file.endswith(".txt") and "transcript" in file.lower():
            transcript_files.append(os.path.join(directory_path, file))

    return transcript_files
