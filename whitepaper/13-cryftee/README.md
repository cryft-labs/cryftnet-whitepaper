## 13. Cryftee: Signed WASM Module Runtime for Chain Utilities

Cryftee is a Rust-based TEE-style sidecar runtime designed to integrate with CryftGo and Web3Signer. It is deliberately stateless: it does not store long-term secrets on disk and instead relies on external key managers (Web3Signer, Vault) or ephemeral key material. Cryftee loads signed WASM modules from a manifest and exposes a versioned API over UDS or HTTPS. It also ships with a kiosk-style web UI for operators on port 3232.

This section is split into multiple files for easier navigation:

- [13.1 Architecture Overview](13-01-architecture.md) - CryftGo vs Cryftee separation, design rationale, federation role
- [13.2 Runtime Properties](13-02-runtime.md) - Module loading, API surface, trust model
- [13.3 Core Modules](13-03-core-modules.md) - BLS/TLS signer, debug, LLM chat
- [13.4 IPFS Module](13-04-ipfs-module.md) - Embedded IPFS node with validator pin rewards
- [13.5 CGS Module (Private Sync)](13-05-cgs-module.md) - Canton-style confidential multi-party transactions
- [13.6 Operational Integration](13-06-operations.md) - Node types, Cryftee requirements, configuration
- [13.7 Agent Identity & Memory (AIM)](13-07-aim.md) - Tokenized agent identity, registry, memory commitments
- [13.8 Redeemable Codes](13-08-redeemable-codes.md) - On-chain gift codes with TEE-secured storage

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

**Module Categories:**

| Category | Modules | Purpose |
|:---------|:--------|:--------|
| **Staking** | `bls_tls_signer_v1` | BLS/TLS key operations, checkpoint signing, multi-device support |
| **Storage** | `ipfs_v1` | Content-addressed storage, tiered pin rewards, storage challenges |
| **Privacy** | `private_sync_v1` | Canton-style CGS, encrypted views, mediator finality |
| **Utility** | `debug_v1`, `llm_chat_v1` | Diagnostics, multi-provider LLM assistance |
| **Distribution** | `redeemable_codes_v1` | TEE-secured gift codes, validator onboarding (US Patent App 20250139608) |
| **Agents** | `agent_registry_v1`, `agent_memory_v1`, `agent_session_v1` | Agent identity, memory commitments, session management |

**Cryftee Requirement by Node Type:**

| Node Type | Consensus? | Rewards? | Cryftee Required? |
|:----------|:-----------|:---------|:------------------|
| Full Validator | Yes | Yes | **Required** |
| Light Validator | Yes (light) | Yes (partial) | **Required** |
| RPC Node | No | No | Not required |
| Archive Node | No | No | Not required |
| Explorer/Indexer | No | No | Optional |

