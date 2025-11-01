#!/usr/bin/env python3
"""
Recursively extract all JAR and ZIP files until PowerPC GCC and GDB server are found.

This script extracts all nested archives (JAR and ZIP files) recursively until it finds:
1. PowerPC GCC compiler (in Cross_Tools directories)
2. P&E GDB Server components:
   - pegdbserver_power_console binary
   - GDI files (plugins/com.pemicro.debug.gdbjtag.ppc_*/)

Examples
--------
>>> python3 extract_until_targets.py
Extracting archives...
Found 8 jar files
Extracting ./C_/MakingInstalers/Layout/eclipse_zg_ia_sf.jar...
...
✓ Found PowerPC GCC at: ./Cross_Tools/gcc-4.9.2-powerpc-eabi/bin/powerpc-eabi-gcc
✓ Found GDB server at: ./plugins/com.pemicro.debug.gdbjtag.ppc_1.7.2.201709281658/lin/pegdbserver_power_console
Extraction complete. All targets found!
"""

import os
import zipfile
import subprocess
from pathlib import Path
from typing import List, Set, Optional, Tuple
import re


def find_archives(
    directory: Path = Path("."), exclude_patterns: List[str] = None
) -> List[Path]:
    """
    Find all JAR and ZIP files in the directory and subdirectories.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")
    exclude_patterns : List[str], optional
        List of filename patterns to exclude, by default None

    Returns
    -------
    List[Path]
        List of paths to archive files found.
    """
    if exclude_patterns is None:
        exclude_patterns = ["installer_payload.zip"]
    archives: List[Path] = []
    for root, dirs, files in os.walk(directory):
        # Skip .git directory
        if ".git" in root:
            continue
        for file in files:
            if file.endswith((".zip", ".jar")):
                # Check if file matches any exclude pattern
                if any(pattern in file for pattern in exclude_patterns):
                    continue
                archives.append(Path(root) / file)
    return archives


def extract_archive(archive_path: Path, skip_if_corrupt: bool = True) -> bool:
    """
    Extract an archive file in place and remove the original.

    Parameters
    ----------
    archive_path : Path
        Path to the archive file to extract.
    skip_if_corrupt : bool, optional
        If True, skip corrupted archives instead of raising, by default True

    Returns
    -------
    bool
        True if extraction was successful and file was removed,
        False if extraction failed or was skipped.
    """
    archive_dir: Path = archive_path.parent
    print(f"Extracting {archive_path}...")

    # First try Python zipfile
    try:
        with zipfile.ZipFile(archive_path, "r", allowZip64=True) as zip_ref:
            # Extract all files to the same directory as the archive
            zip_ref.extractall(archive_dir)
        # Remove the original archive file after successful extraction
        archive_path.unlink()
        print(f"  Removed {archive_path}")
        return True
    except zipfile.BadZipFile:
        # If Python zipfile fails due to corruption, try unzip command
        # which is more tolerant of corrupted extra fields
        try:
            print(f"  Using unzip command (more tolerant of corruption)...")
            result = subprocess.run(
                ["unzip", "-q", "-o", str(archive_path), "-d", str(archive_dir)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0 or "warning" in result.stderr.lower():
                # unzip often returns 0 even with warnings, or non-zero but still extracts
                # Check if files were actually extracted
                if any(archive_dir.iterdir()):
                    archive_path.unlink()
                    print(f"  Removed {archive_path}")
                    return True
                else:
                    raise subprocess.CalledProcessError(
                        result.returncode, "unzip", result.stderr
                    )
            else:
                raise subprocess.CalledProcessError(
                    result.returncode, "unzip", result.stderr
                )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if skip_if_corrupt:
                print(f"  Skipping archive (extraction failed): {archive_path}")
                if isinstance(e, subprocess.CalledProcessError) and e.stderr:
                    print(f"    Error: {e.stderr[:100]}")
                return False
            else:
                raise
    except Exception as e:
        if skip_if_corrupt:
            print(f"  Skipping archive due to error: {archive_path} ({e})")
            return False
        else:
            raise


def find_powerpc_gcc(directory: Path = Path(".")) -> Optional[Path]:
    """
    Find PowerPC GCC compiler in the directory tree.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")

    Returns
    -------
    Optional[Path]
        Path to PowerPC GCC compiler if found, None otherwise.
    """
    # Look for Cross_Tools directories
    cross_tools_dirs = list(directory.rglob("Cross_Tools"))
    for cross_tools in cross_tools_dirs:
        # Look for GCC directories within Cross_Tools
        gcc_dirs = list(cross_tools.glob("gcc-*-powerpc*"))
        for gcc_dir in gcc_dirs:
            # Look for GCC binaries
            for bin_name in [
                "powerpc-eabi-gcc",
                "powerpc-eabivle-gcc",
                "powerpc-gcc",
                "gcc",
            ]:
                gcc_path = gcc_dir / "bin" / bin_name
                if gcc_path.exists() and gcc_path.is_file():
                    return gcc_path

    # Also search for PowerPC GCC directories by name pattern
    for gcc_dir in directory.rglob("powerpc-*-4_9"):
        # Look for GCC binaries in bin directory
        for bin_name in ["powerpc-eabi-gcc", "powerpc-eabivle-gcc", "powerpc-gcc"]:
            gcc_path = gcc_dir / "bin" / bin_name
            if gcc_path.exists() and gcc_path.is_file():
                return gcc_path

    # Also search for GCC executables directly (check if file, even if not executable)
    gcc_patterns = [
        "**/powerpc-eabi-gcc*",
        "**/powerpc-eabivle-gcc*",
        "**/powerpc-gcc*",
    ]
    for pattern in gcc_patterns:
        for gcc_path in directory.glob(pattern):
            if gcc_path.is_file():
                # Verify it's PowerPC GCC by checking path contains powerpc
                if "powerpc" in str(gcc_path).lower() and "gcc" in gcc_path.name.lower():
                    # Check if it's a GCC binary (not a man page or doc)
                    if gcc_path.suffix not in [".1", ".txt", ".pdf", ".html"]:
                        return gcc_path

    return None


def find_pegdbserver(directory: Path = Path(".")) -> Optional[Path]:
    """
    Find P&E GDB Server binary in the directory tree.

    Prefers Linux version over Windows version.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")

    Returns
    -------
    Optional[Path]
        Path to pegdbserver_power_console if found, None otherwise.
    """
    # Prefer Linux version
    server_binary_linux = directory / "plugins" / "com.pemicro.debug.gdbjtag.ppc_1.7.2.201709281658" / "lin" / "pegdbserver_power_console"
    if server_binary_linux.exists():
        return server_binary_linux

    # Also search recursively, preferring Linux paths
    linux_servers = []
    windows_servers = []
    other_servers = []

    for server_path in directory.rglob("pegdbserver_power_console*"):
        if server_path.is_file():
            path_str = str(server_path).lower()
            if "/lin/" in path_str or path_str.endswith("pegdbserver_power_console"):
                if not path_str.endswith(".exe"):
                    linux_servers.append(server_path)
            elif "/win" in path_str or path_str.endswith(".exe"):
                windows_servers.append(server_path)
            else:
                other_servers.append(server_path)

    # Return Linux version first, then others
    if linux_servers:
        return linux_servers[0]
    if other_servers:
        return other_servers[0]
    if windows_servers:
        return windows_servers[0]

    return None


def find_gdi_directory(directory: Path = Path(".")) -> Optional[Path]:
    """
    Find GDI directory for P&E GDB Server.

    Prefers Linux version over Windows version.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")

    Returns
    -------
    Optional[Path]
        Path to GDI directory if found, None otherwise.
    """
    # Prefer Linux version
    gdi_dir_linux = (
        directory
        / "plugins"
        / "com.pemicro.debug.gdbjtag.ppc_1.7.2.201709281658"
        / "lin"
        / "gdi"
    )
    if gdi_dir_linux.exists() and gdi_dir_linux.is_dir():
        return gdi_dir_linux

    # Search recursively for gdi directories, preferring Linux
    linux_gdi = []
    windows_gdi = []
    other_gdi = []

    for gdi_path in directory.rglob("gdi"):
        if gdi_path.is_dir() and (gdi_path / "P&E").exists():
            path_str = str(gdi_path).lower()
            if "/lin/" in path_str:
                linux_gdi.append(gdi_path)
            elif "/win" in path_str:
                windows_gdi.append(gdi_path)
            elif "pemicro" in path_str:
                other_gdi.append(gdi_path)

    # Return Linux version first
    if linux_gdi:
        return linux_gdi[0]
    if other_gdi:
        return other_gdi[0]
    if windows_gdi:
        return windows_gdi[0]

    return None


def check_targets_found(directory: Path = Path(".")) -> Tuple[bool, bool, bool]:
    """
    Check if all target components have been found.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")

    Returns
    -------
    Tuple[bool, bool, bool]
        Tuple of (gcc_found, gdb_server_found, gdi_found)
    """
    gcc_path = find_powerpc_gcc(directory)
    server_path = find_pegdbserver(directory)
    gdi_path = find_gdi_directory(directory)

    return (
        gcc_path is not None,
        server_path is not None,
        gdi_path is not None,
    )


def extract_until_targets(
    max_iterations: int = 200, exclude_patterns: List[str] = None
) -> None:
    """
    Recursively extract all archives until target components are found.

    Parameters
    ----------
    max_iterations : int, optional
        Maximum number of extraction rounds to prevent infinite loops,
        by default 200
    exclude_patterns : List[str], optional
        List of filename patterns to exclude from extraction, by default None

    Notes
    -----
    This function will continue extracting archives until:
    - All target components are found (PowerPC GCC, GDB server, GDI), or
    - max_iterations is reached (to prevent infinite loops)

    Each extracted archive may contain more archives, so the process repeats.
    Corrupted archives will be skipped to prevent infinite loops.
    """
    if exclude_patterns is None:
        exclude_patterns = ["installer_payload.zip"]
    iteration: int = 0
    extracted_count: int = 0
    skipped_files: Set[Path] = set()

    print("Extracting archives until targets are found...")
    print("Looking for:")
    print("  1. PowerPC GCC compiler (in Cross_Tools)")
    print("  2. P&E GDB Server (pegdbserver_power_console)")
    print("  3. GDI directory")
    print()

    while iteration < max_iterations:
        # Check if targets are already found
        gcc_found, server_found, gdi_found = check_targets_found()
        if gcc_found and server_found and gdi_found:
            print("\n" + "=" * 60)
            print("✓ All targets found!")
            gcc_path = find_powerpc_gcc()
            server_path = find_pegdbserver()
            gdi_path = find_gdi_directory()
            if gcc_path:
                print(f"✓ PowerPC GCC: {gcc_path}")
            if server_path:
                print(f"✓ GDB Server: {server_path}")
            if gdi_path:
                print(f"✓ GDI Directory: {gdi_path}")
            print(f"\nTotal archives extracted: {extracted_count}")
            return

        archives: List[Path] = find_archives(exclude_patterns=exclude_patterns)

        # Filter out previously skipped files
        archives = [arc for arc in archives if arc not in skipped_files]

        if not archives:
            print(f"\nNo more archives found.")
            break

        print(f"\nIteration {iteration + 1}: Found {len(archives)} archive(s)")

        for archive in archives:
            success: bool = extract_archive(archive, skip_if_corrupt=True)
            if success:
                extracted_count += 1
            else:
                # Track skipped files to avoid retrying them
                skipped_files.add(archive)

        iteration += 1

        # Print progress every 10 iterations
        if iteration % 10 == 0:
            gcc_found, server_found, gdi_found = check_targets_found()
            status = []
            if gcc_found:
                status.append("GCC")
            if server_found:
                status.append("GDB Server")
            if gdi_found:
                status.append("GDI")
            print(f"Progress: {', '.join(status) if status else 'None'} found")

    # Final status
    print(f"\n{'=' * 60}")
    print(f"Reached maximum iterations ({max_iterations}) or no more archives.")
    print(f"Total archives extracted: {extracted_count}")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} corrupted/problematic file(s)")

    gcc_found, server_found, gdi_found = check_targets_found()
    print(f"\nFinal status:")
    print(f"  PowerPC GCC: {'✓ Found' if gcc_found else '✗ Not found'}")
    if gcc_found:
        gcc_path = find_powerpc_gcc()
        print(f"    Location: {gcc_path}")
    print(f"  GDB Server: {'✓ Found' if server_found else '✗ Not found'}")
    if server_found:
        server_path = find_pegdbserver()
        print(f"    Location: {server_path}")
    print(f"  GDI Directory: {'✓ Found' if gdi_found else '✗ Not found'}")
    if gdi_found:
        gdi_path = find_gdi_directory()
        print(f"    Location: {gdi_path}")


if __name__ == "__main__":
    extract_until_targets()

