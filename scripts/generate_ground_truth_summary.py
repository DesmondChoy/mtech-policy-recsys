#!/usr/bin/env python3
"""
Ground Truth Coverage Summary Generator
=======================================

This script generates a Markdown summary report (`.md`) from existing ground truth evaluation
JSON data (`coverage_evaluation_summary.json`) without re-running the evaluations.

**Note:** The main evaluation script (`generate_ground_truth_coverage.py`) also generates
this Markdown summary as its final step. This script (`generate_ground_truth_summary.py`)
is primarily useful if you need to *regenerate* the Markdown summary from existing JSON
data without re-running the full evaluation process.

Usage:
    python scripts/generate_ground_truth_summary.py [--input_file PATH]

Arguments:
    --input_file: Path to the coverage_evaluation_summary.json file
                 Default: data/evaluation/ground_truth_evaluation/coverage_evaluation_summary.json
"""

import os
import json
import argparse
from pathlib import Path


def generate_markdown_summary(json_path, output_path=None):
    """
    Generate a Markdown summary from existing ground truth evaluation JSON data.

    Args:
        json_path (str or Path): Path to the coverage_evaluation_summary.json file
        output_path (str or Path, optional): Path to save the output Markdown file.
            If not provided, saves in the same directory as the JSON file.

    Returns:
        Path: Path to the generated Markdown file
    """
    # Load the JSON data
    with open(json_path, "r") as f:
        data = json.load(f)

    if "summary" not in data:
        raise ValueError("Invalid summary JSON file. Missing 'summary' key.")

    summary_data = data["summary"]
    overall_stats = summary_data["overall_stats"]
    evaluations = summary_data["evaluations"]

    # Determine output path if not provided
    if not output_path:
        output_path = os.path.join(
            os.path.dirname(json_path), "coverage_evaluation_summary.md"
        )

    # Create a dictionary to track failing customers
    failing_customers = {}
    for customer_id, evaluation in evaluations.items():
        if evaluation["valid_coverage_percentage"] < 100:
            failing_customers[customer_id] = {
                "valid_coverage_percentage": evaluation["valid_coverage_percentage"],
                "not_covered_requirements": evaluation["status_summary"][
                    "not_covered_requirements"
                ],
            }

    # Group failing customers by valid coverage percentage bands
    failing_bands = {
        "90-99%": [],
        "80-89%": [],
        "70-79%": [],
        "60-69%": [],
        "50-59%": [],
        "<50%": [],
    }

    for customer_id, data in failing_customers.items():
        coverage = data["valid_coverage_percentage"]
        if coverage >= 90:
            failing_bands["90-99%"].append(customer_id)
        elif coverage >= 80:
            failing_bands["80-89%"].append(customer_id)
        elif coverage >= 70:
            failing_bands["70-79%"].append(customer_id)
        elif coverage >= 60:
            failing_bands["60-69%"].append(customer_id)
        elif coverage >= 50:
            failing_bands["50-59%"].append(customer_id)
        else:
            failing_bands["<50%"].append(customer_id)

    # Write the Markdown file
    with open(output_path, "w") as f:
        f.write("# Ground Truth Coverage Evaluation Results\n\n")

        # Overview explanation of Total vs Valid Coverage
        f.write("## Coverage Metrics Explained\n\n")
        f.write("This report uses two types of coverage metrics:\n\n")
        f.write(
            "- **Total Coverage**: Percentage of ALL requirements covered by recommended policies\n"
        )
        f.write(
            "- **Valid Coverage**: Percentage of only VALID requirements covered (excluding requirements that don't exist in any policy)\n\n"
        )
        f.write(
            "Unless otherwise specified, **Valid Coverage** is the primary metric used throughout this report.\n\n"
        )

        # Overall statistics section
        f.write("## Overall Statistics\n\n")
        f.write(f"- Total Customers: {overall_stats['total_customers']}\n")
        f.write(f"- Total Requirements (all): {overall_stats['total_requirements']}\n")
        f.write(
            f"- Valid Requirements (excluding non-existent): {overall_stats['total_valid_requirements']}\n"
        )
        f.write(
            f"- Covered Requirements: {overall_stats['total_covered_requirements']}\n"
        )
        f.write(
            f"- **Total Coverage Rate**: {overall_stats['overall_total_coverage_percentage']}%\n"
        )
        f.write(
            f"- **Valid Coverage Rate**: {overall_stats['overall_valid_coverage_percentage']}%\n"
        )
        f.write(
            f"- Customers with 100% Valid Coverage: {overall_stats['perfect_coverage_count']} ({overall_stats['perfect_coverage_percentage']}%)\n\n"
        )

        # Coverage bands section - using Valid Coverage
        f.write("## Valid Coverage Breakdown\n\n")
        f.write(
            "Distribution of customers by valid coverage percentage (excluding non-existent requirements):\n\n"
        )
        f.write("| Valid Coverage Band | Number of Customers | Percentage |\n")
        f.write("|----------------------|---------------------|------------|\n")

        # Perfect coverage (100%)
        perfect_count = overall_stats["perfect_coverage_count"]
        perfect_percent = (
            round((perfect_count / overall_stats["total_customers"]) * 100, 2)
            if overall_stats["total_customers"] > 0
            else 0
        )
        f.write(f"| 100% | {perfect_count} | {perfect_percent}% |\n")

        # Failing bands
        for band, customers in failing_bands.items():
            count = len(customers)
            percent = (
                round((count / overall_stats["total_customers"]) * 100, 2)
                if overall_stats["total_customers"] > 0
                else 0
            )
            f.write(f"| {band} | {count} | {percent}% |\n")

        # Failing customers details - using Valid Coverage
        f.write("\n## Customers With Incomplete Valid Coverage\n\n")
        f.write(
            "Details of customers with less than 100% valid coverage (excluding non-existent requirements):\n\n"
        )

        for band, customers in failing_bands.items():
            if customers:
                f.write(f"### {band} Valid Coverage\n\n")
                for customer_id in sorted(customers):
                    f.write(f"#### Customer: {customer_id}\n")
                    f.write(
                        f"- Valid Coverage Rate: {failing_customers[customer_id]['valid_coverage_percentage']}%\n"
                    )
                    f.write("- Uncovered Requirements:\n")
                    for req in failing_customers[customer_id][
                        "not_covered_requirements"
                    ]:
                        f.write(f"  - {req}\n")
                    f.write("\n")

        # Requirements statistics
        f.write("## Requirements Statistics\n\n")
        f.write(
            f"- Non-existent Requirements (not found in any policy): {overall_stats['total_not_exist_requirements']}\n"
        )
        f.write(
            f"- Customers with Non-existent Requirements: {overall_stats['customers_with_invalid_requirements']}\n"
        )

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate Markdown summary from ground truth evaluation JSON"
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="data/evaluation/ground_truth_evaluation/coverage_evaluation_summary.json",
        help="Path to the coverage_evaluation_summary.json file",
    )
    args = parser.parse_args()

    # Generate the summary
    output_path = generate_markdown_summary(args.input_file)

    print(f"Markdown summary generated at: {output_path}")


if __name__ == "__main__":
    main()
