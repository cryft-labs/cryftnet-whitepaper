### 13.4 Operational Integration

This section describes how Cryftee integrates with CryftGo and the requirements for different node types.

#### 13.4.1 CryftGo Launches Cryftee

**CryftGo is the blockchain interface; Cryftee is the modular utility layer.**

CryftGo (the consensus client) launches Cryftee as a child process and configures it via environment variables. CryftGo can verify the Cryftee binary hash before launch and optionally require attestation for sensitive operations.

**Mandatory startup requirement for validators:** CryftGo MUST fail startup if Cryftee is not running or if required modules (`bls_tls_signer_v1`, `ipfs_v1` for validators) fail to load or attest. This is enforced via startup checks and runtime attestation verification. Non-validator nodes (RPC, archive) may start without Cryftee.

**Responsibility Separation:**

| CryftGo | Cryftee |
|:--------|:--------|
| Consensus participation (block proposal, voting, finalization) | Off-chain computation (parallel validation, IPFS operations, CGS routing) |
| On-chain state validation and commitment | Module execution (WASM sandboxing, API exposure) |
| Verification of Cryftee attestations and proofs | Producing signed attestations for CryftGo to verify |
| Network communication with other validators | Heavy lifting that doesn't need to be in consensus kernel |

This separation allows **modular and targeted implementations**: validators can choose which modules to run, and upgrades happen independently.

#### 13.6.2 Node Types and Cryftee Requirements

**Cryftee is mandatory ONLY for validators participating in consensus or seeking to earn rewards.**

| Node Type | Participates in Consensus? | Earns Rewards? | Runs Cryftee? | Reason / Dependencies |
|:----------|:---------------------------|:---------------|:--------------|:---------------------|
| **Full Validator** | Yes | Yes | **Required** | Needs Cryftee for BLS/TLS signing, checkpoint submission, Code Vault/IPFS fetches, bundle validation support, attestation to peers |
| **Light Validator** | Yes (light-vote path) | Yes (partial) | **Required** | Still needs Cryftee for staking ops, attestation, and some off-chain verification (e.g., GBL queries) |
| **RPC Node** | No | No | **Not required** | Only serves JSON-RPC queries. Can rely on trusted full nodes for data. No signing, no bundle validation, no checkpoint submission |
| **Archive Node** | No | No | **Not required** | Stores historical state for queries. Can sync from validators without Cryftee. No consensus participation or reward eligibility |
| **Explorer / Indexer** | No | No | **Optional** | May benefit from Cryftee's IPFS module for fetching pinned content, but not required |

#### 13.6.3 Why Cryftee is Required for Consensus Participants

Cryftee's main responsibilities are **off-chain utilities that are consensus-critical or reward-critical**:

- **BLS/TLS staking key operations** (`bls_tls_signer_v1`): Validators must sign block proposals, votes, and checkpoint submissions. These cryptographic operations are performed by Cryftee modules and verified by CryftGo.

- **IPFS node management** (`ipfs_v1`): Code Vault lazy mirroring, bundle verification, and content availability attestations require IPFS operations. Validators fetch and pin critical content to maintain consensus integrity.

- **Checkpoint production & signing**: Regions submit checkpoints to the Primary Network for cross-region verification. Cryftee produces these checkpoints and signs them for on-chain acceptance.

- **Runtime attestation** (`/v1/runtime/attestation`): Peers verify that a validator is running the correct module set with valid signatures. This prevents malicious or outdated code from participating in consensus.

- **CGS domain participation** (`private_sync_v1`): Privacy-aware transaction propagation and slot commitment require CGS routing, key rotation, and mediator confirmation logic.

#### 13.6.4 Non-Consensus Nodes

RPC and archive nodes **do not**:
- Propose or vote on bundles
- Sign checkpoints
- Participate in validator committees
- Earn block rewards or staking rewards
- Need to prove module integrity to peers

These nodes can safely run **just CryftGo** in non-validator mode and connect to trusted validators for syncing and serving queries.

**Recommended configuration for non-consensus nodes:**
```bash
# RPC node (serves JSON-RPC queries only)
cryftgo --rpc-only=true --staking-enabled=false --consensus-enabled=false

# Archive node (stores historical state for queries)
cryftgo --archive=true --staking-enabled=false --consensus-enabled=false
```

These nodes may optionally run Cryftee modules (e.g., `ipfs_v1` for convenient access to pinned content) but are not obligated to do so.

#### 13.6.5 CryftGo Startup Logic

When CryftGo starts, it determines whether Cryftee is required based on operational mode:

**Startup logic:**
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

#### 13.6.6 Module Selection for Validators

Full validators should run the following **minimum module set**:

- `bls_tls_signer_v1`: Required for staking operations and checkpoint signing
- `ipfs_v1`: Required for Code Vault access and content availability attestations
- `private_sync_v1`: Recommended for CGS domain participation (opt-in for privacy features)

Light validators may run a subset (e.g., `bls_tls_signer_v1` only) if they delegate heavy computation to full validators.

