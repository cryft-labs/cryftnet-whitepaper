
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

Cryftee is a Rust-based TEE-style sidecar runtime designed to integrate with CryftGo and
Web3Signer. It is deliberately stateless: it does not store long-term secrets on disk and instead relies
on external key managers (Web3Signer, Vault) or ephemeral key material. Cryftee loads signed
WASM modules from a manifest and exposes a versioned API over UDS or HTTPS. It also ships with
a kiosk-style web UI for operators on port 3232.

**Architecture clarity: CryftGo vs. Cryftee**

- **CryftGo** is the consensus client (blockchain interface) - a fork of AvalancheGo that handles on-chain consensus, block validation, and state transitions. CryftGo is the "consensus kernel" that must remain lean and proven.
- **Cryftee** is the off-chain computation and utility layer - a modular sidecar that runs WASM modules for auxiliary features like CGS, IPFS, staking operations, and specialized validation logic.
- **All extensions are modules** within Cryftee. IPFS, CGS, pin provider logic, governance helpers, and future features are all WASM modules that load into Cryftee's runtime.

**Why separate CryftGo and Cryftee?**

1. **Consensus safety:** Novel features (CGS, Smart Slots parallel scheduling, IPFS) do not touch the consensus kernel. CryftGo remains a minimal, auditable, proven codebase.
2. **Modular upgrades:** Modules can be upgraded independently via signed releases without requiring consensus client upgrades or chain-wide coordination.
3. **Off-chain parallelism:** Cryftee can perform parallel validation, content availability checks, and computation-heavy tasks off-chain, then submit proofs/attestations to CryftGo for on-chain recording.
4. **Targeted deployments:** Different validators can run different module sets based on their operational needs (e.g., IPFS-only validators, CGS relays, pin providers).

**Cryftee's role in the federation:**

- **Primary Network (Federal Chain, Mirror Chain, EVM Chain):** All three chains use Cryftee modules for operations:
  - Federal Chain: Validator eligibility checks, governance vote aggregation, checkpoint acceptance logic
  - Mirror Chain: UTXO validation assistance, high-throughput parallel processing
  - **EVM Chain: Global Balance Ledger (GBL) operations** - GBL balance updates are computed by Cryftee modules and validated via consensus; this allows subnets to "opt into" GBL tracking without requiring custom bridge contracts
  - All chains: CGS hosting for privacy-aware transaction propagation

- **Subnets/Regions:** Each subnet validator runs Cryftee for:
  - CGS domain participation (privacy pools, intent routing)
  - IPFS pinning and content availability attestations
  - Local GBL tracking (if opted into federation mirroring)
  - Checkpoint submission to Primary Network

**Consensus validates Cryftee is operating as expected:**

Cryftee performs off-chain computation (parallel validation, IPFS availability checks, CGS routing), but **consensus verifies the results**:

1. Cryftee modules compute outputs (e.g., "these IPFS CIDs are available," "this cross-region transfer is valid")
2. Modules produce signed attestations or proofs
3. CryftGo validators verify attestations on-chain (signature checks, quorum requirements, slashing conditions)
4. Only verified outputs are committed to the blockchain

This achieves **high parallel throughput** (Cryftee does the heavy lifting off-chain) while maintaining **consensus security** (CryftGo validates all results on-chain).

**GBL and Cryftee: opt-in federation without bridges**

The Global Balance Ledger (GBL) on EVM Chain can be accessed by:
- **Cryftee modules** running on subnet validators - modules compute regional balance updates and submit checkpoint attestations
- **Subnets opting into GBL** - instead of deploying custom bridge contracts, subnets run GBL-aware Cryftee modules that synchronize with EVM Chain's authoritative GBL
- **Cross-region transfers** - Cryftee modules handle the debit-checkpoint-credit flow, with consensus validating each step

This provides a **modular, standardized approach to cross-chain balance tracking** without requiring every subnet to implement custom bridging logic.
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
### 13.3 Embedding CGS and IPFS inside Cryftee as modules

**All auxiliary features are WASM modules loaded by Cryftee runtime:**

| Module | Version | Purpose | Representative capabilities |
|:-------|:--------|:--------|:----------------------------|
| bls_tls_signer_v1 | 1.2.0 | BLS + TLS staking module with Web3Signer integration and module signing | bls_register, bls_sign, bls_verify, tls_register, tls_sign, tls_verify, sign_module, verify_module |
| debug_v1 | 1.0.0 | Diagnostics and runtime inspection | debug_echo, debug_info, debug_panic |
| llm_chat_v1 | 1.0.0 | Operator assistance via LLM interface | llm_chat, llm_stream |
| **ipfs_v1** | 2.0.0 | **Embedded IPFS node management (full/light modes)** - IPFS is a Cryftee module, not a separate service | node_start, ipfs_add, ipfs_pin, ipns_publish, peer_connect |
| redeemable_codes_v1 | 1.0.0 | On-chain redeemable gift code system | code_generate, code_redeem, code_freeze, validator_code_redeem |
| **private_sync_v1** | 1.0.0 | **Cryft-style private transaction synchronizer (CGS domain module)** | domain_create, party_register, tx_submit, view_decrypt, mediator_confirm |

**CGS is embedded in Cryftee in two layers:**

- A CGS core service in the runtime that manages routing, pools, and key rotation schedules.
- A set of modules (starting with private_sync_v1) that implement domain logic: party registration, tx submit/confirm, view requests, and mediator flows.

This mirrors Cryft-style constructs while remaining pluggable. Embedding CGS in Cryftee keeps the synchronizer close to the validator, reducing latency and enabling tight integration with mempool selection and Smart Slot scheduling (via slot commitments).

**IPFS layer is a Cryftee module (ipfs_v1):**

The IPFS node runs inside Cryftee's module sandbox. This provides:
- **Unified operational model:** IPFS configuration is managed via Cryftee's module manifest
- **Signature verification:** IPFS module binaries are signed and verified before load
- **Modular upgrades:** IPFS can be updated via module releases without changing CryftGo
- **Integration with other modules:** CGS and governance modules can directly access IPFS for content storage and retrieval

Validators configure IPFS mode (full node, light client, gateway-only) via Cryftee module settings.
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
### 13.7 Operational integration: CryftGo launches Cryftee

**CryftGo is the blockchain interface; Cryftee is the modular utility layer:**

CryftGo (the consensus client) launches Cryftee as a child process and configures it via environment variables. CryftGo can
verify the Cryftee binary hash before launch and optionally require attestation for sensitive operations.

**CryftGo responsibilities:**
- Consensus participation (block proposal, voting, finalization)
- On-chain state validation and commitment
- Verification of Cryftee attestations and proofs
- Network communication with other validators

**Cryftee responsibilities:**
- Off-chain computation (parallel validation, IPFS operations, CGS routing)
- Module execution (WASM sandboxing, API exposure)
- Producing signed attestations for CryftGo to verify
- Heavy lifting that doesn't need to be in consensus kernel

This separation allows **modular and targeted implementations**: validators can choose which modules to run, and upgrades happen independently. A validator running IPFS pinning doesn't need the same modules as a validator focused on CGS privacy relay.

**Core:**
```text
CRYFTTEE_MODULE_DIR=./modules
CRYFTTEE_MODULES=bls_tls_signer_v1,ipfs_v1,private_sync_v1
CRYFTTEE_API_TRANSPORT=uds
CRYFTTEE_UDS_PATH=/tmp/cryfttee.sock
```

**Web3Signer:**
