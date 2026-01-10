        registry = IFederationRegistry(_registry);
        // NO initial balances set here
    }
    
    // Only callable by authorized minter, only on designated home region
    function mint(address to, uint256 amount) external {
        require(msg.sender == registry.authorizedMinter(address(this)));
        require(REGION_ID == registry.homeRegion(address(this)), 
                "Mint only allowed on home region");
        
        balances[to] += amount;
        // Emit event for Mirror GBL to record
        emit Mint(to, amount, REGION_ID);
    }
    
    // Credits from cross-region transfers (called after checkpoint verification)
    function creditFromTransfer(
        bytes32 transferId, 
        address to, 
        uint256 amount,
        bytes calldata proof
    ) external {
        require(!claimed[transferId], "Already claimed");
        require(verifyCheckpointProof(proof), "Invalid proof");
        
        balances[to] += amount;
        claimed[transferId] = true;
        emit CreditFromTransfer(transferId, to, amount);
    }
}
```

**Home region concept:**

Each federated token has a designated **home region** where initial minting occurs:

```text
Token Registry entry:
{
  address: 0xUSDC,
  code_hash: ...,
  home_region: Main,          // Only Main can mint new supply
  total_supply: 1_000_000_000,
  authorized_minter: 0xCircle,
  deployed_regions: [Main, A, B, C]
}

Rules:
- mint() only succeeds on home_region
- Existing supply moves between regions via transferToRegion()
- Mirror Chain GBL tracks: sum(balances across all regions) = total_supply
- Any discrepancy = bug or attack -> bridge pause
```

**What about attacker deploying their own token?**

