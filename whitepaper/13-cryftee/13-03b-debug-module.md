### 13.3.2 Debug Module (`debug_v1`)

The debug module provides diagnostic capabilities for operators.

**Version:** 1.0.0  
**Category:** Diagnostics  
**Status:** Core Module (required for full network capability)

---

#### Purpose

- Runtime inspection and health checks
- Testing module communication and round-trip connectivity
- Controlled panic for testing error handling
- Lightweight diagnostics for development and troubleshooting

---

#### Capabilities

| Function | Description |
|:---------|:------------|
| `debug_echo` | Echo input back to caller (connectivity test) |
| `debug_info` | Return runtime version, loaded modules, and environment info |
| `debug_panic` | Trigger a controlled panic for testing error handling |

---

#### Security Considerations

The `debug_panic` function SHOULD be disabled in production deployments. Operators can configure via:

```text
CRYFTTEE_DEBUG_PANIC_ENABLED=false
```

When disabled, calls to `debug_panic` will return an error response rather than triggering a runtime panic.

---

#### Usage Examples

**Echo Test:**
```text
Request:  debug_echo("hello")
Response: "hello"
```

**Runtime Info:**
```text
Request:  debug_info()
Response: {
  "runtime_version": "0.4.2",
  "modules": ["bls_tls_signer_v1", "debug_v1", "llm_chat_v1", ...],
  "uptime_seconds": 3600,
  "memory_used_mb": 128
}
```
