# Architecture

Alfred is the deployed public interface of a multi-agent, DAG-orchestrated AI system. This document
covers the deployed edge assistant; the broader orchestration layer (planning → execution → review
pipelines) lives in a separate private workspace.

## Design goals
- **Serverless + global** — no servers, low latency everywhere, free-tier friendly.
- **Grounded + persistent** — the assistant remembers conversations and recalls a curated knowledge base.
- **Abuse-proof** — a public endpoint must survive spam and manipulation without falling over.
- **Vendor-neutral** — the language model is a pluggable dependency, not a lock-in.

## Request lifecycle (a small DAG)

```
                 ┌──────────────┐
   Visitor ─────▶│  Edge Worker │
                 └──────┬───────┘
                        ▼
        ┌───────────────────────────────┐
        │ 1. GUARD                       │  token-bucket rate limit, flood/duplicate
        │    (reject/allow)              │  detection, auto-ban, input hygiene
        └───────────────┬───────────────┘
                        ▼ (allowed)
        ┌───────────────────────────────┐
        │ 2. CONTEXT                     │  • RAG: embed query → vector search (Vectorize)
        │    (retrieve)                  │  • Memory: load session history (KV)
        └───────────────┬───────────────┘
                        ▼
        ┌───────────────────────────────┐
        │ 3. PERSONA                     │  system identity + safety rails +
        │    (compose prompt)            │  retrieved knowledge (as reference, not instructions)
        └───────────────┬───────────────┘
                        ▼
        ┌───────────────────────────────┐
        │ 4. MODEL                       │  OpenAI-compatible LLM, or Workers AI fallback
        │    (generate, streaming)       │  → server-sent events streamed to the browser
        └───────────────────────────────┘
```

Each stage is independent and separately testable — a directed-acyclic pipeline.

## The "megamind" (memory + knowledge)
- **Conversation memory (KV).** Each visitor gets a strict, server-issued session id (cookie). Their
  recent turns are stored in a key-value namespace and restored on return, so context survives reloads.
- **Knowledge base (RAG).** Facts are embedded into a vector index. On each question the query is
  embedded, the nearest facts are retrieved, and they're injected into the prompt as **reference
  material** — explicitly framed as data, never as instructions, to blunt data-poisoning.

## Abuse resistance
- **Rate limiting** — per-sender token bucket (steady rate + small burst).
- **Flood detection** — repeated identical messages within a window are throttled.
- **Auto-ban** — senders that trip the limits repeatedly are temporarily banned (fast-rejected).
- **Input hygiene** — control-character stripping, length caps, request-size limits.
- **Load shedding** — bounded in-flight work; graceful holding responses instead of crashing.

The guard is also shipped as a standalone module with a flood stress test and a prompt-injection
red-team suite (`security/`).

## Security posture
- Secrets are platform-managed (encrypted), never committed to source.
- Client-supplied history is validated (role-whitelisted, length-capped) to prevent injection.
- Admin endpoints use constant-time key comparison.
- The browser app renders model output through a sanitizer, sets a strict CSP + anti-clickjacking
  headers, and pins its dependencies with subresource integrity.
