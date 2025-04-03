#!/usr/bin/env python
import argparse
import json
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing the EmbeddingRecommender
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.recommender.embedding_recommender import EmbeddingRecommender

def parse_args():
    parser = argparse.ArgumentParser(
        description="Insurance Policy Recommendation System using embeddings"
    )
    
    parser.add_argument(
        "--requirement",
        "-r",
        type=str,
        required=True,
        help="Path to the requirement JSON file",
    )
    
    parser.add_argument(
        "--policies-dir",
        "-p",
        type=str,
        default=os.path.join("data", "processed_policies"),
        help="Directory containing processed policy JSON files",
    )
    
    parser.add_argument(
        "--top-n",
        "-n",
        type=int,
        default=1,
        help="Number of top recommendations to return",
    )
    
    parser.add_argument(
        "--force-refresh",
        "-f",
        action="store_true",
        help="Force refresh of policy embeddings cache",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Check if requirement file exists
    if not os.path.isfile(args.requirement):
        print(f"Error: Requirement file {args.requirement} not found.")
        sys.exit(1)
    
    # Check if policies directory exists
    if not os.path.isdir(args.policies_dir):
        print(f"Error: Policies directory {args.policies_dir} not found.")
        sys.exit(1)
    
    # Load requirement
    try:
        with open(args.requirement, 'r') as f:
            requirement = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in requirement file {args.requirement}.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading requirement file: {str(e)}")
        sys.exit(1)
    
    # Initialize recommender
    recommender = EmbeddingRecommender(policies_dir=args.policies_dir)
    
    # Generate/load embeddings
    recommender.generate_policy_embeddings(force_refresh=args.force_refresh)
    
    # Get recommendations
    recommendations = recommender.recommend(requirement, top_n=args.top_n)
    
    if not recommendations:
        print(f"No recommendations found for the given requirement.")
        sys.exit(0)
    
    # Print recommendations
    print(f"\n--- Top {len(recommendations)} Recommendations ---\n")
    
    for rank, (policy_id, similarity) in enumerate(recommendations, 1):
        policy = recommender.get_policy_details(policy_id)
        if not policy:
            continue
            
        print(f"Rank #{rank}: {policy_id} (Similarity Score: {similarity:.4f})")
        print(f"Provider: {policy.get('provider_name')}")
        print(f"Policy: {policy.get('policy_name')}, Tier: {policy.get('tier_name')}")
        
        # Find and display relevant coverages
        if args.verbose:
            print("\nRelevant Coverages:")
            req_coverage_types = requirement.get('insurance_coverage_type', [])
            found_relevant = False
            
            for category in policy.get('coverage_categories', []):
                for coverage in category.get('coverages', []):
                    coverage_name = coverage.get('coverage_name', '').lower()
                    
                    # Check if this coverage is relevant to the requirement
                    is_relevant = any(req_type.lower() in coverage_name for req_type in req_coverage_types)
                    
                    if is_relevant:
                        found_relevant = True
                        # Display coverage details
                        print(f"- {coverage.get('coverage_name')}")
                        
                        # Display limits
                        for limit in coverage.get('limits', []):
                            if 'type' in limit and 'limit' in limit:
                                print(f"  • {limit['type']}: {limit['limit']} {policy.get('currency', 'SGD')}")
                        
                        # Display details if available
                        if 'details' in coverage and coverage['details']:
                            # Truncate long details
                            details = coverage['details']
                            if len(details) > 200:
                                details = details[:197] + "..."
                            print(f"  • Details: {details}")
            
            if not found_relevant:
                print("  No coverage specifically matching the requested types was found.")
        
        print("\n" + "-" * 60 + "\n")
    
    # Summary
    print(f"Requirement Summary: {requirement.get('requirement_summary', 'Not specified')}")
    print(f"Requested Coverage Types: {', '.join(requirement.get('insurance_coverage_type', ['Not specified']))}")
    
if __name__ == "__main__":
    main() 