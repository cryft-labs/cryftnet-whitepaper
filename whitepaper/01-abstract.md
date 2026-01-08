## 1. Abstract

CryftNet (Cryft Network) is a federation of blockchains designed to feel like Web2 in latency while
retaining cryptographic integrity and democratic governance. The network is anchored by the **Primary Network**, which consists of three specialized chains: **(1) P-Chain** for validator/subnet coordination and staking, **(2) X-Chain** for high-throughput native asset transfers and issuance, and **(3) M-Chain** for EVM-compatible smart contract execution. When we say "EVM chain," we mean the M-Chain specifically, not the entire Cryft network. This three-chain architecture prevents governance traffic, asset transfer traffic, and smart contract execution traffic from competing for the same bottleneck. Regional chains ("States") are optimized for low-latency execution and confirmations within a
geographic or network-latency domain. Optional local chains ("Cities") can further reduce latency for
dense communities and settle upward. CryftNet is EVM compatible by default. It introduces an opt-in
deterministic parallel execution mechanism called Smart Slots with Process IDs. Transactions may
declare a process_id and explicit slot claims that map to EVM state (account, storage, or
application-defined resource slots). A deterministic scheduler uses these claims to safely parallelize
execution, confining contention to lanes when necessary while preserving identical results across
validators. Privacy and propagation are addressed by Cryft Global Synchronizer (CGS), a
Cryftee-hosted plane that supports privacy-aware intent gossip, selective disclosure, and region-local
privacy pools, while still enabling scheduling via slot commitments. Cryftee itself is a Rust-based
sidecar runtime that loads signed WASM modules from a manifest, provides a versioned API over
UDS or HTTPS, and includes a kiosk UI for operators. Cryftee modules supply chain utilities including
BLS/TLS staking operations, IPFS node management, and private synchronization. Economic security is complemented by incentive alignment for availability: CryftNet includes explicit IPFS pinning rewards. Pin providers register, bond stake, accept pin jobs, and earn rewards based on verified availability proofs over time. The result is a federation where compute, consensus, privacy propagation, and content availability are governed and incentivized rather than assumed.
