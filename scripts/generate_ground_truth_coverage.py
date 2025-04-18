#!/usr/bin/env python3
"""
Ground Truth Coverage Evaluation Script
=======================================

This script evaluates how well recommended insurance policies cover customer requirements by:
1. Reading customer requirements from extracted data files (data/extracted_customer_requirements/requirements_*_<customerID>.json)
2. Finding the recommended policy from recommendation reports (results/<customerID>/recommendation_report_<customerID>.md)
3. Using semantic search to match requirements with ground truth data via the EmbeddingMatcher
4. Evaluating whether each requirement is covered by the recommended policy

Key Feature: This script not only processes the stated "insurance_coverage_type" requirements but also
examines the "activities_to_cover" field to intelligently add additional requirements based on activities.
For example, if a customer lists "golf" in their activities, the script adds golf coverage to their requirements.

The script handles requirements that don't exist in any policy (NOT_EXIST) differently from
requirements that exist but aren't covered by the recommended policy (NOT_COVERED).

Two key metrics are calculated:
- Total coverage: Percentage of ALL requirements covered by the recommended policy
- Valid coverage: Percentage of VALID requirements (excluding non-existent ones) covered by the policy

Features:
- Batch processing of all customers
- Detailed breakdown of covered/not covered/non-existent requirements
- Activity-based requirement enhancement (adds requirements based on activities_to_cover field)
- Summary statistics across all customers
- Individual evaluation files for each customer

Usage:
    python scripts/generate_ground_truth_coverage.py

Output:
    - Individual JSON files for each customer in data/evaluation/ground_truth_evaluation/coverage_evaluation_<customerID>.json
    - Summary JSON file data/evaluation/ground_truth_evaluation/coverage_evaluation_summary.json with statistics across all customers
"""
import os
import json
import re
import sys
from pathlib import Path
import glob

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
        with open(recommendation_file, 'r') as file:
            content = file.read()
            # Look for the pattern: **INSURER - PLAN**
            pattern = r'\*\*([\w\s]+) - ([\w\s]+)\*\*'
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
    
    This enhancement ensures that customers' activity plans (like golf or hiking) are properly
    factored into coverage requirements, even if not explicitly listed in insurance_coverage_type.
    
    Args:
        requirement_file (str or Path): Path to the customer requirements JSON file
                                       (data/extracted_customer_requirements/requirements_*_<customerID>.json)
        
    Returns:
        list: Enhanced list of requirement strings combining explicit requirements and activity-based requirements
    """
    try:
        with open(requirement_file, 'r') as file:
            data = json.load(file)
            if "json_dict" not in data:
                return []
            
            # Get the main insurance coverage types
            requirements = data["json_dict"].get("insurance_coverage_type", [])
            
            # Check activities_to_cover field
            activities = data["json_dict"].get("activities_to_cover", [])
            
            if not activities:
                # If empty, ignore
                pass
            else:
                # Check for golf activities
                has_golf = any("golf" in activity.lower() for activity in activities)
                has_non_golf = any("golf" not in activity.lower() for activity in activities)
                
                # If there's golf mentioned in activities and no golf requirement
                if has_golf and not any("golf" in req.lower() for req in requirements):
                    requirements.append("Golf Coverage")
                
                # If there's any non-golf activity
                if has_non_golf and "Adventurous activities or Amateur sports" not in requirements:
                    requirements.append("Adventurous activities or Amateur sports")
            
            return requirements
    except Exception as e:
        print(f"Error reading requirements file {requirement_file}: {e}")
        return []

def evaluate_coverage(customer_id, requirements, recommended_policy, matcher):
    """
    Evaluate if the recommended policy covers the customer requirements.
    
    Uses the EmbeddingMatcher to match requirements against ground truth data
    and checks if the recommended policy is in the list of matching policies.
    
    Args:
        customer_id (str): Customer ID
        requirements (list): List of requirement strings
        recommended_policy (str): The recommended policy (e.g., "GELS - Platinum")
        matcher (EmbeddingMatcher): Instance of the EmbeddingMatcher for similarity search
        
    Returns:
        dict: Evaluation results containing coverage metrics and detailed breakdown
    """
    coverage_results = {}
    
    # Get ground truth matches for all requirements at once
    ground_truth_matches = matcher.get_values_batch(requirements)
    
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
            "coverage_status": coverage_status
        }
    
    # Calculate valid requirements (excluding NOT_EXIST)
    valid_requirements_count = total_count - not_exist_count
    
    # Calculate percentages
    original_coverage_percentage = round(covered_count / total_count * 100, 2) if total_count > 0 else 0
    adjusted_coverage_percentage = round(covered_count / valid_requirements_count * 100, 2) if valid_requirements_count > 0 else 0
    
    return {
        "customer_id": customer_id,
        "recommended_policy": recommended_policy,
        # Original metrics including all requirements
        "total_coverage_ratio": f"{covered_count}/{total_count}",
        "total_coverage_percentage": original_coverage_percentage,
        # Metrics excluding non-existent requirements
        "valid_coverage_ratio": f"{covered_count}/{valid_requirements_count}" if valid_requirements_count > 0 else "0/0",
        "valid_coverage_percentage": adjusted_coverage_percentage,
        "has_invalid_requirements": not_exist_count > 0,
        "requirements_breakdown": {
            "total": total_count,
            "valid": valid_requirements_count,
            "covered": covered_count,
            "not_covered": not_covered_count,
            "not_exist": not_exist_count
        },
        "status_summary": {
            "covered_requirements": covered_requirements,
            "not_covered_requirements": not_covered_requirements,
            "not_exist_requirements": not_exist_requirements
        },
        "requirements_coverage": coverage_results
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
       c. Evaluate coverage
       d. Save individual evaluation file
    4. Calculate overall statistics
    5. Save summary file with all evaluations
    """
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
        match = re.search(r'requirements_.*?_([a-f0-9\-]+)\.json', req_file)
        if match:
            customer_id = match.group(1)
            customer_ids.append(customer_id)
    
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
    
    for customer_id in customer_ids:
        print(f"Processing customer: {customer_id}")
        
        # Find requirement file
        req_files = glob.glob(str(requirements_path / f"requirements_*_{customer_id}.json"))
        if not req_files:
            print(f"  No requirement file found for customer {customer_id}")
            continue
        
        # Find recommendation file
        rec_file = results_path / customer_id / f"recommendation_report_{customer_id}.md"
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
        
        # Evaluate coverage
        evaluation = evaluate_coverage(customer_id, requirements, recommended_policy, matcher)
        all_evaluations[customer_id] = evaluation
        
        # Update overall stats
        overall_stats["total_customers"] += 1
        overall_stats["total_requirements"] += evaluation["requirements_breakdown"]["total"]
        overall_stats["total_valid_requirements"] += evaluation["requirements_breakdown"]["valid"]
        overall_stats["total_covered_requirements"] += evaluation["requirements_breakdown"]["covered"]
        overall_stats["total_not_covered_requirements"] += evaluation["requirements_breakdown"]["not_covered"]
        overall_stats["total_not_exist_requirements"] += evaluation["requirements_breakdown"]["not_exist"]
        
        if evaluation["has_invalid_requirements"]:
            overall_stats["customers_with_invalid_requirements"] += 1
            
        if evaluation["valid_coverage_percentage"] == 100:
            overall_stats["perfect_coverage_count"] += 1
        
        # Save individual evaluation
        output_file = output_path / f"coverage_evaluation_{customer_id}.json"
        with open(output_file, 'w') as f:
            json.dump(evaluation, f, indent=2)
            
        print(f"  Total coverage ratio (all requirements): {evaluation['total_coverage_ratio']} ({evaluation['total_coverage_percentage']}%)")
        print(f"  Valid coverage ratio (excluding non-existent requirements): {evaluation['valid_coverage_ratio']} ({evaluation['valid_coverage_percentage']}%)")
        if evaluation["has_invalid_requirements"]:
            print(f"  Invalid requirements count: {evaluation['requirements_breakdown']['not_exist']}")
    
    # Calculate overall percentages
    if overall_stats["total_requirements"] > 0:
        overall_stats["overall_total_coverage_percentage"] = round(
            overall_stats["total_covered_requirements"] / overall_stats["total_requirements"] * 100, 2
        )
    else:
        overall_stats["overall_total_coverage_percentage"] = 0
        
    if overall_stats["total_valid_requirements"] > 0:
        overall_stats["overall_valid_coverage_percentage"] = round(
            overall_stats["total_covered_requirements"] / overall_stats["total_valid_requirements"] * 100, 2
        )
    else:
        overall_stats["overall_valid_coverage_percentage"] = 0
    
    # Add percentage of customers with perfect coverage
    if overall_stats["total_customers"] > 0:
        overall_stats["perfect_coverage_percentage"] = round(
            overall_stats["perfect_coverage_count"] / overall_stats["total_customers"] * 100, 2
        )
    else:
        overall_stats["perfect_coverage_percentage"] = 0
    
    # Save summary of all evaluations
    summary_file = output_path / "coverage_evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            "summary": {
                "overall_stats": overall_stats,
                "evaluations": all_evaluations
            }
        }, f, indent=2)
    
    print(f"\nEvaluation complete. Results saved to {output_path}")
    print(f"Overall total coverage: {overall_stats['overall_total_coverage_percentage']}%")
    print(f"Overall valid coverage (excluding non-existent requirements): {overall_stats['overall_valid_coverage_percentage']}%")
    print(f"Customers with perfect valid coverage: {overall_stats['perfect_coverage_count']}/{overall_stats['total_customers']} ({overall_stats['perfect_coverage_percentage']}%)")
    print(f"Customers with non-existent requirements: {overall_stats['customers_with_invalid_requirements']}/{overall_stats['total_customers']}")

if __name__ == "__main__":
    main() 