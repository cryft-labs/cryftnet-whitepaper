#!/usr/bin/env pwsh
# Compile whitepaper.md from individual section files
# Usage: .\compile-whitepaper.ps1

$wpDir = $PSScriptRoot

Write-Host "Compiling CryftNet Whitepaper..." -ForegroundColor Cyan

# Read the front matter (lines 1-67) from the current whitepaper
$frontMatter = Get-Content "$wpDir\whitepaper.md" -TotalCount 67 -Encoding UTF8

# Initialize the compiled content
$compiled = @()
$compiled += $frontMatter
$compiled += ""
$compiled += "---"
$compiled += ""

# Section files in order (1-9)
$sections = @(
    "whitepaper\01-abstract.md",
    "whitepaper\02-design-goals.md",
    "whitepaper\03-background.md",
    "whitepaper\04-system-overview.md",
    "whitepaper\05-network-model.md",
    "whitepaper\06-consensus-crvs.md",
    "whitepaper\07-execution-parallelism.md",
    "whitepaper\08-subnets.md",
    "whitepaper\09-cgs.md"
)

Write-Host "  Adding sections 1-9..." -ForegroundColor Gray
foreach ($section in $sections) {
    $content = Get-Content "$wpDir\$section" -Encoding UTF8
    $compiled += $content
    $compiled += ""
    $compiled += "---"
    $compiled += ""
}

# Section 10 (cross-chain) - compile from sub-files
$s10Files = @(
    "whitepaper\10-cross-chain\10-01-checkpoints.md",
    "whitepaper\10-cross-chain\10-02-messaging-replay.md",
    "whitepaper\10-cross-chain\10-03-zk-verification.md",
    "whitepaper\10-cross-chain\10-04-balance-partitioning.md",
    "whitepaper\10-cross-chain\10-05-user-mobility.md",
    "whitepaper\10-cross-chain\10-06-single-location.md",
    "whitepaper\10-cross-chain\10-07-region-first-deploy.md",
    "whitepaper\10-cross-chain\10-08-cross-region-fees.md",
    "whitepaper\10-cross-chain\10-09-dev-experience.md"
)

Write-Host "  Adding section 10 (cross-chain, 9 sub-files)..." -ForegroundColor Gray
foreach ($s10file in $s10Files) {
    $content = Get-Content "$wpDir\$s10file" -Encoding UTF8
    $compiled += $content
    $compiled += ""
}

$compiled += "---"
$compiled += ""

# Sections 11-16
$finalSections = @(
    "whitepaper\11-asset-rewards-monetary.md",
    "whitepaper\12-governance.md",
    "whitepaper\13-cryftee.md",
    "whitepaper\14-security-threats.md",
    "whitepaper\15-roadmap.md",
    "whitepaper\16-appendices.md"
)

Write-Host "  Adding sections 11-16..." -ForegroundColor Gray
foreach ($section in $finalSections) {
    $content = Get-Content "$wpDir\$section" -Encoding UTF8
    $compiled += $content
    $compiled += ""
    if ($section -ne $finalSections[-1]) {
        $compiled += "---"
        $compiled += ""
    }
}

# Add final line
$compiled += ""
$compiled += "<p align=`"center`"><em>End of document.</em></p>"

# Write the compiled whitepaper
$compiled | Out-File "$wpDir\whitepaper.md" -Encoding UTF8

# Verify compilation
$lines = Get-Content "$wpDir\whitepaper.md" -Encoding UTF8
$headers = $lines | Where-Object { $_ -match "^## \d+\." }

Write-Host ""
Write-Host "✓ Compilation complete!" -ForegroundColor Green
Write-Host "  Total lines: $($compiled.Count)" -ForegroundColor Gray
Write-Host "  Sections found: $($headers.Count)" -ForegroundColor Gray
Write-Host ""
Write-Host "Section headers:" -ForegroundColor Cyan
$headers | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
Write-Host ""
Write-Host "Output: whitepaper.md" -ForegroundColor Green
