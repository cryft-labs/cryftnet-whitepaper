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
**CRITICAL: The version header is hardcoded in `compile-whitepaper.py`**

When releasing a new version, you MUST update BOTH locations:

#### Step 1: Update the compile script header
Edit `compile-whitepaper.py` lines ~113-127 (the `front_matter` variable):

```python
front_matter = """<h1 align="center">CryftNet (Cryft Network) Whitepaper</h1>

<p align="center">
<strong>Revision:</strong> v1.XX<br>           # UPDATE VERSION NUMBER
<strong>Date:</strong> YYYY-MM-DD<br>          # UPDATE DATE
<strong>Status:</strong> Draft (Production Review Candidate)<br>
<strong>Authors:</strong> Cryft Labs (Draft)
</p>

<p align="center">
<strong>Latest Changes (v1.XX):</strong> [DESCRIBE NEW CHANGES]. Previous (v1.YY): [PREVIOUS MAJOR CHANGES]. Earlier (v1.ZZ): [EARLIER CHANGES].
</p>
```

**Best practice for Latest Changes:**
- Start with the new version's changes
- Include a brief summary of the previous version (v1.24, v1.23, etc.)
- Keep it concise but comprehensive
- Mention line counts for major additions
- Include section numbers for reference

#### Step 2: Update README.md version header
Edit `README.md` lines ~3-11 with matching version/date/changes.

#### Step 3: Add entry to README.md revision history
Add a new row to the revision history table in `README.md` with comprehensive details.

#### Step 4: Update individual source files (if needed)
If you're adding substantial content to specific sections, update those section files in `whitepaper/`.

#### Step 5: Compile
Run `python compile-whitepaper.py` to generate the final `whitepaper.md` with the updated header.

**Why this matters:** The compile script generates the header from scratch every time. If you only update `README.md` or source files, the compiled `whitepaper.md` will still have the old version from the script.

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
