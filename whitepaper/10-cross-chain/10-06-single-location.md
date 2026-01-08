   - No supply duplication âœ"
```

**Federation Registry tracks initialization:**

```text
Federation Contract Registry entry:

{
  address: 0xToken,
  code_hash: keccak256(bytecode),
  deployer: 0xDev,
  home_region: A,
  mirrored: true,
  balance_portability: true,
  deployed_regions: [A, B, C, D],
  initialized_on: [A],           // Only home region initialized
  total_supply: 1_000_000_000,   // Tracked by GBL
  conservation_verified: true
}
```

### 10.11 Developer experience summary

**Simplest path (region-local):**

```text
1. Deploy contract on your region
2. Done! Contract works locally, no federation complexity
```

**Federation-wide deployment:**

```text
1. Deploy contract on your region with mirrored=true
2. Call initialize() to set initial state
3. Wait ~1-2 checkpoints for Main to mirror to other regions
4. Contract available everywhere, initial state on your region
5. Users on other regions can receive assets via cross-region transfer
```

**Critical infrastructure (Main-first):**

```text
1. Submit governance proposal for deployment
2. After approval, deploy via FederationDeployer on Main
3. Initialize on Main
4. Automatic mirroring to all CSS-1 regions
5. Highest trust level, shown as "Federation Verified"
```

**Comparison:**

| Aspect | Region-First | Main-First |
|:-------|:-------------|:-----------|
| Deployment latency | Instant | Governance delay (days) |
| Initial availability | Home region only | All regions after approval |
| Mirroring delay | 1-2 checkpoints | Automatic |
| Trust level | Publisher-verified or unverified | Federation-verified |
| Best for | Most dApps, experiments | Canonical tokens, bridges |
| Gas cost | Region gas only | Main + region gas |

**Deterministic addresses guaranteed for both paths** - the key is using RegionDeployer with consistent salt computation.

```text
Deployment propagation flow:

1) Main: FederationDeployer deploys contract ->' emits ContractDeployed(address, code_hash)
2) Main: Registry updated -> included in next EVM Chain checkpoint
3) Regions receive checkpoint with deployment record
4) Region: Authorized deployer calls FederationDeployer.deploy(init_code, salt)
5) Region: Verifies deployed address matches checkpoint record
6) Region: Local registry updated, contract is now live

Timing:
- Main deployment: Instant (governance already approved)
- Region deployment: Within 1-2 checkpoint cycles (minutes)
- All regions get same address: Guaranteed by CREATE2 + same parameters
```

**Edge case: Region deploys before receiving checkpoint**

```text
Scenario: Region B validator tries to deploy USDC before Main checkpoint arrives

1) Validator calls FederationDeployer.deploy(USDC_init_code, salt) on Region B
2) FederationDeployer checks: Is this authorized?
   - Queries local authorization cache (synced from Main)
   - If not yet synced: REVERTS with "Authorization not yet received"
3) Validator must wait for checkpoint
4) After checkpoint: authorization cached, deployment proceeds

This prevents regions from "racing ahead" of Main.
```

**Federation Contract Registry:**

Main maintains a registry of canonical contract deployments:

```text
ContractRegistry on Main:
{
  address: 0xUSDC,
  code_hash: keccak256(USDC_bytecode),
  deployer: 0xFederationDeployer,
  salt: keccak256("USDC.v1"),
  deployed_regions: [Main, A, B, C],
  verified: true
}

Region verification:
- Before interacting with 0xUSDC on Region A, contracts can query:
  Main.ContractRegistry.isVerified(0xUSDC) ->' true
- Wallets display verification status to users
- Unverified contracts are flagged as potentially unsafe
```

**Cross-region transfer in partitioned model:**

```text
Alice transfers 100 USDC from Region A ->' Region B:

1) DEBIT on Region A:
   - Alice calls USDC.transferToRegion(amount=100, dest=B, recipient=Alice)
   - USDC contract on Region A:
     - Debits Alice's balance: balances[A][Alice] -= 100
     - Emits CrossRegionTransfer(id=X, from=Alice, to=Alice, amount=100, dest=B)
     - Records pending_outbound[X] = {amount, dest, recipient, status: pending}

2) CHECKPOINT Region A ->' Main:
   - CrossRegionTransfer event included in checkpoint message_root
   - Main finalizes checkpoint

3) CREDIT on Region B:
   - Alice (or relayer) calls USDC.claimFromRegion(transfer_id=X, proof)
   - USDC contract on Region B:
     - Verifies Merkle proof against Main-finalized checkpoint
     - Verifies transfer_id X not already claimed: claimed[X] == false
     - Credits Alice's balance: balances[B][Alice] += 100
     - Marks claimed[X] = true

4) Result:
   - Region A: Alice has 200 USDC (was 300)
   - Region B: Alice has 100 USDC (was 0)
   - No double-spend possible: A's debit is finalized before B's credit
```

**Critical: Preventing balance duplication on deployment**

A subtle but critical attack vector: if a token contract's constructor initializes balances (e.g., `balances[issuer] = 1_000_000_000`), and that contract is deployed on multiple regions with identical init_code, the issuer would have that balance on EVERY region--effectively multiplying their supply.

**The problem:**

```text
Naive deployment (VULNERABLE):

Token constructor:
  constructor() {
    balances[msg.sender] = 1_000_000_000;  // Initial supply to deployer
    totalSupply = 1_000_000_000;
  }

Deployment via CREATE2 with same deployer/salt/init_code:
- Main: issuer has 1B tokens
- Region A: issuer has 1B tokens  
- Region B: issuer has 1B tokens
- Region C: issuer has 1B tokens

Result: Issuer has 4B tokens total! Supply inflated 4x.
```

**Why this happens:**

CREATE2 guarantees the same ADDRESS for same parameters, but each region executes the constructor INDEPENDENTLY. The constructor runs once per region, initializing local storage on each.

**Solution: EVM Chain GBL is the authoritative source**

The contract's local `balances` mapping is a **cache**, not the source of truth. The EVM Chain Global Balance Ledger (GBL) is authoritative:

```text
Federation-aware token architecture:

1) Constructor initializes ZERO balances:
   constructor() {
     // DO NOT set balances here
     // Initial supply is minted via separate transaction
   }

2) Initial mint happens on ONE region only (typically Main):
   - After deployment, issuer calls mint(amount, home_region=Main)
   - Main's GBL records: balances[USDC, Main, issuer] = 1_000_000_000
   - Main's GBL records: total_supply[USDC] = 1_000_000_000
   - No other region has any balance

3) Regional contract reads from GBL (via checkpoint sync):
   - Region A's USDC contract has balances[issuer] = 0 (no mint occurred here)
   - Region B's USDC contract has balances[issuer] = 0
   - Only Main shows issuer's balance

4) If issuer wants balance on Region A:
   - Must use transferToRegion(Main ->' A)
   - Normal cross-region transfer rules apply
```

**Contract implementation pattern:**

```solidity
// Federation-aware ERC20 (conceptual)
contract FederatedToken {
    // Local balance cache (synced from GBL via checkpoints)
    mapping(address => uint256) public balances;
    
    // Region identifier (set at deployment)
    uint64 public immutable REGION_ID;
    
    // Federation registry reference
    IFederationRegistry public immutable registry;
    
    constructor(uint64 _regionId, address _registry) {
        REGION_ID = _regionId;
