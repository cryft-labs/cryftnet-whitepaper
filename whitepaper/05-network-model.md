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

### 5.7 Operational SLOs and monitoring (CSS-1 enforcement mechanisms)

**Critical for "Web2 feel" claim:** Latency targets and health scores are only meaningful if they're **measurable, enforced, and have consequences**.

This section transforms operational metrics from aspirational to protocol-enforced via CSS-1 compliance requirements.

#### 5.7.1 CSS-1 required metrics (normative specification)

All CSS-1 compliant State chains MUST expose the following metrics via standardized endpoints:

**1. Latency metrics (measured via ping beacons and client telemetry):**

| Metric | Measurement Method | SLO Target | Reporting Frequency |
|:-------|:------------------|:-----------|:--------------------|
| **p50 block latency** | Time from tx submission to block inclusion | <500ms | Every epoch (~10 min) |
| **p95 block latency** | 95th percentile latency | <2000ms | Every epoch |
| **p99 block latency** | 99th percentile latency | <5000ms | Every epoch |
| **Inter-validator RTT** | Round-trip time between validator pairs | <100ms for 67% of pairs | Continuous (5min windows) |
| **RPC response time** | eth_sendRawTransaction to receipt | p95 <3000ms | Every epoch |

**2. Availability metrics:**

| Metric | Measurement Method | SLO Target | Reporting Frequency |
|:-------|:------------------|:-----------|:--------------------|
| **Validator uptime** | Missed block proposals + checkpoint signatures | >95% per validator | Every epoch |
| **RPC endpoint availability** | HTTP 200 responses to health checks | >99.5% uptime | Every 5 minutes |
| **Checkpoint submission success rate** | Successful Federal Chain checkpoint acceptance | >99% of attempts | Every checkpoint |
| **Peer connectivity** | Reachable validator peers | >80% of validator set | Continuous |

**3. Throughput metrics:**

| Metric | Measurement Method | SLO Target | Reporting Frequency |
|:-------|:------------------|:-----------|:--------------------|
| **Transactions per second (TPS)** | Committed txs / time window | >100 TPS sustained | Every epoch |
| **Gas throughput** | Gas used per block | >30M gas/block (EVM equivalent) | Every epoch |
| **Cross-region message processing** | Messages accepted from other regions | >95% acceptance rate | Every checkpoint |

**4. Jitter and stability metrics:**

| Metric | Measurement Method | SLO Target | Reporting Frequency |
|:-------|:------------------|:-----------|:--------------------|
| **Block time variance** | Std dev of block times | <200ms from target | Every 100 blocks |
| **Missed blocks** | Proposed blocks not finalized | <1% of blocks | Every epoch |
| **Fork rate** | Conflicting blocks at same height | <0.01% | Every epoch |

#### 5.7.2 Measurement infrastructure (how metrics are collected)

**Ping Beacon Network (Federal Chain operated):**

`	ext
Architecture:
- 20-50 geographically distributed beacon nodes
- Each beacon pings all CSS-1 validators every 30 seconds
- Beacons report RTT measurements to Federal Chain (on-chain registry)
- Median of 3-5 beacons used to avoid single-beacon bias

Beacon selection:
- Operated by diverse entities (Cryft Labs, infrastructure providers, DAO-funded)
- Geographic distribution: NA (5), EU (5), APAC (5), SA (2), Africa (2), Oceania (1)
- Beacon operators bonded (slashed for false reporting)

Data structure (on-chain):
PingReport {
  beacon_id: 0xBeacon,
  region_id: 1042,
  validator_pubkey: 0xValidator,
  epoch: 12345,
  rtt_samples: [42ms, 45ms, 44ms, 43ms, 41ms],  // 5 samples over epoch
  median_rtt: 43ms,
  p95_rtt: 45ms,
  packet_loss: 0.0,
  timestamp: 1737331200,
  beacon_sig: Sign(...)
}
`

**Client Telemetry (opt-in, privacy-preserving):**

`	ext
Wallets and dApp frontends can opt-in to report anonymized latency metrics:

TelemetryReport {
  region_id: 1042,
  client_type: "metamask" | "custom",
  sample_count: 100,  // aggregated over 1 hour
  p50_latency: 420ms,
  p95_latency: 1800ms,
  p99_latency: 4200ms,
  error_rate: 0.02,   // 2% of requests failed
  anonymized_id: hash(user_id + salt),  // cannot track individual users
  timestamp: ...
}

Reported to: Public dashboard (aggregated), Federal Chain (digest only)
Privacy: No PII, IP addresses, or transaction details
`

**Validator Self-Reporting (required for CSS-1):**

`	ext
Validators MUST publish health metrics to Federal Chain every epoch:

ValidatorHealthReport {
  validator_pubkey: 0xValidator,
  region_id: 1042,
  epoch: 12345,
  
  // Block production
  blocks_proposed: 142,
  blocks_finalized: 140,
  blocks_missed: 2,
  
  // Consensus participation
  checkpoint_signatures_submitted: 144,
  checkpoint_signatures_expected: 144,
  
  // Peer connectivity
  connected_peers: 18,
  expected_peers: 20,
  
  // Resource usage (optional, for capacity planning)
  avg_cpu_usage: 0.45,
  avg_memory_gb: 28.2,
  disk_iops: 5000,
  
  validator_sig: Sign(...)
}

Verification: Federal Chain compares self-report to beacon data (detect lying)
`

#### 5.7.3 SLO violation consequences (enforceable penalties)

**Problem:** Metrics without consequences are ignored.

**Solution: Tiered penalty system based on severity and duration**

**Tier 1: Performance Degradation (p95 latency >2s for 3+ consecutive epochs)**

**Consequences:**
- **Routing deprioritization**: RPC load balancers automatically reduce traffic to slow regions (70%  50%  30%)
- **User warnings**: Wallets display "Region 1042 is experiencing high latency" banner
- **Validator alerts**: Discord/Telegram alerts to region operators ("Fix within 24h or face Tier 2")
- **No slashing**: Temporary performance issues don't lose stake

**Mechanism:**
`solidity
// Federal Chain SLO Monitor
if (p95_latency[region_id][last_3_epochs] > 2000ms) {
    regionHealth[region_id] = DEGRADED;
    emit PerformanceDegraded(region_id, p95_latency[region_id]);
    
    // RPC providers listen to this event and adjust routing weights
}
`

**Tier 2: Sustained SLO Violation (p95 >2s for 10+ consecutive epochs OR uptime <90%)**

**Consequences:**
- **Reward haircut**: Validator rewards reduced by 25% during violation period
- **Checkpoint fee increase**: Region pays 2x normal checkpoint submission fee (incentive to fix)
- **Public dashboard warning**: Region marked "Not recommended" on official network status page
- **DAO notification**: Automated governance proposal created ("Should Region 1042 be suspended?")

**Mechanism:**
`solidity
if (sustained_violation_count[region_id] >= 10) {
    // Apply reward haircut
    validatorRewardMultiplier[region_id] = 0.75;  // 25% reduction
    checkpointFeeMultiplier[region_id] = 2.0;     // 2x fees
    
    // Create DAO proposal for suspension vote
    createGovernanceProposal(
        title: "Suspend Region 1042 for sustained SLO violations?",
        description: "p95 latency >2s for 10 epochs...",
        vote_duration: 7 days
    );
    
    emit SustainedViolation(region_id, violation_count);
}
`

**Tier 3: Critical Failure (uptime <50% OR 24h outage OR fraud detected)**

**Consequences:**
- **Temporary suspension**: Region cannot submit checkpoints (blocks cross-region transfers)
- **Validator slashing**: 2% stake slash for all region validators
- **Emergency DAO vote**: 72h fast-track vote to decide permanent removal or recovery plan
- **User fund protection**: Emergency exit mechanism activated (see Section 4.4.1 City fraud proofs)

**Mechanism:**
`solidity
if (uptime[region_id][last_epoch] < 0.5 || outage_duration > 24 hours) {
    // Immediate suspension
    regionStatus[region_id] = SUSPENDED;
    
    // Slash all validators
    for (validator in regionValidators[region_id]) {
        slashValidator(validator, SLASHING_RATE_SLO_CRITICAL); // 2%
    }
    
    // Emergency DAO vote (72h timeline)
    createEmergencyProposal(
        title: "Region 1042 critical failure - recover or remove?",
        options: ["Grant 7-day recovery period", "Permanent removal", "Emergency coordinator takeover"],
        fast_track: true,
        vote_duration: 72 hours
    );
    
    emit CriticalFailure(region_id, reason);
}
`

#### 5.7.4 Recovery and rehabilitation process

**Problem:** Penalized regions need a path to restore good standing.

**Solution: Staged recovery with proof-of-improvement**

**Stage 1: Diagnosis (0-48 hours)**
- Region operators identify root cause (hardware, network, software bug, attack)
- Submit incident report to DAO forum (public transparency)
- Cryft Labs or community volunteers offer technical assistance (if requested)

**Stage 2: Fix and validation (48h-7 days)**
- Implement fixes (upgrade hardware, optimize software, change validators)
- Run 24h "recovery period" with monitoring (no penalties, but no rewards either)
- Beacon network validates improvement (3 consecutive epochs with p95 <1.5s)

**Stage 3: Probation (7-30 days)**
- Region restored to full status (checkpoints accepted, routing restored)
- Reward haircut reduced gradually (75%  85%  95%  100% over 30 days)
- Enhanced monitoring (5min reporting windows instead of 10min)
- Second violation within probation  immediate Tier 3 (no second chance)

**Stage 4: Full restoration (Day 30+)**
- All penalties removed
- Normal SLO monitoring resumes
- Incident post-mortem published to DAO (learning for other regions)

**Code enforcement:**
`solidity
function requestRecovery(uint64 region_id, string calldata incident_report) external {
    require(msg.sender == regionOperator[region_id], "Unauthorized");
    require(regionStatus[region_id] == SUSPENDED || regionHealth[region_id] == DEGRADED, "Not in violation");
    
    // Enter recovery period (24h validation)
    regionStatus[region_id] = RECOVERING;
    recoveryStartTime[region_id] = block.timestamp;
    
    emit RecoveryRequested(region_id, incident_report);
}

function validateRecovery(uint64 region_id) external {
    require(regionStatus[region_id] == RECOVERING, "Not in recovery");
    require(block.timestamp >= recoveryStartTime[region_id] + 24 hours, "Recovery period not complete");
    
    // Check if SLOs met during recovery period
    bool slos_met = (
        p95_latency[region_id][last_3_epochs] < 1500ms &&
        uptime[region_id][last_3_epochs] > 0.95
    );
    
    if (slos_met) {
        regionStatus[region_id] = PROBATION;
        probationStartTime[region_id] = block.timestamp;
        validatorRewardMultiplier[region_id] = 0.75;  // Start at 75%, increases over 30 days
        emit RecoverySuccessful(region_id);
    } else {
        // Recovery failed, back to suspended
        regionStatus[region_id] = SUSPENDED;
        emit RecoveryFailed(region_id);
    }
}
`

#### 5.7.5 Public SLO dashboard (transparency and accountability)

**Real-time monitoring interface:**

`	ext
URL: https://status.cryftnet.io

Features:
- Live p50/p95/p99 latency for all CSS-1 regions (updated every 10min)
- Validator uptime % (color-coded: green >95%, yellow 90-95%, red <90%)
- Region health status (HEALTHY, DEGRADED, RECOVERING, SUSPENDED)
- Historical performance charts (7-day, 30-day, 90-day views)
- Incident timeline (past violations, recovery events, DAO votes)
- Comparison table (sort regions by latency, uptime, TPS)

User benefits:
- Developers: Choose best region for their dApp deployment
- End users: Wallets auto-route to highest-performance regions
- Validators: Benchmark their performance against peers
- Investors/auditors: Verify network is delivering on "Web2 feel" promise

Data sources:
- Federal Chain on-chain SLO registry (authoritative)
- Beacon network measurements (real-time)
- Client telemetry aggregates (community-reported)
- Validator self-reports (cross-validated)
`

**Dashboard API (for wallet/tooling integration):**

`	ypescript
// Example: MetaMask queries best region for user location
GET /api/v1/regions/recommend?lat=40.7128&lon=-74.0060&min_uptime=0.95

Response:
{
  "recommended_regions": [
    {
      "region_id": 1001,
      "name": "US-East",
      "chainId": 1001,
      "estimated_rtt_ms": 45,
      "p95_latency_ms": 1200,
      "uptime_7d": 0.998,
      "health_status": "HEALTHY",
      "rpc_endpoints": ["https://rpc-us-east.cryftnet.io", ...]
    },
    {
      "region_id": 1002,
      "name": "US-Central",
      "estimated_rtt_ms": 62,
      "p95_latency_ms": 1450,
      "uptime_7d": 0.995,
      "health_status": "HEALTHY",
      ...
    }
  ],
  "fallback_region": {
    "region_id": 3,  // EVM Chain (always available)
    "name": "Primary Network EVM",
    "estimated_rtt_ms": 120,
    ...
  }
}
`

**Enforcement summary:**

| Violation Type | Detection | Consequence | Recovery Time |
|:---------------|:----------|:------------|:--------------|
| Transient slowdown (<3 epochs) | Beacon network | Routing deprioritization, user warnings | Automatic (once p95 <2s) |
| Sustained degradation (10+ epochs) | Beacon + validator reports | 25% reward haircut, 2x checkpoint fees, DAO alert | 7-30 days (probation) |
| Critical failure (24h outage) | Missed checkpoints | 2% validator slash, suspension, emergency DAO vote | 7+ days (incident review) |
| Fraud (fake metrics) | Cross-validation (beacon vs. self-report) | 10% validator slash, immediate removal, funds clawback | Permanent ban |

**Key insight:** This transforms "Web2 feel" from marketing into **enforceable protocol-level guarantees with real consequences**, making CryftNet's latency claims auditable and trustworthy.

