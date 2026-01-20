## 4. System overview

CryftNet is organized as a federation:

- **Primary Network (Federal + Mirror + EVM):** The canonical foundation consisting of three chains: Federal Chain (validator/subnet management), Mirror Chain (native asset transfers), and EVM Chain (EVM smart contracts). Together they provide settlement, cross-chain registries, global governance, and the primary validator DAO.
- **Regional chains (States):** Low-latency committees tuned for users within a latency domain. Most user activity is expected to be region-local and finalizes quickly.
- **Local chains (Cities):** Optional, for dense communities or enterprise enclaves. These settle to a region.
- **Cryftee plane:** A sidecar runtime deployed alongside validators and infrastructure nodes, hosting signed modules and CGS.
- **IPFS plane:** Content-addressed distribution for portals, modules, and application assets, with incentives for availability.

**Figure 1: CryftNet federation overview (conceptual)**

This diagram shows the high-level federation architecture. The Primary Network (Federal Chain + Mirror Chain + EVM Chain) serves as the canonical settlement layer, with Regions providing low-latency service and optional Local chains for dense communities. Cryftee sidecars run alongside all validator nodes, hosting WASM modules and CGS. The IPFS plane provides content distribution across the network.

```mermaid
flowchart TB
  Main["Main / Federal Chain<br>(Global settlement + DAO)"]
  RegionA["Region A (CSS)<br>Low-latency committee"]
  RegionB["Region B (CSS)<br>Low-latency committee"]
  Local["Local chains<br>(optional)"]
  Custom["Custom subnets<br>(optional)"]
  Cryftee["Cryftee Sidecar<br>(WASM modules + CGS)"]
  IPFS["IPFS Plane<br>(portals, modules, content)"]
  
  RegionA -->|checkpoint| Main
  RegionB -->|checkpoint| Main
  Local -->|settle up| RegionA
  Local -->|settle up| RegionB
  Custom --> Main
  
  Cryftee -. deployed beside .- Main
  Cryftee -. deployed beside .- RegionA
  Cryftee -. deployed beside .- RegionB
  
  IPFS <--> Cryftee
  IPFS <--> Main
  IPFS <--> RegionA
  IPFS <--> RegionB
```

The Primary Network and regions are linked by checkpointing. Regions confirm locally, then periodically anchor a
signed checkpoint to Federal Chain. Cross-region transfers use these checkpoints and standard message
formats. The federation is "edge-like" in the sense that regions provide fast service nearby, but it
avoids centralized operators: validator sets are governed by DAOs and measured for eligibility using
network performance signals.

### 4.1 Primary Network architecture (Federal Chain + Mirror Chain + EVM Chain)

Inspired by Avalanche's multi-chain architecture, CryftNet's Primary Network is composed of **three specialized chains**, each optimized for a distinct role. Cryft Labs maintains first-class implementations and long-term governance over all three chains, while subnets may add additional chains as needed:

| Chain | Purpose | VM | Consensus | Typical Operations |
|:------|:--------|:---|:----------|:-------------------|
| **Federal Chain** (Federal) | Validator set management, staking, subnet lifecycle, chain registration/metadata, governance coordination | Native | Snowman (v1 baseline) | Validator add/remove, stake/unstake, subnet registration, governance proposals, slashing |
| **Mirror Chain** (Mirror) | Native asset creation and transfers optimized for throughput (UTXO-style), base asset movements | Native (UTXO) | Snowman (v1 baseline) | CRYFT transfers, asset issuance, cross-chain atomic swaps, high-frequency payments |
| **EVM Chain** (EVM Execution) | Account-based smart contract execution compatible with Solidity/Vyper tooling (the dApp chain) | EVM | Snowman (v1 baseline) | Token contracts, DEX swaps, NFTs, DeFi protocols, user dApp interactions |

**Why three separate chains?**

1. **Performance isolation:** Validator/staking traffic (Federal Chain), asset transfer traffic (Mirror Chain), and smart contract execution traffic (EVM Chain) do not compete for the same bottleneck. This prevents governance operations from being priced out during DeFi congestion, and prevents EVM gas spikes from affecting base asset transfers.

2. **Security differentiation:** Federal Chain can use more conservative parameters (larger committees, longer finality windows) for critical validator/subnet operations. Mirror Chain optimizes for throughput. EVM Chain balances speed with EVM determinism requirements.

3. **Specialized state models:** Federal Chain uses validator set / stake accounting. Mirror Chain uses UTXO for parallel asset transfers. EVM Chain uses account-based EVM state. Each model is optimal for its domain.

4. **Upgrade isolation:** EVM upgrades (new opcodes, gas changes) affect only EVM Chain. Federal Chain and Mirror Chain native VMs can evolve independently based on federation needs.

5. **Economic clarity:** Staking rewards flow through Federal Chain. Asset issuance/burns happen on Mirror Chain. DeFi fees stay on EVM Chain. Clean separation prevents cross-subsidy confusion.

6. **Atomic cross-chain coordination:** Shared validator set enables atomic messaging between chains. Block proposers produce **bundle blocks** containing state transitions for all three chains with a shared `bundle_hash = keccak256(federal_header || mirror_header || evm_header)`. Validators vote on the entire bundle atomically--failures cause rollback across all chains. **Execution semantics**: (1) Each chain's state transition validated independently against its VM rules; (2) Cross-chain message invariants verified (e.g., GBL conservation: debit on Mirror + credit on EVM must balance); (3) If ANY chain invalid OR invariant violated, entire bundle rejected; (4) Upon quorum acceptance, all three chains advance atomically to same bundle height. **Rollback boundary**: Only unfinalized bundles can be rolled back; finality is bundle-finality (single finality event for all three chains). **Failure handling**: Mid-execution failures (validator crash, network partition) trigger rollback to last finalized bundle; proposer may be slashed for invalid bundle proposal. (See Appendix 16.4 for detailed atomic messaging specification.)

   **⚠️ Architectural Note:** This atomic bundle block design is **NOT** Avalanche's standard model of separate chains with independent block production sharing only a validator set. CryftNet implements a **multi-VM atomic commit per height**--a novel kernel-level behavior where validators produce and vote on synchronized state transitions across all three VMs in a single atomic unit. This is a significant architectural departure from typical multi-chain systems and requires custom consensus/execution engine implementation. The trade-off: eliminates cross-chain bridge complexity and latency at the cost of tighter coupling between chains and more complex validator duties.

   **Bundle Block Execution Mechanics (detailed):**

   **Execution Ordering:** VMs execute in fixed order within each bundle to ensure deterministic cross-chain reads:
   ```text
   1. Federal Chain executes first (validator set updates, governance)
   2. Mirror Chain executes second (GBL updates, asset transfers, Code Vault updates)
   3. EVM Chain executes third (smart contracts, with read access to updated GBL via precompiles)
   ```

   **Cross-chain message application:** Messages are applied *before* the receiving chain executes its transactions:
   ```text
   For each chain C in [Federal, Mirror, EVM]:
     1. Apply pending cross-chain messages TO chain C (from other chains in previous bundles)
     2. Execute chain C's transactions for this bundle
     3. Generate outgoing cross-chain messages FROM chain C
     4. Validate cross-chain invariants (e.g., GBL conservation)
   ```

   **Liveness Failure Modes:**

   | Failure Scenario | Behavior | Recovery |
   |:-----------------|:---------|:---------|
   | One VM crashes during execution | Entire bundle rejected; proposer slashed for invalid bundle (see Section 11.3.2); next proposer selected | Next proposer creates recovery bundle with valid state |
   | One VM times out (>5s execution) | Bundle considered invalid; proposer may not be slashed (timeout may be environmental); next proposer selected | Governance may adjust block gas limits or VM parameters |
   | One VM produces invalid state transition | Bundle rejected during validation phase; proposer slashed for invalid bundle (see Section 11.3.2) | Next proposer creates valid bundle |
   | All three VMs execute successfully but cross-chain invariant violated | Bundle rejected; proposer slashed for invariant violation (see Section 11.3.2) | Next proposer creates bundle respecting invariants |
   | Validator set cannot reach quorum on bundle validity | Bundle remains unfinalized; timeout triggers re-proposal | After 3 failed attempts, governance intervention or automatic fallback to empty bundle |

   **Critical property:** If ANY VM fails (crash, timeout, invalid transition), the ENTIRE network waits for the next bundle proposal. There is no "partial advancement" where two chains move forward and one stays behind. This ensures atomic commit but means **liveness depends on the health of all three VMs**. If the EVM implementation has a bug that crashes on a specific opcode, Federal and Mirror chains cannot finalize new blocks until the bug is fixed.

   **Mitigation strategies for VM liveness coupling:**

   1. **Emergency governance bypass:** Main governance can vote to skip a problematic bundle (e.g., if a malicious tx exploits a VM bug). Requires supermajority (80%) + 24hr timelock.
   
   2. **Empty bundle fallback:** If bundle proposal fails 3 consecutive times, validators may propose an empty bundle (no transactions, only cross-chain message settlement). This keeps the chain alive while problematic transactions are excluded.
   
   3. **Per-VM feature flags:** Governance can temporarily disable risky VM features (e.g., new opcodes, experimental precompiles) if they threaten liveness.
   
   4. **Testnet validation:** All VM upgrades MUST be tested on incentivized testnet for >= 30 days before Main deployment.

   **Data Availability & Bandwidth Requirements:**

   To vote on a bundle, validators MUST have access to:
   - Federal header + transaction list (~10-50 KB typical)
   - Mirror header + UTXO transaction list (~50-200 KB typical)
   - EVM header + transaction list (~100-500 KB typical, could be larger for complex blocks)
   - Cross-chain message queue (~10-50 KB)
   - Cross-chain invariant proofs (~5-20 KB)

   **Total per bundle:** ~200-1000 KB depending on activity level. At 2 bundles/second (target), this is ~400 KB/s to 2 MB/s download bandwidth per validator.

   **Light vote path:** Validators may vote based on headers + Merkle roots + invariant proofs WITHOUT downloading full transaction lists. This reduces bandwidth to ~20-50 KB per bundle but requires trusting that >67% of validators validated full data. Not recommended for high-value chains.

   **Data availability sampling (DAS) integration:** Once DAS is deployed (post-mainnet), validators can use erasure coding + sampling to verify data availability with ~10-20 KB samples instead of full downloads. This improves scalability while maintaining security.

   **Crash Consistency & Persistent Checkpoints:**

   Validators maintain persistent state at three levels:

   ```text
   1. Last Finalized Bundle (LFB):
      - Federal state root at height H_f
      - Mirror state root at height H_m
      - EVM state root at height H_e
      - bundle_hash, finalization quorum signature
      - Stored on disk with fsync() guarantee before voting on next bundle
   
   2. Pending Bundle (in-memory):
      - Tentative state roots for current bundle being validated
      - Not persisted until quorum reached
   
   3. Rollback Log (write-ahead log):
      - Before applying bundle B, write: "BEGIN_BUNDLE_B, parent=LFB, changes=[...]"
      - After bundle finalized, write: "COMMIT_BUNDLE_B"
      - If validator crashes mid-bundle, on restart: discard in-progress bundle, revert to LFB
   ```

   **Crash scenarios:**

   | Crash Point | Recovery |
   |:------------|:---------|
   | During bundle execution (before voting) | Discard in-progress bundle; revert to LFB; re-sync missing bundles from peers |
   | After voting but before quorum | Local vote lost; wait for quorum from other validators; apply finalized bundle if quorum reached |
   | During bundle commit to disk | Rollback log replayed on restart; either full commit or full rollback (no partial state) |
   | After commit but before LFB update | Re-commit is idempotent; LFB pointer updated to new bundle |

   **Key invariant:** No validator can have "half-applied" bundles. Either all three chains are at bundle height H, or all three are at H-1. Partial application is impossible due to atomic commit semantics.

#### 4.1.1 Block cadence & asynchronicity

Each chain in the Primary Network (Federal, Mirror, EVM) and each region/state chain runs as an **independent Snowman instance** with its own block production loop, finality cadence, and target block interval. **Each chain uses unmodified Snowman consensus; atomic bundle blocks are a coordination layer that synchronizes finality across chains, not a modification to the consensus mechanism itself.**

- **Asynchronous production** -- Chains are **not** required to produce blocks at the same real-time cadence. Federal Chain might target 2-second blocks, Mirror 1-second, EVM 1.5-second, and individual regions 0.3–1 second -- all running in parallel.
- **Atomic finality only** -- Synchronization occurs only at the **bundle level** for the Primary Network: proposers collect state from all three chains, execute in order, and propose a single bundle vote using the shared Snowman consensus. Finality advances atomically across Federal, Mirror, and EVM only when a bundle is accepted.
- **Regions remain fully independent** -- Region/state chains produce and finalize blocks asynchronously, checkpointing upward to Federal Chain periodically (async message). No real-time coordination is required between regions or between regions and Primary.

This design preserves the performance isolation and regional low-latency goals while enabling atomic cross-chain settlement when needed.

   **Upgrade Coupling & VM Independence:**

   **Problem:** If VMs must execute in lockstep, how do we upgrade one VM without risking a network halt if the upgrade has bugs?

   **Solution: Staged upgrade with governance escape hatches**

   ```text
   Upgrade process for VM X (e.g., EVM Chain):
   
   Phase 1: Testnet deployment (30 days minimum)
     - Deploy upgraded VM on incentivized testnet
     - Monitor for liveness issues, crashes, consensus divergence
     - Bounty program for breaking the upgrade
   
   Phase 2: Governance proposal
     - Propose upgrade on Main
     - Include: upgrade block height, fallback conditions, emergency rollback procedure
     - Voting period: 14 days
     - Acceptance threshold: 67% validator vote
   
   Phase 3: Activation
     - At block height H, validators switch to new VM implementation
     - First 1000 bundles with new VM are "probation period"
     - If >3 bundle failures during probation, automatic rollback to old VM triggered
   
   Phase 4: Stabilization
     - After 1000 successful bundles, upgrade considered stable
     - Old VM implementation kept as backup for 90 days
   ```

   **Emergency rollback conditions:**

   - Governance supermajority (80%) votes to rollback
   - Automated trigger: >3 bundle failures within 1000 blocks
   - Critical bug discovered (e.g., consensus divergence, VM crash on valid input)

   **VM independence limit:** Federal, Mirror, and EVM CAN have different upgrade schedules, but their bundle execution interface must remain compatible. If EVM adds a new precompile, Federal/Mirror don't need to change. If Federal changes validator set encoding, EVM/Mirror don't need to change. **BUT:** If the bundle format itself changes (e.g., adding a 4th chain), all three VMs must upgrade together.

   **Subsystem Degradation (if atomic coordination is lost):**

   This section clarifies what happens if the bundle block system fails catastrophically:

   **If bundle blocks become non-viable (e.g., persistent liveness failures):**
   1. **Fallback to independent chains:** Federal, Mirror, and EVM can continue producing blocks independently using standard Avalanche consensus
   2. **Cross-chain coordination degrades to async bridges:** GBL updates become async message-passing instead of atomic precompile reads
   3. **Latency increases:** Cross-chain transactions require checkpoint-based settlement (5-30s instead of 2-5s)
   4. **Security model changes:** Trust assumptions shift from "single validator set consensus" to "economic security of bridge contracts"

   **The chain still produces blocks**--regional committees can finalize blocks locally even if Main bundle blocks are broken. Federation-wide atomic settlement is lost, but individual regions remain operational. This is an **acceptable degradation** because the core value (regional low-latency execution) is preserved, and only cross-region atomic settlement is affected.


**Federal Chain responsibilities:**

- **Validator Registry:** Global validator identities, stake bonds, delegation relationships, and slashing records. All staking operations occur on Federal Chain.
- **Subnet Registry:** All State/Region chains register here with their chain_id, validator set commitments, consensus parameters, and CEP compatibility declarations.
- **Checkpoint Acceptance:** Receives and validates checkpoint submissions from all registered subnets; maintains the canonical checkpoint history.
- **Governance Coordination:** Proposal lifecycle, voting tallies, timelocks, and execution triggers. Governance decisions are recorded on Federal Chain.
- **Validator Rewards Distribution:** Emission schedule, reward allocation, and validator/delegator payouts.

**Mirror Chain responsibilities:**

- **Native Asset Issuance:** Creation of new asset types (tokens, NFTs) with UTXO-based ownership.
- **High-Throughput Transfers:** Optimized for CRYFT and other native asset movements (not EVM tokens).
- **Cross-Chain Atomic Swaps:** UTXO-style atomic swaps between Mirror Chain assets and EVM Chain ERC-20 tokens.
- **Base Layer Transfers:** Users moving large amounts of CRYFT between wallets typically use Mirror Chain (lower fees than EVM Chain EVM gas).

**EVM Chain responsibilities:**

- **EVM Smart Contracts:** All Solidity/Vyper contracts, DeFi protocols, NFT marketplaces, and dApps.
- **Contract Mirror Registry (CMR):** Authoritative record of federation contract deployments--tracking target_regions[], deployed_regions[], mirror_status per region, and deployment fees paid. Updated via region checkpoints. Lives on EVM Chain (not Mirror).
- **Federation Contract Registry:** Tracks CREATE2 deployments, code hashes, and cross-region contract verification.
- **User-Facing dApp Interface:** When users "interact with CryftNet," they typically transact on EVM Chain (or regional EVM Chain instances).
- **GBL Access:** EVM Chain contracts query Mirror Chain's GBL via atomic cross-chain messaging or precompiles.

**Mirror Chain additional responsibilities:**

- **Global Balance Ledger (GBL):** The authoritative partitioned ledger for EVM token balances across all regions, **managed by Mirror Chain using an extended UTXO model**. Each UTXO includes metadata: {asset_id, region_id, account, amount}, tracking which account owns how much of each asset on which region. Mirror Chain serves as the single source of truth for partitioned balances; EVM Chain and subnets access GBL state via atomic cross-chain messaging or precompiles. Native CRYFT balances also use Mirror Chain (standard UTXO). **GBL tracking is opt-in for subnets--no custom bridge contracts required.**

- **Code Vault (Bytecode Vault):** The canonical storage and commitment layer for federation-deployable smart contract code. Stores code metadata including init_code_hash, runtime_code_hash, and optionally init_code blobs or IPFS CIDs. Each code package is assigned a unique code_id and is cryptographically committed. EVM Chain's CMR references these code_ids for deployment authorization and verification. Mirror Chain does NOT execute smart contracts--it only stores code commitments to enable deterministic CREATE2 deployment across regions. Regions verify deployed bytecode matches the runtime_code_hash from the Code Vault after deployment. This enables lazy mirroring (deploy-on-first-use) while guaranteeing identical contract addresses across all opted-in regions.

**Global Balance Ledger (GBL) architecture:**

The GBL tracks **EVM token balances** (ERC-20, ERC-721, etc.) across regions using **Mirror Chain's extended UTXO model**. Native CRYFT also uses standard UTXO on Mirror Chain. The GBL is **managed entirely by Mirror Chain** as a partitioned ledger; EVM Chain and subnets access it via atomic cross-chain messaging.

**CryftNet supports two distinct portability modes for federation tokens:**

#### 4.1.2 Federation Token Portability Modes

**Mode A: GBL-Authoritative (Recommended for Federation-Backed Assets)**

Mirror Chain GBL stores per-account balances as `(asset_id, region_id, account, amount)` UTXOs. The EVM-side token contract is an ERC-20 façade that routes all balance-changing operations through the GBL precompile. Any local `balances` mapping is a read-only cache for UX/indexing convenience only.

**Use cases:**
- Stablecoins (USDC, USDT)
- CRYFT-wrapped assets
- Federation-verified tokens requiring instant global truth
- Assets where cross-region settlement must be atomic per-transaction

**Trade-offs:**
- ✅ **Per-transaction atomicity:** Cross-region transfers settle immediately with Mirror GBL state update
- ✅ **Instant global truth:** Any node can query canonical balance from Mirror GBL
- ✅ **Maximum safety:** Conservation invariant enforced per bundle block
- ⚠️ **Precompile overhead:** Every transfer incurs GBL precompile gas cost (5000 gas)
- ⚠️ **EVM composability friction:** Contracts must use precompile instead of native Solidity mappings

**Mode B: State-Authoritative with GBL-Allocated Totals (Opt-in for Lower-Cost Assets)**

The State/Region EVM contract maintains authoritative per-account balances (standard ERC-20 `balances` mapping). Mirror Chain GBL stores only **State allocations** as `(asset_id, region_id, allocated_total)`. Each State's sum of account balances must not exceed its GBL allocation. Safety is enforced at checkpoint boundaries, not per-transaction.

**Use cases:**
- Gaming tokens
- Loyalty points
- Regional/local assets with lower security requirements
- High-frequency trading assets where per-tx precompile cost is prohibitive

**Trade-offs:**
- ✅ **Standard ERC-20 composability:** Contracts behave like normal Solidity tokens
- ✅ **Lower per-transfer cost:** No precompile overhead; transfers are local EVM operations
- ✅ **Higher throughput:** Amortizes cross-region validation to checkpoint intervals
- ⚠️ **Checkpoint-security model:** Safety depends on checkpoint verification, not per-tx atomicity
- ⚠️ **Delayed global truth:** "What's my total balance across regions?" requires indexing multiple chains
- ⚠️ **Requires stronger proofs:** Must verify State totals at checkpoint time (quorum sigs or ZK proofs)

**Mode selection is declared at asset registration time and is immutable.** Wallets and explorers MUST check an asset's portability mode to correctly display balances and security guarantees.

```text
GlobalBalanceLedger (Mirror Chain extended UTXO) {
  // Each UTXO carries metadata for partitioned balance tracking
  utxo_set: [
    {
      utxo_id: bytes32,           // Unique UTXO identifier
      asset_id: address,          // EVM token address (or CRYFT for native)
      region_id: uint64,          // Which region this balance belongs to
      account: address,           // EVM account owner
      amount: uint256,            // Balance amount
      lock_script: bytes,         // Spend authorization (signature requirements)
    },
    ...
  ]
  
  // Total supply per asset (derived from UTXO set)
  // total_supply[asset] = sum(utxo.amount for utxo in utxo_set if utxo.asset_id == asset)
  
  // Pending cross-region transfers (also as UTXOs with pending status)
  pending_transfers: [
    {
      transfer_id: bytes32,
      asset_id: address,
      amount: uint256,
      from_region: uint64,
      to_region: uint64,
      sender: address,
      recipient: address,
      initiated_checkpoint: uint64,
      status: enum { Pending, Claimed, Expired, Refunded },
    },
    ...
  ]
  
  // Conservation invariant: sum(utxo.amount for asset_id) == total_supply[asset_id]
}
```

#### 4.1.3 Mode A: GBL-Authoritative Federation Token Standard (Normative Specification)

**A.1 Source of Truth**

For Mode A (GBL-Authoritative) tokens, the authoritative balance for any account on a region is `GBL.queryBalance(asset_id, region_id, account)`. The ERC-20 contract **MUST NOT** make transfer decisions based on any local `balances[account]` mapping. Any local mapping is a UI cache only and MUST be ignored for transfer validation.

**A.2 ERC-20 Function Semantics (Normative)**

```solidity
// Mode A compliant ERC-20 contract MUST implement:

function balanceOf(address account) external view returns (uint256) {
    // MUST query GBL precompile, MUST NOT use local storage
    return GBL.queryBalance(ASSET_ID, REGION_ID, account);
}

function totalSupply() external view returns (uint256) {
    // MUST query GBL for asset-wide total
    return GBL.totalSupply(ASSET_ID);
}

function transfer(address to, uint256 amount) external returns (bool) {
    // MUST call GBL precompile; MUST revert if precompile reverts
    require(GBL.transfer(ASSET_ID, REGION_ID, msg.sender, to, amount), "GBL transfer failed");
    emit Transfer(msg.sender, to, amount);
    return true;
}

function transferFrom(address from, address to, uint256 amount) external returns (bool) {
    // MUST enforce local allowance first (standard ERC-20)
    uint256 currentAllowance = allowances[from][msg.sender];
    require(currentAllowance >= amount, "Insufficient allowance");
    
    // MUST call GBL precompile; MUST revert if precompile reverts
    require(GBL.transfer(ASSET_ID, REGION_ID, from, to, amount), "GBL transfer failed");
    
    // MUST decrement allowance only if GBL call succeeds
    // (automatic due to revert-on-failure above)
    allowances[from][msg.sender] = currentAllowance - amount;
    
    emit Transfer(from, to, amount);
    return true;
}
```

**A.3 Approval Handling (Region-Local)**

- `approve()` and `allowance()` are **region-local** and **contract-local** (standard ERC-20 mapping)
- Approvals **do NOT move with the user across regions automatically**
- `permit()` (EIP-2612) is allowed but also region-local; domain separator MUST include `chainId` or region context

**A.4 Event Emission Rules (Normative)**

**Invariant FT-GBL-01 (Authoritative State):**
For any successful transaction that results in an ERC-20 `Transfer(from, to, amount)` event on region R, the post-state MUST satisfy:

```
GBL.balance(asset, R, from)_after = GBL.balance(asset, R, from)_before − amount
GBL.balance(asset, R, to)_after = GBL.balance(asset, R, to)_before + amount
```

This GBL transition MUST be the one executed by the precompile call inside the transaction.

**Invariant FT-GBL-02 (No Phantom Logs):**
If `GBL.transfer(...)` reverts, the transaction MUST revert and no `Transfer` event is observable.

**A.5 Cross-Region Transfer Events**

For cross-region moves via `transferToRegion()`, **do NOT** emit only a `Transfer` event (confuses indexers). Instead:

```solidity
event TransferToRegionInitiated(
    bytes32 indexed transferId,
    address indexed from,
    address indexed to,
    uint256 amount,
    uint64 fromRegion,
    uint64 toRegion
);

event TransferToRegionClaimed(
    bytes32 indexed transferId,
    address indexed from,
    address indexed to,
    uint256 amount,
    uint64 fromRegion,
    uint64 toRegion
);
```

**Optional ERC-20 Continuity Pattern (for naive explorers):**
Define a canonical "in-transit" address (e.g., precompile address 0x0100) and emit:
- On source region: `Transfer(from, IN_TRANSIT_ADDRESS, amount)`
- On destination claim: `Transfer(IN_TRANSIT_ADDRESS, to, amount)`

This prevents explorers from thinking supply changed while maintaining event-based accounting.

**A.6 Off-Chain Indexing Guidance**

- Indexers CAN track balances from `Transfer` logs per region (standard ERC-20 indexing)
- For canonical correctness or log recovery, indexers SHOULD reconcile by querying `GBL.queryBalance(...)`
- For "global portfolio view," wallets/indexers MUST:
  1. Call `GBL.getAccountRegions(asset_id, account)` to find regions with balances
  2. Sum `GBL.queryBalance(asset_id, region, account)` across all regions

#### 4.1.4 Mode B: State-Authoritative with GBL-Allocated Totals (Normative Specification)

**B.1 Conceptual Model**

The State/Region EVM contract is **authoritative** for per-account balances (classic ERC-20 `balances` mapping). Mirror Chain GBL stores only **State allocations**:

```
GBL_alloc(asset_id, region_id) = total tokens allocated to that region
```

**Key invariant:**
```
sum(balances[account] for all accounts on region) <= GBL_alloc(asset, region)
```

Equality holds except for burned/escrowed tokens.

**B.2 ERC-20 Function Semantics (Normative)**

```solidity
// Mode B compliant ERC-20 contract implements STANDARD ERC-20:

mapping(address => uint256) private balances;
mapping(address => mapping(address => uint256)) private allowances;

function balanceOf(address account) external view returns (uint256) {
    // Uses local state, NOT GBL precompile
    return balances[account];
}

function transfer(address to, uint256 amount) external returns (bool) {
    // Standard ERC-20 logic
    require(balances[msg.sender] >= amount, "Insufficient balance");
    balances[msg.sender] -= amount;
    balances[to] += amount;
    emit Transfer(msg.sender, to, amount);
    return true;
}

// transferFrom(), approve(), allowance() all standard ERC-20
```

**B.3 Checkpoint Invariant Enforcement (Normative)**

Each region checkpoint MUST include:

```text
CheckpointData {
  region_id: uint64,
  height: uint64,
  state_root: bytes32,
  
  // Per-asset state summary
  asset_totals: [
    {
      asset_id: address,
      region_total_supply: uint256,    // sum(balances[account]) for this asset
      delta_alloc_requests: int256,    // requested change in allocation
    },
    ...
  ],
  
  // Cross-region transfer requests
  cross_region_debits: [...],
  cross_region_credits: [...],
  
  validator_signatures: bytes[],      // Quorum signatures
}
```

**Federal Chain verification (at checkpoint acceptance):**

```text
For each asset in checkpoint.asset_totals:
  current_alloc = GBL_alloc(asset, region_id)
  reported_total = asset.region_total_supply
  
  VERIFY:
    1. reported_total <= current_alloc + delta_alloc_requests
    2. cross_region_debits are properly deducted from current_alloc
    3. cross_region_credits are properly added to current_alloc
    4. quorum signatures valid (or ZK proof verifies state transition)
  
  IF verification fails:
    REJECT checkpoint
    PAUSE bridging for this region/asset pair
    SLASH validators for invalid checkpoint
```

**B.4 Proof Requirements**

**v1 (Mainnet):** Quorum validator signatures + deterministic state transition rules
- Federal Chain trusts region validator quorum attestation
- Validators sign commitment to `(state_root, asset_totals, cross_region_messages)`

**vNext (Post-Mainnet):** ZK validity proofs
- Region submits ZK-SNARK proof that:
  - ERC-20 state transitions preserve balance conservation
  - Reported `region_total_supply` equals actual sum of balances
  - Cross-region transfers respected allocation bounds
- Federal Chain verifies proof on-chain (no trust required)

**B.5 Trade-Offs vs Mode A**

**Advantages:**
- ✅ Maximum EVM composability (standard Solidity mappings)
- ✅ No per-transfer precompile cost
- ✅ Higher throughput (checkpoint amortization)

**Disadvantages:**
- ⚠️ Checkpoint-security model (not per-tx atomic)
- ⚠️ Global truth delayed (requires multi-chain indexing)
- ⚠️ Requires ZK proofs or strong validator quorums for safety

**B.6 Asset Registration and Mode Declaration**

Assets MUST declare portability mode at registration time:

```solidity
// Federal Chain asset registry
struct AssetRecord {
    address asset_id;
    string name;
    string symbol;
    PortabilityMode mode;  // GBL_AUTHORITATIVE or STATE_AUTHORITATIVE
    uint64[] target_regions;
    // ... other metadata
}

enum PortabilityMode {
    GBL_AUTHORITATIVE,      // Mode A
    STATE_AUTHORITATIVE     // Mode B
}
```

Mode is **immutable** after registration. Changing modes would require governance-approved migration.

**Why GBL lives on Mirror Chain (not EVM Chain or Federal Chain):**

1. **UTXO efficiency:** Mirror Chain's UTXO model naturally supports parallel validation and partitioned balances without account-based contention.
2. **Native asset layer:** Native CRYFT already uses Mirror Chain UTXO; extending for EVM token tracking unifies the asset layer.
3. **Atomic cross-chain messaging:** Primary Network's three-chain architecture enables atomic reads/writes from EVM Chain to Mirror GBL.
4. **Simple and robust:** Mirror remains lean (no smart contracts)--GBL is a ledger operation, not execution.
5. **Conservation checks:** UTXO model makes conservation invariant (`sum(utxo.amount) == total_supply`) mechanically enforceable.
6. **Modularity:** EVM Chain focuses on execution; Mirror Chain focuses on asset custody and partitioned balances.
7. **Opt-in for subnets:** Subnets query Mirror GBL via precompiles or bridge contracts--no Cryftee module dependency.

**GBL update flow:**

This sequence diagram illustrates a cross-region asset transfer from State A to State B. The flow shows the debit-checkpoint-credit pattern: (1) User initiates transfer on State A, (2) State A debits local balance and includes TransferOut in its checkpoint to Mirror Chain, (3) Mirror Chain GBL consumes source UTXO and creates pending transfer UTXO, (4) State B credits the recipient's local balance on claim, (5) State B's next checkpoint confirms the claim to Mirror Chain, (6) Mirror Chain GBL consumes pending transfer UTXO and creates destination UTXO, marking transfer complete.

```mermaid
sequenceDiagram
  participant User
  participant StateA as State A
  participant Mirror as Mirror Chain (GBL)
  participant StateB as State B
  
  User->>StateA: transferToRegion(asset, amount, B, recipient)
  StateA->>StateA: Debit local balance, emit TransferOut event
  StateA->>Mirror: Checkpoint includes TransferOut
  Mirror->>Mirror: GBL: consume UTXO(asset, A, sender, amount)
  Mirror->>Mirror: GBL: create pending_transfer UTXO
  Mirror->>StateB: Checkpoint confirmation includes pending transfer
  StateB->>StateB: Credit local balance on claim
  StateB->>Mirror: Next checkpoint confirms claim
  Mirror->>Mirror: GBL: consume pending_transfer UTXO
  Mirror->>Mirror: GBL: create UTXO(asset, B, recipient, amount)
```

**EVM Chain contracts accessing Mirror GBL (Mode A Implementation Details):**

**CRITICAL:** This section applies to **Mode A (GBL-Authoritative) tokens only**. For Mode B, see Section 4.1.4.

For Mode A tokens, Mirror Chain GBL is the **single authoritative source** for partitioned balances. EVM contracts MUST NOT maintain independent balance state for federation-verified tokens. Local `balances` mappings in contracts are **read-only caches** synchronized from Mirror GBL.

**Execution-time truth rule:** During transaction execution, balance reads MUST query Mirror GBL via precompile (authoritative). Local storage cache is updated post-execution for UX convenience but is NOT used for balance decisions. **Cache synchronization guarantee:** Before a transaction executes, validators ensure local cache reflects the latest Mirror GBL state from the current bundle block. Cache drift is impossible because bundle blocks are atomic across all three chains.

**Invariants enforced by validator consensus (Mode A only):**
1. **Atomic bundle guarantee:** Mirror GBL updates and EVM state transitions occur in the same bundle block. No interleaving.
2. **Pre-execution sync:** Validators MUST sync cache from Mirror GBL before executing any balance-touching transaction in the bundle.
3. **Single source of truth:** All balance decisions (transfer validation, allowance checks) use Mirror GBL precompile response, never cached storage.
4. **Post-execution consistency:** Cache updates occur deterministically after successful Mirror GBL state change. Failures roll back both.
5. **No divergence:** If cache != GBL at bundle proposal time, bundle is invalid and rejected by honest validators.

**GBL Precompile Interface (address 0x0100):**

```solidity
interface IGBLPrecompile {
    // Query balance for (asset_id, region_id, account)
    // Returns: balance in smallest unit (e.g., wei for ETH-like tokens)
    // Gas cost: 700 gas (warm) / 2600 gas (cold, first access in tx)
    // Reverts: Never (returns 0 for non-existent balances)
    function queryBalance(bytes32 asset_id, uint64 region_id, address account) 
        external view returns (uint256 balance);
    
    // Transfer within same region (atomic, synchronous)
    // Effects: Updates Mirror GBL UTXO set atomically with EVM state
    // Gas cost: 5000 gas base + 700 per account touched
    // Reverts: If insufficient balance, invalid region_id, or GBL invariant violation
    function transfer(
        bytes32 asset_id, 
        uint64 region_id, 
        address from, 
        address to, 
        uint256 amount
    ) external returns (bool success);
    
    // Initiate cross-region transfer (async, creates pending state)
    // Effects: Debits from_region balance, creates pending claim on to_region
    // Returns: transfer_id for tracking settlement status
    // Gas cost: 15000 gas (higher due to cross-chain message queueing)
    // Settlement time: 5-30 seconds (via checkpoint to Main)
    // Reverts: If insufficient balance or invalid region configuration
    function transferToRegion(
        bytes32 asset_id, 
        uint64 from_region, 
        uint64 to_region, 
        address from,
        address to, 
        uint256 amount
    ) external returns (bytes32 transfer_id);
    
    // Query pending cross-region transfer status
    // Returns: (settled, dest_region_height) where settled=true means funds available on dest
    // Gas cost: 700 gas
    function getTransferStatus(bytes32 transfer_id) 
        external view returns (bool settled, uint64 dest_region_height);
    
    // Query total supply for asset across ALL regions
    // Useful for federation-wide token metrics
    // Gas cost: 2000 gas (aggregates across regions)
    function totalSupply(bytes32 asset_id) 
        external view returns (uint256 total);
    
    // Query which regions have non-zero balances for an account
    // Returns: array of region_ids where account has balance > 0
    // Gas cost: 5000 gas base + 100 per region
    // Use case: Wallets discovering user's multi-region balances
    function getAccountRegions(bytes32 asset_id, address account) 
        external view returns (uint64[] memory regions);
}
```

**Precompile behavior specifications:**

**Reentrancy protection:**
- GBL precompile calls are NON-REENTRANT
- If contract A calls GBL precompile, which triggers callback to A, the callback CANNOT call GBL precompile again
- Violation: Reverts with "GBL: reentrant call"
- Reason: Prevents complex cross-chain reentrancy exploits

**Failure modes and error codes:**

```text
queryBalance():
  - Never reverts
  - Returns 0 for invalid asset_id or account with no balance
  - Returns 0 if region_id not in asset's target_regions

transfer():
  - Reverts "GBL: insufficient balance" if from.balance < amount
  - Reverts "GBL: invalid region" if region_id not in asset's target_regions
  - Reverts "GBL: zero amount" if amount == 0
  - Reverts "GBL: self transfer" if from == to (no-op transfers forbidden)
  - Reverts "GBL: conservation violated" if debit+credit doesn't balance (critical error, bundle rejected)

transferToRegion():
  - Reverts "GBL: insufficient balance" if from.balance < amount
  - Reverts "GBL: invalid source region" if from_region != current_region
  - Reverts "GBL: region not federated" if to_region not in asset's target_regions
  - Reverts "GBL: zero amount" if amount == 0
  - Reverts "GBL: same region" if from_region == to_region (use transfer() instead)
```

**Gas cost rationale:**

- queryBalance (700 gas): Comparable to SLOAD, reflects Mirror UTXO read cost
- transfer (5000 gas): Comparable to ERC-20 transfer (2x SLOAD + 2x SSTORE ~= 5200 gas)
- transferToRegion (15000 gas): Higher due to cross-chain message queuing and checkpoint overhead
- totalSupply (2000 gas): Aggregates cached per-region totals (not full UTXO scan)

**Cache consistency enforcement (validator duty):**

Before executing bundle B:
  ```text
  For each asset_id in federation registry:
    For each region_id in asset's target_regions:
      cached_root = EVM_Chain.gblCacheRoot(asset_id, region_id)
      mirror_root = Mirror_Chain.gblRoot(asset_id, region_id)
      
      IF cached_root != mirror_root:
        REJECT bundle B
        REASON: "GBL cache desync detected"
        PROPOSER: Slashed (5% stake)
  ```

This check happens during Phase 4 (invariant validation) of bundle execution. Prevents cache drift from ever reaching consensus.

**Composability constraints:**

- DEXes (Uniswap, etc.) work normally within a region (GBL precompile is just a different balance read)
- Cross-region DEX trades require async settlement (initiator locks funds, counterparty claims after checkpoint)
- Flashloan compatibility: Within-region flashloans work; cross-region flashloans not supported (async nature breaks atomicity)
- Reentrancy: Standard EVM reentrancy guards still apply; GBL precompile adds its own non-reentrancy check

**ERC-20 wrapper pattern (recommended):**

```solidity
// Wrapper ensures ERC-20 compatibility while using GBL backend
contract FederatedERC20 {
    IGBLPrecompile constant GBL = IGBLPrecompile(0x0100);
    bytes32 public immutable ASSET_ID;
    uint64 public immutable REGION_ID;
    
    // Cache (synced by validators before tx execution)
    mapping(address => uint256) private _cachedBalances;
    
    function balanceOf(address account) public view returns (uint256) {
        // Always query authoritative source
        return GBL.queryBalance(ASSET_ID, REGION_ID, account);
    }
    
    function transfer(address to, uint256 amount) public returns (bool) {
        require(GBL.transfer(ASSET_ID, REGION_ID, msg.sender, to, amount), "Transfer failed");
        
        // Update cache (deterministic, validators verify this matches GBL)
        _cachedBalances[msg.sender] -= amount;
        _cachedBalances[to] += amount;
        
        emit Transfer(msg.sender, to, amount);
        return true;
    }
    
    // Standard ERC-20 allowance mechanism (region-local)
    mapping(address => mapping(address => uint256)) private _allowances;
    
    function approve(address spender, uint256 amount) public returns (bool) {
        _allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) public returns (bool) {
        uint256 currentAllowance = _allowances[from][msg.sender];
        require(currentAllowance >= amount, "Insufficient allowance");
        
        require(GBL.transfer(ASSET_ID, REGION_ID, from, to, amount), "Transfer failed");
        
        _allowances[from][msg.sender] = currentAllowance - amount;
        _cachedBalances[from] -= amount;
        _cachedBalances[to] += amount;
        
        emit Transfer(from, to, amount);
        return true;
    }
}
```


**Required pattern for federation-verified tokens:**

**Mode A (GBL-Authoritative) ERC-20 Wrapper Example:**

```text
// Federation-verified ERC-20 wrapper contract (Mode A)
contract FederationTokenModeA {
  // Local storage is CACHE ONLY - not authoritative
  mapping(address => uint256) public balances;  // synced from Mirror GBL
  
  // All balance-modifying operations MUST use Mirror GBL precompiles
  function transfer(address to, uint256 amount) external {
    // Authority: Mirror Chain GBL via precompile at 0x0000...0100
    MIRROR_GBL_PRECOMPILE.transfer(ASSET_ID, REGION_ID, msg.sender, to, amount);
    
    // Update local cache for read convenience
    balances[msg.sender] -= amount;
    balances[to] += amount;
    
    emit Transfer(msg.sender, to, amount);
  }
  
  function transferToRegion(uint64 destRegion, address to, uint256 amount) external {
    // Cross-region transfer via Mirror GBL
    bytes32 transferId = MIRROR_GBL_PRECOMPILE.transferToRegion(
        ASSET_ID, REGION_ID, destRegion, msg.sender, to, amount
    );
    balances[msg.sender] -= amount;  // debit local cache
    
    emit TransferToRegionInitiated(transferId, msg.sender, to, amount, REGION_ID, destRegion);
    emit Transfer(msg.sender, IN_TRANSIT_ADDRESS, amount);  // Optional: for indexers
  }
  
  function balanceOf(address account) external view returns (uint256) {
    // Query authoritative source (NOT local cache)
    return MIRROR_GBL_PRECOMPILE.queryBalance(ASSET_ID, REGION_ID, account);
  }
}
```

**Mode B (State-Authoritative) Standard ERC-20 Example:**

```solidity
// Standard ERC-20 with checkpoint-enforced allocation (Mode B)
contract FederationTokenModeB {
  // Local storage IS authoritative for per-account balances
  mapping(address => uint256) private _balances;
  mapping(address => mapping(address => uint256)) private _allowances;
  
  uint256 private _totalSupply;
  
  function balanceOf(address account) external view returns (uint256) {
    // Standard ERC-20: local state is authoritative
    return _balances[account];
  }
  
  function transfer(address to, uint256 amount) external returns (bool) {
    // Standard ERC-20 logic (no GBL precompile)
    require(_balances[msg.sender] >= amount, "Insufficient balance");
    _balances[msg.sender] -= amount;
    _balances[to] += amount;
    emit Transfer(msg.sender, to, amount);
    return true;
  }
  
  // transferFrom, approve, allowance all standard ERC-20
  
  // Cross-region transfers require checkpoint-level coordination
  // (not shown here; handled by Federal Chain validation at checkpoint time)
}
```

**Allowances and approvals (ERC-20 compatibility clarification):**

**Mode A (GBL-Authoritative)**: Standard `approve/allowance/transferFrom` semantics are preserved on-region. Approval mappings (`mapping(address => mapping(address => uint256)) public allowances`) live in contract storage as usual. This ensures existing DeFi contracts (Uniswap, Aave, etc.) work without modification. Approvals are **region-local** and do not automatically transfer cross-region.

**Mode B (State-Authoritative)**: Standard ERC-20 approvals work exactly as normal. No special handling required.

**For cross-region operations (both modes)**: Approvals are region-local. Cross-region token movements use direct `transferToRegion()` (sender-initiated) rather than delegated transfers. Future versions may support cross-region approval via Mirror UTXO lock scripts or checkpoint-mediated authorization.

**Trade-off**: This maintains full ERC-20 compatibility within a region (recommended) at the cost of region-local approval state. Alternative: Implement approvals as Mirror lock scripts (breaks ERC-20 compatibility but enables cross-region approvals).

**Decision**: CryftNet v1 chooses ERC-20 compatibility to maximize ecosystem adoption.

**Realism tie-in:** Mode A similar to Optimism's canonical bridged tokens (L1 authoritative, L2 cached). Mode B similar to Cosmos ICS-20 (chain-of-origin authoritative, IBC tracks allocations).

**Non-federation tokens:** Standard ERC-20 contracts without GBL integration maintain local state as usual (not partitioned across regions).

Note: Native CRYFT balances use standard Mirror Chain UTXO (not extended). EVM Chain can wrap CRYFT via bridge contract (wrapped CRYFT is ERC-20 on EVM Chain, backed 1:1 by Mirror UTXO).

**Contract Mirror Registry (CMR) architecture:**

The CMR is EVM Chain's native data structure for tracking federation contract deployments and mirror state:

```text
ContractMirrorRegistry {
  // Per-contract deployment record
  contracts: Map<contract_address ->' ContractMirrorRecord>
  
  // Region deployment queue (contracts pending mirroring)
  pending_mirrors: Map<(contract_address, region_id) ->' PendingMirror>
  
  // Fee tracking per contract
  fees_paid: Map<contract_address ->' FeeRecord>
}

ContractMirrorRecord {
  contract_address: address,
  code_hash: bytes32,
  deployer: address,
  salt: bytes32,
  home_region: uint64,                    // Where initial deployment occurred
  target_regions: uint64[],               // Regions developer opted into
  deployed_regions: uint64[],             // Regions where contract is live
  mirror_status: Map<region_id ->' MirrorStatus>,  // Per-region status
  balance_portability: bool,
  portability_mode: PortabilityMode,      // GBL_AUTHORITATIVE or STATE_AUTHORITATIVE (if balance_portability=true)
  verification_level: VerificationLevel,  // Unverified, Publisher, Federation
  created_at: uint64,
  last_updated: uint64
}

MirrorStatus {
  status: enum { Pending, Deployed, Failed, Revoked },
  deployed_at: uint64,
  init_hash: bytes32,          // Hash of initialization data
  initialized: bool,
  last_checkpoint: uint64      // Last checkpoint confirming this region
}

// Status transitions via region checkpoints:
// 1. Main receives deployment event ->' creates record, status[home] = Deployed
// 2. Main queues mirror to target_regions ->' status[target] = Pending
// 3. Region confirms deployment ->' status[target] = Deployed
// 4. Region reports failure ->' status[target] = Failed (auto-retry)
```

**CMR update flow (region-first deployment):**

```text
1) Developer deploys on Region A:
   - RegionDeployer.deploy(init_code, salt, options={target_regions: [A,B,C]})
   - Emits DeploymentEvent with region IDs and fee payment

2) Region A checkpoint -> Main EVM Chain:
   - EVM Chain processes DeploymentEvent
   - CMR creates: contracts[0xToken] = {
       home_region: A,
       target_regions: [A, B, C],
       deployed_regions: [A],
       mirror_status: {A: Deployed, B: Pending, C: Pending}
     }

3) Main triggers mirror to Regions B, C:
   - CMR updates: pending_mirrors[(0xToken, B)] = {queued}
   - CMR updates: pending_mirrors[(0xToken, C)] = {queued}

4) Region B, C receive mirror instruction and deploy:
   - RegionDeployer.mirror() called on each region
   - Region confirms in next checkpoint

5) Region B checkpoint -> Main EVM Chain:
   - EVM Chain updates CMR: deployed_regions: [A, B], mirror_status[B] = Deployed

6) Region C checkpoint -> Main EVM Chain:
   - EVM Chain updates CMR: deployed_regions: [A, B, C], mirror_status[C] = Deployed

CMR is authoritative - regions derive mirror permissions from EVM Chain state.
```

**CMR region expansion (post-deployment):**

```text
1) Developer requests expansion to Region D:
   - Calls FederationRegistry.expandRegions(0xToken, [D])
   - Pays expansion fee (0.01 CRYFT per region)

2) Checkpoint carries expansion request to Main:
   - EVM Chain verifies caller == deployer
   - EVM Chain verifies fee paid
   - CMR updates: target_regions: [A, B, C, D]
   - CMR updates: mirror_status[D] = Pending

3) Main triggers mirror to Region D

4) Region D confirms deployment in checkpoint:
   - CMR updates: deployed_regions: [A, B, C, D], mirror_status[D] = Deployed
```

**Cross-chain communication (Federal -> Mirror -> EVM):**

The Primary Network's three chains share the same validator set and use atomic messaging:

```text
Federal Chain -> EVM Chain:
- Validator set updates (Federal -> EVM for on-chain verification in EVM Chain contracts)
- Governance execution results (Federal -> EVM to trigger contract upgrades)
- Stake/unstake requests (EVM -> Federal when users interact via EVM Chain interface)
- Checkpoint finality confirmations (Federal -> EVM for subnet validation)
- Slashing events (Federal -> EVM to freeze validator-operated contracts)

Mirror Chain -> EVM Chain:
- CRYFT wrapping/unwrapping (Mirror -> EVM for native -> ERC-20 bridge)
- Cross-chain atomic swaps (Mirror -> EVM for asset exchanges)
- Asset issuance events (Mirror -> EVM when native assets need EVM representation)

Federal Chain -> Mirror Chain:
- Validator reward payouts (Federal -> Mirror for native CRYFT distribution)
- Emission schedule updates (Federal -> Mirror for minting authorization)
```

All three chains share the same block production schedule and validators, ensuring atomic cross-chain messaging without external bridges or delays.

**Figure: Primary Network three-chain architecture with subnet hierarchy**

This diagram shows the three-chain Primary Network (Federal, Mirror, EVM) with atomic messaging between them. States (Regions A and B) checkpoint to Federal Chain for settlement. Cities (A1, A2) checkpoint to their parent State, not directly to Main. Registration flows are shown with dotted lines.

```mermaid
flowchart TB
  subgraph Primary["Primary Network"]
    PChain["Federal Chain<br>(Validators, staking, subnets)"]
    XChain["Mirror Chain<br>(Native assets, transfers)"]
    MChain["EVM Chain<br>(EVM contracts, dApps)"]
    PChain <-->|atomic messaging| MChain
    PChain <-->|atomic messaging| XChain
    XChain <-->|atomic messaging| MChain
  end
  RegionA["Region A (State)"]
  RegionB["Region B (State)"]
  CityA1["City A1"]
  CityA2["City A2"]
  RegionA -->|checkpoint| PChain
  RegionB -->|checkpoint| PChain
  CityA1 -->|settle up| RegionA
  CityA2 -->|settle up| RegionA
  RegionA -.->|register via| PChain
  CityA1 -.->|register via| RegionA
```

### 4.2 Validator cross-participation requirements

A key architectural question is whether subnet (State/Region) validators must also validate the Primary Network. CryftNet adopts a **tiered requirement model**:

**Terminology clarification:**
- **Primary Network** = Federal Chain + Mirror Chain + EVM Chain (three chains, shared validator set)
- **Federal Chain** = Settlement/checkpoint/DAO chain specifically  
- **Main EVM Chain** = EVM Chain within Primary Network (hosts CMR, registries)
- Legacy references to "Main" are deprecated; use specific chain names for clarity

**Tier 1: CSS-1 State chains (required Primary Network participation)**

Validators for Cryft Standard Subnet (CSS-1) State chains **must** also be validators on the Primary Network (validating Federal Chain, Mirror Chain, and EVM Chain). This requirement ensures:

- **Security alignment:** State validators have direct stake in the Primary Network's security (via Federal Chain staking), preventing "vampire" attacks where a State chain extracts value without contributing to federation security.
- **Checkpoint integrity:** Validators who sign State checkpoints also validate those checkpoints on Federal Chain, creating accountability.
- **Governance participation:** State validators participate in Primary Network governance (via Federal Chain), ensuring federation decisions reflect the interests of active State operators.
- **Simplified slashing:** Misbehavior on a State chain can be slashed on Federal Chain without complex cross-chain evidence.

**Cryftee requirement for CSS-1 validators:** CSS-1 validators are required to run a full Cryftee instance (with at minimum `bls_tls_signer_v1` and `ipfs_v1` modules) to participate in Primary Network consensus and earn rewards. This ensures all CSS-1 validators have the necessary off-chain utilities for staking operations, checkpoint signing, Code Vault access, and runtime attestation. Non-consensus nodes (RPC, archive) are exempt from this requirement.

**Tier 2: Custom subnets (optional Primary Network participation)**

Custom subnets (non-CSS) may choose whether their validators participate in the Primary Network:

| Participation Level | Requirements | Benefits | Trade-offs |
|:--------------------|:-------------|:---------|:-----------|
| **Full** | Validate Primary Network + subnet | Full federation services, governance rights, priority routing | Higher operational cost |
| **Partial** | Stake on Federal Chain, validate subnet only | Bridge access, registry listing, basic services | No governance votes, standard routing |
| **None** | Subnet-only validation | Maximum independence | No federation services, manual bridging only |

**Minimum stake requirements (canonical):**

```text
Primary Network validator:    1,000 CRYFT minimum stake (see Appendix 16.8)
CSS-1 State validator:         500 CRYFT additional stake (per State)
Custom subnet validator:       Defined by subnet parameters
City validator:                Defined by parent State (typically lower)
```

**Cross-validation benefits:**

- Validators earn rewards from both Main and subnet block production.
- Unified slashing: a single misbehavior affects all validator roles.
- Simplified key management: same validator identity across chains.
- Reputation portability: good behavior on Main improves subnet opportunities.

**Exemptions and transitions:**

- New State chains may request a **bootstrap period** (up to 6 months) where validators are not required to validate Main, allowing the State to establish itself before full integration.
- Validators may **delegate** their Main validation duties to a trusted operator while retaining their subnet role, subject to delegation limits.

### 4.3 Hierarchical chain registration (Cities via States)

CryftNet supports a three-tier hierarchy: Main ->' State (Region) ->' City (Local). A critical design decision is whether City chains must register directly with Main or can register only via their parent State.

**Recommended model: State-mediated City registration**

City chains register **only with their parent State chain**, not directly with Main's EVM Chain. This enables:

1. **Faster experimentation:** Launching a City requires only State DAO approval, not Main governance. This allows rapid iteration for local communities, enterprise enclaves, and specialized use cases.

2. **Reduced Main burden:** Main's EVM Chain does not need to track potentially thousands of City chains. It only tracks the ~10-100 State chains.

3. **State sovereignty:** States can define their own City policies--minimum stake, validator requirements, allowed VMs, and compliance rules--without Main override.

4. **Appropriate trust model:** Users of a City chain trust their State chain; they don't need global Main consensus for local operations.

**State-level City Registry:**

Each CSS-1 State chain maintains a **City Registry** contract/module with:

```text
CityRegistration {
  city_id: uint64,
  city_chain_id: uint256,
  parent_state_id: uint64,
  validator_set_hash: bytes32,
  consensus_type: string,
  vm_type: string,                  // "EVM", "WASM", "Custom"
  cep_compatibility: string,        // "CSS-1", "CSS-lite", "none"
  checkpoint_frequency: uint32,     // blocks between checkpoints to State
  registered_at: uint64,
  status: enum { Active, Suspended, Deregistered },
  metadata_cid: string              // IPFS CID for extended metadata
}
```

**City ->' State settlement:**

**Figure: City checkpoint aggregation flow**

Cities checkpoint to their parent State (not to the Primary Network). The State aggregates City checkpoints and includes a summary (e.g., Merkle root) in its own checkpoint to Federal Chain. The Primary Network does not verify City checkpoints directly.

```mermaid
flowchart LR
  City["City Chain"] -->|checkpoint every N blocks| State["State Chain"]
  State -->|aggregated checkpoint| Main["Main EVM Chain"]
  State -->|includes City summary| Main
```

The State's checkpoint to Federal Chain **may include** an aggregated City summary (Merkle root of City checkpoints), but this is optional. The Primary Network does not verify City checkpoints directly--it trusts the State to manage its Cities.

**City benefits and limitations:**

| Capability | City via State | Direct Main registration |
|:-----------|:---------------|:-------------------------|
| Registration latency | Minutes (State DAO) | Days-weeks (Main governance) |
| Federation Contract Registry | Via State (inherited) | Direct Main access |
| Cross-State bridging | Through State first | Direct (if allowed) |
| Main governance participation | None (vote via State) | Possible |
| Visibility to Main | Aggregated only | Full |
| Slashing authority | State | Main |

**Cross-City transfers (same State):**

Transfers between Cities under the same State settle via the State chain without touching Main:

```text
City A1 ->' City A2 (same State A):
1. City A1 includes transfer in checkpoint to State A
2. State A verifies and includes in State block
3. City A2 claims from State A's confirmed checkpoint
4. No Main involvement required
```

**Cross-City transfers (different States):**

Transfers between Cities under different States route through the Primary Network:

```text
City A1 (State A) ->' City B1 (State B):
1. City A1 checkpoints to State A
2. State A checkpoints to Federal Chain (includes City A1's outbound message)
3. State B receives from Federal Chain
4. City B1 claims from State B
```

**City upgrade path:**

A successful City may choose to "graduate" to State status:

1. City demonstrates sustained activity and validator quality.
2. City applies to Federal Chain governance for State registration.
3. Upon approval, City registers directly with Federal Chain and EVM Chain.
4. City's existing users and contracts migrate or bridge.
5. City can now spawn its own sub-Cities.

### 4.4 City-level account management (State-mediated balances)

Since Cities register only via their parent State (not directly with Main), their account balances are managed **through the State**, not the federal Mirror Chain's Global Balance Ledger. This creates a clean separation:

| Level | Balance Authority | Settlement Target | Account Visibility |
|:------|:------------------|:------------------|:-------------------|
| Main (Mirror Chain) | Mirror Chain GBL (extended UTXO) | Final (self) | Global |
| State | Mirror Chain GBL (via checkpoints) | Main | Global |
| City | State Balance Ledger (SBL) | Parent State | State-local only |

**State Balance Ledger (SBL):**

Each CSS-1 State maintains its own **State Balance Ledger** for its Cities, mirroring Mirror Chain's GBL structure but at the State level:

```text
StateBalanceLedger {
  // Per-asset, per-city, per-account balance
  city_balances: Map<(asset_id, city_id, account) -> uint256>
  
  // State-level aggregate (what Mirror Chain GBL sees for this State)
  state_total: Map<(asset_id, account) -> uint256>
  
  // Invariant: state_total[asset, account] = 
  //   state_direct[asset, account] + sum(city_balances[asset, *, account])
  
  // Pending City->City and City->State transfers
  pending_city_transfers: Map<transfer_id -> PendingCityTransfer>
}
```

**Key architectural principle: Main doesn't see City accounts**

From Main's perspective, a State is a single entity. The Mirror Chain GBL tracks:
- `UTXO(USDC, State_A, Alice, 1000)`

From Main's perspective, a State is a single entity. The GBL tracks:
- `balances[USDC, State_A, Alice] = 1000`

But within State A, Alice's 1000 USDC might be distributed:
- State A direct: 200 USDC
- City A1: 500 USDC
- City A2: 300 USDC

Main doesn't know or care about this internal distribution--it's State A's responsibility to manage.

**City->'City transfers (same State):**

```text
City A1 ->' City A2 transfer (both under State A):

1) User on City A1 calls cityBridge.transferToCity(asset, amount, cityA2, recipient)
2) City A1 debits local balance, emits CityTransferOut
3) City A1 checkpoints to State A
4) State A's SBL updates:
   - city_balances[USDC, A1, Alice] -= 500
   - pending_city_transfers[id] = {Pending, dest=A2, ...}
5) City A2's next checkpoint sync from State includes pending transfer
6) Recipient claims on City A2
7) City A2 checkpoints claim confirmation to State A
8) State A's SBL updates:
   - city_balances[USDC, A2, Bob] += 500
   - pending_city_transfers[id].status = Claimed

Note: Main EVM Chain is NOT involved. State A's total balance is unchanged.
```

**City->'State transfer (escalation):**

```text
City A1 ->' State A direct transfer:

1) User calls cityBridge.escalateToState(asset, amount, recipient)
2) City A1 debits, checkpoints to State A
3) State A's SBL:
   - city_balances[USDC, A1, Alice] -= 500
   - state_direct[USDC, Alice] += 500
4) Alice can now spend directly on State A (faster, more liquidity)

Main still sees: balances[USDC, State_A, Alice] = 1000 (unchanged)
```

**City->Different State transfer (requires Main):**

```text
City A1 (State A) -> State B transfer:

1) City A1: cityBridge.transferToRegion(asset, amount, State_B, recipient)
2) City A1 checkpoints to State A with cross-State intent
3) State A's SBL:
   - city_balances[USDC, A1, Alice] -= 500
   - Cross-State transfer queued for next Main checkpoint
4) State A checkpoints to Main Mirror Chain with:
   - TransferOut(USDC, 500, from=State_A, to=State_B, ...)
5) Mirror Chain GBL:
   - Consume UTXO(USDC, State_A, Alice, old_amount)
   - Create pending_transfer UTXO
6) State B receives, recipient claims
7) Mirror Chain GBL:
   - Consume pending_transfer UTXO
   - Create UTXO(USDC, State_B, Bob, 500)

Note: Main only sees State-level balances. It doesn't know the transfer originated from a City.
```

**City balance visibility:**

| Query | Where to Ask | Response |
|:------|:-------------|:---------|
| "What's my total balance?" | Main Mirror Chain GBL | Sum across all States |
| "What's my State A balance?" | Main Mirror Chain GBL | Single State total |
| "What's my City A1 balance?" | State A SBL | City-specific balance |
| "Where exactly are my assets?" | State A SBL + each City | Full breakdown |

**Wallets and City balances:**

Wallets display City-level balances by:
1. Querying Mirror Chain GBL for State-level totals
2. For each State with balance > 0, querying the State's SBL for City breakdown
3. Displaying hierarchical view:

```text
Alice's USDC:
|-- Primary Network:  500 USDC
|-- State A:      1,000 USDC
|   |-- Direct:     200 USDC
|   |-- City A1:    500 USDC
|   `-- City A2:    300 USDC
`-- State B:        250 USDC
    `-- Direct:     250 USDC
-----------------------------
Total:            1,750 USDC
```

**Why Cities don't register with the Primary Network:**

This hierarchical model provides:

1. **Scalability:** Mirror Chain GBL tracks ~100 States, not ~10,000 Cities.
2. **State sovereignty:** States control their City ecosystem without Primary Network approval.
3. **Latency:** City->City transfers within a State are fast (no Federal Chain checkpoint wait).
4. **Appropriate trust:** City users trust their State; they don't need global Primary Network consensus.
5. **Simpler governance:** Federal Chain governs States; States govern Cities.

**City emergency exit:**

If a City chain fails or its State censors it, users can still recover:

1. Prove City balance via State's last confirmed checkpoint
2. Submit proof to State requesting balance escalation to State-direct
3. If State refuses, appeal to Federal Chain governance with evidence
4. Federal Chain can force-escalate City balances to State level (emergency measure)
5. User then exits State->Primary Network via normal cross-region transfer

This ensures users are never permanently trapped in a City.

This hierarchical model balances federation coherence with local autonomy, enabling CryftNet to scale to thousands of chains without overwhelming Main governance.

#### 4.4.1 City emergency exit and fraud proofs (v1 normative)

**Problem:** If a City chain fails, censors users, or its parent State refuses to process City checkpoints, users must be able to recover their balances without relying on the misbehaving party.

**Solution: Merkle proof-based emergency exit with Federal Chain adjudication.**

**Step 1: City balance commitment (every checkpoint)**

Each City checkpoint includes a **balance Merkle root**:

```text
CityCheckpoint = {
  city_id: 1001005,  // Region 1, City 5
  height: 5_123_456,
  block_hash: 0x...,
  state_root: 0x...,
  balance_merkle_root: 0x...,  // Root of all account balances
  message_root: 0x...,
  validator_quorum: { ... },
  epoch: 1234
}

Balance Merkle tree construction:
  - Leaf: keccak256(account || asset_id || balance)
  - Sorted by account address (ascending)
  - Standard binary Merkle tree (keccak256 hashing)
  - balance_merkle_root = root of tree

Example:
  Leaf_1 = keccak256(0xAlice || USDC || 5000)
  Leaf_2 = keccak256(0xBob || USDC || 2000)
  Leaf_3 = keccak256(0xAlice || CRYFT || 1200)
  ...
  balance_merkle_root = merkleRoot([Leaf_1, Leaf_2, Leaf_3, ...])
```

State chain stores: `city_balance_roots[city_id][height] = balance_merkle_root`

**Step 2: User initiates emergency exit**

**Trigger conditions:**
- City chain offline for > 24 hours
- City checkpoint not processed by State for > 3 epochs
- User suspects censorship or balance manipulation

**Exit request to State:**

```solidity
// State Balance Ledger emergency exit function
function emergencyExitFromCity(
    uint64 city_id,
    uint64 checkpoint_height,
    address account,
    bytes32 asset_id,
    uint256 balance,
    bytes32[] calldata merkle_proof
) external {
    // 1. Verify checkpoint exists and is finalized on State
    bytes32 balance_root = city_balance_roots[city_id][checkpoint_height];
    require(balance_root != 0, "Checkpoint not finalized");
    require(checkpoint_height < block.number - FINALITY_DELAY, "Not finalized yet");
    
    // 2. Verify Merkle proof
    bytes32 leaf = keccak256(abi.encodePacked(account, asset_id, balance));
    bool valid = MerkleProof.verify(merkle_proof, balance_root, leaf);
    require(valid, "Invalid Merkle proof");
    
    // 3. Verify account matches msg.sender (or authorized delegate)
    require(account == msg.sender || isAuthorized[account][msg.sender], "Not authorized");
    
    // 4. Mark balance as exited (prevent double-claim)
    bytes32 exit_key = keccak256(abi.encodePacked(city_id, checkpoint_height, account, asset_id));
    require(!exits[exit_key], "Already exited");
    exits[exit_key] = true;
    
    // 5. Credit balance to State-direct (escalate from City to State)
    state_balances[asset_id][account] += balance;
    
    emit EmergencyExitFromCity(city_id, checkpoint_height, account, asset_id, balance);
}
```

**Merkle proof construction (off-chain, performed by user/wallet):**

```javascript
// User queries City RPC (or State archive if City offline)
const cityState = await cityRPC.getStateAtHeight(checkpoint_height);
const allBalances = cityState.getAllAccountBalances();  // List of (account, asset, balance)

// Sort and construct Merkle tree
const leaves = allBalances
  .sort((a, b) => a.account.localeCompare(b.account))
  .map(b => keccak256(encodePacked(b.account, b.asset_id, b.balance)));
const tree = new MerkleTree(leaves, keccak256);

// Get proof for Alice's USDC balance
const aliceLeaf = keccak256(encodePacked(alice, USDC, 5000));
const proof = tree.getProof(aliceLeaf);  // Array of sibling hashes

// Submit to State
await stateSBL.emergencyExitFromCity(
  city_id,
  checkpoint_height,
  alice,
  USDC,
  5000,
  proof
);
```

**Step 3: Appeal to Federal Chain (if State refuses)**

If State chain censors emergency exit or is offline:

```solidity
// Federal Chain emergency exit (last resort)
function emergencyExitFromCityToFederal(
    uint64 city_id,
    uint64 state_id,
    uint64 city_checkpoint_height,
    uint64 state_checkpoint_height,  // State's checkpoint that includes City's balance root
    address account,
    bytes32 asset_id,
    uint256 balance,
    bytes32[] calldata city_merkle_proof,
    bytes32[] calldata state_merkle_proof  // Proof that balance_root is in State checkpoint
) external {
    // 1. Verify State checkpoint exists on Federal Chain
    Checkpoint memory stateCP = checkpoints[state_id][state_checkpoint_height];
    require(stateCP.height > 0, "State checkpoint not found");
    
    // 2. Verify State checkpoint includes City's balance root
    bytes32 city_balance_root = ...; // Extract from state_merkle_proof
    // (State checkpoint must include City summary; verify via Merkle proof against state_root)
    
    // 3. Verify City balance Merkle proof (same as Step 2)
    bytes32 leaf = keccak256(abi.encodePacked(account, asset_id, balance));
    bool valid = MerkleProof.verify(city_merkle_proof, city_balance_root, leaf);
    require(valid, "Invalid City Merkle proof");
    
    // 4. Verify 72-hour waiting period (prevents impatient appeals)
    require(block.timestamp > stateCP.timestamp + 72 hours, "Must wait 72h for State response");
    
    // 5. Credit balance to Federal-direct (escalate to Primary Network)
    federal_balances[asset_id][account] += balance;
    
    // 6. Slash State validators (2% stake penalty for censorship)
    slashStateValidators(state_id, CENSORSHIP_PENALTY);
    
    emit EmergencyExitToFederal(city_id, state_id, account, asset_id, balance);
}
```

**Step 4: Griefing prevention**

**Attack: User submits fake balance claim with fabricated Merkle proof**

Prevention:
- Merkle proof verification is cryptographically secure (cannot fake valid proof)
- balance_merkle_root is committed in finalized City checkpoint (cannot be altered)
- If City checkpoint is fraudulent (malicious City validators), State detects via fraud proof (separate mechanism)

**Attack: User double-claims (exits same balance twice)**

Prevention:
- `exits[exit_key]` mapping tracks claimed balances per checkpoint
- Second claim with same (city_id, checkpoint_height, account, asset_id) reverts
- User can exit from DIFFERENT checkpoints (e.g., height 100 and height 200) if balance increased

**Attack: Spam emergency exits to DOS State/Federal Chain**

Prevention:
- Emergency exit requires gas fee (economic cost)
- Rate limiting: Max 10 exits per block per account
- Governance can pause emergency exits if abuse detected (requires 67% vote)

**Attack: City validators collude to create fake checkpoint with inflated balances**

Prevention (fraud proof mechanism):

```text
Fraud proof submission (by honest observer):

1. Observer detects invalid City checkpoint (e.g., total balances exceed deposits)
2. Observer submits fraud proof to State:
   - City checkpoint header (balance_merkle_root, quorum, epoch)
   - Proof of invalid transition (e.g., Alice balance increased without deposit tx)
   - Merkle proofs for before/after state
3. State verifies fraud proof:
   - Re-executes disputed transactions
   - Compares computed state_root vs. claimed state_root
   - If mismatch: fraud proven
4. State rejects City checkpoint, slashes City validators (10% stake)
5. State initiates emergency City shutdown (all users must exit via last valid checkpoint)
```

**Fraud proof data structure:**

```solidity
struct CityFraudProof {
    uint64 city_id;
    uint64 disputed_checkpoint_height;
    bytes32 claimed_balance_root;
    bytes32 computed_balance_root;  // Re-computed by fraud prover
    Transaction[] disputed_txs;  // Transactions leading to invalid state
    bytes32[] state_merkle_proofs;  // Proofs for before/after account states
    bytes fraud_evidence;  // Additional evidence (e.g., invalid signature, arithmetic overflow)
}

function submitCityFraudProof(CityFraudProof calldata proof) external {
    // 1. Verify fraud proof validity
    bool isValid = verifyCityFraudProof(proof);
    require(isValid, "Invalid fraud proof");
    
    // 2. Slash City validators
    slashCityValidators(proof.city_id, FRAUD_PENALTY);
    
    // 3. Mark checkpoint as fraudulent
    fraudulent_checkpoints[proof.city_id][proof.disputed_checkpoint_height] = true;
    
    // 4. Reward fraud prover (10% of slashed stake)
    rewardFraudProver(msg.sender, FRAUD_PENALTY * 10 / 100);
    
    emit CityFraudProven(proof.city_id, proof.disputed_checkpoint_height);
}
```

**Adjudication path summary:**

```text
Normal operation:
  City -> State (via checkpoint) -> Federal Chain (summary only)

Emergency exit:
  Step 1: User -> State (emergencyExitFromCity with Merkle proof)
  Step 2 (if State offline/censoring): User -> Federal Chain (emergencyExitFromCityToFederal)
  Step 3 (if City fraudulent): Observer -> State (submitCityFraudProof) -> Federal Chain (slash report)

Timelines:
  - Normal checkpoint: ~10 minutes (City -> State)
  - Emergency exit to State: Immediate (if checkpoint exists)
  - Appeal to Federal: 72-hour waiting period
  - Fraud proof: Immediate (if evidence valid)
```

**Economic incentives:**

| Role | Action | Incentive | Penalty |
|:-----|:-------|:----------|:--------|
| City validators | Submit honest checkpoints | Block rewards + fees | 10% slash for fraud |
| State validators | Process City checkpoints | Checkpoint fees | 2% slash for censorship |
| Users | Emergency exit only when needed | Recover funds | Gas costs (prevents spam) |
| Fraud provers | Submit valid fraud proofs | 10% of slashed stake | None (invalid proofs rejected) |
| Federal Chain | Adjudicate appeals | Governance fees | N/A |

**Version marker: (v1) City emergency exit and fraud proof mechanisms are mainnet-required for hierarchical City deployment.**

### 4.5 Code Vault Storage Modes: On-Chain vs. IPFS-Referenced

The Code Vault on Mirror Chain supports two storage modes for smart contract bytecode: **on-chain storage** (direct inclusion in the UTXO) and **IPFS-referenced storage** (storing a CID that points to pinned content on IPFS). This dual-model approach allows deployers to choose between maximum permanence (on-chain, at higher cost) and cost-efficiency (IPFS, with pinning incentives ensuring availability). Both modes maintain the same security guarantees for code integrity and deterministic deployment, as regions verify against committed hashes regardless of storage location.

#### 4.5.1 Design Rationale
- **On-Chain Storage**: Bytecode is stored directly in the Mirror Chain UTXO, ensuring it is replicated across all validators and immune to pinning failures or IPFS network issues. This mode is ideal for high-value, canonical contracts (e.g., federation governance or stablecoins) where data loss is unacceptable. Trade-off: Higher transaction fees due to data size.
- **IPFS-Referenced Storage**: Bytecode is uploaded to IPFS and referenced via a CID in the UTXO. Availability is ensured through the network's pinning rewards (Section 11.4), with auditors and challenges verifying persistence. This mode is cheaper and scalable for larger contracts but relies on economic incentives. Trade-off: Theoretical risk of pinning errors, mitigated by protocol-level rewards and slashing.

Deployers specify the mode during Code Vault deposit. Regions fetching for lazy mirroring (via `ensureDeployedAndCall()`) only need the hashes for verification--full bytecode retrieval (if needed) is off-chain and optional.

#### 4.5.2 Storage Mode Invariants
- **Integrity**: Both modes commit `init_code_hash` and `runtime_code_hash` in the UTXO. Regions reject deployments if the deployed bytecode does not match `runtime_code_hash`.
- **Availability**: On-chain is guaranteed by chain replication; IPFS uses pinning jobs with budgets and SLAs (e.g., 98% uptime).
- **Immutability**: Once committed, the `code_id` (derived from UTXO ID) cannot be altered. Spending the UTXO is forbidden via a "burn" lock script.
- **Fallback**: If IPFS fetch fails during deployment, regions can query Mirror Chain for a full blob fallback (if stored on-chain) or retry pinning providers.

#### 4.5.3 Extended UTXO Structure for Code Vault Deposits
Code Vault entries use a specialized UTXO with the following structure (binary-encoded in transactions):

| Field                  | Type          | Description                                                                 |
|------------------------|---------------|-----------------------------------------------------------------------------|
| `utxo_id`             | bytes32      | Unique UTXO identifier (hash-based).                                        |
| `asset_id`            | bytes32      | Reserved for Code Vault (e.g., `0xCODE_VAULT`).                             |
| `region_id`           | uint64       | 0 for federation-wide; optional region-specific.                            |
| `account`             | address      | Deployer's address (for authorization and ownership).                       |
| `amount`              | uint256      | 0 (no monetary value; data storage only).                                   |
| `lock_script`         | bytes        | Contains mode, hashes, and data/CID; signed by deployer.                    |

The `lock_script` uses **canonical TLV (Type-Length-Value) encoding** for consensus-critical parsing:

**TLV structure (v1 normative):**

```text
lock_script = TLV_SEQUENCE[
  TLV(type=0x01, length=1, value=storage_mode),      // 0x00=ON_CHAIN, 0x01=IPFS
  TLV(type=0x02, length=32, value=init_code_hash),   // keccak256(init_code)
  TLV(type=0x03, length=32, value=runtime_code_hash), // keccak256(runtime_bytecode)
  
  // Conditional fields based on storage_mode:
  IF storage_mode == ON_CHAIN:
    TLV(type=0x10, length=N, value=init_code_blob),       // Full init bytecode
    TLV(type=0x11, length=M, value=runtime_bytecode),     // Full runtime bytecode
  ELSE IF storage_mode == IPFS:
    TLV(type=0x20, length=L, value=init_code_cid),        // IPFS CID (UTF-8)
    TLV(type=0x21, length=K, value=runtime_bytecode_cid), // IPFS CID (UTF-8)
    TLV(type=0x22, length=8, value=pin_duration_epochs),  // Optional uint64
    TLV(type=0x23, length=32, value=pin_budget),          // Optional uint256
  
  TLV(type=0xFE, length=8, value=nonce),            // uint64 replay protection
  TLV(type=0xFF, length=65, value=signature)        // ECDSA sig over TLV hash
]

TLV encoding rules:
- Each entry: [1 byte type] [4 bytes length (big-endian)] [N bytes value]
- Total lock_script hash = keccak256(all TLV entries before signature)
- Signature field (type=0xFF) covers hash of all preceding TLV entries
- Unknown type codes with high bit set (0x80-0xFD) are skipped (forward compatibility)
- Unknown type codes with high bit clear (0x00-0x7F) cause validation failure
```

**Example: ON_CHAIN mode TLV encoding (pseudocode)**

```python
lock_script_tlv = b''

# TLV(0x01, 1, 0x00)  # storage_mode = ON_CHAIN
lock_script_tlv += bytes([0x01]) + (1).to_bytes(4, 'big') + bytes([0x00])

# TLV(0x02, 32, init_code_hash)
lock_script_tlv += bytes([0x02]) + (32).to_bytes(4, 'big') + init_code_hash

# TLV(0x03, 32, runtime_code_hash)
lock_script_tlv += bytes([0x03]) + (32).to_bytes(4, 'big') + runtime_code_hash

# TLV(0x10, len(init_code), init_code_blob)
lock_script_tlv += bytes([0x10]) + len(init_code).to_bytes(4, 'big') + init_code

# TLV(0x11, len(runtime_bytecode), runtime_bytecode)
lock_script_tlv += bytes([0x11]) + len(runtime_bytecode).to_bytes(4, 'big') + runtime_bytecode

# TLV(0xFE, 8, nonce)
lock_script_tlv += bytes([0xFE]) + (8).to_bytes(4, 'big') + nonce.to_bytes(8, 'big')

# Hash all TLV entries before signature
script_commitment = keccak256(lock_script_tlv)
signature = sign(script_commitment, deployer_private_key)

# TLV(0xFF, 65, signature)
lock_script_tlv += bytes([0xFF]) + (65).to_bytes(4, 'big') + signature
```

**Why TLV over JSON:**

1. **Deterministic serialization:** TLV has canonical byte ordering; JSON has ambiguous whitespace, key ordering, and number encoding. Consensus-critical structures must hash identically across all implementations.
2. **No parser ambiguity:** JSON parsers differ on edge cases (Unicode normalization, number precision, escape sequences). TLV is byte-exact.
3. **Compact:** TLV saves ~30% space vs. JSON for binary data (no base64 encoding overhead).
4. **Forward compatibility:** Unknown TLV types with high bit set can be safely skipped, allowing protocol upgrades without hard forks.
5. **Auditable:** TLV structure is verifiable with simple byte inspection; JSON requires full parser implementation.

**Validation algorithm:**

```python
def validate_code_vault_lock_script(lock_script_bytes):
    tlv_entries = parse_tlv_sequence(lock_script_bytes)
    
    # 1. Extract required fields
    storage_mode = tlv_entries.get(0x01)
    init_hash = tlv_entries.get(0x02)
    runtime_hash = tlv_entries.get(0x03)
    nonce = tlv_entries.get(0xFE)
    signature = tlv_entries.get(0xFF)
    
    assert storage_mode in [0x00, 0x01], "Invalid storage mode"
    assert len(init_hash) == 32, "Invalid init_code_hash length"
    assert len(runtime_hash) == 32, "Invalid runtime_code_hash length"
    
    # 2. Verify mode-specific fields
    if storage_mode == 0x00:  # ON_CHAIN
        init_blob = tlv_entries.get(0x10)
        runtime_blob = tlv_entries.get(0x11)
        assert keccak256(init_blob) == init_hash, "init_code hash mismatch"
        assert keccak256(runtime_blob) == runtime_hash, "runtime_code hash mismatch"
    else:  # IPFS
        init_cid = tlv_entries.get(0x20).decode('utf-8')
        runtime_cid = tlv_entries.get(0x21).decode('utf-8')
        assert is_valid_cid(init_cid), "Invalid init_code CID"
        assert is_valid_cid(runtime_cid), "Invalid runtime_code CID"
    
    # 3. Verify signature over commitment (all TLV entries except 0xFF)
    commitment = keccak256(lock_script_bytes_without_signature_tlv)
    deployer_address = ecrecover(commitment, signature)
    assert deployer_address == utxo.account, "Signature mismatch"
    
    # 4. Verify nonce (replay protection)
    assert nonce == get_account_nonce(deployer_address), "Invalid nonce"
    
    return True
```

**(v1)** TLV encoding is the normative format for all Code Vault lock scripts on mainnet. JSON examples in this document are provided for human readability only; implementations MUST use TLV
```

- **Size Limits**: On-chain blobs have governance-configurable size limits per UTXO to prevent chain bloat; oversized deposits revert. IPFS has no inherent limit (scalable). **EVM Compatibility Constraint**: Regardless of storage mode, the runtime bytecode MUST NOT exceed the maximum contract bytecode size enforced by the target regional or Federal EVM chains (typically 24KB per EIP-170, though regions may configure different limits). Code Vault deposits with runtime_bytecode exceeding the destination chain's limit will be rejected during deployment, even if the Code Vault UTXO was successfully created. Deployers should verify target chain limits before depositing.
- **Fees**: Base fee + `data_size * GAS_PER_BYTE` (e.g., 16 gas/byte for on-chain). IPFS mode adds optional `pin_budget` (escrowed for rewards).

#### 4.5.4 Transaction Flow for Code Vault Deposit
Deployers submit a Mirror Chain transaction to create a Code Vault UTXO. Below is a conceptual flow with examples.

##### Example 1: On-Chain Storage (Direct Bytecode Inclusion)
Assume a small contract (e.g., simple ERC-20) with runtime bytecode ~10KB.

```python
# Pseudocode: Mirror Chain SDK transaction builder
deployer = "0xDeployer"
private_key = "0xPrivateKey"

# Bytecode (truncated example)
init_code = "0x6080604052..."  # Full init code
runtime_bytecode = "0x6060604052..."  # Runtime portion

# Hashes
init_hash = keccak256(init_code)
runtime_hash = keccak256(runtime_bytecode)

# Lock script
lock_script = {
    "type": "CODE_COMMIT",
    "storage_mode": "ON_CHAIN",
    "init_code_hash": init_hash,
    "runtime_code_hash": runtime_hash,
    "init_code_blob": init_code,
    "runtime_bytecode": runtime_bytecode,
    "nonce": get_nonce(deployer),
}
script_hash = keccak256(lock_script)
signature = sign(script_hash, private_key)
lock_script["sig"] = signature

# Input UTXO (for fees)
input = {"utxo_id": "0xInputUTXO", "amount": 1000}  # Enough for fees

# Output UTXO (Code Vault entry)
output = {
    "asset_id": "0xCODE_VAULT",
    "region_id": 0,
    "account": deployer,
    "amount": 0,
    "lock_script": lock_script
}

# Build, sign, submit
tx = build_tx(inputs=[input], outputs=[output])
signed_tx = sign_tx(tx, private_key)
submit_tx(signed_tx)  # Returns tx_id; code_id = keccak256(tx_id)
```

- **Estimated Cost**: Base fee (~0.01 CRYFT) + data fee (10KB * gas/byte -> ~0.05 CRYFT extra).
- **Result**: Bytecode is now on-chain; no pinning needed.

##### Example 2: IPFS-Referenced Storage (CID with Pinning)
For larger bytecode (>24KB), upload to IPFS first.

```python
# Pseudocode
# Step 1: Upload to IPFS (via Cryftee ipfs_v1 module)
init_cid = ipfs_upload(init_code)  # "QmInitCID"
runtime_cid = ipfs_upload(runtime_bytecode)  # "QmRuntimeCID"

# Lock script
lock_script = {
    "type": "CODE_COMMIT",
    "storage_mode": "IPFS",
    "init_code_hash": keccak256(init_code),
    "runtime_code_hash": keccak256(runtime_bytecode),
    "init_code_cid": init_cid,
    "runtime_bytecode_cid": runtime_cid,
    "pin_duration_epochs": 4320,  # ~30 days
    "pin_budget": 2500,           # CRYFT escrowed for pinning rewards
    "nonce": get_nonce(deployer),
}
script_hash = keccak256(lock_script)
signature = sign(script_hash, private_key)
lock_script["sig"] = signature

# Input/Output same as above, but input amount includes pin_budget
input["amount"] = 1000 + 2500  # Fees + budget

# Build, sign, submit
tx = build_tx(inputs=[input], outputs=[output])
signed_tx = sign_tx(tx, private_key)
submit_tx(signed_tx)
```

- **Estimated Cost**: Base tx (~0.01 CRYFT) + pin_budget (escrowed, released over epochs to providers).
- **Pinning Integration**: Transaction auto-creates a Pin Job (Section 11.4) with the provided budget/SLA.
- **Result**: Bytecode on IPFS; Code Vault UTXO holds CIDs + hashes. Pinning ensures availability.

#### 4.5.5 Integration with CMR and Deployment
- **CMR Reference**: CMR entries include `code_id` from the UTXO. Storage mode is queryable via Mirror Chain precompiles.
- **Lazy Mirroring**: During `ensureDeployedAndCall()`, regions fetch bytecode based on mode:
  - ON_CHAIN: Direct from Mirror Chain UTXO (atomic query).
  - IPFS: From pinned providers; fallback to Mirror if unavailable.
- **Failure Handling**: If IPFS fetch fails (despite pinning), deployment reverts; user can retry or appeal via governance (slashing pin providers if fault proven).

This model empowers deployers with choice while leveraging CryftNet's incentives for robust availability. For critical contracts, on-chain mode eliminates external dependencies; for others, IPFS reduces costs without compromising integrity.

## 5. Network model and latency strategy

### 5.1 Regions as latency domains

A region is defined as a set of validators and routing policies optimized for a latency domain. The
domain can be geographic (e.g., Midwest US) or network-derived (e.g., a set of AS paths). The key
requirement is that a significant portion of users experience low RTT (round-trip time) to a sufficient
number of regional validators.

### 5.2 Validator eligibility via ping measurements

To prevent a "region" from being nominal only, CryftNet uses ping-based eligibility. A validator is
eligible for Region R only if it can demonstrate sustained low-latency connectivity to a quorum of
Region R measurement beacons.
Mechanism (proposal): 1) Region R maintains a Beacon Set: B = {b1..bm}. Beacons are run by
independent operators approved by the region DAO and optionally co-hosted by regional validators.
2) During each epoch, validators perform signed ping sessions to beacons using a fixed protocol
(e.g., QUIC PING or UDP echo with replay protection). Beacons also ping validators. 3) Beacons emit
signed measurement reports containing distribution summaries (p50, p95, loss rate, jitter) and
timestamps. 4) Validators submit an aggregated proof to the region chain. The chain computes an
Eligibility Score.
```text
EligibilityScore(v, R) =

  w1 * clamp(1 - p95_rtt(v,R)/RTT_MAX, 0, 1)
+ w2 * clamp(1 - loss(v,R)/LOSS_MAX, 0, 1)
+ w3 * clamp(1 - jitter(v,R)/JITTER_MAX, 0, 1)
+ w4 * beacon_quorum_ok(v,R)
Constraints:
- beacon_quorum_ok requires at least q of m beacons reporting in-window measurements.
- reports are signed by beacons and include nonces to prevent replay.
- Validator eligibility also requires a valid Cryftee attestation (`/v1/runtime/attestation` signed proof of module set) for consensus participants.
