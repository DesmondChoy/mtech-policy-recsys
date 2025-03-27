"""
Fix All Python Files

This script fixes encoding issues in all Python files in the project.
It removes null bytes and fixes other encoding issues.
"""

import os
import sys
import re


def fix_file(file_path):
    """
    Fix encoding issues in a file.

    Args:
        file_path: Path to the file to fix

    Returns:
        True if the file was fixed, False otherwise
    """
    try:
        # Read the file in binary mode
        with open(file_path, "rb") as f:
            content = f.read()

        # Check if the file has null bytes or other encoding issues
        has_null_bytes = b"\x00" in content
        has_bom = (
            content.startswith(b"\xef\xbb\xbf")
            or content.startswith(b"\xff\xfe")
            or content.startswith(b"\xfe\xff")
        )

        # If the file has encoding issues, fix it
        if has_null_bytes or has_bom:
            # Remove null bytes
            content = content.replace(b"\x00", b"")

            # Remove BOM
            if content.startswith(b"\xef\xbb\xbf"):
                content = content[3:]
            elif content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
                content = content[2:]

            # Try to decode the content as UTF-8
            try:
                decoded_content = content.decode("utf-8")
            except UnicodeDecodeError:
                # If UTF-8 decoding fails, try to decode as Latin-1
                try:
                    decoded_content = content.decode("latin-1")
                except UnicodeDecodeError:
                    # If Latin-1 decoding fails, try to decode as ASCII
                    try:
                        decoded_content = content.decode("ascii", errors="ignore")
                    except UnicodeDecodeError:
                        print(f"Failed to decode {file_path}")
                        return False

            # Write the fixed content back to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(decoded_content)

            print(f"Fixed {file_path}")
            return True

        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {str(e)}")
        return False


def fix_directory(directory_path, extensions=None):
    """
    Fix all files in a directory and its subdirectories.

    Args:
        directory_path: Path to the directory to fix
        extensions: List of file extensions to fix (e.g., ['.py', '.txt'])
                   If None, fix all files

    Returns:
        Tuple of (fixed_files, total_files)
    """
    fixed_files = 0
    total_files = 0

    for root, _, files in os.walk(directory_path):
        for file in files:
            if extensions is None or any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                total_files += 1
                if fix_file(file_path):
                    fixed_files += 1

    print(f"Fixed {fixed_files} out of {total_files} files")

    return fixed_files, total_files


def main():
    """Main function to run the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix encoding issues in files")
    parser.add_argument(
        "--dir", default=".", help="Directory to fix (default: current directory)"
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        default=[".py"],
        help="File extensions to fix (default: .py)",
    )

    args = parser.parse_args()

    print(f"Fixing files with extensions {args.ext} in {args.dir}")

    fix_directory(args.dir, args.ext)

    print("\nFiles have been fixed. Try running your script again.")


if __name__ == "__main__":
    main()
