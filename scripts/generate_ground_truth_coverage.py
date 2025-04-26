#!/usr/bin/env python3
"""
Ground Truth Coverage Evaluation Script
=======================================

This script evaluates how well recommended insurance policies cover customer requirements by:
1. Reading customer requirements from extracted data files (data/extracted_customer_requirements/requirements_*_<customerID>.json)
2. Finding the recommended policy from recommendation reports (results/<customerID>/recommendation_report_<customerID>.md)
3. Using semantic search to match requirements with ground truth data via the EmbeddingMatcher
4. Evaluating whether each requirement is covered by the recommended policy

Key Features:
1. Compound Requirement Atomization: The script automatically detects and splits compound requirements
   like "Lost or Damaged Luggage" into atomic requirements ("Lost Luggage" and "Damaged Luggage").
   This allows for more accurate evaluation of coverage when a policy might cover part but not all
   of a compound requirement.

2. Activity-Based Enhancement: The script examines the "activities_to_cover" field to intelligently
   add additional requirements based on activities. For example, if a customer lists "golf" in
   their activities, the script adds golf coverage to their requirements.

The script handles requirements that don't exist in any policy (NOT_EXIST) differently from
requirements that exist but aren't covered by the recommended policy (NOT_COVERED).

Two key metrics are calculated:
- Total coverage: Percentage of ALL requirements covered by the recommended policy
- Valid coverage: Percentage of VALID requirements (excluding non-existent ones) covered by the policy

Features:
- Batch processing of all customers
- Detailed breakdown of covered/not covered/non-existent requirements
- Activity-based requirement enhancement (adds requirements based on activities_to_cover field)
- Compound requirement atomization (splits "or"/"and" requirements for more accurate evaluation)
- Summary statistics across all customers
- Individual evaluation files for each customer

Usage:
    python scripts/generate_ground_truth_coverage.py

Output:
    - Individual JSON files for each customer in data/evaluation/ground_truth_evaluation/coverage_evaluation_<customerID>.json
    - Summary JSON file data/evaluation/ground_truth_evaluation/coverage_evaluation_summary.json with statistics across all customers
    - Summary Markdown file data/evaluation/ground_truth_evaluation/coverage_evaluation_summary.md, formatted from the summary JSON.
      (Note: This duplicates the functionality of `generate_ground_truth_summary.py`)
"""

import os
import json
import re
import sys
from pathlib import Path
import glob
import argparse

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.embedding.embedding_utils import EmbeddingMatcher


def extract_recommended_policy(recommendation_file):
    """
    Extract the recommended policy from a recommendation report markdown file.

    Looks for the pattern '**INSURER - PLAN**' in the markdown file to identify
    the recommended policy.

    Args:
        recommendation_file (str or Path): Path to the recommendation report markdown file

    Returns:
        str or None: Formatted policy string (e.g., "GELS - Platinum") or None if not found
    """
    try:
        with open(recommendation_file, "r") as file:
            content = file.read()
            # Look for the pattern: **INSURER - PLAN**
            pattern = r"\*\*([\w\s]+) - ([\w\s]+)\*\*"
            matches = re.search(pattern, content)
            if matches:
                insurer = matches.group(1).strip()
                plan = matches.group(2).strip()
                return f"{insurer} - {plan}"
            return None
    except Exception as e:
        print(f"Error reading recommendation file {recommendation_file}: {e}")
        return None


def get_customer_requirements(requirement_file):
    """
    Extract insurance coverage types from a customer requirements file and enhance with activity-based requirements.

    This function does two important things:
    1. Extracts the explicit "insurance_coverage_type" list from the requirements file
    2. Examines the "activities_to_cover" field to intelligently add additional requirements

    The activity-based enhancement works as follows:
    1. If activities field is empty: No additional requirements added
    2. If activities contains golf: Add "Golf Coverage" if no golf-related requirement exists
    3. If activities contains non-golf activities: Add "Adventurous activities or Amateur sports"
       only if no similar sports/adventure coverage requirement already exists

    This enhancement ensures that customers' activity plans (like golf or hiking) are properly
    factored into coverage requirements, even if not explicitly listed in insurance_coverage_type.

    Args:
        requirement_file (str or Path): Path to the customer requirements JSON file
                                       (data/extracted_customer_requirements/requirements_*_<customerID>.json)

    Returns:
        list: Enhanced list of requirement strings combining explicit requirements and activity-based requirements
    """
    try:
        with open(requirement_file, "r") as file:
            data = json.load(file)
            if "json_dict" not in data:
                return []

            # Get the main insurance coverage types
            requirements = data["json_dict"].get("insurance_coverage_type", [])

            # Check activities_to_cover field
            activities = data["json_dict"].get("activities_to_cover", [])

            # First, identify and standardize any sport/activity specific requirements
            # (except golf-related ones)
            activity_keywords = [
                "hiking",
                "trek",
                "climb",
                "swim",
                "dive",
                "diving",
                "ski",
                "snowboard",
                "adventure",
                "sport",
                "activity",
                "recreation",
                "bungee",
                "balloon",
            ]

            # Track if we need to add adventure sports coverage
            has_adventure_coverage = False

            # Create a new list for the updated requirements
            updated_requirements = []

            # Process each requirement
            for req in requirements:
                req_lower = req.lower()

                # Skip golf-related requirements
                if "golf" in req_lower:
                    updated_requirements.append(req)
                    continue

                # Check if this is an activity/sport related requirement
                is_activity_req = False
                for keyword in activity_keywords:
                    if keyword in req_lower:
                        is_activity_req = True
                        break

                # If it's an activity requirement, replace it with the standard one
                if is_activity_req:
                    # Skip if it's already our standard format
                    if req == "Adventurous activities or Amateur sports":
                        updated_requirements.append(req)
                        has_adventure_coverage = True
                    elif not has_adventure_coverage:
                        updated_requirements.append(
                            "Adventurous activities or Amateur sports"
                        )
                        has_adventure_coverage = True
                else:
                    # Keep non-activity requirements as they are
                    updated_requirements.append(req)

            # Use the updated requirements list going forward
            requirements = updated_requirements

            # Now proceed with the regular activity enhancement
            if activities:
                # Check for golf activities
                has_golf = any("golf" in activity.lower() for activity in activities)
                has_non_golf = any(
                    "golf" not in activity.lower() for activity in activities
                )

                # If there's golf mentioned in activities and no golf requirement
                if has_golf and not any("golf" in req.lower() for req in requirements):
                    requirements.append("Golf Coverage")

                # If there are non-golf activities and no adventure coverage yet
                if has_non_golf and not has_adventure_coverage:
                    # Define keywords that would indicate adventure/sports coverage
                    # Using word boundaries to match whole words only
                    adventure_keywords = [
                        r"\badventur",
                        r"\bsport",
                        r"\bactiv",
                        r"\brecreation",
                    ]

                    # Check if any existing requirement already contains these keywords
                    for req in requirements:
                        req_lower = req.lower()
                        for keyword in adventure_keywords:
                            # Use regex with word boundaries to match whole words only
                            if re.search(keyword, req_lower):
                                has_adventure_coverage = True
                                break
                        if has_adventure_coverage:
                            break

                    # Only add if no similar requirement exists and there are non-golf activities
                    if not has_adventure_coverage:
                        requirements.append("Adventurous activities or Amateur sports")

            return requirements
    except Exception as e:
        print(f"Error reading requirements file {requirement_file}: {e}")
        return []


def atomize_requirements(requirements):
    """
    Split compound requirements into atomic requirements.

    This function looks for conjunctions like 'or', 'and', '/' in requirements
    and splits them into separate requirements when appropriate.

    Examples:
    - "Lost or Damaged Luggage" -> ["Lost Luggage", "Damaged Luggage"]
    - "Baggage Delay and Loss" -> ["Baggage Delay", "Baggage Loss"]
    - "Loss/Damage of Baggage" -> ["Loss of Baggage", "Damage of Baggage"]
    - "Lost, Damaged, Delayed Luggage" -> ["Lost Luggage", "Damaged Luggage", "Delayed Luggage"]
    - "Lost, Damaged, Delayed Baggage" -> ["Lost Baggage", "Damaged Baggage", "Delayed Baggage"]
    - "Lost, Damaged or Delayed Luggage" -> ["Lost Luggage", "Damaged Luggage", "Delayed Luggage"]
    - "Loss, Damage or Delay of Baggage" -> ["Loss of Baggage", "Damage of Baggage", "Delay of Baggage"]

    Args:
        requirements (list): List of requirement strings

    Returns:
        list: Expanded list with compound requirements split into atomic ones
    """
    atomized_requirements = []
    compound_patterns = [
        # Pattern for "Loss, Damage or Delay of Baggage"
        (
            r"(Loss|Damage|Delay|Theft)(?:,\s+)(Loss|Damage|Delay|Theft)(?:\s+or\s+)(Loss|Damage|Delay|Theft)\s+of\s+(Luggage|Baggage)",
            lambda match, req: [
                f"{match.group(1)} of {match.group(4)}",
                f"{match.group(2)} of {match.group(4)}",
                f"{match.group(3)} of {match.group(4)}",
            ],
        ),
        # Pattern for mixed comma and 'or' - "Lost, Damaged or Delayed Luggage"
        (
            r"(Lost|Damaged|Delayed|Stolen)(?:,\s+)(Lost|Damaged|Delayed|Stolen)(?:\s+or\s+)(Lost|Damaged|Delayed|Stolen)(\s+(Luggage|Baggage))",
            lambda match, req: [
                f"{match.group(1)} {match.group(5)}",
                f"{match.group(2)} {match.group(5)}",
                f"{match.group(3)} {match.group(5)}",
            ],
        ),
        # Pattern for comma-separated luggage issues "Lost, Damaged, Delayed Luggage/Baggage"
        (
            r"(Lost|Damaged|Delayed|Stolen)(?:,\s+)(Lost|Damaged|Delayed|Stolen)(?:,\s+)(Lost|Damaged|Delayed|Stolen)(\s+(Luggage|Baggage))",
            lambda match, req: [
                f"{match.group(1)} {match.group(5)}",
                f"{match.group(2)} {match.group(5)}",
                f"{match.group(3)} {match.group(5)}",
            ],
        ),
        # Pattern for comma-separated pair "Lost, Damaged Luggage/Baggage"
        (
            r"(Lost|Damaged|Delayed|Stolen)(?:,\s+)(Lost|Damaged|Delayed|Stolen)(\s+(Luggage|Baggage))",
            lambda match, req: [
                f"{match.group(1)} {match.group(4)}",
                f"{match.group(2)} {match.group(4)}",
            ],
        ),
        # Pattern for "Lost or Damaged Luggage" type compounds
        (
            r"(Lost|loss)\s+or\s+(Damaged|damage)(\s+(Luggage|Baggage))?",
            lambda match, req: [
                f"Lost {match.group(4) or 'Luggage'}"
                if match.group(3)
                else "Lost Luggage",
                f"Damaged {match.group(4) or 'Luggage'}"
                if match.group(3)
                else "Damaged Luggage",
            ],
        ),
        # Pattern for "Baggage Delay and Loss" type compounds
        (
            r"((Baggage|Luggage)\s+(Delay|Loss|Damage|Theft))\s+and\s+(Delay|Loss|Damage|Theft)",
            lambda match, req: [match.group(1), f"{match.group(2)} {match.group(4)}"],
        ),
        # Pattern for "Lost and Delayed Baggage"
        (
            r"(Lost|Delayed|Damaged|Stolen)\s+and\s+(Lost|Delayed|Damaged|Stolen)(\s+(Luggage|Baggage))",
            lambda match, req: [
                f"{match.group(1)} {match.group(4)}",
                f"{match.group(2)} {match.group(4)}",
            ],
        ),
        # Pattern for "Loss or Damage of Baggage"
        (
            r"(Loss|Damage|Delay|Theft)\s+or\s+(Loss|Damage|Delay|Theft)\s+of\s+(Luggage|Baggage)",
            lambda match, req: [
                f"{match.group(1)} of {match.group(3)}",
                f"{match.group(2)} of {match.group(3)}",
            ],
        ),
        # Pattern for "Loss/Damage of Baggage" (with slash)
        (
            r"(Loss|Damage|Delay|Theft)/(Loss|Damage|Delay|Theft)(\s+of\s+|\s+)(Luggage|Baggage|Items|Belongings)",
            lambda match, req: [
                f"{match.group(1)}{match.group(3)}{match.group(4)}",
                f"{match.group(2)}{match.group(3)}{match.group(4)}",
            ],
        ),
        # Pattern for "Theft/Loss" (simple slash pattern)
        (
            r"(Lost|Loss|Damaged|Damage|Delayed|Delay|Theft|Stolen)/(Lost|Loss|Damaged|Damage|Delayed|Delay|Theft|Stolen)",
            lambda match, req: [
                req.replace(f"{match.group(1)}/{match.group(2)}", match.group(1)),
                req.replace(f"{match.group(1)}/{match.group(2)}", match.group(2)),
            ],
        ),
        # Pattern for "Loss & Damage"
        (
            r"(Loss|Damage|Delay|Theft)\s+&\s+(Loss|Damage|Delay|Theft)",
            lambda match, req: [
                req.replace(f"{match.group(1)} & {match.group(2)}", match.group(1)),
                req.replace(f"{match.group(1)} & {match.group(2)}", match.group(2)),
            ],
        ),
    ]

    for requirement in requirements:
        compound_found = False
        for pattern, replacement_func in compound_patterns:
            match = re.search(pattern, requirement, re.IGNORECASE)
            if match:
                compound_found = True
                # Create atomic requirements from the compound requirement
                atomic_reqs = replacement_func(match, requirement)
                atomized_requirements.extend(atomic_reqs)
                break

        if not compound_found:
            atomized_requirements.append(requirement)

    return atomized_requirements


def evaluate_coverage(
    customer_id, requirements, recommended_policy, matcher, debug=False
):
    """
    Evaluate if the recommended policy covers the customer requirements.

    Uses the EmbeddingMatcher to match requirements against ground truth data
    and checks if the recommended policy is in the list of matching policies.

    Args:
        customer_id (str): Customer ID
        requirements (list): List of requirement strings
        recommended_policy (str): The recommended policy (e.g., "GELS - Platinum")
        matcher (EmbeddingMatcher): Instance of the EmbeddingMatcher for similarity search
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        dict: Evaluation results containing coverage metrics and detailed breakdown
    """
    coverage_results = {}

    # Get ground truth matches for all requirements at once
    ground_truth_matches = matcher.get_values_batch(requirements, debug=debug)

    # Track counts for different statuses
    covered_count = 0
    not_covered_count = 0
    not_exist_count = 0
    total_count = len(requirements)

    # Lists to store requirements by status
    covered_requirements = []
    not_covered_requirements = []
    not_exist_requirements = []

    for requirement in requirements:
        result = ground_truth_matches.get(requirement, "NOT_EXIST")

        if result == "NOT_EXIST":
            coverage_status = "NOT_EXIST"
            matched_key = None
            matched_values = []
            not_exist_count += 1
            not_exist_requirements.append(requirement)
        else:
            matched_key = result["matched_key"]
            matched_values = result["values"]

            if recommended_policy in matched_values:
                coverage_status = "COVERED"
                covered_count += 1
                covered_requirements.append(requirement)
            else:
                coverage_status = "NOT_COVERED"
                not_covered_count += 1
                not_covered_requirements.append(requirement)

        coverage_results[requirement] = {
            "matched_key": matched_key,
            "matched_values": matched_values,
            "recommended_policy": recommended_policy,
            "coverage_status": coverage_status,
        }

    # Calculate valid requirements (excluding NOT_EXIST)
    valid_requirements_count = total_count - not_exist_count

    # Calculate percentages
    original_coverage_percentage = (
        round(covered_count / total_count * 100, 2) if total_count > 0 else 0
    )
    adjusted_coverage_percentage = (
        round(covered_count / valid_requirements_count * 100, 2)
        if valid_requirements_count > 0
        else 0
    )

    return {
        "customer_id": customer_id,
        "recommended_policy": recommended_policy,
        # Original metrics including all requirements
        "total_coverage_ratio": f"{covered_count}/{total_count}",
        "total_coverage_percentage": original_coverage_percentage,
        # Metrics excluding non-existent requirements
        "valid_coverage_ratio": f"{covered_count}/{valid_requirements_count}"
        if valid_requirements_count > 0
        else "0/0",
        "valid_coverage_percentage": adjusted_coverage_percentage,
        "has_invalid_requirements": not_exist_count > 0,
        "requirements_breakdown": {
            "total": total_count,
            "valid": valid_requirements_count,
            "covered": covered_count,
            "not_covered": not_covered_count,
            "not_exist": not_exist_count,
        },
        "status_summary": {
            "covered_requirements": covered_requirements,
            "not_covered_requirements": not_covered_requirements,
            "not_exist_requirements": not_exist_requirements,
        },
        "requirements_coverage": coverage_results,
    }


def main():
    """
    Main function that processes all customers and generates coverage evaluation files.

    The process flow is:
    1. Initialize paths and the EmbeddingMatcher
    2. Get all customer IDs from requirement files
    3. For each customer:
       a. Find their requirement and recommendation files
       b. Extract requirements and recommended policy
       c. Atomize compound requirements into separate requirements
       d. Evaluate coverage
       e. Save individual evaluation file
    4. Calculate overall statistics
    5. Save summary file with all evaluations
    6. Generate a Markdown summary report
    """
    parser = argparse.ArgumentParser(
        description="Generate ground truth coverage evaluation"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug output for similarity scores"
    )
    parser.add_argument(
        "--customer", type=str, help="Process only this specific customer ID"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files",
        default=False,
    )
    args = parser.parse_args()

    # Initialize paths
    requirements_path = project_root / "data" / "extracted_customer_requirements"
    results_path = project_root / "results"
    output_path = project_root / "data" / "evaluation" / "ground_truth_evaluation"

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Initialize the embedding matcher
    matcher = EmbeddingMatcher(use_cache=True)

    # Get all customer IDs from requirement files
    customer_ids = []
    for req_file in glob.glob(str(requirements_path / "requirements_*.json")):
        # Extract customer ID from filename
        match = re.search(r"requirements_.*?_([a-f0-9\-]+)\.json", req_file)
        if match:
            customer_id = match.group(1)
            customer_ids.append(customer_id)

    # If a specific customer ID is provided, filter to only that one
    if args.customer:
        customer_ids = [cid for cid in customer_ids if cid == args.customer]
        if not customer_ids:
            print(f"Customer ID {args.customer} not found")
            return

    all_evaluations = {}
    overall_stats = {
        "total_customers": 0,
        "total_requirements": 0,
        "total_valid_requirements": 0,
        "total_covered_requirements": 0,
        "total_not_covered_requirements": 0,
        "total_not_exist_requirements": 0,
        "customers_with_invalid_requirements": 0,
        "perfect_coverage_count": 0,  # Customers with 100% adjusted coverage
    }

    # For the markdown report - track failing customers by coverage
    failing_customers = {}

    for customer_id in customer_ids:
        print(f"Processing customer: {customer_id}")

        # Find requirement file
        req_files = glob.glob(
            str(requirements_path / f"requirements_*_{customer_id}.json")
        )
        if not req_files:
            print(f"  No requirement file found for customer {customer_id}")
            continue

        # Find recommendation file
        rec_file = (
            results_path / customer_id / f"recommendation_report_{customer_id}.md"
        )
        if not os.path.exists(rec_file):
            print(f"  No recommendation file found for customer {customer_id}")
            continue

        # Extract requirement types and recommended policy
        requirements = get_customer_requirements(req_files[0])
        recommended_policy = extract_recommended_policy(rec_file)

        if not requirements:
            print(f"  No requirements found for customer {customer_id}")
            continue

        if not recommended_policy:
            print(f"  Could not extract recommended policy for customer {customer_id}")
            continue

        # Manual check for adventure activities
        # Load the customer data to directly check activities_to_cover
        try:
            with open(req_files[0], "r") as file:
                data = json.load(file)
                if "json_dict" in data:
                    # First, identify and standardize any sport/activity specific requirements
                    # (except golf-related ones)
                    activity_keywords = [
                        "hiking",
                        "trek",
                        "climb",
                        "swim",
                        "dive",
                        "ski",
                        "snowboard",
                        "adventure",
                        "sport",
                        "activity",
                        "recreation",
                        "bungee",
                        "balloon",
                    ]

                    # Track if we need to add adventure sports coverage
                    has_adventure_coverage = False

                    # Create a new list for the updated requirements
                    updated_requirements = []

                    # Process each requirement
                    for req in requirements:
                        req_lower = req.lower()

                        # Skip golf-related requirements
                        if "golf" in req_lower:
                            updated_requirements.append(req)
                            continue

                        # Check if this is an activity/sport related requirement
                        is_activity_req = False
                        for keyword in activity_keywords:
                            if keyword in req_lower:
                                is_activity_req = True
                                break

                        # If it's an activity requirement, replace it with the standard one
                        if is_activity_req:
                            # Skip if it's already our standard format
                            if req == "Adventurous activities or Amateur sports":
                                updated_requirements.append(req)
                                has_adventure_coverage = True
                            elif not has_adventure_coverage:
                                updated_requirements.append(
                                    "Adventurous activities or Amateur sports"
                                )
                                has_adventure_coverage = True
                        else:
                            # Keep non-activity requirements as they are
                            updated_requirements.append(req)

                    # Use the updated requirements list going forward
                    requirements = updated_requirements

                    # Now check for activities to cover
                    activities = data["json_dict"].get("activities_to_cover", [])

                    # If there are adventure-type activities and no similar coverage exists
                    if activities and len(activities) > 0:
                        # Check if there are any non-golf activities
                        has_golf = any(
                            "golf" in activity.lower() for activity in activities
                        )
                        has_non_golf = any(
                            "golf" not in activity.lower() for activity in activities
                        )

                        # If there's golf mentioned in activities and no golf requirement
                        if has_golf and not any(
                            "golf" in req.lower() for req in requirements
                        ):
                            requirements.append("Golf Coverage")
                            if args.debug:
                                print(f"  Added 'Golf Coverage' due to golf activities")

                        # Only add adventure coverage if we don't already have it and there are non-golf activities
                        if has_non_golf and not has_adventure_coverage:
                            # Define keywords that would indicate adventure/sports coverage
                            # Using word boundaries to match whole words only
                            adventure_keywords = [
                                r"\badventur",
                                r"\bsport",
                                r"\bactiv",
                                r"\brecreation",
                            ]

                            # Check if any existing requirement already contains these keywords
                            for req in requirements:
                                req_lower = req.lower()
                                for keyword in adventure_keywords:
                                    # Use regex with word boundaries to match whole words only
                                    if re.search(keyword, req_lower):
                                        has_adventure_coverage = True
                                        break
                                if has_adventure_coverage:
                                    break

                            # Add adventure sports requirement if none exists and we have non-golf activities
                            if not has_adventure_coverage:
                                requirements.append(
                                    "Adventurous activities or Amateur sports"
                                )
                                if args.debug:
                                    print(
                                        f"  Added 'Adventurous activities or Amateur sports' due to non-golf activities: {[act for act in activities if 'golf' not in act.lower()]}"
                                    )
        except Exception as e:
            print(f"  Error checking activities: {e}")

        # If in debug mode, show original requirements and their similarity scores
        if args.debug:
            print("\n=== ORIGINAL REQUIREMENTS ===")
            for req in requirements:
                print(f"  {req}")
                matcher.debug_similarity(req)

        # Atomize compound requirements into separate requirements
        atomized_requirements = atomize_requirements(requirements)
        if len(atomized_requirements) > len(requirements):
            print(
                f"  Atomized {len(requirements)} requirements into {len(atomized_requirements)} atomic requirements"
            )

            # If in debug mode, show atomized requirements and their similarity scores
            if args.debug:
                print("\n=== ATOMIZED REQUIREMENTS ===")
                for req in atomized_requirements:
                    if (
                        req not in requirements
                    ):  # Only show new requirements from atomization
                        print(f"  {req}")
                        matcher.debug_similarity(req)

        # Evaluate coverage
        evaluation = evaluate_coverage(
            customer_id, atomized_requirements, recommended_policy, matcher, args.debug
        )
        all_evaluations[customer_id] = evaluation

        # Update overall stats
        overall_stats["total_customers"] += 1
        overall_stats["total_requirements"] += evaluation["requirements_breakdown"][
            "total"
        ]
        overall_stats["total_valid_requirements"] += evaluation[
            "requirements_breakdown"
        ]["valid"]
        overall_stats["total_covered_requirements"] += evaluation[
            "requirements_breakdown"
        ]["covered"]
        overall_stats["total_not_covered_requirements"] += evaluation[
            "requirements_breakdown"
        ]["not_covered"]
        overall_stats["total_not_exist_requirements"] += evaluation[
            "requirements_breakdown"
        ]["not_exist"]

        if evaluation["has_invalid_requirements"]:
            overall_stats["customers_with_invalid_requirements"] += 1

        if evaluation["valid_coverage_percentage"] == 100:
            overall_stats["perfect_coverage_count"] += 1
        else:
            # Track failing customers for the markdown report
            failing_customers[customer_id] = {
                "valid_coverage_percentage": evaluation["valid_coverage_percentage"],
                "not_covered_requirements": evaluation["status_summary"][
                    "not_covered_requirements"
                ],
            }

        # Save individual evaluation
        output_file = output_path / f"coverage_evaluation_{customer_id}.json"
        if not args.overwrite and output_file.exists():
            print(f"  Skipping existing individual file: {output_file}")
        else:
            with open(output_file, "w") as f:
                json.dump(evaluation, f, indent=2)

        print(
            f"  Total coverage ratio (all requirements): {evaluation['total_coverage_ratio']} ({evaluation['total_coverage_percentage']}%)"
        )
        print(
            f"  Valid coverage ratio (excluding non-existent requirements): {evaluation['valid_coverage_ratio']} ({evaluation['valid_coverage_percentage']}%)"
        )
        if evaluation["has_invalid_requirements"]:
            print(
                f"  Invalid requirements count: {evaluation['requirements_breakdown']['not_exist']}"
            )

    # Calculate overall percentages
    if overall_stats["total_requirements"] > 0:
        overall_stats["overall_total_coverage_percentage"] = round(
            overall_stats["total_covered_requirements"]
            / overall_stats["total_requirements"]
            * 100,
            2,
        )
    else:
        overall_stats["overall_total_coverage_percentage"] = 0

    if overall_stats["total_valid_requirements"] > 0:
        overall_stats["overall_valid_coverage_percentage"] = round(
            overall_stats["total_covered_requirements"]
            / overall_stats["total_valid_requirements"]
            * 100,
            2,
        )
    else:
        overall_stats["overall_valid_coverage_percentage"] = 0

    # Add percentage of customers with perfect coverage
    if overall_stats["total_customers"] > 0:
        overall_stats["perfect_coverage_percentage"] = round(
            overall_stats["perfect_coverage_count"]
            / overall_stats["total_customers"]
            * 100,
            2,
        )
    else:
        overall_stats["perfect_coverage_percentage"] = 0

    # Save summary of all evaluations
    summary_file = output_path / "coverage_evaluation_summary.json"
    if not args.overwrite and summary_file.exists():
        print(f"\nSkipping existing summary JSON file: {summary_file}")
    else:
        with open(summary_file, "w") as f:
            json.dump(
                {
                    "summary": {
                        "overall_stats": overall_stats,
                        "evaluations": all_evaluations,
                    }
                },
                f,
                indent=2,
            )

    # Generate Markdown summary report
    md_summary_file = output_path / "coverage_evaluation_summary.md"

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

    if not args.overwrite and md_summary_file.exists():
        print(f"Skipping existing summary Markdown file: {md_summary_file}")
    else:
        with open(md_summary_file, "w") as f:
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

    print(f"\nEvaluation complete. Results saved to {output_path}")
    print(
        f"Overall total coverage: {overall_stats['overall_total_coverage_percentage']}%"
    )
    print(
        f"Overall valid coverage (excluding non-existent requirements): {overall_stats['overall_valid_coverage_percentage']}%"
    )
    print(
        f"Customers with perfect valid coverage: {overall_stats['perfect_coverage_count']}/{overall_stats['total_customers']} ({overall_stats['perfect_coverage_percentage']}%)"
    )
    print(
        f"Customers with non-existent requirements: {overall_stats['customers_with_invalid_requirements']}/{overall_stats['total_customers']}"
    )
    print(f"Markdown summary saved to {md_summary_file}")


if __name__ == "__main__":
    main()
