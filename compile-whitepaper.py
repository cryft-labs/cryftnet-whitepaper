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
    # Common corruption patterns from whitepaper
    'â€"': '--',               # em dash corruption
    'âˆ†': 'Δ',                # delta corruption
    'âœ"': '✓',                # checkmark corruption
    'âŒ': '✗',                 # crossmark corruption
    'Ã¢Ë†â€': 'Δ',            # delta severe corruption
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
<strong>Revision:</strong> v1.33<br>
<strong>Date:</strong> February 25, 2026<br>
<strong>Status:</strong> Draft (Production Audit Candidate)<br>
<strong>Authors:</strong> Cryft Labs (Draft)
</p>

<p align="center">
<strong>Latest Changes (v1.33):</strong> **PROOF OF WORK LAUNCH & ETHEREUM-STYLE MONETARY MODEL:** Federal Chain and Primary Network now launch with Proof of Work (SHA3-256, 10s blocks, 2 CRYFT/block) for fair distribution of network gas to early participants, transitioning to Snowman/PoS after bootstrap criteria met (>=3.2M CRYFT in circulation, >=6 months, >=500 unique miners, 67% governance approval). Supply cap removed -- CRYFT now has uncapped continuous issuance following Ethereum's proven model. PoW phase follows Ethereum's original economics (2015-2021): all transaction fees go directly to miners, no EIP-1559, no fee burn. EIP-1559 activates at PoS transition. Post-PoS: sqrt(total_staked) issuance curve + base fee burn. Genesis pre-allocation: 125M CRYFT (all locked until PoS transition). Minimum stake: 32,000 CRYFT. Updated Sections 4, 6, 11, 15, 16. Previous (v1.32): Cryftee module file reorganization.
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
        'whitepaper/04-system-overview-city-fraud.md',  # P1: City emergency exit and fraud proofs
        'whitepaper/05-network-model.md',
        'whitepaper/06-consensus-crvs.md',
        'whitepaper/07-execution-parallelism.md',
        'whitepaper/08-subnets.md',
        'whitepaper/09-cgs.md',
    ]
    
    # Section 10 cross-chain sub-files
    s10_files = [
        'whitepaper/10-cross-chain/10-01-checkpoints.md',
        'whitepaper/10-cross-chain/10-01a-checkpoint-verification.md',  # P1: Checkpoint verification algorithm
        'whitepaper/10-cross-chain/10-02-messaging-replay.md',
        'whitepaper/10-cross-chain/10-03-zk-verification.md',
        'whitepaper/10-cross-chain/10-04-balance-partitioning.md',
        'whitepaper/10-cross-chain/10-05-user-mobility.md',
        'whitepaper/10-cross-chain/10-06-single-location.md',
        'whitepaper/10-cross-chain/10-07-region-first-deploy.md',
        'whitepaper/10-cross-chain/10-08-cross-region-fees.md',
        'whitepaper/10-cross-chain/10-09-dev-experience.md',
    ]
    
    # Section 13 Cryftee sub-files
    s13_files = [
        'whitepaper/13-cryftee/13-01-architecture.md',
        'whitepaper/13-cryftee/13-02-runtime.md',
        'whitepaper/13-cryftee/13-03-core-modules.md',
        'whitepaper/13-cryftee/13-03a-bls-tls-module.md',
        'whitepaper/13-cryftee/13-03b-debug-module.md',
        'whitepaper/13-cryftee/13-03c-llm-chat-module.md',
        'whitepaper/13-cryftee/13-03d-ipfs-module.md',
        'whitepaper/13-cryftee/13-03e-cgs-module.md',
        'whitepaper/13-cryftee/13-03f-redeemable-codes.md',
        'whitepaper/13-cryftee/13-03g-aim.md',
        'whitepaper/13-cryftee/13-06-operations.md',
    ]
    
    # Final sections
    final_sections = [
        'whitepaper/11-asset-rewards-monetary.md',
        'whitepaper/12-governance.md',
    ]
    
    # Post-Cryftee sections
    post_cryftee_sections = [
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
    
    print("  📄 Adding section 10 (cross-chain, README + 9 sub-files)...")
    # Add Section 10 parent header from README
    readme_path = base_dir / 'whitepaper/10-cross-chain/README.md'
    readme_content = readme_path.read_text(encoding='utf-8')
    compiled.append(readme_content)
    compiled.append('')
    
    for s10_file in s10_files:
        path = base_dir / s10_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        compiled.append('')
    
    compiled.append('\n---\n')
    
    print("  📄 Adding sections 11-12...")
    for section_file in final_sections:
        path = base_dir / section_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        compiled.append('\n---\n')
    
    print("  📄 Adding section 13 (Cryftee, README + 11 sub-files)...")
    # Add Section 13 parent header from README
    s13_readme_path = base_dir / 'whitepaper/13-cryftee/README.md'
    s13_readme_content = s13_readme_path.read_text(encoding='utf-8')
    compiled.append(s13_readme_content)
    compiled.append('')
    
    for s13_file in s13_files:
        path = base_dir / s13_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        compiled.append('')
    
    compiled.append('\n---\n')
    
    print("  📄 Adding sections 14-16...")
    for i, section_file in enumerate(post_cryftee_sections):
        path = base_dir / section_file
        content = path.read_text(encoding='utf-8')
        compiled.append(content)
        
        if i < len(post_cryftee_sections) - 1:
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
