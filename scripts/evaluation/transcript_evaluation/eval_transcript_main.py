"""
Transcript Evaluation Script

This script evaluates conversation transcripts to determine if a customer service agent
successfully gathered all required travel insurance coverage information from a customer.

It uses the Google Gemini LLM to analyze transcripts and provide structured evaluations
based on standardized coverage requirements.

Usage:
    # Evaluate a single JSON transcript
    python scripts/evaluation/eval_transcript_main.py --transcript data/transcripts/raw/synthetic/transcript_example_timestamp.json

    # Evaluate all JSON transcripts in a directory
    python scripts/evaluation/eval_transcript_main.py --directory data/transcripts/raw/synthetic/

    # Specify output format and location
    python scripts/evaluation/eval_transcript_main.py --transcript data/transcripts/raw/synthetic/transcript_example_timestamp.json --output-dir custom/output/path --format json,txt
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional

# Add the project root to the Python path to allow imports
# Go up three levels from the current script directory (transcript_evaluation -> evaluation -> scripts -> project_root)
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # Insert at the beginning for priority

# Import coverage requirements directly
from data.coverage_requirements.coverage_requirements import get_coverage_requirements

# Import modules from the evaluation package (using absolute paths from project root)
from scripts.evaluation.transcript_evaluation.eval_transcript_prompts import (
    construct_evaluation_prompt,
)
from scripts.evaluation.transcript_evaluation.eval_transcript_parser import (
    parse_transcript,
    find_transcript_files,
)
from scripts.evaluation.transcript_evaluation.eval_transcript_results import (
    format_evaluation_results,
    save_evaluation_results,
    create_summary_csv,
    save_prompt_for_manual_evaluation,
)
from scripts.evaluation.transcript_evaluation.eval_transcript_gemini import (
    check_gemini_availability,
    generate_gemini_evaluation,
)
from scripts.evaluation.transcript_evaluation.eval_transcript_utils import (
    ensure_output_directory,
    get_transcript_name,
    setup_logging,
    load_environment_variables,
    print_evaluation_instructions,
)

# Configure logging
logger = logging.getLogger(__name__)


def load_scenario_requirements(scenario_name: str) -> Optional[List[str]]:
    """
    Load additional requirements from a scenario file.

    Args:
        scenario_name (str): Name of the scenario

    Returns:
        list: List of additional requirement strings, or None if loading fails
    """
    if not scenario_name:
        return None

    # Construct the path to the scenario file
    scenario_path = os.path.join(
        project_root, "data", "scenarios", f"{scenario_name}.json"
    )

    try:
        with open(scenario_path, "r", encoding="utf-8") as file:
            scenario_data = json.load(file)

        # Extract the additional requirements
        additional_requirements = scenario_data.get("additional_requirements", [])
        if additional_requirements:
            logger.info(
                f"Loaded {len(additional_requirements)} additional requirements from scenario: {scenario_name}"
            )
            return additional_requirements
        else:
            logger.warning(
                f"No additional requirements found in scenario: {scenario_name}"
            )
            return []

    except FileNotFoundError:
        logger.error(f"Scenario file not found: {scenario_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from scenario file: {scenario_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading scenario requirements: {str(e)}")
        return None


def process_single_transcript(
    transcript_path: str,
    output_dir: str,
    formats: List[str],
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Process a single transcript file.

    Args:
        transcript_path (str): Path to the transcript file
        output_dir (str): Directory to save evaluation results
        formats (list): Output formats to save
        api_key (str, optional): The API key to use

    Returns:
        dict: The evaluation results, or None if processing failed
    """
    logger.info(f"Processing transcript: {transcript_path}")

    # Parse the transcript and extract scenario name
    transcript, scenario_name = parse_transcript(transcript_path)
    if not transcript:
        logger.error(f"Failed to parse transcript: {transcript_path}")
        return None

    # Get standard coverage requirements
    coverage_requirements = get_coverage_requirements()

    # Load scenario-specific requirements if a scenario was used
    scenario_requirements = None
    if scenario_name:
        logger.info(f"Transcript uses scenario: {scenario_name}")
        scenario_requirements = load_scenario_requirements(scenario_name)

    # Construct the prompt with scenario information if available
    prompt = construct_evaluation_prompt(
        transcript, coverage_requirements, scenario_name, scenario_requirements
    )

    # Get transcript name
    transcript_name = get_transcript_name(transcript_path)

    # Generate evaluation if Gemini is available
    if check_gemini_availability():
        try:
            # API key is now handled internally by LLMService
            evaluation = generate_gemini_evaluation(prompt)

            # Add transcript name and scenario to the evaluation
            evaluation["transcript_name"] = transcript_name
            if scenario_name:
                evaluation["scenario"] = scenario_name

            # Save evaluation results
            save_evaluation_results(evaluation, transcript_name, output_dir, formats)

            # Display evaluation results
            print("\nEvaluation Results:")
            print(format_evaluation_results(evaluation))

            return evaluation

        except Exception as e:
            logger.error(f"Error generating evaluation: {str(e)}")

            # Save the prompt for manual evaluation
            prompt_path = save_prompt_for_manual_evaluation(
                prompt, transcript_name, output_dir
            )

            print(f"Saved prompt to: {prompt_path}")
            print_evaluation_instructions()
            return None
    else:
        # Save the prompt for manual evaluation
        prompt_path = save_prompt_for_manual_evaluation(
            prompt, transcript_name, output_dir
        )

        print(f"Saved prompt to: {prompt_path}")
        print_evaluation_instructions()
        return None


def process_directory(
    directory_path: str,
    output_dir: str,
    formats: List[str],
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Process all transcript files in a directory.

    Args:
        directory_path (str): Path to directory containing transcript files
        output_dir (str): Directory to save evaluation results
        formats (list): Output formats to save
        api_key (str, optional): The API key to use

    Returns:
        list: List of evaluation results
    """
    results = []

    # Find all transcript files
    transcript_files = find_transcript_files(directory_path)

    if not transcript_files:
        logger.warning(f"No transcript files found in {directory_path}")
        return results

    logger.info(f"Found {len(transcript_files)} transcript files to evaluate")

    # Process each transcript
    for transcript_path in transcript_files:
        try:
            evaluation = process_single_transcript(
                transcript_path, output_dir, formats, api_key
            )
            if evaluation:
                results.append(evaluation)
        except Exception as e:
            logger.error(f"Error processing {transcript_path}: {str(e)}")

    # Generate and save summary if we have results
    if results and "csv" in formats:
        create_summary_csv(results, output_dir)

    return results


def main():
    """Main execution function."""
    # Set up logging
    setup_logging()

    # Load environment variables
    load_environment_variables()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Evaluate transcripts for coverage requirement gathering"
    )
    parser.add_argument("--transcript", help="Path to a single transcript JSON file")
    parser.add_argument(
        "--directory", help="Path to a directory of transcript JSON files"
    )
    parser.add_argument(
        "--output-dir",
        default="data/evaluation/transcript_evaluations",
        help="Directory to save evaluation results",
    )
    parser.add_argument(
        "--format",
        default="json",
        help="Output formats (comma-separated: json,txt,csv)",
    )
    parser.add_argument(
        "--api-key",
        help="Google Gemini API key (if not set in environment variables)",
    )

    args = parser.parse_args()

    # Create output directory
    ensure_output_directory(args.output_dir)

    # Parse formats
    formats = args.format.split(",")

    # Process transcript(s)
    if args.transcript:
        # Process single transcript - designed for orchestrator use
        # Exit with non-zero status on failure for the orchestrator to detect
        logger.info(f"Processing single transcript: {args.transcript}")
        evaluation_result = process_single_transcript(
            args.transcript, args.output_dir, formats, args.api_key
        )
        if evaluation_result is None:
            logger.error(f"Failed to process transcript: {args.transcript}")
            sys.exit(1)  # Exit with error code 1 on failure
        else:
            logger.info(f"Successfully processed transcript: {args.transcript}")
            sys.exit(0)  # Exit with success code 0

    elif args.directory:
        # Process directory of transcripts - for standalone use
        logger.info(f"Processing directory: {args.directory}")
        results = process_directory(
            args.directory, args.output_dir, formats, args.api_key
        )
        logger.info(f"Processed {len(results)} transcripts from directory.")
        # For directory processing, don't exit based on individual failures,
        # as it's intended to process as many as possible.
        sys.exit(0)  # Exit successfully after processing directory

    else:
        # No transcript or directory specified
        parser.print_help()
        sys.exit(1)  # Exit with error code if no valid arguments


if __name__ == "__main__":
    main()
