An attacker could deploy their own token (Tier 3: unverified) with inflated balances:

```text
Attacker deploys ScamToken on multiple regions with constructor:
  balances[attacker] = 1_000_000_000 per region

Result:
- Attacker has billions of ScamToken on each region
- BUT: ScamToken is NOT in Federation Registry
- Wallets show: "⚠️ Unverified contract"
- Users know not to trust it
- ScamToken has no relationship to legitimate tokens
- Cannot be traded on federation DEXs (which require verified tokens)
```

**Why same init_code with balances would be detected:**

Even if an attacker tries to deploy the EXACT same code as a legitimate token (to get the same address):

1. They cannot deploy at the same address without using FederationDeployer (which requires authorization)
2. If they deploy with a different deployer, they get a different address
3. FederationDeployer only accepts deployments that match governance-approved code_hash
4. Governance-approved code MUST use the "zero-balance constructor" pattern
5. Any contract with constructor-initialized balances fails code review and isn't approved

```text
Governance code review checklist for token approval:
☑ Constructor does NOT initialize balances
☑ Constructor does NOT set totalSupply to non-zero
☑ mint() restricted to authorized minter
☑ mint() restricted to home region
☑ Code matches submitted code_hash exactly
☑ Contract implements IFederatedToken interface
☑ Cross-region transfer functions are correct
```

**Deployment flow with balance safety:**

```text
Safe federated token deployment:

