Transfer back (Region B â†' Region A):

1) BURN on Region B:
   - User calls bridge.burn(asset, amount, dest_region=A, recipient)
   - Asset is destroyed on Region B

2) CHECKPOINT to Main:
   - Burn event included in Region B's checkpoint

3) UNLOCK on Region A:
   - User submits proof of burn to Region A
   - Original locked asset is released to recipient
```

**Why this prevents double-spending:**

| Attack Vector | Prevention Mechanism |
|:--------------|:---------------------|
| Spend on A, then transfer to B | Lock happens first; asset is frozen before checkpoint |
| Transfer to B, then spend on A | Asset is locked; spending fails |
| Claim on B twice | transfer_id is marked as consumed after first claim |
| Forge proof of lock | Merkle proof verification against Main-finalized checkpoint |
| Collude with Region A validators to fake lock | Main checkpoint requires quorum signature; ZK proofs add trustlessness |

**Alternative: Partitioned balance model (recommended)**

Rather than wrapped tokens, CryftNet can use a **partitioned balance model** where:

- The same contract address exists on all regions (deterministic deployment via CREATE2).
- Account balances are **region-specific**: your balance on Region A is independent of Region B.
- Cross-region transfers explicitly move balance from one region to another.
- All regions are aware of the contract's existence, but state is partitioned.

This model is conceptually cleaner and avoids "wrapped token" confusion:

```text
Partitioned Balance Model:

Token: USDC (deployed at 0xUSDC on all regions via CREATE2)

User Alice's balances:
â"œâ"€â"€ Main:     500 USDC   (Alice can spend on Main)
â"œâ"€â"€ Region A: 300 USDC   (Alice can spend on Region A)
â"œâ"€â"€ Region B:   0 USDC   (Alice has no Region B balance)
â""â"€â"€ Region C: 200 USDC   (Alice can spend on Region C)

Total Alice owns: 1000 USDC (sum of all regional balances)

To spend on Region B, Alice must first transfer from another region.
```

**Why partitioned balances are safe:**

1. **No double-spend possible:** Alice's Region A balance can only be spent on Region A. To use it on Region B, she must first transfer (which debits A, then credits B after checkpoint).

2. **Clear ownership:** Each regional balance is fully owned and spendable only on that region until explicitly moved.

3. **Atomic transfers:** The cross-region transfer is atomic at the Main checkpoint level:
   - Debit on origin region is checkpointed to Main.
   - Credit on destination requires proof of the debit checkpoint.
