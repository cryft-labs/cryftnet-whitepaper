# CryftNet Whitepaper Maintenance Instructions

## Overview
The whitepaper is compiled from individual section files in the `whitepaper/` directory. All edits should be made to the section files, NOT directly to `whitepaper.md`.

## Workflow

### 1. Making Changes
Edit the appropriate section file in the `whitepaper/` directory:
- `whitepaper/01-abstract.md`
- `whitepaper/02-design-goals.md`
- `whitepaper/03-background.md`
- etc.

### 2. Compiling the Whitepaper
**ALWAYS run the compile script after making changes:**

```bash
python compile-whitepaper.py
```

This script will:
- Fix UTF-8 encoding issues in source files
- Compile all sections into a single `whitepaper.md` file
- Display compilation statistics

### 3. Version Updates
When updating the revision number or date:
1. Edit the header section in the appropriate source file (typically the first section)
2. Update the "Latest Changes" summary to describe the changes
3. Run `python compile-whitepaper.py`

## Encoding Fixes
The compile script automatically fixes malformed UTF-8 characters:
- Corrupted arrows (→, ←, ↔) → ASCII equivalents (->, <-, <->)
- Corrupted em-dashes (—) → double hyphens (--)
- Box drawing characters → ASCII equivalents
- Malformed symbols → readable replacements

**Never edit `whitepaper.md` directly** - all fixes are applied during compilation from the source files.

## File Structure
```
cryftnet-whitepaper/
├── compile-whitepaper.py    # Main compilation script
├── whitepaper.md            # Compiled output (DO NOT EDIT)
├── INSTRUCTIONS.md          # This file
└── whitepaper/              # Source files (EDIT THESE)
    ├── 01-abstract.md
    ├── 02-design-goals.md
    ├── 03-background.md
    └── ... (more section files)
```

## Quick Reference
- **Edit:** Files in `whitepaper/` directory
- **Compile:** `python compile-whitepaper.py`
- **Output:** `whitepaper.md` (generated, do not edit)
