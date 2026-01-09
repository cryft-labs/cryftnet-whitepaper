
**Note:** Section 16 (Appendices) open questions have been transformed into a decision machine with 27 actionable decision items (D-01 through D-27). See Section 16.2 in 15-roadmap.md for the complete decision table with ownership, milestones, and acceptance criteria.

**All open questions from the original list have been converted to decision items with:**
- Type classification (spec/research/simulation/governance/ops)
- Clear ownership (dev/research/tokenomics/ops/governance)
- Milestone assignment (testnet-0/testnet-1/pre-mainnet/post-mainnet)
- Measurable acceptance tests
- Priority tiers (P0=pre-mainnet blockers, P1=testnet-1 required, P2=post-mainnet)

**Example decision items:**
- D-08: Optimal checkpoint frequency -> simulation + throughput model -> "supports X msg/s at Y regions with p95 settlement < Z minutes"
- D-01: Under-claim enforcement -> spec decision -> "no observed nondeterminism in >=10M tx fuzz runs; deterministic fallback works"
- D-24: City emergency bridge to Main (censorship escape hatch) -> spec + governance -> post-mainnet priority

