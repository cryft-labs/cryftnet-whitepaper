### 13.5 CGS Module: Private Sync (`private_sync_v1`)

The CGS (Cryft Global Synchronizer) module implements Canton Network-inspired confidential multi-party transaction synchronization within Cryftee's runtime. It enables atomic multi-party transactions with selective disclosure while maintaining TEE-guaranteed ordering.

#### 13.5.1 Overview

| Property | Value |
|:---------|:------|
| Module ID | `private_sync_v1` |
| Version | 1.0.0 |
| Required for Validators | Recommended (opt-in for privacy features) |
| Inspiration | Canton Network synchronization protocol |
| Purpose | Confidential multi-party transaction execution |

**Purpose:**
- Canton-style synchronization protocol for private smart contract execution
- Sub-transaction privacy with encrypted party views
- Commitment-based confirmation without full data exposure
- Domain-isolated synchronization contexts
- TEE-secured mediator for conflict detection and finality

#### 13.5.2 CGS Architecture within Cryftee

CGS is embedded in Cryftee in two layers:

1. **CGS Core Service:** Manages routing, pools, and key rotation schedules within the Cryftee runtime
2. **Domain Modules:** Implement domain-specific logic (starting with `private_sync_v1`)

This mirrors Canton-style constructs while remaining pluggable. Embedding CGS in Cryftee keeps the synchronizer close to the validator, reducing latency and enabling tight integration with:
- Mempool selection
- Smart Slot scheduling (via slot commitments)
- Intent routing

#### 13.5.3 Key Concepts

**Sub-transaction Privacy:**
Each party receives only an encrypted "view" of the portions relevant to them. No party sees the complete transaction unless explicitly authorized.

**Commitment Scheme:**
Transactions use cryptographic commitments - parties confirm participation without seeing the full transaction data. This enables atomic execution across mutually distrusting parties.

**Domains:**
Isolated synchronization contexts with independent transaction ordering. Each domain maintains its own participant set, key schedule, and confirmation rules.

**Mediator Role:**
TEE-secured mediators provide conflict detection and finality guarantees. Mediators see commitments but not transaction content, ensuring privacy while preventing double-spends.

#### 13.5.4 Capabilities

| Function | Description |
|:---------|:------------|
| `domain_create` | Create a new privacy domain with parameters |
| `party_register` | Register a party in a domain with viewing keys |
| `tx_submit` | Submit a transaction (commitment + encrypted views) |
| `tx_confirm` | Confirm participation based on party's view |
| `view_request` | Request decrypted view for authorized party |
| `contract_create` | Create a private contract within a domain |
| `commitment_create` | Generate cryptographic commitment for transaction |
| `sync_request` | Request synchronization state for a domain |
| `mediator_submit` | Submit transaction to mediator for finality |

#### 13.5.5 Domain Model

Privacy domains define the scope and rules for private transactions:

```text
PrivacyDomain {
  domain_id:       bytes32     // unique domain identifier
  domain_type:     enum        // POOL, BILATERAL, MULTI_PARTY
  participants:    address[]   // registered parties
  viewing_keys:    bytes[]     // encrypted viewing keys per party
  mediators:       address[]   // TEE-secured mediator set
  key_schedule:    KeyRotation // rotation parameters
  slot_policy:     SlotPolicy  // Smart Slot integration rules
  ordering_mode:   enum        // FIFO, PRIORITY, CUSTOM
}
```

#### 13.5.6 Canton-Style Transaction Flow

The synchronization protocol follows Canton's multi-party confirmation model:

**Step 1: Transaction Submission**
```text
Party A submits transaction:
  - commitment: hash(tx_content || salt)
  - encrypted_views: { Party_B: enc(view_B), Party_C: enc(view_C) }
  - slot_claims: commitment to accessed state
```

**Step 2: View Distribution**
```text
Synchronizer routes views to relevant parties WITHOUT decrypting:
  - Party B receives: enc(view_B)
  - Party C receives: enc(view_C)
  - Mediator receives: commitment only (no content)
```

**Step 3: Party Confirmation**
```text
Each party confirms based on their view alone:
  - Decrypt their view using party key
  - Validate view matches expected state changes
  - Sign confirmation: sign(commitment || view_hash || party_id)
```

**Step 4: Mediator Finalization**
```text
When all confirmations received:
  - Mediator verifies all signatures
  - Checks for conflicts (double-spends, ordering violations)
  - Produces finality certificate
  - Transaction commits atomically
```

**Key Property:** No single party (including the mediator) sees the complete transaction. Atomicity is achieved through cryptographic commitments, not data sharing.

#### 13.5.7 Integration with Smart Slots

CGS integrates with Smart Slot scheduling via slot commitments:

```text
SlotCommitment {
  tx_hash:        bytes32     // hash of encrypted transaction
  claimed_slots:  SlotClaim[] // slots this tx will access
  commitment:     bytes32     // hiding commitment to slot claims
  reveal_block:   uint64      // block at which commitment opens
}
```

This allows:
- Parallel scheduling without revealing transaction details
- Privacy-preserving mempool ordering
- Deterministic execution across validators

#### 13.5.8 Key Rotation

Domains support scheduled key rotation for forward secrecy:

```text
KeyRotation {
  interval_blocks: uint64     // blocks between rotations
  current_epoch:   uint64     // current key epoch
  pending_keys:    bytes[]    // next epoch keys (encrypted)
  rotation_delay:  uint64     // blocks before new keys active
}
```

Key rotation:
- Limits exposure from key compromise
- Enables participant addition/removal
- Maintains viewing access to historical transactions

#### 13.5.9 Mediator Flows

For high-value or regulated transactions, domains may require mediator confirmation:

```text
MediatorConfirmation {
  tx_hash:        bytes32     // transaction being confirmed
  mediator:       address     // confirming mediator (TEE-secured)
  decision:       enum        // APPROVE, REJECT, DEFER
  conflict_info:  bytes       // conflict details if rejected
  finality_cert:  bytes       // finality certificate if approved
  signature:      bytes       // mediator signature
}
```

**Mediator Guarantees:**
- TEE-secured execution prevents mediator from seeing transaction content
- Ordering is deterministic and verifiable
- Conflicts are detected without exposing competing transaction details
- Finality certificates are cryptographically verifiable

#### 13.5.10 Configuration

```text
CRYFTTEE_CGS_ENABLED=true
CRYFTTEE_CGS_DEFAULT_POOL=main_privacy_pool
CRYFTTEE_CGS_KEY_ROTATION_INTERVAL=10000
CRYFTTEE_CGS_MEDIATOR_TIMEOUT=300
CRYFTTEE_CGS_CONFIRMATION_QUORUM=all
```

