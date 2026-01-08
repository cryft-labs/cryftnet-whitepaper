## 3. Background and problem statement

Global blockchains face two constraints: physics and contention. The speed of light and the Internet's
routing behavior impose a lower bound on propagation. At the same time, many workloads contend
on shared state (balances, nonces, popular contracts). Larger validator committees increase security
but also increase coordination time and validation bandwidth, creating diminishing returns on latency.
CryftNet treats latency domains as a design primitive. Instead of forcing one global committee to
finalize everything, regional committees provide fast local confirmations for nearby users. The Main
chain acts as a global settlement and governance anchor: regions periodically checkpoint upward,
enabling cross-region settlement without requiring every transaction to wait for global propagation.
Parallel execution is a complementary axis. EVM semantics are serial; naive parallelism breaks
determinism and can lead to chain splits. CryftNet introduces Smart Slots: explicit read/write claims
that enable deterministic, validator-consistent scheduling. When contracts cannot be parallelized,
they fall back to serial lanes. Modern networks also depend on content distribution: portals, module
artifacts, and application assets. IPFS makes this content-addressed and tamper-evident, but
availability remains an economic problem. CryftNet includes pinning rewards and auditable availability proofs so that "the network stays alive" is not a matter of goodwill.
