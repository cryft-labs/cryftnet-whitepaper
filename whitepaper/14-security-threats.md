```text
CRYFTTEE_WEB3SIGNER_URL=http://localhost:9000
CRYFTTEE_WEB3SIGNER_TIMEOUT=30
```

**Key derivation:**
```text
CRYFTTEE_KEY_SEED=<hex>
CRYFTTEE_NODE_ID=<node_id>
```

**Security:**
```text
CRYFTTEE_VERIFIED_BINARY_HASH=sha256:<hex>
CRYFTTEE_REQUIRE_ATTESTATION=false
```

---

## 14. Security model and threat analysis

CryftNet security spans multiple planes: consensus, execution determinism, cross-region asset integrity, governance, privacy propagation, and availability incentives. This section lists key threat classes and mitigations. It is not exhaustive; it is a starting point for formal review.

### 14.1 Consensus threats

- **Network partition:** regions may split. Mitigation: slow-path voting, increased anchoring to Main, conservative checkpoint acceptance.
- **Relay censorship:** rotor relays could delay data. Mitigation: relays are non-authoritative; fallback gossip; relay performance affects rewards.
- **Adaptive adversary:** targets soft leaders. Mitigation: leaderless option; rotate relay sets; use sampling.
- **Checkpoint withholding:** region produces blocks but delays checkpointing to Main. Mitigation: checkpoint liveness requirements; rewards tied to checkpoint frequency; user failover to Main.
- **Cryftee offline or invalid attestation:** Node cannot participate in consensus. Mitigation: CryftGo startup fails if Cryftee not running or required modules fail attestation; peers reject bundles from unattested nodes; reward eligibility requires valid attestation.

### 14.2 Smart Slot threats

- **Under-claiming:** tx claims fewer slots than it touches, breaking determinism. Mitigation: runtime detection where possible; slashing if provable; SDKs; contract-provided hints; conservative policies for high-risk calls.
- **Over-claiming:** reduces parallelism (safe). Mitigation: tooling and incentives (lower fees for precise claims).
- **Slot collision:** bad derivation leads to collisions. Mitigation: strict canonical encoding and domain separators; versioned CEP.

### 14.3 CGS threats

- **Traffic analysis:** timing correlates sender/receiver. Mitigation: batching, cover traffic, delayed reveals.
- **Key compromise:** threshold key compromised. Mitigation: frequent rotation; multi-party control; optional HSM/TEE.
- **Spam intents:** adversary floods. Mitigation: fees, rate limits, capability gating, proof-of-work optional.
- **Complexity:** bugs introduce consensus risk. Mitigation: keep CGS non-consensus-critical where possible; staged rollouts.

### 14.4 Ping eligibility threats

- **Proxy/VPN gaming:** validator tunnels into region. Mitigation: multi-beacon diversity, random challenges, jitter/loss scoring, correlation across peers.
- **Beacon capture:** beacons collude. Mitigation: beacon governance, rotating beacons, audits, optional federation beacon set.
- **Measurement falsification:** forged reports. Mitigation: signed reports, nonces, on-chain verification of signatures.

### 14.5 Pinning incentive threats

- **Fake pin proofs:** provider claims availability without serving. Mitigation: random challenges, auditor fetches, fraud slashing.
- **Sybil providers:** same operator registers many providers. Mitigation: stake requirements, identity policies, diversity bonuses weighted by independent attestations.
- **Auditor corruption:** auditors lie. Mitigation: multiple auditors, randomized sampling, auditor staking and slashing.

### 14.6 Cross-region and partitioned balance threats

The partitioned balance model introduces specific threat vectors that must be addressed:

- **Cross-region double-spend (race condition):** User initiates transfer from A->'B, then tries to spend on A before checkpoint. Mitigation: balance is debited immediately on A; spending fails because balance is already reduced.

- **Replay attack on claims:** Attacker replays a valid claim proof to credit balance multiple times on destination region. Mitigation: each transfer_id is marked as consumed after first claim; claimed[transfer_id] = true prevents replay.

- **Forged checkpoint proof:** Attacker forges a Merkle proof of a debit that never happened. Mitigation: proofs are verified against Main-finalized checkpoint roots; ZK validity proofs make forgery computationally infeasible; validators who sign invalid checkpoints are slashed.

- **Region validator collusion:** Majority of region validators conspire to create fake debit events. Mitigation: Main requires quorum signatures on checkpoints; ZK proofs provide trustless verification; users can always withdraw to Main as escape hatch.

- **Checkpoint reorg attack:** Region finalizes a checkpoint, then reorgs to remove the debit while destination already credited. Mitigation: Main does not accept checkpoints until region finality is confirmed; ZK proofs bind to specific state transitions.

- **Supply inflation via multiple regions:** Bug or attack causes same tokens to exist on multiple regions without proper debit. Mitigation: Main tracks sum(region_balances) per token; discrepancy triggers bridge pause and investigation; conservation invariant is checked on every checkpoint.

- **Contract address mismatch:** Malicious region deploys different code at the "same" address. Mitigation: Federation Contract Registry on Main records (address, code_hash); regions must match; wallets verify registry status before displaying tokens.

- **CREATE2 front-running (malicious code):** Attacker tries to deploy malicious contract at predicted address before legitimate deployment. **Natural protection:** CREATE2 address depends on init_code hash; different code = different address. Attacker cannot deploy different code at the same address. **Residual risk:** Deployer key compromise. Mitigation: federation-controlled deployer with governance authorization; multisig or threshold signatures; tiered deployment model.

- **Deployment race condition (same code):** Multiple parties attempt to deploy identical code simultaneously on different regions. **Not harmful:** Whoever deploys first on a region simply succeeds; the code is identical. Federation Contract Registry ensures only governance-approved deployments are marked as verified.

- **Uncoordinated region deployment:** Region deploys contract before receiving Main checkpoint authorization. Mitigation: FederationDeployer requires authorization from Main checkpoint before allowing deployment; unauthorized calls revert.

- **Constructor balance duplication:** Token constructor initializes balances (e.g., `balances[issuer] = 1B`), and deploying on multiple regions multiplies the supply. **Critical mitigation:** Federation-verified tokens MUST use zero-balance constructors; initial supply is minted via separate transaction on designated home_region only; Mirror Chain GBL is authoritative source of truth, not local contract storage; governance code review rejects contracts with constructor-initialized balances.

- **Home region bypass:** Attacker tries to call mint() on non-home region. Mitigation: mint() function checks `REGION_ID == registry.homeRegion(address(this))` and reverts otherwise; only authorized_minter on home_region can create new supply.

- **Mirroring credit abuse:** User enables mirroring, spends on multiple regions simultaneously before reconciliation. Mitigation: Main orders checkpoints globally; later transactions that exceed remaining credit are reverted; user penalized and mirroring suspended.

- **Stale credit line exploitation:** User's mirroring credit is reduced on Main, but region hasn't received update. User spends stale credit. Mitigation: credit lines have epoch validity; regions must refresh from Main periodically; transactions using stale credit are subject to revert.

- **Griefing via transfer spam:** Attacker initiates many small cross-region transfers to congest checkpoint message roots. Mitigation: minimum transfer amounts; fees proportional to cross-region message size; rate limits per account.

- **Unclaimed transfers (stuck funds):** User initiates transfer but never claims on destination. Mitigation: transfers can be reclaimed on origin after timeout (e.g., 30 days); refund requires proof of non-claim.

- **Region exit scam:** Region validators collude to steal all regional balances before abandoning the chain. Mitigation: users can always exit to Main via checkpoint proof; Main serves as "home of last resort"; region slashing and reputation systems.

### 14.7 Data availability and ZK threats

- **DAS sampling failure:** Insufficient samples to guarantee availability. Mitigation: conservative sampling parameters; fallback to full download for critical operations.
- **ZK prover centralization:** Few parties can generate proofs, creating censorship risk. Mitigation: multiple prover implementations; prover decentralization incentives; fallback to quorum verification.
- **ZK soundness bug:** Flaw in ZK system allows invalid proofs. Mitigation: multiple proof systems; formal verification; staged rollout with quorum fallback.

### 14.8 Multi-chain Main and hierarchical registration threats

- **Federal Chain / EVM Chain desync:** Atomic messaging between Federal Chain and EVM Chain fails, causing inconsistent state. Mitigation: shared validator set ensures atomic block production; recovery protocol for rare edge cases.
- **EVM Chain governance capture:** Attacker gains control of EVM Chain to manipulate subnet registrations. Mitigation: same governance protections as Federal Chain; two-chamber votes; timelocks.
- **Rogue State chain registering malicious Cities:** State DAO approves a City designed to defraud users. Mitigation: State reputation systems; user warnings for new Cities; exit to State as escape hatch.
- **City checkpoint withholding:** City validators delay checkpointing to State to enable fraud. Mitigation: checkpoint liveness requirements enforced by State; City slashing; user failover to State.
- **Cross-participation evasion:** CSS-1 validator stops validating Main while continuing State validation. Mitigation: Main monitors CSS-1 validator participation; automatic suspension from State if Main duties lapse.
- **State-mediated censorship of Cities:** State refuses to include City checkpoints. Mitigation: Cities can appeal to Main governance; emergency City-to-Main bridge for exit; State reputation damage.

### 14.9 Global Balance Ledger (GBL), Contract Mirror Registry (CMR), and State Balance Ledger (SBL) threats

- **GBL manipulation:** Attacker attempts to modify Mirror Chain GBL records to inflate regional balances. Mitigation: GBL updates require checkpoint proofs from origin region; Mirror Chain validator consensus on all GBL UTXO transitions; slashing for malicious proposals; UTXO model provides strong integrity guarantees.
- **GBL-regional desync:** Region's local balance tracking diverges from Mirror GBL. Mitigation: periodic reconciliation audits; discrepancy detection triggers bridge pause; conservation invariant checked on every checkpoint; UTXOs provide audit trail.
- **CMR manipulation:** Attacker attempts to modify EVM Chain CMR to add unauthorized target_regions or mark non-deployed contracts as deployed. Mitigation: CMR updates only via verified checkpoint proofs; fee verification before region addition; EVM Chain validator consensus on all CMR state transitions.
- **CMR-region desync:** Region's local deployment registry diverges from EVM Chain CMR. Mitigation: regions derive mirror permissions from CMR state in checkpoints; unauthorized local deployments not recognized by federation; periodic reconciliation audits.
- **CMR status forgery:** Region checkpoint falsely claims successful deployment. Mitigation: Main can verify deployment by querying region; ZK proof of contract existence; slashing for false checkpoint claims.
- **SBL-GBL desync:** City's State Balance Ledger diverges from State's view of City balances, or State's aggregate diverges from Mirror GBL. Mitigation: State checkpoints include City balance summaries; discrepancies flagged for investigation; City suspension pending resolution; Mirror GBL reconciliation.
- **City balance inflation:** City attempts to credit users with balances not backed by State allocation. Mitigation: SBL credits must not exceed State-allocated balance for City; checkpoints rejected if SBL sum exceeds allocation; Mirror GBL tracks State total.
- **State blocking City transfers:** State refuses to process legitimate City-to-State balance movements. Mitigation: City can appeal to Main; emergency exit mechanism via Main governance; State reputation damage.
- **Orphaned regional balances:** Region becomes permanently unreachable, leaving Mirror GBL balances stranded. Mitigation: governance can trigger balance recovery after extended unreachability; Main serves as arbiter of final state; UTXO-based recovery possible.

### 14.10 Region-first deployment and federation fee threats

- **RegionDeployer compromise:** Attacker gains control of RegionDeployer on one region. Mitigation: RegionDeployer is immutable; only allows CREATE2 with predetermined logic; no admin keys; upgrade requires governance-approved chain migration.
- **Unauthorized mirror triggering:** Attacker calls `mirror()` on regions not declared in target_regions[]. Mitigation: mirror() verifies caller authorization from Main checkpoint; unauthorized calls revert; only Main can authorize mirroring.
- **target_regions[] manipulation:** Developer changes target_regions[] after deployment to add regions without paying fees. Mitigation: target_regions[] is immutable after deployment transaction; expanding requires new governance proposal and fee payment.
- **Federation fee evasion:** Developer deploys on region, then manually deploys on other regions to avoid federation fees. Mitigation: manual deployments are not marked as Federation-verified; users see warning for unverified contracts; no mirroring benefits.
- **Fee underpayment:** Developer provides insufficient fee for declared target_regions[]. Mitigation: RegionDeployer calculates required fee dynamically; transaction reverts if msg.value < requiredFee.
- **Fee oracle manipulation:** Attacker manipulates on-chain price oracle to reduce federation fees. Mitigation: fee rates are governance-controlled parameters; oracle aggregation; rate limits on fee changes.
- **Two-phase initialization griefing:** Attacker front-runs initialize() call on mirrored contract to set malicious parameters. Mitigation: initialize() requires deployer signature or is restricted to authorized_initializer set by constructor.
- **Initialization replay:** Attacker replays initialize() call on newly mirrored region. Mitigation: initialize() sets initialized = true; subsequent calls revert; pattern enforced by OpenZeppelin Initializable.
- **Cross-region initialization race:** Same contract initialized with different parameters on different regions. Mitigation: RegionDeployer requires init_data to be identical across regions; hash of init_data recorded on Main; mismatched initializations flagged.
- **Region expansion DoS:** Attacker declares maximum target_regions[] to congest checkpoints. Mitigation: per-deployment maximum regions (e.g., 50); checkpoint size limits; gas costs scale with region count.

### 14.11 Lazy mirroring and Code Vault threats

- **Malicious code injection via Code Vault:** Attacker attempts to inject malicious bytecode into Mirror Chain Code Vault. Mitigation: Code Vault entries require governance approval or multi-signature authorization; immutable once committed; code_id is hash-based and cannot be reused.
- **Code Vault / CMR desync:** Mirror Chain Code Vault shows code_id as available, but EVM Chain CMR does not authorize deployment. Mitigation: RegionDeployer enforces CMR authorization check before deployment; unauthorized deployments revert regardless of Code Vault state.
- **Incorrect init_code / runtime_code mismatch:** Deployed contract's runtime bytecode does not match Code Vault's runtime_code_hash commitment. Mitigation: RegionDeployer verifies keccak256(deployed.code) == Code Vault runtime_code_hash after CREATE2; mismatches cause deployment revert.
- **Front-running ensureDeployedAndCall():** Attacker observes pending ensureDeployedAndCall() tx and front-runs with own deployment to grief first caller. **Natural protection:** CREATE2 allows only one deployment per (deployer, salt, init_code_hash); duplicate attempts fail. First successful deployment wins; second caller's ensureDeployedAndCall() detects existing code and proceeds to call phase. **Residual risk:** Griefing by deploying with different init_code to occupy address (prevented by init_code_hash verification).
- **Stale authorization proof:** User submits ensureDeployedAndCall() with authorization proof from old checkpoint, but CMR has since revoked authorization for that code_id/region. Mitigation: RegionDeployer verifies proof against latest finalized Main checkpoint; stale proofs rejected; proof includes checkpoint height/hash.
- **Deploy-before-checkpoint race:** Attacker deploys contract on region before Main checkpoint authorizing it arrives. Mitigation: RegionDeployer requires valid authorization proof before deployment; proof binds to specific checkpoint; unauthorized deployments revert.
- **ensureDeployedAndCall() DoS via repeated deployment attempts:** Attacker spams ensureDeployedAndCall() with invalid proofs to congest region. Mitigation: invalid proof verification reverts immediately (before expensive operations); standard tx fee mechanism prevents spam; rate limiting at mempool level.
- **Constructor-based supply duplication (critical):** Token contract deploys on multiple regions via lazy mirroring, constructor initializes `balances[issuer] = 1B` on each region, inflating total supply. **Critical mitigation:** Federation-verified contracts MUST use zero-balance constructors (enforced by code review); constructor MUST NOT mint supply or set balances; initial state set via separate initialize() transaction restricted to home_region only; Mirror GBL is authoritative for balances, not local contract storage; governance rejects code_id approval for contracts with constructor-initialized balances.
- **Loader init_code fetch failure:** Region attempts to deploy using loader init_code, but IPFS fetch fails. Mitigation: Mirror Code Vault stores full init_code as fallback; regions can request full init_code if loader fails; timeout and retry logic; deployment fee refunded on persistent failure.
- **Code Vault data availability:** Mirror Chain Code Vault becomes unavailable, preventing new deployments. Mitigation: Code Vault data replicated across Mirror Chain validators; IPFS backup for large init_code blobs; emergency fallback to Main EVM Chain storage if Mirror unavailable.
- **Max code size violation:** Attacker attempts to deploy contract exceeding EVM code size limit (24KB). Mitigation: RegionDeployer enforces max code size check before CREATE2; oversized deployments revert; Code Vault rejects code_id registration for oversized bytecode.
- **Unauthorized lazy deployment on non-target region:** Attacker calls ensureDeployedAndCall() on Region Z, which is NOT in target_regions[] for that code_id. Mitigation: CMR authorization proof explicitly lists authorized regions; RegionDeployer verifies REGION_ID is in authorized list; unauthorized regions reject deployment with proof verification failure.

### 14.12 Threat matrix (comprehensive summary)

| Threat | Plane | Impact | Mitigation summary |
|:-------|:------|:-------|:-------------------|
| Under-claimed slots | Execution | Nondeterminism / forks | SDK enforcement, audit, provable slashing, conservative policies |
| Relay censorship | Network | Delayed inclusion | Fallback gossip, performance-weighted rewards |
| Beacon capture | Eligibility | Fake regions | Beacon rotation, federation audits, quorum requirements |
| Pin provider fraud | Availability | Content loss | Challenge-response, auditors, slashing |
| CGS key compromise | Privacy | Disclosure risk | Threshold rotation, multi-party control, monitoring |
| Governance capture | Governance | Bad upgrades | Two-chamber votes, timelocks, veto and emergency policies |
| Cross-region double-spend | Asset integrity | Token duplication | Immediate debit, checkpoint ordering, transfer_id consumption |
| Forged checkpoint proof | Asset integrity | Unauthorized minting | Merkle verification, ZK proofs, validator slashing |
| Region validator collusion | Asset integrity | Fake debits/credits | Main quorum verification, ZK proofs, exit to Main |
| Supply inflation | Asset integrity | Economic damage | Conservation invariant check, bridge pause, checkpoint audits |
| Contract address mismatch | Execution | Malicious code execution | Federation Contract Registry, code_hash verification |
| Mirroring credit abuse | Asset integrity | Overspending | Global checkpoint ordering, revert mechanism, penalties |
| Region exit scam | Asset integrity | Total loss on region | Exit to Main via proof, slashing, reputation systems |
| Checkpoint withholding | Liveness | Delayed settlement | Liveness requirements, reward incentives, user failover |
| ZK soundness bug | Asset integrity | Invalid state accepted | Multiple proof systems, formal verification, quorum fallback |
| Federal Chain / EVM Chain desync | Consistency | Split-brain state | Shared validators, atomic blocks, recovery protocol |
| Rogue City registration | Asset integrity | User fraud via City | State reputation, user warnings, exit to State |
| Cross-participation evasion | Security | Weakened Main | Participation monitoring, automatic State suspension |
| GBL manipulation | Asset integrity | Regional balance inflation | Checkpoint proofs, Main consensus, slashing |
| GBL-regional desync | Consistency | Balance divergence | Reconciliation audits, bridge pause, invariant checks |
| CMR manipulation | Deployment | Unauthorized mirror expansion | Checkpoint proofs, fee verification, Main consensus |
| CMR-region desync | Consistency | Mirror state divergence | CMR as authority, periodic reconciliation |
| CMR status forgery | Security | False deployment claims | Main verification queries, ZK proofs, slashing |
| SBL-GBL desync | Consistency | City/State imbalance | State checkpoint audits, discrepancy flags, City suspension |
| City balance inflation | Asset integrity | Unbacked credits | SBL sum validation, allocation enforcement |
| Orphaned regional balances | Asset integrity | Stranded funds | Governance recovery, Main arbitration |
| RegionDeployer compromise | Security | Unauthorized deployments | Immutable contracts, no admin keys, governance migration |
| Unauthorized mirroring | Deployment | Unintended region spread | Main checkpoint authorization, target_regions[] enforcement |
| target_regions[] manipulation | Economics | Fee evasion | Immutable after deployment, governance for expansion |
| Federation fee evasion | Economics | Revenue loss | Unverified contract warnings, no mirroring benefits |
| Fee underpayment | Economics | Service denial | Dynamic fee calculation, revert on insufficient payment |
| Two-phase init griefing | Security | Malicious initialization | Deployer signature, authorized_initializer restriction |
| Initialization replay | Security | Parameter hijacking | initialized flag, OpenZeppelin Initializable pattern |
| Cross-region init race | Consistency | Parameter mismatch | Identical init_data requirement, Main hash recording |
| Region expansion DoS | Availability | Checkpoint congestion | Max regions limit, size limits, scaled gas costs |
| Malicious code injection (Code Vault) | Security | Deployment of malicious contracts | Governance approval, multi-sig authorization, immutable code_id |
| Code Vault / CMR desync | Consistency | Unauthorized deployment | CMR authorization enforced before deployment, dual verification |
| init_code / runtime_code mismatch | Security | Code tampering | Post-deployment bytecode verification against Code Vault hash |
| Front-running ensureDeployedAndCall | Security | Griefing | CREATE2 allows single deployment per hash; duplicate fails |
| Stale authorization proof | Security | Unauthorized deployment | Proof verified against latest checkpoint, includes checkpoint height |
| Deploy-before-checkpoint race | Security | Unauthorized early deployment | Authorization proof required before deployment, reverts without proof |
| ensureDeployedAndCall DoS | Availability | Region congestion | Early revert on invalid proof, standard tx fees, mempool rate limits |
| Constructor supply duplication | Asset integrity | Supply inflation | Zero-balance constructor enforcement, code review, GBL authority |
| Loader init_code fetch failure | Availability | Deployment failures | Full init_code fallback, retry logic, fee refund on persistent failure |
| Code Vault unavailability | Availability | Deployment blockage | Validator replication, IPFS backup, emergency Main EVM fallback |
| Max code size violation | Security | Resource exhaustion | Code size check before CREATE2, Code Vault registration limits |
| Unauthorized lazy deployment | Security | Deployment on wrong region | CMR proof lists authorized regions, REGION_ID verification |

---

## 15. Implementation roadmap and engineering checklist

This roadmap is a pragmatic decomposition into testable milestones. Each milestone should produce
artifacts: code, tests, benchmarks, and documented threat reviews. The checklist is intentionally
exhaustive: it is easier to delete items later than to discover them during an outage.
### 15.1 Milestone 0: Specification and simulation

- Finalize CEP-CSS-1 slot derivation and scheduler determinism rules.
- Define CRVS parameter ranges and implement a simulator (network + adversary models).
- Define checkpoint formats and message roots; build light verifier library.
- Define ping protocol (packet formats, nonce rules, signing, report encoding).
- Threat modeling workshops for Smart Slots, CGS, and pinning incentives.
### 15.2 Milestone 1: Primary Network prototype (Federal + Mirror + EVM)

- Fork and bootstrap consensus client (cryftgo baseline) and integrate Cryftee sidecar launch.
- Implement three-chain Primary Network: Federal Chain (native VM for validators/governance), Mirror Chain (native UTXO for assets + GBL extended UTXO + Code Vault), and EVM Chain (EVM for smart contracts + CMR).
- Implement Mirror Chain Global Balance Ledger (GBL) with extended UTXO model for per-region balance tracking.
- **Implement Mirror Chain Code Vault (Bytecode Vault) for canonical smart contract code storage and commitment.**
- **Implement code_id registration, init_code_hash and runtime_code_hash commitment storage in Code Vault.**
- Implement EVM Chain atomic cross-chain messaging and precompiles for Mirror GBL and Code Vault queries.
- Implement EVM Chain Contract Mirror Registry (CMR) for deployment mirror state tracking and authorization.
- **Implement CMR integration with Code Vault: code_id references, verification_level policies, authorization proofs.**
- Implement CMR synchronization with Federal Chain subnet registry.
- Implement Main chain registry contracts (regions, subnets, publishers, pin providers).
- Implement Federation Contract Registry with CREATE2 verification and code_hash tracking.
- Implement RegionDeployer and FederationDeployer contracts on Main.
- **Implement ensureDeployedAndCall() function in RegionDeployer for lazy mirroring (deploy-on-first-use).**
- **Implement CMR authorization proof verification in RegionDeployer (checkpoint Merkle proofs or ZK proofs).**
- **Implement runtime bytecode verification against Code Vault runtime_code_hash after CREATE2 deployment.**
- Implement checkpoint acceptance contract and quorum verification (BLS aggregate or equivalent).
- Implement cross-region transfer tracking via Mirror Chain UTXO transitions and conservation invariant verification.
- Implement federation fee collection and treasury distribution.
- Implement governance framework (proposal lifecycle, timelocks, two-chamber vote scaffolding).
- Implement basic fee market and reward distribution accounting (no pinning yet).

### 15.3 Milestone 2: CSS-1 region chain prototype

- Implement CRVS region consensus prototype (fast/slow path; relay plane fallback).
- Implement Smart Slot envelope parsing and deterministic scheduler in the EVM engine.
- Deploy RegionDeployer on region chains with identical address to Main.
- Implement region-first deployment with target_regions[] declaration.
- Implement federation mirroring receiver (mirror() function with authorization verification).
- Implement two-phase initialization pattern for mirrored contracts.
- **Implement ensureDeployedAndCall() support on regional RegionDeployer contracts.**
- **Add test suite: deterministic address tests across regions, deploy-on-first-use functionality tests.**
- **Add security tests: unauthorized deployment attempts, code integrity verification, constructor safety validation.**
