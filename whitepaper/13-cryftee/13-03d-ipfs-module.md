### 13.3.4 IPFS Module (`ipfs_v1`)

The IPFS module embeds a standalone content-addressed storage node within Cryftee's runtime, combining standard IPFS operations with blockchain-based storage incentives. No external IPFS daemon is required.

**Version:** 1.1.0  
**Category:** Storage  
**Status:** Core Module (required for full network capability)

---

#### Overview

| Property | Value |
|:---------|:------|
| Module ID | `ipfs_v1` |
| Version | 1.1.0 |
| Required for Validators | Yes |
| Modes | Full node (default), Light client |
| External Dependencies | None (standalone embedded node) |

**Purpose:**
- Standalone embedded IPFS node (no external daemon required)
- Content availability attestations with storage challenge verification
- Blockchain-integrated reward system for incentivized pinning
- Code Vault access for contract verification
- Integration with CGS for content-addressed privacy payloads

#### 13.3.4.2 Capabilities

**Standard IPFS Operations:**

| Function | Description |
|:---------|:------------|
| `add` | Add content to the local IPFS node |
| `cat` | Retrieve content by CID |
| `get` | Download content to local filesystem |
| `pin` | Pin content for persistent storage |
| `unpin` | Remove pin from content |
| `ipns_publish` | Publish an IPNS name pointing to content |

**DHT Operations:**

| Function | Description |
|:---------|:------------|
| `peer_connect` | Connect to specific IPFS peers |
| `dht_findpeer` | Locate a peer in the DHT |
| `dht_findprovs` | Find providers for a CID |

**Validator Reward Operations:**

| Function | Description |
|:---------|:------------|
| `validator_stats` | Get validator pinning statistics (pins, rewards, challenges) |
| `incentivized_list` | List all content with active incentives |
| `storage_challenge` | Respond to a storage challenge with proof |
| `claim_rewards` | Claim accumulated pinning rewards |

#### 13.3.4.3 IPFS as a Cryftee Module

IPFS runs inside Cryftee's module sandbox rather than as a separate service. This provides:

- **Unified operational model:** IPFS configuration is managed via Cryftee's module manifest
- **Signature verification:** IPFS module binaries are signed and verified before load
- **Modular upgrades:** IPFS can be updated via module releases without changing CryftGo
- **Integration with other modules:** CGS and governance modules can directly access IPFS for content storage and retrieval
- **No external dependencies:** Standalone embedded node eliminates daemon management

#### 13.3.4.4 Node Modes

Validators configure IPFS mode via Cryftee module settings:

**Full Node Mode (Default):**
- Stores and serves content
- Participates in DHT routing
- Eligible for pinning rewards
- Responds to storage challenges
- Higher storage and bandwidth requirements

**Light Client Mode:**
- Retrieves content on demand
- Minimal local storage
- Relies on full nodes for content discovery
- Suitable for light validators
- Not eligible for pinning rewards

**Configuration:**
```text
CRYFTTEE_IPFS_MODE=full|light
CRYFTTEE_IPFS_STORAGE_PATH=/data/ipfs
CRYFTTEE_IPFS_STORAGE_LIMIT=100GB
CRYFTTEE_IPFS_SWARM_PORT=4001
```

#### 13.3.4.5 Incentivized Pinning Reward System

The IPFS module integrates with the Cryft blockchain for storage incentives:

**How It Works:**
1. Content creators deposit CRYFT tokens to incentivize their content
2. Validators pin incentivized content and respond to storage challenges
3. Proofs are verified on-chain and rewards distributed automatically

**Reward Tiers:**

| Tier | Multiplier | Use Case |
|:-----|:-----------|:---------|
| **Basic** | 1x | Standard content, low priority |
| **Standard** | 2x | Regular application data |
| **Priority** | 5x | Important contracts, high-availability content |
| **Critical** | 10x | System-critical data, consensus artifacts |

**Storage Challenges:**

To prevent fake pinning claims, the network issues random storage challenges:

```text
StorageChallenge {
  cid:           string      // content to prove
  chunk_index:   uint64      // specific chunk to sample
  nonce:         bytes32     // challenge randomness
  deadline:      uint64      // block height deadline
}

ChallengeResponse {
  challenge_id:  bytes32     // reference to challenge
  chunk_hash:    bytes32     // hash of requested chunk
  merkle_proof:  bytes[]     // proof of chunk in content
  signature:     bytes       // validator signature
}
```

**Validator Statistics:**

The module tracks per-validator metrics:
- Total pins maintained
- Rewards earned (lifetime and pending)
- Challenges received and passed
- Uptime and availability score

#### 13.3.4.6 Content Availability Attestations

Validators generate signed attestations proving content availability:

```text
AvailabilityAttestation {
  cid:          string       // IPFS content identifier
  validator_id: bytes32      // validator's node ID
  timestamp:    uint64       // attestation time
  block_height: uint64       // reference block for timing
  sample_hash:  bytes32      // hash of sampled content chunk
  signature:    bytes        // BLS signature over attestation
}
```

Attestations are:
- Submitted to on-chain pinning contracts
- Aggregated for quorum verification
- Used to calculate pinning rewards
- Evidence for storage challenge responses

#### 13.3.4.7 Code Vault Integration

The IPFS module supports Code Vault lazy mirroring:

1. Contract bytecode is uploaded to IPFS with a deterministic CID
2. Validators pin contract code based on registry entries
3. During contract deployment, CryftGo fetches bytecode via Cryftee's IPFS module
4. Bytecode hash is verified against the on-chain registry

This enables:
- Lazy loading of contract code (reduced chain bloat)
- Verified contract source availability
- Cross-region contract mirroring

#### 13.3.4.8 Pinning Provider Operations

Pin providers operate through the IPFS module:

1. Register as pin provider with stake bond
2. Accept pin jobs from the on-chain registry
3. Maintain content availability
4. Respond to storage challenges
5. Generate periodic attestations
6. Receive tiered rewards based on verified availability

See Section 11 (Asset Rewards & Monetary) for detailed pinning reward mechanics.

