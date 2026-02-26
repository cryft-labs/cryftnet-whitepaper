<h1 align="center">CryftNet (Cryft Network) Whitepaper</h1>

<p align="center">
<strong>Revision:</strong> v1.34<br>
<strong>Date:</strong> February 26, 2026<br>
<strong>Status:</strong> Draft (Production Audit Candidate)<br>
<strong>Authors:</strong> Cryft Labs (Draft)
</p>

<p align="center">
<strong>Latest Changes (v1.34):</strong> **PARALLELISM CONFLICT MODEL CLARITY (PRE-LOCK VS SPECULATIVE):** Section 7.3.6 now includes explicit design rationale contrasting CryftNet's Ethereum-style pre-lock conflict model with Solana-style speculative execution. CryftNet acquires locks before execution -- conflicting transactions are never executed and waste zero compute; they return to the mempool and are included in a future block once the conflict resolves. Solana speculatively executes transactions in parallel and aborts/retries on conflict, wasting compute on failed runs. Clarified that deferred transactions return to mempool (not retried intra-block). Trade-off: one-block latency for conflicts, acceptable given sub-second regional block times. Updated Section 7. Previous (v1.33): Proof of Work launch and Ethereum-style monetary model.
</p>

<p align="center"><em>
This document is a technical design proposal. Some subsystems (notably CGS privacy and CRVS consensus) require validation via simulation, formal review, and security audits before production use.
</em></p>

---

## Table of Contents

- [1. Abstract](whitepaper/01-abstract.md)
- [2. Design goals and non-goals](whitepaper/02-design-goals.md)
  - [2.1 Goals](whitepaper/02-design-goals.md#21-goals)
  - [2.2 Non-goals](whitepaper/02-design-goals.md#22-non-goals)
- [3. Background and problem statement](whitepaper/03-background.md)
- [4. System overview](whitepaper/04-system-overview.md)
  - [4.1 Primary Network architecture (Federal Chain + Mirror Chain + EVM Chain)](whitepaper/04-system-overview.md#41-primary-network-architecture-federal-chain--mirror-chain--evm-chain)
  - [4.2 Validator cross-participation requirements](whitepaper/04-system-overview.md#42-validator-cross-participation-requirements)
  - [4.3 Hierarchical chain registration (Cities via States)](whitepaper/04-system-overview.md#43-hierarchical-chain-registration-cities-via-states)
  - [4.4 City-level account management (State-mediated balances)](whitepaper/04-system-overview.md#44-city-level-account-management-state-mediated-balances)
  - [4.5 Code Vault Storage Modes: On-Chain vs. IPFS-Referenced](whitepaper/04-system-overview.md#45-code-vault-storage-modes-on-chain-vs-ipfs-referenced)
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
- [13. Cryftee: signed WASM module runtime for chain utilities](whitepaper/13-cryftee/README.md)
  - [13.1 Architecture Overview](whitepaper/13-cryftee/13-01-architecture.md)
  - [13.2 Runtime Properties](whitepaper/13-cryftee/13-02-runtime.md)
  - [13.3 Core Modules](whitepaper/13-cryftee/13-03-core-modules.md)
    - [13.3.1 BLS/TLS Signer](whitepaper/13-cryftee/13-03a-bls-tls-module.md)
    - [13.3.2 Debug Module](whitepaper/13-cryftee/13-03b-debug-module.md)
    - [13.3.3 LLM Chat Module](whitepaper/13-cryftee/13-03c-llm-chat-module.md)
    - [13.3.4 IPFS Module](whitepaper/13-cryftee/13-03d-ipfs-module.md)
    - [13.3.5 CGS Module (Private Sync)](whitepaper/13-cryftee/13-03e-cgs-module.md)
    - [13.3.6 Redeemable Codes](whitepaper/13-cryftee/13-03f-redeemable-codes.md)
  - [13.4 Operational Integration](whitepaper/13-cryftee/13-06-operations.md)
  - [13.5 Agent Identity & Memory (AIM)](whitepaper/13-cryftee/13-07-aim.md)
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
| **Cryftee runtime** | [whitepaper/13-cryftee/](whitepaper/13-cryftee/) (see index) |
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

### Section 13 (Cryftee) Sub-Files

Section 13 is split into multiple files for modular editing:

- [13-01-architecture.md](whitepaper/13-cryftee/13-01-architecture.md) - CryftGo vs Cryftee separation, design rationale
- [13-02-runtime.md](whitepaper/13-cryftee/13-02-runtime.md) - Module loading, API surface, trust model
- [13-03-core-modules.md](whitepaper/13-cryftee/13-03-core-modules.md) - Overview of all 6 core modules
  - [13-03a-bls-tls-module.md](whitepaper/13-cryftee/13-03a-bls-tls-module.md) - BLS/TLS Signer (staking, multi-device)
  - [13-03b-debug-module.md](whitepaper/13-cryftee/13-03b-debug-module.md) - Debug module (diagnostics)
  - [13-03c-llm-chat-module.md](whitepaper/13-cryftee/13-03c-llm-chat-module.md) - LLM Chat (operator interface)
  - [13-03d-ipfs-module.md](whitepaper/13-cryftee/13-03d-ipfs-module.md) - IPFS (storage, pin rewards)
  - [13-03e-cgs-module.md](whitepaper/13-cryftee/13-03e-cgs-module.md) - CGS/Private Sync (Canton-style)
  - [13-03f-redeemable-codes.md](whitepaper/13-cryftee/13-03f-redeemable-codes.md) - Redeemable Codes (gift codes)
- [13-06-operations.md](whitepaper/13-cryftee/13-06-operations.md) - Node types, Cryftee requirements
- [13-07-aim.md](whitepaper/13-cryftee/13-07-aim.md) - Agent Identity & Memory (infrastructure layer)

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

## Revision History

| Version | Date | Notes |
|:--------|:-----|:------|
| v1.34 | February 26, 2026 | **PARALLELISM CONFLICT MODEL CLARITY (PRE-LOCK VS SPECULATIVE):** Section 7.3.6 now includes explicit design rationale contrasting CryftNet's Ethereum-style pre-lock conflict model with Solana-style speculative execution. CryftNet acquires locks before execution -- conflicting transactions are never executed and waste zero compute; they return to the mempool and are included in a future block once the conflict resolves. Solana speculatively executes in parallel and aborts/retries on conflict. Clarified deferred transactions return to mempool, not retried intra-block. Updated Section 7. |
| v1.33 | February 25, 2026 | **PROOF OF WORK LAUNCH & ETHEREUM-STYLE MONETARY MODEL:** Federal Chain and Primary Network now launch with Proof of Work (SHA3-256, 10s blocks, 2 CRYFT/block) for fair distribution of network gas to early participants, transitioning to Snowman/PoS after bootstrap criteria met (>=3.2M CRYFT in circulation, >=6 months, >=500 unique miners, 67% governance approval). Supply cap removed -- CRYFT now has uncapped continuous issuance following Ethereum's proven model. PoW phase follows Ethereum's original economics (2015-2021): all transaction fees go directly to miners, no EIP-1559, no fee burn. EIP-1559 activates at PoS transition. Post-PoS: sqrt(total_staked) issuance curve + base fee burn. Genesis pre-allocation: 125M CRYFT (all locked until PoS transition). Minimum stake: 32,000 CRYFT. Updated Sections 4, 6, 11, 15, 16. |
| v1.32 | February 4, 2026 | **CRYFTEE MODULE FILE REORGANIZATION:** All 6 core modules now have individual specification files using consistent 13.3.x numbering (13-03a through 13-03f). Modules: bls_tls_signer_v1 (13.3.1), debug_v1 (13.3.2), llm_chat_v1 (13.3.3), ipfs_v1 (13.3.4), private_sync_v1 (13.3.5), redeemable_codes_v1 (13.3.6). All modules designated as CORE MODULES required for full network capability. Added clear distinction between llm_chat_v1 (operator chat interface within Cryftee runtime) and AIM (on-chain agent identity infrastructure layer) - they serve different purposes; llm_chat may optionally use AIM-registered agents as LLM providers. Operations renumbered to 13.4, AIM to 13.5. |
| v1.31 | February 4, 2026 | **CRYFTEE MODULE ACCURACY UPDATE:** Updated all Cryftee modules to match actual cryfttee implementation. bls_tls_signer_v1: TLS-first Node ID derivation, multi-device support, 3 storage backends (Vault/Local/Memory). llm_chat_v1: Updated to v2.0.0 with multi-provider support (OpenAI/Anthropic/Local), 50 concurrent sessions, 128k token context. ipfs_v1: Added tiered reward system (Basic 1x to Critical 10x), storage challenges with merkle proofs, 6 operations. private_sync_v1 (CGS): Updated to Canton Network-inspired protocol with encrypted party views, commitment-based confirmation, TEE-secured mediator finality. Added Section 13.8 Redeemable Codes Module (US Patent App 20250139608): dual smart contract architecture (Public + Private TEE), XXXX-YYYY-YYYY-YYYY code format, multiple content types. |
| v1.30 | February 4, 2026 | **CRYFTEE MODULAR REORGANIZATION:** Restructured Section 13 into directory format (whitepaper/13-cryftee/) matching Section 10 cross-chain structure. Added Section 13.7 Tokenized Agent Identity & Memory (Cryftee AIM): GBL-backed AgentRegistry for canonical identity, AgentAccount smart wallet interface, anchored memoryHead commitments for persistent memory, session key delegation, memory epochs for efficient verification. Minimum viable compliance: AgentRegistry + AgentAccount + memoryHead. Explicit design principle: AI reasoning MUST NOT be consensus-critical. Optional extensions: tokenized memory capsules, agent marketplaces, auditor agents. |
| v1.29 | January 20, 2026 | **INVESTOR/AUDITOR CONFIDENCE ADDITIONS:** Added Section 12.4 Bootstrapping and Decentralization Trajectory (~750 lines): Explicit 4-phase transition plan with enforced timeline (Phase 0: Days 0-30 controlled launch with Cryft Labs 40% validators, Phase 1: Days 31-90 governance bootstrap with DAO execution authority, Phase 2: Days 91-180 module publisher decentralization requiring 3-of-5 signatures, Phase 3: Days 181-365 full decentralization removing all Cryft Labs special powers). On-chain time-locked enforcement contracts (DecentralizationEnforcement.sol) prevent \"perpetual bootstrap\" by allowing anyone to trigger phase transitions after deadlines (Phase 1 by Day 31, Phase 2 by Day 91, Phase 3 by Day 365). Initial control assumptions documented: governance multisigs, module signing authority, treasury control, release authority, emergency pause (72h, expires Day 180). Sunset plan: By Day 365 Cryft Labs becomes one participant among many with <10% validator stake, no special keys, subject to same slashing rules. Public Decentralization Dashboard tracks all Cryft Labs-controlled keys in real-time. Addresses \"benevolent dictatorship\" investor concern with code-enforced transition. Added Section 11.5 Economics with Zero Emission (~650 lines): Answers \"who pays for security at low usage\" question. Genesis distribution: 1B CRYFT total supply (10% genesis validators, 30% treasury, 15% team, 20% investors, 15% community sale, 10% ecosystem). Validator bootstrap program: 100M CRYFT distributed Days 0-180 with tapering rewards (100% Days 0-30, 75% Days 31-90, 50% Days 91-150, 25% Days 151-180, 0% after Day 180). Realistic fee projections: $2.2k/day Month 1 (break-even for 100 validators at $150-200/month costs), $28k/day Month 6 (10x growth, $840/month per validator = +320% ROI). State fee subsidy pools (opt-in, DAO-gated for treasury-funded, max 1M CRYFT per State, 24-month cap). Treasury emergency validator stipends (activation requires 4 criteria: fees <$1k/day for 14 days, validators <75, DAO 67% supermajority, treasury >5M CRYFT; 90-day maximum duration with auto-sunset). Long-term sustainability: Pure fee-based model post-bootstrap with DAO flexibility to introduce emission if economic reality demands (not ideological rigidity). Added Section 5.7 Operational SLOs and Monitoring (~550 lines): Transforms \"Web2 feel\" claim from marketing into enforceable protocol guarantees. CSS-1 required metrics: p50/p95/p99 block latency (<500ms/<2s/<5s), validator uptime (>95%), RPC availability (>99.5%), TPS (>100 sustained), block time variance (<±200ms). Measurement infrastructure: 20-50 geographically distributed ping beacons (Federal Chain operated, beacon operators bonded/slashed for false reporting), client telemetry opt-in (privacy-preserving, no PII), validator self-reporting (cross-validated against beacon data). Tiered penalty system: Tier 1 routing deprioritization for p95 >2s for 3+ epochs (no slashing), Tier 2 sustained violation 25% reward haircut + 2x checkpoint fees for 10+ epochs (DAO alert), Tier 3 critical failure 2% validator slash + suspension for <50% uptime or 24h outage (emergency DAO vote). Recovery process: diagnosis (0-48h) → fix/validation (48h-7d) → probation (7-30d gradual reward restoration) → full restoration (Day 30+). Public SLO dashboard at https://status.cryftnet.io with live p50/p95/p99 for all regions, color-coded validator uptime, historical charts, incident timeline, wallet API for region recommendation (MetaMask integration example). Makes operational claims auditable and trustworthy with real consequences. Total additions: ~1,950 lines addressing three critical investor/auditor concerns. Previous (v1.28): P1 specification gaps resolved. |
| v1.28 | January 20, 2026 | **P1 SPECIFICATION GAPS RESOLVED:** Added Section 5.6 Chain IDs and RPC Compatibility (~300 lines): precise chainId numbering scheme (Federal=1, Mirror=2, EVM=3, States=1000-999999, Cities=1000000-9999999, Custom=10000000+), EIP-155 replay protection universally enforced, Federal Chain discovery registry with signed metadata and fallback mechanisms, RPC behavior matrix across chain types (validator set queries, checkpoint methods), wallet/tooling integration patterns (MetaMask network params, Hardhat config, block explorer URLs). Added Section 10.1.1 Checkpoint Verification Algorithm (~350 lines): canonical validator set tracking via Federal Chain registry (ValidatorSetCommitment with epoch, validator_set_hash, quorum_threshold, transition_height), BLS aggregate signature verification algorithm (verifyBLSAggregateSignature with bitmap, computeSigningStake), mid-epoch validator set change handling with dual validator set support, light client minimum-data verification (trust Federal Chain's acceptance vs. full quorum re-verification), failure modes table (wrong validator_set_hash, unregistered epoch, invalid signature, insufficient stake), performance metrics (registration ~50k gas, verification ~200k gas, light client ~5k gas). Added Section 4.4.1 City Emergency Exit and Fraud Proofs (~250 lines): Merkle proof-based emergency exit from City→State→Federal escalation path, balance Merkle root commitment in every City checkpoint (sorted leaf construction: keccak256(account || asset_id || balance)), State Balance Ledger emergencyExitFromCity() function with Merkle proof verification, Federal Chain appeal path if State censors (72h waiting period, 2% censorship slash), fraud proof mechanism with CityFraudProof struct and submitCityFraudProof() for invalid checkpoints (10% fraud slash), griefing prevention (cryptographic proof security, double-claim tracking via exits mapping, spam rate limiting, governance pause), economic incentive table (validators/users/fraud provers). Updated Section 4.5.3 Code Vault Canonical Encoding (~150 lines replaced): TLV (Type-Length-Value) encoding replacing JSON for consensus-critical lock_script parsing (deterministic, no parser ambiguity, compact, forward-compatible with skip-unknown-types rule), complete TLV structure specification (type codes: 0x01=storage_mode, 0x02=init_code_hash, 0x03=runtime_code_hash, 0x10/0x11=ON_CHAIN blobs, 0x20/0x21/0x22/0x23=IPFS fields, 0xFE=nonce, 0xFF=signature), validation algorithm in Python with signature verification over commitment, rationale for TLV over JSON (canonical byte ordering, ~30% space savings, byte-exact parsing, auditable structure), version marker (v1) for mainnet enforcement. Added version markers throughout: DAS extensions marked (vNext) optional in v1 with production integration 2027+, ZK-EVM validity proofs marked (vNext) with phased adoption timeline 2027-2030, light voting mechanisms marked (vNext) for future research. Total additions: ~900 lines of normative specifications addressing auditor feedback on consensus-critical encoding correctness, developer UX for tooling integration, and hierarchical City safety guarantees. Compilation now includes whitepaper/04-system-overview-city-fraud.md and whitepaper/10-cross-chain/10-01a-checkpoint-verification.md. Whitepaper upgraded to "Production Audit Candidate" status. Previous (v1.27): Section numbering consistency fixes. |
| v1.27 | January 20, 2026 | **SECTION NUMBERING CONSISTENCY:** Fixed all duplicate and misordered section numbers throughout the whitepaper. Resolved duplicate Section 10.9 (removed "Initial supply" duplicate from 10-05-user-mobility.md, kept "Region-first deployment" in 10-07-region-first-deploy.md). Renumbered Section 11.3 subsections: changed first occurrence from 11.3.2 to 11.3.1 for "v1 Slashing Evidence Specification", kept second as 11.3.2 for "Parameter table". Corrected Section 7.3 subsections: kept 7.3.6 "Deterministic scheduling", renumbered second 7.3.6 to 7.3.7 for "Receipts and proofs". Added missing Section 10 parent header "## 10. Cross-chain communication and settlement" by including 10-cross-chain/README.md in compilation process. Updated compilation script to properly include cross-chain README for hierarchical structure. Changed "## 10.9" to "### 10.9" in 10-07-region-first-deploy.md to maintain proper subsection hierarchy. All 16 main sections now properly numbered with no duplicates and correct sequential ordering. Ensures clean structure for implementation reference and eliminates navigation confusion. |
| v1.26 | January 17, 2026 | **IMPLEMENTATION-READY HARDENING:** Added Section 4.1.1 Block Cadence & Asynchronicity clarifying independent Snowman instances with atomic finality at bundle level only ("Each chain uses unmodified Snowman consensus; atomic bundle blocks are a coordination layer that synchronizes finality across chains, not a modification to the consensus mechanism itself"). Added explicit "v1 = pure Snowman" statement to Section 6.8: Primary Network launches with pure, unmodified Avalanche/Snowman consensus per chain; atomic bundle coordinator is separate layer above consensus (no CRVS components active in v1). **Added Section 11.3.2 v1 Slashing Evidence Specification (Snowman Consensus)** with provable misbehavior set for v1: Checkpoint Equivocation (5%), Invalid Bundle Proposal (3%), Cryftee Attestation Fraud (10%); defined NOT slashable behaviors (Snowman vote equivocation, block withholding, invalid propagation, liveness failures); complete evidence formats with cryptographic verification steps and Federal Chain submission flow; resolves "proof substrate" gap for implementation. **Added Section 4.1.2 Federation Token Portability Modes:** Mode A (GBL-Authoritative, recommended for stablecoins/federation-backed assets): Mirror GBL stores per-account balances, ERC-20 is facade routing through precompiles; provides per-tx atomicity and instant global truth; trade-off: 5000 gas precompile cost per transfer. Mode B (State-Authoritative with GBL-Allocation, opt-in for gaming/loyalty tokens): States maintain per-account balances (standard ERC-20 mappings), GBL tracks only State allocations/totals; safety enforced at checkpoint boundaries via quorum sigs or ZK proofs; provides standard ERC-20 composability and lower cost; trade-off: checkpoint-security model and delayed global truth. Added Sections 4.1.3-4.1.4 with normative specifications for both modes: source of truth rules, ERC-20 function semantics, event emission invariants (FT-GBL-01/02), cross-region transfer events, checkpoint verification for Mode B, proof requirements (v1 quorum sigs, vNext ZK proofs), asset registration with immutable PortabilityMode enum. Updated Section 4.1 CMR to include portability_mode field. **Added Section 9.7a CGS Decryption & Inclusion Liveness** resolving CGS liveness story: Who must be online (t-of-n committee, proposer requests shares), fallback mechanism (client-side detection + wallet automatic conversion to legacy tx with same nonce), proposer behavior (5s timeout, skip intent if < t shares, broadcast COMMITTEE_DOWN signal), privacy mode dependency matrix (NONE/SELECTIVE/FULL encryption levels), committee incentive fees, censorship resistance with 4 mitigation layers (multi-pool routing, evidence-based slashing 2%, emergency plaintext submission, reputation tracking). Clarifies proposer does NOT need committee cooperation for public/non-private transactions, only for CGS encrypted intents. Added 2 glossary entries. Enhanced Section 13.8 Cryftee Requirement & Node Stack with comprehensive node type matrix (Full Validator, Light Validator, RPC, Archive, Explorer), implementation guidance with CryftGo flags (--require-cryftee-for-consensus, --cryftee-path, --cryftee-required-modules, --cryftee-attestation-required), and module selection guidelines for validators (minimum: bls_tls_signer_v1 + ipfs_v1). Added Cryftee attestation requirements to Section 14.1 threat model ("Cryftee offline or invalid attestation" with startup failure mitigation) and Section 5.2 validator eligibility (valid /v1/runtime/attestation required). Added mandatory startup failure requirement to Section 13.7: CryftGo MUST fail if Cryftee not running or required modules fail attestation. Added CSS-1 Cryftee requirement note to Section 4.2 ensuring full-stack validator obligations for Primary Network participation. These changes eliminate implementation ambiguity, clarify consensus baseline (Snowman, not CRVS), define clear node stack requirements, specify v1 slashing proof substrate, add flexible portability modes for federation tokens, and make CGS liveness/censorship resistance implementation-tight. Prevents "I forgot Cryftee" bugs and premature consensus innovation. Makes whitepaper ready for AvalancheGo fork development. |
| v1.25 | January 15, 2026 | **CODE VAULT DUAL STORAGE MODES:** Added Section 4.5 with comprehensive Code Vault storage architecture supporting two modes: (1) On-chain storage for critical contracts with direct bytecode inclusion in Mirror Chain UTXO (higher cost, guaranteed replication across all validators, immune to external dependencies); (2) IPFS-referenced storage for larger contracts with CID references (scalable, cost-efficient, 98% uptime SLA via pinning incentives from Section 11.4). Extended UTXO structure includes storage_mode flag, init_code_hash/runtime_code_hash for integrity, mode-specific fields (init_code_blob/runtime_bytecode for on-chain OR init_code_cid/runtime_bytecode_cid for IPFS), pin_duration_epochs and pin_budget for IPFS jobs. Transaction flow examples with Python pseudocode demonstrate both paths: on-chain pays base + data fees (16 gas/byte); IPFS escrows pin_budget for provider rewards. Storage mode invariants ensure identical security regardless of retrieval location (regions verify against committed hashes). Integration with CMR for lazy mirroring: ensureDeployedAndCall() fetches based on mode (atomic query for on-chain, pinning providers for IPFS with Mirror fallback). Failure handling includes deployment revert with governance appeal and provider slashing. **EVM Compatibility Constraint:** Added clarification that runtime bytecode must not exceed maximum contract size enforced by target regional/Federal EVM chains (typically 24KB per EIP-170), with deployment rejection for oversized bytecode even if Code Vault UTXO created successfully; deployers must verify target chain limits before depositing. Empowers deployers to choose permanence vs. cost tradeoff. ~300 lines added to Section 4.5 with rationale, invariants, UTXO schema, transaction examples, integration details. |
| v1.24 | January 10, 2026 | **PRODUCTION-READY P0 EXPANSIONS:** Complete CRVS state machine with per-validator states (UNDECIDED/PREFERRED/FINALIZED/TIMEOUT_RECOVERY), fast/slow path health score triggers, safety/liveness properties with adversary resilience table (<15% to ≥50%), hysteresis rules for preference switching (gap=3), clock skew handling (±500ms), failure modes table (Section 6.4 ~200 lines, Appendix 16.3 ~400 lines). Atomic bundle block execution with 6-phase deterministic ordering (pre-validation → message application → execute each chain → invariant validation → quorum voting → finalization/rollback), liveness failure modes table (7 scenarios), crash consistency with WAL structure and recovery algorithm, data availability requirements (200-1000 KB/bundle), upgrade coupling 4-phase process, subsystem degradation strategies (Section 4.1 ~150 lines, Appendix 16.4 ~350 lines). Smart Slots EVM access-tracing determinism specification with what counts as access (BALANCE/EXTCODESIZE/CALL/SLOAD/SSTORE/precompiles), DELEGATECALL attribution to caller's storage context, STATICCALL READ-only rules, enforcement policies (A1 REVERT 50% penalty testnet, A2 SERIAL_FALLBACK mainnet), determinism guarantee across all EVM implementations (Section 6 ~30 lines). GBL precompile interface (IGBLPrecompile) with 6 functions (queryBalance/transfer/transferToRegion/getTransferStatus/totalSupply/getAccountRegions), gas costs (700/2600/5000/15000), reentrancy protection (NON-REENTRANT), 9 error codes, cache consistency enforcement algorithm, composability constraints, ERC-20 wrapper pattern (Section 4.1 ~180 lines). All P0 subsystems now include explicit failure modes, assumptions, "what happens when X fails" analysis. CRVS slashing evidence formats (Equivocation 5%, RelayWithholding 2%, InvalidVote 1%) specified in Appendix 16.3 for FUTURE use; v1 Snowman slashing added in v1.26 (Section 11.3.2). Protobuf message schemas. Status upgraded to "Production Review Candidate." Total additions: ~1,310 lines across critical sections. |
| v1.23 | January 10, 2026 | **P0/P1 GAP ANALYSIS & ENCODING FIXES:** Identified 8 P0 and 2 P1 critical gaps requiring expansion before production review (documented in P0_GAPS_ANALYSIS.md). Fixed Section 6.4 incomplete metastable sampling gap. Corrected character encoding corruption throughout whitepaper (Ã-- → ×, âš ï¸ → ⚠️, malformed arrows). Fixed RegionDeployer code duplication and corruption. Corrected ensureDeployedAndCall() value flow bug (callValue = msg.value - deploymentFee). Fixed bytecode hash checking syntax to use assembly extcodehash. Fixed duplicate section numbering (7.3.5 → 7.3.6). Fixed truncated process_id examples. Added atomic bundle blocks warning labels. Prepared foundation for major P0 expansions in v1.24. |
| v1.22 | January 10, 2026 | **LAZY MIRRORING & CODE VAULT:** Added lazy mirroring via CREATE2 with Mirror Chain Code Vault for deploy-on-first-use pattern. Mirror Chain stores canonical bytecode commitments (code_id, init_code_hash, runtime_code_hash); EVM Chain CMR authorizes deployments. Implemented ensureDeployedAndCall() in RegionDeployer enabling contracts to deploy on-demand when first called on a region, maintaining identical addresses via CREATE2 determinism. First caller pays deployment gas + federation fee; subsequent callers pay normal gas. Added 11 new security threats (Section 14.11) covering Code Vault injection, code integrity verification, constructor supply duplication enforcement, authorization proofs, and lazy deployment attacks. Updated roadmap (Milestones 15.2-15.3) with Code Vault implementation, CMR integration, authorization proof verification, and runtime bytecode checks. Added 6 glossary terms: Code Vault, code_id, ensureDeployedAndCall(), lazy mirroring, loader init_code. Zero-balance constructor enforcement prevents supply duplication across regions. Mirror remains lean (no smart contract execution). |
| v1.21 | January 10, 2026 | **MIRROR CHAIN GBL ARCHITECTURE:** Updated GBL from EVM Chain to Mirror Chain using extended UTXO model. Each UTXO includes metadata: {asset_id, region_id, account, amount}. Mirror Chain serves as dedicated partitioned ledger and source of truth for EVM-based balances across opted-in subnets. EVM Chain and subnets access Mirror GBL via atomic cross-chain messaging or precompiles. Updated Sections 4.1, 10.4, 10.6, 10.7, 11, 13, 14.9, 15.2, 15.9, and glossary. CMR remains on EVM Chain. Conservation invariant enforced by Mirror Chain UTXO model. |
| v1.20 | January 08, 2026 | **PRODUCTION READINESS:** Added deterministic under-claiming enforcement for Smart Slots (Section 7.3.5) with runtime access-trace validation. Clarified CGS consensus boundary (Sections 9.5-9.9): CGS is mempool transport only, not consensus-critical; added concrete threshold encryption key management, explicit privacy goals, and mainnet gating criteria. Transformed Section 16.2 open questions into decision machine with 27 actionable items (type, owner, milestone, acceptance tests, priority tiers). Added pragmatic Mainnet v1 deployment strategy (Section 15.9): proven baseline consensus, regions enabled, Smart Slots/CGS/CRVS testnet-only or deferred. |
| v1.19 | January 08, 2026 | **CHAIN RENAMING:** P-Chain → Federal Chain, X-Chain → Mirror Chain, M-Chain → EVM Chain. Updated all 16 sections with new nomenclature. Fixed mermaid diagram syntax errors. Corrected UTF-8 encoding issues (malformed arrows, em-dashes, special characters). |
| v1.18 | January 07, 2026 | **ARCHITECTURE CLARIFICATION:** Primary Network consists of THREE chains: Federal Chain (validator/staking/subnets), Mirror Chain (native asset transfers/issuance), EVM Chain (EVM execution). Replaces previous "dual-chain Main" terminology. Staking anchored to Federal Chain, native assets and GBL to EVM Chain, smart contracts to EVM Chain. When we say "EVM chain," we mean EVM Chain specifically. |
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

<p align="center"><em>For the latest version, visit the CryftNet repository.</em></p>
