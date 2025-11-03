#!/usr/bin/env python3
"""
Extract S32DS Power Linux installer and package into .deb.

This script performs the complete extraction and packaging workflow:
1. Extract .bin → payload.zip
2. Extract payload.zip → installer/
3. Loop: extract all JARs until none remain
4. Extract all remaining ZIPs recursively
5. Collect deliverables (compiler, GDB server, EWL runtime, drivers)
6. Build .deb package structure
7. Create DEB control files and postinst
8. Package with dpkg-deb

Usage
-----
.. code-block:: bash

    python3 extract_and_package.py [input.bin]

Default behavior:
- Input: Automatically finds .bin file in current directory
- Output: s32ds-power-linux_*.deb in current directory

Raises
------
FileNotFoundError
    If the input .bin file does not exist.
ValueError
    If no PK header is found in the .bin file.
"""

import argparse
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Set, Tuple


def find_bin_file() -> Optional[Path]:
    """
    Find the first .bin file in the current directory.

    Returns
    -------
    Optional[Path]
        Path to .bin file if found, None otherwise.
    """
    for file in Path(".").glob("*.bin"):
        return file
    return None


def find_pk_header(data: bytes) -> Optional[int]:
    """
    Find the first PK header (ZIP local file header signature) in binary data.

    Parameters
    ----------
    data : bytes
        Binary data to search in.

    Returns
    -------
    Optional[int]
        Offset of the first PK header, or None if not found.
    """
    offset: int = data.find(b'PK\x03\x04')
    return offset if offset != -1 else None


def extract_payload_from_bin(input_bin: Path, output_zip: Path) -> None:
    """
    Extract the ZIP payload from NXP S32DS .bin installer.

    Parameters
    ----------
    input_bin : Path
        Path to the input .bin file.
    output_zip : Path
        Path to the output ZIP file.

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    ValueError
        If no PK header is found in the file.
    """
    print(f"Extracting payload from {input_bin}...")
    with open(input_bin, 'rb') as f:
        data: bytes = f.read()

    offset: Optional[int] = find_pk_header(data)

    if offset is None:
        raise ValueError("No PK header found in the file")

    print(f"  Found ZIP payload at offset: {offset}")

    with open(output_zip, 'wb') as f:
        f.write(data[offset:])

    print(f"  Extracted to {output_zip}")


def extract_zip_file(zip_path: Path, output_dir: Path) -> None:
    """
    Extract a ZIP file to the specified directory.

    Parameters
    ----------
    zip_path : Path
        Path to the ZIP file to extract.
    output_dir : Path
        Directory to extract to.

    Raises
    ------
    zipfile.BadZipFile
        If the ZIP file is corrupted and unzip also fails.
    """
    try:
        with zipfile.ZipFile(zip_path, "r", allowZip64=True) as zip_ref:
            zip_ref.extractall(output_dir)
    except zipfile.BadZipFile:
        # Fallback to unzip command which is more tolerant of corrupted extra fields
        print(f"  Using unzip command (more tolerant of corruption)...")
        result: subprocess.CompletedProcess = subprocess.run(
            ["unzip", "-q", "-o", str(zip_path), "-d", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            # unzip often returns non-zero but still extracts files
            # Check if files were actually extracted by checking if output_dir has content
            if not any(output_dir.iterdir()):
                raise zipfile.BadZipFile(f"Failed to extract {zip_path}: {result.stderr}")


def find_jar_files(directory: Path = Path(".")) -> List[Path]:
    """
    Find all JAR files in the directory and subdirectories.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")

    Returns
    -------
    List[Path]
        List of paths to JAR files found.
    """
    jar_files: List[Path] = []
    for root, dirs, files in os.walk(directory):
        # Skip .git directory
        if ".git" in root:
            continue
        for file in files:
            if file.endswith(".jar"):
                jar_files.append(Path(root) / file)
    return jar_files


def extract_jar(jar_path: Path, skip_if_corrupt: bool = True) -> bool:
    """
    Extract a JAR file in place and remove the original.

    Parameters
    ----------
    jar_path : Path
        Path to the JAR file to extract.
    skip_if_corrupt : bool, optional
        If True, skip corrupted JAR files instead of raising, by default True

    Returns
    -------
    bool
        True if extraction was successful and file was removed,
        False if extraction failed or was skipped.
    """
    jar_dir: Path = jar_path.parent
    dest_dir: Path = jar_path.with_suffix("")

    try:
        with zipfile.ZipFile(jar_path, "r", allowZip64=True) as jar_ref:
            jar_ref.extractall(dest_dir)
        jar_path.unlink()
        return True
    except zipfile.BadZipFile:
        # Fallback to unzip command which is more tolerant of corrupted extra fields
        try:
            result: subprocess.CompletedProcess = subprocess.run(
                ["unzip", "-q", "-o", str(jar_path), "-d", str(dest_dir)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0 or any(dest_dir.iterdir()):
                jar_path.unlink()
                return True
            else:
                if skip_if_corrupt:
                    print(f"  Warning: Skipping corrupted JAR: {jar_path}")
                    return False
                else:
                    raise zipfile.BadZipFile(f"Failed to extract {jar_path}: {result.stderr}")
        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            if skip_if_corrupt:
                print(f"  Warning: Skipping corrupted JAR: {jar_path} ({e})")
                return False
            else:
                raise
    except Exception as e:
        if skip_if_corrupt:
            print(f"  Warning: Skipping corrupted JAR: {jar_path} ({e})")
            return False
        else:
            raise


def extract_all_jars(directory: Path = Path("."), max_iterations: int = 200) -> None:
    """
    Recursively extract all JAR files until none remain.

    Parameters
    ----------
    directory : Path, optional
        Directory to search for JAR files in, by default Path(".")
    max_iterations : int, optional
        Maximum number of extraction rounds to prevent infinite loops,
        by default 200

    Notes
    -----
    This function will continue extracting JAR files until:
    - No more JAR files are found, or
    - max_iterations is reached (to prevent infinite loops)
    """
    iteration: int = 0
    extracted_count: int = 0
    skipped_files: Set[Path] = set()

    print("\nExtracting JAR files...")

    while iteration < max_iterations:
        jar_files: List[Path] = find_jar_files(directory)
        jar_files = [jf for jf in jar_files if jf not in skipped_files]

        if not jar_files:
            print(f"\n  No more JAR files found. Extraction complete.")
            print(f"  Total JARs extracted: {extracted_count}")
            return

        if iteration == 0 or len(jar_files) > 0:
            print(f"  Iteration {iteration + 1}: Found {len(jar_files)} JAR file(s)")

        for jar_file in jar_files:
            success: bool = extract_jar(jar_file, skip_if_corrupt=True)
            if success:
                extracted_count += 1
            else:
                skipped_files.add(jar_file)

        iteration += 1

    print(f"\n  Warning: Reached maximum iterations ({max_iterations})")
    print(f"  Total JARs extracted: {extracted_count}")


def find_zip_files(directory: Path = Path("."), exclude_patterns: List[str] = None) -> List[Path]:
    """
    Find all ZIP files in the directory and subdirectories.

    Parameters
    ----------
    directory : Path, optional
        Directory to search in, by default Path(".")
    exclude_patterns : List[str], optional
        List of filename patterns to exclude, by default None

    Returns
    -------
    List[Path]
        List of paths to ZIP files found.
    """
    if exclude_patterns is None:
        exclude_patterns = ["installer_payload.zip"]
    zip_files: List[Path] = []
    for root, dirs, files in os.walk(directory):
        # Skip .git directory
        if ".git" in root:
            continue
        for file in files:
            if file.endswith(".zip"):
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
    """
    zip_dir: Path = zip_path.parent

    try:
        with zipfile.ZipFile(zip_path, "r", allowZip64=True) as zip_ref:
            zip_ref.extractall(zip_dir)
        zip_path.unlink()
        return True
    except (zipfile.BadZipFile, Exception) as e:
        if skip_if_corrupt:
            print(f"  Warning: Skipping corrupted ZIP: {zip_path} ({e})")
            return False
        else:
            raise


def extract_all_zips(directory: Path = Path("."), max_iterations: int = 100) -> None:
    """
    Recursively extract all ZIP files until none remain.

    Parameters
    ----------
    directory : Path, optional
        Directory to search for ZIP files in, by default Path(".")
    max_iterations : int, optional
        Maximum number of extraction rounds to prevent infinite loops,
        by default 100
    """
    iteration: int = 0
    extracted_count: int = 0
    skipped_files: Set[Path] = set()

    print("\nExtracting ZIP files...")

    while iteration < max_iterations:
        zip_files: List[Path] = find_zip_files(directory, exclude_patterns=["installer_payload.zip"])
        zip_files = [zf for zf in zip_files if zf not in skipped_files]

        if not zip_files:
            print(f"\n  No more ZIP files found. Extraction complete.")
            print(f"  Total ZIPs extracted: {extracted_count}")
            return

        if iteration == 0 or len(zip_files) > 0:
            print(f"  Iteration {iteration + 1}: Found {len(zip_files)} ZIP file(s)")

        for zip_file in zip_files:
            success: bool = extract_zip(zip_file, skip_if_corrupt=True)
            if success:
                extracted_count += 1
            else:
                skipped_files.add(zip_file)

        iteration += 1

    print(f"\n  Warning: Reached maximum iterations ({max_iterations})")
    print(f"  Total ZIPs extracted: {extracted_count}")


def find_deliverables(installer_dir: Path) -> Tuple[Optional[Path], Optional[Path], Optional[Path], Optional[Path]]:
    """
    Find all deliverable components in the extracted installer structure.

    Parameters
    ----------
    installer_dir : Path
        Path to the installer directory.

    Returns
    -------
    Tuple[Optional[Path], Optional[Path], Optional[Path], Optional[Path]]
        Tuple of (compiler_path, gdb_server_path, ewl_path, drivers_path)
        Returns None for any component not found.
    """
    # Try the expected layout structure first
    layout_dir: Path = installer_dir / "C_" / "MakingInstalers" / "Layout"
    
    # PowerPC compiler - search for powerpc-eabivle-4_9 directory
    compiler_path: Optional[Path] = None
    if layout_dir.exists():
        compiler_path = layout_dir / "Cross_Tools_zg_ia_sf" / "powerpc-eabivle-4_9"
        if not compiler_path.exists():
            compiler_path = None
    
    # If not found in expected location, search recursively
    if compiler_path is None or not compiler_path.exists():
        for path in installer_dir.rglob("powerpc-eabivle-4_9"):
            if path.is_dir() and (path / "bin" / "powerpc-eabivle-gcc").exists():
                compiler_path = path
                break

    # P&E GDB server (find the lin directory in the plugin)
    gdb_server_path: Optional[Path] = None
    if layout_dir.exists():
        plugin_base: Path = layout_dir / "eclipse_zg_ia_sf" / "plugins"
        if plugin_base.exists():
            for plugin_dir in plugin_base.glob("com.pemicro.debug.gdbjtag.ppc_*"):
                lin_dir: Path = plugin_dir / "lin"
                if lin_dir.exists() and (lin_dir / "pegdbserver_power_console").exists():
                    gdb_server_path = lin_dir
                    break
    
    # If not found, search recursively
    if gdb_server_path is None:
        for lin_path in installer_dir.rglob("lin"):
            if (lin_path / "pegdbserver_power_console").exists():
                gdb_server_path = lin_path
                break

    # e200_ewl2 runtime
    ewl_path: Optional[Path] = None
    if layout_dir.exists():
        ewl_path = layout_dir / "S32DS_zg_ia_sf" / "e200_ewl2"
        if not ewl_path.exists():
            ewl_path = None
    
    # If not found, search recursively
    if ewl_path is None or not ewl_path.exists():
        for path in installer_dir.rglob("e200_ewl2"):
            if path.is_dir() and (path / "EWL_C").exists():
                ewl_path = path
                break

    # USB drivers
    drivers_path: Optional[Path] = None
    if layout_dir.exists():
        drivers_path = layout_dir / "Drivers_zg_ia_sf" / "libusb_64_32"
        if not drivers_path.exists():
            drivers_path = None
    
    # If not found, search recursively
    if drivers_path is None or not drivers_path.exists():
        for path in installer_dir.rglob("libusb_64_32"):
            if path.is_dir() and (path / "58-pemicro.rules").exists():
                drivers_path = path
                break

    return compiler_path, gdb_server_path, ewl_path, drivers_path


def create_deb_structure(
    deb_dir: Path,
    compiler_path: Optional[Path],
    gdb_server_path: Optional[Path],
    ewl_path: Optional[Path],
    drivers_path: Optional[Path],
) -> None:
    """
    Create the DEB package structure and copy deliverables.

    Parameters
    ----------
    deb_dir : Path
        Temporary directory for building the DEB package.
    compiler_path : Optional[Path]
        Path to PowerPC compiler directory.
    gdb_server_path : Optional[Path]
        Path to P&E GDB server lin directory.
    ewl_path : Optional[Path]
        Path to e200_ewl2 directory.
    drivers_path : Optional[Path]
        Path to USB drivers directory.
    """
    install_prefix: Path = deb_dir / "usr" / "local" / "s32ds-power-linux"

    print("\nCreating DEB package structure...")

    if compiler_path and compiler_path.exists():
        print(f"  Copying compiler: {compiler_path.name}")
        shutil.copytree(compiler_path, install_prefix / "powerpc-eabivle-4_9")

    if gdb_server_path and gdb_server_path.exists():
        print(f"  Copying GDB server")
        shutil.copytree(gdb_server_path, install_prefix / "pegdbserver")

    if ewl_path and ewl_path.exists():
        print(f"  Copying EWL runtime: {ewl_path.name}")
        shutil.copytree(ewl_path, install_prefix / "e200_ewl2")

    if drivers_path and drivers_path.exists():
        print(f"  Copying USB drivers")
        drivers_dest: Path = install_prefix / "drivers"
        drivers_dest.mkdir(parents=True, exist_ok=True)
        for item in drivers_path.iterdir():
            if item.is_file():
                shutil.copy2(item, drivers_dest / item.name)


def create_deb_control_files(deb_dir: Path, version: str = "2017.1") -> None:
    """
    Create DEB control files (control, postinst).

    Parameters
    ----------
    deb_dir : Path
        Temporary directory for building the DEB package.
    version : str, optional
        Package version, by default "2017.1"
    """
    debian_dir: Path = deb_dir / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)

    # Create control file
    control_content: str = f"""Package: s32ds-power-linux
Version: {version}
Architecture: amd64
Maintainer: Automated Extraction
Description: NXP S32 Design Studio for Power Architecture - Extracted Toolchain
 Extracted toolchain containing:
  - PowerPC GCC compiler (eabivle-4.9)
  - P&E GDB server for PowerPC debugging
  - e200 EWL runtime library
  - USB drivers for P&E Micro debugging hardware
"""
    with open(debian_dir / "control", "w") as f:
        f.write(control_content)

    # Create postinst script
    postinst_content: str = """#!/bin/bash
set -e

# Install udev rules for P&E Micro USB devices
if [ -f /usr/local/s32ds-power-linux/drivers/58-pemicro.rules ]; then
    cp -f /usr/local/s32ds-power-linux/drivers/58-pemicro.rules /lib/udev/rules.d/
    
    # Reload udev rules
    if [ -e /sbin/udevadm ]; then
        /sbin/udevadm control --reload-rules
    elif [ -e /sbin/udevcontrol ]; then
        /sbin/udevcontrol reload_rules
    fi
    
    chmod 644 /lib/udev/rules.d/58-pemicro.rules
fi

# Install USB library
if [ -f /usr/local/s32ds-power-linux/drivers/libp64-0.1.so.4 ]; then
    if [ ! -d /usr/lib ]; then
        echo "Warning: /usr/lib does not exist"
    else
        cp -f /usr/local/s32ds-power-linux/drivers/libp64-0.1.so.4 /usr/lib/
        /sbin/ldconfig
    fi
fi

exit 0
"""
    postinst_path: Path = debian_dir / "postinst"
    with open(postinst_path, "w") as f:
        f.write(postinst_content)
    postinst_path.chmod(0o755)


def build_deb_package(deb_dir: Path, output_path: Path, version: str = "2017.1") -> None:
    """
    Build the final .deb package using dpkg-deb.

    Parameters
    ----------
    deb_dir : Path
        Temporary directory containing the DEB structure.
    output_path : Path
        Path where the .deb file should be created.
    version : str, optional
        Package version, by default "2017.1"
    """
    print(f"\nBuilding .deb package...")

    cmd: List[str] = [
        "dpkg-deb",
        "--build",
        str(deb_dir),
        str(output_path),
    ]

    result: subprocess.CompletedProcess = subprocess.run(
        cmd, capture_output=True, text=True, check=True
    )

    print(f"  Created: {output_path}")


def main() -> None:
    """
    Main extraction and packaging workflow.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Extract S32DS Power Linux installer and package into .deb"
    )
    parser.add_argument(
        "input_bin",
        nargs="?",
        help="Path to .bin installer file (auto-detected if not provided)",
    )
    parser.add_argument(
        "--version",
        default="2017.1",
        help="Package version (default: 2017.1)",
    )
    parser.add_argument(
        "--output",
        help="Output .deb filename (default: s32ds-power-linux_VERSION.deb)",
    )

    args: argparse.Namespace = parser.parse_args()

    # Find input .bin file
    if args.input_bin:
        input_bin: Path = Path(args.input_bin)
    else:
        input_bin = find_bin_file()
        if input_bin is None:
            print("Error: No .bin file found. Please specify input file.")
            return

    if not input_bin.exists():
        print(f"Error: Input file does not exist: {input_bin}")
        return

    # Determine output .deb filename
    if args.output:
        output_deb: Path = Path(args.output)
    else:
        output_deb = Path(f"s32ds-power-linux_{args.version}_amd64.deb")

    print(f"Input: {input_bin}")
    print(f"Output: {output_deb}\n")

    # Step 1: Extract .bin → payload.zip
    payload_zip: Path = Path("installer_payload.zip")
    extract_payload_from_bin(input_bin, payload_zip)

    # Step 2: Extract payload.zip → installer/
    installer_dir: Path = Path("installer")
    if installer_dir.exists():
        print(f"\nRemoving existing installer directory...")
        shutil.rmtree(installer_dir)
    installer_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nExtracting payload to installer/...")
    extract_zip_file(payload_zip, installer_dir)
    
    payload_zip.unlink()  # Remove payload zip after extraction

    # Step 3: Extract all JARs (loop until none remain)
    extract_all_jars(installer_dir)

    # Step 4: Extract all remaining ZIPs
    extract_all_zips(installer_dir)

    # Step 5: Find deliverables
    print("\nLocating deliverables...")
    compiler_path, gdb_server_path, ewl_path, drivers_path = find_deliverables(
        installer_dir
    )

    if compiler_path:
        print(f"  ✓ Compiler: {compiler_path}")
    else:
        print("  ✗ Compiler: Not found")

    if gdb_server_path:
        print(f"  ✓ GDB Server: {gdb_server_path}")
    else:
        print("  ✗ GDB Server: Not found")

    if ewl_path:
        print(f"  ✓ EWL Runtime: {ewl_path}")
    else:
        print("  ✗ EWL Runtime: Not found")

    if drivers_path:
        print(f"  ✓ USB Drivers: {drivers_path}")
    else:
        print("  ✗ USB Drivers: Not found")

    # Step 6-8: Build .deb package
    with tempfile.TemporaryDirectory() as temp_dir:
        deb_dir: Path = Path(temp_dir) / "deb-build"
        deb_dir.mkdir(parents=True, exist_ok=True)

        create_deb_structure(deb_dir, compiler_path, gdb_server_path, ewl_path, drivers_path)
        create_deb_control_files(deb_dir, args.version)
        build_deb_package(deb_dir, output_deb, args.version)

    print(f"\n✓ Complete! Package created: {output_deb}")


if __name__ == "__main__":
    main()

