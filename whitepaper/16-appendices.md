
**Note:** Section 16 (Appendices) open questions have been transformed into a decision machine with 27 actionable decision items (D-01 through D-27). See Section 16.2 in 15-roadmap.md for the complete decision table with ownership, milestones, and acceptance criteria.

**All open questions from the original list have been converted to decision items with:**
- Type classification (spec/research/simulation/governance/ops)
- Clear ownership (dev/research/tokenomics/ops/governance)
- Milestone assignment (testnet-0/testnet-1/pre-mainnet/post-mainnet)
- Measurable acceptance tests
- Priority tiers (P0=pre-mainnet blockers, P1=testnet-1 required, P2=post-mainnet)

**Example decision items:**
- D-08: Optimal checkpoint frequency -> simulation + throughput model -> "supports X msg/s at Y regions with p95 settlement < Z minutes"
- D-01: Under-claim enforcement -> spec decision -> "no observed nondeterminism in >=10M tx fuzz runs; deterministic fallback works"
- D-24: City emergency bridge to Main (censorship escape hatch) -> spec + governance -> post-mainnet priority

---

### 16.3 CRVS Normative Specification v1 (Draft)

**⚠️ IMPORTANT: This appendix specifies CRVS consensus for FUTURE use (testnet-1 and beyond). For v1 mainnet Snowman baseline, see Section 11.3.2 for slashing evidence specification.**

This appendix provides a **draft specification** for CRVS consensus, based on AvalancheGo with rotor optimizations. This is a design document, not yet a production-ready consensus specification. A full normative spec with state machine formalization, test vectors, and slashing evidence verification will be published separately as "CRVS-SPEC.md" before testnet-1.

**⚠️ Status:** This specification is INCOMPLETE and requires formal verification, simulation validation, and security review before production use. See Section 6.8 for mainnet readiness gates.

**Message Formats** (Protobuf schemas, subject to refinement):

```protobuf
message Proposal {
  bytes header = 1;              // Block header (chain-specific format)
  bytes32 tx_list_hash = 2;      // Merkle root of transaction list
  bytes32 parent_hash = 3;       // Parent block hash
  uint64 timestamp = 4;          // Unix timestamp (milliseconds)
  uint64 slot = 5;               // Slot number
  bytes proposer_pubkey = 6;     // Proposer's validator public key
  bytes signature = 7;           // Proposer signature over (header || tx_list_hash || parent_hash || slot)
}

message Vote {
  bytes32 candidate_hash = 1;    // Hash of the candidate being voted for
  uint64 slot = 2;               // Slot number
  uint32 round = 3;              // Vote round number
  enum VoteType {
    PREFER = 0;                  // "I currently prefer this candidate"
    FINALIZE = 1;                // "I have finalized this candidate"
  }
  VoteType type = 4;
  bytes voter_pubkey = 5;        // Voter's validator public key
  bytes signature = 6;           // Voter signature over (candidate_hash || slot || round || type)
}

message SamplingQuery {
  uint64 slot = 1;               // Which slot are you asking about?
  bytes32 preferred_candidate = 2; // Optional: my current preference (for gossip optimization)
  uint64 round = 3;              // Query round number
  bytes querier_pubkey = 4;      // Querier's validator public key
  bytes signature = 5;           // Signature over (slot || round)
}

message SamplingResponse {
  uint64 slot = 1;
  bytes32 preferred_candidate = 2; // Responder's current preference (or null if UNDECIDED)
  uint32 confidence = 3;           // Responder's confidence score for preferred_candidate
  bool finalized = 4;              // True if responder has finalized this candidate
  bytes responder_pubkey = 5;
  bytes signature = 6;             // Signature over (slot || preferred_candidate || confidence || finalized)
}

message RelayChunk {
  bytes32 content_hash = 1;      // Hash of the data being relayed
  bytes chunk_data = 2;          // Actual data chunk (block header, tx list, etc.)
  uint64 slot = 3;               // Slot this data belongs to
  bytes relay_pubkey = 4;        // Relay's validator public key
  bytes signature = 5;           // Relay signature over (content_hash || slot)
}
```

**State Machine (per-validator, per-slot):**

```text
States:
  1. UNDECIDED          - No candidate seen or preferred yet
  2. PREFERRED(C)       - Currently prefer candidate C, confidence < beta
  3. FINALIZED(C)       - Committed to candidate C (terminal state)
  4. TIMEOUT_RECOVERY   - Slot finalization failed; waiting for recovery

State Variables (per slot s):
  - preferred_candidate: bytes32 | null
  - confidence[candidate]: uint32  (for each seen candidate)
  - round_number: uint32
  - seen_candidates: set<bytes32>
  - finalized: bool
  - timeout_counter: uint32

Transitions:

  UNDECIDED -> PREFERRED(C):
    Trigger: First valid candidate C received
    Condition: validate_candidate(C) == true
    Action:
      preferred_candidate = C
      confidence[C] = 1
      broadcast SamplingQuery(s, C)
    
  PREFERRED(C) -> PREFERRED(C'):
    Trigger: Sampling round indicates strong preference for C' != C
    Condition: 
      sample_votes[C'] >= alpha AND
      sample_votes[C'] > sample_votes[C] + hysteresis_gap
    Action:
      preferred_candidate = C'
      confidence[C'] = 1
      confidence[C] = 0
      broadcast SamplingQuery(s, C')
  
  PREFERRED(C) -> FINALIZED(C):
    Trigger: Confidence threshold reached
    Condition: confidence[C] >= beta
    Action:
      finalized = true
      broadcast Vote(C, slot=s, type=FINALIZE)
      apply_block(C)
      advance_to_next_slot()
  
  PREFERRED(C) -> UNDECIDED:
    Trigger: Confidence decays to zero due to sampling failures
    Condition: confidence[C] == 0 AND no other candidate has confidence > 0
    Action:
      preferred_candidate = null
  
  PREFERRED(C) -> TIMEOUT_RECOVERY:
    Trigger: Timeout_max rounds elapsed without finalization
    Condition: round_number > Timeout_max (e.g., 30 rounds)
    Action:
      log_error("Slot finalization timeout")
      enter_recovery_protocol()
  
  FINALIZED(C) -> (terminal):
    No further transitions for this slot

Timeouts:
  - delta_propagate = 2000ms      # Max time to wait for candidate propagation
  - delta_sample = 200ms          # Time between sampling rounds
  - round_timeout = 5000ms        # Max time per round before considering it failed
  - Timeout_max = 30 rounds       # Absolute max rounds before recovery
  - jitter = rand(0, 1000ms)      # Random jitter to prevent synchronization

Reset conditions:
  - If network partition detected, reset to UNDECIDED and wait for partition heal
  - If clock skew >500ms detected, enter SLOW_PATH mode with increased timeouts
```

**Fork-Choice Rule (deterministic tie-breaking):**

```text
PreferredCandidate(S) = min(Rank(C) for C in S where valid(C) and seen(C))

Rank(C) = (C.slot, keccak256(C.header), C.proposer_vk)

Comparison:
  - First by slot (lower slot number is older, preferred)
  - Then by header hash (lexicographic order)
  - Then by proposer public key (lexicographic order)

This ensures:
  1. Deterministic: All validators compute the same Rank()
  2. Unpredictable: Proposers cannot manipulate ranking (header hash is unpredictable pre-proposal)
  3. Fair: No inherent bias toward any proposer
```

**Locking and Safety Conditions:**

```text
Vote Locking:
  - Once a validator votes FINALIZE for candidate C in slot s, it MUST NOT vote for C' != C in slot s
  - Violation of this rule is equivocation (slashable offense)

Finality Rule:
  - A candidate C is considered finalized when:
    1. Local finalization: Validator has confidence[C] >= beta, OR
    2. Network finalization: Validator observes >= quorum_finalize FINALIZE votes for C
    
  - quorum_finalize = ceil(0.67 * committee_size)

Safety Invariant:
  - Under partial synchrony and <30% Byzantine validators, no two honest validators will finalize different candidates for the same slot
  - Proof sketch: Finalization requires beta consecutive rounds with alpha/k threshold. Adversary cannot cause >alpha votes for conflicting candidates without controlling >alpha validators, but alpha = 0.75*k ensures honest majority dominates sampling.
```

**Slashing Conditions & Evidence Formats:**

**1. Equivocation (double-voting):**

```text
Evidence:
{
  type: "EQUIVOCATION",
  vote1: Vote {
    candidate_hash: 0xAAA...,
    slot: 12345,
    round: 5,
    type: FINALIZE,
    voter_pubkey: 0xValidator1,
    signature: 0x...
  },
  vote2: Vote {
    candidate_hash: 0xBBB...,  // Different candidate
    slot: 12345,                // Same slot
    round: 7,                   // Possibly different round
    type: FINALIZE,
    voter_pubkey: 0xValidator1, // Same validator
    signature: 0x...
  }
}

Verification:
  1. verify_signature(vote1.signature, vote1.voter_pubkey, message_hash(vote1)) == true
  2. verify_signature(vote2.signature, vote2.voter_pubkey, message_hash(vote2)) == true
  3. vote1.voter_pubkey == vote2.voter_pubkey
  4. vote1.slot == vote2.slot
  5. vote1.candidate_hash != vote2.candidate_hash
  6. vote1.type == FINALIZE OR vote2.type == FINALIZE (at least one finalization vote)

Slashing: Automatic on valid evidence; slash 5% of validator's stake.
```

**2. Relay Withholding (censorship):**

```text
Evidence:
{
  type: "RELAY_WITHHOLDING",
  slot: 12345,
  relay_pubkey: 0xRelay1,
  relay_assignment_proof: 0x...,  // Proof that this validator was assigned as relay for this slot
  request: RelayChunkRequest {
    chunk_hash: 0x...,
    requester_pubkey: 0xValidator2,
    timestamp: 1234567890,
    signature: 0x...
  },
  timeout_proof: {
    request_timestamp: 1234567890,
    timeout_duration: 5000ms,
    witness_signatures: [...]  // Multiple validators attest they didn't receive data
  }
}

Verification:
  1. Verify relay_assignment_proof shows relay_pubkey was indeed a relay for this slot
  2. Verify request.signature is valid
  3. Verify timeout_proof has >= 3 witness signatures attesting to non-delivery
  4. Verify timeout_duration >= delta_propagate + network_buffer (2000ms + 1000ms)

Slashing: 2% of validator's stake; relay role suspended for 100 epochs.

False-positive risk: Low if witnesses are chosen randomly and independently. Requires collusion of >=3 validators to fabricate evidence.
```

**3. Invalid Vote (malformed message):**

```text
Evidence:
{
  type: "INVALID_VOTE",
  vote: Vote { ... },
  error: "INVALID_SIGNATURE" | "INVALID_CANDIDATE" | "TIMESTAMP_OUT_OF_BOUNDS",
  validator_pubkey: 0x...,
  block_height: 12345  // When this invalid vote was observed
}

Verification:
  1. Attempt to verify vote.signature
  2. If signature invalid, evidence is valid
  3. If signature valid, check if vote.candidate_hash refers to a non-existent or invalid candidate
  4. If candidate invalid, evidence is valid

Slashing: 1% of stake; warning flag for persistent misbehavior.

False-positive risk: Negligible (cryptographic verification is deterministic).
```

**Slashing Evidence Submission:**

- **Who can submit:** Any validator in the committee
- **Where:** Evidence submitted as special transaction on Federal Chain
- **Verification:** Federal Chain validates evidence during block execution
- **Dispute period:** 7 days for validator to provide counter-evidence or governance appeal
- **Automatic execution:** If no valid dispute, slashing executes automatically

**Assumptions:**

```text
Network Model:
  - Partial synchrony: After unknown Global Stabilization Time (GST), all messages delivered within Δ_max
  - Δ_max = 10 seconds (conservative; typical networks achieve <1s)
  - No assumption of synchrony before GST (network may be arbitrarily slow/partitioned)

Clock Model:
  - Loosely synchronized clocks with bounded drift
  - Max clock skew: ±500ms between any two validators
  - Maintained via NTP or similar; clock skew >500ms triggers alerts

Adversary Model:
  - Byzantine adversary controlling <30% of validators (by stake)
  - Adversary can:
    * Delay, reorder, or drop messages (within partial synchrony bounds)
    * Equivocate (send conflicting messages to different validators)
    * Censor transactions (if proposer)
    * Collude with other Byzantine validators
  - Adversary cannot:
    * Forge signatures without private keys
    * Break cryptographic assumptions (e.g., collision resistance of hash functions)
    * Violate partial synchrony bounds after GST

Liveness Assumption:
  - Requires honest majority (>50%) and eventual synchrony
  - If adversary controls 30-50%, liveness may degrade but safety preserved
  - If adversary controls >=50%, both safety and liveness can be violated

Safety Assumption:
  - Preserved under <30% Byzantine validators and partial synchrony
  - Does NOT require synchrony assumption (safety holds even during network partitions, though liveness may be lost)
```

**What Happens When Assumptions Fail:**

| Failed Assumption | Impact | System Behavior |
|:------------------|:-------|:----------------|
| Clock skew >500ms on >30% validators | Liveness degrades; finality slower | Validators enter SLOW_PATH; timeouts increased to 15s; alerts triggered |
| Network partition isolates >30% validators | Minority partition halts; majority continues | Minority validators detect low participation, stop finalizing; partition heals -> re-sync |
| Adversary 30-50% stake | Liveness at risk; safety preserved | Finalization may take 10-30s instead of 2-5s; governance may intervene |
| Adversary >=50% stake | Safety and liveness both violated | Chain is insecure; requires social recovery (community decides canonical chain) |
| GST never stabilizes (network always unstable) | Liveness lost; safety preserved | No finalization; chain halts; manual intervention required |

**Monitoring and Alerting Requirements:**

To detect assumption violations in production:

```text
Metrics to track (per validator):
  - consensus.round_time_p50, p95, p99
  - consensus.confidence_score_per_round
  - consensus.finalization_time_per_slot
  - consensus.fork_rate (slots with multiple candidates)
  - consensus.participation_rate (% validators responding to samples)
  - network.clock_skew_vs_ntp
  - network.relay_responsiveness
  - network.partition_events

Alerts:
  - CRITICAL: Clock skew >500ms detected
  - CRITICAL: Participation rate <70% for >5 minutes
  - CRITICAL: Finalization stalled for >30 seconds
  - WARNING: Slow path active for >10 minutes
  - WARNING: Fork rate >5% (multiple candidates competing frequently)
  - INFO: Relay rotation event
```

**Open Questions (must resolve before mainnet):**

1. **Parameter optimization:** What are the optimal values for k, alpha, beta under real-world network conditions?
2. **Fast/slow path hysteresis:** What is the correct threshold for switching between paths to avoid oscillation?
3. **Relay censorship detection:** How do we detect and prove relay censorship vs network failures?
4. **Cross-slot dependencies:** How do we handle situations where slot s+1 builds on a candidate for slot s that hasn't finalized yet?
5. **Proposer rotation fairness:** Is the soft-leader selection mechanism fair and censorship-resistant?

**Next Steps for Production Readiness:**

1. ✅ Complete state machine specification (this document)
2. ❌ Formal TLA+ or similar model of state machine
3. ❌ Exhaustive simulation campaign (10M+ rounds under adversarial conditions)
4. ❌ Security audit by external firm (e.g., Trail of Bits, Zellic)
5. ❌ Testnet deployment with real validators and economic incentives
6. ❌ Soak test (3+ months) with bounties for breaking safety/liveness
7. ❌ Parameter sensitivity analysis and optimization
8. ❌ Formal writeup of safety/liveness proofs


---

### 16.4 Atomic Messaging Spec

**⚠️ Architectural Note:** This atomic bundle block mechanism is **NOT** standard Avalanche behavior. While inspired by Avalanche's subnet model, CryftNet implements a **multi-VM atomic commit substrate** where all three chains (Federal, Mirror, EVM) must advance together in lockstep at the consensus layer. This is a custom kernel-level enhancement requiring coordination between three independent VM execution engines and shared finality semantics. This design eliminates bridge latency but increases validator complexity and requires all three VMs to be available for the network to progress.

Proposers produce bundle blocks (Federal+Mirror+EVM) with shared bundle_hash = keccak256(concat(headers)); validators vote on bundle. Failures rollback all chains in bundle. Validity: Each chain's rules + cross-chain invariants (e.g., GBL updates atomic with events).

**Bundle Block Structure:**

```text
BundleBlock {
  // Individual chain headers
  federal_header: BlockHeader {
    height: uint64,
    parent_hash: bytes32,
    state_root: bytes32,
    tx_root: bytes32,
    timestamp: uint64,
    validator_set_hash: bytes32,
    proposer_signature: bytes
  },
  
  mirror_header: BlockHeader {
    height: uint64,
    parent_hash: bytes32,
    utxo_root: bytes32,
    tx_root: bytes32,
    timestamp: uint64,
    proposer_signature: bytes
  },
  
  evm_header: BlockHeader {
    height: uint64,
    parent_hash: bytes32,
    state_root: bytes32,
    tx_root: bytes32,
    timestamp: uint64,
    gas_used: uint64,
    gas_limit: uint64,
    proposer_signature: bytes
  },
  
  // Bundle-level commitment
  bundle_hash: bytes32,  // keccak256(federal_header || mirror_header || evm_header)
  bundle_height: uint64, // Must be consistent across all three chains
  
  // Cross-chain messages (applied in this bundle)
  cross_chain_messages: [
    {
      from_chain: enum { Federal, Mirror, EVM },
      to_chain: enum { Federal, Mirror, EVM },
      message_type: string,  // e.g., "GBL_UPDATE", "VALIDATOR_REWARD", "CODE_VAULT_COMMIT"
      payload: bytes,
      nonce: uint64,
      commitment_hash: bytes32  // Hash of (from_chain || to_chain || message_type || payload || nonce)
    },
    ...
  ],
  
  // Cross-chain invariant proofs
  invariant_proofs: {
    gbl_conservation_proof: {
      // Proves that sum(debits) == sum(credits) for all GBL updates in this bundle
      merkle_root: bytes32,
      total_debits: uint256,
      total_credits: uint256,
      proof_data: bytes
    },
    validator_set_consistency_proof: {
      // Proves that Federal Chain validator set hash is consistent with what EVM Chain expects
      federal_validator_set_hash: bytes32,
      proof_data: bytes
    }
  },
  
  // Proposer signature over entire bundle
  proposer_pubkey: bytes,
  proposer_signature: bytes  // Signs: bundle_hash || bundle_height || timestamp
}
```

**Deterministic Execution Ordering:**

```text
Phase 1: Pre-execution validation
  For each chain C in [Federal, Mirror, EVM]:
    1. Verify chain C's header is well-formed
    2. Verify parent_hash links to previous finalized bundle
    3. Verify timestamp is within acceptable bounds (±2s from proposer's timestamp)
    4. Verify tx_root matches actual transaction list
  
  If any header invalid: REJECT bundle, proposer slashed

Phase 2: Cross-chain message application (before execution)
  For each chain C in execution order [Federal, Mirror, EVM]:
    1. Fetch pending cross-chain messages TO chain C from previous bundles
    2. Apply messages in nonce order (deterministic)
    3. Verify message signatures and commitments
    4. Update chain C's pre-execution state
  
  If any message invalid: REJECT bundle, proposer slashed

Phase 3: Execute each chain in order
  1. Federal Chain executes:
       - Process Federal Chain transactions
       - Update validator set, stake, governance state
       - Generate outgoing messages (e.g., validator rewards to Mirror Chain)
     
     If Federal execution fails or produces invalid state_root: REJECT bundle
  
  2. Mirror Chain executes:
       - Apply Federal messages (e.g., validator reward credits)
       - Process Mirror Chain UTXO transactions
       - Update GBL (Global Balance Ledger)
       - Update Code Vault (bytecode storage)
       - Generate outgoing messages (e.g., GBL updates to EVM Chain)
     
     If Mirror execution fails or produces invalid utxo_root: REJECT bundle
  
  3. EVM Chain executes:
       - Apply Mirror messages (e.g., GBL updates via precompiles)
       - Process EVM Chain transactions
       - Transactions can READ latest GBL state via precompiles (atomic read)
       - Generate outgoing messages (e.g., contract deployment events to Mirror Chain)
     
     If EVM execution fails or produces invalid state_root: REJECT bundle

Phase 4: Cross-chain invariant validation
  1. GBL Conservation:
       Verify: sum(GBL debits in bundle) == sum(GBL credits in bundle)
       If violated: REJECT bundle, proposer slashed
  
  2. Validator Set Consistency:
       Verify: Federal validator_set_hash matches what Mirror/EVM expect
       If violated: REJECT bundle (data race, proposer may not be slashed)
  
  3. Code Vault Integrity:
       Verify: All code_ids referenced by EVM deployments exist in Mirror Code Vault
       If violated: REJECT bundle

Phase 5: Quorum voting
  1. Each validator computes: bundle_hash_computed = keccak256(federal_header || mirror_header || evm_header)
  2. If bundle_hash_computed == bundle.bundle_hash: vote ACCEPT
  3. If any phase failed: vote REJECT
  4. Broadcast vote to committee
  5. Collect votes until quorum reached (67% for ACCEPT, 33% for REJECT)

Phase 6: Finalization or rollback
  If quorum votes ACCEPT:
    - Commit all three chains' state changes atomically
    - Update Last Finalized Bundle (LFB) pointer
    - Advance to next bundle height
    - Broadcast finalization message
  
  If quorum votes REJECT:
    - Rollback all in-progress state changes
    - Revert to previous LFB
    - Proposer slashed (if rejection due to invalid bundle vs network timeout)
    - Next validator becomes proposer for retry
```

**Atomic Execution Contract (formal semantics):**

```text
Define: BundleExecution(B) -> (Success, NewStateFederal, NewStateMirror, NewStateEVM) | (Failure, Reason)

Atomicity guarantee:
  IF BundleExecution(B) returns Success:
    THEN all three state transitions are applied
  ELSE IF BundleExecution(B) returns Failure:
    THEN NO state transitions are applied (all chains remain at previous state)

No partial states:
  It is IMPOSSIBLE for Federal to be at height H and Mirror at height H-1.
  Either all three are at H, or all three are at H-1.

Idempotence:
  Applying BundleExecution(B) multiple times (e.g., after crash recovery) 
  produces the same result as applying it once.
```

**Rollback Mechanism:**

```text
Rollback triggers:
  1. Validator crash during Phase 3 (execution)
  2. ANY chain produces invalid state_root
  3. Cross-chain invariant violation detected
  4. Quorum REJECT vote
  5. Timeout (if bundle execution takes >15 seconds)

Rollback procedure:
  1. Halt execution immediately
  2. Discard in-memory state changes for all three chains
  3. Read Last Finalized Bundle (LFB) from persistent storage
  4. Restore Federal state to LFB.federal_state_root
  5. Restore Mirror state to LFB.mirror_utxo_root
  6. Restore EVM state to LFB.evm_state_root
  7. Clear pending transaction pool (proposer will re-select txs)
  8. Wait for next proposer to create recovery bundle

Recovery bundle:
  - Contains only valid, non-conflicting transactions
  - May be empty bundle if problematic tx cannot be identified
  - MUST have valid parent_hash linking to LFB
  - MUST satisfy all cross-chain invariants

Proposer slashing (if rollback due to invalid bundle):
  - Slash 5% of proposer's stake
  - Proposer suspended from proposal duty for 100 bundles
  - Evidence: {bundle, rejection quorum signatures, reason}
```

**Crash Consistency Guarantees:**

Write-ahead log structure:

```text
WAL Entry Format:
  {
    entry_type: "BEGIN_BUNDLE" | "COMMIT_BUNDLE" | "ROLLBACK_BUNDLE",
    bundle_height: uint64,
    bundle_hash: bytes32,
    timestamp: uint64,
    changes: {
      federal_changes: [...],
      mirror_changes: [...],
      evm_changes: [...]
    }
  }

Crash recovery algorithm:
  On validator restart:
    1. Read WAL from disk
    2. Find last completed entry (entry_type == "COMMIT_BUNDLE")
    3. If last entry is "BEGIN_BUNDLE":
         -> Incomplete bundle detected
         -> Rollback to previous LFB
         -> Discard incomplete changes
    4. Rebuild state from LFB + committed bundles
    5. Sync missing bundles from peers if necessary
    6. Resume normal operation

Persistence requirements:
  - LFB MUST be fsync()'d before broadcasting vote
  - WAL entries MUST be fsync()'d before applying state changes
  - State roots MUST be written atomically (all three or none)
```

**Data Availability Requirements:**

Minimum data required to vote on bundle B:

```text
Required:
  1. federal_header (200 bytes)
  2. mirror_header (200 bytes)
  3. evm_header (500 bytes)
  4. cross_chain_messages list (1-50 KB depending on activity)
  5. invariant_proofs (5-20 KB)
  
  Total: ~6-71 KB

Optional (for full validation):
  1. Federal transaction list (10-50 KB)
  2. Mirror transaction list (50-200 KB)
  3. EVM transaction list (100-500 KB)
  
  Total: 166-821 KB

Light vote path:
  - Validator downloads only Required data
  - Trusts that >=67% of validators validated full data
  - Acceptable for low-value chains or during sync
  - NOT recommended for Main Chain

Full validation path:
  - Validator downloads Required + Optional data
  - Re-executes all three chains independently
  - Computes state roots and compares to bundle headers
  - Votes only if all roots match
  - Recommended for high-security applications
```

**Bandwidth Analysis:**

At 2 bundles/second (target throughput):

```text
Light validators:
  - 71 KB/bundle * 2 bundles/sec = 142 KB/s = ~1.1 Mbps download
  - Acceptable for consumer-grade internet (10+ Mbps)

Full validators:
  - 821 KB/bundle * 2 bundles/sec = 1.64 MB/s = ~13 Mbps download
  - Acceptable for datacenter-grade internet (100+ Mbps)
  - May be challenging for home validators in some regions

Mitigation for high bandwidth:
  - Data availability sampling (DAS) reduces to ~10-20 KB/sample
  - Transaction compression (zstd, brotli)
  - Erasure coding + peer-to-peer distribution (BitTorrent-style)
  - Light validator mode for non-critical roles
```

**Upgrade Coupling & VM Versioning:**

```text
Bundle format versioning:
  BundleBlock_v1: (current spec)
    - Three chains: Federal, Mirror, EVM
    - Fixed execution order
    - Cross-chain messages + invariants
  
  BundleBlock_v2: (future, if needed)
    - Four chains: Federal, Mirror, EVM, CustomVM
    - Flexible execution order (configurable via governance)
    - Enhanced invariant proof system

Upgrade process:
  1. Propose BundleBlock_v2 on Federal Chain via governance
  2. Voting period: 14 days, threshold: 67%
  3. Activation height: H_activate (set by governance)
  4. All validators MUST upgrade by height H_activate - 1000
  5. At height H_activate, bundle format switches to v2
  6. Validators running old version cannot participate after H_activate

Backward compatibility:
  - Old validators can continue validating old bundles during grace period
  - New validators can validate both old and new bundle formats
  - Grace period: 90 days after activation

Emergency rollback:
  - If v2 causes persistent liveness failures within 7 days of activation:
    -> Governance supermajority (80%) can vote to rollback to v1
    -> Rollback must happen within 48 hours of vote passing
    -> All bundles after H_activate are invalidated
    -> Chain reorgs to last v1 bundle
```

**Failure Mode Summary:**

| Failure Type | Detection | Recovery Time | Data Loss | Proposer Slashed? |
|:-------------|:----------|:--------------|:----------|:------------------|
| Invalid federal_header | Phase 1 validation | Immediate (next proposer) | None | Yes |
| Invalid mirror_header | Phase 1 validation | Immediate (next proposer) | None | Yes |
| Invalid evm_header | Phase 1 validation | Immediate (next proposer) | None | Yes |
| Federal execution crash | Phase 3 execution | 2-5 seconds (rollback + retry) | None | No (environmental) |
| Mirror execution crash | Phase 3 execution | 2-5 seconds (rollback + retry) | None | No (environmental) |
| EVM execution crash | Phase 3 execution | 2-5 seconds (rollback + retry) | None | No (environmental) |
| GBL conservation violated | Phase 4 invariant check | Immediate (reject) | None | Yes |
| Validator set inconsistency | Phase 4 invariant check | Immediate (reject) | None | Maybe (depends on cause) |
| Quorum cannot be reached | Phase 5 voting timeout | 10-30 seconds (re-proposal) | None | No |
| Proposer censors transactions | Off-chain detection | Eventual (next proposer) | Delayed txs | Slashed if provable |
| Network partition | Minority partition halts | Minutes to hours (partition heals) | None (after re-sync) | No |

**Open Questions (must resolve before production):**

1. What is the maximum acceptable bundle execution time before triggering timeout?
2. How do we handle situations where one VM is consistently slower than others (e.g., EVM gas limit too high)?
3. Should we allow "partial bundles" where one chain has no transactions? (Current answer: yes, empty tx list is valid)
4. How do we prevent proposers from gaming execution order to extract MEV across chains?
5. What monitoring infrastructure is needed to detect cross-chain invariant violations in real-time?


---

### 16.5 Checkpoint & Message Root Spec

**Hash function choice:** Message roots use **Poseidon Merkle trees** when ZK validity proofs are enabled (reduces proof generation cost in ZK circuits). For baseline checkpoints without ZK proofs, standard **Keccak-256 Merkle trees** are used. This dual approach balances ZK-friendliness with EVM tooling compatibility.

Message root: Poseidon Merkle tree (ZK mode) or Keccak Merkle tree (baseline mode); leaves: ABI-encoded messages sorted by type+id. Proofs: Standard Merkle paths. Validator-set: Federal registry hashes per epoch.

**Message Root Construction:**

```text
messages = [msg1, msg2, ...] // All cross-chain messages in checkpoint
sorted_messages = sort(messages, key=lambda m: (m.type, m.id))
leaves = [keccak256(abi.encode(msg)) for msg in sorted_messages]
message_root = PoseidonMerkleRoot(leaves)
```

**Checkpoint Structure:**

```text
Checkpoint {
  region_id: uint64,
  height: uint64,
  block_hash: bytes32,
  state_root: bytes32,
  message_root: bytes32,
  validator_set_hash: bytes32,  // From Federal registry for this epoch
  quorum_sig: BLS_Signature,
  timestamp: uint64
}
```

**Merkle Proof Verification:**

```text
VerifyMessageInclusion(checkpoint, message, proof):
  leaf = keccak256(abi.encode(message))
  computed_root = PoseidonMerkleVerify(leaf, proof)
  return computed_root == checkpoint.message_root
```

---

### 16.6 Gas Schedule

Slot claim: 200 gas/claim; trace logging: 100 gas/access; penalty: 1.5x consumed.

**Smart Slots Gas Costs:**

| Operation | Gas Cost | Notes |
|:----------|:---------|:------|
| Slot claim (per slot) | 200 gas | Paid at tx validation time |
| Trace logging (per access) | 100 gas | Paid during execution |
| Under-claim penalty | 1.5x consumed gas | Applied if actual access > claimed |
| Object slot declaration | 200 gas | Via DECLARE_OBJECT_SLOT precompile |
| Parallel lane scheduling | 0 gas | Free (part of consensus) |
| Serial fallback | +1000 gas | Penalty for forcing serial execution |

**Example:**

```text
Transaction with 3 slot claims, 5 actual accesses, 50k gas execution:
- Slot claim cost: 3 * 200 = 600 gas
- Trace logging: 5 * 100 = 500 gas
- Execution: 50,000 gas
- Total: 51,100 gas

If under-claimed (6 accesses, only claimed 3):
- Penalty: 51,100 * 1.5 = 76,650 gas
```

---

### 16.7 Ping Spec

QUIC PING with Ed25519 sig + nonce; reports: summaries + random samples; on-chain: post aggregated proof, verify quorum sigs.

**Ping Protocol:**

```text
PingRequest {
  target_node: NodeID,
  timestamp: uint64,
  nonce: bytes32,
  sig: Ed25519Sig
}

PingResponse {
  request_hash: bytes32,
  latency_ms: uint32,
  timestamp: uint64,
  sig: Ed25519Sig
}
```

**Eligibility Proof:**

Validator aggregates ping responses and posts summary on-chain:

```text
PingReport {
  validator: address,
  epoch: uint64,
  num_pings: uint32,
  avg_latency_ms: uint32,
  sample_pings: [PingResponse],  // Random sample for verification
  aggregated_sig: BLS_Signature  // Quorum of validators attesting to report
}
```

**On-Chain Verification:**

```text
VerifyPingEligibility(report):
  1. Verify aggregated_sig covers >=2/3 of validator set
  2. Verify sample_pings signatures
  3. Verify avg_latency_ms <= threshold (e.g., 100ms)
  4. Verify num_pings >= minimum (e.g., 100 pings/epoch)
  5. Mark validator eligible for low-latency rewards
```

---

### 16.8 v1 Monetary Policy

Continuous issuance (no supply cap); PoW phase: all fees to miner; PoS phase: EIP-1559 fee burn + issuance; slashing evidence structs.

**Monetary Policy Parameters:**

```text
=== PoW Phase (v1 launch) ===
Block Reward:    2 CRYFT/block     // Continuous issuance, no supply cap
Fee Model:       First-price auction // All tx fees (gas_used * gas_price) to block miner
Fee Burn Rate:   0%                 // No burning during PoW phase (same as Ethereum 2015-2021)
Supply Cap:      NONE               // Uncapped, like Ethereum

=== PoS Phase (post-transition) ===
Issuance:        sqrt(total_staked) curve  // Ethereum-style validator rewards
Fee Model:       EIP-1559            // base_fee burned, priority_fee to validator
Slashing Rate:   1/32 of stake (~3.125%)   // Per provable misbehavior
Minimum Stake:   32,000 CRYFT       // To become validator
```

**Fee Distribution:**

```text
PoW Phase:
  For each transaction with fee F:
    miner_reward = F     // 100% of fees to block miner
    burned = 0           // No burn during PoW
    Total miner income per block = block_reward (2 CRYFT) + sum(tx_fees)

PoS Phase (EIP-1559):
  For each transaction with fee F = base_fee + priority_fee:
    burned = base_fee              // Algorithmically adjusted, burned permanently
    validator_reward = priority_fee // Tip goes to block proposer
    Total validator income per epoch = issuance_reward + sum(priority_fees)

Total Supply: Uncapped (continuous issuance; net inflation/deflation determined by
              issuance rate vs. burn rate once EIP-1559 activates)
```

**Slashing Evidence Structures:**

```text
EquivocationEvidence {
  vote1: Vote,
  vote2: Vote,
  validator_pubkey: bytes,
  // Verification: vote1.round == vote2.round AND vote1.candidate != vote2.candidate
}

WithholdingEvidence {
  request: RelayChunkRequest,
  timeout_proof: uint64,
  validator_pubkey: bytes,
  // Verification: timeout_proof > request.timestamp + MAX_RELAY_DELAY
}

InvalidVoteEvidence {
  vote: Vote,
  error: string,
  validator_pubkey: bytes,
  // Verification: vote.sig invalid OR vote.format incorrect
}
```

---

### 16.9 Cryftee Sandbox Spec

Host functions: limited (fs read-only, net peers only); limits (1s CPU, 512MB mem); admin API: HTTPS+TLS; kiosk UI: sandboxed iframes.

**Cryftee Module Sandbox:**

```text
Sandbox Limits:
- CPU: 1 second per request
- Memory: 512MB max
- Filesystem: Read-only access to /data
- Network: Only peers in validator set (no arbitrary outbound)
- Syscalls: Whitelist only (no exec, no raw sockets)
```

**Host Functions:**

```rust
// Available to Cryftee WASM modules
interface CryfteeHost {
  // Storage
  fn read_file(path: &str) -> Result<Vec<u8>>;
  
  // Network (restricted to peers)
  fn send_to_peer(peer_id: NodeID, data: &[u8]) -> Result<()>;
  fn recv_from_peer(timeout_ms: u32) -> Result<(NodeID, Vec<u8>)>;
  
  // Crypto
  fn sign_ed25519(data: &[u8]) -> Result<Signature>;
  fn verify_bls_sig(sig: &[u8], pubkey: &[u8], msg: &[u8]) -> bool;
  
  // Logging
  fn log(level: LogLevel, msg: &str);
}
```

**Admin API:**

```text
HTTPS + TLS required
Endpoints:
  POST /modules/install   - Install signed WASM module
  GET  /modules/list      - List installed modules
  POST /modules/enable    - Enable module
  POST /modules/disable   - Disable module
  GET  /health            - Health check
```

**Kiosk UI:**

- Sandboxed iframes for module UIs
- No direct DOM access to host page
- PostMessage API for limited communication
- CSP: `default-src 'none'; script-src 'self'; style-src 'self'`

---

### 16.10 Pinning Proofs Spec

UnixFS chunking; merkle proofs; on-chain: auditor attestations (quorum sigs), full proofs off-chain for disputes.

**IPFS Pinning Proof Structure:**

```text
PinningProof {
  cid: IPFS_CID,
  pin_provider: address,
  epoch: uint64,
  challenge_block: bytes32,  // Random challenge from on-chain
  merkle_proof: bytes,       // Proof of chunk availability
  auditor_attestations: [
    {
      auditor: address,
      timestamp: uint64,
      sig: BLS_Signature
    },
    ...
  ]
}
```

**Challenge-Response Protocol:**

```text
1. On-chain: Post random challenge_block for CID
2. Pin provider: Compute Merkle proof for random chunk derived from challenge_block
3. Pin provider: Submit proof + auditor attestations (quorum sigs)
4. On-chain: Verify quorum (>=2/3 auditors) attested
5. If valid: reward pin provider; else: slash
```

**UnixFS Chunking:**

- Default chunk size: 256KB
- Merkle tree: SHA-256 based
- On-chain storage: Only root CID + auditor sigs
- Dispute: Full Merkle proof posted on-chain if challenged

**Auditor Attestation:**

Auditors independently verify chunk availability:

```text
Auditor verifies:
  1. Fetch chunk from pin provider
  2. Compute chunk_hash = SHA256(chunk_data)
  3. Verify Merkle inclusion proof
  4. Sign attestation: BLS_Sign(auditor_key, (cid, chunk_hash, epoch))
  5. Submit to pin provider for aggregation
```
