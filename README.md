# CryftNet Whitepaper

<p align="center">
  <strong>A Federation of Blockchains with Web2-like Latency</strong><br>
  <em>Version 1.17  January 2026  Draft</em>
</p>

---

## Overview

CryftNet (Cryft Network) is a federation of blockchains designed to feel like Web2 in latency while retaining cryptographic integrity and democratic governance. This repository contains the technical whitepaper in **diff-friendly Markdown** format, suitable for collaborative development and version control.

## Repository Structure

```
cryftnet-whitepaper/
 README.md           # This file
 LICENSE             # License information
 whitepaper.md       # Primary whitepaper source (Markdown)
```

## Quick Links

-  **[Read the Whitepaper](whitepaper.md)**  Full technical specification
-  **[License](LICENSE)**  Repository license

## Key Concepts

| Concept | Description |
|:--------|:------------|
| **Main / Federal Chain** | Dual-chain architecture (C-Chain + M-Chain) for settlement and governance |
| **State / Region Chains** | Low-latency chains optimized for geographic domains |
| **City / Local Chains** | Optional sub-chains registering via parent States |
| **Smart Slots** | Deterministic parallel execution with explicit state dependencies |
| **CGS** | Cantons Global Synchronizer for privacy-aware propagation |
| **Cryftee** | Signed WASM module runtime for chain utilities |

## Architecture Highlights

- **EVM Compatible**  Works with existing Ethereum tooling and wallets
- **Hierarchical Federation**  Main  States  Cities with checkpoint-based settlement
- **Partitioned Balances**  Same contract address across regions with region-specific balances
- **Global Balance Ledger (GBL)**  M-Chain tracks authoritative cross-region balances
- **Contract Mirror Registry (CMR)**  M-Chain tracks deployment mirror state across regions
- **IPFS Pinning Rewards**  Incentivized content availability

## Document Sections

1. **Abstract**  High-level overview
2. **Design Goals**  What CryftNet aims to achieve
3. **Background**  Problem statement and motivation
4. **System Overview**  Dual-chain Main, validator requirements, hierarchical registration
5. **Network Model**  Latency strategy and routing
6. **Consensus (CRVS)**  Fast/slow path finality, DAS, ZK-EVM integration
7. **Execution Layer**  EVM compatibility, Smart Slots, deterministic parallelism
8. **Subnet Model**  CSS-1 standard subnets vs custom subnets
9. **CGS**  Privacy propagation and federation sync
10. **Cross-chain Communication**  Settlement, partitioned balances, region-first deployment
11. **Asset Model**  Rewards, monetary policy, federation fees
12. **Governance**  Federated DAO, cross-network democracy
13. **Cryftee**  WASM module runtime
14. **Security Model**  Comprehensive threat analysis (30+ threats)
15. **Roadmap**  Implementation milestones
16. **Appendices**  Glossary, open questions

## Recent Changes (v1.17)

-  Dual-chain Main architecture (C-Chain + M-Chain)
-  Global Balance Ledger (GBL) for cross-region balance tracking
-  Contract Mirror Registry (CMR) for deployment state
-  Region-first deployment with federation mirroring
-  Explicit target_regions[] and federation fee structure
-  Clarified: Main C-Chain does NOT require region IDs
-  Comprehensive threat matrix (30+ threats)
-  State Balance Ledger (SBL) for City management

## Contributing

This whitepaper is a living document. Contributions, corrections, and suggestions are welcome via pull requests or issues.

### Formatting Guidelines

- Headings are numbered to preserve document structure
- Concept diagrams use Mermaid flowcharts for easy editing
- Code examples use fenced code blocks with language hints
- Tables use GitHub-flavored Markdown

### Generating PDF

To generate a PDF version locally:

1. Install the [Markdown PDF](https://marketplace.visualstudio.com/items?itemName=yzane.markdown-pdf) VS Code extension
2. Open `whitepaper.md`
3. Press `Ctrl+Shift+P`  "Markdown PDF: Export (pdf)"

Or use Pandoc:
```bash
pandoc whitepaper.md -o whitepaper.pdf --pdf-engine=xelatex
```

## Status

 **Draft**  This document is a technical design proposal. Some subsystems (notably CGS privacy and CRVS consensus) require validation via simulation, formal review, and security audits before production use.

## License

See [LICENSE](LICENSE) for details.

---

<p align="center">
  <em>CryftNet  Where decentralization meets usability</em>
</p>
