"""
Transcript Evaluation Script (Legacy)

This script is maintained for backward compatibility.
Please use eval_transcript_main.py for new development.

This script evaluates conversation transcripts to determine if a customer service agent
successfully gathered all required travel insurance coverage information from a customer.

Usage:
    # Evaluate a single transcript
    python scripts/evaluation/evaluate_transcripts.py --transcript data/transcripts/synthetic/transcript_01.txt

    # Evaluate all transcripts in a directory
    python scripts/evaluation/evaluate_transcripts.py --directory data/transcripts/synthetic/

    # Specify output format and location
    python scripts/evaluation/evaluate_transcripts.py --transcript transcript_01.txt --output-dir custom/output/path --format json,txt
"""

import sys
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the main function from the refactored module
try:
    from scripts.evaluation.eval_transcript_main import (
        process_single_transcript,
        process_directory,
        ensure_output_directory,
    )

    REFACTORED_AVAILABLE = True
except ImportError:
    logger.error("Refactored modules not found. Please check your installation.")
    REFACTORED_AVAILABLE = False


def main():
    """Main execution function."""
    if not REFACTORED_AVAILABLE:
        logger.error("Cannot continue without refactored modules.")
        return

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Evaluate transcripts for coverage requirement gathering"
    )
    parser.add_argument("--transcript", help="Path to a single transcript file")
    parser.add_argument("--directory", help="Path to a directory of transcript files")
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

    # Print deprecation warning
    logger.warning(
        "This script is deprecated. Please use eval_transcript_main.py for new development."
    )

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
