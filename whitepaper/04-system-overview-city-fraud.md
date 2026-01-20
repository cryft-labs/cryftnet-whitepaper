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

**Step 3: Appeal to Federal Chain (if State refuses)**

If State chain censors emergency exit or is offline:

```solidity
// Federal Chain emergency exit (last resort)
function emergencyExitFromCityToFederal(
    uint64 city_id,
    uint64 state_id,
    uint64 city_checkpoint_height,
    uint64 state_checkpoint_height,
    address account,
    bytes32 asset_id,
    uint256 balance,
    bytes32[] calldata city_merkle_proof,
    bytes32[] calldata state_merkle_proof
) external {
    // 1. Verify State checkpoint exists on Federal Chain
    Checkpoint memory stateCP = checkpoints[state_id][state_checkpoint_height];
    require(stateCP.height > 0, "State checkpoint not found");
    
    // 2. Verify State checkpoint includes City's balance root (via Merkle proof)
    // ... (implementation details)
    
    // 3. Verify City balance Merkle proof
    bytes32 leaf = keccak256(abi.encodePacked(account, asset_id, balance));
    bool valid = MerkleProof.verify(city_merkle_proof, city_balance_root, leaf);
    require(valid, "Invalid City Merkle proof");
    
    // 4. Verify 72-hour waiting period (prevents impatient appeals)
    require(block.timestamp > stateCP.timestamp + 72 hours, "Must wait 72h for State response");
    
    // 5. Credit balance to Federal-direct
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

**Attack: User double-claims (exits same balance twice)**

Prevention:
- `exits[exit_key]` mapping tracks claimed balances per checkpoint
- Second claim with same (city_id, checkpoint_height, account, asset_id) reverts

**Attack: Spam emergency exits to DOS State/Federal Chain**

Prevention:
- Emergency exit requires gas fee (economic cost)
- Rate limiting: Max 10 exits per block per account
- Governance can pause emergency exits if abuse detected (requires 67% vote)

**Attack: City validators collude to create fake checkpoint with inflated balances**

Prevention (fraud proof mechanism):

```text
Fraud proof submission (by honest observer):

1. Observer detects invalid City checkpoint
2. Observer submits fraud proof to State:
   - City checkpoint header (balance_merkle_root, quorum, epoch)
   - Proof of invalid transition
   - Merkle proofs for before/after state
3. State verifies fraud proof by re-executing disputed transactions
4. If fraud proven: State slashes City validators (10% stake)
5. State initiates emergency City shutdown
```

**Fraud proof data structure:**

```solidity
struct CityFraudProof {
    uint64 city_id;
    uint64 disputed_checkpoint_height;
    bytes32 claimed_balance_root;
    bytes32 computed_balance_root;
    Transaction[] disputed_txs;
    bytes32[] state_merkle_proofs;
    bytes fraud_evidence;
}

function submitCityFraudProof(CityFraudProof calldata proof) external {
    bool isValid = verifyCityFraudProof(proof);
    require(isValid, "Invalid fraud proof");
    
    slashCityValidators(proof.city_id, FRAUD_PENALTY);
    fraudulent_checkpoints[proof.city_id][proof.disputed_checkpoint_height] = true;
    rewardFraudProver(msg.sender, FRAUD_PENALTY * 10 / 100);
    
    emit CityFraudProven(proof.city_id, proof.disputed_checkpoint_height);
}
```

**Economic incentives:**

| Role | Action | Incentive | Penalty |
|:-----|:-------|:----------|:--------|
| City validators | Submit honest checkpoints | Block rewards + fees | 10% slash for fraud |
| State validators | Process City checkpoints | Checkpoint fees | 2% slash for censorship |
| Users | Emergency exit only when needed | Recover funds | Gas costs (prevents spam) |
| Fraud provers | Submit valid fraud proofs | 10% of slashed stake | None (invalid proofs rejected) |

**Version marker: (v1) City emergency exit and fraud proof mechanisms are mainnet-required for hierarchical City deployment.**
