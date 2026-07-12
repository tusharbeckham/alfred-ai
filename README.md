<div align="center">

# 🧠 Alfred

**A hardened, memory-augmented AI assistant — deployed serverless on the edge.**
The public interface of a multi-agent, DAG-orchestrated AI system.

![Cloudflare Workers](https://img.shields.io/badge/Cloudflare-Workers-F38020?style=flat-square&logo=cloudflare&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-2563eb?style=flat-square)
![Status](https://img.shields.io/badge/status-live-brightgreen?style=flat-square)

</div>

---

Alfred is a production-grade conversational AI assistant that runs entirely on **Cloudflare's edge** — no servers to manage, global low latency, and a free-tier-friendly footprint. It pairs a streaming chat experience with **persistent memory**, a **retrieval-augmented knowledge base**, and a **multi-layer abuse-resistance guard** that's been red-team + stress tested.

It is the deployed front end of a larger **multi-agent orchestration system**, organized as a directed-acyclic graph (DAG) of specialized roles that plan, execute, and review work.

## ✨ Features

- **⚡ Edge-native + streaming** — served from Cloudflare Workers; token-by-token streaming for instant replies.
- **🧠 "Megamind" — memory + knowledge**
  - **Conversation memory** — per-visitor history persisted in Cloudflare **KV** and restored across sessions.
  - **Knowledge base (RAG)** — facts embedded into Cloudflare **Vectorize**; the assistant retrieves the most relevant ones and grounds its answers in them.
- **🛡️ Abuse-resistant by design** — per-sender token-bucket rate limiting, flood/duplicate detection, and automatic temporary bans, all in-worker. Stress-tested to hundreds of thousands of requests/second with the spammer auto-banned.
- **🔌 LLM-agnostic** — plug in any OpenAI-compatible model, or use Cloudflare Workers AI as a zero-key fallback.
- **🎨 Premium UI** — a polished, responsive chat interface with light/dark themes, sanitized markdown rendering, and no theme flash on load.
- **🔒 Secure by default** — secrets live only as encrypted platform secrets (never in code), strict input validation, timing-safe admin auth, CSP + anti-clickjacking headers, and SRI-pinned front-end dependencies.

## 🏗️ Architecture

```
Visitor ─▶ Edge Worker
              ├─ Guard      rate-limit · flood · auto-ban · input hygiene
              ├─ Context    RAG retrieval (Vectorize) + conversation memory (KV)
              ├─ Persona    identity + safety rails
              └─ Model      OpenAI-compatible / Workers AI ──▶ streamed reply
```

Every request flows through a small DAG of stages — guard → context → persona → model — with each stage independently testable. Full write-up in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 🧰 Tech

Cloudflare **Workers** · **Workers AI** · **Vectorize** (vector DB) · **Workers KV** · JavaScript · Python (security tooling)

## 📁 Layout

| Path | Purpose |
|------|---------|
| `worker/worker.js` | The edge assistant — chat UI + API + guard + memory + RAG |
| `worker/wrangler.toml` | Deployment config + resource bindings |
| `security/` | Standalone abuse guard, flood stress test, and prompt-injection red-team suite |
| `ARCHITECTURE.md` | System design and request lifecycle |

## 🚀 Deploy (overview)

1. Create a Cloudflare Worker and paste `worker/worker.js`.
2. Add bindings: **Workers AI** (`AI`), **KV** (`MEMORY`), **Vectorize** (`VEC`).
3. *(Optional)* set an `LLM_API_KEY` (+ `LLM_BASE_URL`) for a hosted model, and `ADMIN_KEY` to protect the knowledge-ingestion endpoint.
4. Deploy — you get a public URL. That's it.

## 🔐 Security suite

`security/` ships three standalone tools:
- `guard.py` — the rate-limit / flood / auto-ban engine (with unit self-tests).
- `stress_test.py` — floods the guard to prove it never crashes and bans abusers.
- `redteam.py` — checks the assistant's resistance to prompt-injection and jailbreak attempts.

```bash
python security/guard.py        # self-tests
python security/stress_test.py  # flood simulation
python security/redteam.py      # injection judge tests
```

## 📜 License

[MIT](LICENSE).
