"""
Results processor for transcript evaluation.

This module contains functions for formatting and saving evaluation results.
"""

import os
import json
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def format_evaluation_results(
    evaluation: Dict[str, Any], format_type: str = "text"
) -> str:
    """
    Format evaluation results for display.

    Args:
        evaluation (dict): Evaluation results
        format_type (str): Output format type (text, json)

    Returns:
        str: Formatted evaluation results

    Raises:
        ValueError: If the format type is not supported
    """
    if format_type == "json":
        return json.dumps(evaluation, indent=2)

    elif format_type == "text":
        lines = []
        lines.append("TRANSCRIPT EVALUATION")
        lines.append(f"Evaluated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        for eval_item in evaluation["evaluations"]:
            lines.append(f"COVERAGE: {eval_item['name']}")
            lines.append(f"RESULT: {eval_item['result']}")
            lines.append(f"JUSTIFICATION: {eval_item['justification']}")
            if "customer_quote" in eval_item:
                lines.append(f'CUSTOMER QUOTE: "{eval_item["customer_quote"]}"')
            lines.append(f"AGENT PERFORMANCE: {eval_item['agent_performance']}")
            lines.append(
                f"AGENT JUSTIFICATION: {eval_item['agent_performance_justification']}"
            )
            if "agent_quote" in eval_item:
                lines.append(f'AGENT QUOTE: "{eval_item["agent_quote"]}"')
            lines.append("")

        lines.append("SUMMARY:")
        lines.append(
            f"Requirements Met: {evaluation['summary']['requirements_met']}/{evaluation['summary']['total_requirements']}"
        )
        lines.append(
            f"Overall Assessment: {evaluation['summary']['overall_assessment']}"
        )

        return "\n".join(lines)

    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def save_evaluation_results(
    evaluation: Dict[str, Any],
    transcript_name: str,
    output_dir: str,
    formats: List[str] = ["json", "txt"],
) -> None:
    """
    Save evaluation results to specified formats.

    Args:
        evaluation (dict): Evaluation results
        transcript_name (str): Name of the transcript file (without extension)
        output_dir (str): Directory to save results
        formats (list): Output formats to save
    """
    os.makedirs(output_dir, exist_ok=True)

    for fmt in formats:
        # Construct the new base filename by replacing the first 'transcript_' with 'transcript_eval_'
        new_base_name = transcript_name.replace("transcript_", "transcript_eval_", 1)

        if fmt == "json":
            output_path = os.path.join(output_dir, f"{new_base_name}.json")
            # Ensure ensure_ascii=True (default) for standard JSON escaping
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(evaluation, f, indent=2, ensure_ascii=True)
            logger.info(f"Saved JSON evaluation to: {output_path}")

        elif fmt == "txt":
            output_path = os.path.join(output_dir, f"{new_base_name}.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(format_evaluation_results(evaluation, "text"))
            logger.info(f"Saved text evaluation to: {output_path}")

        elif fmt == "csv":
            # Only create CSV for batch processing
            pass

        else:
            logger.warning(f"Unsupported format: {fmt}")


def create_summary_csv(results: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Create a CSV summary of multiple transcript evaluations.

    Args:
        results (list): List of evaluation results
        output_dir (str): Directory to save the CSV
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_path = os.path.join(output_dir, f"summary_{timestamp}.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "transcript",
            "total_requirements",
            "requirements_met",
            "pass_rate",
        ]

        # Add each coverage type
        if results and "evaluations" in results[0]:
            for eval_item in results[0]["evaluations"]:
                fieldnames.append(f"{eval_item['coverage_type']}_result")

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            row = {
                "transcript": result.get("transcript_name", "Unknown"),
                "total_requirements": result["summary"]["total_requirements"],
                "requirements_met": result["summary"]["requirements_met"],
                "pass_rate": f"{(result['summary']['requirements_met'] / result['summary']['total_requirements']) * 100:.1f}%",
            }

            # Add results for each coverage type
            for eval_item in result["evaluations"]:
                row[f"{eval_item['coverage_type']}_result"] = eval_item["result"]

            writer.writerow(row)

    logger.info(f"Saved CSV summary to: {csv_path}")


def save_prompt_for_manual_evaluation(
    prompt: str, transcript_name: str, output_dir: str
) -> None:
    """
    Save a prompt for manual evaluation when automated evaluation fails.

    Args:
        prompt (str): The evaluation prompt
        transcript_name (str): Name of the transcript file (without extension)
        output_dir (str): Directory to save the prompt
    """
    os.makedirs(output_dir, exist_ok=True)
    prompt_path = os.path.join(output_dir, f"{transcript_name}_prompt.txt")

    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    logger.info(f"Saved prompt to: {prompt_path} for manual evaluation")
    return prompt_path
