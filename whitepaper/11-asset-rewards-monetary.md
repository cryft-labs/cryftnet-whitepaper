   
5) INITIAL MINT (Main only):
   - Circle calls USDC.mint(Circle, 1_000_000_000)
   - Mirror GBL creates: UTXO(USDC, Main, Circle, 1B)
   - Mirror GBL records: total_supply[USDC] = 1B
   
6) DEPLOY ON REGIONS (after checkpoint):
   - Each region deploys same code at 0xUSDC
   - All regional contracts start with ZERO balances
   - Only Main has Circle's balance
   
7) DISTRIBUTION:
   - Circle transfers USDC to users via normal transfers
   - Cross-region transfers move balances as needed
   - Mirror Chain GBL always enforces: sum(regional) = total_supply
```

**Racing attack is now impossible:**

```text
Attack attempt: Attacker races to deploy on Region B before Main checkpoint

1) Attacker tries to call FederationDeployer.deploy(USDC_bytecode, salt) on Region B
2) FederationDeployer checks authorization from Main checkpoint
3) Authorization not yet received ->' REVERTS
4) Attacker cannot deploy

Even if attacker deploys their own version:
- Uses different deployer ->' different address (not 0xUSDC)
- Not in Federation Registry ->' wallets warn users
- Cannot mint because they're not authorized_minter on a verified contract
```

**Handling native CRYFT:**

The native gas token (CRYFT) uses the same partitioned model, but at the protocol level rather than contract level:

- Each region tracks CRYFT balances independently.
- Cross-region CRYFT transfers use the same debit-checkpoint-credit flow.
- Main tracks total supply and ensures conservation: sum(region_balances) = total_supply.

**Comparison: Partitioned vs. Wrapped model:**

| Aspect | Partitioned Balances | Wrapped Tokens (LMB) |
|:-------|:--------------------|:---------------------|
| User mental model | "I have 300 USDC on Region A" | "I have 300 wUSDC (wrapped) on Region A" |
| Contract address | Same everywhere | Different (bridge + wrapped token) |
| Token symbol | Same (USDC) | Different (wUSDC, USDC.a, etc.) |
| Transfer mechanism | transferToRegion() | lock() + claim() |
| Accounting | Sum of regional balances | Locked on home + wrapped on others |
| Implementation complexity | Simpler | More contracts |
| Wallet UX | Cleaner (one token, regional balances) | Confusing (multiple token symbols) |

**Recommendation:** Use the **partitioned balance model** as the default for CSS-1 regions. The wrapped token model remains available for custom subnets or bridging to external chains (Ethereum, etc.).

**Supply conservation invariant:**

```text
For any token T deployed via federation registry:

sum (balances[region][account] for all accounts, for all regions) = total_supply[T]

This is verified by:
1) Each region reports its total balance in checkpoints
2) Main aggregates and verifies: sum(region_totals) = expected_supply
3) Discrepancy triggers investigation and potential bridge pause
```

**Handling the "follow-me" mirroring case:**

The account mirroring feature (Section 10.6) can work with the partitioned model, but requires careful design. Mirroring allows a user to have **spending authorization** across multiple regions without explicitly transferring each time.

**Important:** Mirroring does NOT duplicate assets. It provides a **credit line** mechanism:

1. User deposits assets on Main into a mirroring contract.
2. Mirroring contract grants spending credit to selected regions.
3. User can spend up to their credit on any mirrored region.
4. Main reconciles all spending after checkpoints and adjusts remaining credit.
5. If user overspends (double-spend attempt), later transactions are reverted.

```text
Mirroring with partitioned balances:

User Alice enables mirroring for 1000 USDC across regions [A, B, C]:

Step 1: Deposit
- Alice transfers 1000 USDC from her Region A balance to Main mirroring contract
- Her Region A balance: 1000 ->' 0 USDC
- Main mirroring contract holds: 1000 USDC for Alice

Step 2: Credit allocation
- Main grants Alice credit_line = 1000 on each mirrored region
- This is NOT balance duplication--it's spending authorization

Step 3: Spending
- Alice spends 300 on Region A ->' local_spent[A] = 300
- Alice spends 200 on Region B ->' local_spent[B] = 200
- Total spent: 500, within 1000 limit ✓

Step 4: Reconciliation (on checkpoint)
- Main receives: spent_A=300, spent_B=200, spent_C=0
- Main debits mirroring contract: 1000 - 500 = 500 remaining
- New credit_line pushed to regions: 500 each

Step 5: Double-spend attempt (attack)
- Alice tries to spend 400 on A and 400 on B simultaneously (total 800)
- Before sync: both succeed locally (each within 500 credit)
- Checkpoint order: A finalizes first ->' spent_A=400, remaining=100
- B's checkpoint arrives ->' spent_B=400 would exceed remaining
- Main rejects B's spend, marks for revert on Region B
- Alice penalized; mirroring may be suspended
```

The key insight: **mirroring converts partitioned balances into a credit system**, where Main is the source of truth and regions operate optimistically with reconciliation.

**Protocol-level enforcement:**

The single-location invariant (or partitioned balance integrity) is enforced at multiple layers:

1. **Partitioned balance contracts** track per-region balances separately.
2. **Cross-region transfers** require debit-checkpoint-credit flow.
3. **Checkpoint verification** (on Main) ensures only valid debits are recognized.
4. **Claim verification** (on destination) verifies Merkle proofs and tracks consumed transfer_ids.
5. **ZK validity proofs** (optional) make forgery computationally infeasible.
6. **Federation Contract Registry** ensures same code at same address across regions.
7. **Slashing** for validators who sign invalid checkpoints.

**Emergency procedures:**

If a bug or attack causes balance discrepancy:

1. **Pause cross-region transfers** via federation governance emergency action.
2. **Audit discrepancy** using checkpoint history on Main.
3. **Reconcile** by adjusting balances on affected region(s) or compensating from treasury.
4. **Post-mortem** and protocol upgrade to prevent recurrence.

The combination of partitioned balances, cryptographic proofs, deterministic deployment, and governance oversight ensures that the sum of all regional balances always equals the canonical supply.

---

## 11. Asset model, rewards, and monetary policy

### 11.1 Native gas asset across the federation

CryftNet uses a native gas asset (denoted CRYFT in this document) for transaction fees on Main and
on CSS chains by default. Custom subnets may use alternative fee assets, but must publish their fee
asset policy in their Federation Interface Declaration. A consistent fee asset simplifies routing, pricing,
and cross-chain UX, but is not mandatory for all subnets.

### 11.2 Fee markets

There are multiple fee markets: - Execution fees: EVM gas fees on Main and on subnets. - Settlement
fees: fees for anchoring checkpoints and relaying cross-chain messages. - CGS fees: fees for private
intent propagation, threshold services, and spam resistance. - Storage/pinning fees: budgets
attached to pin jobs for IPFS availability.

### 11.3 Validator rewards: Primary Network and regions

**v1 Fixed Policy (Mainnet Launch):**
CryftNet mainnet v1 launches with a **fixed monetary policy** (see Appendix 16.8 for canonical specification):
- **No emission**: 0 CRYFT/block (no inflation)
- **Fee distribution**: 50% burned, 30% to validator rewards, 20% to treasury
- **Minimum stake**: 1,000 CRYFT for Primary Network validators
- **Slashing rate**: 5% of stake per provable misbehavior (see Section 11.3.2 for v1 evidence specification)

This v1 policy provides economic predictability for mainnet launch.

#### 11.3.1 v1 Slashing Evidence Specification (Snowman Consensus)

**Provable Misbehavior Set for v1 (Snowman/Avalanche Consensus):**

Unlike BFT consensus protocols with explicit double-vote detection, Snowman consensus does not produce a simple "conflicting block signature" evidence surface. v1 slashing is limited to behaviors with **cryptographically verifiable on-chain evidence**.

**Slashable in v1:**

1. **Checkpoint Equivocation (5% stake)**
   - **Evidence**: Two checkpoint signatures from same validator for same height with conflicting state roots.
   - **Messages**: `CheckpointSignature{height, state_root, merkle_root, validator_pubkey, signature}`
   - **Verification on Federal Chain**:
     ```
     1. Verify both signatures are valid for validator_pubkey
     2. Verify height is identical
     3. Verify state_root or merkle_root differ
     4. Verify validator was in active set at that height
     ```
   - **Rationale**: Checkpoints anchor region/subnet state to Federal Chain; conflicting checkpoints enable double-spend attacks on cross-chain transfers.

2. **Invalid Bundle Proposal (3% stake)**
   - **Evidence**: Bundle proposal with provably invalid state transition (e.g., violated cross-chain invariant, invalid EVM execution).
   - **Messages**: `BundleProposal{height, federal_block, mirror_block, evm_block, proposer_sig}` + `InvalidStateProof{violated_invariant, merkle_proof}`
   - **Verification on Federal Chain**:
     ```
     1. Verify proposer signature on bundle
     2. Re-execute state transition deterministically
     3. Verify invariant violation (e.g., Mirror debit != EVM credit)
     4. Verify proposer was scheduled for that bundle height
     ```
   - **Rationale**: Primary Network atomic bundles require all three VMs to execute validly; proposers who submit invalid bundles are penalized.

3. **Cryftee Attestation Fraud (10% stake)**
   - **Evidence**: Node submits attestation claiming valid Cryftee modules, but peer verification or governance audit proves attestation is forged or modules are malicious.
   - **Messages**: `AttestationClaim{node_id, module_hashes[], signature}` + `FraudProof{challenge_response, verification_failure}`
   - **Verification on Federal Chain**:
     ```
     1. Verify attestation signature matches validator's registered key
     2. Governance committee or quorum of validators submit counter-proof
     3. Counter-proof shows module hashes do not match canonical registry OR attestation signature is invalid
     ```
   - **Rationale**: Cryftee attestation is a security-critical requirement for validators; forging attestation undermines the entire execution integrity model.

**NOT Slashable in v1 (lack of objective proof substrate):**

1. **Snowman Vote Equivocation**: Snowman uses preference signaling, not finalization votes. Validators may legitimately change preferences during the consensus process. No objective "double-vote" surface exists.

2. **Block Withholding**: Validators in Snowman do not have explicit block proposal duties based on deterministic assignment. Withholding cannot be proven without timing assumptions that are not consensus-safe.

3. **Invalid Snowman Block Propagation**: Invalid blocks are rejected by peers during normal consensus operation; propagating an invalid block is not distinguishable from network errors or software bugs. No objective evidence format exists.

4. **Liveness Failures**: Offline validators or delayed block production cannot be slashed because network conditions, hardware failures, and software bugs are indistinguishable from intentional behavior.

**Evidence Submission Flow:**

1. **Observation**: Any network participant observes slashable misbehavior.
2. **Evidence Construction**: Participant constructs evidence package with required cryptographic proofs.
3. **On-Chain Submission**: Evidence submitted to Federal Chain via `submitSlashingEvidence(evidence_bytes)` transaction.
4. **Automated Verification**: Federal Chain VM verifies evidence deterministically using rules above.
5. **Slashing Execution**: If valid, Federal Chain immediately:
   - Reduces validator's bonded stake by slashing percentage
   - Marks validator as "slashed" (may affect future participation)
   - Burns slashed amount or distributes to treasury per governance policy
6. **Appeal Process**: Validator may appeal via governance proposal within 30 days; requires supermajority vote to reverse.

**Future Flexibility (Post-Mainnet via Governance):**
After mainnet stabilizes, governance may propose adjustments including:
- Optional emission schedules
- Adjustable fee burn rates and reward splits  
- Regional reward weight tuning
- CGS service provider compensation models

Any changes require supermajority governance approval on Federal Chain.

#### 11.3.2 Parameter table (example defaults)

| Parameter | Symbol | Example | Notes |
|:----------|:-------|:--------|:------|
| Epoch length | EPOCH | 10 minutes (regions), 30 minutes (Main) | Regions shorter; Main longer for stability |
| Fast quorum | q_fast | 67% | Used in CRVS fast path |
| Slow quorum | q_slow | 80% | Used in CRVS slow path |
| Ping RTT max (region) | RTT_MAX | 80 ms | Eligibility gate; region-specific |
| Ping quorum | q_beacon | >= 3 of 5 beacons | Prevents single beacon bias |
| Slashing max | SLASH_MAX | up to 5% stake | For provable misbehavior; governed |

```text
Example weight policy (governance-controlled):
w_main   = 0.35
w_regions= 0.45
w_cgs    = 0.10
w_treas  = 0.10   // treasury accumulation
(These are illustrative, not fixed.)
```

Within a validator set, rewards are distributed by a combination of stake weight and performance:

- **stake_weight(v):** based on bonded stake (and delegated stake where supported)
- **perf(v):** based on uptime, vote participation, relay responsiveness, and (for regions) eligibility score from pings

```text
RewardShare(v) = stake_weight(v)^a * perf(v)^b / Z
```

with exponents a,b set by governance (typical: a near 1, b in [0.3, 1.0]).

**Figure 2: Reward flows (illustrative)**

This diagram shows how fees and emissions flow through the treasury to various network participants. Fees collected from transactions and newly minted tokens (emissions) flow into the Treasury, which distributes rewards to Main validators, Region validators, CGS service providers, and IPFS pin providers according to governance-defined policies.

```mermaid
flowchart LR
  Fees[Fees] --> Treasury[Treasury / Policy]
  Emission[Emission] --> Treasury
  Treasury --> MainV[Main validators]
  Treasury --> RegionV[Region validators]
  Treasury --> CGS[CGS / service providers]
  Treasury --> Pins[Pin providers]
```

### 11.4 IPFS pinning rewards: availability as a protocol primitive

CryftNet treats IPFS availability as a rewarded service rather than a background assumption. Pinning
rewards are designed to keep critical content (portals, module binaries, and app assets) available
with measurable reliability. Key components: 1) Pin Provider Registry: providers stake/bond and
advertise a service endpoint (or declare they operate via Cryftee ipfs_v1). 2) Pin Jobs: on-chain

### 11.5 Economics with zero emission: validator incentives at launch (v1 bootstrap model)

**Critical investor question:** "If there's no inflation, why do validators show up on day 1?"

Zero-emission monetary policy is economically sustainable **only if** early validator economics are explicitly addressed. This section provides the v1 bootstrap model.

#### 11.5.1 Fee volume expectations (launch economics)

**Realistic fee projections (conservative model):**

`	ext
Assumptions (Month 1 post-mainnet):
- Primary Network transactions:  100-500 tx/block (~6,000-30,000 tx/day)
- Average gas price:             20 gwei (~.05 per tx at  ETH-equivalent pricing)
- Regional State transactions:   10-50 States active, 1,000-10,000 tx/day each
- Cross-region transfers:        100-500/day (higher fees: -5 per transfer)

Daily fee revenue (Month 1):
  Primary Network:   6,000 tx * .05 = /day
  State chains:      10 States * 5,000 tx * .03 = ,500/day
  Cross-region fees: 200 transfers *  = /day
  Total daily fees:  ~,200/day = ,000/month

Validator count (Month 1): 100 validators
Fee distribution (50% burn, 30% validators, 20% treasury):
  Validator pool: ,200 * 0.30 = /day
  Per-validator:   / 100 = .60/day = /month

Cost to run validator (AWS c5.2xlarge + bandwidth): ~-200/month
Break-even: Achieved at Month 1 with conservative usage
`

**Month 6 projections (growth scenario):**

`	ext
Assumptions:
- 10x transaction growth (early dApp adoption, DeFi migration)
- 50 active States (regional expansion)
- 5,000 cross-region transfers/day

Daily fee revenue (Month 6):
  Primary Network:   60,000 tx * .05 = ,000/day
  State chains:      50 States * 10,000 tx * .03 = ,000/day
  Cross-region fees: 5,000 transfers *  = ,000/day
  Total daily fees:  ~,000/day = ,000/month

Validator count (Month 6): 300 validators
Per-validator (30% to validator pool):
  ,000 * 0.30 / 300 = /day = /month

Validator profit margin:  -  (costs) = /month (+320% ROI)
`

**Key insight:** Even with zero emission, validators are profitable at modest adoption levels due to fee-based rewards.

#### 11.5.2 Genesis distribution and validator bootstrap incentives

**Problem:** Validators incur costs (hardware, bandwidth, staking capital) before fee revenue materializes.

**Solution: Genesis allocation includes validator bootstrap program**

**Genesis CRYFT distribution (total supply: 1,000,000,000 CRYFT):**

| Allocation | Amount | % | Purpose | Vesting |
|:-----------|:-------|:--|:--------|:--------|
| **Genesis validators** | 100,000,000 | 10% | Rewards for first 100 validators (Days 0-180) | 6-month linear unlock |
| **Treasury** | 300,000,000 | 30% | Protocol development, grants, ecosystem growth | DAO-controlled |
| **Core team & advisors** | 150,000,000 | 15% | Cryft Labs team, strategic advisors | 4-year vest, 1-year cliff |
| **Early investors** | 200,000,000 | 20% | Seed/Series A fundraising | 2-year vest, 6-month cliff |
| **Community sale** | 150,000,000 | 15% | Public token sale (fair launch component) | No lockup |
| **Ecosystem incentives** | 100,000,000 | 10% | Liquidity mining, State chain grants, developer rewards | DAO-controlled, 2-year distribution |

**Genesis validator program (v1 specific):**

`	ext
Validator Bootstrap Rewards (100M CRYFT / 180 days):

Formula:
  daily_pool = 100,000,000 / 180 = 555,555 CRYFT/day
  validator_share = (validator_uptime * validator_stake) / total_weighted_stake

Minimum requirements:
  - Stake: 1,000 CRYFT (genesis validators can stake from bootstrap allocation)
  - Uptime: >95% (measured via missed block proposals and checkpoint signatures)
  - Hardware: Meets CSS-1 specifications (8 vCPU, 32GB RAM, 1TB NVMe)

Reward cliff:
  Days 0-30:   100% of formula (maximum rewards for early validators)
  Days 31-90:  75% of formula (reduced as fee revenue grows)
  Days 91-150: 50% of formula
  Days 151-180: 25% of formula (phase-out as fees dominate)
  Days 181+:    0% (pure fee-based economics)

Example validator (Day 15, 1,000 CRYFT stake, 98% uptime):
  Assume 100 validators, all 1,000 stake, 95% avg uptime:
  daily_pool = 555,555 CRYFT
  validator_share = (0.98 * 1000) / (95 * 1000) = 1.03% (slightly above average)
  daily_reward = 555,555 * 0.0103 = 5,722 CRYFT (~,400 at  CRYFT)
  
  Compare to Month 1 fee revenue: .60/day
  Total validator income (Month 1): ,406/day (bootstrap) + .60/day (fees)
  
  Break-even time: Day 1 (bootstrap rewards cover all costs)
`

**Vesting and anti-gaming:**

- Bootstrap rewards vest linearly over 6 months (cannot dump immediately)
- Validators who drop below 90% uptime forfeit that day's rewards (redistributed to honest validators)
- Validators slashed for misbehavior lose all unvested bootstrap allocation
- Minimum participation period: 30 days (early exit forfeits 50% of earned rewards)

#### 11.5.3 Regional State fee subsidies (opt-in mechanism)

**Problem:** New State chains have low transaction volume initially, making it hard to attract validators.

**Solution: State deployers can subsidize fees using treasury grants or self-funding**

**State Fee Subsidy Pool (governance-approved mechanism):**

`solidity
contract StateFeeSubsidyPool {
    mapping(uint64 region_id => uint256 subsidy_balance) public subsidies;
    
    // State deployer or DAO deposits subsidy budget
    function depositSubsidy(uint64 region_id, uint256 amount) external {
        require(msg.sender == regionDeployer[region_id] || msg.sender == DAO, "Unauthorized");
        subsidies[region_id] += amount;
    }
    
    // Validators claim subsidized rewards (on top of base fees)
    function claimSubsidy(uint64 region_id, uint256 epoch) external {
        require(isValidator(msg.sender, region_id), "Not validator");
        
        // Calculate validator's share based on participation
        uint256 validatorShare = calculateShare(msg.sender, region_id, epoch);
        uint256 subsidy = subsidies[region_id] * validatorShare / totalShares[region_id];
        
        // Pay out (capped by remaining subsidy balance)
        uint256 payout = min(subsidy, subsidies[region_id]);
        subsidies[region_id] -= payout;
        payable(msg.sender).transfer(payout);
        
        emit SubsidyClaimed(region_id, msg.sender, payout, epoch);
    }
}
`

**Subsidy policy examples:**

`	ext
Example 1: Enterprise State (self-funded)
- Deployer: MegaCorp deploys State 1042 for internal supply chain dApp
- Subsidy budget: ,000 CRYFT (from MegaCorp treasury)
- Duration: 12 months
- Validator incentive: ,000 / 12 months / 20 validators = /validator/month
- MegaCorp benefits: Guaranteed validator participation, low fees for internal users

Example 2: Community State (DAO grant)
- Deployer: DeFi DAO deploys State 1101 for decentralized exchange
- Subsidy budget: 500,000 CRYFT (approved via CryftNet DAO proposal)
- Duration: 6 months (bootstrap only)
- Validator incentive: Tapers from /month (Month 1) to /month (Month 6)
- DAO benefits: Attracts early liquidity, then transitions to fee-based sustainability

Example 3: No subsidy (organic growth)
- Deployer: Public goods State (donation-funded)
- Subsidy budget: 0 CRYFT
- Validator incentive: Pure fee-based (validators join only if volume justifies)
- Result: Slower initial adoption but no artificial incentives
`

**Governance controls:**

- Treasury-funded subsidies require DAO vote (>51% approval)
- Maximum subsidy per State: 1,000,000 CRYFT (prevents capture)
- Subsidy duration cap: 24 months (forces transition to sustainability)
- Audit requirement: Subsidized States must publish monthly transaction volume reports

#### 11.5.4 Treasury validator stipends (emergency backstop, governance-gated)

**Problem:** Catastrophic scenariousage crashes, fee revenue drops below validator costs, validators churn.

**Solution: Treasury emergency validator stipend program (requires DAO supermajority)**

**Activation criteria (all must be true):**

1. Network-wide fee revenue <,000/day for 14 consecutive days
2. Validator count drops below 75 (security threshold: 100 minimum)
3. DAO approves emergency stipend via 67% supermajority vote
4. Treasury balance >5,000,000 CRYFT (sufficient runway)

**Stipend structure (if activated):**

`	ext
Duration: Maximum 90 days (must resolve underlying usage problem, not prop up indefinitely)
Amount: /validator/month (covers AWS costs + 50% margin)
Eligibility: Validators with >95% uptime over previous 30 days
Cap: 150 validators maximum (total cost: /month from treasury)

Conditions:
  - DAO must simultaneously approve "usage recovery plan" (marketing, partnerships, fee reductions)
  - Stipend automatically sunsets after 90 days (requires re-vote to extend)
  - If fee revenue recovers to >,000/day, stipend ends immediately (return unused funds to treasury)
`

**Why this works without long-term dependency:**

1. **Time-limited:** 90-day maximum forces focus on fundamentals (usage, product-market fit)
2. **Supermajority gating:** Prevents frivolous use (requires broad community consensus that network is worth saving)
3. **Auto-sunset:** No "perpetual UBI" for validators; stipend ends when crisis resolves or time expires
4. **Transparency:** All stipend payments on-chain, auditable in real-time

**Historical precedent:** Similar emergency programs exist in other networks (Cosmos Hub community pool, Polkadot Treasury) but are rarely activated because fee revenue typically grows with adoption.

#### 11.5.5 Long-term sustainability model (post-bootstrap)

**Timeline: Month 7+ (bootstrap fully phased out)**

Validator economics transition to **pure fee-based model:**

`	ext
Revenue sources (no emission):
  1. Primary Network tx fees (50% burn, 30% validators, 20% treasury)
  2. State chain tx fees (70% validators, 30% treasuryhigher validator share for region work)
  3. Cross-region transfer fees (-10 per transfer, validator split)
  4. Federation fees (contract mirroring, balance portabilitytreasury for protocol overhead)
  5. Checkpoint fees (regions pay Federal Chain for settlementvalidator split)

Cost optimization (expected by Month 12):
  - Validator hardware costs decrease with software optimization (better parallelism, state pruning)
  - Bandwidth costs amortized over higher transaction volume
  - Staking capital requirements potentially reduced via governance (if network secure at lower stake)

Profitability projection (Month 12, moderate success scenario):
  Daily network fees: ,000 (conservative: 1/10th of Avalanche C-Chain at similar stage)
  Validator count: 500
  Per-validator revenue (30% to validator pool): ,000 * 0.30 / 500 = /day = /month
  Validator costs (optimized): -150/month
  Net profit: -800/month per validator (+500-800% ROI on costs, plus staking rewards)
`

**Failure scenario and pivot options:**

If fee revenue remains insufficient by Month 12:

1. **DAO can vote to introduce emission** (not permanently disabled, just initially zero)
2. **Adjust fee distribution** (e.g., 40% to validators instead of 30%, reduce burn)
3. **Reduce minimum stake** (lower capital requirements to improve validator economics)
4. **Protocol optimization** (lower validator costs via client improvements)

**Key principle:** Zero emission is the **default and target**, but governance retains flexibility to adapt if economic reality demands it. This is not ideological rigidityit's pragmatic long-term sustainability with clear bootstrap mechanics.

