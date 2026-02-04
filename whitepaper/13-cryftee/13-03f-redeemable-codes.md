### 13.3.6 Redeemable Codes Module (`redeemable_codes_v1`)

The Redeemable Codes module implements an on-chain managed gift code system with TEE-secured code storage, enabling secure token distribution, validator onboarding, and promotional campaigns.

**Version:** 1.0.0  
**Category:** Distribution  
**Status:** Core Module (required for full network capability)

**Patent Notice:** This module implements technology described in US Patent Application 20250139608.

---

#### Overview

| Property | Value |
|:---------|:------|
| Module ID | `redeemable_codes_v1` |
| Version | 1.0.0 |
| Required for Validators | No (utility module) |
| Patent | US Patent App 20250139608 |
| Purpose | On-chain gift codes with TEE-secured storage |

**Purpose:**
- Generate and manage redeemable gift codes for token distribution
- Secure code storage using dual smart contract architecture
- Support for multiple content types (tokens, NFTs, experiences, validator registration)
- Blockchain-recorded redemption with immutable audit trail
- Batch operations for large-scale distributions

#### 13.3.6.2 Dual Smart Contract Architecture

The module uses a novel dual-contract design to separate sensitive code storage from public management:

**Public Contract (On-Chain, Visible):**
- Manages non-sensitive information
- Tracks code status (active, frozen, redeemed, revoked)
- Handles content assignments and redemption records
- Provides public query interface

**Private Contract (TEE-Only):**
- Stores encrypted codes (hash + salt)
- Executed only within TEE environment
- Never exposes plaintext codes
- Validates redemption requests

```text
┌---------------------------------------------------------┐
|                    Public Contract                       |
|  ┌-------------┬------------┬-------------------------┐ |
|  | Code Index  |   Status   |   Content Assignment    | |
|  |-------------┼------------┼-------------------------┤ |
|  |    0001     |   ACTIVE   |   100 CRYFT tokens      | |
|  |    0002     |  REDEEMED  |   NFT #4521             | |
|  |    0003     |   FROZEN   |   Validator slot        | |
|  `-------------┴------------┴-------------------------┘ |
`---------------------------------------------------------┘
                          |
                          | Status queries
                          ▼
┌---------------------------------------------------------┐
|              Private Contract (TEE-Only)                 |
|  ┌-------------┬------------------┬--------------------┐|
|  | Code Index  |   Hash(code)     |       Salt         ||
|  |-------------┼------------------┼--------------------┤|
|  |    0001     |   0xabc123...    |   0xdef456...      ||
|  |    0002     |   0x789def...    |   0x123abc...      ||
|  |    0003     |   0x456789...    |   0x789012...      ||
|  `-------------┴------------------┴--------------------┘|
|                                                          |
|  ⚠ Codes stored as hash+salt, NEVER exposed in plaintext|
`---------------------------------------------------------┘
```

#### 13.3.6.3 Code Structure

Redeemable codes follow a structured format for efficient lookup and validation:

```text
Code Format: XXXX-YYYY-YYYY-YYYY

Where:
  XXXX         = Storage Index (locates hash in private contract)
  YYYY-YYYY-YYYY = Redeemable Portion (validated against stored hash)

Example: A1B2-C3D4-E5F6-G7H8
  - Storage Index: A1B2
  - Redeemable: C3D4-E5F6-G7H8
```

**Security Properties:**
- Storage index allows O(1) lookup without revealing code
- Redeemable portion is never stored in plaintext
- Hash + salt prevents rainbow table attacks
- TEE execution prevents extraction of code database

#### 13.3.6.4 Capabilities

**Code Generation:**

| Function | Description |
|:---------|:------------|
| `code_generate` | Generate a single redeemable code with specified content |
| `batch_generate` | Generate multiple codes for bulk distribution |
| `validator_code_generate` | Generate codes specifically for validator registration |

**Code Management:**

| Function | Description |
|:---------|:------------|
| `code_status` | Query status of a code (without revealing code value) |
| `code_freeze` | Temporarily prevent redemption |
| `code_unfreeze` | Re-enable frozen code |
| `code_revoke` | Permanently invalidate a code |
| `code_transfer` | Transfer management rights to another address |

**Redemption:**

| Function | Description |
|:---------|:------------|
| `code_redeem` | Redeem a code and receive assigned content |
| `validator_code_redeem` | Validator-assisted redemption for cross-region codes |
| `batch_redeem` | Redeem multiple codes in a single transaction |

#### 13.3.6.5 Content Types

The module supports multiple content types for flexible distribution:

| Content Type | Description | Example Use Case |
|:-------------|:------------|:-----------------|
| **Tokens** | CRYFT or other fungible tokens | Promotional giveaways, rewards |
| **NFTs** | Non-fungible tokens | Digital collectibles, access passes |
| **Experiences** | Off-chain service entitlements | Premium features, API credits |
| **Validator Registration** | Validator slot + initial stake | Onboarding new validators |
| **Custom** | Application-defined content | Game items, subscription credits |

**Content Assignment:**

```text
ContentAssignment {
  code_index:    uint32      // storage index
  content_type:  enum        // TOKENS, NFT, EXPERIENCE, VALIDATOR, CUSTOM
  content_id:    bytes32     // token address, NFT ID, or custom identifier
  amount:        uint256     // quantity (for fungible content)
  metadata:      bytes       // additional content-specific data
  expiry:        uint64      // optional expiration timestamp
}
```

#### 13.3.6.6 Redemption Flow

**Standard Redemption:**

```text
1. User submits: code_redeem(code="A1B2-C3D4-E5F6-G7H8", recipient=0x...)

2. Module extracts storage index: A1B2

3. TEE queries private contract:
   - Retrieves hash and salt for index A1B2
   - Computes: expected_hash = hash(C3D4-E5F6-G7H8 || salt)
   - Verifies: expected_hash == stored_hash

4. If valid:
   - Public contract marks code as REDEEMED
   - Content is transferred to recipient
   - Redemption recorded on-chain with timestamp

5. Returns: RedemptionReceipt {
     code_index: A1B2,
     recipient: 0x...,
     content: {...},
     tx_hash: 0x...,
     timestamp: 1700000000
   }
```

**Validator-Assisted Redemption:**

For cross-region codes, validators facilitate redemption:

```text
1. User presents code to local validator
2. Validator submits: validator_code_redeem(code, user, region_proof)
3. Cross-region verification via checkpoint
4. Content delivered in user's home region
5. Validator receives small facilitation fee
```

#### 13.3.6.7 Batch Operations

For large-scale distributions (airdrops, promotions):

```text
BatchGeneration {
  count:         uint32      // number of codes to generate
  content_type:  enum        // content type for all codes
  content_id:    bytes32     // shared content identifier
  amount_each:   uint256     // amount per code
  prefix:        string      // optional code prefix for tracking
  expiry:        uint64      // shared expiration
}

Result: BatchResult {
  codes: string[]           // generated codes (returned once, not stored)
  indices: uint32[]         // storage indices for management
  total_value: uint256      // total content allocated
}
```

**Security Note:** Generated codes are returned exactly once during batch generation. The module does not retain plaintext codes after generation.

#### 13.3.6.8 Audit Trail

All code operations are recorded on-chain for transparency:

```text
CodeEvent {
  event_type:   enum        // GENERATED, REDEEMED, FROZEN, REVOKED, TRANSFERRED
  code_index:   uint32      // storage index (never reveals code)
  actor:        address     // address that triggered event
  timestamp:    uint64      // block timestamp
  metadata:     bytes       // event-specific data
}
```

**Query Functions:**

| Function | Description |
|:---------|:------------|
| `audit_history` | Get all events for a code index |
| `redemption_stats` | Aggregate statistics for a batch or campaign |
| `active_codes` | Count of unredeemed codes by content type |

#### 13.3.6.9 Security Considerations

**Threat Mitigations:**

| Threat | Mitigation |
|:-------|:-----------|
| Code extraction | Codes stored as hash+salt in TEE-only contract |
| Brute force | Rate limiting + salt prevents offline attacks |
| Replay attacks | One-time redemption enforced on-chain |
| Code enumeration | Storage indices are not sequential |
| Insider theft | Dual-contract separation limits exposure |

**Operational Security:**

- Generated codes should be distributed through secure channels
- Batch codes should have expiration dates
- Frozen codes should be investigated before unfreezing
- Revoked codes cannot be recovered

#### 13.3.6.10 Configuration

```text
CRYFTTEE_CODES_ENABLED=true
CRYFTTEE_CODES_MAX_BATCH_SIZE=10000
CRYFTTEE_CODES_DEFAULT_EXPIRY=31536000  # 1 year in seconds
CRYFTTEE_CODES_RATE_LIMIT=100           # redemptions per minute per IP
```

#### 13.3.6.11 Use Cases

**Promotional Token Distribution:**
- Generate codes for marketing campaigns
- Track redemption rates by campaign prefix
- Set expiration for limited-time offers

**Validator Onboarding:**
- Issue validator registration codes with initial stake
- Enable sponsored validator slots for partners
- Track validator origin for analytics

**Cross-Region Gifts:**
- Users gift tokens to recipients in other regions
- Validator-assisted redemption handles cross-region transfer
- Gift sender pays cross-region fees upfront

**NFT Claim Codes:**
- Physical merchandise includes redemption code
- Code unlocks digital NFT companion
- One-time redemption prevents duplication

