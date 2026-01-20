#### 10.1.1 Checkpoint verification algorithm (v1 normative)

**Problem:** Federal Chain receives checkpoint from Region R at epoch E. How does Federal Chain verify the quorum signature without storing every region's full validator set?

**Solution:** Canonical validator set tracking via Federal Chain registry + commitment-based verification.

**Step 1: Validator set registration (performed once per epoch or on validator set change)**

Regions register their validator set with Federal Chain at epoch boundaries:

```text
ValidatorSetCommitment = {
  region_id: 42,
  epoch: 771,
  validator_set: [
    {pubkey: 0xVal1, stake: 1500, status: ACTIVE},
    {pubkey: 0xVal2, stake: 2000, status: ACTIVE},
    {pubkey: 0xVal3, stake: 1200, status: ACTIVE},
    // ... up to N validators
  ],
  total_stake: 4700,
  quorum_threshold: 3149,  // 67% of total_stake
  validator_set_hash: keccak256(serialize(validator_set)),
  transition_height: 8240000,  // height at which this set becomes active
  registration_signature: BLS_AGG_SIG  // quorum of PREVIOUS validator set
}
```

**Federal Chain stores:**

```solidity
// Canonical registry on Federal Chain
mapping(uint64 region_id => mapping(uint64 epoch => ValidatorSetCommitment)) public validatorSets;
mapping(uint64 region_id => uint64 current_epoch) public currentEpoch;

// Fast lookup: validator_set_hash -> ValidatorSetCommitment
mapping(bytes32 validator_set_hash => ValidatorSetCommitment) public validatorSetByHash;
```

**Step 2: Checkpoint submission**

Region submits checkpoint to Federal Chain:

```solidity
function submitCheckpoint(Checkpoint memory cp) external {
    // 1. Retrieve validator set for this epoch
    ValidatorSetCommitment memory valSet = validatorSets[cp.region_id][cp.epoch];
    require(valSet.epoch == cp.epoch, "Validator set not registered for epoch");
    
    // 2. Verify validator_set_hash matches
    require(cp.validator_set_hash == valSet.validator_set_hash, "Validator set hash mismatch");
    
    // 3. Verify quorum signature
    bool valid = verifyBLSAggregateSignature(
        cp.quorum.sig,
        cp.quorum.signers_bitmap,
        valSet.validator_set,
        checkpointCommitment(cp)
    );
    require(valid, "Invalid quorum signature");
    
    // 4. Verify quorum threshold met
    uint256 signingStake = computeSigningStake(cp.quorum.signers_bitmap, valSet.validator_set);
    require(signingStake >= valSet.quorum_threshold, "Insufficient stake");
    
    // 5. Store checkpoint
    checkpoints[cp.region_id][cp.height] = cp;
    emit CheckpointAccepted(cp.region_id, cp.height, cp.block_hash);
}
```

**Step 3: Signature verification details**

```text
Function: verifyBLSAggregateSignature(sig, bitmap, validator_set, message)

1. Extract signing validators from bitmap:
   signing_validators = []
   for i in range(len(validator_set)):
       if bitmap[i] == 1:
           signing_validators.append(validator_set[i])

2. Aggregate public keys:
   agg_pubkey = BLS_Aggregate([v.pubkey for v in signing_validators])

3. Verify signature:
   message_hash = keccak256(message)
   return BLS_Verify(agg_pubkey, message_hash, sig)

Function: computeSigningStake(bitmap, validator_set)

1. total = 0
2. for i in range(len(validator_set)):
       if bitmap[i] == 1:
           total += validator_set[i].stake
3. return total

Function: checkpointCommitment(cp)

1. Serialize checkpoint fields (excluding quorum):
   data = abi.encodePacked(
       cp.region_id,
       cp.chain_id,
       cp.height,
       cp.block_hash,
       cp.state_root,
       cp.message_root,
       cp.validator_set_hash,
       cp.epoch,
       cp.ping_epoch
   )
2. return keccak256(data)
```

**Step 4: Handling mid-epoch validator set changes**

**Scenario:** Region's validator set changes at height 8240500 (mid-epoch 771).

**Solution: Dual validator set support**

```text
1. Region registers new validator set with Federal Chain:
   - epoch: 771 (same)
   - transition_height: 8240500
   - validator_set_hash: 0xNEW
   - registration_signature: signed by CURRENT (old) validator set

2. Federal Chain tracks both:
   validatorSets[42][771] = [
     {validator_set_hash: 0xOLD, valid_until: 8240499},
     {validator_set_hash: 0xNEW, valid_from: 8240500}
   ]

3. Checkpoint verification uses height-based lookup:
   if (cp.height < 8240500):
       use validator_set_hash = 0xOLD
   else:
       use validator_set_hash = 0xNEW

4. Checkpoint at height 8240500+ MUST use validator_set_hash = 0xNEW
   (transition enforced at boundary)
```

**Step 5: Light client verification (minimum data)**

**Full verification (requires validator set):**
- Federal Chain stores full validator set (~10KB per region per epoch)
- Verifies BLS aggregate signature + stake threshold
- Required for: Federal Chain nodes, critical infrastructure

**Light verification (requires only validator_set_hash + trust assumption):**
- Client fetches: checkpoint + quorum signature + validator_set_hash
- Client verifies: validator_set_hash is registered on Federal Chain (via Merkle proof)
- Client trusts: Federal Chain verified the full quorum (does not re-verify BLS sig)
- Minimum data: ~500 bytes (checkpoint + Merkle proof)
- Required for: Wallets, light clients, mobile apps

**Light client verification algorithm:**

```text
1. Client fetches checkpoint from region RPC
2. Client queries Federal Chain: getValidatorSetHash(region_id, epoch)
3. Federal Chain returns: (validator_set_hash, Merkle_proof_of_registration)
4. Client verifies Merkle proof against Federal Chain state root
5. Client checks: checkpoint.validator_set_hash == registered_validator_set_hash
6. If match: checkpoint is valid (Federal Chain already verified full quorum)
7. If no match: reject checkpoint
```

**Trust model:**
- Light clients trust Federal Chain's checkpoint acceptance (2/3+ honest Federal validators)
- Full nodes independently verify checkpoint signatures (zero trust)
- Regions cannot submit fake checkpoints (quorum signature required)
- Federal Chain cannot accept checkpoints with < 67% stake (enforced by BLS verification)

**Failure modes:**

| Scenario | Detection | Mitigation |
|:---------|:----------|:-----------|
| Region submits checkpoint with wrong validator_set_hash | Federal Chain rejects (hash mismatch) | Region re-submits with correct hash |
| Validator set not registered for epoch | Federal Chain rejects (no valSet entry) | Region must register validator set first |
| Quorum signature invalid | Federal Chain rejects (BLS verify fails) | Indicates Byzantine behavior or bug; region investigates |
| Insufficient stake (<67%) | Federal Chain rejects (below threshold) | Region collects more signatures before re-submitting |
| Mid-epoch validator set change without registration | Federal Chain rejects future checkpoints | Region must register new set before transition height |

**Performance considerations:**

- Validator set registration: Once per epoch (~10 minutes) or on change
- Registration cost: ~50,000 gas (Federal Chain transaction)
- Checkpoint verification cost: ~200,000 gas (BLS aggregate + stake computation)
- Light client verification cost: ~5,000 gas (Merkle proof only)
- Federal Chain storage per region: ~10KB per epoch (validator set) + ~1KB per checkpoint

**Version marker: (v1) All checkpoint verification rules are mainnet-required and implemented.**
