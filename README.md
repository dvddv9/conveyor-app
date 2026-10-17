Here is the detailed project description in English.

---

# 🐉 Vishap v6.3.0 — Full Project Description

**Vishap** is a SaaS platform for automated security analysis of engineering materials and code. It takes a file as input (Python, Java, C, specs, logs) and returns a structured Markdown report containing:
- **Vulnerabilities** (SQLi, RCE, path traversal, buffer overflow).
- **STRIDE threat model**.
- **Refactoring options**.
- **Audit trail** (PII detection, compliance flags).

The project evolved from a local CLI tool into a **full-fledged SaaS product** with a web interface, billing, authentication, and observability.

---

##  Architecture 

```
┌─────────────────────────────────────────────────────────────┐
│  Client Layer                                                │
│  ├─ Next.js Dashboard (React + Tailwind + Clerk)            │
│  ├─ Streamlit UI (legacy, for local development)            │
│  └─ CLI (vishap analyze file.py)                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  API Layer (FastAPI)                                         │
│  ├─ /analyze (sync)                                          │
│  ├─ /analyze/async (Celery)                                  │
│  ├─ /status/{job_id}, /report/{job_id}                       │
│  ├─ /analyze/secure (Clerk JWT)                              │
│  ├─ /webhook/github (HMAC)                                   │
│  ├─ /webhook/stripe (HMAC)                                   │
│  └─ /metrics (Prometheus)                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Queue Layer                                                 │
│  ├─ Celery workers (async jobs)                             │
│  ├─ Redis (broker + result backend)                          │
│  └─ Retry + dead-letter                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Layer (6 stages)                                  │
│  1. Ingestion → 2. Taint (AST) → 3. Dataflow →             │
│  4. Risk → 5. Verdict → 6. Report                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Storage Layer                                               │
│  ├─ PostgreSQL (jobs, PostgresJobStore)                     │
│  └─ Fernet (secret encryption)                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Observability Layer                                         │
│  ├─ Structlog (JSON logs)                                    │
│  ├─ Prometheus (metrics)                                     │
│  ├─ OpenTelemetry (traces)                                   │
│  ├─ Tempo (trace storage)                                    │
│  └─ Grafana (dashboards)                                     │
└─────────────────────────────────────────────────────────────┘
```

---

##  Key Features 

### **Core Pipeline (6 Stages)**
1. **Ingestion** — file parsing (Python AST, Java/C regex).
2. **Taint Analysis** — finding sources and sinks.
3. **Dataflow** — tracking data flow (Python AST, Java/C regex).
4. **Risk Assessment** — risk scoring (risk_nodes, severity).
5. **Verdict** — final verdict (compute_risk_verdict).
6. **Report** — Markdown generation (SARIF, SBOM).

### **Backend (FastAPI + Celery)**
- Sync + async API (`/analyze`, `/analyze/async`).
- Job-based queue (Celery + Redis).
- Retry policy (3 attempts, exponential backoff).
- Dead-letter (via Redis).
- PostgresJobStore (persistent jobs).

### **Auth (Clerk)**
- JWT verification (RS256, JWKS cache).
- `current_user` middleware (dependency).
- `/analyze/secure` (protected endpoint).
- Multi-tenant (tenant_id in Postgres).

### **Billing (Stripe)**
- Checkout Session (subscription mode).
- Webhook (`customer.subscription.updated`).
- Usage-based billing (Stripe Meters API).
- `get_customer`, `record_usage`.

### **GitHub App**
- Webhook handler (HMAC SHA256).
- JWT (RS256, App ID + private key).
- Installation token.
- PR auto-analyze + inline comment.
- SARIF upload (Code Scanning).

### **UI Next.js (Block 13)**
- **Stack:** Next.js 16, React 19, TypeScript, Tailwind 4, Clerk 7, SWR.
- **Pages:**
  - `/` — Dashboard (jobs list).
  - `/analyze` — form (file upload + textarea + polling).
  - `/report/[id]` — Markdown render (react-markdown + remark-gfm).
- **Components:** Navbar, JobCard, UploadForm.
- **Auth:** Clerk middleware (`src/proxy.ts`, Next 16 convention).
- **Theme:** dark terminal (Tailwind + custom CSS).

### **Observability (Block 11)**
- **OpenTelemetry:** fail-open wrapper (`src/observability/tracing.py`).
- **Spans:** HTTP, Celery, 6 pipeline stages.
- **Tempo:** trace storage (`:3200`, `:4318`, `:4317`).
- **Prometheus:** metrics (`/metrics`, `:9090`).
- **Grafana:** dashboards (`:3001`).
- **Structlog:** JSON logs.

### **Docs + Landing**
- **Docusaurus:** [dvddv9.github.io/vishap](https://dvddv9.github.io/vishap/) (5 pages: getting-started, api-reference, cli, architecture, case-studies).
- **Landing:** [dvddv9.github.io/vishap/landing](https://dvddv9.github.io/vishap/landing/) (HTML + Tailwind, hero + features + pricing).

---

## Distribution

| Platform | Link | Install |
|---|---|---|
| **PyPI** | `vishap-analyzer==6.3.0` | `pip install vishap-analyzer==6.3.0` |
| **Docker Hub** | `dvddv9/vishap-analyzer:6.3.0` | `docker pull dvddv9/vishap-analyzer:6.3.0` |
| **GitHub** | `dvddv9/vishap` | `git clone https://github.com/dvddv9/vishap.git` |
| **Docs** | `dvddv9.github.io/vishap/` | Online |
| **Landing** | `dvddv9.github.io/vishap/landing/` | Online |

---

##  Quality & CI/CD

### **Tests**
- **553 tests** (pytest) — all green.
- Coverage: API, pipeline, auth, billing, GitHub App, observability.
- Integration tests (Postgres).

### **CI/CD (GitHub Actions)**
- **`ci.yml`:** pytest + ruff + ast.parse (Python 3.11, 3.12, Postgres service).
- **`docs.yml`:** Docusaurus build + GitHub Pages deploy.
- **`publish.yml`:** build + twine check + PyPI Trusted Publishing (OIDC).
- **`vishap.yml`:** dogfood (non-blocking, Ollama unavailable in CI).

### **Releases**
- v6.2.0 (PyPI) — PyPI publish workflow.
- v6.2.1 (PyPI) — version sync.
- **v6.3.0** (PyPI + Docker Hub) — UI Next.js.

---

##  SaaS Roadmap 

| # | Item | Status |
|---|---|---|
| 1 | FastAPI | ✅ |
| 2 | Queue (Celery) | ✅ |
| 3 | PostgreSQL | ✅ |
| 4 | GitHub App | ✅ |
| 5 | UI Next.js | ✅ |
| 6 | Auth (Clerk) | ✅ |
| 7 | Billing (Stripe) | ✅ |
| 8 | Observability (OTel + Grafana) | ✅ |
| 9 | Docs (Docusaurus) | ✅ |
| 10 | Landing (HTML) | ✅ |

---

##  Target Audience

- **Developers** — quick security audit before commit.
- **DevOps** — CI/CD integration (GitHub App, SARIF).
- **Enterprise** — SSO (Clerk), multi-tenant, audit trail, compliance flags.

---

##  License

MIT License.

---

