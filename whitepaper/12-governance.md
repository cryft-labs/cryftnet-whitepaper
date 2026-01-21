contracts describing what to pin, how long, replication targets, and budgets. 3) Proof of Availability:
periodic challenges and attestations to verify that providers can actually serve the pinned content. 4)
Reward distribution and slashing: providers earn per-epoch rewards based on verified availability;
repeated failure or fraud is penalized.
#### 11.4.1 Pin Provider Registry

Providers register on Main or on a CSS region chain (or both). Registration includes: - provider_id
(pubkey or address) - service endpoint metadata (optional; can be hidden for private providers) -
supported regions / latency hints - bonded stake and slashing terms - supported proof method
(challenge-response, auditor, or hybrid)
PinProvider {
  provider_id: 0xPubKey,
  stake_bond: 10000 CRYFT,
  endpoints: ["https://pin.midwest.example", "ipfs-peer:12D3KooW..."],
  regions: [42],                   // optional
  proof_method: "HYBRID",
  max_jobs: 1000,
  terms: { slash_missed: 0.1%, slash_fraud: 5%, grace: 2 epochs }
}
#### 11.4.2 Pin Jobs and markets

A pin job is a contract created by a user/app/treasury. Jobs can be public or private. Public job: CID is
visible on-chain. Private job: chain stores only a commitment; CID is disclosed to selected providers
via CGS envelopes.
PinJob {
  job_id: 771_000_0042,
  cid_or_commitment: "cid:Qm..." | "commitment:0x...",
  replication_target: 7,
  duration_epochs: 4320,            // e.g., 30 days if epoch=10min
  budget: 2500 CRYFT,
  region_hint: 42,
  privacy: { mode: "public" | "private", auditors: [a1,a2,a3] },
  sla: { max_p95_retrieval_ms: 400, min_availability: 0.98 }
}
#### 11.4.3 Proof of Availability (hybrid scheme)

Primary proposal: Hybrid challenge-response plus auditor sampling. - The chain (or a region
committee) issues challenges derived from a randomness beacon. - Each challenge references the
CID and a random block index. Providers must return a proof within a time window. - Auditors
randomly verify a subset by fetching content from the provider and comparing hashes. Auditors then
sign attestations. This avoids trusting providers alone while limiting on-chain bandwidth.
Challenge(epoch, job_id, provider_id):
  idx = H(rand || provider_id) mod N_blocks
  nonce = H(rand || "nonce" || provider_id)
ProviderResponse:

```jsonc
{
  job_id: ...,
  provider_id: ...,
  epoch: ...,
  idx: ...,
  nonce: ...,
  // proof depends on chunking scheme:
  // - block_hash + raw block bytes OR
  // - merkle proof if CID references a merklized DAG
  block_hash: 0x...,
  block_bytes_b64: "...",
  sig: Sign(provider_sk, H(job_id||epoch||idx||nonce||block_hash))
}
AuditorAttestation:
{
  job_id: ...,
  provider_id: ...,
  epoch: ...,
  checked: true,
  retrieval_ms_p95: 312,
  ok: true,
  auditor_sig: Sign(auditor_sk, H(...))
}
```

#### 11.4.4 Availability scoring and rewards

Providers earn rewards based on an Availability Score computed per job per epoch. Score =
0.5*success_rate + 0.3*audit_ok + 0.2*latency_score + diversity_bonus Reward(job, provider, epoch)
= (job_budget_per_epoch) * Score / sum_provider_scores
job_budget_per_epoch = job.budget / job.duration_epochs
If provider misses challenges:
- apply slash_missed per epoch beyond grace
If fraud proven (forged response or impossible content):
- slash_fraud and ban provider for ban_epochs
#### 11.4.5 Pinning and portals/IPNS

Critical CryftNet web portals and module artifacts are content-addressed and often referenced via
IPNS keys. To keep "latest portal" reliable, the network can: - pin the portal index CID set referenced
by the current IPNS record, - additionally pin the last N historical portal versions for rollback
resilience, - run private pin jobs for sensitive modules or private portals, using CGS to reveal CIDs
only to authorized providers. Pinning rewards thus become part of the chain's operational backbone.

---

## 12. Governance: federated DAO and cross-network democracy

CryftNet governance is federated. The Main chain hosts the primary DAO that defines
federation-wide rules, registries, and security parameters. Each subnet/region can host its own DAO
for local parameters. The key design tension is: - local autonomy for regions and custom subnets, -
global coordination for shared UX, security, and registries. The governance system therefore
distinguishes: Federation Proposals vs Local Proposals.

### 12.1 Federation Proposals (Main chain)

Federation Proposals affect the shared layer:

- protocol upgrades for Main (CRVS params, scheduler rules, checkpoint format)
- registry changes (region list, subnet listings, certification programs)
- global economic parameters (emission schedule, base fee policy, treasury policy)
- Cryftee trust roots: publisher allowlists, GitHub verification policy
- global CGS standards (message formats, key rotation cadence)
- disputes and slashing appeals that affect cross-chain trust
### 12.2 Local Proposals (Regions and subnets)

Local Proposals affect a single subnet or region:

- committee membership policies and staking minimums
- ping beacon set membership and RTT thresholds
- local fee policies and subsidy allocation
- local pinning reward programs and auditor committees
- optional features (e.g., enabling CGS pools, enabling parallel tx envelope by default)
### 12.3 The Federated DAO: broader votes across all networks

Federation governance is strengthened by including votes from across the federation, not only Main validators. Proposal: a two-chamber model with cross-network aggregation.

**Chamber A: Validator Council (Main)**
- stake-weighted vote of Main validators
- optimized for rapid security decisions and technical upgrades

**Chamber B: Federation Assembly (All networks)**
- voting power aggregated from regions and certified subnets
- allows broader representation of users and local validator sets
- each network may choose its own internal voting method, then export a signed aggregate to Main
#### 12.3.1 Cross-network vote export (Governance Adapters)

A subnet that wants to participate in federation governance registers a Governance Adapter on Main:

### 12.4 Bootstrapping and decentralization trajectory (v1 transition plan)

**Critical for investor/auditor confidence:** "Cryft Labs maintains first-class implementations" requires explicit guardrails and a sunset plan for special powers.

#### 12.4.1 Initial control assumptions (mainnet launch)

At mainnet launch (v1), Cryft Labs holds **temporary centralized controls** for operational safety:

**1. Primary Network deployment keys:**
- **Federal Chain governance multisig** (3-of-5): Initially controlled by Cryft Labs founding team
- **Mirror Chain system parameter updates**: Emergency upgrades via Cryft Labs-controlled proxy
- **EVM Chain CMR admin**: Contract registry admin key for adding/removing authorized deployers

**2. Cryftee module signing authority:**
- **Root publisher allowlist**: Only Cryft Labs GitHub org authorized to publish signed modules
- **Module attestation keys**: Cryft Labs controls TEE signing keys for initial module set (bls_tls_signer_v1, ipfs_v1, cgs_v1)
- **Module upgrade coordination**: Cryft Labs schedules mandatory upgrades for security patches

**3. Treasury and genesis distribution:**
- **Treasury multisig** (5-of-9): Initially Cryft Labs (5), Strategic Partners (2), Community Representatives (2)
- **Emergency circuit breakers**: Cryft Labs retains 72h pause authority for critical exploits (expires after 180 days post-mainnet)
- **Genesis validator set**: Cryft Labs operates 40% of genesis validators (decreases to <10% by Month 6)

**4. Code repository and release authority:**
- **CryftGo (AvalancheGo fork)**: Cryft Labs GitHub org maintains canonical repository
- **Release signing keys**: All binary releases signed by Cryft Labs GPG key (additional community signing keys added by Month 3)
- **Protocol upgrade proposals**: Cryft Labs has expedited proposal path for first 90 days (then requires standard governance)

#### 12.4.2 Decentralization phases (enforced timeline)

**Phase 0: Controlled Launch (Days 0-30)**
- **Goal:** Operational stability, security hardening, incident response
- **Cryft Labs powers:** Full control over all keys/multisigs, expedited upgrades, validator majority (40%)
- **Governance:** Read-only DAO (community can view proposals but not execute)
- **Exit criteria:** Zero critical exploits, >95% validator uptime, successful atomic bundle stress test

**Phase 1: Governance Bootstrap (Days 31-90)**
- **Goal:** Transfer governance execution authority to community DAO
- **Changes:**
  - Federal Chain governance multisig  5-of-9 (Cryft Labs 3, Community 4, Strategic 2)
  - Treasury multisig  4-of-9 (Cryft Labs 2, Community 4, Strategic 3)
  - Emergency pause authority  Requires 2-of-3 security council (Cryft Labs 1 seat)
  - DAO proposals become executable by tokenholders (>67% supermajority required)
- **Cryft Labs retains:** Module signing authority, release coordination, expedited proposal path (expires Day 90)
- **Exit criteria:** 3 successful community governance proposals executed, >50 active governance participants

**Phase 2: Module Publisher Decentralization (Days 91-180)**
- **Goal:** Multi-organization module signing authority
- **Changes:**
  - Cryftee root publisher allowlist expanded to 5 organizations (Cryft Labs + 4 approved publishers)
  - Module attestation requires 3-of-5 publisher signatures (Cryft Labs + 2 others minimum)
  - Community Module Review Committee (7 members, DAO-elected) can veto malicious modules
  - Open-source module development grants (treasury-funded) for alternative implementations
- **Cryft Labs retains:** 1-of-5 publisher seat (cannot unilaterally publish modules)
- **Exit criteria:** 2 non-Cryft Labs modules published and adopted by >20% of validators

**Phase 3: Operational Decentralization (Days 181-365)**
- **Goal:** Remove all Cryft Labs special powers
- **Changes:**
  - Emergency pause authority removed entirely (replaced by standard DAO fast-track for emergencies)
  - Cryft Labs validator stake reduced to <10% of network (public commitment to sell excess)
  - Federal Chain governance multisig  DAO-controlled (7-of-11 elected community members)
  - Treasury multisig  DAO-controlled (5-of-7 elected community members)
  - Protocol upgrades require standard DAO approval (no expedited path)
- **Cryft Labs becomes:** One participant among many (no special keys or authorities)
- **Enforcement:** Smart contract time-locks prevent Cryft Labs from extending Phase 3 beyond Day 365

#### 12.4.3 Enforcement mechanisms (preventing "perpetual bootstrap")

**Problem:** Many projects claim decentralization but never execute. How is CryftNet's transition enforceable?

**Solution: On-chain time-locked enforcement contracts**

`solidity
contract DecentralizationEnforcement {
    uint256 public constant MAINNET_LAUNCH = ...; // genesis timestamp
    
    // Phase deadlines (immutable)
    uint256 public constant PHASE_1_DEADLINE = MAINNET_LAUNCH + 90 days;
    uint256 public constant PHASE_2_DEADLINE = MAINNET_LAUNCH + 180 days;
    uint256 public constant PHASE_3_DEADLINE = MAINNET_LAUNCH + 365 days;
    
    // Authority tracking
    mapping(address => bool) public emergencyPauseAuthority;
    mapping(address => bool) public modulePublishers;
    
    // Phase 1 enforcement: DAO must be executable by Day 31
    function enforcePhase1() external {
        require(block.timestamp >= MAINNET_LAUNCH + 31 days, "Too early");
        require(daoExecutable == false, "Already enforced");
        
        // Transfer governance execution to DAO contract
        governanceExecutor = address(DAO_CONTRACT);
        daoExecutable = true;
        
        emit Phase1Enforced(block.timestamp);
    }
    
    // Phase 2 enforcement: Multi-publisher signing by Day 91
    function enforcePhase2() external {
        require(block.timestamp >= PHASE_1_DEADLINE, "Too early");
        require(modulePublishers[CRYFT_LABS] == true, "Already enforced");
        
        // Remove Cryft Labs sole authority
        moduleSigningThreshold = 3; // Require 3-of-5
        
        emit Phase2Enforced(block.timestamp);
    }
    
    // Phase 3 enforcement: Remove all special powers by Day 365
    function enforcePhase3() external {
        require(block.timestamp >= PHASE_3_DEADLINE, "Too early");
        
        // Remove emergency pause (irreversible)
        delete emergencyPauseAuthority[CRYFT_LABS];
        emergencyPauseEnabled = false;
        
        // Transfer multisig control to DAO-elected addresses
        federalChainGovernance = DAO_ELECTED_MULTISIG;
        treasuryMultisig = DAO_ELECTED_MULTISIG;
        
        emit Phase3Enforced(block.timestamp);
        emit FullDecentralizationAchieved(block.timestamp);
    }
}
`

**Enforcement guarantees:**

1. **Anyone can trigger enforcement** - Community members can call enforcePhase3() if Cryft Labs delays
2. **Time-locks are immutable** - Deadlines cannot be extended (contract is non-upgradeable)
3. **Public auditability** - All key transfers emit events tracked by block explorers
4. **Slashing for failure** - If Cryft Labs-controlled validators violate post-Phase 3 rules, automatic 10% slash

**Community oversight:**

- **Decentralization Dashboard** (public website): Real-time tracking of all Cryft Labs-controlled keys, validator stake %, module publisher list
- **Quarterly transparency reports**: Cryft Labs publishes detailed breakdown of remaining centralized controls
- **DAO veto power**: Community can vote to accelerate any phase (e.g., force Phase 3 early if desired)

#### 12.4.4 Long-term Cryft Labs role (post-decentralization)

After Phase 3 (Day 365+), Cryft Labs operates as:

**1. Core protocol contributor** (not owner):
- Maintains one of several CryftGo client implementations (alternative clients encouraged)
- Proposes protocol improvements via standard DAO governance (no special voting power)
- Operates <10% of validator stake (subject to further reduction via DAO vote)

**2. Ecosystem development organization:**
- Develops reference Cryftee modules (but requires DAO approval for mainnet inclusion)
- Funds grants for alternative implementations (Go, Rust, TypeScript clients)
- Operates developer documentation and SDKs (community-maintained repos accepted)

**3. Strategic partnerships and adoption:**
- Business development for enterprise State chain deployments
- Integration partnerships with wallets, explorers, RPC providers
- No special on-chain privileges (partnerships negotiated as private contracts)

**Accountability:**

- Cryft Labs subject to same slashing rules as all validators
- DAO can vote to remove Cryft Labs from any funded programs (treasury grants, ecosystem fund)
- Community can fork CryftGo and form alternative governance if Cryft Labs acts against network interest

**Sunset commitment:**

> "By Day 365 post-mainnet, CryftNet will be a credibly neutral protocol with no single point of control. Cryft Labs commits to transferring all special authorities to community governance by this deadline, enforced via immutable time-locked smart contracts. This transition is not a promiseit is code."

