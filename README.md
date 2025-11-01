# extract_S32DS_Power_Linux
Decrapify the NXP Install which is a dumpester fire in its own right.

## Downloading the Installer

The S32DS Power Linux installer (`.bin` file) is **not** included in this repository due to its size. You need to download it from NXP's website.

### Steps to Download

1. **Visit the NXP S32 Design Studio Page:**
   - Navigate to: https://www.nxp.com/design/design-center/software/development-software/s32-design-studio-ide/s32-design-studio-for-s32-platform:S32DS-S32PLATFORM

2. **Sign In or Register:**
   - Click "Sign In" at the top-right corner
   - If you don't have an account, select "Register" to create one (NXP account is required for downloads)

3. **Download the Installer:**
   - Once signed in, navigate to the "Downloads" section
   - Locate `S32DS_Power_Linux_v2017.R1_b171024.bin`
   - Click "Download" to obtain the installer file

4. **Place the File:**
   - Save the downloaded `.bin` file in this repository directory
   - The file should be named: `S32DS_Power_Linux_v2017.R1_b171024.bin`

## Extraction

Use the provided `extract_payload.py` script to extract the installer payload:

```bash
python3 extract_payload.py
```

This will create `installer_payload.zip` containing the extracted contents.
