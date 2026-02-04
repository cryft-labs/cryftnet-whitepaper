### 13.3 Core Modules Overview

This section describes the foundational modules included in Cryftee's initial release (v0.4.x runtime). All modules follow the **Power of Ten** safety rules: static bounds declared at module top, no unsafe code, proper error handling (no panics), self-contained limits, and comprehensive input validation.

**All seven modules below are considered CORE MODULES** required for full compatibility with network capabilities. Operators MUST enable all core modules to participate in the complete feature set of CryftNet.

---

#### Module Summary

| Module | Version | Category | Purpose |
|:-------|:--------|:---------|:--------|
| `bls_tls_signer_v1` | 1.2.0 | Staking | BLS + TLS key operations, checkpoint signing, multi-device support |
| `debug_v1` | 1.0.0 | Diagnostics | Runtime inspection, connectivity testing, error handling |
| `llm_chat_v1` | 2.0.0 | Operator Interface | Direct LLM chat within Cryftee for operator assistance |
| `ipfs_v1` | 1.1.0 | Storage | Content-addressed storage, tiered pin rewards, storage challenges |
| `private_sync_v1` | 1.0.0 | Privacy | Canton-style CGS, encrypted views, mediator finality |
| `redeemable_codes_v1` | 1.0.0 | Distribution | TEE-secured gift codes, validator onboarding |
| `aim_v1` | 1.0.0 | Agent Identity | On-chain agent registry, tokenized identity, memory commitments |

---

#### Individual Module Specifications

Each core module has its own detailed specification:

- **Section 13.3.1:** [BLS/TLS Signer Module](13-03a-bls-tls-module.md) - Staking cryptography, multi-device, Web3Signer
- **Section 13.3.2:** [Debug Module](13-03b-debug-module.md) - Diagnostics and runtime inspection
- **Section 13.3.3:** [LLM Chat Module](13-03c-llm-chat-module.md) - Operator assistance interface
- **Section 13.3.4:** [IPFS Module](13-03d-ipfs-module.md) - Content-addressed storage with pin rewards
- **Section 13.3.5:** [CGS Module (Private Sync)](13-03e-cgs-module.md) - Canton-style confidential transactions
- **Section 13.3.6:** [Redeemable Codes](13-03f-redeemable-codes.md) - TEE-secured gift codes
- **Section 13.3.7:** [Agent Identity & Memory (AIM)](13-03g-aim.md) - Tokenized agent identity and memory

---

#### Power of Ten Compliance

All modules MUST adhere to these safety rules:

1. **Static bounds:** All resource limits declared at module top
2. **No unsafe code:** Pure safe Rust/WASM only
3. **No panics:** Proper error handling with Result types
4. **Self-contained limits:** Each module manages its own resource constraints
5. **Input validation:** Comprehensive validation before processing
