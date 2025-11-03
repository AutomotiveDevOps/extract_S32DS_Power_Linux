# S32DS Power Linux Toolchain Extractor

> **One command. One .deb package. One toolchain ready to use.**
> 
> Extract the NXP S32 Design Studio for Power Architecture installer and package it as a clean, installable Debian package—no Java, no Eclipse, no activation keys, no corporate bloatware.

## The Problem This Solves

### The Burning Platform: Why You Can't Just `apt-get install gcc-powerpc-vle`

You need to compile code for PowerPC VLE (Variable Length Encoding) embedded systems. The architecture powers billions of devices—from Caterpillar engine control modules to automotive ECUs, industrial automation systems to aerospace controllers. But here's the reality:

**GCC mainline rejected PowerPC VLE support in 2013** as "too invasive." This left developers with three terrible options:

1. **Out-of-tree GCC 4.9 fork** (from 2016) - buried in corporate installers, hard to find, 11+ years old
2. **Proprietary toolchains** - $10,000+ per seat, hardware dongles, licensing nightmares (Green Hills, etc.)
3. **NXP's official installer** - multi-GB binary, requires Java 1.6, Eclipse bloatware, activation keys, and generally makes you question life choices

### What the Official Installer Experience Looks Like

1. Download a 1.1GB `.bin` installer binary
2. Fight with Java version compatibility (needs ancient Java 1.6 or 1.7)
3. Discover it requires 47 different system dependencies that conflict with modern Linux
4. Watch it try to install Eclipse (because who doesn't want to relive 2005?)
5. Fill out license agreements, activation forms, and corporate paperwork
6. Realize you just wanted the compiler, not a 500MB IDE
7. Give up and extract the installer manually

**This project solves steps 1-7 with one command.**

## What This Enables

### 🎯 Single Command Workflow

```bash
python3 extract_and_package.py
dpkg -i s32ds-power-linux_*.deb
```

That's it. No manual steps, no repeated JAR extraction, no hunting for components.

### ✅ What You Get

A complete, installable Debian package (`s32ds-power-linux_*.deb`) containing:

1. **PowerPC GCC Compiler** (`powerpc-eabivle-4.9`)
   - Full GCC 4.9.4 toolchain with VLE support
   - All standard tools: `gcc`, `g++`, `gdb`, `ld`, `objdump`, etc.
   - Installed to `/usr/local/s32ds-power-linux/powerpc-eabivle-4_9/`

2. **P&E Micro GDB Server**
   - `pegdbserver_power_console` for PowerPC debugging
   - Complete GDI (GDB Debug Interface) plugin system
   - Installed to `/usr/local/s32ds-power-linux/pegdbserver/`

3. **e200 EWL Runtime Library**
   - Embedded C/C++ standard library for PowerPC e200 cores
   - Complete headers and runtime components
   - Installed to `/usr/local/s32ds-power-linux/e200_ewl2/`

4. **USB Drivers**
   - udev rules for P&E Micro debugging hardware (`58-pemicro.rules`)
   - USB library (`libp64-0.1.so.4`)
   - Automatically installed to system locations via package postinst script

### 🚀 What This Enables

- **Version Control**: Toolchain can be committed to git, versioned, and distributed
- **CI/CD Integration**: Automate toolchain installation in build pipelines
- **Containerization**: Include toolchain in Docker images without bloated installers
- **Reproducible Builds**: Same toolchain version across all developers and build systems
- **No Java Required**: Pure Python extraction, no runtime dependencies
- **Modern Linux Support**: Works on current distributions without compatibility hacks
- **Clean Installation**: Standard Debian package management, easy uninstall
- **System Integration**: USB drivers automatically configured via udev rules

## The Burning Platform: Historical Context

### The VLE Saga: When GCC Said "Nah, Too Invasive"

Back in 2012, CodeSourcery tried to merge PowerPC [VLE (Variable Length Encoding)](https://en.wikipedia.org/wiki/PowerPC#Variable_Length_Encoding) support into GCC mainline. VLE is part of the [Power ISA Book E](https://en.wikipedia.org/wiki/Power_ISA#Book_E) specification, designed specifically for embedded systems.

**Here's what happened:**

- **Oct 2012**: CodeSourcery submitted "[PATCH] PowerPC VLE port" to `gcc-patches`. Reviewers complained about "invasive" changes.

- **Mar 2013**: GCC maintainer David Edelsohn delivered the verdict: full VLE support was **too invasive** and would "significantly complicate the common parts of the rs6000 port." Translation: "Your patch works, but we don't want it in our tree."

- **2016-2017**: Binutils maintainers accepted VLE bits for BFD/opcodes, but the GCC port itself remained out-of-tree.

- **Result**: VLE support exists only in out-of-tree branches (like `gcc-4.9.4` with VLE patches), maintained by NXP/CodeSourcery. Millions of embedded developers are stuck with ancient compilers or expensive proprietary alternatives.

### The Scale of the Problem

- **Over 1 billion Power Architecture chips** shipped since 1991
- **Every Caterpillar ECM** runs PowerPC—every construction site, mining operation, ship, generator
- **Nearly every 2009 GM North America vehicle** had PowerPC processors in engine controllers
- **$4.4 billion microprocessor market** (as of 2010), #1 in 32-bit processors
- **Hardware still shipping in 2040s**: NXP guarantees 15-20 year availability for development boards

All of this, and GCC mainline said the VLE patch was "too invasive." So here we are in 2025, extracting installers because the free toolchain should have been a tarball.

### The Proprietary Alternative

When GCC rejected VLE support, proprietary vendors filled the vacuum:

- **Green Hills Software**: "If you have to ask, you can't afford it" — toolchains costing tens of thousands per seat, hardware dongles
- **diab Compiler**: Chosen for IP protection (non-GPL), not performance
- **Wind River**: Acquired by Intel for $884M (2009), sold to TPG for billions (2022)

The "burning platform" isn't just GCC's rejection—it's an ecosystem forcing developers into expensive, proprietary tools when open-source alternatives could work perfectly fine.

## Installation and Usage

### Prerequisites

- Python 3.6+ (no other dependencies required)
- `unzip` command-line tool (for handling corrupted ZIP files)
- `dpkg-deb` (standard on Debian/Ubuntu systems, or install `dpkg-dev`)

### Quick Start

1. **Download the installer**:
   - Get `S32DS_Power_Linux_v*.bin` from [NXP S32 Design Studio](https://www.nxp.com/design/design-center/software/automotive-software-and-tools/s32-design-studio-ide/s32-design-studio-for-power-architecture:S32DS-PA)
   - Place it in this repository directory

2. **Extract and package**:
   ```bash
   python3 extract_and_package.py
   ```
   
   Or use the Makefile:
   ```bash
   make
   ```

3. **Install the package**:
   ```bash
   sudo dpkg -i s32ds-power-linux_*.deb
   ```

4. **Use the toolchain**:
   ```bash
   /usr/local/s32ds-power-linux/powerpc-eabivle-4_9/bin/powerpc-eabivle-gcc --version
   ```

### Command-Line Options

```bash
python3 extract_and_package.py [input.bin] [--version VERSION] [--output OUTPUT.deb]
```

- **`input.bin`**: Path to the `.bin` installer file (auto-detected if not provided)
- **`--version VERSION`**: Package version string (default: `2017.1`)
- **`--output OUTPUT.deb`**: Output `.deb` filename (default: `s32ds-power-linux_VERSION_amd64.deb`)

**Examples:**

```bash
# Auto-detect .bin file, use defaults
python3 extract_and_package.py

# Specify input file and version
python3 extract_and_package.py S32DS_Power_Linux_v2017.R1_b171024.bin --version 2017.1

# Custom output filename
python3 extract_and_package.py --output my-toolchain.deb
```

## How It Works

### Extraction Workflow

The script performs a complete extraction and packaging workflow:

1. **Extract `.bin` → `payload.zip`**
   - Finds the ZIP payload at the first `PK\x03\x04` signature (ZIP header)
   - Extracts everything from that offset to end of file

2. **Extract `payload.zip` → `installer/`**
   - Extracts the installer payload to `installer/` directory
   - Uses `unzip` command (more tolerant of corrupted ZIP files than Python's zipfile)

3. **Extract JAR files (3 iterations)**
   - Finds all `.jar` files within `installer/` directory
   - Extracts each JAR to a directory with the same name (without `.jar` extension)
   - Removes the original JAR file
   - **Loops automatically** until no more JARs are found (handles nested JARs)
   - Typically requires 2-3 iterations as nested JARs are extracted

4. **Extract remaining ZIP files**
   - Finds and extracts any remaining `.zip` files recursively
   - Handles corrupted ZIP files gracefully

5. **Locate deliverables**
   - Searches for:
     - PowerPC compiler: `powerpc-eabivle-4_9` directory
     - GDB server: `pegdbserver_power_console` binary in Eclipse plugin
     - EWL runtime: `e200_ewl2` directory
     - USB drivers: `libusb_64_32` directory with udev rules

6. **Build DEB package**
   - Creates package structure in temporary directory
   - Copies deliverables to `/usr/local/s32ds-power-linux/`
   - Generates Debian control files (`control`, `postinst`)
   - Packages with `dpkg-deb`

### Package Structure

The resulting `.deb` package installs to:

```
/usr/local/s32ds-power-linux/
├── powerpc-eabivle-4_9/          # GCC compiler toolchain
│   ├── bin/                       # All compiler binaries
│   ├── lib/                       # Libraries
│   ├── include/                   # Headers
│   └── share/                     # Documentation, man pages
├── pegdbserver/                   # P&E GDB server
│   ├── pegdbserver_power_console  # Main server binary
│   └── gdi/                       # GDB Debug Interface plugins
├── e200_ewl2/                     # EWL runtime library
│   ├── EWL_C/                     # C runtime
│   ├── EWL_C++/                   # C++ runtime
│   └── EWL_Runtime/               # Runtime components
└── drivers/                       # USB drivers (reference)
    ├── 58-pemicro.rules           # udev rules
    └── libp64-0.1.so.4            # USB library
```

### Post-Install Script

The package includes a `postinst` script that automatically:

1. Copies `58-pemicro.rules` to `/lib/udev/rules.d/`
2. Copies `libp64-0.1.so.4` to `/usr/lib/`
3. Reloads udev rules (`udevadm control --reload-rules`)
4. Runs `ldconfig` to register the USB library

This enables P&E Micro debugging hardware to work immediately after installation.

## Technical Details

### Why Not Python's zipfile Module?

The installer ZIP files contain corrupted "extra fields" that Python's `zipfile` module cannot handle (raises `BadZipFile: Corrupt extra field`). The script uses the system `unzip` command as a fallback, which is more tolerant of these corruptions.

### Directory Scoping

All extraction is scoped to the `installer/` directory only. The script:
- Extracts payload ZIP to `installer/`
- Searches for JAR/ZIP files only within `installer/`
- Never touches files outside the extraction directory

This prevents accidental extraction of unrelated archives in the project directory.

### Nested JAR Handling

JAR files can contain nested JAR files, which themselves can contain more JAR files. The script automatically loops:
- **Iteration 1**: Extracts top-level JARs
- **Iteration 2**: Extracts JARs that were inside the first JARs
- **Iteration 3**: Extracts JARs that were nested even deeper
- Continues until no more JARs are found

The script handles this automatically—no manual repetition required.

## Repository Structure

```
extract_S32DS_Power_Linux/
├── extract_and_package.py    # Main extraction and packaging script
├── Makefile                   # Convenience wrapper (optional)
├── README.md                  # This file
├── LICENSE                    # License information
└── S32DS_Power_Linux_*.bin    # Installer file (you download this)
```

### Generated Files (can be cleaned up)

- `installer/` - Extracted installer directory (temporary, removed by `make clean`)
- `installer_payload.zip` - Intermediate ZIP payload (temporary)
- `s32ds-power-linux_*.deb` - Final Debian package (keep this!)

## Cleaning Up

Remove temporary extraction files:

```bash
make clean
```

Or manually:

```bash
rm -rf installer installer_payload.zip
```

The `.deb` package is kept (it's the final product).

## Troubleshooting

### "No .bin file found"

Place the `.bin` installer file in the repository directory, or specify the path:

```bash
python3 extract_and_package.py /path/to/S32DS_Power_Linux_v*.bin
```

### "BadZipFile: Corrupt extra field"

This is normal—the script automatically uses `unzip` command as a fallback. Make sure `unzip` is installed:

```bash
sudo apt-get install unzip  # Debian/Ubuntu
```

### "Deliverables not found"

If extraction completes but deliverables aren't found, the installer structure may have changed. Check the extracted `installer/` directory structure and verify paths in `find_deliverables()` function.

### Package installation fails

Check that `dpkg-deb` is available:

```bash
sudo apt-get install dpkg-dev  # Debian/Ubuntu
```

## Contributing

Found a better way to extract this? Improvements welcome! Areas that could use help:

- Support for newer installer versions
- Detection of installer structure changes
- Additional package formats (RPM, tarball)
- CI/CD integration examples

## License

See `LICENSE` file. This tool extracts and repackages NXP's toolchain for easier distribution. The extracted toolchain itself remains under NXP's license terms.

## Disclaimer

This is an educational tool to extract and repackage the free GCC toolchain that NXP distributes. We're not responsible if NXP's lawyers show up at your door (though honestly, they probably don't care—we're just trying to use the *free* toolchain that should have been a tarball in the first place).

The toolchain extracted here is the same free GCC 4.9.4 with VLE support that NXP provides—just packaged in a sane, installable format instead of buried in a multi-GB installer with Java and Eclipse.

---

*Made with ❤️ and a healthy dose of frustration with corporate software development tools.*

**From installer hell to one command. From corporate bloatware to clean Debian packages. This is what proper toolchain distribution should look like.**
