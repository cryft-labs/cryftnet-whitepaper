### 10.9 Region-first deployment with federation mirroring

Developers may opt to deploy to a region first, later mirror to Primary Network. The federation
mirror ensures all contracts eventually appear in the Code Vault on Main, but region-first workflows
allow staging, local optimizations, or gradual rollouts. When a contract is later mirrored to Main,
the Canonical CMR from the region is imported into Main's vault, preserving region-specific bytecode
and linking region-based execution outputs back to Main. Any disputes about region execution can be
anchored in Main using fraud proofs referencing the CMR in the Code Vault.

#### 10.9.1 Region ID requirement table

| Deployment Mode | Primary Network State | Region chain state | RegionID in CMR | Mirror flow | Mirror trigger |
|:----------------|:---------------------|:-------------------|:---------------|:------------|:--------------|
| **Main-direct** | CMR in Main EVM | n/a (no region) | n/a | n/a | n/a |
| **Region-local** | no CMR initially | CMR in Region EVM | region_id | manual or auto | dev or policy |
| **Federation-mirrored** | CMR in Main EVM | CMR also in Region EVM | region_id in region's CMR | auto federation | checkpoint + governance |

**Main-direct deployment:**
```solidity
// Developer deploys to Main EVM Chain (Primary Network)
// CMR is created automatically in Main EVM Chain
CMR {
  contract_hash: keccak256(bytecode),
  deployment_height: MainBlock,
  region_id: null,              // Primary Network deployment
  vault_cid: ipfs://Qm...,
  delegation_mode: NATIVE_EVM   // Standard EVM execution on Main
}
```

**Region-local deployment:**
```solidity
// Developer deploys to Region A EVM Chain
// Region A creates its own CMR
CMR_Region {
  contract_hash: keccak256(bytecode),
  deployment_height: RegionBlock,
  region_id: "region_a_42",     // Explicit region ID
  vault_cid: ipfs://Qm...,
  delegation_mode: REGION_EVM   // Executes locally in region
}

// Later, Region A checkpoint includes CMR reference
Checkpoint_A {
  height: RegionBlock,
  contracts_deployed: [CMR_Region.contract_hash],
  ...
}

// Federation mirrors CMR to Main (triggered by checkpoint or governance)
CMR_Main {
  contract_hash: keccak256(bytecode),  // Same hash
  deployment_height: MainBlockMirrored,
  region_id: "region_a_42",            // References region
  vault_cid: ipfs://Qm...,             // Same IPFS CID
  delegation_mode: REGION_DELEGATED,   // Execution in region, but CMR visible on Main
  origin_checkpoint: Checkpoint_A_hash
}
```

**Federation-mirrored deployment:**
```solidity
// Automatic mirroring: Region submits checkpoint with contract registry update
// Main validator quorum verifies checkpoint and auto-mirrors new CMRs

Mirroring_Transaction {
  type: "MIRROR_CONTRACT",
  source_region: "region_a_42",
  checkpoint_ref: 0x1234...,
  contract_hash: 0xabcd...,
  vault_cid: "ipfs://Qm...",
  proof: aggregated_sig  // Proves region quorum approved
}

// Main EVM Chain processes mirroring transaction:
if verify_checkpoint_proof(proof) and verify_quorum(proof):
  CMR_Main = create_mirror(
    contract_hash=0xabcd...,
    region_id="region_a_42",
    vault_cid="ipfs://Qm...",
    delegation_mode=REGION_DELEGATED
  )
  emit ContractMirrored(CMR_Main.contract_hash, "region_a_42")
```

