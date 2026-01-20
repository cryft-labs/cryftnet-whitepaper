to ensure their validator sets are actually region-serving. Validators may participate in Main and in
multiple regions, but each region can enforce its own RTT thresholds and scoring. Mitigations against
gaming include: multi-beacon diversity, random challenge timing, cross-check pings from validators to
each other, and penalties for detected proxy/VPN abuse.
```

### 5.3 User routing and failover

Clients choose a region through a combination of DNS hints, signed region metadata (published on
Main), and direct latency probing. If a region degrades (beacon reports, missed blocks, or poor p95),
clients fail over to a nearby region or to the Main chain for safety-critical operations. Regions can also
choose to temporarily increase anchoring frequency to Main during instability.

### 5.4 Diminishing returns: why committee size has a ceiling

For a fixed network, increasing validators increases message fanout and signature verification cost.
Beyond a point, latency improves more by splitting into regions than by growing a single committee.
CryftNet therefore expects: - Main: moderate committee size optimized for security and global
settlement cadence. - Regions: smaller committees optimized for p50/p95 latency. - Local chains:
smallest committees, often for specialized workloads.

### 5.5 Optional overlay mesh transport (Nebula reference implementation)

CryftNet's *architecture* only assumes an authenticated, low-jitter transport between validators and supporting services (Cryftee, beacons, pin auditors). It does **not** require any specific overlay network. However, an overlay mesh can be a pragmatic way to:

- reduce reliance on public IP exposure (validators can keep private addressing and still form a stable mesh),
- enforce mutual authentication and segmentation via cryptographic identities and groups,
- standardize private service discovery for operator tooling and Cryftee modules (UDS/HTTPS endpoints),
- provide an operational "back channel" for upgrades, telemetry, and incident response.

A concrete candidate is **Nebula** (a WireGuard-style encrypted mesh with lighthouses and optional relays). Recommended stance:

- **Consensus plane:** prefer direct, performance-tuned UDP/QUIC links on public or private underlay whenever possible. If Nebula is used for consensus traffic, it should be *measured* and treated as a tunable deployment choice because overlays can add jitter and introduce relay-path outliers.
- **Control plane:** Nebula is an excellent fit (Cryftee management API, beacons, pin-auditor coordination, internal RPC, dashboards), because security and operability dominate micro-latency.

Latency note: Nebula typically adds only small per-packet overhead (encryption + encapsulation). The real risk is *path inflation* when traffic hairpins through lighthouses/relays or when MTU issues cause fragmentation. These risks should be monitored via the existing ping/eligibility telemetry and treated like any other transport variable.

Security note: the main advantage is **cryptographic identity at the network layer** (mutual auth, key rotation, segmentation) and the ability to keep services non-public while still reachable by authorized peers. It is not a substitute for protocol-layer authentication; it is a defense-in-depth layer.

---

## 6. Consensus and finality model (CRVS proposal)

CryftNet's consensus design aims to combine fast propagation, low coordination overhead, and rapid
finality within regions. We propose a stack nicknamed CRVS: Cryft Rotor-Votor Snow. It combines: -
Rotor-like propagation: efficient dissemination of candidate blocks and transaction data using rotating
relay roles. - Votor-like voting: fast-path vote aggregation for quick finality and slow-path recovery
during partial synchrony. - Avalanche-style metastable sampling: leaderless or low-leader
coordination where nodes repeatedly sample peers and converge on a preferred candidate with high
probability.

### 6.1 Data propagation plane (rotor-inspired)

Propagation is about moving bytes, not deciding truth. CRVS uses rotating relays to reduce
redundant broadcast. Relays are chosen deterministically per round (e.g., hash of epoch, round, and
validator key). Relays are not authorities: they only accelerate dissemination. If relays fail or censor,
fallback is direct gossip.
Inputs:
- committee V of size n
- round r within epoch e

- relay_count t (e.g., 3-7)
```text
RelaySet(e,r) = smallest t validators by score( H("relay"||e||r||vk) )
Protocol:
1) proposer sends candidate header to RelaySet(e,r)
2) relays fetch missing tx data by content hash and broadcast compact references
3) peers request missing chunks; relays respond; peers also serve each other
Fallback: if relay responsiveness drops below threshold, revert to all-to-all gossip.
```

### 6.2 Candidate production: leaderless or soft-leader

CRVS can run in a leaderless mode where multiple proposers may submit candidate blocks for the
same slot. The network then converges on one candidate via voting/sampling. A soft-leader variant
reduces forks by selecting a preferred proposer, but nodes remain free to accept alternatives if the
leader is slow or censored.
Slot s:
- Any validator may propose candidate C = (header, tx_list, parent_ref)
- Valid candidates are those with valid parent_ref, correct block time window, and valid txs.
Deterministic tie-break:
```text
PreferredCandidateSet = all valid candidates seen within Δpropagate (within the propagation window)
Rank(C) = (slot s, H(C.header), proposer_vk)
Choose smallest Rank among candidates that reach vote threshold.
```

### 6.3 Voting and finality (votor-inspired fast/slow paths)

Voting determines finality. CRVS uses a two-path structure: Fast path: when network is healthy and
participation is high, validators aggregate votes quickly to finalize a candidate. Slow path: when
participation is partial or network is unstable, the protocol falls back to repeated rounds and higher
confirmation thresholds before finalizing. Votes are signed; aggregation may use BLS signatures to
reduce bandwidth, or threshold aggregation via Cryftee modules.
Definitions:
- quorum_fast = ceil(0.67 * n)          # target; tunable by governance
- quorum_slow = ceil(0.80 * n)          # more conservative
- rounds_fast = 1..2
- rounds_slow = up to Rmax (e.g., 8)
Fast path:
1) collect votes for candidate C during round r
2) if votes(C) >= quorum_fast and no conflicting candidate with >= quorum_fast, finalize C
Slow path:
1) repeat vote rounds; if conflict persists, prefer candidate with higher confidence score from
2) finalize when votes(C) >= quorum_slow for consecutive k rounds (k >= 2)

### 6.4 Metastable sampling (Avalanche-inspired)

**Core mechanism:** Validators refine their preference for a candidate by repeatedly sampling a small subset of peers and asking "Which candidate do you currently prefer for slot s?" If a candidate consistently receives majority support across consecutive samples, confidence increases until finalization.

**State machine per validator for slot s:**

```text
States:
  UNDECIDED        -> No preferred candidate yet
  PREFERRED(C)     -> Currently prefer candidate C, confidence < finalization threshold
  FINALIZED(C)     -> Committed to candidate C, irreversible

Transitions:
  UNDECIDED -> PREFERRED(C):  
    When first valid candidate C seen and passes initial checks
  
  PREFERRED(C) -> PREFERRED(C'):  
    If sampled peers strongly prefer C' over C (churn threshold crossed)
  
  PREFERRED(C) -> FINALIZED(C):  
    When confidence(C) >= beta consecutive rounds with alpha/k threshold met
  
  FINALIZED(C) -> (terminal):  
    No further state changes for this slot
```

**Sampling algorithm:**

```text
Parameters:
  k = 20        # sample size per round
  alpha = 15    # acceptance threshold (must have >= alpha votes for C)
  beta = 12     # consecutive successful rounds needed to finalize
  delta_sample = 200ms  # time between sample rounds

Per-slot state:
  preferred_candidate = None
  confidence[C] = 0 for all candidates
  round_number = 0

Loop until finalized:
  round_number += 1
  
  // Sample k random peers from committee
  peers = random_sample(committee, k)
  
  // Query each peer for their current preference
  responses = query_peers(peers, "preferred_candidate_for_slot", s)
  
  // Count votes for each candidate
  vote_counts = count_by_candidate(responses)
  C_max = candidate_with_most_votes(vote_counts)
  
  // Check if C_max meets acceptance threshold
  if vote_counts[C_max] >= alpha:
    if C_max == preferred_candidate:
      confidence[C_max] += 1
    else:
      // Switch preference if new candidate has strong support
      preferred_candidate = C_max
      confidence[C_max] = 1
      confidence[other candidates] = 0
  else:
    // No clear leader this round, decay confidence
    confidence[preferred_candidate] = max(0, confidence[preferred_candidate] - 1)
  
  // Check for finalization
  if confidence[preferred_candidate] >= beta:
    FINALIZE(preferred_candidate)
    broadcast_finalization_vote(preferred_candidate)
    return
  
  sleep(delta_sample)
```

**Fork-choice rule (deterministic tie-breaking):**

When multiple valid candidates exist for the same slot:

```text
Rank(C) = (C.slot, keccak256(C.header), C.proposer_vk)

Preference order:
  1. Candidate with highest confidence score
  2. If tied, candidate with most recent successful sample round
  3. If still tied, candidate with smallest Rank() value

This ensures deterministic convergence even under adversarial candidate spam.
```

**Safety properties:**

- **Finalization is irreversible:** Once a validator finalizes candidate C for slot s, it will never accept C' != C for that slot
- **No conflicting finality under honest majority:** If >50% of validators are honest and network is eventually synchronous, no two honest validators will finalize different candidates for the same slot
- **Metastability convergence:** Once a supermajority prefers C, the sampling dynamics amplify that preference, making it exponentially unlikely for the network to switch to C'

**Liveness properties:**

- **Guaranteed progress under GST:** After Global Stabilization Time (GST), when network delays are bounded and >50% validators are honest, the network will finalize some candidate for every slot
- **Timeout-based fallback:** If confidence for any candidate fails to reach beta after T_max rounds (e.g., 30 rounds ~= 6 seconds), validators may propose a new candidate with stronger guarantees or enter recovery mode

**Adversary resilience:**

| Adversary % | Impact | Mitigation |
|:------------|:-------|:-----------|
| <15% | Minimal impact; may slow finality by 1-2 rounds | Sampling dynamics dominate |
| 15-30% | Can delay finality; cannot create conflicting forks under partial synchrony | Slow path activates, quorum thresholds increase |
| 30-49% | Can delay finality significantly; cannot break safety | Manual recovery may be required; governance intervention |
| >=50% | Can halt network or create forks | Safety assumption violated; chain is insecure |

**Hysteresis rules (prevent oscillation):**

To prevent validators from thrashing between candidates C and C' when sampling results are marginal:

```text
Preference switch rule:
  Current preference: C
  New candidate: C'
  
  Switch to C' only if:
    1. vote_counts[C'] >= alpha (meets threshold), AND
    2. vote_counts[C'] > vote_counts[C] + hysteresis_gap, where hysteresis_gap = 3
    
  Example: If C has 14 votes and C' has 16 votes (diff=2 < gap=3), don't switch yet.
           If C has 13 votes and C' has 17 votes (diff=4 > gap=3), switch to C'.

This adds "stickiness" to preferences, reducing churn from sampling noise.
```

**Fast path vs slow path triggers:**

```text
Fast path active when:
  - Network health score >= 0.85 (based on recent round-trip times, relay availability)
  - No conflicting candidates with >= quorum_fast votes
  - Participation rate >= 0.90 (>90% of validators responding to samples)
  
  Fast path finalization: beta_fast = 8 consecutive rounds with alpha = 15 out of k = 20

Slow path activated when:
  - Network health score < 0.85, OR
  - Multiple candidates have >= quorum_fast/2 votes (fork contention), OR
  - Participation rate < 0.90
  
  Slow path finalization: beta_slow = 15 consecutive rounds with alpha = 17 out of k = 20
  
Hysteresis between paths:
  - Once slow path is activated, require 10 consecutive "healthy" rounds before returning to fast path
  - This prevents rapid oscillation between modes during marginal network conditions
```

**Clock skew handling:**

Validators tolerate clock drift up to ±500ms. If a validator's clock is skewed beyond this:
- Its sampling queries may time out (peers reject queries for "future" or "stale" slots)
- It will observe low response rates and may enter slow path or fallback mode
- Monitoring alerts trigger if clock skew is detected (via NTP health checks)

**Assumptions:**

- **Partial synchrony:** After unknown GST, message delays bounded by Δ_max = 10 seconds
- **Clock drift:** <500ms between validators (enforced via NTP monitoring)
- **Adversary bound:** <30% Byzantine validators (safety); <50% required for liveness
- **Network model:** Eventually message delivery; routers may censor but cannot forge validator signatures

**Failure modes:**

| Condition | Behavior | Recovery |
|:----------|:---------|:---------|
| Network partition (>30% isolated) | Minority partition halts; majority continues | Partition heals -> minority re-syncs to majority chain |
| Clock skew >500ms on >30% validators | Slow path activates; finality degrades to ~10-15s | NTP fixes -> fast path resumes |
| All relays censored/offline | Fallback to direct gossip; 2-5x bandwidth increase | Relay election rotates; new relays selected |
| Adversary spams candidates | Fork-choice rule deterministically selects one; sampling converges | No persistent impact; spam filtered by gas limits |
| Confidence never reaches beta | Timeout after 30 rounds -> manual intervention or proposer rotation | Governance investigation; potential config adjustment |

**Relationship to Avalanche consensus:**

CRVS borrows Avalanche's metastable sampling core (k, alpha, beta parameters; repeated peer queries; confidence accumulation) but differs in:
- **Propagation layer:** Avalanche uses all-to-all gossip; CRVS uses rotor relays with fallback
- **Vote aggregation:** CRVS optionally uses BLS signature aggregation (votor-inspired); Avalanche doesn't aggregate
- **Fast/slow path logic:** Explicit dual-path design vs Avalanche's single parameterization
- **Integration:** CRVS is designed for a three-chain federated system; Avalanche is for independent subnets

**What's not proven (yet):**

This design is a **proposal**. Before mainnet:
- Formal safety proof under partial synchrony model
- Simulation results showing convergence under adversarial network conditions
- Parameter sensitivity analysis (how much do k, alpha, beta changes affect safety/liveness?)
- Testnet soak test with real economic incentives and adversarial validators

See Section 6.8 for the complete path to production readiness.

### 5.6 Chain IDs and RPC compatibility (v1 normative spec)

**Critical for Web2-like UX:** Wallets, dApps, and tooling must seamlessly interact with Primary Network chains (Federal, Mirror, EVM) and regional State/City chains. This requires precise chain ID conventions, discovery mechanisms, and RPC behavior specifications.

#### 5.6.1 Chain ID conventions (EIP-155 compliant)

**Primary Network chain IDs (reserved range 1-99):**

```text
Federal Chain:  chainId = 1  (canonical governance/staking chain)
Mirror Chain:   chainId = 2  (native assets/GBL/UTXO chain)
EVM Chain:      chainId = 3  (smart contracts/CMR/Main execution)
```

**State/Region chain IDs (range 1000-999999):**

```text
Format: 1000 + region_id

Examples:
  Region 1 (e.g., US-East):     chainId = 1001
  Region 42 (e.g., EU-Central): chainId = 1042
  Region 500 (e.g., APAC):      chainId = 1500

Maximum: region_id < 999000 (reserved)
```

**City chain IDs (range 1000000-9999999):**

```text
Format: 1000000 + (parent_region_id * 1000) + city_local_id

Examples:
  Region 1, City 5:  chainId = 1001005
  Region 42, City 12: chainId = 1042012
  Region 500, City 3: chainId = 1500003

Constraints:
  - parent_region_id < 9000 (max 8999 regions)
  - city_local_id < 1000 (max 999 cities per region)
```

**Custom subnet chain IDs (range 10000000+):**

Custom (non-CSS) subnets choose chain IDs >= 10000000 during Federal Chain registration. Collisions rejected at registration time.

**Replay protection invariant:**

All chains use **EIP-155 replay protection**. Transactions signed for chainId=1001 (Region 1) cannot be replayed on chainId=1042 (Region 42) or chainId=3 (EVM Chain). This is enforced at transaction validation (v, r, s signature check includes chainId).

**Version marker: (v1) All chain ID conventions and RPC specs are mainnet-required and implemented.**
