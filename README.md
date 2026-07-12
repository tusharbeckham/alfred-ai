<div align="center">

# ⚡ Alfred

### Retrieval-augmented conversational AI, engineered from a multi-agent DAG-orchestrated system and shipped to the edge.

[![Live](https://img.shields.io/badge/⚡_Live-Talk_to_Alfred-22c55e?style=for-the-badge&logo=cloudflare&logoColor=white)](https://alfred.tusharentheoria.workers.dev)
![Deployed on Cloudflare Workers](https://img.shields.io/badge/deployed-Cloudflare%20Workers-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)

**Designed and built by Tushar**

[![Alfred in action](assets/demo.gif)](https://alfred.tusharentheoria.workers.dev)

</div>

---

I built Alfred end to end. It's a **retrieval-augmented conversational AI** that runs entirely at the **network edge**, with no origin server in the path. Every message hits a **Cloudflare Worker**, clears an in-worker **abuse guard** (per-IP token-bucket rate limiting, flood detection, automatic bans), gets grounded against a **Vectorize** vector index for **RAG**, threaded with conversation state from **Workers KV**, then **streamed back token by token over Server-Sent Events**. It's the public front end of the **multi-agent, DAG-orchestrated** system I architected.

## 🚀 Live Deployment

Running in production, serverless on **Cloudflare's global edge**: **[alfred.tusharentheoria.workers.dev](https://alfred.tusharentheoria.workers.dev)**. Requests execute and stream from whichever edge location is closest to the user, so there are no cold origins and no infrastructure to babysit.

## 🧰 Tech Stack

![Cloudflare Workers](https://img.shields.io/badge/Cloudflare_Workers-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)
![Workers AI](https://img.shields.io/badge/Workers_AI-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)
![Vectorize](https://img.shields.io/badge/Vectorize-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)
![Workers KV](https://img.shields.io/badge/Workers_KV-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-2563eb?style=for-the-badge)
![Server-Sent Events](https://img.shields.io/badge/SSE_Streaming-111111?style=for-the-badge)
![Multi-Agent DAG](https://img.shields.io/badge/Multi--Agent_DAG-8A2BE2?style=for-the-badge)

## ✨ Capabilities

- **Edge-native streaming.** Token-by-token responses over SSE, straight from the Worker.
- **Vector RAG.** I embed each query, pull the nearest facts from a **Vectorize** index, and ground the model on them so answers stay factual.
- **Stateful memory.** Conversation state persisted in **Workers KV**, keyed to a signed, HttpOnly session cookie.
- **Client-side chat history.** A saved-chats sidebar backed by localStorage; nothing conversational touches a server.
- **Custom Canvas UI.** A hand-tuned starfield renderer in raw Canvas 2D (twinkle, depth parallax, shooting stars), zero UI libraries.
- **In-worker abuse guard.** Token-bucket rate limiting, flood and duplicate detection, auto-ban, and graceful load-shedding under pressure.
- **Hardened by default.** Strict CSP, anti-clickjacking headers, SRI-pinned CDN assets, timing-safe admin-key checks, and role-whitelisted history validation.

## 🏗️ Architecture

```
Visitor  ->  Edge Worker
                |-- Guard     rate-limit, flood, auto-ban, input hygiene
                |-- Context   RAG retrieval (Vectorize) + memory (KV)
                |-- Persona   identity + safety rails
                |-- Model     ->  streamed reply
```

A directed-acyclic request pipeline (guard, context, persona, model). Each stage is isolated and independently testable, and the assistant itself is one node in the broader multi-agent system I built.

## 🛡️ Security

Red-team and stress tested. In simulation the guard absorbed floods of hundreds of thousands of requests per second with the abuser auto-banned, and the prompt surface is hardened against injection and jailbreak attempts.

## 📄 Notice

This repository showcases the architecture and interface of a personal project. The knowledge base, prompts, model configuration, and production secrets that power the live system are private and not included here.

Copyright (c) 2026 Tushar. All rights reserved. Not licensed for copying, redistribution, or derivative works.
