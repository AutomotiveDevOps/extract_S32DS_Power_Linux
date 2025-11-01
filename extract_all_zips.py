#!/usr/bin/env python3
"""
Recursively extract all ZIP files in the current directory and subdirectories.

This script finds all .zip files, extracts them in place, removes the original
ZIP file, and repeats until no more ZIP files remain.

Examples
--------
>>> python3 extract_all_zips.py
Found 2 zip files
Extracting ./C_/MakingInstalers/parts/Activation.zip...
Extracting ./installer_payload.zip...
Found 1 zip files
Extracting ./some_new.zip...
No more zip files found. Extraction complete.
"""

import os
import zipfile
from pathlib import Path
from typing import List, Set


def find_zip_files(
    directory: Path = Path("."), exclude_patterns: List[str] = None
) -> List[Path]:
    """
    Find all ZIP files in the directory and subdirectories.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")
    exclude_patterns : List[str], optional
        List of filename patterns to exclude (e.g., ["installer_payload.zip"]),
        by default None

    Returns
    -------
    List[Path]
        List of paths to ZIP files found.
    """
    if exclude_patterns is None:
        exclude_patterns = []
    zip_files: List[Path] = []
    for root, dirs, files in os.walk(directory):
        # Skip .git directory
        if ".git" in root:
            continue
        for file in files:
            if file.endswith(".zip"):
                # Check if file matches any exclude pattern
                if any(pattern in file for pattern in exclude_patterns):
                    continue
                zip_files.append(Path(root) / file)
    return zip_files


def extract_zip(zip_path: Path, skip_if_corrupt: bool = True) -> bool:
    """
    Extract a ZIP file in place and remove the original.

    Parameters
    ----------
    zip_path : Path
        Path to the ZIP file to extract.
    skip_if_corrupt : bool, optional
        If True, skip corrupted ZIP files instead of raising, by default True

    Returns
    -------
    bool
        True if extraction was successful and file was removed,
        False if extraction failed or was skipped.

    Raises
    ------
    PermissionError
        If there are permission issues reading/writing files.
    """
    zip_dir: Path = zip_path.parent
    print(f"Extracting {zip_path}...")

    try:
        # Try with allowZip64 and ignore errors for corrupted extra fields
        with zipfile.ZipFile(zip_path, "r", allowZip64=True) as zip_ref:
            # Test if ZIP is readable
            zip_ref.testzip()
            # Extract all files to the same directory as the ZIP
            zip_ref.extractall(zip_dir)

        # Remove the original ZIP file after successful extraction
        zip_path.unlink()
        print(f"  Removed {zip_path}")
        return True

    except zipfile.BadZipFile as e:
        if skip_if_corrupt:
            print(f"  Skipping corrupted ZIP file: {zip_path} ({e})")
            return False
        else:
            raise
    except Exception as e:
        if skip_if_corrupt:
            print(f"  Skipping ZIP file due to error: {zip_path} ({e})")
            return False
        else:
            raise


def extract_all_recursive(
    max_iterations: int = 100, exclude_patterns: List[str] = None
) -> None:
    """
    Recursively extract all ZIP files until none remain.

    Parameters
    ----------
    max_iterations : int, optional
        Maximum number of extraction rounds to prevent infinite loops,
        by default 100
    exclude_patterns : List[str], optional
        List of filename patterns to exclude from extraction
        (e.g., ["installer_payload.zip"]), by default None

    Notes
    -----
    This function will continue extracting ZIP files until:
    - No more ZIP files are found, or
    - max_iterations is reached (to prevent infinite loops)

    Each extracted ZIP may contain more ZIP files, so the process repeats.
    Corrupted ZIP files will be skipped to prevent infinite loops.
    """
    if exclude_patterns is None:
        exclude_patterns = ["installer_payload.zip"]
    iteration: int = 0
    extracted_count: int = 0
    skipped_files: Set[Path] = set()

    while iteration < max_iterations:
        zip_files: List[Path] = find_zip_files(exclude_patterns=exclude_patterns)

        # Filter out previously skipped files
        zip_files = [zf for zf in zip_files if zf not in skipped_files]

        if not zip_files:
            print(f"\nNo more zip files found. Extraction complete.")
            print(f"Total files extracted: {extracted_count}")
            if skipped_files:
                print(f"Skipped {len(skipped_files)} corrupted/problematic file(s)")
            return

        print(f"\nFound {len(zip_files)} zip file(s)")

        for zip_file in zip_files:
            success: bool = extract_zip(zip_file, skip_if_corrupt=True)
            if success:
                extracted_count += 1
            else:
                # Track skipped files to avoid retrying them
                skipped_files.add(zip_file)

        iteration += 1

    print(f"\nWarning: Reached maximum iterations ({max_iterations})")
    print(f"Total files extracted: {extracted_count}")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} corrupted/problematic file(s)")


if __name__ == "__main__":
    extract_all_recursive()

