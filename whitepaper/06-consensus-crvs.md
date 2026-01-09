queries. Each validator periodically samples k peers and asks which candidate they currently prefer
for slot s (or which parent tip they prefer). If a candidate repeatedly exceeds an acceptance threshold
alpha across consecutive rounds beta, the node increases its confidence. This tends to produce
metastable convergence: once a majority leans one way, it becomes increasingly likely that the whole

network converges.
Parameters (example):
- k = 20               # sample size
- alpha = 15           # acceptance threshold (alpha <= k)
- beta = 12            # consecutive successful samples to decide
```text
Loop for slot s:
conf[C] = 0 for all candidates C
while not finalized:
  S = sample_k_peers()
  counts = query_preference(S, s)
  C* = argmax(counts)
  if counts[C*] >= alpha:
     conf[C*] += 1
  else:
     conf[C*] = max(conf[C*] - 1, 0)
  if conf[C*] >= beta:
     cast_vote(C*)
     (finalization still requires Section 6.3 thresholds)
```

### 6.5 Finality layering: region soft-finality vs Main hard-finality

Regions provide fast soft-finality (practically irreversible under normal operation). Main provides
hard-finality for cross-region settlement by accepting checkpoints. A checkpoint is a region-signed
commitment to a region block height and state root (or output root) plus proof of validator quorum.
Once Main finalizes a checkpoint, cross-region transfers referencing that checkpoint can be treated as final under Main's security assumptions.

### 6.6 Data availability sampling (DAS) extensions

CRVS focuses on consensus efficiency within committees, but does not inherently solve the data availability problem at scale. Data Availability Sampling (DAS), as demonstrated by Ethereum's PeerDAS (introduced via the Fusaka upgrade in December 2025), enables nodes to verify that block data is available for reconstruction by sampling small fragments rather than downloading entire blocks.

CryftNet can integrate DAS as an optional enhancement layer:

**How DAS complements CRVS:**

- **Checkpoint data availability:** Before Main accepts a region checkpoint, light clients or sampling nodes can verify that the underlying region block data is available without downloading the full block. This is especially valuable for cross-region settlement where Main validators should not need to store all region data.
- **Scalability without centralization:** DAS allows larger block sizes (higher throughput) while preserving the ability for resource-constrained nodes to participate in verification. This aligns with CryftNet's goal of Web2-like latency without sacrificing decentralization.
- **BitTorrent-style distribution:** DAS works like "BitTorrent with consensus"--data is erasure-coded and distributed across peers. Nodes sample random chunks and use cryptographic commitments (e.g., KZG polynomial commitments) to verify availability.

**Integration points:**

- **Region block producers** erasure-code block data and publish KZG commitments.
- **Region validators** perform DAS sampling before voting on block validity.
- **Main checkpoint verification** can optionally require DAS proofs that region data was available at checkpoint time.
- **Cryftee modules** can implement DAS sampling logic and commitment verification.

```text
DAS Verification (simplified):
1) Block producer computes erasure-coded chunks: C_1..C_n
2) Producer publishes KZG commitment: commit(C_1..C_n)
3) Sampler requests k random chunks from peers
4) Sampler verifies chunk inclusion against commitment
5) If >= threshold chunks verified, data is considered available
   with high probability (e.g., 99.9% with k=75 samples)
```

DAS is not mandatory for CSS-1 compliance but is recommended for high-throughput regions and for any chain seeking trustless light client support.

### 6.7 ZK-EVM integration for validity proofs

Zero-knowledge Ethereum Virtual Machines (ZK-EVMs) enable cryptographic proof-based validation of transaction batches. Instead of re-executing transactions, validators can verify a succinct proof that execution was performed correctly. This dramatically reduces computational load and enables trustless cross-chain verification.

**Current state (as of January 2026):**

ZK-EVMs have reached production-quality performance, with ongoing safety hardening. Full adoption as the primary validation method is expected between 2027 and 2030. CryftNet is positioned to adopt ZK proofs incrementally.

**ZK-EVM integration points in CryftNet:**

- **Checkpoint validity proofs:** Regions can attach ZK proofs to checkpoints, allowing Main to verify region state transitions without re-executing transactions. This enables:
  - Trustless light clients on Main
  - Reduced Main validator computational requirements
  - Faster checkpoint acceptance (verify proof vs. download and re-execute)

- **Cross-chain settlement:** ZK proofs can replace or supplement quorum signatures for cross-chain message verification, reducing trust assumptions from "2/3 of region validators are honest" to "the ZK proof system is sound."

- **Custom subnet bridging:** Non-EVM subnets can provide validity proofs for their state transitions, enabling trustless bridging to Main without requiring Main to understand the subnet's execution semantics.

- **CGS privacy proofs:** ZK proofs can attest to properties of private transactions (e.g., "this transfer is valid and the sender had sufficient balance") without revealing transaction details.

**Proof types supported:**

| Proof System | Use Case | Trade-offs |
|:-------------|:---------|:-----------|
| ZK-SNARK | Checkpoint validity, cross-chain proofs | Small proofs, fast verification; trusted setup or universal setup required |
| ZK-STARK | High-security applications, post-quantum | Larger proofs, no trusted setup, quantum-resistant |
| Hybrid | Recursive composition | Combine SNARK efficiency with STARK security for critical paths |

**Phased adoption roadmap:**

1. **Phase 1 (2026):** Optional ZK proofs for checkpoint verification; regions may provide proofs for faster Main acceptance.
2. **Phase 2 (2027-2028):** ZK-EVM provers integrated into Cryftee modules; CSS-1 regions encouraged to produce validity proofs.
3. **Phase 3 (2028-2030):** ZK proofs become the default verification method; quorum signatures retained as fallback and for governance.

```text
Checkpoint with ZK validity proof:
Checkpoint_ZK = {
  region_id: 42,
  chain_id: 1001,
  height: 8_240_112,
  block_hash: 0x...,
  state_root: 0x...,
  prev_state_root: 0x...,
  validity_proof: {
    type: "ZK_SNARK" | "ZK_STARK",
    proof: 0x...,
    public_inputs: [prev_state_root, state_root, block_hash],
    verifier_contract: 0xVerifier...
  },
  // quorum signature optional if validity_proof present
  quorum: { ... } | null
}
```

**Relationship to the blockchain trilemma:**

The combination of DAS (Section 6.6) and ZK-EVMs addresses the classic trilemma:

- **Decentralization:** DAS allows resource-constrained nodes to verify data availability; ZK proofs allow lightweight verification of execution.
- **Security:** Cryptographic proofs (KZG for DAS, ZK for execution) provide mathematical guarantees rather than economic/game-theoretic ones.
- **Scalability:** Larger blocks and parallel execution become viable when verification cost is decoupled from execution cost.

CRVS remains the consensus backbone--DAS and ZK-EVMs are complementary technologies that enhance what CRVS-based committees can achieve.

### 6.8 Path to production: making CRVS mainnet-ready

**Current status:** CRVS as described in sections 6.1-6.4 is a **proposal** that combines rotor-inspired propagation, votor-inspired voting, and Avalanche-style metastable sampling. While conceptually sound, it requires significant validation before mainnet deployment.

**The core challenge:** CRVS is currently a "stack of vibes"--combining multiple consensus patterns without:
- Formal safety and liveness proofs
- Simulation-derived parameter bounds
- Explicit fast/slow path transition rules
- Well-defined failure modes under various adversarial conditions

**Pragmatic de-risking strategy: "Proven core, experimental edges"**

The most practical path to mainnet is to:

1. **Use a proven consensus kernel** (the part that decides the canonical chain)
   - If building on AvalancheGo: Don't mutate the core Avalanche consensus until measured gains justify the risk
   - Consider: Avalanche consensus (proven) + optional networking/vote-aggregation optimizations

2. **Treat rotor relays as transport optimization only**
   - Never make relay functionality a safety requirement
   - Fallback to direct gossip must be seamless and well-tested

3. **Treat votor aggregation as compression of already-defined votes**
   - Not a new voting logic, but an optimization of vote collection
   - BLS aggregation or threshold schemes are well-understood; use them conservatively

4. **Leverage regionalization for "web2 feel" first**
   - Fast local committees and region-local confirmation provide low latency
   - Mainnet consensus can be conservative while still achieving user-facing speed

**Required deliverables before mainnet:**

| Artifact | Purpose | Status |
|:---------|:--------|:-------|
| **CRVS Specification (normative)** | Message types, state machine, timeouts, fork-choice, fast/slow triggers, finality definition, misbehavior definitions | ❌ TODO |
| **Failure Model Document** | Behavior under partitions, clock skew, relay censorship, 30% Byzantine | ❌ TODO |
| **Simulator + Parameter Campaign** | Test jitter, loss, topology, adversary strategies; measure safety incidents, liveness, bandwidth | ❌ TODO |
| **Testnet Acceptance Gates** | Define quantitative criteria: "No safety violations across X node-hours under Y adversary", "p95 finality < Z" | ❌ TODO |
| **External Security Review** | At least one independent audit of consensus logic and implementation | ❌ TODO |
| **Soak Test at Scale** | Multi-month testnet with real validator incentives and adversarial testing | ❌ TODO |

**Mainnet gating rule:**

CRVS is mainnet-eligible **only** when all of the following are complete:
1. ✅ Specification locked and published
2. ✅ Simulator results published showing safety/liveness under adversarial conditions
3. ✅ Soak test at scale (>=3 months, >=100 validators, adversarial scenarios)
4. ✅ External security review completed with all critical/high findings resolved
5. ✅ Fast/slow path transition rules validated through testing

**Recommended phases:**

| Phase | Focus | Consensus Approach |
|:------|:------|:-------------------|
| **Phase 0 (Current)** | Architecture design, simulation planning | Testnet only; proven baseline (Avalanche) |
| **Phase 1 (Spec + Sim)** | Complete CRVS spec, run parameter campaigns, identify safety bounds | Devnet with instrumented consensus |
| **Phase 2 (Testnet)** | Deploy CRVS on incentivized testnet with real economic stakes | Public testnet with fallback to proven consensus |
| **Phase 3 (Audit + Soak)** | External review, long-running adversarial testing | Pre-mainnet hardening |
| **Phase 4 (Mainnet)** | Production deployment with monitoring and governance escape hatches | Mainnet with conservative parameters |

**Open research questions (must resolve before Phase 2):**

- What are the exact parameter bounds for k, alpha, beta under various network conditions?
- How do fast/slow path transitions behave under oscillating network conditions?
- What is the fork probability under 20-30% Byzantine adversary with network partition?
- How does relay censorship affect time-to-finality, and what are the fallback performance characteristics?
- What monitoring and alerting infrastructure is needed to detect consensus degradation in production?

**Risk mitigation:**

- **Governance escape hatch:** Main governance can force-downgrade to slower but proven consensus if CRVS exhibits unexpected behavior
- **Regional experimentation:** Test CRVS on low-value regions before deploying to Main
- **Gradual rollout:** Enable CRVS features incrementally (propagation -> voting -> sampling) with ability to disable each layer
- **Telemetry requirements:** All CRVS nodes must report consensus metrics (vote latency, fork rate, relay performance) to monitoring infrastructure

Until these deliverables are complete, **web2-like latency comes from regionalization and fast local committees, not from unvalidated consensus innovation**.

---

## 7. Execution layer: EVM compatibility and deterministic parallelism

### 7.1 Baseline EVM mode

CryftNet remains compatible with standard EVM transactions. Legacy transactions are executed
serially and need not include any Cryft-specific fields. Standard wallets and tooling continue to work
unmodified.

### 7.2 Parallel execution mode (opt-in)

Parallel mode is opt-in. A transaction may declare that it participates in deterministic parallel
scheduling by including:
- **process_id:** identifies a workflow lane and namespace
- **slot_claims:** explicit read/write claims over state slots (consensus-critical, required for execution)
- **slot_commitment:** optional commitment hash over slot_claims for privacy-aware propagation via CGS (mempool transport only; revealed claims must be in block for execution)

### 7.3 Smart Slots and Process IDs (canonical model)

Smart Slots represent the smallest schedulable units of state contention. The goal is not to perfectly
capture every possible data dependency, but to capture enough structure that most real workloads
can safely parallelize while maintaining determinism.

#### 7.3.1 Slot types

- Account Slot: derived from an address. Used for nonce, balance, and code hash transitions. Any
transaction that modifies an account's nonce or balance claims WRITE on the account slot.
- Storage Slot: derived from (contract_address, storage_key). Claims map to EVM
SLOAD/SSTORE keys. A transaction that writes a given key claims WRITE on that slot; reads
claim READ.
- Object/Resource Slot: derived from an application resource ID (e.g., gift_code_id). Used when
an app wants parallelism without over-claiming whole accounts.
#### 7.3.2 Slot derivation

Slot IDs are computed by hashing a canonical encoding. The encoding includes a domain separator,
chain identity, scope, and type-specific data. Scope distinguishes Main from subnets (regions) and
prevents accidental collisions.
```text
slot_id = H(
  domain || chain_id || scope_id || process_id ||
  slot_type || addr || key || extra
)
Where:
- H() is keccak256 (or another fixed hash function) over bytes.
- domain is a constant ASCII tag, e.g., "CRYFT:SLOT:V1"
- chain_id identifies the chain (Main or subnet).
- scope_id = 0 for Main; = subnet_id (or region_id) for subnets.
- slot_type in {ACCOUNT, STORAGE, OBJECT}
- addr/key/extra are type-dependent fields.
Worked input composition examples (illustrative):
Example A (Account Slot): domain='CRYFT:SLOT:V1' | chain_id=1 | scope_id=0 | process_id='payment
Example B (Storage Slot): domain='CRYFT:SLOT:V1' | chain_id=1001 | scope_id=42 | process_id='gif
```

#### 7.3.3 Process IDs

A process_id identifies a workflow lane and its namespace. In the simplest case, process_id is a
human-readable string namespaced by the publisher, e.g., "cryft.giftcodes.v1". Governance may
reserve process_id prefixes for critical system workflows. A process_id can also be derived
deterministically from a contract address and ABI signature, but string-based IDs improve auditability.
#### 7.3.4 Transaction format extensions

Legacy transactions are unchanged. Parallel transactions add an envelope. Example (JSON-like):
```jsonc
// 1) Legacy transaction (unchanged)
{
  "type": "legacy",
  "from": "0xAlice",
  "to": "0xBob",
  "value": "0.05 ETH",
  "data": "0x",
  "gas": 21000,
  "nonce": 17
}

// 2) Parallel transaction with explicit slot claims
{
  "type": "cryft_parallel",
  "from": "0xAlice",
  "to": "0xGiftCodeContract",
  "value": "0",
  "data": "0x...",
  "gas": 100000,
  "nonce": 18,
  "process_id": "cryft.giftcodes.v1",
  "slot_claims": [
    {"slot_id": "0x1234...", "mode": "READ"},   // account slot for Alice
    {"slot_id": "0x5678...", "mode": "WRITE"},  // storage slot for gift code
    {"slot_id": "0xabcd...", "mode": "WRITE"}   // object slot for code_id
  ]
}
```

Smart Slots build on the mental model of [EIP-2930 access lists](https://eips.ethereum.org/EIPS/eip-2930): addresses and storage keys are already familiar to Ethereum developers. Object slots extend this to application-defined resources, reducing "newness tax" and improving tooling compatibility.

#### 7.3.5 Under-claiming enforcement (deterministic access-trace validation)

**The problem:** If a transaction under-claims its access set (e.g., claims to read slot A but actually reads slots A and B), determinism breaks. Different validators may schedule the transaction in different parallel lanes, observe different states, and produce different state roots--**causing chain splits**.

**Solution: Runtime access-trace enforcement**

When a transaction opts into Smart Slots, the VM records the actual accessed set during execution:
- **Accounts touched:** Any address whose nonce, balance, or codehash was read or written
- **Storage slots accessed:** All SLOAD/SSTORE keys (contract_address, storage_key)
- **Object slots accessed:** Application-defined resource IDs (if used)

**Enforcement rule (deterministic):**

```text
After execution:
  actual_access = set of all slots the transaction actually touched
  claimed_access = set of all slots in slot_claims

  IF actual_access ⊄ claimed_access THEN
    tx is INVALID as parallel
    CHOOSE enforcement policy:
      [A1] REVERT + penalty (strictest; best for consensus safety)
      [A2] FALLBACK to serial lane (best UX; more scheduler complexity)
```

**Policy A1: Revert + penalty (recommended for consensus safety)**
- Transaction execution is reverted (no state changes applied)
- Gas is consumed up to the point of under-claim detection
- Optional: charge an additional penalty fee for wasting parallel capacity
- Receipt includes: `status: "REVERTED_UNDERCLAIM"`, `access_hash: H(actual_access)`

**Policy A2: Deterministic fallback to serial lane (best UX)**
- Transaction is removed from parallel scheduler
- Re-executed in the serial lane at end of block
- Fallback order is deterministic: txs are appended to serial tail in `tx_hash` order
- Extra fee charged for wasting parallel capacity
- Receipt includes: `underclaimed: true`, `execution_mode: "SERIAL_FALLBACK"`, `access_hash: H(actual_access)`

**Why this is safe:**

1. **No fraud proofs needed:** Detection happens during execution, not post-hoc
2. **No subjective disputes:** "You claimed X, you touched Y" is a fact, not an opinion
3. **No external oracles:** The VM itself is the source of truth
4. **Deterministic:** All validators follow the same rule and reach the same conclusion
5. **Compatible with legacy txs:** Legacy transactions don't opt into Smart Slots, so they're unaffected

**Relationship to EIP-2930 access lists:**

Smart Slots generalize EIP-2930's concept:
- **EIP-2930:** Optional access lists to reduce gas costs (warm vs. cold SLOAD)
- **Smart Slots:** Mandatory claims for parallel execution, with enforcement

This reduces "newness tax"--Ethereum developers already understand the mental model of declaring accessed addresses and storage keys. Object slots are "extra lanes" for app-defined resources.

**Implementation sketch:**

```text
Execution trace validation (simplified):
1) VM begins execution of tx with slot_claims = [S1, S2, ...]
2) During execution, VM maintains access_log = []
3) On every state access (account read/write, SLOAD/SSTORE):
     slot_id = derive_slot_id(access_type, address, key)
     IF slot_id NOT IN slot_claims THEN
       record_underclaim(slot_id)
4) After execution:
     IF underclaim_detected THEN
       apply_enforcement_policy(tx, access_log)
     ELSE
       commit_state_changes()
```

**Cost analysis:**

- **Overhead:** ~5-10% execution slowdown due to access logging (acceptable for parallel gain)
- **Storage:** Access logs are ephemeral (discarded after block finalization); receipts store only `access_hash`
- **Gas:** Under-claimed txs pay for wasted parallel scheduler capacity

**Fallback policy recommendation:**

For **Phase 1 (testnet):** Use Policy A1 (revert + penalty) to surface under-claiming issues early and force tooling to improve.

For **Phase 2 (mainnet):** Consider Policy A2 (fallback to serial) for better UX, but only after scheduler complexity is validated.

**Escape hatch:**

If a contract legitimately cannot predict its access set (e.g., dynamic dispatch based on block.timestamp), it should:
- Not opt into Smart Slots, OR
- Use a conservative over-claim (claim all possible slots), OR
- Execute in serial lane explicitly
