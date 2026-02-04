### 13.3 Core Modules

This section describes the foundational modules included in Cryftee's initial release (v0.4.x runtime). All modules follow the **Power of Ten** safety rules: static bounds declared at module top, no unsafe code, proper error handling (no panics), self-contained limits, and comprehensive input validation.

#### 13.3.1 Module Overview

| Module | Version | Purpose | Representative Capabilities |
|:-------|:--------|:--------|:---------------------------|
| `bls_tls_signer_v1` | 1.2.0 | BLS + TLS staking with multi-device support | bls_register, bls_sign, bls_verify, tls_register, tls_sign, tls_verify, sign_module, verify_module, hash_module |
| `debug_v1` | 1.0.0 | Diagnostics and runtime inspection | debug_echo, debug_info, debug_panic |
| `llm_chat_v1` | 2.0.0 | Multi-provider LLM assistant with session management | llm_chat, llm_stream, session management |

#### 13.3.2 BLS/TLS Signer Module (`bls_tls_signer_v1`)

The staking module provides cryptographic operations for validator participation with automatic TLS-first Node ID derivation for multi-device support.

**Purpose:**
- BLS (Boneh-Lynn-Shacham) signature generation for block proposals and votes
- TLS certificate management for secure peer communication
- Automatic TLS-first Node ID derivation for multi-device isolation
- Module signing for Cryftee's trust model
- Integration with Web3Signer for key custody

**Node ID Derivation:**

The module implements TLS-first identity bootstrapping:
1. On first initialization, auto-bootstraps TLS identity if none exists
2. Derives unique Node ID from TLS public key: `"NodeID-" + SHA256(pubkey)[0:40]`
3. Keys are namespaced per device under `/keys/{NodeID}/` for multi-device isolation

**Storage Backends:**

| Backend | Use Case | Description |
|:--------|:---------|:------------|
| **Vault** | Production (recommended) | HashiCorp Vault integration for secure key storage |
| **Local Keystore** | Development/small deployments | EIP-2335 compatible encrypted JSON files |
| **Memory** | Testing only | Non-persistent storage, keys lost on restart |

**Capabilities:**

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

**Web3Signer Integration:**

The module delegates key operations to Web3Signer when configured:
```text
WEB3SIGNER_API_URL=http://localhost:9000
WEB3SIGNER_TLS_CERT=/path/to/web3signer.crt
```

This allows validators to use hardware security modules (HSMs) or other secure key custody solutions without exposing keys to the Cryftee process.

#### 13.3.3 Debug Module (`debug_v1`)

The debug module provides diagnostic capabilities for operators:

**Purpose:**
- Runtime inspection and health checks
- Testing module communication and round-trip connectivity
- Controlled panic for testing error handling
- Lightweight diagnostics for development and troubleshooting

**Capabilities:**

| Function | Description |
|:---------|:------------|
| `debug_echo` | Echo input back to caller (connectivity test) |
| `debug_info` | Return runtime version, loaded modules, and environment info |
| `debug_panic` | Trigger a controlled panic for testing error handling |

**Security Note:** The `debug_panic` function SHOULD be disabled in production deployments. Operators can configure via:
```text
CRYFTTEE_DEBUG_PANIC_ENABLED=false
```

#### 13.3.4 LLM Chat Module (`llm_chat_v1`)

The LLM module provides a self-contained interactive AI assistant for runtime and module interaction, with all conversation state managed in-module.

**Purpose:**
- Answer operator questions about Cryftee configuration
- Assist with troubleshooting and diagnostics
- Provide documentation and guidance
- Multi-provider support for flexibility

**Architecture:**
- Self-contained chat interface managing all conversation state in-module
- Host calls used ONLY for network I/O to external APIs
- Token counting and context management to stay within model limits
- Response streaming assembly for real-time chat

**Session Management:**

| Limit | Value |
|:------|:------|
| Max concurrent sessions | 50 |
| Max context window | 128k tokens |
| Session timeout | Configurable per provider |

**Supported Providers:**

| Provider | Models | Notes |
|:---------|:-------|:------|
| **OpenAI** | GPT-4, GPT-3.5-turbo | Default provider |
| **Anthropic** | Claude-3-opus, Claude-3-sonnet | Extended context support |
| **Local** | Llama, Mistral | Self-hosted, no external API calls |

**Capabilities:**

| Function | Description |
|:---------|:------------|
| `llm_chat` | Send a message and receive a complete response |
| `llm_stream` | Send a message and receive a streaming response |

**Configuration:**
```text
CRYFTTEE_LLM_PROVIDER=openai|anthropic|local
CRYFTTEE_LLM_API_KEY=<key>
CRYFTTEE_LLM_MODEL=gpt-4
CRYFTTEE_LLM_MAX_SESSIONS=50
CRYFTTEE_LLM_CONTEXT_WINDOW=128000
```

**Security Note:** LLM outputs are NOT consensus-critical. The module provides operator assistance only; no LLM responses affect chain state or validator behavior

