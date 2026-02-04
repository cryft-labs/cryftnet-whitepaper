### 13.1 Architecture Overview

Cryftee is the off-chain computation and utility layer for CryftNet, designed as a modular sidecar that runs WASM modules for auxiliary features like CGS, IPFS, staking operations, and specialized validation logic.

#### 13.1.1 CryftGo vs. Cryftee

- **CryftGo** is the consensus client (blockchain interface) - a fork of AvalancheGo that handles on-chain consensus, block validation, and state transitions. CryftGo is the "consensus kernel" that must remain lean and proven.
- **Cryftee** is the off-chain computation and utility layer - a modular sidecar that runs WASM modules for auxiliary features like CGS, IPFS, staking operations, and specialized validation logic.
- **All extensions are modules** within Cryftee. IPFS, CGS, pin provider logic, governance helpers, and future features are all WASM modules that load into Cryftee's runtime.

#### 13.1.2 Design Rationale

1. **Consensus safety:** Novel features (CGS, Smart Slots parallel scheduling, IPFS) do not touch the consensus kernel. CryftGo remains a minimal, auditable, proven codebase.
2. **Modular upgrades:** Modules can be upgraded independently via signed releases without requiring consensus client upgrades or chain-wide coordination.
3. **Off-chain parallelism:** Cryftee can perform parallel validation, content availability checks, and computation-heavy tasks off-chain, then submit proofs/attestations to CryftGo for on-chain recording.
4. **Targeted deployments:** Different validators can run different module sets based on their operational needs (e.g., IPFS-only validators, CGS relays, pin providers).

#### 13.1.3 Why a Sidecar Runtime?

- Keeps the consensus client lean: consensus and execution code stays minimal; auxiliary features live in modules.
- Upgrades and experiments are safer: modules are signed and version-gated; incompatible code can be rejected.
- Operational consistency: the same module APIs can be used across Main and subnets.
- Security boundaries: key operations can be isolated behind Web3Signer and attestation hooks.

#### 13.1.4 Cryftee's Role in the Federation

**Primary Network (Federal Chain, Mirror Chain, EVM Chain):** All three chains use Cryftee modules for operations:
- Federal Chain: Validator eligibility checks, governance vote aggregation, checkpoint acceptance logic
- Mirror Chain: UTXO validation assistance, high-throughput parallel processing, GBL management support
- EVM Chain: Smart contract execution support, cross-chain messaging coordination
- All chains: CGS hosting for privacy-aware transaction propagation

**Subnets/Regions:** Each subnet validator runs Cryftee for:
- CGS domain participation (privacy pools, intent routing)
- IPFS pinning and content availability attestations
- Local balance tracking synchronization with Mirror Chain GBL (if opted into federation)
- Checkpoint submission to Primary Network

#### 13.1.5 Consensus Validates Cryftee Outputs

Cryftee performs off-chain computation (parallel validation, IPFS availability checks, CGS routing), but **consensus verifies the results**:

1. Cryftee modules compute outputs (e.g., "these IPFS CIDs are available," "this cross-region transfer is valid")
2. Modules produce signed attestations or proofs
3. CryftGo validators verify attestations on-chain (signature checks, quorum requirements, slashing conditions)
4. Only verified outputs are committed to the blockchain

This achieves **high parallel throughput** (Cryftee does the heavy lifting off-chain) while maintaining **consensus security** (CryftGo validates all results on-chain).

#### 13.1.6 GBL and Cryftee: Opt-in Federation Without Bridges

The Global Balance Ledger (GBL) on Mirror Chain can be accessed by:
- **Subnets opting into GBL** - subnets query Mirror Chain's GBL via atomic cross-chain messaging or precompiles; no custom bridge contracts required
- **EVM Chain contracts** - query Mirror GBL via precompiles or atomic messaging for federation-wide balance views
- **Cross-region transfers** - processed through Mirror Chain's UTXO model with checkpoint verification at each step

This provides a **unified, robust approach to cross-chain balance tracking** with Mirror Chain as the authoritative ledger.

