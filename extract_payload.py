#!/usr/bin/env python3
"""
Extract the installer payload from NXP S32DS Power Linux .bin installer.

Purpose
-------
Extract the ZIP payload from the self-extracting `.bin` installer binary.

The NXP installer is a self-extracting binary that consists of:
1. A shell script header (handles Java checks, system requirements, etc.)
2. A ZIP archive payload starting at the first `PK\x03\x04` (ZIP local file header signature)

This script:
- Reads the `.bin` file and searches for the first ZIP file header signature
  (`PK\x03\x04`, which is `0x50 0x4B 0x03 0x04`)
- Extracts everything from that offset to the end of the file as `installer_payload.zip`
- This ZIP file contains all the actual installer components (JAR files, nested ZIPs,
  toolchain archives, etc.)

Usage
-----
.. code-block:: bash

    python3 extract_payload.py

Default behavior:
- Input: `S32DS_Power_Linux_v2017.R1_b171024.bin` (change the `input_filename`
  parameter in `extract_installer_payload()` for different versions)
- Output: `installer_payload.zip`

What it does
------------
1. Opens the `.bin` file in binary mode
2. Searches for the first occurrence of the ZIP signature `PK\x03\x04`
3. Writes everything from that offset to the end of the file as `installer_payload.zip`
4. Prints the offset where the ZIP payload starts

This is the **first step** in the extraction process. Once you have `installer_payload.zip`,
you can proceed to extract the nested archives within it using `extract_all_zips.py` or
`extract_until_targets.py`.

Examples
--------
.. code-block:: bash

    $ python3 extract_payload.py
    offset: 12345
    wrote installer_payload.zip

Notes
-----
The script assumes the .bin file is named:
    S32DS_Power_Linux_v2017.R1_b171024.bin

Change the `input_filename` parameter in the `extract_installer_payload()` function
if using a different version.

Raises
------
FileNotFoundError
    If the input `.bin` file does not exist.
ValueError
    If no PK header (`PK\x03\x04`) is found in the file.
"""

from typing import Optional


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
    return data.find(b'PK\x03\x04')


def extract_installer_payload(
    input_filename: str = "S32DS_Power_Linux_v2017.R1_b171024.bin",
    output_filename: str = "installer_payload.zip"
) -> None:
    """
    Extract the installer payload from NXP S32DS .bin installer.

    Parameters
    ----------
    input_filename : str, optional
        Path to the input .bin file, by default "S32DS_Power_Linux_v2017.R1_b171024.bin"
    output_filename : str, optional
        Path to the output ZIP file, by default "installer_payload.zip"

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    ValueError
        If no PK header is found in the file.
    """
    with open(input_filename, 'rb') as f:
        data: bytes = f.read()

    offset: Optional[int] = find_pk_header(data)

    if offset == -1:
        raise ValueError("No PK header found in the file")

    print(f"offset: {offset}")

    with open(output_filename, 'wb') as f:
        f.write(data[offset:])

    print(f"wrote {output_filename}")


if __name__ == "__main__":
    extract_installer_payload()

