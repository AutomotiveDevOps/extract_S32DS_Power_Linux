#!/usr/bin/env python3
"""
Extract the installer payload from NXP S32DS Power Linux .bin installer.

The NXP installer is a self-extracting binary that contains a ZIP archive
starting at the first PK header (ZIP local file header signature: 0x50 0x4B 0x03 0x04).

This script:
1. Reads the .bin file
2. Finds the first PK header signature
3. Extracts everything from that offset to the end as installer_payload.zip

Examples
--------
>>> python3 extract_payload.py
offset: 12345
wrote installer_payload.zip

Notes
-----
The script assumes the .bin file is named:
S32DS_Power_Linux_v2017.R1_b171024.bin

Change the filename variable in the script if using a different version.
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

