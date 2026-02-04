### 13.3.1 BLS/TLS Signer Module (`bls_tls_signer_v1`)

The staking module provides cryptographic operations for validator participation with automatic TLS-first Node ID derivation for multi-device support.

**Version:** 1.2.0  
**Category:** Staking  
**Status:** Core Module (required for full network capability)

---

#### Purpose

- BLS (Boneh-Lynn-Shacham) signature generation for block proposals and votes
- TLS certificate management for secure peer communication
- Automatic TLS-first Node ID derivation for multi-device isolation
- Module signing for Cryftee's trust model
- Integration with Web3Signer for key custody

---

#### Node ID Derivation

The module implements TLS-first identity bootstrapping:

1. On first initialization, auto-bootstraps TLS identity if none exists
2. Derives unique Node ID from TLS public key: `"NodeID-" + SHA256(pubkey)[0:40]`
3. Keys are namespaced per device under `/keys/{NodeID}/` for multi-device isolation

---

#### Storage Backends

| Backend | Use Case | Description |
|:--------|:---------|:------------|
| **Vault** | Production (recommended) | HashiCorp Vault integration for secure key storage |
| **Local Keystore** | Development/small deployments | EIP-2335 compatible encrypted JSON files |
| **Memory** | Testing only | Non-persistent storage, keys lost on restart |

---

#### Capabilities

| Function | Description |
|:---------|:------------|
| `bls_register` | Register a new BLS public key for staking |
| `bls_sign` | Sign a message using the validator's BLS key |
| `bls_verify` | Verify a BLS signature |
| `tls_register` | Register TLS certificate for peer authentication |
| `tls_sign` | Sign data for TLS handshakes |
| `tls_verify` | Verify TLS signatures |
| `module_signing_key` | Retrieve the dedicated WASM module signing key |
| `sign_module` | Sign a WASM module for distribution |
| `verify_module` | Verify a module signature before load |
| `hash_module` | Compute hash of a WASM module binary |

---

#### Web3Signer Integration

The module delegates key operations to Web3Signer when configured:

```text
WEB3SIGNER_API_URL=http://localhost:9000
WEB3SIGNER_TLS_CERT=/path/to/web3signer.crt
```

This allows validators to use hardware security modules (HSMs) or other secure key custody solutions without exposing keys to the Cryftee process.

---

#### Configuration

```text
CRYFTTEE_BLS_BACKEND=vault|keystore|memory
CRYFTTEE_VAULT_ADDR=http://localhost:8200
CRYFTTEE_VAULT_TOKEN=<token>
CRYFTTEE_KEYSTORE_PATH=/path/to/keystore
```
