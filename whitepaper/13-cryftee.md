
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
  - Mirror Chain: UTXO validation assistance, high-throughput parallel processing, GBL management support
  - EVM Chain: Smart contract execution support, cross-chain messaging coordination
  - All chains: CGS hosting for privacy-aware transaction propagation

- **Subnets/Regions:** Each subnet validator runs Cryftee for:
  - CGS domain participation (privacy pools, intent routing)
  - IPFS pinning and content availability attestations
  - Local balance tracking synchronization with Mirror Chain GBL (if opted into federation)
  - Checkpoint submission to Primary Network

**Consensus validates Cryftee is operating as expected:**

Cryftee performs off-chain computation (parallel validation, IPFS availability checks, CGS routing), but **consensus verifies the results**:

1. Cryftee modules compute outputs (e.g., "these IPFS CIDs are available," "this cross-region transfer is valid")
2. Modules produce signed attestations or proofs
3. CryftGo validators verify attestations on-chain (signature checks, quorum requirements, slashing conditions)
4. Only verified outputs are committed to the blockchain

This achieves **high parallel throughput** (Cryftee does the heavy lifting off-chain) while maintaining **consensus security** (CryftGo validates all results on-chain).

**GBL and Cryftee: opt-in federation without bridges**

The Global Balance Ledger (GBL) on Mirror Chain can be accessed by:
- **Subnets opting into GBL** - subnets query Mirror Chain's GBL via atomic cross-chain messaging or precompiles; no custom bridge contracts required
- **EVM Chain contracts** - query Mirror GBL via precompiles or atomic messaging for federation-wide balance views
- **Cross-region transfers** - processed through Mirror Chain's UTXO model with checkpoint verification at each step

This provides a **unified, robust approach to cross-chain balance tracking** with Mirror Chain as the authoritative ledger.
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

**Mandatory startup requirement for validators:** CryftGo MUST fail startup if Cryftee is not running or if required modules (`bls_tls_signer_v1`, `ipfs_v1` for validators) fail to load or attest. This is enforced via startup checks and runtime attestation verification. Non-validator nodes (RPC, archive) may start without Cryftee.

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

**Web3Signer:**```text
WEB3SIGNER_API_URL=http://localhost:9000
WEB3SIGNER_TLS_CERT=/path/to/web3signer.crt
```

### 13.8 Cryftee requirement & node stack

**Cryftee is mandatory ONLY for validators participating in consensus or seeking to earn rewards.**

CryftNet supports multiple node types with different operational requirements. Cryftee's off-chain utilities (BLS/TLS signing, checkpoint submission, IPFS/CGS operations, runtime attestation) are consensus-critical and reward-critical, but they are **not required** for nodes that merely serve queries or archive historical state.

#### 13.8.1 Node types & Cryftee requirement summary

| Node Type              | Participates in Consensus? | Earns Rewards? | Runs Cryftee? | Reason / Dependencies                                                                 |
|------------------------|----------------------------|----------------|---------------|---------------------------------------------------------------------------------------|
| **Full Validator**     | Yes                        | Yes            | **Required**  | Needs Cryftee for BLS/TLS signing, checkpoint submission, Code Vault/IPFS fetches, bundle validation support, attestation to peers |
| **Light Validator**    | Yes (light-vote path)      | Yes (partial)  | **Required**  | Still needs Cryftee for staking ops, attestation, and some off-chain verification (e.g., GBL queries) |
| **RPC Node**           | No                         | No             | **Not required** | Only serves JSON-RPC queries (eth_getBlockByNumber, etc.). Can rely on trusted full nodes or validators for data. No signing, no bundle validation, no checkpoint submission |
| **Archive Node**       | No                         | No             | **Not required** | Stores historical state for queries. Can sync from validators without Cryftee. No consensus participation or reward eligibility |
| **Explorer / Indexer** | No                         | No             | **Optional**  | May benefit from Cryftee's IPFS module for fetching pinned content, but not required |

#### 13.8.2 Why Cryftee is required for consensus participants

Cryftee's main responsibilities are **off-chain utilities that are consensus-critical or reward-critical**:

- **BLS/TLS staking key operations** (`bls_tls_signer_v1`): Validators must sign block proposals, votes, and checkpoint submissions. These cryptographic operations are performed by Cryftee modules and verified by CryftGo.
- **IPFS node management** (`ipfs_v1`): Code Vault lazy mirroring, bundle verification, and content availability attestations require IPFS operations. Validators fetch and pin critical content to maintain consensus integrity.
- **Checkpoint production & signing**: Regions submit checkpoints to the Primary Network for cross-region verification. Cryftee produces these checkpoints and signs them for on-chain acceptance.
- **Runtime attestation** (`/v1/runtime/attestation`): Peers verify that a validator is running the correct module set with valid signatures. This prevents malicious or outdated code from participating in consensus.
- **CGS domain participation** (`private_sync_v1`): Privacy-aware transaction propagation and slot commitment require CGS routing, key rotation, and mediator confirmation logic.

#### 13.8.3 Non-consensus nodes: RPC, archive, and indexers

RPC and archive nodes **do not**:
- Propose or vote on bundles
- Sign checkpoints
- Participate in validator committees
- Earn block rewards or staking rewards
- Need to prove module integrity to peers

These nodes can safely run **just CryftGo** (the consensus client) in non-validator mode and connect to trusted validators for syncing and serving queries. They do not require Cryftee unless the operator wishes to leverage optional IPFS functionality for convenient access to pinned content.

**Recommended configuration for non-consensus nodes:**
```bash
# RPC node (serves JSON-RPC queries only)
cryftgo --rpc-only=true --staking-enabled=false --consensus-enabled=false

# Archive node (stores historical state for queries)
cryftgo --archive=true --staking-enabled=false --consensus-enabled=false
```

These nodes may optionally run Cryftee modules (e.g., `ipfs_v1` for convenient access to pinned content or explorer features) but are not obligated to do so.

#### 13.8.4 Practical implications for CryftGo implementation

When CryftGo starts, it determines whether Cryftee is required based on operational mode:

**Startup logic** (`cmd/cryftgo/main.go` or `node/node.go`):
- If `--staking-enabled=true` or `--validator-mode=true` -> **require** Cryftee running + valid attestation
- If `--rpc-only=true` or `--archive=true` -> allow startup without Cryftee

**Recommended flags:**
```bash
--require-cryftee-for-consensus    # default true; enforces Cryftee for validators
--cryftee-path                     # path to Cryftee binary for auto-launch
--cryftee-required-modules         # comma-separated list (e.g., bls_tls_signer_v1,ipfs_v1)
--cryftee-attestation-required     # default true for validators; verify runtime attestation
```

**Benefits of this approach:**
- **No unnecessary overhead** for public RPC providers or archive operators
- **Clear security boundary**: validators are locked down with mandatory Cryftee modules and attestation
- **Operational flexibility**: node operators can choose their configuration based on their role in the network

#### 13.8.5 Module selection for validators

Full validators should run the following **minimum module set**:

- `bls_tls_signer_v1`: Required for staking operations and checkpoint signing
- `ipfs_v1`: Required for Code Vault access and content availability attestations
- `private_sync_v1`: Recommended for CGS domain participation (opt-in for privacy features)

Light validators may run a subset (e.g., `bls_tls_signer_v1` only) if they delegate heavy computation to full validators.

**Module configuration in manifest.json:**
```json
{
  "modules": [
    {
      "id": "bls_tls_signer_v1",
      "version": "1.2.0",
      "required": true,
      "hash": "sha256:abc123...",
      "signature": "ed25519:def456..."
    },
    {
      "id": "ipfs_v1",
      "version": "2.0.0",
      "required": true,
      "hash": "sha256:789abc...",
      "signature": "ed25519:012def..."
    },
    {
      "id": "private_sync_v1",
      "version": "1.0.0",
      "required": false,
      "hash": "sha256:345678...",
      "signature": "ed25519:901234..."
    }
  ]
}
```

This modular approach ensures that **consensus participants run Cryftee with verified modules**, while **non-consensus nodes remain lightweight and efficient** without unnecessary overhead.

---