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
    '\u2014': '--',      # em dash
    '\u2192': '->',      # rightwards arrow
    '\u2190': '<-',      # leftwards arrow
    '\u2194': '<->',     # left right arrow
    '\u2200': 'for all', # for all (∀)
    '\u2211': 'sum',     # n-ary summation (Σ)
    '\u2265': '>=',      # greater-than or equal to
    '\u2264': '<=',      # less-than or equal to
    '\u2018': "'",       # left single quote
    '\u2019': "'",       # right single quote
    '\u201C': '"',       # left double quote
    '\u201D': '"',       # right double quote
    '\u2026': '...',     # horizontal ellipsis
}

def fix_encoding(text):
    """Replace problematic UTF-8 characters with ASCII equivalents."""
    for old, new in ENCODING_FIXES.items():
        text = text.replace(old, new)
    return text

def fix_source_files(base_dir):
    """Fix encoding in all source markdown files."""
    fixed_count = 0
    whitepaper_dir = base_dir / 'whitepaper'
    
    for md_file in whitepaper_dir.rglob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8')
            fixed_content = fix_encoding(content)
            
            if content != fixed_content:
                md_file.write_text(fixed_content, encoding='utf-8')
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
<strong>Version:</strong> v1.18 (GitHub edition)<br>
<strong>Based on:</strong> v1.5 (January 02, 2026)<br>
<strong>Status:</strong> Draft<br>
<strong>Authors:</strong> Cryft Labs (Draft)
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
