import os
import json
from collections import defaultdict
from pathlib import Path

def main():
    # Define paths
    processed_dir = Path("data/policies/processed")
    output_file = Path("data/ground_truth/ground_truth.json")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to store coverage -> list of files mapping
    # Using lowercase keys for case-insensitive comparison
    coverage_mapping = defaultdict(list)
    # Dictionary to keep track of original case for display
    original_case = {}
    
    # Load existing mapping if the file exists
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_mapping = json.load(f)
                
            # Convert existing mapping to defaultdict with list values
            # Use lowercase keys for case-insensitive matching
            for coverage_name, files in existing_mapping.items():
                lowercase_name = coverage_name.lower()
                coverage_mapping[lowercase_name].extend(files)
                # Keep the original case version (use the first one encountered)
                if lowercase_name not in original_case:
                    original_case[lowercase_name] = coverage_name
            
            print(f"Loaded existing mapping with {len(existing_mapping)} coverages")
        except Exception as e:
            print(f"Error loading existing mapping: {str(e)}")
            print(f"Starting with new mapping")
    
    # Process all json files in the processed directory
    json_files = list(processed_dir.glob("*.json"))
    print(f"Found {len(json_files)} policy files to process")
    
    for json_file in json_files:
        file_name = json_file.name
        print(f"Processing {file_name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                policy_data = json.load(f)
            
            # Extract coverage names from all categories
            for category in policy_data.get("coverage_categories", []):
                for coverage in category.get("coverages", []):
                    coverage_name = coverage.get("coverage_name")
                    
                    # Skip coverages that are not covered or NA
                    if coverage_name:
                        # Check base_limits to see if it's covered
                        base_limits = coverage.get("base_limits", [])
                        is_covered = True
                        
                        # If any limit is "Not covered", "NA", or "N.A." (case insensitive), skip this coverage
                        for limit_obj in base_limits:
                            limit_value = limit_obj.get("limit", "")
                            if isinstance(limit_value, str) and limit_value.lower() in ["not covered", "na", "n.a."]:
                                is_covered = False
                                break
                        
                        if not is_covered:
                            continue  # Skip this coverage
                            
                        # Convert to lowercase for case-insensitive comparison
                        lowercase_name = coverage_name.lower()
                        
                        # Only append if file name isn't already in the list
                        if file_name not in coverage_mapping[lowercase_name]:
                            coverage_mapping[lowercase_name].append(file_name)
                        
                        # Save original case (prefer longer names if different)
                        if lowercase_name not in original_case or len(coverage_name) > len(original_case[lowercase_name]):
                            original_case[lowercase_name] = coverage_name
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
    
    # Convert defaultdict to regular dict for JSON serialization
    # Use the original case for final output keys
    coverage_mapping_dict = {}
    for lowercase_name, files in coverage_mapping.items():
        # Use the saved original case version as the key
        original_name = original_case.get(lowercase_name, lowercase_name)
        coverage_mapping_dict[original_name] = sorted(files)
    
    # Write the mapping to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(coverage_mapping_dict, f, indent=2, sort_keys=True)
    
    print(f"Coverage mapping created with {len(coverage_mapping_dict)} unique coverages")
    print(f"Output written to {output_file}")

if __name__ == "__main__":
    main() 