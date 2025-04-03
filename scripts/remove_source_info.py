import json
import os
import argparse

def remove_source_info(json_file_path, output_dir='for_embedding'):
    """
    Remove the source_info field from a JSON file and save to a new file in output directory.
    
    Args:
        json_file_path (str): Path to the JSON file
        output_dir (str): Directory to save the modified files
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Function to recursively remove source_info
        def remove_source_info_recursive(obj):
            if isinstance(obj, dict):
                # Remove source_info if it exists
                if 'source_info' in obj:
                    del obj['source_info']
                # Recursively process all values
                for key, value in list(obj.items()):
                    obj[key] = remove_source_info_recursive(value)
            elif isinstance(obj, list):
                # Process each item in the list
                return [remove_source_info_recursive(item) for item in obj]
            return obj
        
        # Remove source_info recursively
        modified_data = remove_source_info_recursive(data)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the filename and create new path
        filename = os.path.basename(json_file_path)
        output_path = os.path.join(output_dir, filename)
        
        # Write the modified data to the new file
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(modified_data, file, indent=2, ensure_ascii=False)
        
        print(f"Successfully created modified file at {output_path}")
        
    except json.JSONDecodeError:
        print(f"Error: {json_file_path} is not a valid JSON file")
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
    except Exception as e:
        print(f"Error processing {json_file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Remove source_info field from JSON files and save to new files')
    parser.add_argument('file_path', help='Path to the JSON file or directory containing JSON files')
    parser.add_argument('--recursive', '-r', action='store_true', help='Process JSON files recursively in directories')
    parser.add_argument('--output', '-o', default=os.path.join("data", "policies", "for_embedding"), help='Output directory for modified files (default: for_embedding)')
    
    args = parser.parse_args()
    
    if os.path.isfile(args.file_path):
        if args.file_path.endswith('.json'):
            remove_source_info(args.file_path, args.output)
        else:
            print("Error: File is not a JSON file")
    elif os.path.isdir(args.file_path):
        for root, _, files in os.walk(args.file_path if args.recursive else args.file_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    remove_source_info(file_path, args.output)
    else:
        print(f"Error: {args.file_path} is not a valid file or directory")

if __name__ == "__main__":
    main() 