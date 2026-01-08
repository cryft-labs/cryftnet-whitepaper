
4. **Higher latency for cross-region is expected:** If Alice is in Region B but her balance is on Region A:
   - She can relay her transaction to Region A (incurs cross-region latency).
   - Or she transfers balance to Region B first (one-time migration cost, then local speed).

**Contract deployment models:**

CryftNet supports multiple deployment models to balance developer convenience with federation coordination. The most user-friendly approach is **region-first deployment with opt-in federation mirroring**.

**Critical: Region ID requirements**

**Primary Network M-Chain does NOT require region IDs.** The M-Chain (EVM execution chain within the Primary Network) is the default chain for dApp interactionsâ€"users and developers interact with M-Chain exactly like a standard EVM chain. Region IDs are only required when operating on State/Region chains or requesting cross-region operations.

| Operation | Chain | Region ID Required? |
|:----------|:------|:--------------------|
| Deploy contract | Primary Network M-Chain | **NO** |
| Call contract | Primary Network M-Chain | **NO** |
| Transfer tokens | Primary Network M-Chain | **NO** |
| Deploy contract | State/Region chain | YES (implicit from submission endpoint) |
| Call contract | State/Region chain | YES (implicit from submission endpoint) |
| Request mirroring to regions | Primary Network M-Chain | YES (explicit target_regions[]) |
| Cross-region transfer | Any chain | YES (explicit dest_region) |

**Why the Primary Network M-Chain doesn't need region IDs:**
- The Primary Network (P + X + M) is the canonical foundationâ€"it has no "region" because it IS the federation anchor
- Transactions submitted to M-Chain execute on M-Chain; there's no ambiguity
- This preserves standard EVM UX for M-Chain interactions
- Region IDs are only needed when the user wants to interact with a specific State/Region chain OR move assets across regions

**Explicit region ID declaration (for federation operations):**

When users or developers want federation-wide operations, they MUST explicitly declare target region IDs. This ensures:

1. **Proper fee collection:** Main receives gas fees proportional to the number of regions being updated
2. **Developer control:** Deployers choose exactly which regions they pay for
3. **No surprise costs:** Users know upfront what they're paying for
4. **Scalability:** Main doesn't automatically push to all regions

```text
Transaction region declaration (federation operations only):

// Deploy or update transaction includes explicit region list
tx.target_regions = [A, B, C]  // Explicit opt-in regions

Fee calculation:
  base_fee = local_gas_cost
  federation_fee = Î£(per_region_fee[r] for r in target_regions)
  total_fee = base_fee + federation_fee

If target_regions is empty or omitted:
  â†' Transaction is local only (Main or single region)
  â†' No federation fees charged
  â†' Contract/balance exists only on execution region
```

### 10.8 Region-first deployment with federation mirroring

**Core principle:** Developers deploy to their preferred region first. Main automatically detects new contracts via checkpoints and can mirror them to **explicitly declared regions** if the developer opts in and pays the appropriate fees.

**Region ID requirements:**

| Interaction Type | Region ID Required? | Notes |
|:-----------------|:--------------------|:------|
| **Main C-Chain transactions** | **NO** | Main is the default home chain; no region declaration needed |
| **Main C-Chain contract deployment** | **NO** | Deploys directly on Main; mirroring requires target_regions[] |
| **State/Region chain transactions** | YES | Must specify which region to execute on |
| **Cross-region transfers** | YES | Must specify dest_region explicitly |
| **Federation mirroring** | YES | Must declare target_regions[] and pay fees |

**Main as the default chain:** Users interacting with Main Federal C-Chain do not need to specify any region ID. Main is the "home" chain of the federationâ€"transactions submitted to Main execute on Main. Region IDs are only required when:
1. Deploying or transacting on State/Region chains
2. Requesting federation mirroring to specific regions
3. Initiating cross-region asset transfers

**Deployment modes:**

| Mode | Scope | Region Declaration | Fee Structure |
|:-----|:------|:-------------------|:--------------|
| **Main-direct** | Main C-Chain only | None required | Main gas only |
| **Region-local** | Single region only | Implicit (current region) | Region gas only |
| **Federation-mirrored** | Declared regions | Explicit target_regions[] | Origin + per-region fee |
| **Main-first (governance)** | All CSS-1 regions | Explicit or "all CSS-1" | Main + per-region fee |

**Main-direct deployment (no region ID needed):**

```text
Developer deploys contract directly on Main C-Chain:

1) Dev deploys via standard CREATE2 or FederationDeployer on Main
   - NO region ID required - Main is the default chain
   - Transaction: deploy(init_code, salt)
   - Fee: Main gas only
   
2) Contract exists on Main C-Chain
   - Users interact with contract on Main without specifying region
   - Standard EVM experience, no federation complexity
   
3) Optional: Request mirroring to regions later
   - Call FederationRegistry.requestMirroring(contract, target_regions[])
   - Pay federation fees for each target region
   - Main triggers mirroring via checkpoints

Use case: Main-only contracts, governance, canonical registries
```

**Region-local deployment (requires region context):**

```text
Developer deploys GameContract on Region A:

1) Dev deploys via RegionDeployer on Region A
   - RegionDeployer.deploy(init_code, salt, options={
       target_regions: []  // Empty = local only
     })
   - Contract deployed at address 0xGame (deterministic via CREATE2)
   - Fee: Region A gas only
   
2) Contract exists ONLY on Region A
   - balances[Alice] = 100 tokens (on Region A only)
   - Users in Region A interact normally
   
3) Main sees deployment in Region A's checkpoint
   - Records in registry: {address: 0xGame, home_region: A, target_regions: [A]}
   - Does NOT deploy to other regions (none declared)
   
4) Users in Region B cannot interact with 0xGame
   - Contract doesn't exist on Region B
   - Wallet shows: "This contract is only available on Region A"
```

**Federation-mirrored deployment (explicit region opt-in):**

```text
Developer wants token available on Regions A, B, C (not D or E):

1) Dev deploys via RegionDeployer on Region A (their local region)
   - RegionDeployer.deploy(init_code, salt, options={
       target_regions: [A, B, C],    // EXPLICIT region list
       balance_portability: true,
       home_region: A
     })
   - Contract deployed at 0xToken on Region A
