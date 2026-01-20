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
routed to Region B or to Primary Network (Main), then forwarded. Privacy pools should avoid single points of control:
threshold keys are managed by committees with rotation (see Section 9.6). Residual risk remains: any privacy system
can be degraded by global adversaries controlling network paths; CryftNet treats this as measurable
and provides monitoring via Cryftee modules.

### 9.7a CGS Decryption & Inclusion Liveness

**Who must be online to reveal plaintext for inclusion?**

CGS uses a **t-of-n threshold encryption** model where ANY t members of the key committee can cooperate to decrypt. Decryption liveness does NOT require all n members.

**Decryption participants (per privacy pool):**
- **Key committee members**: t-of-n validators/nodes holding key shares
- **Threshold requirement**: t members must be online and cooperative (e.g., 5-of-7, 7-of-11)
- **Proposer role**: Does NOT require special committee membership; requests decryption from committee

**Liveness guarantee:**
```text
If >= t committee members online and honest:
  -> Decryption succeeds
  -> Private intents can be included

If < t committee members online:
  -> Decryption fails for that privacy pool
  -> Fallback to legacy (non-private) transactions (see below)
```

**What happens if the committee is down? How is fallback triggered?**

**Detection (client-side):**
```text
Client submits private intent to CGS:

1) Client monitors IntentEnvelope propagation (30 seconds)
2) Client queries proposer: "Can you decrypt my intent?"
   - Proposer checks: Can I get t shares from committee?
   - Response: 
     - "DECRYPTABLE" (>= t members responsive)
     - "DEGRADED" (< t members, decryption uncertain)
     - "UNAVAILABLE" (committee offline, decryption impossible)

3) If response == "UNAVAILABLE" OR intent not included after timeout:
   - Client triggers LOCAL FALLBACK (automatic in wallet)
```

**Fallback mechanism (normative):**
```text
Wallet behavior when CGS unavailable:

1) Wallet detects committee down:
   - Query timeout (>30s no decryption confirmation)
   - OR proposer returns "UNAVAILABLE"
   - OR IntentEnvelope not gossiped (CGS plane unreachable)

2) Wallet prompts user:
   "Privacy service unavailable. Submit as standard transaction?"
   - User selects: "Yes, submit public" OR "Cancel, wait for privacy"

3) If user confirms fallback:
   - Wallet converts intent to legacy EVM transaction
   - Same nonce, same calldata (now public)
   - Submits to standard mempool
   - Transaction included normally (no CGS dependency)

4) Nonce management:
   - Intent and fallback tx MUST use same nonce
   - Whichever is included first invalidates the other
   - Prevents double-spend (only one can execute)
```

**Proposer behavior (automatic fallback trigger):**
```text
Proposer building block:

1) Proposer selects IntentEnvelopes for inclusion
2) For each envelope, proposer requests decryption:
   - Broadcast ShareRequest to committee members
   - Collect >= t shares (timeout: 5 seconds)

3) Decryption outcomes:
   
   CASE A: >= t shares received within timeout
     -> Decrypt ciphertext
     -> Verify H(revealed_claims) == slot_commitment
     -> Include transaction with revealed_claims
   
   CASE B: < t shares received (committee degraded)
     -> Mark envelope as "PENDING_RETRY"
     -> Skip this intent (do not include in block)
     -> Client will retry next block or fallback
   
   CASE C: Committee completely offline (0 responses)
     -> Proposer broadcasts "COMMITTEE_DOWN" signal
     -> Clients automatically fallback to legacy txs
     -> Block continues with non-private transactions only

4) Block production never halts due to CGS failure
   - CGS unavailability reduces privacy, not liveness
```

**Does the proposer need committee cooperation every time, or only for some privacy modes?**

**Privacy mode dependency matrix:**

| Transaction Type | Committee Required? | Notes |
|:-----------------|:-------------------|:------|
| **Legacy transaction (public)** | **NO** | Standard EVM tx; no CGS involvement |
| **Parallel execution (no privacy)** | **NO** | Slot claims public; no encryption |
| **CGS private intent (encrypted)** | **YES** | Requires t-of-n committee to decrypt |
| **Selective disclosure (hybrid)** | **PARTIAL** | Some fields encrypted, some public; committee needed only for encrypted fields |

**Implementation detail:**
```text
Private intent submission includes privacy_level flag:

privacy_level = "NONE" | "SELECTIVE" | "FULL"

NONE:
  - No encryption, no committee
  - Standard parallel execution with public slot claims
  - Example: Public DeFi transaction using Smart Slots

SELECTIVE:
  - Encrypt sensitive fields only (e.g., recipient address)
  - Public fields: sender, slot_commitment, process_id
  - Committee decrypts only encrypted portions
  - Reduces committee load vs FULL encryption

FULL:
  - Entire transaction payload encrypted
  - Maximum privacy, maximum committee dependency
  - Highest gas cost (committee incentive fees)
```

**Committee incentive (required for cooperation):**
```text
Private intent fee structure:

base_fee = normal_gas_cost
committee_fee = per_share_fee * t  // Pay for t decryptions

Total fee = base_fee + committee_fee + priority_tip

Distribution:
- base_fee -> proposer (normal)
- committee_fee -> distributed to t committee members who provided shares
- priority_tip -> proposer (normal)

Economic liveness guarantee:
- Committee members earn committee_fee for decryption work
- Higher fees incentivize liveness
- If committee offline, no fee earned (opportunity cost)
```

**What is the censorship-resistance story if the committee colludes?**

**Threat: Committee refuses to decrypt specific intents (censorship).**

**Mitigation layers:**

**Layer 1: Multi-pool routing (immediate fallback)**
```text
Multiple privacy pools exist per region:

pools = [
  {pool_id: 1, committee: [V1, V2, V3, V4, V5], region: A},
  {pool_id: 2, committee: [V6, V7, V8, V9, V10], region: A},
  {pool_id: 3, committee: [V11, V12, V13, V14, V15], region: B}
]

If pool 1 committee censors intent:
  -> Client detects (no decryption after 2 blocks)
  -> Client re-encrypts intent to pool 2 key
  -> Submits to pool 2
  -> Pool 2 committee decrypts and includes

If both pool 1 AND pool 2 censor:
  -> Client routes to pool 3 (different region)
  -> Or routes to Primary Network (Main EVM Chain)
```

**Layer 2: Censorship evidence and slashing**
```text
Client proves censorship:

Evidence = {
  intent_envelope: {
    slot_commitment: 0x1234...,
    ciphertext: 0x...,
    fee: 1000 CRYFT,  // High fee paid
    timestamp: T
  },
  
  committee_responses: [
    // All members responsive, but refused to decrypt
    {member: V1, response: "ACTIVE", but share_provided: false},
    {member: V2, response: "ACTIVE", but share_provided: false},
    ...
  ],
  
  proof_of_validity: {
    // Client proves intent was valid (correct format, sufficient fee)
    signature: client_sig,
    revealed_plaintext: 0x...,  // Client reveals plaintext as proof
    verified: H(revealed_plaintext) == slot_commitment
  }
}

If verified by governance or Primary Network validators:
  -> Committee members slashed (2% stake each)
  -> Censored transaction included retroactively
  -> User compensated from slashed funds
```

**Layer 3: Emergency plaintext submission (ultimate escape hatch)**
```text
If ALL privacy pools refuse to decrypt:

Client can submit "EMERGENCY_PLAINTEXT" transaction:

tx = {
  type: "EMERGENCY_PLAINTEXT",
  intent_envelope_hash: 0x1234...,  // Reference to censored intent
  revealed_plaintext: 0x...,        // Full plaintext calldata
  revealed_claims: [...],           // Full slot claims
  proof_of_censorship: {
    attempts: [
      {pool: 1, timestamp: T1, result: "REFUSED"},
      {pool: 2, timestamp: T2, result: "REFUSED"},
      {pool: 3, timestamp: T3, result: "REFUSED"}
    ],
    committee_evidence: signatures  // Proof committee was online but refused
  }
}

Validation:
  -> If proof_of_censorship valid, transaction included as public
  -> User pays normal gas (no privacy)
  -> Committees may be slashed for proven censorship
  -> Transaction executes normally (no privacy, but censorship-resistant)
```

**Layer 4: Committee accountability via reputation**
```text
On-chain reputation tracking:

committee_metrics = {
  decryption_success_rate: 99.5%,   // How often committee decrypts
  censorship_reports: 0,            // Proven censorship events
  average_response_time: 2.3s,      // Decryption latency
  uptime: 99.9%                     // Availability
}

Consequences of bad reputation:
  -> Fewer intents routed to that pool (users avoid)
  -> Lower committee_fee earnings
  -> Governance can force committee rotation
  -> Persistent censorship -> ejection from validator set
```

**Summary: Censorship resistance guarantees**

| Scenario | Resistance Mechanism | Outcome |
|:---------|:--------------------|:--------|
| Single committee member offline | t-of-n threshold (requires only t members) | Intent decrypted normally |
| < t members online (not censorship) | Client fallback to legacy tx | Transaction included as public |
| Committee censors specific intent | Multi-pool routing + evidence submission | Intent re-routed or committee slashed |
| All committees collude to censor | Emergency plaintext submission | Transaction included as public; committees slashed |
| Network-wide censorship (all validators) | Same as any blockchain censorship | No special protection; standard blockchain censorship resistance applies |

**Key principle: CGS provides privacy when available, degrades gracefully to public transactions when unavailable, and never creates a liveness dependency for the chain.**

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
