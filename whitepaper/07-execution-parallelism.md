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

#### 7.3.6 Deterministic scheduling and conflict rules (pre-lock design)

Validators derive the schedule deterministically from the ordered tx list in the proposed block (proposer-chosen order). The scheduler organizes transactions into lanes by process_id and attempts to acquire READ and WRITE locks on slots. Locks are acquired in sorted slot_id order to avoid deadlocks. Deterministic ordering key: (process_id, keccak256(tx_hash)).

Proposer selects and orders txs; validators verify the schedule matches lock rules. Invalid schedules result in invalid block rejection.

Inputs:
- block transactions T (in proposer-committed order)
- deterministic ordering key: (process_id, keccak256(tx_hash))
1) Partition:
   Legacy = [t in T where t.type == legacy]
   Parallel = group by process_id: L[p] = sorted(t in T where t.process_id==p, key=keccak256(tx_hash))
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

## 9. Cryft Global Synchronizer (CGS): privacy propagation and federation sync

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

**CRITICAL CONSENSUS BOUNDARY:**

CGS is **mempool transport only**. It is NOT consensus-critical. The consensus-critical data (slot_claims) MUST appear in the block in a form every validator can verify without CGS.

**The rule that resolves the contradiction:**

Slot commitments bridge privacy and determinism, but with a clear separation:
- **slot_commitment** is an anti-equivocation/integrity proof and privacy-preserving placeholder BEFORE inclusion
- **revealed slot_claims** are the consensus-critical data used for execution
- **At inclusion time**, validators MUST receive RevealClaims and the block MUST include enough data to verify H(revealed_claims) == slot_commitment
- **Execution uses revealed claims**, not the commitment

**What this means:**
- CGS failing should NOT halt the chain
- CGS degradation means private intents don't propagate well, but consensus continues
- The block contains either full revealed slot_claims OR a deterministic, verifiable equivalent required for execution
- Legacy (non-private) transactions bypass CGS entirely and work normally

**Intent submission (privacy-aware path):**
```text
1) Client computes slot_claims and slot_commitment = H(canonical(slot_claims))
2) Client encrypts tx data to pool key K_pool (threshold encryption key)
3) Client sends IntentEnvelope(process_id, slot_commitment, ciphertext, routing_hint) via CGS
```

**Inclusion (proposer side):**
```text
1) Proposer selects intent by commitment and policy
2) Proposer requests RevealClaims from sender (or authorized party)
3) Proposer verifies H(revealed_claims) == slot_commitment
4) Proposer includes revealed_claims in block (or equivalent verifiable data)
5) Scheduler runs pre-lock acquisition on revealed_claims
6) If acquired, execute tx and include receipt linking to commitment
```

**Block content (consensus-critical):**

**CRITICAL**: On-chain block MUST contain plaintext calldata + revealed_claims (or digest + full claims via IPFS CID if large). **No ciphertext is stored on-chain** for consensus execution. Ciphertext exists only off-chain (mempool/CGS layer).

```text
Block = {
  ...,
  transactions: [
    // Legacy tx (unchanged)
    { type: "legacy", from, to, value, data, nonce, ... },
    
    // Private intent (revealed at inclusion; NO CIPHERTEXT IN BLOCK)
    { 
      type: "cryft_private",
      slot_commitment: 0x1234...,
      revealed_claims: [...],       // MUST be present for execution (plaintext)
      plaintext_calldata: 0x...,    // Decrypted call data for EVM execution
      proof_of_reveal: signature    // Proves sender authorized reveal
      // NO ciphertext field - privacy exists in mempool propagation only
    }
  ]
}
```

**All validators execute using revealed plaintext.** Transactions that cannot be decrypted or lack revealed plaintext are invalid and rejected.

**Privacy model**: CGS provides privacy during mempool propagation (before inclusion). Once a validator includes a tx in a block, the plaintext is revealed to all validators for deterministic execution. Block data is public.

**Verification (every validator, with or without CGS):**
```text
1) For each private tx in block:
   - Verify H(revealed_claims) == slot_commitment
   - Verify proof_of_reveal signature
   - Decrypt ciphertext (if validator has key) OR trust revealed_claims
   - Execute using revealed_claims (deterministic)
2) All validators reach same state root because revealed_claims are deterministic
```

**Privacy guarantees:**
- **Before inclusion:** slot_commitment hides exact access set from public observers
- **After inclusion:** revealed_claims are in the block (privacy ends at execution)
- **Who sees what:**
  - Public observers: see commitment, revealed claims after inclusion
  - Region validators: see revealed claims at inclusion time (must verify execution)
  - Sender/recipient: always know full transaction details
- **Threat model:** CGS provides privacy from casual observers and timing decorrelation, NOT strong anonymity from determined adversaries

### 9.6 Key management for threshold encryption

**CGS key management was previously hand-wavy. Here is the concrete model:**

**Key committee structure:**
- Each privacy pool has a **key committee** (could be region validators or a designated subset)
- Committee size: recommended 7-15 members with t-of-n threshold (e.g., 5-of-7, 11-of-15)
- Committee members run key generation ceremonies using distributed key generation (DKG)

**Key lifecycle:**
```text
Phase 1: Setup
- Committee runs DKG to generate K_pool (threshold encryption key)
- Each member holds a key share; t shares needed to decrypt
- Public key K_pool_pub is published on-chain

Phase 2: Active use (epoch duration: N blocks, e.g., N=10,000)
- Intents encrypted to K_pool_pub
- Decryption requires t-of-n committee members to cooperate
- Committee publishes availability attestation every M blocks

Phase 3: Rotation (every N epochs, e.g., every 100,000 blocks)
- New committee runs DKG for K_pool_new
- Rotation transaction published on-chain:
  - old_key_id, new_key_id, new_key_pub, rotation_height
- After rotation_height, intents use K_pool_new
- Old key remains available for H blocks for dispute resolution

Phase 4: Compromise response (emergency)
- If compromise detected: immediate rotation trigger
- Governance or committee publishes compromise event:
  - compromised_key_id, compromise_height, severity
- Optionally invalidate envelopes in pre-compromise window
- Affected users re-submit with new key
```

**Key rotation triggers:**
- **Scheduled:** Every N epochs (e.g., 100,000 blocks = ~2 weeks at 12s blocks)
- **Committee change:** When validator set changes significantly
- **Compromise detection:** Immediate rotation if key leakage suspected
- **Governance:** Emergency rotation via Main governance

**Key compromise response:**
```text
Compromise event = {
  event_type: "KEY_COMPROMISE",
  pool_id: 42,
  compromised_key_id: 0x1234...,
  compromise_height: 8_240_000,  // best-guess compromise time
  severity: "HIGH" | "MEDIUM" | "LOW",
  response: {
    rotate_immediately: true,
    invalidate_window: [8_230_000, 8_240_112],  // envelopes in this range invalidated
    resubmit_required: true
  },
  governance_approval: signature
}
```

**Explicit privacy goals (what CGS actually provides):**
1. **Hide recipient from public observers until inclusion** (commitment-based routing)
2. **Decorrelate timing** (batching, cover traffic)
3. **Reduce metadata surface** (encrypted payloads, selective disclosure)
4. **Anti-equivocation** (commitment prevents double-spend before reveal)

**Explicit NON-goals (what CGS does NOT provide):**
1. ❌ Strong anonymity from nation-state adversaries
2. ❌ Protection against global network observers (timing correlation still possible)
3. ❌ Protection against key committee collusion (committee sees plaintext)
4. ❌ Hiding transaction amounts or asset types after inclusion

**Leakage metrics (measurable):**
- **Timing correlation:** Measure correlation between IntentEnvelope arrival and block inclusion
- **Metadata surface:** Count of public fields in IntentEnvelope vs. legacy tx
- **Committee privacy:** Probability that t-of-n committee members collude
- **Network-level leakage:** Traffic analysis correlation tests

**Failure modes (explicit):**
- **Key committee offline:** Intents can't be decrypted -> fallback to legacy (non-private) txs
- **Key committee censorship:** Route intents to different region or Main
- **Key compromise:** Emergency rotation, invalidate affected window
- **DKG failure:** Retry with different committee or fallback to simpler setup

### 9.7 Anti-censorship and liveness

CGS uses multi-route gossip and region fallbacks. If Region A appears censored, intents can be
routed to Region B or to Main, then forwarded. Privacy pools should avoid single points of control:
threshold keys are managed by committees with rotation (see Section 9.6). Residual risk remains: any privacy system
can be degraded by global adversaries controlling network paths; CryftNet treats this as measurable
and provides monitoring via Cryftee modules.

### 9.8 Failure modes and residual risk

- Metadata leakage through timing and traffic analysis (mitigate with batching and cover traffic).
- Threshold key compromise (mitigate with rotations, HSM/TEE options, and slashing).
- Denial of service via junk intents (mitigate with fees, rate limits, and capability gating).
- Complexity risk: CGS must not be consensus-critical without extensive validation.
- Committee collusion: t-of-n members collude to decrypt all intents (mitigate with audits, rotation, slashing).
- Network-level attacks: Global observer correlates IntentEnvelope with inclusion (mitigate with cover traffic, batching, decoy intents).

### 9.9 CGS mainnet gating criteria

**CGS remains "non-consensus-critical experimental" until ALL of the following are complete:**

| Deliverable | Purpose | Status |
|:------------|:--------|:-------|
| **Formal threat model** | Document adversary capabilities, attack vectors, privacy guarantees, and explicit non-guarantees | ❌ TODO |
| **Key ceremony specification** | Normative spec for DKG, rotation, compromise response, committee selection | ❌ TODO |
| **Privacy leakage metrics** | Quantitative tests: timing correlation, metadata surface, traffic analysis resistance | ❌ TODO |
| **Red-team style tests** | External adversarial testing: traffic analysis + denial of service attacks | ❌ TODO |
| **Crypto + protocol audit** | External security review of threshold encryption, commitment scheme, and CGS protocol logic | ❌ TODO |
| **Testnet soak test (>=3 months)** | Real validator incentives, adversarial testing, key rotation under load | ❌ TODO |

**Mainnet deployment strategy:**

**Phase 0 (Current):** CGS design and specification
- Status: Proposal only
- Risk: High (unvalidated)
- Action: Complete formal threat model and key ceremony spec

**Phase 1 (Devnet):** Basic functionality testing
- Threshold encryption with toy parameters
- Key rotation under controlled conditions
- No real economic value at risk

**Phase 2 (Testnet):** Incentivized testing with adversarial scenarios
- Real validator incentives (testnet tokens)
- Red-team attacks: traffic analysis, timing correlation, DoS
- Key compromise drills (deliberate compromise + recovery)
- Leakage metric collection and analysis

**Phase 3 (Audit + Hardening):** External review and fixes
- Independent security audit of crypto + protocol
- Resolve all critical/high findings
- Publish audit report and threat model

**Phase 4 (Mainnet - EXPERIMENTAL):** Limited deployment
- CGS available on Main but marked EXPERIMENTAL
- Clear warnings: "Privacy is best-effort, not guaranteed"
- Monitoring and telemetry required for all CGS participants
- Governance escape hatch: can disable CGS if issues detected

**Phase 5 (Mainnet - PRODUCTION):** Only after all gating criteria met
- Formal threat model published
- Audit complete with no unresolved high/critical issues
- >=3 month testnet soak test with adversarial scenarios
- Leakage metrics below acceptable thresholds
- Key rotation proven under load

**Fallback plan:**
- If CGS validation extends beyond launch window, ship mainnet WITHOUT CGS
- All transactions use legacy (non-private) path
- CGS can be added post-launch via governance upgrade once validated

**Monitoring requirements (Phase 4+):**
- **Key committee health:** Availability, rotation success rate, response time
- **Privacy metrics:** Timing correlation scores, metadata leakage detection
- **Censorship detection:** Intent routing success rate per region
- **Attack detection:** Anomalous traffic patterns, DoS attempts
- **Performance impact:** CGS overhead vs. legacy tx throughput

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
| Hybrid (ZK + quorum) | Either assumption | O(1) each | Proof ready ->' fast; else fallback |

**Recommended approach:** Hybrid verification. Regions produce ZK proofs asynchronously. If a proof is available when the checkpoint reaches Main, use it. Otherwise, fall back to quorum verification. Over time, as ZK prover performance improves, proofs become available faster and become the primary path.

**Benefits for cross-chain settlement:**

- **Trustless bridges:** Assets locked on Region A can be minted on Region B with cryptographic proof of the lock, not just validator attestations.
- **Light client support:** Mobile wallets and browsers can verify cross-chain state without trusting RPC providers--they verify the ZK proof directly.
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
3) Checkpoint to Federal Chain includes aggregated proof
4) Recipient on Region B claims with proof of inclusion + recipient key
5) Region B mints without learning sender identity
```

This enables privacy-preserving cross-chain transfers with cryptographic (not just economic) security.

### 10.6 User mobility and cross-region asset portability

A core UX goal of CryftNet is that users are **never region-locked**. If a user physically moves from the Midwest to the West Coast, they should immediately benefit from low-latency access via their nearest region without losing access to assets or requiring complex migrations.

**Unified account model:**

CryftNet uses a unified address space across the federation. The same Ethereum-style address (derived from the user's private key) is valid on Main and all regions. This means:

- A user's identity is portable--no need to create new accounts when switching regions.
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
1) Wallet probes regional endpoints ->' determines nearest healthy region (R_user)
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
3) User spends on Region B ->' deducted locally, async sync to Main
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
Transfer from Region A ->' Region B:

1) LOCK on Region A:
   - User calls bridge.lock(asset, amount, dest_region=B, recipient)
   - Asset is locked in bridge contract (user cannot spend it)
   - Lock event emitted with unique transfer_id

2) CHECKPOINT to Federal Chain:
   - Region A's next checkpoint includes the lock event in message_root
   - Federal Chain finalizes checkpoint ->' lock is now globally ordered

3) MINT on Region B:
   - User (or relayer) submits claim to Region B with:
     - Merkle proof of lock event inclusion in Region A's checkpoint
     - Main's finalization proof for that checkpoint
   - Region B verifies proofs and mints equivalent asset to recipient
   - Mint is linked to transfer_id (prevents replay)

4) Asset now exists ONLY on Region B

