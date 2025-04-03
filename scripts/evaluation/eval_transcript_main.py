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
import argparse
import logging
from typing import Dict, List, Any, Optional

# Add the project root to the Python path to allow imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

# Import coverage requirements directly
from data.coverage_requirements.coverage_requirements import get_coverage_requirements

# Import modules from the evaluation package
from scripts.evaluation.prompts.eval_transcript_prompts import (
    construct_evaluation_prompt,
)
from scripts.evaluation.processors.eval_transcript_parser import (
    parse_transcript,
    find_transcript_files,
)
from scripts.evaluation.processors.eval_transcript_results import (
    format_evaluation_results,
    save_evaluation_results,
    create_summary_csv,
    save_prompt_for_manual_evaluation,
)
from scripts.evaluation.evaluators.eval_transcript_gemini import (
    check_gemini_availability,
    generate_gemini_evaluation,
)
from scripts.evaluation.utils.eval_transcript_utils import (
    ensure_output_directory,
    get_transcript_name,
    setup_logging,
    load_environment_variables,
    print_evaluation_instructions,
)

# Configure logging
logger = logging.getLogger(__name__)


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

    # Parse the transcript
    transcript = parse_transcript(transcript_path)
    if not transcript:
        logger.error(f"Failed to parse transcript: {transcript_path}")
        return None

    # Get coverage requirements
    coverage_requirements = get_coverage_requirements()

    # Construct the prompt
    prompt = construct_evaluation_prompt(transcript, coverage_requirements)

    # Get transcript name
    transcript_name = get_transcript_name(transcript_path)

    # Generate evaluation if Gemini is available
    if check_gemini_availability():
        try:
            evaluation = generate_gemini_evaluation(prompt, api_key)

            # Add transcript name to the evaluation
            evaluation["transcript_name"] = transcript_name

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
        default="json,txt",
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
        # Process single transcript
        process_single_transcript(
            args.transcript, args.output_dir, formats, args.api_key
        )
    elif args.directory:
        # Process directory of transcripts
        results = process_directory(
            args.directory, args.output_dir, formats, args.api_key
        )
        logger.info(f"Processed {len(results)} transcripts")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
