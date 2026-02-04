## 13. Cryftee: Signed WASM Module Runtime for Chain Utilities

Cryftee is a Rust-based TEE-style sidecar runtime designed to integrate with CryftGo and Web3Signer. It is deliberately stateless: it does not store long-term secrets on disk and instead relies on external key managers (Web3Signer, Vault) or ephemeral key material. Cryftee loads signed WASM modules from a manifest and exposes a versioned API over UDS or HTTPS. It also ships with a kiosk-style web UI for operators on port 3232.

This section is split into multiple files for easier navigation:

- [13.1 Architecture Overview](13-01-architecture.md) - CryftGo vs Cryftee separation, design rationale, federation role
- [13.2 Runtime Properties](13-02-runtime.md) - Module loading, API surface, trust model
- [13.3 Core Modules](13-03-core-modules.md) - Overview of all 7 core modules
  - [13.3.1 BLS/TLS Signer](13-03a-bls-tls-module.md) - Staking cryptography, multi-device, Web3Signer
  - [13.3.2 Debug Module](13-03b-debug-module.md) - Diagnostics and runtime inspection
  - [13.3.3 LLM Chat Module](13-03c-llm-chat-module.md) - Operator assistance interface
  - [13.3.4 IPFS Module](13-03d-ipfs-module.md) - Content-addressed storage with pin rewards
  - [13.3.5 CGS Module (Private Sync)](13-03e-cgs-module.md) - Canton-style confidential transactions
  - [13.3.6 Redeemable Codes](13-03f-redeemable-codes.md) - TEE-secured gift codes
  - [13.3.7 Agent Identity & Memory (AIM)](13-03g-aim.md) - On-chain agent registry, tokenized identity
- [13.4 Operational Integration](13-06-operations.md) - Node types, Cryftee requirements, configuration

---

### Architecture Summary

**CryftGo vs. Cryftee:**

| Component | Role | Responsibilities |
|:----------|:-----|:-----------------|
| **CryftGo** | Consensus client | Block validation, state transitions, consensus participation, on-chain verification |
| **Cryftee** | Utility sidecar | Off-chain computation, WASM module execution, IPFS/CGS operations, signed attestations |

**Why separate?**

1. **Consensus safety:** Novel features do not touch the consensus kernel
2. **Modular upgrades:** Modules upgrade independently via signed releases
3. **Off-chain parallelism:** Heavy computation off-chain, proofs verified on-chain
4. **Targeted deployments:** Validators choose module sets based on operational needs

**Core Modules (Required for Full Network Capability):**

All seven modules below are considered **core modules** required to operate at full capacity with complete network capabilities:

| Module | Category | Purpose |
|:-------|:---------|:--------|
| `bls_tls_signer_v1` | **Staking** | BLS/TLS key operations, checkpoint signing, multi-device support |
| `ipfs_v1` | **Storage** | Content-addressed storage, tiered pin rewards, storage challenges |
| `private_sync_v1` | **Privacy** | Canton-style CGS, encrypted views, mediator finality |
| `debug_v1` | **Diagnostics** | Runtime inspection, connectivity testing, error handling |
| `llm_chat_v1` | **Operator Interface** | Direct LLM chat within Cryftee for operator assistance |
| `redeemable_codes_v1` | **Distribution** | TEE-secured gift codes, validator onboarding (US Patent App 20250139608) |
| `aim_v1` | **Agent Identity** | On-chain agent registry, tokenized identity, memory commitments |

**Note:** AIM and `llm_chat_v1` serve different purposes:
- **`llm_chat_v1`** is a Cryftee module for direct operator chat interface within the runtime
- **AIM (`aim_v1`)** is infrastructure for managing autonomous agent identities and memory
- The `llm_chat_v1` module MAY utilize LLM providers that are themselves AIM-registered agents

**Cryftee Requirement by Node Type:**

| Node Type | Consensus? | Rewards? | Cryftee Required? |
|:----------|:-----------|:---------|:------------------|
| Full Validator | Yes | Yes | **Required** |
| Light Validator | Yes (light) | Yes (partial) | **Required** |
| RPC Node | No | No | Not required |
| Archive Node | No | No | Not required |
| Explorer/Indexer | No | No | Optional |

