#!/usr/bin/env python
"""
Example script demonstrating the embedding-based insurance policy recommender.
"""
import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.embedding.embedding_recommender import EmbeddingRecommender

def main():
    print("Insurance Policy Recommendation System Demo")
    print("------------------------------------------")
    
    # Initialize the recommender
    recommender = EmbeddingRecommender()
    print(f"Loading policies from {recommender.policies_dir}")
    
    # Load sample requirement
    requirement_path = os.path.join("data", "extracted_requirements", "insurance_requirement.json")
    
    try:
        with open(requirement_path, 'r') as f:
            requirement = json.load(f)
    except FileNotFoundError:
        print(f"Error: Requirement file not found at {requirement_path}")
        print("Make sure you have a requirement JSON file in the specified location.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in requirement file {requirement_path}")
        return
    
    print("\nUser Requirement:")
    print(f"- Summary: {requirement.get('requirement_summary', 'Not specified')}")
    print(f"- Destination: {requirement.get('travel_destination', 'Not specified')}")
    print(f"- Duration: {requirement.get('travel_duration', 'Not specified')}")
    print(f"- Coverage Types: {', '.join(requirement.get('insurance_coverage_type', ['Not specified']))}")
    print(f"- Travelers: {requirement.get('travelers_count', 'Not specified')}")
    
    print("\nGenerating recommendations...")
    # Get recommendations
    recommendations = recommender.recommend(requirement, top_n=3)
    
    if not recommendations:
        print("No recommendations found.")
        return
    
    print("\nTop 3 Recommended Policies:")
    for rank, (policy_id, similarity) in enumerate(recommendations, 1):
        policy = recommender.get_policy_details(policy_id)
        if not policy:
            continue
            
        print(f"\n{rank}. {policy_id} (Similarity: {similarity:.4f})")
        print(f"   Provider: {policy.get('provider_name')}")
        print(f"   Policy: {policy.get('policy_name')}, Tier: {policy.get('tier_name')}")
        
        # Find coverage types that match requirement
        req_coverage_types = requirement.get('insurance_coverage_type', [])
        
        for category in policy.get('coverage_categories', []):
            for coverage in category.get('coverages', []):
                coverage_name = coverage.get('coverage_name', '').lower()
                
                if any(req_type.lower() in coverage_name for req_type in req_coverage_types):
                    limit_info = []
                    for limit in coverage.get('limits', []):
                        if 'type' in limit and 'limit' in limit:
                            limit_info.append(f"{limit['type']}: {limit['limit']} {policy.get('currency', 'SGD')}")
                    
                    print(f"   - {coverage.get('coverage_name')}: {', '.join(limit_info)}")
    
    print("\nNote: This demo uses placeholder random embeddings.")
    print("In production, replace with actual API calls to an embedding model.")
    print("\n------------------------------------------")

if __name__ == "__main__":
    main() 