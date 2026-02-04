### 13.3.3 LLM Chat Module (`llm_chat_v1`)

The LLM module provides a self-contained interactive AI assistant for runtime and module interaction, with all conversation state managed in-module.

**Version:** 2.0.0  
**Category:** Operator Interface  
**Status:** Core Module (required for full network capability)

---

#### Purpose

- Answer operator questions about Cryftee configuration
- Assist with troubleshooting and diagnostics
- Provide documentation and guidance
- Multi-provider support for flexibility

---

#### Relationship to AIM

> **Note on AIM vs LLM Chat:** This module provides direct LLM chat within the Cryftee operator interface. It is **distinct from the Agent Identity & Memory (AIM) specification** (Section 13.7).
>
> - **`llm_chat_v1`** is a runtime module for operator assistance within Cryftee
> - **AIM** defines on-chain infrastructure for tokenized autonomous agent identities
>
> The `llm_chat_v1` module MAY utilize LLM providers that are themselves AIM-registered agents, enabling operators to interact with AIM-managed autonomous agents through this interface.

---

#### Architecture

- Self-contained chat interface managing all conversation state in-module
- Host calls used ONLY for network I/O to external APIs
- Token counting and context management to stay within model limits
- Response streaming assembly for real-time chat

---

#### Session Management

| Limit | Value |
|:------|:------|
| Max concurrent sessions | 50 |
| Max context window | 128k tokens |
| Session timeout | Configurable per provider |

---

#### Supported Providers

| Provider | Models | Notes |
|:---------|:-------|:------|
| **OpenAI** | GPT-4, GPT-3.5-turbo | Default provider |
| **Anthropic** | Claude-3-opus, Claude-3-sonnet | Extended context support |
| **Local** | Llama, Mistral | Self-hosted, no external API calls |
| **AIM Agent** | Any AIM-registered agent | Tokenized agent interaction |

---

#### Capabilities

| Function | Description |
|:---------|:------------|
| `llm_chat` | Send a message and receive a complete response |
| `llm_stream` | Send a message and receive a streaming response |

---

#### Configuration

```text
CRYFTTEE_LLM_PROVIDER=openai|anthropic|local|aim
CRYFTTEE_LLM_API_KEY=<key>
CRYFTTEE_LLM_MODEL=gpt-4
CRYFTTEE_LLM_MAX_SESSIONS=50
CRYFTTEE_LLM_CONTEXT_WINDOW=128000
```

For AIM-based providers:
```text
CRYFTTEE_LLM_PROVIDER=aim
CRYFTTEE_LLM_AGENT_ID=<agentId>
```

---

#### Security Note

LLM outputs are NOT consensus-critical. The module provides operator assistance only; no LLM responses affect chain state or validator behavior.
