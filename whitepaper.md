<h1 align="center">CryftNet (Cryft Network) Whitepaper</h1>

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

## Revision history

| Version | Date | Notes |
|:--------|:-----|:------|
| v1.18 | January 07, 2026 | **ARCHITECTURE CLARIFICATION:** Primary Network consists of THREE chains: P-Chain (validator/staking/subnets), M-Chain (native asset transfers/issuance), EVM-Chain (EVM execution). Replaces previous "dual-chain Main" terminology. Staking anchored to P-Chain, native assets and GBL to M-Chain, smart contracts to EVM-Chain. When we say "EVM chain," we mean EVM-Chain specifically. |
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
| v1.6 | January 02, 2026 | GitHub edition: reformatted as Markdown for version control; adds an optional “overlay mesh transport” note (Nebula as a reference implementation) without making it consensus-critical. |
| v1.5 | January 02, 2026 | Initial consolidated draft including Smart Slots, CRVS consensus proposal, CGS, Cryftee modules, IPFS pinning rewards, and cross-network federated DAO governance. |

---

## Table of Contents

- [1. Abstract](#1-abstract)
- [2. Design goals and non-goals](#2-design-goals-and-non-goals)
- [3. Background and problem statement](#3-background-and-problem-statement)
- [4. System overview](#4-system-overview)
  - [4.1 Primary Network architecture (P-Chain + X-Chain + M-Chain)](#41-primary-network-architecture-p-chain--x-chain--m-chain)
  - [4.2 Validator cross-participation requirements](#42-validator-cross-participation-requirements)
  - [4.3 Hierarchical chain registration (Cities via States)](#43-hierarchical-chain-registration-cities-via-states)
  - [4.4 City-level account management (State-mediated balances)](#44-city-level-account-management-state-mediated-balances)
- [5. Network model and latency strategy](#5-network-model-and-latency-strategy)
- [6. Consensus and finality model (CRVS proposal)](#6-consensus-and-finality-model-crvs-proposal)
  - [6.6 Data availability sampling (DAS) extensions](#66-data-availability-sampling-das-extensions)
  - [6.7 ZK-EVM integration for validity proofs](#67-zk-evm-integration-for-validity-proofs)
- [7. Execution layer: EVM compatibility and deterministic parallelism](#7-execution-layer-evm-compatibility-and-deterministic-parallelism)
- [8. Standard subnet model vs custom subnets](#8-standard-subnet-model-vs-custom-subnets)
- [9. Cryft Global Synchronizer (CGS)](#9-cryft-global-synchronizer-cgs-privacy-propagation-and-federation-sync)
- [10. Cross-chain communication and settlement](#10-cross-chain-communication-and-settlement)
  - [10.5 ZK-based cross-chain verification](#105-zk-based-cross-chain-verification)
  - [10.6 User mobility and cross-region asset portability](#106-user-mobility-and-cross-region-asset-portability)
  - [10.7 Single-location guarantee: preventing cross-region double-spending](#107-single-location-guarantee-preventing-cross-region-double-spending)
  - [10.8 Region-first deployment with federation mirroring](#108-region-first-deployment-with-federation-mirroring)
  - [10.9 Balance portability modes](#109-balance-portability-modes)
  - [10.10 Initial supply and home region](#1010-initial-supply-and-home-region)
  - [10.11 Developer experience summary](#1011-developer-experience-summary)
- [11. Asset model, rewards, and monetary policy](#11-asset-model-rewards-and-monetary-policy)
- [12. Governance: federated DAO and cross-network democracy](#12-governance-federated-dao-and-cross-network-democracy)
- [13. Cryftee: signed WASM module runtime for chain utilities](#13-cryftee-signed-wasm-module-runtime-for-chain-utilities)
- [14. Security model and threat analysis](#14-security-model-and-threat-analysis)
  - [14.8 Multi-chain Main and hierarchical registration threats](#148-multi-chain-main-and-hierarchical-registration-threats)
  - [14.9 GBL, CMR, and SBL threats](#149-global-balance-ledger-gbl-contract-mirror-registry-cmr-and-state-balance-ledger-sbl-threats)

---

## 1. Abstract

CryftNet (Cryft Network) is a federation of blockchains designed to feel like Web2 in latency while
retaining cryptographic integrity and democratic governance. The network is anchored by the **Primary Network**, which consists of three specialized chains: **(1) P-Chain** for validator/subnet coordination and staking, **(2) X-Chain** for high-throughput native asset transfers and issuance, and **(3) M-Chain** for EVM-compatible smart contract execution. When we say "EVM chain," we mean the M-Chain specifically, not the entire Cryft network. This three-chain architecture prevents governance traffic, asset transfer traffic, and smart contract execution traffic from competing for the same bottleneck. Regional chains ("States") are optimized for low-latency execution and confirmations within a
geographic or network-latency domain. Optional local chains ("Cities") can further reduce latency for
dense communities and settle upward. CryftNet is EVM compatible by default. It introduces an opt-in
deterministic parallel execution mechanism called Smart Slots with Process IDs. Transactions may
declare a process_id and explicit slot claims that map to EVM state (account, storage, or
application-defined resource slots). A deterministic scheduler uses these claims to safely parallelize
execution, confining contention to lanes when necessary while preserving identical results across
validators. Privacy and propagation are addressed by Cryft Global Synchronizer (CGS), a
Cryftee-hosted plane that supports privacy-aware intent gossip, selective disclosure, and region-local
privacy pools, while still enabling scheduling via slot commitments. Cryftee itself is a Rust-based
sidecar runtime that loads signed WASM modules from a manifest, provides a versioned API over
UDS or HTTPS, and includes a kiosk UI for operators. Cryftee modules supply chain utilities including
BLS/TLS staking operations, IPFS node management, and private synchronization. Economic security is complemented by incentive alignment for availability: CryftNet includes explicit IPFS pinning rewards. Pin providers register, bond stake, accept pin jobs, and earn rewards based on verified availability proofs over time. The result is a federation where compute, consensus, privacy propagation, and content availability are governed and incentivized rather than assumed.

---

## 2. Design goals and non-goals

### 2.1 Goals

- Web2-like perceived latency via region-local confirmation and routing.
- EVM compatibility for mainstream wallets and developer tooling.
- Deterministic, opt-in parallel execution without breaking legacy contracts.
- Federated governance: Main chain as primary DAO; subnets as local DAOs; cross-network
voting support.
- Privacy-aware propagation (CGS) that reduces metadata leakage and resists censorship.
- Practical operations: signed module system (Cryftee) to ship chain utilities safely.
- Availability of content and tooling via IPFS pinning incentives.
- Region eligibility measurement using pings so validators serve the region they claim.

### 2.2 Non-goals

- Claiming infinite TPS or zero-latency global finality.
- Forcing all subnets to conform to a single VM or single consensus mechanism.
- Mandatory TEEs for security (TEEs may be used but are optional).
- Perfect anonymity guarantees; privacy is treated as measurable and adversarially tested.
- Assuming IPFS persistence without explicit incentives.

---

## 3. Background and problem statement

Global blockchains face two constraints: physics and contention. The speed of light and the Internet's
routing behavior impose a lower bound on propagation. At the same time, many workloads contend
on shared state (balances, nonces, popular contracts). Larger validator committees increase security
but also increase coordination time and validation bandwidth, creating diminishing returns on latency.
CryftNet treats latency domains as a design primitive. Instead of forcing one global committee to
finalize everything, regional committees provide fast local confirmations for nearby users. The Main
chain acts as a global settlement and governance anchor: regions periodically checkpoint upward,
enabling cross-region settlement without requiring every transaction to wait for global propagation.
Parallel execution is a complementary axis. EVM semantics are serial; naive parallelism breaks
determinism and can lead to chain splits. CryftNet introduces Smart Slots: explicit read/write claims
that enable deterministic, validator-consistent scheduling. When contracts cannot be parallelized,
they fall back to serial lanes. Modern networks also depend on content distribution: portals, module
artifacts, and application assets. IPFS makes this content-addressed and tamper-evident, but
availability remains an economic problem. CryftNet includes pinning rewards and auditable availability proofs so that "the network stays alive" is not a matter of goodwill.

---

## 4. System overview

CryftNet is organized as a federation:

- **Primary Network (P + X + M):** The canonical foundation consisting of three chains: P-Chain (validator/subnet management), X-Chain (native asset transfers), and M-Chain (EVM smart contracts). Together they provide settlement, cross-chain registries, global governance, and the primary validator DAO.
- **Regional chains (States):** Low-latency committees tuned for users within a latency domain. Most user activity is expected to be region-local and finalizes quickly.
- **Local chains (Cities):** Optional, for dense communities or enterprise enclaves. These settle to a region.
- **Cryftee plane:** A sidecar runtime deployed alongside validators and infrastructure nodes, hosting signed modules and CGS.
- **IPFS plane:** Content-addressed distribution for portals, modules, and application assets, with incentives for availability.

**Figure 1: CryftNet federation overview (conceptual)**

``mermaid
flowchart TB
  Main["Main / Federal Chain<br>(Global settlement + DAO)"]
  RegionA["Region A (CSS)<br>Low-latency committee"]
  RegionB["Region B (CSS)<br>Low-latency committee"]
  Local["Local chains<br>(optional)"]
  Custom["Custom subnets<br>(optional)"]
  Cryftee["Cryftee Sidecar<br>(WASM modules + CGS)"]
  IPFS["IPFS Plane<br>(portals, modules, content)"]
  RegionA -->|checkpoint| Main
  RegionB -->|checkpoint| Main
  Local -->|settle up| RegionA
  Local -->|settle up| RegionB
  Custom --> Main
  Cryftee -. deployed beside .- Main
  Cryftee -. deployed beside .- RegionA
  Cryftee -. deployed beside .- RegionB
  IPFS <--> Cryftee
  IPFS <--> Main
  IPFS <--> RegionA
  IPFS <--> RegionB
``

Main and regions are linked by checkpointing. Regions confirm locally, then periodically anchor a
signed checkpoint to Main. Cross-region transfers use these checkpoints and standard message
formats. The federation is "edge-like" in the sense that regions provide fast service nearby, but it
avoids centralized operators: validator sets are governed by DAOs and measured for eligibility using
network performance signals.

  IPFS <--> Main
  IPFS <--> RegionA
  IPFS <--> RegionB
```

Main and regions are linked by checkpointing. Regions confirm locally, then periodically anchor a
signed checkpoint to Main. Cross-region transfers use these checkpoints and standard message
formats. The federation is "edge-like" in the sense that regions provide fast service nearby, but it
avoids centralized operators: validator sets are governed by DAOs and measured for eligibility using
network performance signals.

### 4.1 Primary Network architecture (P-Chain + X-Chain + M-Chain)

Inspired by Avalanche's multi-chain architecture, CryftNet's Primary Network is composed of **three specialized chains**, each optimized for a distinct role. Cryft Labs maintains first-class implementations and long-term governance over all three chains, while subnets may add additional chains as needed:

| Chain | Purpose | VM | Consensus | Typical Operations |
|:------|:--------|:---|:----------|:-------------------|
| **P-Chain** (Platform) | Validator set management, staking, subnet lifecycle, chain registration/metadata, governance coordination | Native | CRVS (high security) | Validator add/remove, stake/unstake, subnet registration, governance proposals, slashing |
| **X-Chain** (Exchange) | Native asset creation and transfers optimized for throughput (UTXO-style), base asset movements | Native (UTXO) | CRVS (high throughput) | CRYFT transfers, asset issuance, cross-chain atomic swaps, high-frequency payments |
| **M-Chain** (EVM Execution) | Account-based smart contract execution compatible with Solidity/Vyper tooling (the dApp chain) | EVM | CRVS (fast finality) | Token contracts, DEX swaps, NFTs, DeFi protocols, user dApp interactions |

**Why three separate chains?**

1. **Performance isolation:** Validator/staking traffic (P-Chain), asset transfer traffic (X-Chain), and smart contract execution traffic (M-Chain) do not compete for the same bottleneck. This prevents governance operations from being priced out during DeFi congestion, and prevents EVM gas spikes from affecting base asset transfers.

2. **Security differentiation:** P-Chain can use more conservative parameters (larger committees, longer finality windows) for critical validator/subnet operations. X-Chain optimizes for throughput. M-Chain balances speed with EVM determinism requirements.

3. **Specialized state models:** P-Chain uses validator set / stake accounting. X-Chain uses UTXO for parallel asset transfers. M-Chain uses account-based EVM state. Each model is optimal for its domain.

4. **Upgrade isolation:** EVM upgrades (new opcodes, gas changes) affect only M-Chain. P-Chain and X-Chain native VMs can evolve independently based on federation needs.

5. **Economic clarity:** Staking rewards flow through P-Chain. Asset issuance/burns happen on X-Chain. DeFi fees stay on M-Chain. Clean separation prevents cross-subsidy confusion.

**P-Chain responsibilities:**

- **Validator Registry:** Global validator identities, stake bonds, delegation relationships, and slashing records. All staking operations occur on P-Chain.
- **Subnet Registry:** All State/Region chains register here with their chain_id, validator set commitments, consensus parameters, and CEP compatibility declarations.
- **Checkpoint Acceptance:** Receives and validates checkpoint submissions from all registered subnets; maintains the canonical checkpoint history.
- **Governance Coordination:** Proposal lifecycle, voting tallies, timelocks, and execution triggers. Governance decisions are recorded on P-Chain.
- **Validator Rewards Distribution:** Emission schedule, reward allocation, and validator/delegator payouts.

**X-Chain responsibilities:**

- **Native Asset Issuance:** Creation of new asset types (tokens, NFTs) with UTXO-based ownership.
- **High-Throughput Transfers:** Optimized for CRYFT and other native asset movements (not EVM tokens).
- **Cross-Chain Atomic Swaps:** UTXO-style atomic swaps between X-Chain assets and M-Chain ERC-20 tokens.
- **Base Layer Transfers:** Users moving large amounts of CRYFT between wallets typically use X-Chain (lower fees than M-Chain EVM gas).

**M-Chain responsibilities:**

- **EVM Smart Contracts:** All Solidity/Vyper contracts, DeFi protocols, NFT marketplaces, and dApps.
- **Global Balance Ledger (GBL):** The authoritative record of partitioned EVM token balances across all regionsâ€”tracking which account owns how much of each M-Chain asset on which region. (Note: Native CRYFT balances live on X-Chain; ERC-20 wrapped CRYFT lives on M-Chain.)
- **Contract Mirror Registry (CMR):** Authoritative record of federation contract deploymentsâ€”tracking target_regions[], deployed_regions[], mirror_status per region, and deployment fees paid. Updated via region checkpoints.
- **Federation Contract Registry:** Tracks CREATE2 deployments, code hashes, and cross-region contract verification.
- **User-Facing dApp Interface:** When users "interact with CryftNet," they typically transact on M-Chain (or regional M-Chain instances).

**Global Balance Ledger (GBL) architecture:**

The GBL tracks **M-Chain EVM token balances** (ERC-20, ERC-721, etc.) across regions. It does NOT track native CRYFT (that lives on X-Chain). The GBL is conceptually part of M-Chain's state but may be implemented as a native data structure for efficiency:

```text
GlobalBalanceLedger {
  // Per-asset, per-region, per-account balance
  balances: Map<(asset_id, region_id, account) â†’ uint256>
  
  // Total supply per asset (conservation invariant)
  total_supply: Map<asset_id â†’ uint256>
  
  // Pending cross-region transfers
  pending_transfers: Map<transfer_id â†’ PendingTransfer>
  
  // Conservation check: âˆ€ asset: Î£(balances[asset, *, *]) == total_supply[asset]
}

PendingTransfer {
  transfer_id: bytes32,
  asset_id: address,
  amount: uint256,
  from_region: uint64,
  to_region: uint64,
  sender: address,
  recipient: address,
  initiated_checkpoint: uint64,  // checkpoint where debit occurred
  status: enum { Pending, Claimed, Expired, Refunded }
}
```

**Why GBL lives on M-Chain (not C-Chain):**

1. **Native efficiency:** Balance tracking is a simple ledger operationâ€”no EVM overhead needed.
2. **Atomic with checkpoints:** When M-Chain accepts a State checkpoint, it atomically updates GBL balances.
3. **Single source of truth:** Eliminates sync issues between C-Chain contracts and M-Chain state.
4. **Simpler conservation checks:** M-Chain can enforce Î£(regional balances) = total_supply natively.
5. **Cross-region transfers as first-class operations:** Not contract calls, but native M-Chain transactions.

**GBL update flow:**

```mermaid
sequenceDiagram
  participant User
  participant StateA as State A
  participant MChain as M-Chain (GBL)
  participant StateB as State B
  
  User->>StateA: transferToRegion(asset, amount, B, recipient)
  StateA->>StateA: Debit local balance, emit TransferOut event
  StateA->>MChain: Checkpoint includes TransferOut
  MChain->>MChain: GBL: debit(asset, A, sender, amount)
  MChain->>MChain: GBL: pending_transfers[id] = {Pending...}
  MChain->>StateB: Checkpoint confirmation includes pending transfer
  StateB->>StateB: Credit local balance on claim
  StateB->>MChain: Next checkpoint confirms claim
  MChain->>MChain: GBL: credit(asset, B, recipient, amount)
  MChain->>MChain: GBL: pending_transfers[id].status = Claimed
```

**M-Chain EVM contracts and GBL:**

M-Chain EVM contracts can **query** GBL state (which tracks M-Chain token balances across regions):

```text
// M-Chain EVM contract can query GBL
function getRegionalBalance(address asset, uint64 regionId, address account) 
  returns (uint256) {
  return GBL.balances[asset][regionId][account];
}

// Useful for:
// - DeFi protocols that need to know user's federation-wide balance
// - Governance contracts weighting votes by total holdings
// - Treasury contracts distributing rewards proportionally
```

Note: Native CRYFT balances live on X-Chain (UTXO model). M-Chain sees wrapped CRYFT (ERC-20) only.

**Contract Mirror Registry (CMR) architecture:**

The CMR is M-Chain's native data structure for tracking federation contract deployments and mirror state:

```text
ContractMirrorRegistry {
  // Per-contract deployment record
  contracts: Map<contract_address â†’ ContractMirrorRecord>
  
  // Region deployment queue (contracts pending mirroring)
  pending_mirrors: Map<(contract_address, region_id) â†’ PendingMirror>
  
  // Fee tracking per contract
  fees_paid: Map<contract_address â†’ FeeRecord>
}

ContractMirrorRecord {
  contract_address: address,
  code_hash: bytes32,
  deployer: address,
  salt: bytes32,
  home_region: uint64,                    // Where initial deployment occurred
  target_regions: uint64[],               // Regions developer opted into
  deployed_regions: uint64[],             // Regions where contract is live
  mirror_status: Map<region_id â†’ MirrorStatus>,  // Per-region status
  balance_portability: bool,
  verification_level: VerificationLevel,  // Unverified, Publisher, Federation
  created_at: uint64,
  last_updated: uint64
}

MirrorStatus {
  status: enum { Pending, Deployed, Failed, Revoked },
  deployed_at: uint64,
  init_hash: bytes32,          // Hash of initialization data
  initialized: bool,
  last_checkpoint: uint64      // Last checkpoint confirming this region
}

// Status transitions via region checkpoints:
// 1. Main receives deployment event â†’ creates record, status[home] = Deployed
// 2. Main queues mirror to target_regions â†’ status[target] = Pending
// 3. Region confirms deployment â†’ status[target] = Deployed
// 4. Region reports failure â†’ status[target] = Failed (auto-retry)
```

**CMR update flow (region-first deployment):**

```text
1) Developer deploys on Region A:
   - RegionDeployer.deploy(init_code, salt, options={target_regions: [A,B,C]})
   - Emits DeploymentEvent with region IDs and fee payment

2) Region A checkpoint â†’ Main M-Chain:
   - M-Chain processes DeploymentEvent
   - CMR creates: contracts[0xToken] = {
       home_region: A,
       target_regions: [A, B, C],
       deployed_regions: [A],
       mirror_status: {A: Deployed, B: Pending, C: Pending}
     }

3) Main triggers mirror to Regions B, C:
   - CMR updates: pending_mirrors[(0xToken, B)] = {queued}
   - CMR updates: pending_mirrors[(0xToken, C)] = {queued}

4) Region B, C receive mirror instruction and deploy:
   - RegionDeployer.mirror() called on each region
   - Region confirms in next checkpoint

5) Region B checkpoint â†’ Main M-Chain:
   - M-Chain updates CMR: deployed_regions: [A, B], mirror_status[B] = Deployed

6) Region C checkpoint â†’ Main M-Chain:
   - M-Chain updates CMR: deployed_regions: [A, B, C], mirror_status[C] = Deployed

CMR is authoritative - regions derive mirror permissions from M-Chain state.
```

**CMR region expansion (post-deployment):**

```text
1) Developer requests expansion to Region D:
   - Calls FederationRegistry.expandRegions(0xToken, [D])
   - Pays expansion fee (0.01 CRYFT per region)

2) Checkpoint carries expansion request to Main:
   - M-Chain verifies caller == deployer
   - M-Chain verifies fee paid
   - CMR updates: target_regions: [A, B, C, D]
   - CMR updates: mirror_status[D] = Pending

3) Main triggers mirror to Region D

4) Region D confirms deployment in checkpoint:
   - CMR updates: deployed_regions: [A, B, C, D], mirror_status[D] = Deployed
```

**Cross-chain communication (P â†” X â†” M):**

The Primary Network's three chains share the same validator set and use atomic messaging:

```text
P-Chain â†” M-Chain:
- Validator set updates (P â†’ M for on-chain verification in M-Chain contracts)
- Governance execution results (P â†’ M to trigger contract upgrades)
- Stake/unstake requests (M â†’ P when users interact via M-Chain interface)
- Checkpoint finality confirmations (P â†’ M for subnet validation)
- Slashing events (P â†’ M to freeze validator-operated contracts)

X-Chain â†” M-Chain:
- CRYFT wrapping/unwrapping (X â†” M for native â†” ERC-20 bridge)
- Cross-chain atomic swaps (X â†” M for asset exchanges)
- Asset issuance events (X â†’ M when native assets need EVM representation)

P-Chain â†” X-Chain:
- Validator reward payouts (P â†’ X for native CRYFT distribution)
- Emission schedule updates (P â†’ X for minting authorization)
```

All three chains share the same block production schedule and validators, ensuring atomic cross-chain messaging without external bridges or delays.

```mermaid
flowchart TB
  subgraph Primary["Primary Network"]
    PChain["P-Chain<br>(Validators, staking, subnets)"]
    XChain["X-Chain<br>(Native assets, transfers)"]
    MChain["M-Chain<br>(EVM contracts, dApps)"]
    PChain <-->|atomic messaging| MChain
    PChain <-->|atomic messaging| XChain
    XChain <-->|atomic messaging| MChain
  end
  RegionA["Region A (State)"]
  RegionB["Region B (State)"]
  end
  RegionA["Region A (State)"]
  RegionB["Region B (State)"]
  CityA1["City A1"]
  CityA2["City A2"]
  RegionA -->|checkpoint| PChain
  RegionB -->|checkpoint| PChain
  CityA1 -->|settle up| RegionA
  CityA2 -->|settle up| RegionA
  RegionA -.->|register via| PChain
  CityA1 -.->|register via| RegionA
```

### 4.2 Validator cross-participation requirements

A key architectural question is whether subnet (State/Region) validators must also validate the Primary Network. CryftNet adopts a **tiered requirement model**:

**Tier 1: CSS-1 State chains (required Primary Network participation)**

Validators for Cryft Standard Subnet (CSS-1) State chains **must** also be validators on the Primary Network (validating P-Chain, X-Chain, and M-Chain). This requirement ensures:

- **Security alignment:** State validators have direct stake in the Primary Network's security (via P-Chain staking), preventing "vampire" attacks where a State chain extracts value without contributing to federation security.
- **Checkpoint integrity:** Validators who sign State checkpoints also validate those checkpoints on P-Chain, creating accountability.
- **Governance participation:** State validators participate in Primary Network governance (via P-Chain), ensuring federation decisions reflect the interests of active State operators.
- **Simplified slashing:** Misbehavior on a State chain can be slashed on P-Chain without complex cross-chain evidence.

**Tier 2: Custom subnets (optional Primary Network participation)**

Custom subnets (non-CSS) may choose whether their validators participate in the Primary Network:

| Participation Level | Requirements | Benefits | Trade-offs |
|:--------------------|:-------------|:---------|:-----------|
| **Full** | Validate Main + subnet | Full federation services, governance rights, priority routing | Higher operational cost |
| **Partial** | Stake on Main, validate subnet only | Bridge access, registry listing, basic services | No governance votes, standard routing |
| **None** | Subnet-only validation | Maximum independence | No federation services, manual bridging only |

**Minimum stake requirements:**

```text
Main validator:           100,000 CRYFT minimum stake
CSS-1 State validator:    50,000 CRYFT additional stake (per State)
Custom subnet validator:  Defined by subnet parameters
City validator:           Defined by parent State (typically lower)
```

**Cross-validation benefits:**

- Validators earn rewards from both Main and subnet block production.
- Unified slashing: a single misbehavior affects all validator roles.
- Simplified key management: same validator identity across chains.
- Reputation portability: good behavior on Main improves subnet opportunities.

**Exemptions and transitions:**

- New State chains may request a **bootstrap period** (up to 6 months) where validators are not required to validate Main, allowing the State to establish itself before full integration.
- Validators may **delegate** their Main validation duties to a trusted operator while retaining their subnet role, subject to delegation limits.

### 4.3 Hierarchical chain registration (Cities via States)

CryftNet supports a three-tier hierarchy: Main â†’ State (Region) â†’ City (Local). A critical design decision is whether City chains must register directly with Main or can register only via their parent State.

**Recommended model: State-mediated City registration**

City chains register **only with their parent State chain**, not directly with Main's M-Chain. This enables:

1. **Faster experimentation:** Launching a City requires only State DAO approval, not Main governance. This allows rapid iteration for local communities, enterprise enclaves, and specialized use cases.

2. **Reduced Main burden:** Main's M-Chain does not need to track potentially thousands of City chains. It only tracks the ~10-100 State chains.

3. **State sovereignty:** States can define their own City policiesâ€”minimum stake, validator requirements, allowed VMs, and compliance rulesâ€”without Main override.

4. **Appropriate trust model:** Users of a City chain trust their State chain; they don't need global Main consensus for local operations.

**State-level City Registry:**

Each CSS-1 State chain maintains a **City Registry** contract/module with:

```text
CityRegistration {
  city_id: uint64,
  city_chain_id: uint256,
  parent_state_id: uint64,
  validator_set_hash: bytes32,
  consensus_type: string,
  vm_type: string,                  // "EVM", "WASM", "Custom"
  cep_compatibility: string,        // "CSS-1", "CSS-lite", "none"
  checkpoint_frequency: uint32,     // blocks between checkpoints to State
  registered_at: uint64,
  status: enum { Active, Suspended, Deregistered },
  metadata_cid: string              // IPFS CID for extended metadata
}
```

**City â†’ State settlement:**

Cities checkpoint to their parent State (not to Main):

```mermaid
flowchart LR
  City["City Chain"] -->|checkpoint every N blocks| State["State Chain"]
  State -->|aggregated checkpoint| Main["Main M-Chain"]
  State -->|includes City summary| Main
```

The State's checkpoint to Main **may include** an aggregated City summary (Merkle root of City checkpoints), but this is optional. Main does not verify City checkpoints directlyâ€”it trusts the State to manage its Cities.

**City benefits and limitations:**

| Capability | City via State | Direct Main registration |
|:-----------|:---------------|:-------------------------|
| Registration latency | Minutes (State DAO) | Days-weeks (Main governance) |
| Federation Contract Registry | Via State (inherited) | Direct Main access |
| Cross-State bridging | Through State first | Direct (if allowed) |
| Main governance participation | None (vote via State) | Possible |
| Visibility to Main | Aggregated only | Full |
| Slashing authority | State | Main |

**Cross-City transfers (same State):**

Transfers between Cities under the same State settle via the State chain without touching Main:

```text
City A1 â†’ City A2 (same State A):
1. City A1 includes transfer in checkpoint to State A
2. State A verifies and includes in State block
3. City A2 claims from State A's confirmed checkpoint
4. No Main involvement required
```

**Cross-City transfers (different States):**

Transfers between Cities under different States route through Main:

```text
City A1 (State A) â†’ City B1 (State B):
1. City A1 checkpoints to State A
2. State A checkpoints to Main (includes City A1's outbound message)
3. State B receives from Main
4. City B1 claims from State B
```

**City upgrade path:**

A successful City may choose to "graduate" to State status:

1. City demonstrates sustained activity and validator quality.
2. City applies to Main governance for State registration.
3. Upon approval, City registers directly with M-Chain.
4. City's existing users and contracts migrate or bridge.
5. City can now spawn its own sub-Cities.

### 4.4 City-level account management (State-mediated balances)

Since Cities register only via their parent State (not directly with Main), their account balances are managed **through the State**, not the federal M-Chain's Global Balance Ledger. This creates a clean separation:

| Level | Balance Authority | Settlement Target | Account Visibility |
|:------|:------------------|:------------------|:-------------------|
| Main (C-Chain/M-Chain) | M-Chain GBL | Final (self) | Global |
| State | M-Chain GBL (via checkpoints) | Main | Global |
| City | State Balance Ledger (SBL) | Parent State | State-local only |

**State Balance Ledger (SBL):**

Each CSS-1 State maintains its own **State Balance Ledger** for its Cities, mirroring M-Chain's GBL structure but at the State level:

```text
StateBalanceLedger {
  // Per-asset, per-city, per-account balance
  city_balances: Map<(asset_id, city_id, account) â†’ uint256>
  
  // State-level aggregate (what M-Chain GBL sees for this State)
  state_total: Map<(asset_id, account) â†’ uint256>
  
  // Invariant: state_total[asset, account] = 
  //   state_direct[asset, account] + Î£(city_balances[asset, *, account])
  
  // Pending Cityâ†’City and Cityâ†’State transfers
  pending_city_transfers: Map<transfer_id â†’ PendingCityTransfer>
}
```

**Key architectural principle: Main doesn't see City accounts**

From Main's perspective, a State is a single entity. The GBL tracks:
- `balances[USDC, State_A, Alice] = 1000`

But within State A, Alice's 1000 USDC might be distributed:
- State A direct: 200 USDC
- City A1: 500 USDC
- City A2: 300 USDC

Main doesn't know or care about this internal distributionâ€”it's State A's responsibility to manage.

**Cityâ†’City transfers (same State):**

```text
City A1 â†’ City A2 transfer (both under State A):

1) User on City A1 calls cityBridge.transferToCity(asset, amount, cityA2, recipient)
2) City A1 debits local balance, emits CityTransferOut
3) City A1 checkpoints to State A
4) State A's SBL updates:
   - city_balances[USDC, A1, Alice] -= 500
   - pending_city_transfers[id] = {Pending, dest=A2, ...}
5) City A2's next checkpoint sync from State includes pending transfer
6) Recipient claims on City A2
7) City A2 checkpoints claim confirmation to State A
8) State A's SBL updates:
   - city_balances[USDC, A2, Bob] += 500
   - pending_city_transfers[id].status = Claimed

Note: Main M-Chain is NOT involved. State A's total balance is unchanged.
```

**Cityâ†’State transfer (escalation):**

```text
City A1 â†’ State A direct transfer:

1) User calls cityBridge.escalateToState(asset, amount, recipient)
2) City A1 debits, checkpoints to State A
3) State A's SBL:
   - city_balances[USDC, A1, Alice] -= 500
   - state_direct[USDC, Alice] += 500
4) Alice can now spend directly on State A (faster, more liquidity)

Main still sees: balances[USDC, State_A, Alice] = 1000 (unchanged)
```

**Cityâ†’Different State transfer (requires Main):**

```text
City A1 (State A) â†’ State B transfer:

1) City A1: cityBridge.transferToRegion(asset, amount, State_B, recipient)
2) City A1 checkpoints to State A with cross-State intent
3) State A's SBL:
   - city_balances[USDC, A1, Alice] -= 500
   - Cross-State transfer queued for next Main checkpoint
4) State A checkpoints to Main M-Chain with:
   - TransferOut(USDC, 500, from=State_A, to=State_B, ...)
5) M-Chain GBL:
   - balances[USDC, State_A, Alice] -= 500
   - pending_transfers[id] = {Pending, to=State_B, ...}
6) State B receives, recipient claims
7) M-Chain GBL: balances[USDC, State_B, Bob] += 500

Note: Main only sees State-level balances. It doesn't know the transfer originated from a City.
```

**City balance visibility:**

| Query | Where to Ask | Response |
|:------|:-------------|:---------|
| "What's my total balance?" | Main M-Chain GBL | Sum across all States |
| "What's my State A balance?" | Main M-Chain GBL | Single State total |
| "What's my City A1 balance?" | State A SBL | City-specific balance |
| "Where exactly are my assets?" | State A SBL + each City | Full breakdown |

**Wallets and City balances:**

Wallets display City-level balances by:
1. Querying M-Chain GBL for State-level totals
2. For each State with balance > 0, querying the State's SBL for City breakdown
3. Displaying hierarchical view:

```text
Alice's USDC:
â”œâ”€â”€ Main:           500 USDC
â”œâ”€â”€ State A:      1,000 USDC
â”‚   â”œâ”€â”€ Direct:     200 USDC
â”‚   â”œâ”€â”€ City A1:    500 USDC
â”‚   â””â”€â”€ City A2:    300 USDC
â””â”€â”€ State B:        250 USDC
    â””â”€â”€ Direct:     250 USDC
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Total:            1,750 USDC
```

**Why Cities don't register with Main:**

This hierarchical model provides:

1. **Scalability:** Main GBL tracks ~100 States, not ~10,000 Cities.
2. **State sovereignty:** States control their City ecosystem without Main approval.
3. **Latency:** Cityâ†”City transfers within a State are fast (no Main checkpoint wait).
4. **Appropriate trust:** City users trust their State; they don't need global Main consensus.
5. **Simpler Main governance:** Main governs States; States govern Cities.

**City emergency exit:**

If a City chain fails or its State censors it, users can still recover:

1. Prove City balance via State's last confirmed checkpoint
2. Submit proof to State requesting balance escalation to State-direct
3. If State refuses, appeal to Main governance with evidence
4. Main can force-escalate City balances to State level (emergency measure)
5. User then exits Stateâ†’Main via normal cross-region transfer

This ensures users are never permanently trapped in a City.

This hierarchical model balances federation coherence with local autonomy, enabling CryftNet to scale to thousands of chains without overwhelming Main governance.

## 5. Network model and latency strategy

### 5.1 Regions as latency domains

A region is defined as a set of validators and routing policies optimized for a latency domain. The
domain can be geographic (e.g., Midwest US) or network-derived (e.g., a set of AS paths). The key
requirement is that a significant portion of users experience low RTT (round-trip time) to a sufficient
number of regional validators.

### 5.2 Validator eligibility via ping measurements

To prevent a "region" from being nominal only, CryftNet uses ping-based eligibility. A validator is
eligible for Region R only if it can demonstrate sustained low-latency connectivity to a quorum of
Region R measurement beacons.
Mechanism (proposal): 1) Region R maintains a Beacon Set: B = {b1..bm}. Beacons are run by
independent operators approved by the region DAO and optionally co-hosted by regional validators.
2) During each epoch, validators perform signed ping sessions to beacons using a fixed protocol
(e.g., QUIC PING or UDP echo with replay protection). Beacons also ping validators. 3) Beacons emit
signed measurement reports containing distribution summaries (p50, p95, loss rate, jitter) and
timestamps. 4) Validators submit an aggregated proof to the region chain. The chain computes an
Eligibility Score.
```text
EligibilityScore(v, R) =

  w1 * clamp(1 - p95_rtt(v,R)/RTT_MAX, 0, 1)
+ w2 * clamp(1 - loss(v,R)/LOSS_MAX, 0, 1)
+ w3 * clamp(1 - jitter(v,R)/JITTER_MAX, 0, 1)
+ w4 * beacon_quorum_ok(v,R)
Constraints:
- beacon_quorum_ok requires at least q of m beacons reporting in-window measurements.
- reports are signed by beacons and include nonces to prevent replay.

---

to ensure their validator sets are actually region-serving. Validators may participate in Main and in
multiple regions, but each region can enforce its own RTT thresholds and scoring. Mitigations against
gaming include: multi-beacon diversity, random challenge timing, cross-check pings from validators to
each other, and penalties for detected proxy/VPN abuse.
```

### 5.3 User routing and failover

Clients choose a region through a combination of DNS hints, signed region metadata (published on
Main), and direct latency probing. If a region degrades (beacon reports, missed blocks, or poor p95),
clients fail over to a nearby region or to the Main chain for safety-critical operations. Regions can also
choose to temporarily increase anchoring frequency to Main during instability.

### 5.4 Diminishing returns: why committee size has a ceiling

For a fixed network, increasing validators increases message fanout and signature verification cost.
Beyond a point, latency improves more by splitting into regions than by growing a single committee.
CryftNet therefore expects: - Main: moderate committee size optimized for security and global
settlement cadence. - Regions: smaller committees optimized for p50/p95 latency. - Local chains:
smallest committees, often for specialized workloads.

### 5.5 Optional overlay mesh transport (Nebula reference implementation)

CryftNetâ€™s *architecture* only assumes an authenticated, low-jitter transport between validators and supporting services (Cryftee, beacons, pin auditors). It does **not** require any specific overlay network. However, an overlay mesh can be a pragmatic way to:

- reduce reliance on public IP exposure (validators can keep private addressing and still form a stable mesh),
- enforce mutual authentication and segmentation via cryptographic identities and groups,
- standardize private service discovery for operator tooling and Cryftee modules (UDS/HTTPS endpoints),
- provide an operational â€œback channelâ€ for upgrades, telemetry, and incident response.

A concrete candidate is **Nebula** (a WireGuard-style encrypted mesh with lighthouses and optional relays). Recommended stance:

- **Consensus plane:** prefer direct, performance-tuned UDP/QUIC links on public or private underlay whenever possible. If Nebula is used for consensus traffic, it should be *measured* and treated as a tunable deployment choice because overlays can add jitter and introduce relay-path outliers.
- **Control plane:** Nebula is an excellent fit (Cryftee management API, beacons, pin-auditor coordination, internal RPC, dashboards), because security and operability dominate micro-latency.

Latency note: Nebula typically adds only small per-packet overhead (encryption + encapsulation). The real risk is *path inflation* when traffic hairpins through lighthouses/relays or when MTU issues cause fragmentation. These risks should be monitored via the existing ping/eligibility telemetry and treated like any other transport variable.

Security note: the main advantage is **cryptographic identity at the network layer** (mutual auth, key rotation, segmentation) and the ability to keep services non-public while still reachable by authorized peers. It is not a substitute for protocol-layer authentication; it is a defense-in-depth layer.

---

## 6. Consensus and finality model (CRVS proposal)

CryftNet's consensus design aims to combine fast propagation, low coordination overhead, and rapid
finality within regions. We propose a stack nicknamed CRVS: Cryft Rotor-Votor Snow. It combines: -
Rotor-like propagation: efficient dissemination of candidate blocks and transaction data using rotating
relay roles. - Votor-like voting: fast-path vote aggregation for quick finality and slow-path recovery
during partial synchrony. - Avalanche-style metastable sampling: leaderless or low-leader
coordination where nodes repeatedly sample peers and converge on a preferred candidate with high
probability.

### 6.1 Data propagation plane (rotor-inspired)

Propagation is about moving bytes, not deciding truth. CRVS uses rotating relays to reduce
redundant broadcast. Relays are chosen deterministically per round (e.g., hash of epoch, round, and
validator key). Relays are not authorities: they only accelerate dissemination. If relays fail or censor,
fallback is direct gossip.
Inputs:
- committee V of size n
- round r within epoch e

- relay_count t (e.g., 3-7)
```text
RelaySet(e,r) = smallest t validators by score( H("relay"||e||r||vk) )
Protocol:
1) proposer sends candidate header to RelaySet(e,r)
2) relays fetch missing tx data by content hash and broadcast compact references
3) peers request missing chunks; relays respond; peers also serve each other
Fallback: if relay responsiveness drops below threshold, revert to all-to-all gossip.
```

### 6.2 Candidate production: leaderless or soft-leader

CRVS can run in a leaderless mode where multiple proposers may submit candidate blocks for the
same slot. The network then converges on one candidate via voting/sampling. A soft-leader variant
reduces forks by selecting a preferred proposer, but nodes remain free to accept alternatives if the
leader is slow or censored.
Slot s:
- Any validator may propose candidate C = (header, tx_list, parent_ref)
- Valid candidates are those with valid parent_ref, correct block time window, and valid txs.
Deterministic tie-break:
```text
PreferredCandidateSet = all valid candidates seen within âˆ†propagate
Rank(C) = (slot s, H(C.header), proposer_vk)
Choose smallest Rank among candidates that reach vote threshold.
```

### 6.3 Voting and finality (votor-inspired fast/slow paths)

Voting determines finality. CRVS uses a two-path structure: Fast path: when network is healthy and
participation is high, validators aggregate votes quickly to finalize a candidate. Slow path: when
participation is partial or network is unstable, the protocol falls back to repeated rounds and higher
confirmation thresholds before finalizing. Votes are signed; aggregation may use BLS signatures to
reduce bandwidth, or threshold aggregation via Cryftee modules.
Definitions:
- quorum_fast = ceil(0.67 * n)          # target; tunable by governance
- quorum_slow = ceil(0.80 * n)          # more conservative
- rounds_fast = 1..2
- rounds_slow = up to Rmax (e.g., 8)
Fast path:
1) collect votes for candidate C during round r
2) if votes(C) >= quorum_fast and no conflicting candidate with >= quorum_fast, finalize C
Slow path:
1) repeat vote rounds; if conflict persists, prefer candidate with higher confidence score from
2) finalize when votes(C) >= quorum_slow for consecutive k rounds (k >= 2)

### 6.4 Metastable sampling (Avalanche-inspired)


---

queries. Each validator periodically samples k peers and asks which candidate they currently prefer
for slot s (or which parent tip they prefer). If a candidate repeatedly exceeds an acceptance threshold
alpha across consecutive rounds beta, the node increases its confidence. This tends to produce
metastable convergence: once a majority leans one way, it becomes increasingly likely that the whole

network converges.
Parameters (example):
- k = 20               # sample size
- alpha = 15           # acceptance threshold (alpha <= k)
- beta = 12            # consecutive successful samples to decide
```text
Loop for slot s:
conf[C] = 0 for all candidates C
while not finalized:
  S = sample_k_peers()
  counts = query_preference(S, s)
  C* = argmax(counts)
  if counts[C*] >= alpha:
     conf[C*] += 1
  else:
     conf[C*] = max(conf[C*] - 1, 0)
  if conf[C*] >= beta:
     cast_vote(C*)
     (finalization still requires Section 6.3 thresholds)
```

### 6.5 Finality layering: region soft-finality vs Main hard-finality

Regions provide fast soft-finality (practically irreversible under normal operation). Main provides
hard-finality for cross-region settlement by accepting checkpoints. A checkpoint is a region-signed
commitment to a region block height and state root (or output root) plus proof of validator quorum.
Once Main finalizes a checkpoint, cross-region transfers referencing that checkpoint can be treated as final under Main's security assumptions.

### 6.6 Data availability sampling (DAS) extensions

CRVS focuses on consensus efficiency within committees, but does not inherently solve the data availability problem at scale. Data Availability Sampling (DAS), as demonstrated by Ethereum's PeerDAS (introduced via the Fusaka upgrade in December 2025), enables nodes to verify that block data is available for reconstruction by sampling small fragments rather than downloading entire blocks.

CryftNet can integrate DAS as an optional enhancement layer:

**How DAS complements CRVS:**

- **Checkpoint data availability:** Before Main accepts a region checkpoint, light clients or sampling nodes can verify that the underlying region block data is available without downloading the full block. This is especially valuable for cross-region settlement where Main validators should not need to store all region data.
- **Scalability without centralization:** DAS allows larger block sizes (higher throughput) while preserving the ability for resource-constrained nodes to participate in verification. This aligns with CryftNet's goal of Web2-like latency without sacrificing decentralization.
- **BitTorrent-style distribution:** DAS works like "BitTorrent with consensus"â€”data is erasure-coded and distributed across peers. Nodes sample random chunks and use cryptographic commitments (e.g., KZG polynomial commitments) to verify availability.

**Integration points:**

- **Region block producers** erasure-code block data and publish KZG commitments.
- **Region validators** perform DAS sampling before voting on block validity.
- **Main checkpoint verification** can optionally require DAS proofs that region data was available at checkpoint time.
- **Cryftee modules** can implement DAS sampling logic and commitment verification.

```text
DAS Verification (simplified):
1) Block producer computes erasure-coded chunks: C_1..C_n
2) Producer publishes KZG commitment: commit(C_1..C_n)
3) Sampler requests k random chunks from peers
4) Sampler verifies chunk inclusion against commitment
5) If >= threshold chunks verified, data is considered available
   with high probability (e.g., 99.9% with k=75 samples)
```

DAS is not mandatory for CSS-1 compliance but is recommended for high-throughput regions and for any chain seeking trustless light client support.

### 6.7 ZK-EVM integration for validity proofs

Zero-knowledge Ethereum Virtual Machines (ZK-EVMs) enable cryptographic proof-based validation of transaction batches. Instead of re-executing transactions, validators can verify a succinct proof that execution was performed correctly. This dramatically reduces computational load and enables trustless cross-chain verification.

**Current state (as of January 2026):**

ZK-EVMs have reached production-quality performance, with ongoing safety hardening. Full adoption as the primary validation method is expected between 2027 and 2030. CryftNet is positioned to adopt ZK proofs incrementally.

**ZK-EVM integration points in CryftNet:**

- **Checkpoint validity proofs:** Regions can attach ZK proofs to checkpoints, allowing Main to verify region state transitions without re-executing transactions. This enables:
  - Trustless light clients on Main
  - Reduced Main validator computational requirements
  - Faster checkpoint acceptance (verify proof vs. download and re-execute)

- **Cross-chain settlement:** ZK proofs can replace or supplement quorum signatures for cross-chain message verification, reducing trust assumptions from "2/3 of region validators are honest" to "the ZK proof system is sound."

- **Custom subnet bridging:** Non-EVM subnets can provide validity proofs for their state transitions, enabling trustless bridging to Main without requiring Main to understand the subnet's execution semantics.

- **CGS privacy proofs:** ZK proofs can attest to properties of private transactions (e.g., "this transfer is valid and the sender had sufficient balance") without revealing transaction details.

**Proof types supported:**

| Proof System | Use Case | Trade-offs |
|:-------------|:---------|:-----------|
| ZK-SNARK | Checkpoint validity, cross-chain proofs | Small proofs, fast verification; trusted setup or universal setup required |
| ZK-STARK | High-security applications, post-quantum | Larger proofs, no trusted setup, quantum-resistant |
| Hybrid | Recursive composition | Combine SNARK efficiency with STARK security for critical paths |

**Phased adoption roadmap:**

1. **Phase 1 (2026):** Optional ZK proofs for checkpoint verification; regions may provide proofs for faster Main acceptance.
2. **Phase 2 (2027-2028):** ZK-EVM provers integrated into Cryftee modules; CSS-1 regions encouraged to produce validity proofs.
3. **Phase 3 (2028-2030):** ZK proofs become the default verification method; quorum signatures retained as fallback and for governance.

```text
Checkpoint with ZK validity proof:
Checkpoint_ZK = {
  region_id: 42,
  chain_id: 1001,
  height: 8_240_112,
  block_hash: 0x...,
  state_root: 0x...,
  prev_state_root: 0x...,
  validity_proof: {
    type: "ZK_SNARK" | "ZK_STARK",
    proof: 0x...,
    public_inputs: [prev_state_root, state_root, block_hash],
    verifier_contract: 0xVerifier...
  },
  // quorum signature optional if validity_proof present
  quorum: { ... } | null
}
```

**Relationship to the blockchain trilemma:**

The combination of DAS (Section 6.6) and ZK-EVMs addresses the classic trilemma:

- **Decentralization:** DAS allows resource-constrained nodes to verify data availability; ZK proofs allow lightweight verification of execution.
- **Security:** Cryptographic proofs (KZG for DAS, ZK for execution) provide mathematical guarantees rather than economic/game-theoretic ones.
- **Scalability:** Larger blocks and parallel execution become viable when verification cost is decoupled from execution cost.

CRVS remains the consensus backboneâ€”DAS and ZK-EVMs are complementary technologies that enhance what CRVS-based committees can achieve.

---

## 7. Execution layer: EVM compatibility and deterministic parallelism

### 7.1 Baseline EVM mode

CryftNet remains compatible with standard EVM transactions. Legacy transactions are executed
serially and need not include any Cryft-specific fields. Standard wallets and tooling continue to work
unmodified.

### 7.2 Parallel execution mode (opt-in)

Parallel mode is opt-in. A transaction may declare that it participates in deterministic parallel
scheduling by including: - process_id: identifies a workflow lane and namespace - slot_claims: explicit
read/write claims over state slots - slot_commitment: a commitment hash over slot_claims, enabling
private propagation via CGS

### 7.3 Smart Slots and Process IDs (canonical model)

Smart Slots represent the smallest schedulable units of state contention. The goal is not to perfectly
capture every possible data dependency, but to capture enough structure that most real workloads
can safely parallelize while maintaining determinism.

#### 7.3.1 Slot types

- Account Slot: derived from an address. Used for nonce, balance, and code hash transitions. Any
transaction that modifies an account's nonce or balance claims WRITE on the account slot.
- Storage Slot: derived from (contract_address, storage_key). Claims map to EVM
SLOAD/SSTORE keys. A transaction that writes a given key claims WRITE on that slot; reads
claim READ.
- Object/Resource Slot: derived from an application resource ID (e.g., gift_code_id). Used when
an app wants parallelism without over-claiming whole accounts.
#### 7.3.2 Slot derivation

Slot IDs are computed by hashing a canonical encoding. The encoding includes a domain separator,
chain identity, scope, and type-specific data. Scope distinguishes Main from subnets (regions) and
prevents accidental collisions.
```text
slot_id = H(
  domain || chain_id || scope_id || process_id ||
  slot_type || addr || key || extra
)
Where:
- H() is keccak256 (or another fixed hash function) over bytes.
- domain is a constant ASCII tag, e.g., "CRYFT:SLOT:V1"
- chain_id identifies the chain (Main or subnet).
- scope_id = 0 for Main; = subnet_id (or region_id) for subnets.
- slot_type in {ACCOUNT, STORAGE, OBJECT}
- addr/key/extra are type-dependent fields.
Worked input composition examples (illustrative):
Example A (Account Slot): domain='CRYFT:SLOT:V1' | chain_id=1 | scope_id=0 | process_id='payment
Example B (Storage Slot): domain='CRYFT:SLOT:V1' | chain_id=1001 | scope_id=42 | process_id='gif
```

#### 7.3.3 Process IDs

A process_id identifies a workflow lane and its namespace. In the simplest case, process_id is a
human-readable string namespaced by the publisher, e.g., "cryft.giftcodes.v1". Governance may
reserve process_id prefixes for critical system workflows. A process_id can also be derived
deterministically from a contract address and ABI signature, but string-based IDs improve auditability.
#### 7.3.4 Transaction format extensions

Legacy transactions are unchanged. Parallel transactions add an envelope. Example (JSON-like):
```jsonc
// 1) Legacy transaction (unchanged)
{
  "type": "legacy",
  "from": "0xAlice",
  "to": "0xBob",
  "value": "0.05 ETH",
  "data": "0x",
  "gas": 21000,
  "nonce": 17
}

// 2) Parallel transaction with explicit slot claims
{
  "type": "cryft_parallel",
  "from": "0xAlice",

---

  "data": "0x<call redeem(code_id, ...)>",
  "gas": 250000,
  "nonce": 18,
  "process_id": "cryft.giftcodes.v1",
  "slot_claims": [
    {"slot_id": "0xSLOT(account:0xAlice)", "mode": "WRITE"},
    {"slot_id": "0xSLOT(object:gift_code:0xC0DE)", "mode": "WRITE"},
    {"slot_id": "0xSLOT(storage:0xGiftContract:0xKey1)", "mode": "READ"}
  ],
  "slot_commitment": "0xKECCAK(slot_claims_canonical_bytes)",
  "capabilities": ["cap:giftcodes.redeem.v1"],
  "conflict_policy": {"mode": "prelock"}
}
// 3) Private intent envelope (CGS) - claims committed, not revealed publicly until inclusion
{
  "type": "cryft_private_intent",
  "from": "0xAlice",
  "to": "0xGiftContract",
  "data_ciphertext": "0x...",
  "gas": 250000,
  "nonce": 18,
  "process_id": "cryft.giftcodes.v1",
  "slot_commitment": "0xKECCAK(slot_claims_canonical_bytes)",
  "reveal_policy": {"when": "on_inclusion", "scope": "validators_only"},
  "cgs_route": {"region_hint": 42, "privacy_pool": "midwest.v1"}
}
```

#### 7.3.5 Deterministic scheduling and conflict rules (pre-lock design)

CryftNet uses a deterministic pre-lock scheduler for parallel transactions. Validators must arrive at
identical schedules given the same mempool snapshot. The scheduler organizes transactions into
lanes by process_id and attempts to acquire READ and WRITE locks on slots. Locks are acquired in
sorted slot_id order to avoid deadlocks.
Inputs:
- mempool transactions T (including legacy and parallel)
- deterministic ordering key: (process_id, tx_hash, arrival_index)
1) Partition:
   Legacy = [t in T where t.type == legacy]
   Parallel = group by process_id: L[p] = sorted(t in T where t.process_id==p)
2) Initialize lock tables:
   read_locks[slot_id] = set()
   write_lock[slot_id] = optional owner
3) Build block:
   a) Schedule legacy txs serially in canonical order (e.g., tx_hash order).
   b) For each lane p in sorted(process_id):
        for tx in L[p]:
           if acquire_all_locks(tx.slot_claims):

                schedule tx in lane p (may run in parallel with other lanes)
           else:
                defer tx to next block (or later within block deterministically)
Acquire_all_locks(claims):
   for slot in sort_by_slot_id(claims):
       if claim.mode == READ:
           if write_lock[slot] is held by another tx: return false
       if claim.mode == WRITE:
           if write_lock[slot] held OR read_locks[slot] non-empty: return false
```jsonc
   // if all checks pass, take locks
   for slot in sort_by_slot_id(claims):
       if claim.mode == READ: read_locks[slot].add(tx_id)
       else: write_lock[slot] = tx_id
   return true
```

#### 7.3.6 Receipts and proofs

Receipts must prove how a transaction was scheduled and whether it conflicted. For parallel
transactions, receipts include: - lane (process_id) - lane_index (order within lane) - slot_claims_hash
(commitment) - revealed_slot_claims (if reveal policy allows; otherwise a reference) - lock_result
(acquired / deferred) - execution_result (status, logs, gas)
```jsonc
{
  "tx_hash": "0x...",
  "block": 123456,
  "type": "cryft_parallel",
  "process_id": "cryft.giftcodes.v1",
  "lane_index": 7,
  "slot_commitment": "0x...",
  "slot_claims_revealed": true,
  "slot_claims": [
    {"slot_id":"0x...", "mode":"WRITE"},
    {"slot_id":"0x...", "mode":"WRITE"}
  ],
  "lock_result": "acquired",
  "conflict_note": null,
  "status": "success",
  "gas_used": 184321
}
```

### 7.4 Handling normally non-parallel transactions

Not all workloads can be parallelized. Any transaction may choose to omit slot_claims and run in
legacy serial mode. Even in parallel mode, a transaction can intentionally over-claim (e.g., WRITE an
entire account slot) to ensure safety. This reduces parallelism but preserves determinism. Over time,
popular contracts can adopt more precise slot claims, or use Object slots for application-level
resources.

### 7.5 Developer experience and backward compatibility

Developers can adopt parallelism incrementally: - Phase 0: deploy standard Solidity contracts; use
legacy transactions. - Phase 1: clients attach slot claims for known call patterns (SDK supported). -
Phase 2: contracts emit recommended slot hints, or provide view methods to derive slot claims. -
Phase 3: high-value workflows use CGS private intents with slot commitments and selective

disclosure. MetaMask and standard JSON-RPC continue to work; parallel fields are optional extensions.

---

## 8. Standard subnet model vs custom subnets

### 8.1 Cryft Standard Subnet (CSS-1)

CSS-1 is an optional standardized subnet profile intended to maximize interoperability, tooling
support, and federation services. CSS-1 chains are EVM compatible and adopt the canonical Smart
Slot model and CGS interfaces.
CSS-1 guarantees: - EVM JSON-RPC compatibility - Smart Slot envelope support (process_id,
slot_claims, slot_commitment) - Deterministic scheduling rules (pre-lock) - Standard checkpoint
format for anchoring to Main - Compatibility with federation registries and pinning reward primitives

### 8.2 CEP-CSS-1: standardized execution profile

CEP-CSS-1 is a versioned specification published on Main and adopted by CSS chains. It defines: -
slot derivation domain tags and hashing rules - required receipt fields for parallel txs - scheduler
determinism constraints - CGS message types required for private intents - upgrade signaling and
compatibility windows

### 8.3 Custom subnets

Custom subnets may use any VM and any consensus mechanism. They are first-class citizens.
However, to receive federation services (bridging, registry listing, standardized tooling), a custom
subnet can publish a Federation Interface Declaration (FID) on Main.
FID fields (example): - subnet_id, chain_id, VM type - consensus summary and security assumptions
- checkpoint proof model (signatures, light client, validity proof) - message format for cross-chain calls
- asset mapping and replay protection rules - CGS compatibility level (none / partial / full)

### 8.4 Compatibility certification

The federation may offer optional certification for custom subnets. Certification is not a gate to
existence; it is a promise to users and tooling providers. Certified subnets may receive default routing, shared libraries, and aggregated dashboards.

---

## 9. Cantons Global Synchronizer (CGS): privacy propagation and federation sync

CGS is a Cryftee-hosted plane for privacy-aware propagation of intents and synchronization across
regions. It is inspired by canton-style private synchronization in the sense that parties coordinate over
domains and reveal only what is necessary to authorized participants. CGS is not "magic privacy"; it
is a structured messaging and keying system that aims to reduce the amount of public metadata
required for transaction inclusion and cross-chain coordination.

### 9.1 Core design constraints

- Must not break EVM compatibility: legacy transactions remain public and unchanged.
- Must provide liveness under partial censorship: multiple routes, region fallbacks, and
anti-correlation strategies.
- Must limit metadata leakage: minimize public exposure of counterparties, resource IDs, and full
slot claims.
- Must support deterministic scheduling: even private intents require commitments that can be
verified later.

### 9.2 CGS message types (proposal)

CGS defines a small set of message types carried over a privacy-aware gossip layer. Messages are content-addressed where possible, and large payloads may be stored on IPFS with encrypted references.

- **IntentEnvelope:** encrypted transaction intent plus slot_commitment and minimal routing hints.
- **RevealClaims:** reveals slot_claims to validators (or to an auditor committee) at inclusion time.
- **KeyRotate:** rotates threshold encryption keys for a privacy pool or region domain.
- **AvailabilityAttestation:** posts aggregated availability/pinning attestations without revealing private CID details.
- **SyncRequest / SyncConfirm:** domain synchronization for multi-party workflows.
- **DisputeBundle:** evidence package for fraud/slashing (signed transcripts, challenge failures, etc.).

### 9.3 Metadata visibility matrix

| Field | Public observers | Region validators | Main validators | Counterparties | Pin auditors |
|:------|:-----------------|:------------------|:----------------|:---------------|:-------------|
| Sender address | Legacy: yes; CGS: optional | yes (for inclusion) | only if anchored and required | yes | no |
| Recipient address | Legacy: yes; CGS: optional | yes (for execution) | only if required | yes | no |
| Slot claims | Legacy/parallel: yes; CGS intent: commitment only | claims revealed at inclusion or to auditor | commitment only unless dispute | optional | no |
| Process ID | often yes (may be masked in CGS) | yes | yes (in checkpoints) | yes | no |
| Resource IDs (object slots) | optional | only if revealed | only if dispute | yes | no |
| CID of pinned content | public pin job: yes; private pin: commitment only | auditor-only for private pin | aggregate only | optional | auditor yes |
| Proof responses (pin challenges) | public: yes; private: auditor-posted aggregate | yes | yes (if disputed) | no | yes |

### 9.4 Selective disclosure

Selective disclosure means revealing the minimum needed, at the latest safe time, to the minimum
required audience. Examples: - A private intent may reveal slot_claims only to region validators at
inclusion time, while the public chain sees only a commitment. - A private pin job may reveal the CID
only to selected pin providers and auditors; the chain stores only a commitment and aggregated

scores. Selective disclosure is constrained by verifiability: when disputes arise, evidence may need to
be revealed to Main or to a court-like committee.

### 9.5 CGS and Smart Slots via slot commitments

Slot commitments bridge privacy and determinism. A private intent includes slot_commitment =
H(canonical(slot_claims)). Validators can: 1) reserve scheduling capacity using the commitment
(without seeing claims), 2) require RevealClaims during inclusion, and 3) verify that revealed claims
match the commitment before executing.
Intent submission:
- client computes slot_claims and slot_commitment
- client encrypts tx data to pool key K_pool (threshold key)
- sends IntentEnvelope(process_id, slot_commitment, ciphertext, routing_hint)
Inclusion:
- proposer selects intent by commitment and policy
- proposer requests RevealClaims from sender (or authorized party)
- proposer verifies H(revealed_claims) == slot_commitment
- scheduler runs pre-lock acquisition on revealed_claims
- if acquired, execute tx and include receipt linking to commitment

### 9.6 Anti-censorship and liveness

CGS uses multi-route gossip and region fallbacks. If Region A appears censored, intents can be
routed to Region B or to Main, then forwarded. Privacy pools should avoid single points of control:
threshold keys are managed by committees with rotation. Residual risk remains: any privacy system
can be degraded by global adversaries controlling network paths; CryftNet treats this as measurable
and provides monitoring via Cryftee modules.

### 9.7 Failure modes and residual risk

- Metadata leakage through timing and traffic analysis (mitigate with batching and cover traffic).
- Threshold key compromise (mitigate with rotations, HSM/TEE options, and slashing).
- Denial of service via junk intents (mitigate with fees, rate limits, and capability gating).
- Complexity risk: CGS must not be consensus-critical without extensive validation.

---

## 10. Cross-chain communication and settlement

### 10.1 Checkpoint format

Regions anchor to Main via checkpoints. A checkpoint commits to:

- region_id and chain_id
- region block height h and block hash
- region state root (or output root) at height h
- validator quorum proof (aggregated signature or threshold proof)
- optional summary of outgoing messages (message root)

```text
Checkpoint = {
  region_id: 42,
  chain_id: 1001,
  height: 8_240_112,
  block_hash: 0x...,
  state_root: 0x...,
  message_root: 0x...,
  quorum: { type: "BLS_AGG", signers_bitmap: 0x..., sig: 0x... },
  epoch: 771,
  ping_epoch: 771,          // binds validator eligibility measurements
  metadata: { cep_css: "1.0.0" }
}
```

### 10.2 Message passing guarantees

Messages from Region A to Region B are routed through Main for final settlement. The guarantee is:

- If a message is included in a checkpoint finalized on Main, it is globally ordered relative to other finalized checkpoints.
- Regions may implement local fast-path transfers (optimistic) but must reconcile with Main anchoring to prevent fraud.

### 10.3 Replay protection and ordering

Replay protection uses (origin_chain_id, origin_height, message_index) as a unique identifier.
Destination chains maintain a consumed set keyed by this tuple. Ordering constraints are defined by
the origin chain's checkpoint. Destination chains may choose strict ordering (process sequentially) or
relaxed ordering (parallelizable) depending on the message type.

### 10.4 Interaction with CGS

CGS can carry private envelopes for cross-chain intents. However, settlement proofs must eventually become verifiable on-chain. A private cross-chain transfer therefore separates:

- private negotiation and intent propagation (CGS),
- public commitment and checkpointing (region and Main),
- selective disclosure only when required for validation or disputes.

### 10.5 ZK-based cross-chain verification

Traditional cross-chain verification relies on quorum signatures: Main trusts that 2/3+ of a region's validators signed the checkpoint honestly. ZK validity proofs offer an alternative with stronger guarantees.

**Verification modes:**

| Mode | Trust Assumption | Verification Cost | Latency |
|:-----|:-----------------|:------------------|:--------|
| Quorum signature only | 2/3 validators honest | O(1) signature verify | Fast (seconds) |
| ZK validity proof only | ZK system soundness | O(1) proof verify | Slower (proof generation) |
| Hybrid (ZK + quorum) | Either assumption | O(1) each | Proof ready â†’ fast; else fallback |

**Recommended approach:** Hybrid verification. Regions produce ZK proofs asynchronously. If a proof is available when the checkpoint reaches Main, use it. Otherwise, fall back to quorum verification. Over time, as ZK prover performance improves, proofs become available faster and become the primary path.

**Benefits for cross-chain settlement:**

- **Trustless bridges:** Assets locked on Region A can be minted on Region B with cryptographic proof of the lock, not just validator attestations.
- **Light client support:** Mobile wallets and browsers can verify cross-chain state without trusting RPC providersâ€”they verify the ZK proof directly.
- **Fraud-proof elimination:** With validity proofs, there is no fraud window. The proof either verifies or it doesn't. This simplifies the security model compared to optimistic systems.
- **Custom subnet interoperability:** Non-EVM subnets can bridge to Main by providing validity proofs, enabling heterogeneous federation without requiring Main to execute foreign VMs.

**Integration with CGS:**

Private cross-chain transfers can use ZK proofs to attest to validity without revealing transaction details:

```text
Private cross-chain proof:
1) Sender on Region A creates private transfer intent (CGS)
2) Region A includes transfer in block, generates ZK proof of:
   - sender had sufficient balance
   - transfer is valid per protocol rules
   - commitment to recipient (hidden)
3) Checkpoint to Main includes aggregated proof
4) Recipient on Region B claims with proof of inclusion + recipient key
5) Region B mints without learning sender identity
```

This enables privacy-preserving cross-chain transfers with cryptographic (not just economic) security.

### 10.6 User mobility and cross-region asset portability

A core UX goal of CryftNet is that users are **never region-locked**. If a user physically moves from the Midwest to the West Coast, they should immediately benefit from low-latency access via their nearest region without losing access to assets or requiring complex migrations.

**Unified account model:**

CryftNet uses a unified address space across the federation. The same Ethereum-style address (derived from the user's private key) is valid on Main and all regions. This means:

- A user's identity is portableâ€”no need to create new accounts when switching regions.
- Smart contracts can reference the same addresses across regions.
- Wallets display a unified view of assets regardless of which region holds them.

**Asset location vs. user location:**

Assets exist on specific chains (Main, Region A, Region B, etc.), but users can **interact from any region**. The key mechanisms:

| Scenario | Mechanism | Latency | Notes |
|:---------|:----------|:--------|:------|
| Assets on Region A, user in Region A | Direct transaction | Fastest (local) | Ideal case |
| Assets on Region A, user in Region B | Cross-region relay | Fast (seconds) | Region B forwards intent to Region A via CGS or direct relay |
| Assets on Region A, user wants them on Region B | Cross-region transfer | Minutes (checkpoint) | Lock on A, mint on B after checkpoint |
| Assets on Main, user in any region | Direct to Main or relay | Medium | Main is always reachable |

**Automatic routing layer:**

Wallets and dApps use a routing layer that:

1. **Detects user location** via latency probing to regional RPC endpoints.
2. **Routes transactions** to the optimal region based on:
   - Where the user's assets are located
   - Current region health (congestion, latency)
   - Transaction type (local vs. cross-region)
3. **Abstracts complexity** so users don't need to manually select regions.

```text
Routing decision flow:
1) Wallet probes regional endpoints â†’ determines nearest healthy region (R_user)
2) User initiates transaction to contract C on region R_asset
3) If R_user == R_asset:
     Submit directly to R_asset (fastest path)
4) If R_user != R_asset:
     Option A: Relay intent via CGS to R_asset (user pays relay fee)
     Option B: Submit to R_user, trigger cross-region message to R_asset
     Option C: For high-value, submit directly to Main (global settlement)
5) Wallet displays estimated confirmation time based on path chosen
```

**Cross-region asset transfer (migration):**

When a user permanently moves regions and wants to migrate assets for ongoing low-latency access:

1. **Initiate transfer** on origin region (lock assets in bridge contract).
2. **Wait for checkpoint** to finalize on Main (minutes, not hours with ZK proofs).
3. **Claim on destination region** with proof of inclusion from Main.
4. **Assets now local** to user's new region.

For fungible tokens (CRYFT, ERC-20s), this is straightforward. For NFTs and complex state, the destination region must support the same contract interfaces or use a canonical registry on Main.

**"Follow-me" account state (optional, advanced):**

For users who frequently travel, CryftNet can support optional **account mirroring**:

- User opts in to mirror their account state across multiple regions.
- Regions maintain synchronized balances via frequent micro-checkpoints.
- Transactions are accepted on any mirrored region and reconciled.
- Trade-off: higher fees (pays for synchronization overhead), but seamless UX.

```text
Account mirroring flow:
1) User registers for mirroring: regions [A, B, C], asset types [CRYFT, USDC]
2) Mirroring contract on Main tracks authoritative balances
3) User spends on Region B â†’ deducted locally, async sync to Main
4) Main reconciles and propagates updated balance to A, C
5) Conflict resolution: if double-spend attempted, Main state is authoritative;
   offending region transaction is reverted, user may face penalty
```

**No region lock guarantee:**

The federation governance charter should include a **user mobility rights** clause:

- Users can always withdraw assets to Main (cannot be blocked by region governance).
- Main provides a "home of last resort" for users whose local region becomes unavailable.
- Regions cannot impose exit fees beyond reasonable gas costs.
- Cross-region transfers are a protocol-level right, not a feature that regions can disable.

This ensures that even if a regional DAO makes unfavorable decisions, users retain sovereignty over their assets and can migrate to a better-governed region or to Main.

### 10.7 Single-location guarantee: preventing cross-region double-spending

A fundamental invariant of CryftNet's cross-region model is that **assets exist in exactly one location at any given time**. This prevents double-spending attacks where a malicious user could spend the same asset on multiple regions before checkpoints reconcile.

**Core principle: Lock-Mint-Burn (LMB) model**

Cross-region asset transfers use a canonical lock-mint-burn pattern:

```text
Transfer from Region A â†’ Region B:

1) LOCK on Region A:
   - User calls bridge.lock(asset, amount, dest_region=B, recipient)
   - Asset is locked in bridge contract (user cannot spend it)
   - Lock event emitted with unique transfer_id

2) CHECKPOINT to Main:
   - Region A's next checkpoint includes the lock event in message_root
   - Main finalizes checkpoint â†’ lock is now globally ordered

3) MINT on Region B:
   - User (or relayer) submits claim to Region B with:
     - Merkle proof of lock event inclusion in Region A's checkpoint
     - Main's finalization proof for that checkpoint
   - Region B verifies proofs and mints equivalent asset to recipient
   - Mint is linked to transfer_id (prevents replay)

4) Asset now exists ONLY on Region B


---

Transfer back (Region B â†’ Region A):

1) BURN on Region B:
   - User calls bridge.burn(asset, amount, dest_region=A, recipient)
   - Asset is destroyed on Region B

2) CHECKPOINT to Main:
   - Burn event included in Region B's checkpoint

3) UNLOCK on Region A:
   - User submits proof of burn to Region A
   - Original locked asset is released to recipient
```

**Why this prevents double-spending:**

| Attack Vector | Prevention Mechanism |
|:--------------|:---------------------|
| Spend on A, then transfer to B | Lock happens first; asset is frozen before checkpoint |
| Transfer to B, then spend on A | Asset is locked; spending fails |
| Claim on B twice | transfer_id is marked as consumed after first claim |
| Forge proof of lock | Merkle proof verification against Main-finalized checkpoint |
| Collude with Region A validators to fake lock | Main checkpoint requires quorum signature; ZK proofs add trustlessness |

**Alternative: Partitioned balance model (recommended)**

Rather than wrapped tokens, CryftNet can use a **partitioned balance model** where:

- The same contract address exists on all regions (deterministic deployment via CREATE2).
- Account balances are **region-specific**: your balance on Region A is independent of Region B.
- Cross-region transfers explicitly move balance from one region to another.
- All regions are aware of the contract's existence, but state is partitioned.

This model is conceptually cleaner and avoids "wrapped token" confusion:

```text
Partitioned Balance Model:

Token: USDC (deployed at 0xUSDC on all regions via CREATE2)

User Alice's balances:
â”œâ”€â”€ Main:     500 USDC   (Alice can spend on Main)
â”œâ”€â”€ Region A: 300 USDC   (Alice can spend on Region A)
â”œâ”€â”€ Region B:   0 USDC   (Alice has no Region B balance)
â””â”€â”€ Region C: 200 USDC   (Alice can spend on Region C)

Total Alice owns: 1000 USDC (sum of all regional balances)

To spend on Region B, Alice must first transfer from another region.
```

**Why partitioned balances are safe:**

1. **No double-spend possible:** Alice's Region A balance can only be spent on Region A. To use it on Region B, she must first transfer (which debits A, then credits B after checkpoint).

2. **Clear ownership:** Each regional balance is fully owned and spendable only on that region until explicitly moved.

3. **Atomic transfers:** The cross-region transfer is atomic at the Main checkpoint level:
   - Debit on origin region is checkpointed to Main.
   - Credit on destination requires proof of the debit checkpoint.

---


4. **Higher latency for cross-region is expected:** If Alice is in Region B but her balance is on Region A:
   - She can relay her transaction to Region A (incurs cross-region latency).
   - Or she transfers balance to Region B first (one-time migration cost, then local speed).

**Contract deployment models:**

CryftNet supports multiple deployment models to balance developer convenience with federation coordination. The most user-friendly approach is **region-first deployment with opt-in federation mirroring**.

**Critical: Region ID requirements**

**Primary Network M-Chain does NOT require region IDs.** The M-Chain (EVM execution chain within the Primary Network) is the default chain for dApp interactionsâ€”users and developers interact with M-Chain exactly like a standard EVM chain. Region IDs are only required when operating on State/Region chains or requesting cross-region operations.

| Operation | Chain | Region ID Required? |
|:----------|:------|:--------------------|
| Deploy contract | Primary Network M-Chain | **NO** |
| Call contract | Primary Network M-Chain | **NO** |
| Transfer tokens | Primary Network M-Chain | **NO** |
| Deploy contract | State/Region chain | YES (implicit from submission endpoint) |
| Call contract | State/Region chain | YES (implicit from submission endpoint) |
| Request mirroring to regions | Primary Network M-Chain | YES (explicit target_regions[]) |
| Cross-region transfer | Any chain | YES (explicit dest_region) |

**Why the Primary Network M-Chain doesn't need region IDs:**
- The Primary Network (P + X + M) is the canonical foundationâ€”it has no "region" because it IS the federation anchor
- Transactions submitted to M-Chain execute on M-Chain; there's no ambiguity
- This preserves standard EVM UX for M-Chain interactions
- Region IDs are only needed when the user wants to interact with a specific State/Region chain OR move assets across regions

**Explicit region ID declaration (for federation operations):**

When users or developers want federation-wide operations, they MUST explicitly declare target region IDs. This ensures:

1. **Proper fee collection:** Main receives gas fees proportional to the number of regions being updated
2. **Developer control:** Deployers choose exactly which regions they pay for
3. **No surprise costs:** Users know upfront what they're paying for
4. **Scalability:** Main doesn't automatically push to all regions

```text
Transaction region declaration (federation operations only):

// Deploy or update transaction includes explicit region list
tx.target_regions = [A, B, C]  // Explicit opt-in regions

Fee calculation:
  base_fee = local_gas_cost
  federation_fee = Î£(per_region_fee[r] for r in target_regions)
  total_fee = base_fee + federation_fee

If target_regions is empty or omitted:
  â†’ Transaction is local only (Main or single region)
  â†’ No federation fees charged
  â†’ Contract/balance exists only on execution region
```

### 10.8 Region-first deployment with federation mirroring

**Core principle:** Developers deploy to their preferred region first. Main automatically detects new contracts via checkpoints and can mirror them to **explicitly declared regions** if the developer opts in and pays the appropriate fees.

**Region ID requirements:**

| Interaction Type | Region ID Required? | Notes |
|:-----------------|:--------------------|:------|
| **Main C-Chain transactions** | **NO** | Main is the default home chain; no region declaration needed |
| **Main C-Chain contract deployment** | **NO** | Deploys directly on Main; mirroring requires target_regions[] |
| **State/Region chain transactions** | YES | Must specify which region to execute on |
| **Cross-region transfers** | YES | Must specify dest_region explicitly |
| **Federation mirroring** | YES | Must declare target_regions[] and pay fees |

**Main as the default chain:** Users interacting with Main Federal C-Chain do not need to specify any region ID. Main is the "home" chain of the federationâ€”transactions submitted to Main execute on Main. Region IDs are only required when:
1. Deploying or transacting on State/Region chains
2. Requesting federation mirroring to specific regions
3. Initiating cross-region asset transfers

**Deployment modes:**

| Mode | Scope | Region Declaration | Fee Structure |
|:-----|:------|:-------------------|:--------------|
| **Main-direct** | Main C-Chain only | None required | Main gas only |
| **Region-local** | Single region only | Implicit (current region) | Region gas only |
| **Federation-mirrored** | Declared regions | Explicit target_regions[] | Origin + per-region fee |
| **Main-first (governance)** | All CSS-1 regions | Explicit or "all CSS-1" | Main + per-region fee |

**Main-direct deployment (no region ID needed):**

```text
Developer deploys contract directly on Main C-Chain:

1) Dev deploys via standard CREATE2 or FederationDeployer on Main
   - NO region ID required - Main is the default chain
   - Transaction: deploy(init_code, salt)
   - Fee: Main gas only
   
2) Contract exists on Main C-Chain
   - Users interact with contract on Main without specifying region
   - Standard EVM experience, no federation complexity
   
3) Optional: Request mirroring to regions later
   - Call FederationRegistry.requestMirroring(contract, target_regions[])
   - Pay federation fees for each target region
   - Main triggers mirroring via checkpoints

Use case: Main-only contracts, governance, canonical registries
```

**Region-local deployment (requires region context):**

```text
Developer deploys GameContract on Region A:

1) Dev deploys via RegionDeployer on Region A
   - RegionDeployer.deploy(init_code, salt, options={
       target_regions: []  // Empty = local only
     })
   - Contract deployed at address 0xGame (deterministic via CREATE2)
   - Fee: Region A gas only
   
2) Contract exists ONLY on Region A
   - balances[Alice] = 100 tokens (on Region A only)
   - Users in Region A interact normally
   
3) Main sees deployment in Region A's checkpoint
   - Records in registry: {address: 0xGame, home_region: A, target_regions: [A]}
   - Does NOT deploy to other regions (none declared)
   
4) Users in Region B cannot interact with 0xGame
   - Contract doesn't exist on Region B
   - Wallet shows: "This contract is only available on Region A"
```

**Federation-mirrored deployment (explicit region opt-in):**

```text
Developer wants token available on Regions A, B, C (not D or E):

1) Dev deploys via RegionDeployer on Region A (their local region)
   - RegionDeployer.deploy(init_code, salt, options={
       target_regions: [A, B, C],    // EXPLICIT region list
       balance_portability: true,
       home_region: A
     })
   - Contract deployed at 0xToken on Region A

---

   
   Fee breakdown:
   - Region A deployment gas: 500,000 gas Ã— Region A gas price
   - Federation fee to Main: 
     - Region B mirroring: 0.01 CRYFT
     - Region C mirroring: 0.01 CRYFT
   - Total: local_gas + 0.02 CRYFT federation fee

2) Region A checkpoint includes deployment event:
   - DeploymentEvent(address=0xToken, code_hash, salt, target_regions=[A,B,C], fee_paid=0.02)

3) Main receives checkpoint and processes:
   - Verifies fee_paid >= required fee for target_regions
   - Records in Federation Registry: {
       address: 0xToken, 
       home_region: A,
       target_regions: [A, B, C],  // Only these regions
       balance_portability: true,
       deployed_regions: [A]       // Initially only A
     }
   - Queues deployment to B and C ONLY (not D or E)

4) Main triggers mirroring to Region B, C:
   - RegionDeployer.mirror() called on B and C
   - Region D and E: no deployment (not in target_regions)

5) Contract now exists at 0xToken on Regions A, B, C
   - Region D and E: contract does NOT exist

   - Developer can later expand to D, E by paying additional fee
```

**Expanding to additional regions (post-deployment):**

```text
Developer later wants to add Region D:

1) Dev calls FederationRegistry.expandRegions(contract_addr, [D])
   - On any region where contract exists (A, B, or C)
   - Fee: 0.01 CRYFT for Region D mirroring

2) Checkpoint carries expansion request to Main

3) Main verifies:
   - Caller is original deployer (or authorized)
   - Fee paid for new regions
   - Updates: target_regions: [A, B, C, D]

4) Main triggers mirror to Region D

5) Contract now exists on A, B, C, D
```

**Fee structure for federation operations:**

```text
Federation Fee Schedule (set by Main governance):


Operation                          | Fee per Region
-----------------------------------|----------------
Contract deployment mirroring      | 0.01 CRYFT
Balance portability setup          | 0.005 CRYFT
Cross-region balance update        | 0.001 CRYFT
Region expansion (post-deploy)     | 0.01 CRYFT

Example: Deploy token to 5 regions with balance portability
- Local deployment gas: ~500k gas
- Mirroring to 4 additional regions: 4 Ã— 0.01 = 0.04 CRYFT
- Balance portability on 5 regions: 5 Ã— 0.005 = 0.025 CRYFT
- Total federation fee: 0.065 CRYFT + local gas

Fees flow to:
- 50% â†’ Main treasury (funds federation operations)
- 30% â†’ Target region validators (incentivizes mirroring)
- 20% â†’ Checkpoint relayers (incentivizes fast propagation)
```

**RegionDeployer architecture:**

To ensure deterministic addresses across regions, every region has a `RegionDeployer` contract at the same address:

```text
RegionDeployer (exists at 0xRegionDeployer on all chains):

  // Federation fee receiver (Main treasury on each region)
  address public immutable FEE_RECEIVER;
  
  // Per-region mirroring fee (set by Main governance)
  uint256 public mirrorFeePerRegion;
  uint256 public portabilityFeePerRegion;

  // Developer-initiated deployment (region-first)
  function deploy(
    bytes calldata init_code,
    bytes32 salt,
    DeployOptions calldata options
  ) external payable returns (address) {
    
    // Calculate required federation fee
    uint256 requiredFee = calculateFederationFee(options);
    require(msg.value >= requiredFee, "Insufficient federation fee");
    
    // Forward fee to Main treasury
    if (requiredFee > 0) {
      FEE_RECEIVER.transfer(requiredFee);
    }
    
    // Compute deterministic address
    bytes32 final_salt = keccak256(abi.encode(msg.sender, salt));
    address deployed = CREATE2(init_code, final_salt);
    
    // Record deployment with explicit region targets
    deployments[deployed] = DeploymentRecord({
      deployer: msg.sender,
      code_hash: keccak256(init_code),
      salt: salt,
      final_salt: final_salt,
      target_regions: options.target_regions,  // EXPLICIT region list
      balance_portability: options.balance_portability,
      home_region: REGION_ID,
      fee_paid: requiredFee,
      timestamp: block.timestamp
    });
    
    emit ContractDeployed(deployed, msg.sender, options.target_regions, requiredFee);
    return deployed;
  }
  
  function calculateFederationFee(DeployOptions calldata options) 
    public view returns (uint256) {
    
    uint256 fee = 0;
    
    // Mirroring fee for each target region beyond home
    uint256 mirrorRegions = options.target_regions.length > 0 

      ? options.target_regions.length - 1  // Exclude home region
      : 0;
    fee += mirrorRegions * mirrorFeePerRegion;
    
    // Balance portability fee per region
    if (options.balance_portability) {
      fee += options.target_regions.length * portabilityFeePerRegion;
    }
    
    return fee;
  }
  
  // Main-triggered mirroring (after checkpoint, only for declared regions)
  function mirror(
    bytes calldata init_code,
    bytes32 salt,
    address original_deployer,
    uint64[] calldata authorized_regions
  ) external onlyFederationRelay {
    
    // Verify this region is in the authorized list
    require(isRegionAuthorized(REGION_ID, authorized_regions), 
            "Region not in target_regions");
    
    // Use SAME final_salt as original deployment
    bytes32 final_salt = keccak256(abi.encode(original_deployer, salt));
    address deployed = CREATE2(init_code, final_salt);
    
    // Record as mirrored instance
    deployments[deployed].is_mirror = true;
    deployments[deployed].home_region = /* from Main */;
    deployments[deployed].target_regions = authorized_regions;
    
    emit ContractMirrored(deployed, original_deployer, REGION_ID);
  }
  
  // Expand to additional regions (must pay additional fee)
  function expandRegions(
    address contract_addr,
    uint64[] calldata new_regions
  ) external payable {
    
    DeploymentRecord storage record = deployments[contract_addr];
    require(msg.sender == record.deployer, "Not deployer");
    
    // Calculate fee for new regions
    uint256 expansionFee = new_regions.length * mirrorFeePerRegion;
    if (record.balance_portability) {
      expansionFee += new_regions.length * portabilityFeePerRegion;
    }
    require(msg.value >= expansionFee, "Insufficient expansion fee");
    
    // Forward fee
    FEE_RECEIVER.transfer(expansionFee);
    
    // Emit expansion event for checkpoint
    emit RegionExpansionRequested(contract_addr, new_regions, expansionFee);
  }
```

**Why same address is guaranteed:**

```text
Address computation for mirrored contracts:

Original deployment on Region A:
  deployer_contract = 0xRegionDeployer (same on all regions)
  final_salt = keccak256(original_deployer || user_salt)
  address = CREATE2(0xRegionDeployer, final_salt, init_code)
  â†’ 0xToken

Mirror deployment on Region B:
  deployer_contract = 0xRegionDeployer (SAME)
  final_salt = keccak256(original_deployer || user_salt) (SAME)
  init_code = (SAME, verified by code_hash)
  address = CREATE2(0xRegionDeployer, final_salt, init_code)
  â†’ 0xToken (SAME!)

The original_deployer is baked into the salt, so even though
the actual deployer (RegionDeployer) is the same, each developer
gets their own address namespace.
```

### 10.9 Balance portability modes

When a contract opts into federation mirroring, it can choose how balances work:

**Mode 1: Region-locked balances (default for non-mirrored)**

```text
balances[Alice] exists only on the region where the action occurred.
No cross-region transfers possible.
Simplest model, lowest complexity.

Use case: Local games, region-specific loyalty points, test contracts
```

**Mode 2: Portable balances (opt-in)**

```text
Contract enables balance_portability = true

- Balances are tracked per-region: balances[region][account]
- Users can call transferToRegion(amount, dest_region, recipient)
- Standard debit-checkpoint-credit flow
- M-Chain GBL tracks conservation: Î£(regional balances) = total_supply

Use case: Tokens, stablecoins, any asset users want to move
```

**Mode 3: Replicated balances (advanced, opt-in)**

```text
Contract enables balance_replication = true

- ALL balances are automatically replicated to all mirrored regions
- User has SAME balance on every region (no transferToRegion needed)
- Writes are serialized through Main to prevent conflicts
- Higher latency for writes, but instant reads anywhere

Trade-offs:
- Every balance change requires Main checkpoint (slower)
- Higher fees (pays for replication overhead)
- Simpler UX (no manual transfers)

Use case: Governance tokens (need to vote from any region), identity contracts
```

**Implementation: Portable vs. Replicated:**

```solidity
// Portable balance model (recommended)

contract PortableToken {
    // Balances are region-specific
    mapping(address => uint256) public balances;  // local to this region
    
    // Authorized target regions (set at deployment)
    uint64[] public targetRegions;
    
    function transfer(address to, uint256 amount) external {
        // Normal transfer within region - no federation fee
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
    
    function transferToRegion(
        uint256 amount, 
        uint64 destRegion, 
        address recipient
    ) external payable {
        // MUST declare valid target region
        require(isValidTargetRegion(destRegion), "Region not in target_regions");
        
        // Must pay cross-region fee
        uint256 requiredFee = federationRegistry.crossRegionFee();
        require(msg.value >= requiredFee, "Insufficient cross-region fee");
        
        // Debit locally
        balances[msg.sender] -= amount;
        
        // Forward fee to Main treasury
        FEDERATION_FEE_RECEIVER.transfer(requiredFee);
        
        // Emit for checkpoint inclusion (includes dest_region explicitly)
        emit CrossRegionTransfer(
            transferId, 
            msg.sender, 
            recipient, 
            amount, 
            destRegion,      // Explicit destination
            requiredFee      // Fee paid
        );
    }
    
    function isValidTargetRegion(uint64 regionId) internal view returns (bool) {
        for (uint i = 0; i < targetRegions.length; i++) {
            if (targetRegions[i] == regionId) return true;
        }
        return false;
    }
}

// Replicated balance model (simpler UX, higher cost)
contract ReplicatedToken {
    // Balances are global (synced via Main)
    // Local storage is just a cache
    mapping(address => uint256) public balanceCache;
    
    function transfer(address to, uint256 amount) external {
        // Must go through Main for global ordering
        // Option A: Queue for next checkpoint (delayed)
        // Option B: Synchronous call to Main (expensive)
        emit GlobalTransfer(msg.sender, to, amount);
    }
    
    // Called by federation relay after Main confirms
    function applyGlobalTransfer(...) external onlyRelay {
        balanceCache[from] -= amount;
        balanceCache[to] += amount;
    }
}
```

### 10.10 Initial supply and home region

**The home region problem:**

When a contract is deployed on Region A and mirrored to B, C, D, where do initial balances exist?

**Solution: Home region holds initial state**

```text
Deployment with initial state:

1) Dev deploys on Region A with constructor that sets initial balances:
   constructor() {
     balances[issuer] = 1_000_000_000;
   }

2) Contract deployed on Region A:
   - balances[issuer] = 1B on Region A âœ“

3) Main mirrors to Region B, C, D:
   - Constructor runs on each region? NO!
   - Mirror deployment uses a DIFFERENT init_code path

Mirror deployment init_code:
   - RegionDeployer.mirror() deploys with MODIFIED init_code
   - Original: constructor sets balances
   - Mirror: constructor sets balances to ZERO + marks as mirror
   
   // Pseudocode for mirror init
   constructor(bool is_mirror, uint64 home_region) {
     if (is_mirror) {
       // NO initial balances - this is a mirror
       _home_region = home_region;
     } else {
       // Original deployment - set initial balances
       balances[msg.sender] = INITIAL_SUPPLY;
     }
   }
```

**Wait - different init_code means different address!**

You're right! This is a problem. If mirror init_code differs, the address differs.

**Solution: Two-phase initialization**

```text
Correct approach: Separate deployment from initialization

1) Contract code has NO constructor logic for balances:
   
   contract Token {
     bool public initialized;
     uint64 public home_region;
     
     constructor() {
       // NOTHING here - same code on all regions
     }
     
     function initialize(uint256 initialSupply) external {
       require(!initialized, "Already initialized");
       require(REGION_ID == home_region || home_region == 0, "Not home region");
       
       if (home_region == 0) {
         // First initialization sets home region
         home_region = REGION_ID;
       }
       
       balances[msg.sender] = initialSupply;
       initialized = true;
     }
   }

2) Deployment flow:
   a) Dev deploys on Region A via RegionDeployer (zero balances)
   b) Dev calls initialize(1_000_000_000) on Region A
   c) Region A now has: home_region=A, balances[dev]=1B
   
   d) Main mirrors contract to Region B, C, D (same code, zero balances)
   e) Mirror regions have: home_region=A (set via mirror params), initialized=true
   f) initialize() cannot be called on mirrors (wrong region OR already initialized)

3) Result:
   - Same address (0xToken) on all regions âœ“
   - Initial supply exists ONLY on Region A âœ“
   - Mirror regions start with zero balances âœ“

   - No supply duplication âœ“
```

**Federation Registry tracks initialization:**

```text
Federation Contract Registry entry:

{
  address: 0xToken,
  code_hash: keccak256(bytecode),
  deployer: 0xDev,
  home_region: A,
  mirrored: true,
  balance_portability: true,
  deployed_regions: [A, B, C, D],
  initialized_on: [A],           // Only home region initialized
  total_supply: 1_000_000_000,   // Tracked by GBL
  conservation_verified: true
}
```

### 10.11 Developer experience summary

**Simplest path (region-local):**

```text
1. Deploy contract on your region
2. Done! Contract works locally, no federation complexity
```

**Federation-wide deployment:**

```text
1. Deploy contract on your region with mirrored=true
2. Call initialize() to set initial state
3. Wait ~1-2 checkpoints for Main to mirror to other regions
4. Contract available everywhere, initial state on your region
5. Users on other regions can receive assets via cross-region transfer
```

**Critical infrastructure (Main-first):**

```text
1. Submit governance proposal for deployment
2. After approval, deploy via FederationDeployer on Main
3. Initialize on Main
4. Automatic mirroring to all CSS-1 regions
5. Highest trust level, shown as "Federation Verified"
```

**Comparison:**

| Aspect | Region-First | Main-First |
|:-------|:-------------|:-----------|
| Deployment latency | Instant | Governance delay (days) |
| Initial availability | Home region only | All regions after approval |
| Mirroring delay | 1-2 checkpoints | Automatic |
| Trust level | Publisher-verified or unverified | Federation-verified |
| Best for | Most dApps, experiments | Canonical tokens, bridges |
| Gas cost | Region gas only | Main + region gas |

**Deterministic addresses guaranteed for both paths** - the key is using RegionDeployer with consistent salt computation.

```text
Deployment propagation flow:

1) Main: FederationDeployer deploys contract â†’ emits ContractDeployed(address, code_hash)
2) Main: Registry updated â†’ included in next M-Chain checkpoint
3) Regions receive checkpoint with deployment record
4) Region: Authorized deployer calls FederationDeployer.deploy(init_code, salt)
5) Region: Verifies deployed address matches checkpoint record
6) Region: Local registry updated, contract is now live

Timing:
- Main deployment: Instant (governance already approved)
- Region deployment: Within 1-2 checkpoint cycles (minutes)
- All regions get same address: Guaranteed by CREATE2 + same parameters
```

**Edge case: Region deploys before receiving checkpoint**

```text
Scenario: Region B validator tries to deploy USDC before Main checkpoint arrives

1) Validator calls FederationDeployer.deploy(USDC_init_code, salt) on Region B
2) FederationDeployer checks: Is this authorized?
   - Queries local authorization cache (synced from Main)
   - If not yet synced: REVERTS with "Authorization not yet received"
3) Validator must wait for checkpoint
4) After checkpoint: authorization cached, deployment proceeds

This prevents regions from "racing ahead" of Main.
```

**Federation Contract Registry:**

Main maintains a registry of canonical contract deployments:

```text
ContractRegistry on Main:
{
  address: 0xUSDC,
  code_hash: keccak256(USDC_bytecode),
  deployer: 0xFederationDeployer,
  salt: keccak256("USDC.v1"),
  deployed_regions: [Main, A, B, C],
  verified: true
}

Region verification:
- Before interacting with 0xUSDC on Region A, contracts can query:
  Main.ContractRegistry.isVerified(0xUSDC) â†’ true
- Wallets display verification status to users
- Unverified contracts are flagged as potentially unsafe
```

**Cross-region transfer in partitioned model:**

```text
Alice transfers 100 USDC from Region A â†’ Region B:

1) DEBIT on Region A:
   - Alice calls USDC.transferToRegion(amount=100, dest=B, recipient=Alice)
   - USDC contract on Region A:
     - Debits Alice's balance: balances[A][Alice] -= 100
     - Emits CrossRegionTransfer(id=X, from=Alice, to=Alice, amount=100, dest=B)
     - Records pending_outbound[X] = {amount, dest, recipient, status: pending}

2) CHECKPOINT Region A â†’ Main:
   - CrossRegionTransfer event included in checkpoint message_root
   - Main finalizes checkpoint

3) CREDIT on Region B:
   - Alice (or relayer) calls USDC.claimFromRegion(transfer_id=X, proof)
   - USDC contract on Region B:
     - Verifies Merkle proof against Main-finalized checkpoint
     - Verifies transfer_id X not already claimed: claimed[X] == false
     - Credits Alice's balance: balances[B][Alice] += 100
     - Marks claimed[X] = true

4) Result:
   - Region A: Alice has 200 USDC (was 300)
   - Region B: Alice has 100 USDC (was 0)
   - No double-spend possible: A's debit is finalized before B's credit
```

**Critical: Preventing balance duplication on deployment**

A subtle but critical attack vector: if a token contract's constructor initializes balances (e.g., `balances[issuer] = 1_000_000_000`), and that contract is deployed on multiple regions with identical init_code, the issuer would have that balance on EVERY regionâ€”effectively multiplying their supply.

**The problem:**

```text
Naive deployment (VULNERABLE):

Token constructor:
  constructor() {
    balances[msg.sender] = 1_000_000_000;  // Initial supply to deployer
    totalSupply = 1_000_000_000;
  }

Deployment via CREATE2 with same deployer/salt/init_code:
- Main: issuer has 1B tokens
- Region A: issuer has 1B tokens  
- Region B: issuer has 1B tokens
- Region C: issuer has 1B tokens

Result: Issuer has 4B tokens total! Supply inflated 4x.
```

**Why this happens:**

CREATE2 guarantees the same ADDRESS for same parameters, but each region executes the constructor INDEPENDENTLY. The constructor runs once per region, initializing local storage on each.

**Solution: M-Chain GBL is the authoritative source**

The contract's local `balances` mapping is a **cache**, not the source of truth. The M-Chain Global Balance Ledger (GBL) is authoritative:

```text
Federation-aware token architecture:

1) Constructor initializes ZERO balances:
   constructor() {
     // DO NOT set balances here
     // Initial supply is minted via separate transaction
   }

2) Initial mint happens on ONE region only (typically Main):
   - After deployment, issuer calls mint(amount, home_region=Main)
   - Main's GBL records: balances[USDC, Main, issuer] = 1_000_000_000
   - Main's GBL records: total_supply[USDC] = 1_000_000_000
   - No other region has any balance

3) Regional contract reads from GBL (via checkpoint sync):
   - Region A's USDC contract has balances[issuer] = 0 (no mint occurred here)
   - Region B's USDC contract has balances[issuer] = 0
   - Only Main shows issuer's balance

4) If issuer wants balance on Region A:
   - Must use transferToRegion(Main â†’ A)
   - Normal cross-region transfer rules apply
```

**Contract implementation pattern:**

```solidity
// Federation-aware ERC20 (conceptual)
contract FederatedToken {
    // Local balance cache (synced from GBL via checkpoints)
    mapping(address => uint256) public balances;
    
    // Region identifier (set at deployment)
    uint64 public immutable REGION_ID;
    
    // Federation registry reference
    IFederationRegistry public immutable registry;
    
    constructor(uint64 _regionId, address _registry) {
        REGION_ID = _regionId;

        registry = IFederationRegistry(_registry);
        // NO initial balances set here
    }
    
    // Only callable by authorized minter, only on designated home region
    function mint(address to, uint256 amount) external {
        require(msg.sender == registry.authorizedMinter(address(this)));
        require(REGION_ID == registry.homeRegion(address(this)), 
                "Mint only allowed on home region");
        
        balances[to] += amount;
        // Emit event for GBL to record
        emit Mint(to, amount, REGION_ID);
    }
    
    // Credits from cross-region transfers (called after checkpoint verification)
    function creditFromTransfer(
        bytes32 transferId, 
        address to, 
        uint256 amount,
        bytes calldata proof
    ) external {
        require(!claimed[transferId], "Already claimed");
        require(verifyCheckpointProof(proof), "Invalid proof");
        
        balances[to] += amount;
        claimed[transferId] = true;
        emit CreditFromTransfer(transferId, to, amount);
    }
}
```

**Home region concept:**

Each federated token has a designated **home region** where initial minting occurs:

```text
Token Registry entry:
{
  address: 0xUSDC,
  code_hash: ...,
  home_region: Main,          // Only Main can mint new supply
  total_supply: 1_000_000_000,
  authorized_minter: 0xCircle,
  deployed_regions: [Main, A, B, C]
}

Rules:
- mint() only succeeds on home_region
- Existing supply moves between regions via transferToRegion()
- GBL tracks: Î£(balances across all regions) = total_supply
- Any discrepancy = bug or attack â†’ bridge pause
```

**What about attacker deploying their own token?**


An attacker could deploy their own token (Tier 3: unverified) with inflated balances:

```text
Attacker deploys ScamToken on multiple regions with constructor:
  balances[attacker] = 1_000_000_000 per region

Result:
- Attacker has billions of ScamToken on each region
- BUT: ScamToken is NOT in Federation Registry
- Wallets show: "âš ï¸ Unverified contract"
- Users know not to trust it
- ScamToken has no relationship to legitimate tokens
- Cannot be traded on federation DEXs (which require verified tokens)
```

**Why same init_code with balances would be detected:**

Even if an attacker tries to deploy the EXACT same code as a legitimate token (to get the same address):

1. They cannot deploy at the same address without using FederationDeployer (which requires authorization)
2. If they deploy with a different deployer, they get a different address
3. FederationDeployer only accepts deployments that match governance-approved code_hash
4. Governance-approved code MUST use the "zero-balance constructor" pattern
5. Any contract with constructor-initialized balances fails code review and isn't approved

```text
Governance code review checklist for token approval:
â˜ Constructor does NOT initialize balances
â˜ Constructor does NOT set totalSupply to non-zero
â˜ mint() restricted to authorized minter
â˜ mint() restricted to home region
â˜ Code matches submitted code_hash exactly
â˜ Contract implements IFederatedToken interface
â˜ Cross-region transfer functions are correct
```

**Deployment flow with balance safety:**

```text
Safe federated token deployment:


1) PROPOSAL: Circle submits USDC deployment proposal
   - code_hash: keccak256(USDC_bytecode)
   - home_region: Main
   - initial_supply: 1_000_000_000
   - authorized_minter: 0xCircle
   
2) REVIEW: Governance verifies:
   - Constructor has zero initial balances âœ“
   - mint() is properly restricted âœ“
   - Cross-region logic is correct âœ“
   
3) APPROVAL: Governance approves deployment

4) DEPLOY ON MAIN:
   - FederationDeployer.deploy(USDC_bytecode, salt)
   - Contract deployed at 0xUSDC with zero balances

---

   
5) INITIAL MINT (Main only):
   - Circle calls USDC.mint(Circle, 1_000_000_000)
   - GBL records: balances[USDC, Main, Circle] = 1B
   - GBL records: total_supply[USDC] = 1B
   
6) DEPLOY ON REGIONS (after checkpoint):
   - Each region deploys same code at 0xUSDC
   - All regional contracts start with ZERO balances
   - Only Main has Circle's balance
   
7) DISTRIBUTION:
   - Circle transfers USDC to users via normal transfers
   - Cross-region transfers move balances as needed
   - GBL always enforces: Î£(regional) = total_supply
```

**Racing attack is now impossible:**

```text
Attack attempt: Attacker races to deploy on Region B before Main checkpoint

1) Attacker tries to call FederationDeployer.deploy(USDC_bytecode, salt) on Region B
2) FederationDeployer checks authorization from Main checkpoint
3) Authorization not yet received â†’ REVERTS
4) Attacker cannot deploy

Even if attacker deploys their own version:
- Uses different deployer â†’ different address (not 0xUSDC)
- Not in Federation Registry â†’ wallets warn users
- Cannot mint because they're not authorized_minter on a verified contract
```

**Handling native CRYFT:**

The native gas token (CRYFT) uses the same partitioned model, but at the protocol level rather than contract level:

- Each region tracks CRYFT balances independently.
- Cross-region CRYFT transfers use the same debit-checkpoint-credit flow.
- Main tracks total supply and ensures conservation: Î£(region_balances) = total_supply.

**Comparison: Partitioned vs. Wrapped model:**

| Aspect | Partitioned Balances | Wrapped Tokens (LMB) |
|:-------|:--------------------|:---------------------|
| User mental model | "I have 300 USDC on Region A" | "I have 300 wUSDC (wrapped) on Region A" |
| Contract address | Same everywhere | Different (bridge + wrapped token) |
| Token symbol | Same (USDC) | Different (wUSDC, USDC.a, etc.) |
| Transfer mechanism | transferToRegion() | lock() + claim() |
| Accounting | Sum of regional balances | Locked on home + wrapped on others |
| Implementation complexity | Simpler | More contracts |
| Wallet UX | Cleaner (one token, regional balances) | Confusing (multiple token symbols) |

**Recommendation:** Use the **partitioned balance model** as the default for CSS-1 regions. The wrapped token model remains available for custom subnets or bridging to external chains (Ethereum, etc.).

**Supply conservation invariant:**

```text
For any token T deployed via federation registry:

Î£ (balances[region][account] for all accounts, for all regions) = total_supply[T]

This is verified by:
1) Each region reports its total balance in checkpoints
2) Main aggregates and verifies: Î£(region_totals) = expected_supply
3) Discrepancy triggers investigation and potential bridge pause
```

**Handling the "follow-me" mirroring case:**

The account mirroring feature (Section 10.6) can work with the partitioned model, but requires careful design. Mirroring allows a user to have **spending authorization** across multiple regions without explicitly transferring each time.

**Important:** Mirroring does NOT duplicate assets. It provides a **credit line** mechanism:

1. User deposits assets on Main into a mirroring contract.
2. Mirroring contract grants spending credit to selected regions.
3. User can spend up to their credit on any mirrored region.
4. Main reconciles all spending after checkpoints and adjusts remaining credit.
5. If user overspends (double-spend attempt), later transactions are reverted.

```text
Mirroring with partitioned balances:

User Alice enables mirroring for 1000 USDC across regions [A, B, C]:

Step 1: Deposit
- Alice transfers 1000 USDC from her Region A balance to Main mirroring contract
- Her Region A balance: 1000 â†’ 0 USDC
- Main mirroring contract holds: 1000 USDC for Alice

Step 2: Credit allocation
- Main grants Alice credit_line = 1000 on each mirrored region
- This is NOT balance duplicationâ€”it's spending authorization

Step 3: Spending
- Alice spends 300 on Region A â†’ local_spent[A] = 300
- Alice spends 200 on Region B â†’ local_spent[B] = 200
- Total spent: 500, within 1000 limit âœ“

Step 4: Reconciliation (on checkpoint)
- Main receives: spent_A=300, spent_B=200, spent_C=0
- Main debits mirroring contract: 1000 - 500 = 500 remaining
- New credit_line pushed to regions: 500 each

Step 5: Double-spend attempt (attack)
- Alice tries to spend 400 on A and 400 on B simultaneously (total 800)
- Before sync: both succeed locally (each within 500 credit)
- Checkpoint order: A finalizes first â†’ spent_A=400, remaining=100
- B's checkpoint arrives â†’ spent_B=400 would exceed remaining
- Main rejects B's spend, marks for revert on Region B
- Alice penalized; mirroring may be suspended
```

The key insight: **mirroring converts partitioned balances into a credit system**, where Main is the source of truth and regions operate optimistically with reconciliation.

**Protocol-level enforcement:**

The single-location invariant (or partitioned balance integrity) is enforced at multiple layers:

1. **Partitioned balance contracts** track per-region balances separately.
2. **Cross-region transfers** require debit-checkpoint-credit flow.
3. **Checkpoint verification** (on Main) ensures only valid debits are recognized.
4. **Claim verification** (on destination) verifies Merkle proofs and tracks consumed transfer_ids.
5. **ZK validity proofs** (optional) make forgery computationally infeasible.
6. **Federation Contract Registry** ensures same code at same address across regions.
7. **Slashing** for validators who sign invalid checkpoints.

**Emergency procedures:**

If a bug or attack causes balance discrepancy:

1. **Pause cross-region transfers** via federation governance emergency action.
2. **Audit discrepancy** using checkpoint history on Main.
3. **Reconcile** by adjusting balances on affected region(s) or compensating from treasury.
4. **Post-mortem** and protocol upgrade to prevent recurrence.

The combination of partitioned balances, cryptographic proofs, deterministic deployment, and governance oversight ensures that the sum of all regional balances always equals the canonical supply.

---

## 11. Asset model, rewards, and monetary policy

### 11.1 Native gas asset across the federation

CryftNet uses a native gas asset (denoted CRYFT in this document) for transaction fees on Main and
on CSS chains by default. Custom subnets may use alternative fee assets, but must publish their fee
asset policy in their Federation Interface Declaration. A consistent fee asset simplifies routing, pricing,
and cross-chain UX, but is not mandatory for all subnets.

### 11.2 Fee markets

There are multiple fee markets: - Execution fees: EVM gas fees on Main and on subnets. - Settlement
fees: fees for anchoring checkpoints and relaying cross-chain messages. - CGS fees: fees for private
intent propagation, threshold services, and spam resistance. - Storage/pinning fees: budgets
attached to pin jobs for IPFS availability.

### 11.3 Validator rewards: Main and regions

Reward sources are a sum of: - base emission (optional): E_epoch - transaction fees: F_epoch (gas
fees) net of burns (if any) - settlement fees: S_epoch - treasury subsidies: T_epoch (optional) Let

```text
R_epoch = E_epoch + F_epoch + S_epoch + T_epoch. Rewards are split: - Main validator set:
R_main = R_epoch * w_main - Region validator sets: R_regions = R_epoch * w_regions (distributed
among participating regions by activity and stake) - CGS service providers: R_cgs = R_epoch *
w_cgs - Pin providers: R_pin = P_epoch (separately budgeted by pin jobs, plus optional treasury
top-ups) Where w_main + w_regions + w_cgs <= 1; remaining may be burned or sent to treasury.
```

#### 11.3.1 Parameter table (example defaults)

| Parameter | Symbol | Example | Notes |
|:----------|:-------|:--------|:------|
| Epoch length | EPOCH | 10 minutes (regions), 30 minutes (Main) | Regions shorter; Main longer for stability |
| Fast quorum | q_fast | 67% | Used in CRVS fast path |
| Slow quorum | q_slow | 80% | Used in CRVS slow path |
| Ping RTT max (region) | RTT_MAX | 80 ms | Eligibility gate; region-specific |
| Ping quorum | q_beacon | >= 3 of 5 beacons | Prevents single beacon bias |
| Slashing max | SLASH_MAX | up to 5% stake | For provable misbehavior; governed |

```text
Example weight policy (governance-controlled):
w_main   = 0.35
w_regions= 0.45
w_cgs    = 0.10
w_treas  = 0.10   // treasury accumulation
(These are illustrative, not fixed.)
```

Within a validator set, rewards are distributed by a combination of stake weight and performance:

- **stake_weight(v):** based on bonded stake (and delegated stake where supported)
- **perf(v):** based on uptime, vote participation, relay responsiveness, and (for regions) eligibility score from pings

```text
RewardShare(v) = stake_weight(v)^a * perf(v)^b / Z
```

with exponents a,b set by governance (typical: a near 1, b in [0.3, 1.0]).

**Figure 2: Reward flows (illustrative)**

```mermaid
flowchart LR
  Fees[Fees] --> Treasury[Treasury / Policy]
  Emission[Emission] --> Treasury
  Treasury --> MainV[Main validators]
  Treasury --> RegionV[Region validators]
  Treasury --> CGS[CGS / service providers]
  Treasury --> Pins[Pin providers]
```

### 11.4 IPFS pinning rewards: availability as a protocol primitive

CryftNet treats IPFS availability as a rewarded service rather than a background assumption. Pinning
rewards are designed to keep critical content (portals, module binaries, and app assets) available
with measurable reliability. Key components: 1) Pin Provider Registry: providers stake/bond and
advertise a service endpoint (or declare they operate via Cryftee ipfs_v1). 2) Pin Jobs: on-chain

---

contracts describing what to pin, how long, replication targets, and budgets. 3) Proof of Availability:
periodic challenges and attestations to verify that providers can actually serve the pinned content. 4)
Reward distribution and slashing: providers earn per-epoch rewards based on verified availability;
repeated failure or fraud is penalized.
#### 11.4.1 Pin Provider Registry

Providers register on Main or on a CSS region chain (or both). Registration includes: - provider_id
(pubkey or address) - service endpoint metadata (optional; can be hidden for private providers) -
supported regions / latency hints - bonded stake and slashing terms - supported proof method
(challenge-response, auditor, or hybrid)
PinProvider {
  provider_id: 0xPubKey,
  stake_bond: 10000 CRYFT,
  endpoints: ["https://pin.midwest.example", "ipfs-peer:12D3KooW..."],
  regions: [42],                   // optional
  proof_method: "HYBRID",
  max_jobs: 1000,
  terms: { slash_missed: 0.1%, slash_fraud: 5%, grace: 2 epochs }
}
#### 11.4.2 Pin Jobs and markets

A pin job is a contract created by a user/app/treasury. Jobs can be public or private. Public job: CID is
visible on-chain. Private job: chain stores only a commitment; CID is disclosed to selected providers
via CGS envelopes.
PinJob {
  job_id: 771_000_0042,
  cid_or_commitment: "cid:Qm..." | "commitment:0x...",
  replication_target: 7,
  duration_epochs: 4320,            // e.g., 30 days if epoch=10min
  budget: 2500 CRYFT,
  region_hint: 42,
  privacy: { mode: "public" | "private", auditors: [a1,a2,a3] },
  sla: { max_p95_retrieval_ms: 400, min_availability: 0.98 }
}
#### 11.4.3 Proof of Availability (hybrid scheme)

Primary proposal: Hybrid challenge-response plus auditor sampling. - The chain (or a region
committee) issues challenges derived from a randomness beacon. - Each challenge references the
CID and a random block index. Providers must return a proof within a time window. - Auditors
randomly verify a subset by fetching content from the provider and comparing hashes. Auditors then
sign attestations. This avoids trusting providers alone while limiting on-chain bandwidth.
Challenge(epoch, job_id, provider_id):
  idx = H(rand || provider_id) mod N_blocks
  nonce = H(rand || "nonce" || provider_id)
ProviderResponse:

```jsonc
{
  job_id: ...,
  provider_id: ...,
  epoch: ...,
  idx: ...,
  nonce: ...,
  // proof depends on chunking scheme:
  // - block_hash + raw block bytes OR
  // - merkle proof if CID references a merklized DAG
  block_hash: 0x...,
  block_bytes_b64: "...",
  sig: Sign(provider_sk, H(job_id||epoch||idx||nonce||block_hash))
}
AuditorAttestation:
{
  job_id: ...,
  provider_id: ...,
  epoch: ...,
  checked: true,
  retrieval_ms_p95: 312,
  ok: true,
  auditor_sig: Sign(auditor_sk, H(...))
}
```

#### 11.4.4 Availability scoring and rewards

Providers earn rewards based on an Availability Score computed per job per epoch. Score =
0.5*success_rate + 0.3*audit_ok + 0.2*latency_score + diversity_bonus Reward(job, provider, epoch)
= (job_budget_per_epoch) * Score / sum_provider_scores
job_budget_per_epoch = job.budget / job.duration_epochs
If provider misses challenges:
- apply slash_missed per epoch beyond grace
If fraud proven (forged response or impossible content):
- slash_fraud and ban provider for ban_epochs
#### 11.4.5 Pinning and portals/IPNS

Critical CryftNet web portals and module artifacts are content-addressed and often referenced via
IPNS keys. To keep "latest portal" reliable, the network can: - pin the portal index CID set referenced
by the current IPNS record, - additionally pin the last N historical portal versions for rollback
resilience, - run private pin jobs for sensitive modules or private portals, using CGS to reveal CIDs
only to authorized providers. Pinning rewards thus become part of the chain's operational backbone.

---

## 12. Governance: federated DAO and cross-network democracy

CryftNet governance is federated. The Main chain hosts the primary DAO that defines
federation-wide rules, registries, and security parameters. Each subnet/region can host its own DAO
for local parameters. The key design tension is: - local autonomy for regions and custom subnets, -
global coordination for shared UX, security, and registries. The governance system therefore
distinguishes: Federation Proposals vs Local Proposals.

### 12.1 Federation Proposals (Main chain)

Federation Proposals affect the shared layer:

- protocol upgrades for Main (CRVS params, scheduler rules, checkpoint format)
- registry changes (region list, subnet listings, certification programs)
- global economic parameters (emission schedule, base fee policy, treasury policy)
- Cryftee trust roots: publisher allowlists, GitHub verification policy
- global CGS standards (message formats, key rotation cadence)
- disputes and slashing appeals that affect cross-chain trust
### 12.2 Local Proposals (Regions and subnets)

Local Proposals affect a single subnet or region:

- committee membership policies and staking minimums
- ping beacon set membership and RTT thresholds
- local fee policies and subsidy allocation
- local pinning reward programs and auditor committees
- optional features (e.g., enabling CGS pools, enabling parallel tx envelope by default)
### 12.3 The Federated DAO: broader votes across all networks

Federation governance is strengthened by including votes from across the federation, not only Main validators. Proposal: a two-chamber model with cross-network aggregation.

**Chamber A: Validator Council (Main)**
- stake-weighted vote of Main validators
- optimized for rapid security decisions and technical upgrades

**Chamber B: Federation Assembly (All networks)**
- voting power aggregated from regions and certified subnets
- allows broader representation of users and local validator sets
- each network may choose its own internal voting method, then export a signed aggregate to Main
#### 12.3.1 Cross-network vote export (Governance Adapters)

A subnet that wants to participate in federation governance registers a Governance Adapter on Main:

---


- adapter_type (EVM contract, validity proof system, or external committee)
- vote_weight policy (stake-based, token-based, mixed, or capped)
- export format (signed root of votes, merkle proofs for audits)
- dispute and audit rules

```text
VoteExport {
  proposal_id: 0xP...,
  subnet_id: 42,
  totals: { yes: 1_230_000, no: 120_000, abstain: 50_000 },
  eligible_weight: 1_500_000,
  merkle_root: 0x...,
  proof: { type: "SUBNET_QUORUM_SIG", sig: 0x..., signers: bitmap },
  timestamp: 1700000000
}
```
#### 12.3.2 Aggregation and decision rules

Main computes a final decision using both chambers. Example rule (illustrative): - A proposal passes
if: (ValidatorCouncil_yes >= 2/3 of stake AND Assembly_yes >= 1/2 of exported weight) OR
(ValidatorCouncil_yes >= 3/4) for emergency security patch class
### 12.4 Governance safety: timelocks, signaling, and staged activation

Upgrades and parameter changes use:

- on-chain signaling period (days to weeks)
- timelock before activation
- activation height for deterministic deployment
- rollback plan and kill-switch conditions for emergencies

Regions may adopt federation upgrades on their own cadence, but CSS-1 compatibility requires staying within supported version windows.
### 12.5 Validator eligibility governance via pings

Ping-based eligibility is itself governed. Regions can vote on:

- which beacons are trusted
- RTT/loss/jitter thresholds (and how strict they are)
- how eligibility affects rewards (e.g., linear scaling vs hard gate)
- penalties for falsified measurement attempts

Main can set federation minimums to prevent "fake regions" that degrade user routing or security assumptions.
### 12.6 Dispute resolution and appeals

Some decisions require adjudication: - slashing disputes (validator misbehavior, pin provider fraud,
CGS key compromise) - governance export disputes (subnet reported totals vs audited votes)
CryftNet may use a "court-like" committee elected by federation governance. The committee can
require selective disclosure of evidence (CGS DisputeBundle). Decisions are recorded on Main and
can trigger slashing or registry changes.

---

## 13. Cryftee: signed WASM module runtime for chain utilities

Cryftee is a Rust-based TEE-style sidecar runtime designed to integrate with cryftgo and
Web3Signer. It is deliberately stateless: it does not store long-term secrets on disk and instead relies
on external key managers (Web3Signer, Vault) or ephemeral key material. Cryftee loads signed
WASM modules from a manifest and exposes a versioned API over UDS or HTTPS. It also ships with
a kiosk-style web UI for operators on port 3232.
### 13.1 Why a sidecar runtime?

- Keeps the consensus client lean: consensus and execution code stays minimal; auxiliary features
live in modules.
- Upgrades and experiments are safer: modules are signed and version-gated; incompatible code
can be rejected.
- Operational consistency: the same module APIs can be used across Main and subnets.
- Security boundaries: key operations can be isolated behind Web3Signer and attestation hooks.
### 13.2 Runtime properties

- Loads and manages signed WASM modules from a manifest.json registry.
- Provides BLS/TLS staking key operations via modular plugins.
- Exposes a versioned API over Unix Domain Socket (default) or HTTPS.
- Includes a kiosk web UI on port 3232 with per-module GUIs rendered as tabs.
- Enforces version compatibility (minCryftteeVersion) and publisher trust.
### 13.3 Embedding CGS inside Cryftee

| Module | Version | Purpose | Representative capabilities |
|:-------|:--------|:--------|:----------------------------|
| bls_tls_signer_v1 | 1.2.0 | BLS + TLS staking module with Web3Signer integration and module signing | bls_register, bls_sign, bls_verify, tls_register, tls_sign, tls_verify, sign_module, verify_module |
| debug_v1 | 1.0.0 | Diagnostics and runtime inspection | debug_echo, debug_info, debug_panic |
| llm_chat_v1 | 1.0.0 | Operator assistance via LLM interface | llm_chat, llm_stream |
| ipfs_v1 | 2.0.0 | Embedded IPFS node management (full/light modes) | node_start, ipfs_add, ipfs_pin, ipns_publish, peer_connect |
| redeemable_codes_v1 | 1.0.0 | On-chain redeemable gift code system | code_generate, code_redeem, code_freeze, validator_code_redeem |
| private_sync_v1 | 1.0.0 | Cryft-style private transaction synchronizer (CGS domain module) | domain_create, party_register, tx_submit, view_decrypt, mediator_confirm |

CGS is embedded in Cryftee in two layers:

- A CGS core service in the runtime that manages routing, pools, and key rotation schedules.
- A set of modules (starting with private_sync_v1) that implement domain logic: party registration, tx submit/confirm, view requests, and mediator flows.

This mirrors Cryft-style constructs while remaining pluggable. Embedding CGS in Cryftee keeps the synchronizer close to the validator, reducing latency and enabling tight integration with mempool selection and Smart Slot scheduling (via slot commitments).
### 13.4 Trust model: signed modules and publisher verification

All modules are verified before load:

- hash verification against manifest.json
- signature verification (Ed25519) against trust.toml or
- GitHub-based verification (signed commits, CI builds, attestations) under policy

Rejected modules do not load and do not affect runtime stability.
```jsonc
// trust.toml (example)
[[publishers]]
id        = "cryft-labs"
algo      = "ed25519"
publicKey = "BASE64_PUBLIC_KEY_HERE"
[[github_publishers]]
id                     = "cryft-labs"
github_org             = "cryft-labs"
allowed_repos          = ["cryfttee-modules"]
require_signed_commits = true
require_actions_build  = true
allowed_workflows      = ["release.yml"]
allow_prereleases      = false
```

### 13.5 Initial module set (v0.4.x runtime)

The initial module set provides staking, diagnostics, IPFS services, redeemable codes, and private synchronization. Modules may include GUIs served through the kiosk interface and sandboxed in iframes.
### 13.6 API surface (summary)

Cryftee provides:

- **Staking endpoints:** BLS/TLS register and sign
- **Runtime endpoints:** attestation, schema, reload modules
- **Module GUI endpoints**

The transport can be UDS (default) or HTTPS.

**Staking:**
```text
POST /v1/staking/bls/register
POST /v1/staking/bls/sign
POST /v1/staking/tls/register
POST /v1/staking/tls/sign
GET  /v1/staking/status
```

**Runtime/Admin:**
```text
GET  /v1/runtime/attestation
GET  /v1/schema/modules
POST /v1/admin/reload-modules
```

**Module GUIs:**
```text
GET  /api/modules/{module_id}/gui/
```
### 13.7 Operational integration with cryftgo

cryftgo launches Cryftee as a child process and configures it via environment variables. cryftgo can
verify the Cryftee binary hash before launch and optionally require attestation for sensitive operations.

**Core:**
```text
CRYFTTEE_MODULE_DIR=./modules
CRYFTTEE_MODULES=bls_tls_signer_v1,ipfs_v1,private_sync_v1
CRYFTTEE_API_TRANSPORT=uds
CRYFTTEE_UDS_PATH=/tmp/cryfttee.sock
```

**Web3Signer:**

---

```text
CRYFTTEE_WEB3SIGNER_URL=http://localhost:9000
CRYFTTEE_WEB3SIGNER_TIMEOUT=30
```

**Key derivation:**
```text
CRYFTTEE_KEY_SEED=<hex>
CRYFTTEE_NODE_ID=<node_id>
```

**Security:**
```text
CRYFTTEE_VERIFIED_BINARY_HASH=sha256:<hex>
CRYFTTEE_REQUIRE_ATTESTATION=false
```

---

## 14. Security model and threat analysis

CryftNet security spans multiple planes: consensus, execution determinism, cross-region asset integrity, governance, privacy propagation, and availability incentives. This section lists key threat classes and mitigations. It is not exhaustive; it is a starting point for formal review.

### 14.1 Consensus threats

- **Network partition:** regions may split. Mitigation: slow-path voting, increased anchoring to Main, conservative checkpoint acceptance.
- **Relay censorship:** rotor relays could delay data. Mitigation: relays are non-authoritative; fallback gossip; relay performance affects rewards.
- **Adaptive adversary:** targets soft leaders. Mitigation: leaderless option; rotate relay sets; use sampling.
- **Checkpoint withholding:** region produces blocks but delays checkpointing to Main. Mitigation: checkpoint liveness requirements; rewards tied to checkpoint frequency; user failover to Main.

### 14.2 Smart Slot threats

- **Under-claiming:** tx claims fewer slots than it touches, breaking determinism. Mitigation: runtime detection where possible; slashing if provable; SDKs; contract-provided hints; conservative policies for high-risk calls.
- **Over-claiming:** reduces parallelism (safe). Mitigation: tooling and incentives (lower fees for precise claims).
- **Slot collision:** bad derivation leads to collisions. Mitigation: strict canonical encoding and domain separators; versioned CEP.

### 14.3 CGS threats

- **Traffic analysis:** timing correlates sender/receiver. Mitigation: batching, cover traffic, delayed reveals.
- **Key compromise:** threshold key compromised. Mitigation: frequent rotation; multi-party control; optional HSM/TEE.
- **Spam intents:** adversary floods. Mitigation: fees, rate limits, capability gating, proof-of-work optional.
- **Complexity:** bugs introduce consensus risk. Mitigation: keep CGS non-consensus-critical where possible; staged rollouts.

### 14.4 Ping eligibility threats

- **Proxy/VPN gaming:** validator tunnels into region. Mitigation: multi-beacon diversity, random challenges, jitter/loss scoring, correlation across peers.
- **Beacon capture:** beacons collude. Mitigation: beacon governance, rotating beacons, audits, optional federation beacon set.
- **Measurement falsification:** forged reports. Mitigation: signed reports, nonces, on-chain verification of signatures.

### 14.5 Pinning incentive threats

- **Fake pin proofs:** provider claims availability without serving. Mitigation: random challenges, auditor fetches, fraud slashing.
- **Sybil providers:** same operator registers many providers. Mitigation: stake requirements, identity policies, diversity bonuses weighted by independent attestations.
- **Auditor corruption:** auditors lie. Mitigation: multiple auditors, randomized sampling, auditor staking and slashing.

### 14.6 Cross-region and partitioned balance threats

The partitioned balance model introduces specific threat vectors that must be addressed:

- **Cross-region double-spend (race condition):** User initiates transfer from Aâ†’B, then tries to spend on A before checkpoint. Mitigation: balance is debited immediately on A; spending fails because balance is already reduced.

- **Replay attack on claims:** Attacker replays a valid claim proof to credit balance multiple times on destination region. Mitigation: each transfer_id is marked as consumed after first claim; claimed[transfer_id] = true prevents replay.

- **Forged checkpoint proof:** Attacker forges a Merkle proof of a debit that never happened. Mitigation: proofs are verified against Main-finalized checkpoint roots; ZK validity proofs make forgery computationally infeasible; validators who sign invalid checkpoints are slashed.

- **Region validator collusion:** Majority of region validators conspire to create fake debit events. Mitigation: Main requires quorum signatures on checkpoints; ZK proofs provide trustless verification; users can always withdraw to Main as escape hatch.

- **Checkpoint reorg attack:** Region finalizes a checkpoint, then reorgs to remove the debit while destination already credited. Mitigation: Main does not accept checkpoints until region finality is confirmed; ZK proofs bind to specific state transitions.

- **Supply inflation via multiple regions:** Bug or attack causes same tokens to exist on multiple regions without proper debit. Mitigation: Main tracks Î£(region_balances) per token; discrepancy triggers bridge pause and investigation; conservation invariant is checked on every checkpoint.

- **Contract address mismatch:** Malicious region deploys different code at the "same" address. Mitigation: Federation Contract Registry on Main records (address, code_hash); regions must match; wallets verify registry status before displaying tokens.

- **CREATE2 front-running (malicious code):** Attacker tries to deploy malicious contract at predicted address before legitimate deployment. **Natural protection:** CREATE2 address depends on init_code hash; different code = different address. Attacker cannot deploy different code at the same address. **Residual risk:** Deployer key compromise. Mitigation: federation-controlled deployer with governance authorization; multisig or threshold signatures; tiered deployment model.

- **Deployment race condition (same code):** Multiple parties attempt to deploy identical code simultaneously on different regions. **Not harmful:** Whoever deploys first on a region simply succeeds; the code is identical. Federation Contract Registry ensures only governance-approved deployments are marked as verified.

- **Uncoordinated region deployment:** Region deploys contract before receiving Main checkpoint authorization. Mitigation: FederationDeployer requires authorization from Main checkpoint before allowing deployment; unauthorized calls revert.

- **Constructor balance duplication:** Token constructor initializes balances (e.g., `balances[issuer] = 1B`), and deploying on multiple regions multiplies the supply. **Critical mitigation:** Federation-verified tokens MUST use zero-balance constructors; initial supply is minted via separate transaction on designated home_region only; M-Chain GBL is authoritative source of truth, not local contract storage; governance code review rejects contracts with constructor-initialized balances.

- **Home region bypass:** Attacker tries to call mint() on non-home region. Mitigation: mint() function checks `REGION_ID == registry.homeRegion(address(this))` and reverts otherwise; only authorized_minter on home_region can create new supply.

- **Mirroring credit abuse:** User enables mirroring, spends on multiple regions simultaneously before reconciliation. Mitigation: Main orders checkpoints globally; later transactions that exceed remaining credit are reverted; user penalized and mirroring suspended.

- **Stale credit line exploitation:** User's mirroring credit is reduced on Main, but region hasn't received update. User spends stale credit. Mitigation: credit lines have epoch validity; regions must refresh from Main periodically; transactions using stale credit are subject to revert.

- **Griefing via transfer spam:** Attacker initiates many small cross-region transfers to congest checkpoint message roots. Mitigation: minimum transfer amounts; fees proportional to cross-region message size; rate limits per account.

- **Unclaimed transfers (stuck funds):** User initiates transfer but never claims on destination. Mitigation: transfers can be reclaimed on origin after timeout (e.g., 30 days); refund requires proof of non-claim.

- **Region exit scam:** Region validators collude to steal all regional balances before abandoning the chain. Mitigation: users can always exit to Main via checkpoint proof; Main serves as "home of last resort"; region slashing and reputation systems.

### 14.7 Data availability and ZK threats

- **DAS sampling failure:** Insufficient samples to guarantee availability. Mitigation: conservative sampling parameters; fallback to full download for critical operations.
- **ZK prover centralization:** Few parties can generate proofs, creating censorship risk. Mitigation: multiple prover implementations; prover decentralization incentives; fallback to quorum verification.
- **ZK soundness bug:** Flaw in ZK system allows invalid proofs. Mitigation: multiple proof systems; formal verification; staged rollout with quorum fallback.

### 14.8 Multi-chain Main and hierarchical registration threats

- **C-Chain / M-Chain desync:** Atomic messaging between C-Chain and M-Chain fails, causing inconsistent state. Mitigation: shared validator set ensures atomic block production; recovery protocol for rare edge cases.
- **M-Chain governance capture:** Attacker gains control of M-Chain to manipulate subnet registrations. Mitigation: same governance protections as C-Chain; two-chamber votes; timelocks.
- **Rogue State chain registering malicious Cities:** State DAO approves a City designed to defraud users. Mitigation: State reputation systems; user warnings for new Cities; exit to State as escape hatch.
- **City checkpoint withholding:** City validators delay checkpointing to State to enable fraud. Mitigation: checkpoint liveness requirements enforced by State; City slashing; user failover to State.
- **Cross-participation evasion:** CSS-1 validator stops validating Main while continuing State validation. Mitigation: Main monitors CSS-1 validator participation; automatic suspension from State if Main duties lapse.
- **State-mediated censorship of Cities:** State refuses to include City checkpoints. Mitigation: Cities can appeal to Main governance; emergency City-to-Main bridge for exit; State reputation damage.

### 14.9 Global Balance Ledger (GBL), Contract Mirror Registry (CMR), and State Balance Ledger (SBL) threats

- **GBL manipulation:** Attacker attempts to modify M-Chain GBL records to inflate regional balances. Mitigation: GBL updates require checkpoint proofs from origin region; Main validator consensus on all GBL state transitions; slashing for malicious proposals.
- **GBL-regional desync:** Region's local balance tracking diverges from GBL. Mitigation: periodic reconciliation audits; discrepancy detection triggers bridge pause; conservation invariant checked on every checkpoint.
- **CMR manipulation:** Attacker attempts to modify M-Chain CMR to add unauthorized target_regions or mark non-deployed contracts as deployed. Mitigation: CMR updates only via verified checkpoint proofs; fee verification before region addition; Main validator consensus on all CMR state transitions.
- **CMR-region desync:** Region's local deployment registry diverges from M-Chain CMR. Mitigation: regions derive mirror permissions from CMR state in checkpoints; unauthorized local deployments not recognized by federation; periodic reconciliation audits.
- **CMR status forgery:** Region checkpoint falsely claims successful deployment. Mitigation: Main can verify deployment by querying region; ZK proof of contract existence; slashing for false checkpoint claims.
- **SBL-GBL desync:** City's State Balance Ledger diverges from State's view of City balances. Mitigation: State checkpoints include City balance summaries; discrepancies flagged for investigation; City suspension pending resolution.
- **City balance inflation:** City attempts to credit users with balances not backed by State allocation. Mitigation: SBL credits must not exceed State-allocated balance for City; checkpoints rejected if SBL sum exceeds allocation.
- **State blocking City transfers:** State refuses to process legitimate City-to-State balance movements. Mitigation: City can appeal to Main; emergency exit mechanism via Main governance; State reputation damage.
- **Orphaned regional balances:** Region becomes permanently unreachable, leaving GBL balances stranded. Mitigation: governance can trigger balance recovery after extended unreachability; Main serves as arbiter of final state.

### 14.10 Region-first deployment and federation fee threats

- **RegionDeployer compromise:** Attacker gains control of RegionDeployer on one region. Mitigation: RegionDeployer is immutable; only allows CREATE2 with predetermined logic; no admin keys; upgrade requires governance-approved chain migration.
- **Unauthorized mirror triggering:** Attacker calls `mirror()` on regions not declared in target_regions[]. Mitigation: mirror() verifies caller authorization from Main checkpoint; unauthorized calls revert; only Main can authorize mirroring.
- **target_regions[] manipulation:** Developer changes target_regions[] after deployment to add regions without paying fees. Mitigation: target_regions[] is immutable after deployment transaction; expanding requires new governance proposal and fee payment.
- **Federation fee evasion:** Developer deploys on region, then manually deploys on other regions to avoid federation fees. Mitigation: manual deployments are not marked as Federation-verified; users see warning for unverified contracts; no mirroring benefits.
- **Fee underpayment:** Developer provides insufficient fee for declared target_regions[]. Mitigation: RegionDeployer calculates required fee dynamically; transaction reverts if msg.value < requiredFee.
- **Fee oracle manipulation:** Attacker manipulates on-chain price oracle to reduce federation fees. Mitigation: fee rates are governance-controlled parameters; oracle aggregation; rate limits on fee changes.
- **Two-phase initialization griefing:** Attacker front-runs initialize() call on mirrored contract to set malicious parameters. Mitigation: initialize() requires deployer signature or is restricted to authorized_initializer set by constructor.
- **Initialization replay:** Attacker replays initialize() call on newly mirrored region. Mitigation: initialize() sets initialized = true; subsequent calls revert; pattern enforced by OpenZeppelin Initializable.
- **Cross-region initialization race:** Same contract initialized with different parameters on different regions. Mitigation: RegionDeployer requires init_data to be identical across regions; hash of init_data recorded on Main; mismatched initializations flagged.
- **Region expansion DoS:** Attacker declares maximum target_regions[] to congest checkpoints. Mitigation: per-deployment maximum regions (e.g., 50); checkpoint size limits; gas costs scale with region count.

### 14.11 Threat matrix (comprehensive summary)

| Threat | Plane | Impact | Mitigation summary |
|:-------|:------|:-------|:-------------------|
| Under-claimed slots | Execution | Nondeterminism / forks | SDK enforcement, audit, provable slashing, conservative policies |
| Relay censorship | Network | Delayed inclusion | Fallback gossip, performance-weighted rewards |
| Beacon capture | Eligibility | Fake regions | Beacon rotation, federation audits, quorum requirements |
| Pin provider fraud | Availability | Content loss | Challenge-response, auditors, slashing |
| CGS key compromise | Privacy | Disclosure risk | Threshold rotation, multi-party control, monitoring |
| Governance capture | Governance | Bad upgrades | Two-chamber votes, timelocks, veto and emergency policies |
| Cross-region double-spend | Asset integrity | Token duplication | Immediate debit, checkpoint ordering, transfer_id consumption |
| Forged checkpoint proof | Asset integrity | Unauthorized minting | Merkle verification, ZK proofs, validator slashing |
| Region validator collusion | Asset integrity | Fake debits/credits | Main quorum verification, ZK proofs, exit to Main |
| Supply inflation | Asset integrity | Economic damage | Conservation invariant check, bridge pause, checkpoint audits |
| Contract address mismatch | Execution | Malicious code execution | Federation Contract Registry, code_hash verification |
| Mirroring credit abuse | Asset integrity | Overspending | Global checkpoint ordering, revert mechanism, penalties |
| Region exit scam | Asset integrity | Total loss on region | Exit to Main via proof, slashing, reputation systems |
| Checkpoint withholding | Liveness | Delayed settlement | Liveness requirements, reward incentives, user failover |
| ZK soundness bug | Asset integrity | Invalid state accepted | Multiple proof systems, formal verification, quorum fallback |
| C-Chain / M-Chain desync | Consistency | Split-brain state | Shared validators, atomic blocks, recovery protocol |
| Rogue City registration | Asset integrity | User fraud via City | State reputation, user warnings, exit to State |
| Cross-participation evasion | Security | Weakened Main | Participation monitoring, automatic State suspension |
| GBL manipulation | Asset integrity | Regional balance inflation | Checkpoint proofs, Main consensus, slashing |
| GBL-regional desync | Consistency | Balance divergence | Reconciliation audits, bridge pause, invariant checks |
| CMR manipulation | Deployment | Unauthorized mirror expansion | Checkpoint proofs, fee verification, Main consensus |
| CMR-region desync | Consistency | Mirror state divergence | CMR as authority, periodic reconciliation |
| CMR status forgery | Security | False deployment claims | Main verification queries, ZK proofs, slashing |
| SBL-GBL desync | Consistency | City/State imbalance | State checkpoint audits, discrepancy flags, City suspension |
| City balance inflation | Asset integrity | Unbacked credits | SBL sum validation, allocation enforcement |
| Orphaned regional balances | Asset integrity | Stranded funds | Governance recovery, Main arbitration |
| RegionDeployer compromise | Security | Unauthorized deployments | Immutable contracts, no admin keys, governance migration |
| Unauthorized mirroring | Deployment | Unintended region spread | Main checkpoint authorization, target_regions[] enforcement |
| target_regions[] manipulation | Economics | Fee evasion | Immutable after deployment, governance for expansion |
| Federation fee evasion | Economics | Revenue loss | Unverified contract warnings, no mirroring benefits |
| Fee underpayment | Economics | Service denial | Dynamic fee calculation, revert on insufficient payment |
| Two-phase init griefing | Security | Malicious initialization | Deployer signature, authorized_initializer restriction |
| Initialization replay | Security | Parameter hijacking | initialized flag, OpenZeppelin Initializable pattern |
| Cross-region init race | Consistency | Parameter mismatch | Identical init_data requirement, Main hash recording |
| Region expansion DoS | Availability | Checkpoint congestion | Max regions limit, size limits, scaled gas costs |

---

## 15. Implementation roadmap and engineering checklist

This roadmap is a pragmatic decomposition into testable milestones. Each milestone should produce
artifacts: code, tests, benchmarks, and documented threat reviews. The checklist is intentionally
exhaustive: it is easier to delete items later than to discover them during an outage.
### 15.1 Milestone 0: Specification and simulation

- Finalize CEP-CSS-1 slot derivation and scheduler determinism rules.
- Define CRVS parameter ranges and implement a simulator (network + adversary models).
- Define checkpoint formats and message roots; build light verifier library.
- Define ping protocol (packet formats, nonce rules, signing, report encoding).
- Threat modeling workshops for Smart Slots, CGS, and pinning incentives.
### 15.2 Milestone 1: Main chain prototype (C-Chain + M-Chain)

- Fork and bootstrap consensus client (cryftgo baseline) and integrate Cryftee sidecar launch.
- Implement dual-chain Main architecture: C-Chain (EVM) and M-Chain (native VM).
- Implement M-Chain Global Balance Ledger (GBL) with per-region balance tracking.
- Implement M-Chain Contract Mirror Registry (CMR) for deployment mirror state tracking.
- Implement CMR â†” C-Chain Federation Registry synchronization.
- Implement Main chain registry contracts (regions, subnets, publishers, pin providers).
- Implement Federation Contract Registry with CREATE2 verification and code_hash tracking.
- Implement RegionDeployer and FederationDeployer contracts on Main.
- Implement checkpoint acceptance contract and quorum verification (BLS aggregate or equivalent).
- Implement cross-region transfer tracking and conservation invariant verification.
- Implement federation fee collection and treasury distribution.
- Implement governance framework (proposal lifecycle, timelocks, two-chamber vote scaffolding).
- Implement basic fee market and reward distribution accounting (no pinning yet).

### 15.3 Milestone 2: CSS-1 region chain prototype

- Implement CRVS region consensus prototype (fast/slow path; relay plane fallback).
- Implement Smart Slot envelope parsing and deterministic scheduler in the EVM engine.
- Deploy RegionDeployer on region chains with identical address to Main.
- Implement region-first deployment with target_regions[] declaration.
- Implement federation mirroring receiver (mirror() function with authorization verification).
- Implement two-phase initialization pattern for mirrored contracts.

---

- Implement partitioned balance contracts with transferToRegion() and claimFromRegion().
- Implement balance portability modes (region-locked, portable, replicated).
- Implement transfer_id generation, tracking, and replay protection.
- Add receipt extensions for parallel txs and commitment verification for CGS reveal.
- Implement region checkpoint producer and submitter to Main (including cross-region message roots).
- Implement ping beacon set governance and eligibility scoring.
- Implement cross-region transfer timeout and refund mechanism.
- Implement State Balance Ledger (SBL) for City balance tracking.
- Implement City registration via State (not Main).
### 15.4 Milestone 3: CGS and private intents

- Implement CGS core service in Cryftee runtime (routing, pools, key rotation cadence).
- Implement private_sync_v1 module support for domains, parties, tx submit/confirm, view
requests.

- Implement slot commitment workflow: IntentEnvelope -> RevealClaims -> scheduler -> execution.
- Implement dispute bundles and evidence retention policies.
- Add observability: metrics, dashboards, and privacy leak tests (timing correlation).
### 15.5 Milestone 4: IPFS pinning rewards

- Implement Pin Provider Registry and bonding/slashing rules.
- Implement Pin Job contract (public + private job modes).
- Implement challenge-response protocol and auditor committee tooling.
- Integrate with Cryftee ipfs_v1 module for node management and pin operations.
- Launch testnet with real pin providers and measure availability + fraud attempts.
### 15.6 Milestone 5: Federation hardening and production readiness

- Formal verification / property tests for scheduler determinism and slot lock rules.
- Consensus adversarial simulations (network partitions, equivocation, relay censorship).
- Security audits for Cryftee runtime, module verification, and key management integrations.
- Governance audits: vote export integrity, aggregation correctness, and timelock safety.
- Operational playbooks: upgrades, rollback, emergency pause policies, key rotation procedures.
### 15.7 Whitepaper completeness checklist (for publication)

- Clear definitions: Main, region, subnet, local chain, Cryftee, CGS, Smart Slots.
- Consensus description: safety/liveness assumptions, parameters, and finality guarantees.
- Execution model: EVM compatibility, tx formats, scheduler determinism, receipts, and conflict
handling.
- Federation model: checkpoints, cross-chain messages, replay protection, bridging assumptions.
- Governance: chambers, vote export, aggregation rules, proposal lifecycle, and upgrade safety.
- Validator eligibility: ping protocol, beacon governance, scoring, and incentives.
- Economics: fee markets, reward splits, emissions, and slashing policies.
- IPFS incentives: pin provider registry, job format, proof scheme, scoring, and fraud handling.
- Privacy: CGS message types, metadata matrix, key management, and dispute evidence rules.
- Security: threat model, mitigation list, audit plan, and monitoring metrics.
- Roadmap: milestones, test plans, benchmarks, and deployment strategy.
- Appendices: glossary, parameter ranges, JSON schema definitions, and reference implementations.

---

## 16. Appendices

### 16.1 Glossary (selected)

- **Primary Network:** The canonical foundation of CryftNet, consisting of three specialized chains: P-Chain (Platform), X-Chain (Exchange), and M-Chain (EVM Execution). Cryft Labs maintains first-class implementations and long-term governance over all three chains.
- **P-Chain (Platform):** The validator management and staking chain within the Primary Network. Handles validator set coordination, subnet registration, staking/delegation, checkpoint acceptance, and governance. Uses a native VM (not EVM).
- **X-Chain (Exchange):** The high-throughput native asset transfer chain within the Primary Network. Optimized for CRYFT transfers and native asset issuance using a UTXO model. Default chain for base asset movements.
- **M-Chain (EVM Execution):** The account-based smart contract execution chain within the Primary Network. Compatible with Solidity/Vyper toolingâ€”the dApp chain. When we say "EVM chain," we mean the M-Chain specifically, not the entire Cryft network. Interactions with M-Chain do not require region ID specification.
- **Region ID:** Unique identifier for a State/Region chain within the federation. Required for State/Region chain transactions and cross-region operations. NOT required for Primary Network M-Chain interactions.
- **Global Balance Ledger (GBL):** The authoritative data structure (part of M-Chain or P-Chain) tracking partitioned M-Chain token balances across all regionsâ€”which account owns how much of each M-Chain asset on which region. Native CRYFT balances live on X-Chain.
- **Contract Mirror Registry (CMR):** The authoritative data structure (part of M-Chain or P-Chain) tracking federation contract deploymentsâ€”target_regions[], deployed_regions[], mirror_status per region; updated via region checkpoints.
- **State Balance Ledger (SBL):** A State-level ledger tracking City balances within that State; not visible to the Primary Network.
- **Region chain / State chain:** A low-latency chain serving a latency domain and anchoring to the Primary Network (via P-Chain checkpoints). Requires region ID for transaction submission.
- **City chain / Local chain:** A sub-chain that registers via its parent State, not directly with the Primary Network; balances tracked in parent State's SBL.
- **CSS-1:** Cryft Standard Subnet profile for interoperability.
- **Smart Slot:** A deterministic schedulable resource representing a state dependency.
- **Process ID:** A lane identifier and namespace for parallel scheduling.
- **CGS:** Cryft Global Synchronizer, the privacy-aware propagation and synchronization plane.
- **Cryftee:** Signed WASM module runtime sidecar providing chain utilities and CGS hosting.
- **Pin provider:** An operator who earns rewards by keeping content available on IPFS.
- **Partitioned balance:** An asset accounting model where balances are tracked per-region; the same contract address exists on all regions but balances are region-specific.
- **Federation Contract Registry:** Main-hosted registry of canonical contract deployments, recording address, code_hash, deployer, and verified regions.
- **CREATE2 deployment:** Deterministic contract deployment using CREATE2 opcode, ensuring same address across all regions given identical deployer, salt, and init_code.
- **Cross-region transfer:** Movement of assets from one region to another via debit-checkpoint-credit flow, recorded in M-Chain GBL.
- **Cross-City transfer:** Movement of assets between Cities under the same State, recorded in State's SBL (does not touch Main).
- **Transfer_id:** Unique identifier for a cross-region transfer, used to prevent replay attacks.
- **Credit line (mirroring):** Spending authorization granted to regions for a user's mirrored balance, backed by assets held on Main.
- **Conservation invariant:** The rule that Î£(regional balances) must equal total supply for any token; enforced natively by M-Chain GBL.
- **Home region:** The designated region where a token's initial supply is minted; mint() calls only succeed on this region.
- **Zero-balance constructor:** Required pattern for federation-verified tokens where constructor initializes no balances; prevents supply duplication on multi-region deployment.
- **FederationDeployer:** A contract deployed on Main and all regions that enforces governance-approved deployments via CREATE2; requires Main checkpoint authorization before deploying.
- **RegionDeployer:** A contract at the same address on all regions enabling region-first deployment with deterministic addresses; supports opt-in federation mirroring.
- **Region-first deployment:** Developer-friendly model where contracts deploy to a region first, then Main mirrors to other regions via checkpoints if opted in.
- **Federation mirroring:** Process where Main propagates a contract deployment to other regions, maintaining the same address via deterministic CREATE2.
- **Balance portability:** Opt-in feature allowing contract balances to transfer across regions via debit-checkpoint-credit flow.
- **Target regions (target_regions[]):** Explicit list of region IDs a contract opts into for federation mirroring; deployer must pay federation fees for each declared region.
- **Federation fee:** Fee paid to Main for multi-region operations including contract mirroring, balance portability setup, and cross-region transfers; ensures Main receives appropriate gas for federation coordination.
- **Region expansion:** Post-deployment process to add additional regions to a contract's target_regions[]; requires payment of additional federation fees.
- **Two-phase initialization:** Pattern where contract deployment (zero state) is separate from initialization (setting initial balances), ensuring same address across regions.
- **DAS (Data Availability Sampling):** Technique allowing nodes to verify block data availability by sampling fragments rather than downloading entire blocks.
- **ZK-EVM:** Zero-knowledge Ethereum Virtual Machine enabling cryptographic proof-based validation of transaction batches.
### 16.2 Key open questions (research and engineering)

- What is the best enforcement mechanism against under-claimed slots without making the EVM slower (static analysis vs runtime tracing vs economic incentives)?
- What are optimal CRVS parameters under realistic Internet jitter for committees of size 50-500 across regions?
- How can CGS provide strong privacy guarantees without becoming consensus-critical complexity?
- What is the most robust and low-cost proof of availability for IPFS DAGs at scale?
- How should cross-network vote weight be capped to prevent plutocracy while still being Sybil-resistant?
- What is the optimal checkpoint frequency for cross-region transfers (latency vs. Main throughput trade-off)?
- How should mirroring credit lines be sized and refreshed to balance UX with double-spend risk?
- What timeout period for unclaimed transfers balances user convenience with stuck-funds risk?
- How can cross-region transfer fees be priced to discourage spam while remaining affordable?
- Should ZK validity proofs be required for cross-region claims above a certain value threshold?
- What is the optimal division of responsibilities between C-Chain and M-Chain? Should some operations (e.g., staking) live on C-Chain for EVM composability?
- How should validator rewards be split between Main validation and State validation duties?
- What is the appropriate bootstrap period for new CSS-1 States before requiring Main validation?

---

- Should Cities be allowed to "emergency bridge" directly to Main if their parent State censors them?
- How many Cities can a single State chain practically manage before checkpoint aggregation becomes a bottleneck?
- Should there be a minimum validator overlap requirement between a State and its Cities?
- What is the optimal federation fee structure to balance developer accessibility with Main sustainability?
- How should federation fees be adjusted dynamically based on network congestion or demand?
- Should region-first deployments have a "cooling period" before mirroring to prevent rushed malicious deployments?
- What is the maximum number of target_regions a single deployment can declare before checkpoint congestion becomes problematic?
- How should GBL handle edge cases where a region becomes permanently unreachable (orphaned balances)?
- Should two-phase initialization have a timeout after which anyone can initialize (preventing initialization griefing)?
- How should the federation handle a scenario where RegionDeployer needs to be upgraded across all chains?
- What dispute resolution mechanism should exist when a State and its City disagree on SBL balances?

---

<p align="center"><em>End of document.</em></p>
