#!/usr/bin/env python3
"""
Compile whitepaper.md from individual section files with encoding fixes.
Usage: python compile-whitepaper.py
"""

import os
from pathlib import Path
import re

# Encoding fixes: problematic Unicode -> ASCII equivalents
ENCODING_FIXES = {
    '\u2014': '--',      # em dash (—)
    '\u2192': '->',      # rightwards arrow (→)
    '\u2190': '<-',      # leftwards arrow (←)
    '\u2194': '<->',     # left right arrow (↔)
    '\u2200': 'for all', # for all (∀)
    '\u2211': 'sum',     # n-ary summation (Σ)
    '\u2265': '>=',      # greater-than or equal to (≥)
    '\u2264': '<=',      # less-than or equal to (≤)
    '\u2018': "'",       # left single quote (')
    '\u2019': "'",       # right single quote (')
    '\u201C': '"',       # left double quote (")
    '\u201D': '"',       # right double quote (")
    '\u2026': '...',     # horizontal ellipsis (…)
    '\ufeff': '',        # BOM character
    # Box drawing characters (tree structure)
    '\u251C': '|',       # box drawings light vertical and right (├)
    '\u2514': '`',       # box drawings light up and right (└)
    '\u2502': '|',       # box drawings light vertical (│)
    '\u2500': '-',       # box drawings light horizontal (─)
}

# Malformed UTF-8 patterns (double-encoded as Latin-1)
# These occur when UTF-8 bytes are incorrectly interpreted as Latin-1
MALFORMED_FIXES = {
    '\xe2\x86\x92': '->',      # â†' (malformed →)
    '\xe2\x86\x90': '<-',      # â†� (malformed ←)
    '\xe2\x86\x94': '<->',     # â†" (malformed ↔)
    '\xce\xa3': 'sum',         # Î£ (malformed Σ)
    '\xe2\x9c\x93': '[x]',     # âœ" (malformed ✓)
    '\xe2\x94\x9c': '|',       # â"œ (malformed ├)
    '\xe2\x94\x94': '`',       # â"" (malformed └)
    '\xe2\x94\x82': '|',       # â"‚ (malformed │)
    '\xe2\x94\x80': '-',       # â"€ (malformed ─)
    '\xe2\x9a\xa0': '[!]',     # âš  (malformed ⚠)
    # Additional corrupted sequences (when bytes get replaced with Unicode)
    '\xe2\u2020': '->',        # â† (corrupted →, dagger U+2020 instead of bytes 0x86)
    '\u00ce\u00a3': 'sum',     # ÎŁ (double Latin-1 encoded Σ)
    '\xe2\u20ac"': '--',       # â€" (corrupted EM DASH — U+2014)
}

def fix_encoding(text):
    """Replace problematic UTF-8 characters with ASCII equivalents."""
    # First pass: Unicode replacements
    for old, new in ENCODING_FIXES.items():
        text = text.replace(old, new)
    
    # Second pass: Malformed UTF-8 (double-encoded)
    for old, new in MALFORMED_FIXES.items():
        text = text.replace(old, new)
    
    return text

def fix_source_files(base_dir):
    """Fix encoding in all source markdown files."""
    fixed_count = 0
    whitepaper_dir = base_dir / 'whitepaper'
    
    for md_file in whitepaper_dir.rglob('*.md'):
        try:
            # Read file as bytes to check for malformed UTF-8
            with open(md_file, 'rb') as f:
                raw_bytes = f.read()
            
            # Decode as UTF-8
            try:
                content = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_bytes.decode('utf-8', errors='replace')
            
            original = content
            fixed_content = fix_encoding(content)
            
            if content != fixed_content:
                # Write back as clean UTF-8
                with open(md_file, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(fixed_content)
                fixed_count += 1
        except Exception as e:
            print(f"  ⚠ Error processing {md_file.name}: {e}")
    
    return fixed_count

def compile_whitepaper(base_dir):
    """Compile the whitepaper from section files."""
    print("🔨 Compiling CryftNet Whitepaper...")
    
    # Fix encoding in source files first
    print("  📝 Fixing UTF-8 encoding in source files...")
    fixed_count = fix_source_files(base_dir)
    if fixed_count > 0:
        print(f"    ✓ Fixed encoding in {fixed_count} files")
    else:
        print(f"    ✓ All files clean")
    
    # Front matter
    front_matter = """<h1 align="center">CryftNet (Cryft Network) Whitepaper</h1>

<p align="center">
<strong>Revision:</strong> v1.23<br>
<strong>Date:</strong> January 10, 2026<br>
<strong>Status:</strong> Draft<br>
<strong>Authors:</strong> Cryft Labs (Draft)
</p>

<p align="center">
<strong>Latest Changes:</strong> Filled P0/P1 gaps for CRVS spec, Smart Slots determinism, under-claim enforcement, CGS boundary, GBL authority, atomic messaging, checkpoints, replay protection, RegionDeployer Solidity, two-phase init, object slots, fee/gas model, ping protocol, tokenomics, governance chambers, Cryftee sandbox, pinning proofs (new Appendices 16.3–16.10); minor P2 naming/external ref fixes.
</p>

<p align="center"><em>
This document is a technical design proposal. Some subsystems (notably CGS privacy and CRVS consensus) require validation via simulation, formal review, and security audits before production use.
</em></p>

---
"""
    
    # Section files in order
    sections = [
        'whitepaper/01-abstract.md',
        'whitepaper/02-design-goals.md',
        'whitepaper/03-background.md',
        'whitepaper/04-system-overview.md',
        'whitepaper/05-network-model.md',
        'whitepaper/06-consensus-crvs.md',
        'whitepaper/07-execution-parallelism.md',
        'whitepaper/08-subnets.md',
        'whitepaper/09-cgs.md',
    ]
    
    # Section 10 cross-chain sub-files
    s10_files = [
        'whitepaper/10-cross-chain/10-01-checkpoints.md',
        'whitepaper/10-cross-chain/10-02-messaging-replay.md',
        'whitepaper/10-cross-chain/10-03-zk-verification.md',
        'whitepaper/10-cross-chain/10-04-balance-partitioning.md',
        'whitepaper/10-cross-chain/10-05-user-mobility.md',
        'whitepaper/10-cross-chain/10-06-single-location.md',
        'whitepaper/10-cross-chain/10-07-region-first-deploy.md',
        'whitepaper/10-cross-chain/10-08-cross-region-fees.md',
        'whitepaper/10-cross-chain/10-09-dev-experience.md',
    ]
    
    # Final sections
    final_sections = [
        'whitepaper/11-asset-rewards-monetary.md',
        'whitepaper/12-governance.md',
        'whitepaper/13-cryftee.md',
        'whitepaper/14-security-threats.md',
        'whitepaper/15-roadmap.md',
        'whitepaper/16-appendices.md',
    ]
    
    # Compile content
    compiled = [front_matter]
    
    print("  📄 Adding sections 1-9...")
    for section_file in sections:
        path = base_dir / section_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        compiled.append('\n---\n')
    
    print("  📄 Adding section 10 (cross-chain, 9 sub-files)...")
    for s10_file in s10_files:
        path = base_dir / s10_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        compiled.append('')
    
    compiled.append('\n---\n')
    
    print("  📄 Adding sections 11-16...")
    for i, section_file in enumerate(final_sections):
        path = base_dir / section_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        
        if i < len(final_sections) - 1:
            compiled.append('\n---\n')
    
    # Add final line
    compiled.append('\n\n<p align="center"><em>End of document.</em></p>\n')
    
    # Join and fix any remaining encoding issues
    full_content = '\n'.join(compiled)
    full_content = fix_encoding(full_content)
    
    # Write output
    output_file = base_dir / 'whitepaper.md'
    output_file.write_text(full_content, encoding='utf-8')
    
    # Verify compilation
    lines = full_content.split('\n')
    headers = [line for line in lines if re.match(r'^## \d+\.', line)]
    
    print()
    print("✅ Compilation complete!")
    print(f"  Total lines: {len(lines)}")
    print(f"  Sections found: {len(headers)}")
    print()
    print("📋 Section headers:")
    for header in headers:
        print(f"  {header}")
    print()
    print("💾 Output: whitepaper.md")
    print(f"   Size: {len(full_content):,} bytes")

if __name__ == '__main__':
    base_dir = Path(__file__).parent
    compile_whitepaper(base_dir)
