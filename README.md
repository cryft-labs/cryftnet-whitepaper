<h1 align="center">CryftNet (Cryft Network) Whitepaper</h1>

<p align="center">
<strong>Revision:</strong> v1.19<br>
<strong>Date:</strong> January 08, 2026<br>
<strong>Status:</strong> Draft<br>
<strong>Authors:</strong> Cryft Labs (Draft)
</p>

<p align="center">
<strong>Latest Changes:</strong> Renamed chains (P-Chain → F-Chain/Federal, X-Chain → Mirror Chain, M-Chain → EVM Chain). Fixed mermaid diagrams and UTF-8 encoding issues.
</p>

<p align="center"><em>
This document is a technical design proposal. Some subsystems (notably CGS privacy and CRVS consensus) require validation via simulation, formal review, and security audits before production use.
</em></p>

---

## Revision History

| Version | Date | Notes |
|:--------|:-----|:------|
| v1.19 | January 08, 2026 | **CHAIN RENAMING:** P-Chain → F-Chain (Federal), X-Chain → Mirror Chain, M-Chain → EVM Chain. Updated all 16 sections with new nomenclature. Fixed mermaid diagram syntax errors. Corrected UTF-8 encoding issues (malformed arrows, em-dashes, special characters). |
| v1.18 | January 07, 2026 | **ARCHITECTURE CLARIFICATION:** Primary Network consists of THREE chains: F-Chain (validator/staking/subnets), Mirror Chain (native asset transfers/issuance), EVM Chain (EVM execution). Replaces previous "dual-chain Main" terminology. Staking anchored to F-Chain, native assets and GBL to EVM Chain, smart contracts to EVM Chain. When we say "EVM chain," we mean EVM Chain specifically. |
| v1.17 | January 06, 2026 | Clarifies that region IDs are NOT required for Main Federal C-Chain interactions; Main is the default/home chain where users interact without region specification; region IDs only required for State/City chain operations and cross-region transfers. |
| v1.16 | January 06, 2026 | Introduces Contract Mirror Registry (CMR) on M-Chain as authoritative source for deployment mirror state; clarifies region ID usage across deployments, checkpoints, and fee determination; CMR updated via region checkpoints; C-Chain Federation Registry syncs with M-Chain CMR. |
| v1.15 | January 06, 2026 | Comprehensive consistency review; expands threat analysis to 30+ threats covering all v1.9-v1.14 additions; adds GBL/SBL threats, region-first deployment threats, federation fee threats; updates roadmap milestones; adds 8 new open questions. |
| v1.14 | January 06, 2026 | Requires explicit region ID declaration (target_regions[]) for federation operations; adds federation fee structure for mirroring and cross-region transfers; ensures Main receives appropriate gas for multi-region operations. |
| v1.13 | January 06, 2026 | Introduces region-first deployment model with opt-in federation mirroring; adds RegionDeployer architecture; defines balance portability modes (region-locked, portable, replicated); two-phase initialization pattern for deterministic addresses. |
| v1.12 | January 06, 2026 | Addresses balance duplication attack on multi-region deployment; adds zero-balance constructor pattern; defines home region concept for initial minting; adds governance code review checklist. |
| v1.11 | January 06, 2026 | Expands CREATE2 deployment security model; explains why different init_code prevents front-running; adds federation-controlled deployer architecture and tiered deployment model. |
| v1.10 | January 06, 2026 | Expands M-Chain to include Global Balance Ledger (GBL) for authoritative cross-region balance tracking; adds City-level account management architecture with State-mediated settlement. |
| v1.9 | January 06, 2026 | Introduces dual-chain Main architecture (C-Chain + M-Chain); defines validator cross-participation requirements; adds hierarchical City chain registration via State chains only. |
| v1.8 | January 06, 2026 | Adds partitioned balance model for cross-region assets; user mobility and single-location guarantees; CREATE2 deterministic deployment; Federation Contract Registry; comprehensive threat analysis update for cross-region security. |
| v1.7 | January 06, 2026 | Adds Data Availability Sampling (DAS/PeerDAS-style) and ZK-EVM integration sections addressing the blockchain trilemma; adds ZK-based cross-chain verification. |
| v1.6 | January 02, 2026 | GitHub edition: reformatted as Markdown for version control; adds an optional "overlay mesh transport" note (Nebula as a reference implementation) without making it consensus-critical. |
| v1.5 | January 02, 2026 | Initial consolidated draft including Smart Slots, CRVS consensus proposal, CGS, Cryftee modules, IPFS pinning rewards, and cross-network federated DAO governance. |

---

## Table of Contents

- [1. Abstract](whitepaper/01-abstract.md)
- [2. Design goals and non-goals](whitepaper/02-design-goals.md)
  - [2.1 Goals](whitepaper/02-design-goals.md#21-goals)
  - [2.2 Non-goals](whitepaper/02-design-goals.md#22-non-goals)
- [3. Background and problem statement](whitepaper/03-background.md)
- [4. System overview](whitepaper/04-system-overview.md)
  - [4.1 Primary Network architecture (F-Chain + Mirror Chain + EVM Chain)](whitepaper/04-system-overview.md#41-primary-network-architecture-f-chain--mirror-chain--evm-chain)
  - [4.2 Validator cross-participation requirements](whitepaper/04-system-overview.md#42-validator-cross-participation-requirements)
  - [4.3 Hierarchical chain registration (Cities via States)](whitepaper/04-system-overview.md#43-hierarchical-chain-registration-cities-via-states)
  - [4.4 City-level account management (State-mediated balances)](whitepaper/04-system-overview.md#44-city-level-account-management-state-mediated-balances)
- [5. Network model and latency strategy](whitepaper/05-network-model.md)
  - [5.1 Regions as latency domains](whitepaper/05-network-model.md#51-regions-as-latency-domains)
  - [5.2 Validator eligibility via ping measurements](whitepaper/05-network-model.md#52-validator-eligibility-via-ping-measurements)
  - [5.3 User routing and failover](whitepaper/05-network-model.md#53-user-routing-and-failover)
  - [5.4 Diminishing returns: why committee size has a ceiling](whitepaper/05-network-model.md#54-diminishing-returns-why-committee-size-has-a-ceiling)
  - [5.5 Optional overlay mesh transport (Nebula reference implementation)](whitepaper/05-network-model.md#55-optional-overlay-mesh-transport-nebula-reference-implementation)
- [6. Consensus and finality model (CRVS proposal)](whitepaper/06-consensus-crvs.md)
  - [6.1 Data propagation plane (rotor-inspired)](whitepaper/06-consensus-crvs.md#61-data-propagation-plane-rotor-inspired)
  - [6.2 Candidate production: leaderless or soft-leader](whitepaper/06-consensus-crvs.md#62-candidate-production-leaderless-or-soft-leader)
  - [6.3 Voting and finality (votor-inspired fast/slow paths)](whitepaper/06-consensus-crvs.md#63-voting-and-finality-votor-inspired-fastslow-paths)
  - [6.4 Metastable sampling (Avalanche-inspired)](whitepaper/06-consensus-crvs.md#64-metastable-sampling-avalanche-inspired)
  - [6.5 Finality layering: region soft-finality vs Main hard-finality](whitepaper/06-consensus-crvs.md#65-finality-layering-region-soft-finality-vs-main-hard-finality)
  - [6.6 Data availability sampling (DAS) extensions](whitepaper/06-consensus-crvs.md#66-data-availability-sampling-das-extensions)
  - [6.7 ZK-EVM integration for validity proofs](whitepaper/06-consensus-crvs.md#67-zk-evm-integration-for-validity-proofs)
- [7. Execution layer: EVM compatibility and deterministic parallelism](whitepaper/07-execution-parallelism.md)
  - [7.1 Baseline EVM mode](whitepaper/07-execution-parallelism.md#71-baseline-evm-mode)
  - [7.2 Parallel execution mode (opt-in)](whitepaper/07-execution-parallelism.md#72-parallel-execution-mode-opt-in)
  - [7.3 Smart Slots and Process IDs (canonical model)](whitepaper/07-execution-parallelism.md#73-smart-slots-and-process-ids-canonical-model)
  - [7.4 Handling normally non-parallel transactions](whitepaper/07-execution-parallelism.md#74-handling-normally-non-parallel-transactions)
  - [7.5 Developer experience and backward compatibility](whitepaper/07-execution-parallelism.md#75-developer-experience-and-backward-compatibility)
- [8. Standard subnet model vs custom subnets](whitepaper/08-subnets.md)
  - [8.1 Cryft Standard Subnet (CSS-1)](whitepaper/08-subnets.md#81-cryft-standard-subnet-css-1)
  - [8.2 CEP-CSS-1: standardized execution profile](whitepaper/08-subnets.md#82-cep-css-1-standardized-execution-profile)
  - [8.3 Custom subnets](whitepaper/08-subnets.md#83-custom-subnets)
  - [8.4 Compatibility certification](whitepaper/08-subnets.md#84-compatibility-certification)
- [9. Cryft Global Synchronizer (CGS)](whitepaper/09-cgs.md)
  - [9.1 Core design constraints](whitepaper/09-cgs.md#91-core-design-constraints)
  - [9.2 CGS message types (proposal)](whitepaper/09-cgs.md#92-cgs-message-types-proposal)
  - [9.3 Metadata visibility matrix](whitepaper/09-cgs.md#93-metadata-visibility-matrix)
  - [9.4 Selective disclosure](whitepaper/09-cgs.md#94-selective-disclosure)
  - [9.5 CGS and Smart Slots via slot commitments](whitepaper/09-cgs.md#95-cgs-and-smart-slots-via-slot-commitments)
  - [9.6 Anti-censorship and liveness](whitepaper/09-cgs.md#96-anti-censorship-and-liveness)
  - [9.7 Failure modes and residual risk](whitepaper/09-cgs.md#97-failure-modes-and-residual-risk)
- [10. Cross-chain communication and settlement](whitepaper/10-cross-chain/README.md)
  - [10.1 Checkpoint format](whitepaper/10-cross-chain/10-01-checkpoints.md)
  - [10.2 Message passing guarantees](whitepaper/10-cross-chain/10-02-messaging-replay.md#102-message-passing-guarantees)
  - [10.3 Replay protection and ordering](whitepaper/10-cross-chain/10-02-messaging-replay.md#103-replay-protection-and-ordering)
  - [10.4 Interaction with CGS](whitepaper/10-cross-chain/10-02-messaging-replay.md#104-interaction-with-cgs)
  - [10.5 ZK-based cross-chain verification](whitepaper/10-cross-chain/10-03-zk-verification.md)
  - [10.6 Partitioned balance model: cross-region asset portability](whitepaper/10-cross-chain/10-04-balance-partitioning.md)
  - [10.7 User mobility and cross-region transfers](whitepaper/10-cross-chain/10-05-user-mobility.md)
  - [10.8 Single-location guarantee: preventing double-spending](whitepaper/10-cross-chain/10-06-single-location.md)
  - [10.9 Region-first deployment with federation mirroring](whitepaper/10-cross-chain/10-07-region-first-deploy.md)
  - [10.10 Federation fees and multi-region gas economics](whitepaper/10-cross-chain/10-08-cross-region-fees.md)
  - [10.11 Developer experience summary](whitepaper/10-cross-chain/10-09-dev-experience.md)
- [11. Asset model, rewards, and monetary policy](whitepaper/11-asset-rewards-monetary.md)
- [12. Governance: federated DAO and cross-network democracy](whitepaper/12-governance.md)
- [13. Cryftee: signed WASM module runtime for chain utilities](whitepaper/13-cryftee.md)
- [14. Security model and threat analysis](whitepaper/14-security-threats.md)
  - [14.1 Threat categories](whitepaper/14-security-threats.md#141-threat-categories)
  - [14.2 Consensus safety threats](whitepaper/14-security-threats.md#142-consensus-safety-threats)
  - [14.3 Liveness and censorship threats](whitepaper/14-security-threats.md#143-liveness-and-censorship-threats)
  - [14.4 Data availability and sampling threats](whitepaper/14-security-threats.md#144-data-availability-and-sampling-threats)
  - [14.5 Privacy threats (CGS, selective disclosure)](whitepaper/14-security-threats.md#145-privacy-threats-cgs-selective-disclosure)
  - [14.6 Cross-chain settlement threats](whitepaper/14-security-threats.md#146-cross-chain-settlement-threats)
  - [14.7 Parallel execution threats](whitepaper/14-security-threats.md#147-parallel-execution-threats)
  - [14.8 Multi-chain Main and hierarchical registration threats](whitepaper/14-security-threats.md#148-multi-chain-main-and-hierarchical-registration-threats)
  - [14.9 GBL, CMR, and SBL threats](whitepaper/14-security-threats.md#149-global-balance-ledger-gbl-contract-mirror-registry-cmr-and-state-balance-ledger-sbl-threats)
  - [14.10 Region-first deployment and federation fee threats](whitepaper/14-security-threats.md#1410-region-first-deployment-and-federation-fee-threats)
  - [14.11 Threat matrix (comprehensive summary)](whitepaper/14-security-threats.md#1411-threat-matrix-comprehensive-summary)
- [15. Implementation roadmap and engineering checklist](whitepaper/15-roadmap.md)
- [16. Appendices](whitepaper/16-appendices.md)

---

## How to Edit This Whitepaper

The whitepaper has been split into multiple files for easier maintenance and targeted editing:

### Quick Reference

| Topic | File |
|:------|:-----|
| **Abstract** | [whitepaper/01-abstract.md](whitepaper/01-abstract.md) |
| **Design goals** | [whitepaper/02-design-goals.md](whitepaper/02-design-goals.md) |
| **Background** | [whitepaper/03-background.md](whitepaper/03-background.md) |
| **System architecture** | [whitepaper/04-system-overview.md](whitepaper/04-system-overview.md) |
| **Network & latency** | [whitepaper/05-network-model.md](whitepaper/05-network-model.md) |
| **Consensus (CRVS)** | [whitepaper/06-consensus-crvs.md](whitepaper/06-consensus-crvs.md) |
| **EVM & parallelism** | [whitepaper/07-execution-parallelism.md](whitepaper/07-execution-parallelism.md) |
| **Subnets** | [whitepaper/08-subnets.md](whitepaper/08-subnets.md) |
| **CGS privacy** | [whitepaper/09-cgs.md](whitepaper/09-cgs.md) |
| **Cross-chain** | [whitepaper/10-cross-chain/](whitepaper/10-cross-chain/) (see index) |
| **Assets & rewards** | [whitepaper/11-asset-rewards-monetary.md](whitepaper/11-asset-rewards-monetary.md) |
| **Governance** | [whitepaper/12-governance.md](whitepaper/12-governance.md) |
| **Cryftee runtime** | [whitepaper/13-cryftee.md](whitepaper/13-cryftee.md) |
| **Security & threats** | [whitepaper/14-security-threats.md](whitepaper/14-security-threats.md) |
| **Roadmap** | [whitepaper/15-roadmap.md](whitepaper/15-roadmap.md) |
| **Appendices** | [whitepaper/16-appendices.md](whitepaper/16-appendices.md) |

### Section 10 (Cross-Chain) Sub-Files

Section 10 is split into multiple files for easier navigation:

- [10-01-checkpoints.md](whitepaper/10-cross-chain/10-01-checkpoints.md) - Checkpoint format
- [10-02-messaging-replay.md](whitepaper/10-cross-chain/10-02-messaging-replay.md) - Message passing, replay protection, CGS interaction
- [10-03-zk-verification.md](whitepaper/10-cross-chain/10-03-zk-verification.md) - ZK-based cross-chain verification
- [10-04-balance-partitioning.md](whitepaper/10-cross-chain/10-04-balance-partitioning.md) - Partitioned balance model
- [10-05-user-mobility.md](whitepaper/10-cross-chain/10-05-user-mobility.md) - User mobility and cross-region transfers
- [10-06-single-location.md](whitepaper/10-cross-chain/10-06-single-location.md) - Single-location guarantee
- [10-07-region-first-deploy.md](whitepaper/10-cross-chain/10-07-region-first-deploy.md) - Region-first deployment
- [10-08-cross-region-fees.md](whitepaper/10-cross-chain/10-08-cross-region-fees.md) - Federation fees
- [10-09-dev-experience.md](whitepaper/10-cross-chain/10-09-dev-experience.md) - Developer experience summary

### Guidelines

- **Preserve section numbering** when editing (e.g., "6.7 ZK-EVM integration" stays "6.7")
- **Cross-file links** use relative paths: `[text](../06-consensus-crvs.md#anchor)`
- **Keep Mermaid diagrams** in the files where they're referenced
- **Update revision history** in this README when making significant changes

### Compiling the Single-File Version

The main `whitepaper.md` file is compiled from all the individual section files. After editing any section file, recompile the whitepaper:

```bash
# Python (includes automatic encoding fixes)
python compile-whitepaper.py
```

**The compilation script automatically:**
- Fixes UTF-8 encoding issues (arrows, em-dashes, math symbols → ASCII)
- Fixes malformed UTF-8 sequences from double-encoding
- Combines all section files in the correct order
- Adds the header with revision info and latest changes
- Generates the final `whitepaper.md` for single-file reading

**Workflow:**
1. Edit individual section files in `whitepaper/` directory
2. Run `python compile-whitepaper.py` to regenerate `whitepaper.md`
3. Commit both the section files and the compiled `whitepaper.md`

**Important:** Always edit the source files in `whitepaper/` directory, never edit `whitepaper.md` directly. The compiled output is regenerated each time you run the compile script. See [INSTRUCTIONS.md](INSTRUCTIONS.md) for detailed maintenance guidelines.

---

<p align="center"><em>For the latest version, visit the CryftNet repository.</em></p>
