1) PROPOSAL: Circle submits USDC deployment proposal
   - code_hash: keccak256(USDC_bytecode)
   - home_region: Main
   - initial_supply: 1_000_000_000
   - authorized_minter: 0xCircle
   
2) REVIEW: Governance verifies:
   - Constructor has zero initial balances ✓
   - mint() is properly restricted ✓
   - Cross-region logic is correct ✓
   
3) APPROVAL: Governance approves deployment

4) DEPLOY ON MAIN:
   - FederationDeployer.deploy(USDC_bytecode, salt)
   - Contract deployed at 0xUSDC with zero balances
