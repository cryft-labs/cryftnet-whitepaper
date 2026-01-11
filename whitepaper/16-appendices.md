
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

### 16.3 CRVS Normative Specification v1

This appendix provides the canonical, implementable spec for CRVS consensus, based on AvalancheGo with rotor optimizations. All implementations MUST follow this exactly to avoid forks.

**Message Formats** (Protobuf schemas):
- Proposal: {header: bytes, tx_list_hash: bytes32, parent_hash: bytes32, timestamp: uint64, sig: bytes}
- Vote: {candidate_hash: bytes32, round: uint32, sig: bytes}
- RelayChunk: {content_hash: bytes32, chunk_data: bytes, sig: bytes}
- SamplingQuery: {slot: uint64, preferred_candidate: optional bytes32}

**State Machine (per-validator)**:
- States: Proposing, VotingFast, VotingSlow, Finalized
- Transitions: Proposing -> VotingFast on proposal send; VotingFast -> VotingSlow on miss_quorum(k=2) OR conflicts>=2; VotingSlow -> Finalized on stable_quorum(k=3) AND no conflicts; timeouts (delta_propagate=2s, round_timeout=5s + rand(1s jitter)) reset rounds.

**Fork-Choice Rule**:
PreferredCandidate = min(rank(C) for C in quorum_candidates where votes(C) >= q_fast)
rank(C) = (C.slot, keccak256(C.header), C.proposer_vk)
Lock on q_fast votes; finalize on beta=12 consecutive samples exceeding alpha=15 in k=20.

**Slashing Conditions & Evidence**:
- Equivocation: Two votes same round (evidence: {votes: [Vote1, Vote2]})
- Withholding: Relay failure proof (evidence: {request: RelayChunkRequest, timeout: uint64})
- Invalid Vote: Bad sig/format (evidence: {vote: Vote, error: string})
- Slashing: Automatic on valid evidence; slash 5% stake.

**Assumptions**:
- Partial synchrony: GST=10s max delay
- Clock drift: <500ms
- Adversary: <30% Byzantine

---

### 16.4 Atomic Messaging Spec

Proposers produce bundle blocks (Federal+Mirror+EVM) with shared bundle_hash = keccak256(concat(headers)); validators vote on bundle. Failures rollback all chains in bundle. Validity: Each chain's rules + cross-chain invariants (e.g., GBL updates atomic with events).

**Bundle Block Structure:**

```text
BundleBlock {
  federal_header: BlockHeader,
  mirror_header: BlockHeader,
  evm_header: BlockHeader,
  bundle_hash: keccak256(federal_header || mirror_header || evm_header),
  cross_chain_messages: [
    {
      from_chain: enum { Federal, Mirror, EVM },
      to_chain: enum { Federal, Mirror, EVM },
      message_type: string,
      payload: bytes,
      nonce: uint64
    },
    ...
  ],
  proposer_sig: bytes
}
```

**Atomic Execution:**

1. Validator receives BundleBlock
2. Validates each chain's header independently
3. Validates cross-chain message invariants (e.g., GBL conservation)
4. If ANY chain invalid OR invariant violated: reject entire bundle
5. If all valid: vote to accept bundle
6. Upon quorum: apply all three chains atomically

**Rollback Mechanism:**

If bundle fails mid-execution (validator crash, etc.):
- All three chains rollback to last finalized bundle
- Proposer slashed for invalid bundle
- Next proposer creates recovery bundle

---

### 16.5 Checkpoint & Message Root Spec

Message root: Poseidon Merkle tree; leaves: ABI-encoded messages sorted by type+id. Proofs: Standard Merkle paths. Validator-set: Federal registry hashes per epoch.

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

No emission; 50% fee burn; formula a=1, b=0.5; slashing evidence structs.

**Monetary Policy Parameters:**

```text
Emission Rate: 0 CRYFT/block  // No new issuance
Fee Burn Rate: 50%            // Half of tx fees burned
Slashing Rate: 5%             // Of validator stake per offense
Minimum Stake: 1000 CRYFT     // To become validator
```

**Fee Distribution:**

```text
For each transaction with fee F:
  burned = F * 0.5
  validator_reward = F * 0.3
  treasury = F * 0.2

Total Supply: Fixed at genesis (no inflation)
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
