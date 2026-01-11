- Implement partitioned balance contracts with transferToRegion() and claimFromRegion().
- Implement balance portability modes (region-locked, portable, replicated).
- Implement transfer_id generation, tracking, and replay protection.
- Add receipt extensions for parallel txs and commitment verification for CGS reveal.
- Implement region checkpoint producer and submitter to Main (including cross-region message roots).
- Implement ping beacon set governance and eligibility scoring.
- Implement cross-region transfer timeout and refund mechanism.
- Implement State Balance Ledger (SBL) for City balance tracking.
- Implement City registration via State (not Main).
### 15.4 Milestone 3: CGS and private intents

- Implement CGS core service in Cryftee runtime (routing, pools, key rotation cadence).
- Implement private_sync_v1 module support for domains, parties, tx submit/confirm, view
requests.

- Implement slot commitment workflow: IntentEnvelope -> RevealClaims -> scheduler -> execution.
- Implement dispute bundles and evidence retention policies.
- Add observability: metrics, dashboards, and privacy leak tests (timing correlation).
### 15.5 Milestone 4: CRVS consensus validation (CRITICAL PATH)

**This milestone gates mainnet deployment.** CRVS must move from "proposal" to "production-ready" through rigorous validation.

**Deliverables:**

- **CRVS formal specification** (normative document):
  - Complete state machine with message types and transitions
  - Explicit timing assumptions (partial synchrony bounds, clock drift tolerance)
  - Fork-choice rule with deterministic tie-breaking
  - Fast/slow path transition triggers (quantitative thresholds, not heuristics)
  - Finality definition (soft vs hard, cross-region implications)
  - Misbehavior definitions with slashing criteria (equivocation, withholding, invalid votes)
  - Safety and liveness properties with formal proofs or bounded analysis

- **Failure mode analysis**:
  - Behavior under network partitions (1-way, 2-way, oscillating)
  - Clock skew tolerance bounds (max drift before safety violations)
  - Relay censorship scenarios (centralized, coordinated, random)
  - Byzantine adversary models (20%, 30%, adaptive)
  - Edge cases: simultaneous forks, quorum split, stuck finalizer

- **Consensus simulator**:
  - Network topology models (mesh, hierarchical, lossy links)
  - Configurable jitter, packet loss, bandwidth constraints
  - Adversary strategies (withholding, equivocation, timing attacks)
  - Metrics: fork probability, time-to-finality (p50/p95/p99), bandwidth usage, vote efficiency
  - Parameter campaign outputs: validated ranges for k, alpha, beta, quorum thresholds

- **Testnet acceptance gates** (quantitative criteria):
  - No safety violations across >=10,000 simulated validator-hours under 30% Byzantine adversary
  - p95 finality < 3 seconds under normal conditions (< 5% packet loss, < 100ms jitter)
  - Graceful degradation: partition recovery without permanent lock within 2 epochs
  - Relay failure: fallback to direct gossip increases latency by < 50% (not ∞)
  - Fast/slow path transition: no oscillation under simulated variable network conditions

- **External security review**:
  - At least one independent audit of CRVS specification and reference implementation
  - All critical/high findings resolved before testnet Phase 2
  - Audit report published for community review

- **Instrumented devnet deployment**:
  - Deploy CRVS with full telemetry (vote latency, fork events, relay performance, transition triggers)
  - Run for >=3 months with adversarial testing (manual and automated)
  - Demonstrate acceptance gates are met in real-world conditions

**Mainnet gate:** CRVS may proceed to mainnet **only** if all above deliverables are complete and community consensus approves the audit results.

**Fallback plan:** If CRVS validation timeline extends beyond launch window, deploy mainnet with proven baseline consensus (e.g., Avalanche) and upgrade to CRVS post-launch via governance.

### 15.6 Milestone 5: IPFS pinning rewards

- Implement Pin Provider Registry and bonding/slashing rules.
- Implement Pin Job contract (public + private job modes).
- Implement challenge-response protocol and auditor committee tooling.
- Integrate with Cryftee ipfs_v1 module for node management and pin operations.
- Launch testnet with real pin providers and measure availability + fraud attempts.
### 15.7 Milestone 6: Federation hardening and production readiness

- Formal verification / property tests for scheduler determinism and slot lock rules.
- Security audits for Cryftee runtime, module verification, and key management integrations.
- Governance audits: vote export integrity, aggregation correctness, and timelock safety.
- Operational playbooks: upgrades, rollback, emergency pause policies, key rotation procedures.
- Multi-region stress testing: simultaneous State launches, cross-region transfer congestion, Mirror GBL conservation under load.
- Disaster recovery testing: Main partition scenarios, checkpoint withholding, orphaned region recovery.

### 15.8 Whitepaper completeness checklist (for publication)

- Clear definitions: Main, region, subnet, local chain, Cryftee, CGS, Smart Slots.
- Consensus description: safety/liveness assumptions, parameters, and finality guarantees.
- Execution model: EVM compatibility, tx formats, scheduler determinism, receipts, and conflict
handling.
- Federation model: checkpoints, cross-chain messages, replay protection, bridging assumptions.
- Governance: chambers, vote export, aggregation rules, proposal lifecycle, and upgrade safety.
- Validator eligibility: ping protocol, beacon governance, scoring, and incentives.
- Economics: fee markets, reward splits, emissions, and slashing policies.
- IPFS incentives: pin provider registry, job format, proof scheme, scoring, and fraud handling.
- Privacy: CGS message types, metadata matrix, key management, and dispute evidence rules.
- Security: threat model, mitigation list, audit plan, and monitoring metrics.
- Roadmap: milestones, test plans, benchmarks, and deployment strategy.
- Appendices: glossary, parameter ranges, JSON schema definitions, and reference implementations.

---

### 15.9 Pragmatic Mainnet v1: what to ship first

**Philosophy:** Don't invent a rocket and a new kind of gravity in the same sprint.

This section defines a **sane Mainnet v1** that avoids catastrophic risks while still delivering CryftNet's core value proposition: low-latency regions with EVM compatibility. Experimental features are gated behind feature flags or deferred to post-launch upgrades.

#### 15.9.1 Mainnet v1 scope (conservative launch)

| Component | Mainnet v1 Status | Rationale |
|:----------|:------------------|:----------|
| **Consensus** | Proven baseline (Avalanche or similar) | No novel CRVS logic in safety kernel until Milestone 15.5 complete and audited |
| **EVM Chain** | Standard EVM compatibility | Works with MetaMask, Hardhat, standard tooling; no surprises |
| **Regions (CSS-1)** | ✅ YES (enabled) | This is where "web2 feel" comes from; already proven in subnet architectures |
| **Federal Chain** | ✅ YES (validator management, checkpoints) | Core federation coordination; uses native VM (proven, not experimental) |
| **Mirror Chain** | ✅ YES (native CRYFT transfers) | High-throughput UTXO chain; proven design |
| **GBL/CMR** | ✅ YES (with enforced invariants) | Mirror Chain GBL with extended UTXO + EVM Chain CMR; partitioned balances + contract registry; ensure chain responsibilities consistent and invariants mechanically enforceable |
| **Smart Slots** | ⚠️ TESTNET-ONLY or WHITELISTED | Feature flag: disabled by default; enable only for governance-approved contracts with enforced under-claim detection (Section 7.3.5) |
| **CGS (privacy)** | ❌ TESTNET-ONLY | Not mainnet until Section 9.9 gating criteria met; all txs use legacy (non-private) path initially |
| **CRVS consensus** | ❌ DEFERRED | Deploy with proven consensus; upgrade to CRVS post-launch via governance after Milestone 15.5 validation complete |
| **DAS (Data Availability Sampling)** | ❌ OPTIONAL/POST-LAUNCH | Nice-to-have; not required for CSS-1; add incrementally |
| **ZK-EVM validity proofs** | ❌ OPTIONAL/POST-LAUNCH | Checkpoint verification uses quorum signatures initially; ZK proofs added later |

#### 15.9.2 What Mainnet v1 delivers

**User-facing value:**
- ✅ Low-latency regions (sub-second finality for region-local transactions)
- ✅ EVM compatibility (deploy Solidity contracts, use MetaMask, no code changes)
- ✅ Cross-region asset transfers (via Mirror GBL debit-checkpoint-credit flow)
- ✅ Federation-verified contracts (deterministic addresses across regions)
- ✅ Proven security (Avalanche-style consensus, no unvalidated experiments in safety kernel)

**Developer-facing value:**
- ✅ Standard EVM tooling works (Hardhat, Foundry, Remix, ethers.js, viem)
- ✅ Region-first deployment (deploy to preferred region, opt-in to federation mirroring)
- ✅ Partitioned balances (scale horizontally across regions without global state bottleneck)
- ✅ Clear operational model (checkpoints, cross-region messages, governance)

**What Mainnet v1 does NOT deliver (deferred to post-launch):**
- ❌ Novel consensus optimizations (CRVS) - proven baseline only
- ❌ Privacy-aware propagation (CGS) - all txs public initially
- ❌ Deterministic parallelism (Smart Slots) - serial EVM execution only, or whitelisted contracts
- ❌ ZK validity proofs - quorum signatures for checkpoints initially
- ❌ Advanced data availability (DAS) - optional for regions, not required

#### 15.9.3 Conservative deployment principles

**Principle 1: Proven core, experimental edges**
- Use battle-tested consensus (Avalanche) for safety kernel
- Use standard EVM for execution (no experimental VM features in critical path)
- Defer optimizations (CRVS, Smart Slots, CGS) until validated via decision machine (Section 16.2)

**Principle 2: Feature flags for experiments**
- Smart Slots: `--enable-smart-slots=false` by default; governance can enable per-contract
- CGS: `--enable-cgs=false` by default; testnet-only until Section 9.9 criteria met
- Parallel execution: `--enable-parallel-scheduler=false` by default; serial execution proven safe

**Principle 3: Mechanical invariant enforcement**
- Mirror GBL conservation: `sum(utxo.amount for asset) == total_supply` enforced by Mirror Chain UTXO model
- CMR consistency: Region deployments verified against EVM Chain registry before execution
- Checkpoint validity: Quorum signatures required; optional ZK proofs post-launch

**Principle 4: Clear upgrade path**
- Governance can enable CRVS via consensus upgrade once Milestone 15.5 complete
- Governance can enable CGS via protocol upgrade once Section 9.9 criteria met
- Governance can enable Smart Slots per-contract basis with enforced under-claim detection
- No breaking changes required; experimental features opt-in via config or contract flags

#### 15.9.4 Mainnet v1 acceptance gates

Before launching Mainnet v1, ALL of the following must be complete:

| Gate | Acceptance Criteria | Status |
|:-----|:--------------------|:-------|
| **Baseline consensus audit** | External audit of Avalanche integration; all critical/high findings resolved | ❌ TODO |
| **EVM Chain compatibility** | Passes Ethereum test suite; MetaMask/Hardhat work without modifications | ❌ TODO |
| **GBL invariant validation** | Formal verification or exhaustive property tests: no balance creation/loss; conservation holds under 1M cross-region transfers; UTXO integrity verified | ❌ TODO |
| **Checkpoint security** | Quorum signature verification; replay protection; no checkpoint forgery in adversarial tests | ❌ TODO |
| **Region interop testing** | 3+ regions with cross-region transfers, contract mirroring, checkpoint flow; p95 settlement <30s | ❌ TODO |
| **Testnet soak (>=3 months)** | Incentivized testnet with real validator economics; no critical bugs; uptime >99.9% | ❌ TODO |
| **Operational playbooks** | Documented upgrade, rollback, emergency pause, validator onboarding procedures | ❌ TODO |
| **Governance launch** | Federal Chain governance live; >=3 governance proposals executed successfully on testnet | ❌ TODO |

#### 15.9.5 Post-launch upgrade roadmap

**Phase 1 (Months 1-3): Stabilization**
- Monitor Mainnet v1 metrics: finality time, cross-region latency, validator participation
- Address any operational issues discovered in production
- Begin CRVS simulator validation (Milestone 15.5)

**Phase 2 (Months 4-6): CRVS validation**
- Complete Milestone 15.5 deliverables (formal spec, simulator, testnet)
- External audit of CRVS specification and reference implementation
- Community governance proposal: upgrade to CRVS consensus

**Phase 3 (Months 7-9): CGS hardening**
- Complete Section 9.9 deliverables (threat model, key ceremony, red-team tests)
- Deploy CGS on testnet with incentivized adversarial testing
- External audit of CGS crypto + protocol logic

**Phase 4 (Months 10-12): Experimental features**
- Enable Smart Slots for whitelisted contracts (with under-claim enforcement)
- Enable CGS for opt-in privacy (marked EXPERIMENTAL)
- Collect metrics and iterate based on real-world usage

**Phase 5 (Year 2+): Production-grade optimizations**
- CRVS consensus graduates from experimental to default (if validation successful)
- CGS graduates from experimental to production (if hardening successful)
- Smart Slots available to all contracts (if determinism validation successful)
- ZK-EVM validity proofs for checkpoint verification
- DAS for high-throughput regions

#### 15.9.6 Risk mitigation

**What could go wrong with Mainnet v1 (and how we mitigate):**

| Risk | Mitigation |
|:-----|:-----------|
| **Avalanche consensus bug** | Use well-audited codebase (AvalancheGo); extensive testnet soak; emergency pause governance |
| **GBL balance creation bug** | Formal verification of conservation invariant; property-based tests; real-time monitoring with alerts |
| **Cross-region checkpoint forgery** | Quorum signature verification; replay protection; slashing for invalid checkpoints |
| **Region validator cartel** | Minimum validator overlap requirements; Main governance can blacklist malicious regions |
| **EVM compatibility regression** | Run Ethereum test suite in CI; bounty program for compatibility issues |
| **Testnet doesn't surface issues** | Incentivized testnet with real economics; adversarial testing budget; external security reviews |

**What we're NOT trying to solve in v1:**
- Novel consensus optimizations (CRVS) - use proven baseline
- Privacy guarantees (CGS) - all txs public initially
- Parallel execution (Smart Slots) - serial EVM proven safe
- Advanced cryptography (ZK-EVMs) - quorum signatures sufficient

**Philosophy:** Ship a **boring, reliable foundation** that delivers core value (low-latency regions + EVM compatibility). Add experimental features post-launch via governance upgrades once validated through decision machine (Section 16.2).

This is not "giving up." This is **risk management**. You can iterate on CRVS, CGS, and Smart Slots in production once you've proven the foundation works.

## 16. Appendices

### 16.1 Glossary (selected)

- **Primary Network:** The canonical foundation of CryftNet, consisting of three specialized chains: Federal Chain (Federal), Mirror Chain (Mirror), and EVM Chain (EVM Execution). Cryft Labs maintains first-class implementations and long-term governance over all three chains.
- **Federal Chain (Federal):** The validator management and staking chain within the Primary Network. Handles validator set coordination, subnet registration, staking/delegation, checkpoint acceptance, and governance. Uses a native VM (not EVM).
- **Mirror Chain (Mirror):** The high-throughput native asset transfer chain within the Primary Network. Optimized for CRYFT transfers and native asset issuance using a UTXO model. Default chain for base asset movements.
- **EVM Chain (EVM Execution):** The account-based smart contract execution chain within the Primary Network. Compatible with Solidity/Vyper tooling--the dApp chain. When we say "EVM chain," we mean the EVM Chain specifically, not the entire Cryft network. Interactions with EVM Chain do not require region ID specification.
- **Region ID:** Unique identifier for a State/Region chain within the federation. Required for State/Region chain transactions and cross-region operations. NOT required for Primary Network EVM Chain interactions.
- **Global Balance Ledger (GBL):** The authoritative partitioned ledger for EVM token balances across all regions, managed by Mirror Chain using an extended UTXO model. Each UTXO includes metadata: {asset_id, region_id, account, amount}. Mirror Chain serves as the single source of truth; EVM Chain and subnets access GBL via atomic cross-chain messaging or precompiles. Native CRYFT balances also use Mirror Chain (standard UTXO).
- **Contract Mirror Registry (CMR):** The authoritative data structure on EVM Chain tracking federation contract deployments--target_regions[], deployed_regions[], mirror_status per region; updated via region checkpoints.
- **State Balance Ledger (SBL):** A State-level ledger tracking City balances within that State; mirrors Mirror Chain's GBL structure at State level; not visible to the Primary Network.
- **Region chain / State chain:** A low-latency chain serving a latency domain and anchoring to the Primary Network (via Federal Chain checkpoints). Requires region ID for transaction submission.
- **City chain / Local chain:** A sub-chain that registers via its parent State, not directly with the Primary Network; balances tracked in parent State's SBL.
- **CSS-1:** Cryft Standard Subnet profile for interoperability.
- **Smart Slot:** A deterministic schedulable resource representing a state dependency.
- **Process ID:** A lane identifier and namespace for parallel scheduling.
- **CGS:** Cryft Global Synchronizer, the privacy-aware propagation and synchronization plane.
- **Cryftee:** Signed WASM module runtime sidecar providing chain utilities and CGS hosting.
- **Pin provider:** An operator who earns rewards by keeping content available on IPFS.
- **Partitioned balance:** An asset accounting model where balances are tracked per-region via Mirror Chain GBL extended UTXO; the same contract address exists on all regions but balances are region-specific.
- **Federation Contract Registry:** Main-hosted registry of canonical contract deployments, recording address, code_hash, deployer, and verified regions.
- **CREATE2 deployment:** Deterministic contract deployment using CREATE2 opcode, ensuring same address across all regions given identical deployer, salt, and init_code.
- **Cross-region transfer:** Movement of assets from one region to another via debit-checkpoint-credit flow, recorded in Mirror Chain GBL as UTXO transitions.
- **Cross-City transfer:** Movement of assets between Cities under the same State, recorded in State's SBL (does not touch Main).
- **Transfer_id:** Unique identifier for a cross-region transfer, used to prevent replay attacks.
- **Credit line (mirroring):** Spending authorization granted to regions for a user's mirrored balance, backed by assets held on Main.
- **Conservation invariant:** The rule that sum(regional balances) must equal total supply for any token; enforced by Mirror Chain GBL UTXO model (`sum(utxo.amount for asset) == total_supply`).
- **Home region:** The designated region where a token's initial supply is minted; mint() calls only succeed on this region.
- **Zero-balance constructor:** Required pattern for federation-verified tokens where constructor initializes no balances; prevents supply duplication on multi-region deployment.
- **FederationDeployer:** A contract deployed on Main and all regions that enforces governance-approved deployments via CREATE2; requires Main checkpoint authorization before deploying.
- **RegionDeployer:** A contract at the same address on all regions enabling region-first deployment with deterministic addresses; supports opt-in federation mirroring and lazy mirroring (deploy-on-first-use via ensureDeployedAndCall()).
- **Code Vault (Bytecode Vault):** The canonical storage and commitment layer on Mirror Chain for federation-deployable smart contract code. Stores code metadata including init_code_hash, runtime_code_hash, and optionally init_code blobs or IPFS CIDs. Each code package assigned unique code_id. Enables deterministic CREATE2 deployment across regions without executing smart contracts on Mirror Chain.
- **code_id:** Unique identifier for a code package in Mirror Chain Code Vault. Hash-based and immutable once committed. Referenced by EVM Chain CMR for deployment authorization.
- **ensureDeployedAndCall():** RegionDeployer function enabling lazy mirroring (deploy-on-first-use). Checks if contract deployed on current region; if not, deploys via CREATE2 with CMR authorization verification, then executes call atomically. First caller pays deployment gas + federation fee; subsequent callers pay normal gas.
- **Lazy mirroring (deploy-on-first-use):** Pattern where contracts don't need eager deployment on all target regions. First caller on a region triggers deployment via ensureDeployedAndCall(); CREATE2 determinism ensures same address. Reduces upfront deployment costs while maintaining address guarantees.
- **Loader init_code (optional):** Advanced pattern where init_code stored in Code Vault is minimal "loader" bytecode that fetches actual contract code from IPFS during deployment. Reduces Code Vault storage requirements for large contracts while maintaining deterministic deployment.
- **Region-first deployment:** Developer-friendly model where contracts deploy to a region first, then Main mirrors to other regions via checkpoints if opted in.
- **Federation mirroring:** Process where Main propagates a contract deployment to other regions, maintaining the same address via deterministic CREATE2.
- **Balance portability:** Opt-in feature allowing contract balances to transfer across regions via debit-checkpoint-credit flow.
- **Target regions (target_regions[]):** Explicit list of region IDs a contract opts into for federation mirroring; deployer must pay federation fees for each declared region.
- **Federation fee:** Fee paid to Main for multi-region operations including contract mirroring, balance portability setup, and cross-region transfers; ensures Main receives appropriate gas for federation coordination.
- **Region expansion:** Post-deployment process to add additional regions to a contract's target_regions[]; requires payment of additional federation fees.
- **Two-phase initialization:** Pattern where contract deployment (zero state) is separate from initialization (setting initial balances), ensuring same address across regions.
- **DAS (Data Availability Sampling):** Technique allowing nodes to verify block data availability by sampling fragments rather than downloading entire blocks.
- **ZK-EVM:** Zero-knowledge Ethereum Virtual Machine enabling cryptographic proof-based validation of transaction batches.

### 16.2 Open decisions: decision machine

This section transforms open questions into actionable decision items with clear ownership, milestones, and acceptance criteria. Each item is categorized by type and assigned to a functional owner with measurable outcomes.

**Legend:**
- **Type:** `spec` (specification decision), `research` (theoretical analysis), `simulation` (parameter validation via testing), `governance` (on-chain parameter), `ops` (operational policy)
- **Owner:** `dev` (core development), `research` (research team), `tokenomics` (economic modeling), `ops` (operations/DevOps), `governance` (community decision)
- **Milestone:** `testnet-0` (devnet), `testnet-1` (incentivized testnet), `pre-mainnet` (launch blocker), `post-mainnet` (can iterate after launch)
- **Status:** `BLOCKED` (waiting on other work), `TODO` (ready to start), `IN PROGRESS`, `DONE`

---

#### 16.2.1 Consensus and execution decisions

| # | Decision | Type | Owner | Milestone | Acceptance Test | Status |
|:--|:---------|:-----|:------|:----------|:----------------|:-------|
| **D-01** | Under-claim enforcement mechanism | `spec` | dev | pre-mainnet | No observed nondeterminism in >=10M tx fuzz runs; deterministic fallback works with zero safety violations | TODO |
| **D-02** | CRVS parameter optimization | `simulation` | research | pre-mainnet | Supports 50-500 validator committees with p99 finality <5s under 20% Byzantine + realistic jitter; fork rate <0.001% | BLOCKED (needs simulator) |
| **D-03** | CRVS fast/slow path transition rules | `spec` | research | pre-mainnet | Formal specification published; no oscillation under adversarial partition scenarios in 100K rounds | TODO |
| **D-04** | Federal vs. EVM Chain responsibility split | `spec` | dev + governance | testnet-1 | Clear separation documented; no circular dependencies; staking decision finalized with security audit | TODO |

#### 16.2.2 Privacy and CGS decisions

| # | Decision | Type | Owner | Milestone | Acceptance Test | Status |
|:--|:---------|:-----|:------|:----------|:----------------|:-------|
| **D-05** | CGS privacy guarantees (threat model) | `research` | research + ops | pre-mainnet | Formal threat model published; timing correlation <X%, red-team test passed | TODO |
| **D-06** | CGS key committee size and rotation frequency | `governance` + `simulation` | tokenomics + ops | testnet-1 | Key compromise drills pass; rotation completes in <1 epoch; committee liveness >99.9% | TODO |
| **D-07** | CGS mainnet readiness criteria | `spec` | dev + research | pre-mainnet | All 6 gating criteria from Section 9.9 met; external audit complete | BLOCKED (needs audit) |

#### 16.2.3 Cross-chain and federation decisions

| # | Decision | Type | Owner | Milestone | Acceptance Test | Status |
|:--|:---------|:-----|:------|:----------|:----------------|:-------|
| **D-08** | Optimal checkpoint frequency | `simulation` | research + dev | testnet-1 | Supports X msg/s at Y regions with p95 settlement <Z minutes; Main throughput degradation <10% | TODO |
| **D-09** | Mirroring credit line sizing policy | `spec` + `simulation` | tokenomics + dev | testnet-1 | No double-spend in 1M cross-region tx; UX acceptable (refresh frequency <1/day for 90% of users) | TODO |
| **D-10** | Unclaimed transfer timeout period | `governance` | tokenomics + governance | testnet-1 | <0.1% of transfers timeout; user complaints <acceptable threshold; reclaim mechanism works | TODO |
| **D-11** | Cross-region transfer fee pricing | `governance` + `simulation` | tokenomics | testnet-1 | Spam rate <0.01%; affordable for legitimate users (cost <$0.50 for 90% of transfers) | TODO |
| **D-12** | ZK proof requirement threshold for high-value transfers | `governance` | governance + dev | post-mainnet | Reduces trust assumptions for transfers >$X without breaking UX | TODO |
| **D-13** | Federation fee structure (base + per-region) | `governance` + `simulation` | tokenomics | testnet-1 | Sustainable Main revenue; developer cost acceptable (<$50 for 5-region deployment) | TODO |
| **D-14** | Maximum target_regions per deployment | `spec` + `simulation` | dev | testnet-1 | Main checkpoint congestion <10% at peak; deployment succeeds in <20 regions | TODO |
| **D-15** | Orphaned balance recovery mechanism (unreachable regions) | `spec` | dev + governance | post-mainnet | Governance can reclaim balances after timeout; no griefing vectors | TODO |
| **D-16** | RegionDeployer upgrade coordination mechanism | `spec` + `ops` | dev + ops | pre-mainnet | Upgrade completes across all regions within 1 epoch; no deployment failures | TODO |

#### 16.2.4 Data availability and storage decisions

| # | Decision | Type | Owner | Milestone | Acceptance Test | Status |
|:--|:---------|:-----|:------|:----------|:----------------|:-------|
| **D-17** | IPFS proof of availability mechanism | `spec` + `simulation` | dev + research | testnet-1 | Fraud detection rate >99%; proof verification cost <$0.01/GB; false positive rate <0.001% | TODO |
| **D-18** | Pin provider scoring and slashing policy | `governance` + `simulation` | tokenomics + ops | testnet-1 | Honest providers earn >95% expected rewards; malicious providers slashed >95% of time | TODO |

#### 16.2.5 Governance and economics decisions

| # | Decision | Type | Owner | Milestone | Acceptance Test | Status |
|:--|:---------|:-----|:------|:----------|:----------------|:-------|
| **D-19** | Cross-network vote weight cap mechanism | `governance` + `research` | tokenomics + governance | testnet-1 | Sybil-resistant (attack cost >$X million); not plutocratic (top 10 holders control <30% of vote) | TODO |
| **D-20** | Validator reward split (Main vs. State duties) | `governance` + `simulation` | tokenomics | testnet-1 | Validators incentivized to validate both; State validation participation >80% of Main validators | TODO |
| **D-21** | CSS-1 State bootstrap period before Main validation required | `governance` | governance + ops | testnet-1 | New States can experiment safely; migration to Main validation smooth (>90% success rate) | TODO |

#### 16.2.6 Subnet topology and scaling decisions

| # | Decision | Type | Owner | Milestone | Acceptance Test | Status |
|:--|:---------|:-----|:------|:----------|:----------------|:-------|
| **D-22** | Cities per State scalability limit | `simulation` | research + dev | testnet-1 | State checkpoint aggregation <5s for <=100 Cities; Main accepts aggregated checkpoint in <10s | TODO |
| **D-23** | Minimum validator overlap requirement (State-City) | `spec` + `governance` | dev + tokenomics | testnet-1 | Security analysis shows overlap prevents censorship; operational overhead acceptable | TODO |
| **D-24** | City emergency bridge to Main (censorship escape) | `spec` + `governance` | dev + governance | post-mainnet | Censorship-resistant; anti-griefing mechanisms prevent abuse; governance approval required | TODO |
| **D-25** | Region-first deployment cooling period | `governance` | governance + ops | testnet-1 | Prevents rushed malicious deployments; false positive rate <1%; delay acceptable to developers | TODO |
| **D-26** | Two-phase initialization timeout (anti-griefing) | `spec` + `governance` | dev | testnet-1 | Prevents initialization griefing; timeout period balances security and UX | TODO |
| **D-27** | State-City SBL dispute resolution mechanism | `spec` + `governance` | dev + governance | post-mainnet | Disputes resolvable in <7 days; Main governance can arbitrate; no fund loss | TODO |

---

#### 16.2.7 Decision process workflow

**For each decision:**

1. **Assign owner** (if not already assigned)
2. **Define success criteria** (refine "Acceptance Test" column)
3. **Identify dependencies** (what must be done first?)
4. **Schedule milestone** (which testnet phase or pre-mainnet blocker?)
5. **Execute work** (spec writing, simulation, governance proposal, etc.)
6. **Validate** (run acceptance test)
7. **Document** (publish decision and rationale)
8. **Mark DONE** (move to implementation)

**Blockers and dependencies:**

- D-02 (CRVS parameters) is BLOCKED until consensus simulator is complete (Milestone 15.5)
- D-07 (CGS mainnet) is BLOCKED until external audit is funded and scheduled
- Governance decisions (D-10, D-12, D-19, D-21, D-24, D-25, D-27) require community RFC process before testnet-1

**Priority tiers:**

- **P0 (pre-mainnet blockers):** D-01, D-02, D-03, D-04, D-07, D-16
- **P1 (testnet-1 required):** D-05, D-06, D-08, D-09, D-11, D-13, D-14, D-17, D-19, D-20, D-22, D-23, D-26
- **P2 (post-mainnet, can iterate):** D-10, D-12, D-15, D-18, D-21, D-24, D-25, D-27
