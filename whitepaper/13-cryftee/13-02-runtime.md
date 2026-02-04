### 13.2 Runtime Properties and Trust Model

This section describes Cryftee's runtime architecture, module loading, API surface, and security model.

#### 13.2.1 Core Runtime Properties

Cryftee provides:
- Loads and manages signed WASM modules from a manifest.json registry
- Provides BLS/TLS staking key operations via modular plugins
- Exposes a versioned API over Unix Domain Socket (default) or HTTPS
- Includes a kiosk web UI on port 3232 with per-module GUIs rendered as tabs
- Enforces version compatibility (minCryftteeVersion) and publisher trust

#### 13.2.2 Trust Model: Signed Modules and Publisher Verification

All modules are verified before load:

- Hash verification against manifest.json
- Signature verification (Ed25519) against trust.toml
- GitHub-based verification (signed commits, CI builds, attestations) under policy

Rejected modules do not load and do not affect runtime stability.

```toml
# trust.toml (example)
[[publishers]]
id        = "cryft-labs"
algo      = "ed25519"
publicKey = "BASE64_PUBLIC_KEY_HERE"

[[github_publishers]]
id                     = "cryft-labs"
github_org             = "cryft-labs"
allowed_repos          = ["cryfttee-modules"]
require_signed_commits = true
require_actions_build  = true
allowed_workflows      = ["release.yml"]
allow_prereleases      = false
```

#### 13.2.3 API Surface

Cryftee provides endpoints organized by function:

**Staking Endpoints:**
```text
POST /v1/staking/bls/register
POST /v1/staking/bls/sign
POST /v1/staking/tls/register
POST /v1/staking/tls/sign
GET  /v1/staking/status
```

**Runtime/Admin Endpoints:**
```text
GET  /v1/runtime/attestation
GET  /v1/schema/modules
POST /v1/admin/reload-modules
```

**Module GUI Endpoints:**
```text
GET  /api/modules/{module_id}/gui/
```

The transport can be UDS (default) or HTTPS.

#### 13.2.4 Module Manifest Format

Modules are declared in manifest.json with hash and signature verification:

```json
{
  "modules": [
    {
      "id": "bls_tls_signer_v1",
      "version": "1.2.0",
      "required": true,
      "hash": "sha256:abc123...",
      "signature": "ed25519:def456..."
    },
    {
      "id": "ipfs_v1",
      "version": "2.0.0",
      "required": true,
      "hash": "sha256:789abc...",
      "signature": "ed25519:012def..."
    },
    {
      "id": "private_sync_v1",
      "version": "1.0.0",
      "required": false,
      "hash": "sha256:345678...",
      "signature": "ed25519:901234..."
    }
  ]
}
```

#### 13.2.5 Environment Configuration

**Core Settings:**
```text
CRYFTTEE_MODULE_DIR=./modules
CRYFTTEE_MODULES=bls_tls_signer_v1,ipfs_v1,private_sync_v1
CRYFTTEE_API_TRANSPORT=uds
CRYFTTEE_UDS_PATH=/tmp/cryfttee.sock
```

**Web3Signer Integration:**
```text
CRYFTTEE_WEB3SIGNER_URL=http://localhost:9000
CRYFTTEE_WEB3SIGNER_TIMEOUT=30
```

**Key Derivation:**
```text
CRYFTTEE_KEY_SEED=<hex>
CRYFTTEE_NODE_ID=<node_id>
```

**Security:**
```text
CRYFTTEE_VERIFIED_BINARY_HASH=sha256:<hex>
CRYFTTEE_REQUIRE_ATTESTATION=false
```

