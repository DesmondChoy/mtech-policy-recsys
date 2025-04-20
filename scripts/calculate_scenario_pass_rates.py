"""
Scenario Evaluation Pass Rate Calculator
========================================

This script analyzes the evaluation results from scenario testing JSON files and calculates
pass rates for each scenario. It processes all JSON files with 'all_transcripts' in their names
from the 'data/evaluation/scenario_evaluation/' directory.

Purpose:
--------
- Find all JSON files containing 'all_transcripts' in their names
- Calculate the pass rate for each scenario (passes / total cases)
- Generate a Markdown report with the results
- Save the report to 'data/evaluation/scenario_evaluation/scenario_evaluation_results.md'

A "pass" is defined as either "PASS" or "PASS (Partial Cover)", while a "fail" is either
"FAIL" or "FAIL (Partial)".

Usage:
------
Run this script from the project root directory:

    python scripts/calculate_scenario_pass_rates.py

Output:
-------
The script generates a Markdown file with sections for each scenario, showing:
- Number of passes
- Total number of cases
- Pass rate (formatted as a percentage)

The output is saved to: data/evaluation/scenario_evaluation/scenario_evaluation_results.md
"""

import os
import json
import glob
from typing import Dict, List, Tuple


def find_all_transcript_files(directory: str) -> List[str]:
    """Find all JSON files with 'all_transcripts' in their names."""
    pattern = os.path.join(directory, "*all_transcripts*.json")
    return glob.glob(pattern)


def calculate_pass_rate(data: List[Dict]) -> Tuple[int, int, float]:
    """
    Calculate the pass rate from evaluation results.

    Returns:
        Tuple containing (passes, total, pass_rate)
    """
    total_cases = len(data)
    passes = sum(1 for item in data if "PASS" in item.get("evaluation_result", ""))
    pass_rate = passes / total_cases if total_cases > 0 else 0
    return passes, total_cases, pass_rate


def collect_failing_uuids(data: List[Dict]) -> List[str]:
    """Collect UUIDs of failing cases."""
    failing_uuids = []
    for item in data:
        # Check if the evaluation result indicates a failure
        if "FAIL" in item.get("evaluation_result", ""):
            failing_uuids.append(item.get("uuid", "Unknown"))
    return failing_uuids


def extract_scenario_name(filename: str) -> str:
    """Extract the scenario name from the filename."""
    # Example: results_golf_coverage_all_transcripts_20250420_143545.json
    # We want to extract "golf_coverage"
    base_name = os.path.basename(filename)
    parts = base_name.split("_")
    # Find the index of 'all' and take the parts before it, excluding 'results'
    try:
        all_index = parts.index("all")
        scenario_parts = parts[1:all_index]
        return "_".join(scenario_parts)
    except ValueError:
        # Fallback if 'all' is not found (shouldn't happen based on file pattern)
        return "_".join(parts[1:-2])  # Guess based on original logic


def main():
    directory = "data/evaluation/scenario_evaluation/"
    transcript_files = find_all_transcript_files(directory)

    # Create a markdown string for the results
    markdown = "# Scenario Evaluation Results\n\n"

    # Sort files by scenario name for consistency
    transcript_files.sort(key=extract_scenario_name)

    for file_path in transcript_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:  # Specify encoding
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            continue  # Skip this file
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            continue  # Skip this file

        if not data:  # Check if data is empty
            print(f"Warning: No data found in {file_path}")
            continue  # Skip this file

        scenario_name = extract_scenario_name(file_path)
        passes, total, pass_rate = calculate_pass_rate(data)
        failing_uuids = collect_failing_uuids(data)

        # Add scenario results to markdown
        markdown += f"## {scenario_name}\n\n"
        markdown += f"- Passes: {passes}\n"
        markdown += f"- Total Cases: {total}\n"
        markdown += f"- Pass Rate: {pass_rate:.2%}\n"

        # Add failing UUIDs if any
        if failing_uuids:
            markdown += "\n### Failing Customer IDs:\n"
            for uuid in failing_uuids:
                markdown += f"- {uuid}\n"
        markdown += "\n"

    # Write the markdown to a file in the specified directory
    output_file = "data/evaluation/scenario_evaluation/scenario_evaluation_results.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:  # Specify encoding
            f.write(markdown)
        print(f"Results written to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}")


if __name__ == "__main__":
    main()
