# Extracting S32 Design Studio for Power Architecture: A Cautionary Tale

> **TL;DR**: NXP finally released the VLE GCC port after... *checks notes*... way too long. After jumping through too many hoops, dealing with Java hell, and contemplating whether Eclipse deserves to exist, we decided to take matters into our own hands. This repository contains scripts to extract the installer like a digital archaeologist and build a **sane toolchain installable with git** in 2025.

## The Corporate Software Experience™

You know the drill:

1. Download a multi-GB installer binary
2. Fight with Java version compatibility (because *of course* they bundled Java 1.6 or some cursed ancient version)
3. Realize the installer requires 47 different system dependencies that conflict with your existing setup
4. Discover it wants to install Eclipse (because who doesn't want to relive 2005?)
5. Find out you need activation keys, license agreements, and a blood sacrifice to the corporate overlords
6. Give up and decide to just extract the installer and use the actual tools directly

**This project is step 6.**

## Why This Exists

After too many hoops to get this installer running with Java issues, and the thought of ever touching Eclipse for free being repulsive, we just decided to ~~jailbreak~~ extract the installer and move forward in 2025 with a sane toolchain that:

- ✅ Can be installed with git (like civilized software)
- ✅ Doesn't require activation keys (because we own the hardware, dammit)
- ✅ Doesn't force Eclipse on us (because 2025)
- ✅ Actually works in a modern Linux environment
- ✅ Can be version-controlled and automated

## A Brief History Lesson (Because History Repeats Itself)

Before we dive into extracting this mess, let's talk about *why* you're stuck using a proprietary toolchain in the first place instead of just `apt-get install gcc-powerpc-vle` like a normal person.

### The VLE Saga: When GCC Said "Nah, Too Invasive"

Back in the day (circa 2012), CodeSourcery tried to merge PowerPC VLE (Variable Length Encoding) support into GCC mainline. This would have given us a proper open-source compiler for embedded PowerPC chips without needing $10,000 hardware dongles for smoke testing (looking at you, Green Hills).

**Here's what happened:**

- **Oct 2012**: CodeSourcery submitted their initial "[PATCH] PowerPC VLE port" to `gcc-patches`. Reviewers immediately started complaining about how "invasive" the changes were and how it would "complicate the common parts of the rs6000 port."

- **Mar 2013**: On `gcc@`, David Edelsohn delivered the verdict: full VLE support was **too invasive** and would "significantly complicate the common parts of the rs6000 port." Translation: "Your patch works, but we don't want it in our tree because reasons." They suggested *maybe* some less disruptive pieces could go in. (Source: [gcc.gnu.org](https://gcc.gnu.org))

- **2016-2017**: Binutils maintainers were more reasonable—they accepted VLE bits for BFD/opcodes as groundwork for a future GCC port. But the GCC port itself? Still nowhere to be seen. (Source: [sourceware.org](https://inbox.sourceware.org))

- **Result**: VLE support lived on in out-of-tree branches and forks (like `gcc-4.9.4` with VLE patches), maintained by NXP/CodeSourcery and the community, because FSF GCC proper wouldn't take it.

So here we are in 2025, extracting installers and dealing with Java hell, because someone decided that maintaining clean codebase boundaries was more important than supporting an entire embedded architecture properly. And now you have to choose between:
- Using an out-of-tree GCC fork (if you can find it)
- Paying for a proprietary toolchain with a dongle-based license system
- Dealing with this installer nightmare

**The moral of the story**: Sometimes the best patches get rejected not because they're wrong, but because they're "too invasive." Meanwhile, entire industries build around proprietary workarounds. But hey, at least the GCC maintainers' codebase stayed clean! 🎉

## Step 1: Download the Installer

**Looking for**: NXP Embedded GCC for Power Architecture, v4.9.4 build 1705 - Linux

**Source**: [NXP S32 Design Studio for Power Architecture](https://www.nxp.com/design/design-center/software/automotive-software-and-tools/s32-design-studio-ide/s32-design-studio-for-power-architecture:S32DS-PA)

Download the Linux installer binary. It's probably named something like `S32DS_Power_Linux_v*.bin` and weighs in at several hundred megabytes of corporate bloatware. Inside this installer, we're specifically hunting for the GCC 4.9.4 toolchain (build 1705) that should have been a simple tarball.

## Step 2: Extract the Installer (TBD)

*Work in progress* - The extraction scripts in this repository will help you:
- Extract the `.bin` installer format (which is usually just a shell script + payload)
- Find and extract the actual toolchain archives
- Organize the GCC toolchain, libraries, and headers into a sane directory structure
- Create a simple installation process that doesn't require Java, Eclipse, or your firstborn

## Current Status

This repository contains extraction scripts to:
- Recursively extract nested ZIP files (`extract_all_zips.py`)
- Extract specific payloads (`extract_payload.py`)
- Target specific components (`extract_until_targets.py`)

**Coming soon**: A proper install script that sets up the toolchain in `/usr/local` or a user directory, adds it to PATH, and lets you forget this installer ever existed.

## Contributing

Found a better way to extract this mess? Pull requests welcome. Bonus points if your solution requires fewer steps than the original installer.

## Disclaimer

This is an educational exercise in reverse-engineering corporate installers. We're not responsible if NXP's lawyers show up at your door demanding to know why you didn't use their official installer (though honestly, they probably don't care - we're just trying to use the *free* GCC toolchain that should have been distributed as a tarball in the first place).

---

*Made with ❤️ and a healthy dose of frustration with corporate software development tools.*

