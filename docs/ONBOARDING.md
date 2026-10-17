# 🐉 Vishap Onboarding Guide

Welcome to Vishap! This guide will help you run the project locally and verify that everything works.

## 1. Prerequisites

- **Python:** 3.11 or 3.12
- **Node.js:** 18+ (for Next.js UI)
- **Docker Desktop:** running (for Postgres, Redis, Tempo, Prometheus, Grafana)
- **Git:** installed

## 2. Environment Setup (.env)

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:
```env
# API
VISHAP_API_KEY=dev-key-123

# Postgres
DATABASE_URL=postgresql+asyncpg://vishap:vishap_dev@localhost:5432/vishap

# Redis (Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Clerk (Auth) — get keys from https://dashboard.clerk.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# OTel (Observability)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=vishap
OTEL_SDK_DISABLED=false
OTEL_METRICS_EXPORTER=none
```

## 3. Backend Startup

```bash
# 1. Clone
git clone https://github.com/dvddv9/vishap.git
cd vishap

# 2. Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .\\.venv\\Scripts\\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start databases (Postgres, Redis, Tempo, Prometheus, Grafana)
docker compose up -d

# 5. Run API
python -m src.main
```

**Verify:** `http://localhost:5001/docs` (Swagger UI) and `http://localhost:5001/health` (should return `{"status":"ok"}`).

## 4. UI Startup (Next.js)

```bash
cd ui-next
npm install
cp .env.local.example .env.local
# Fill in Clerk keys in .env.local
npm run dev
```

**Verify:** `http://localhost:3000` — Dashboard with Clerk sign-in.

## 5. Smoke Test (Verify Everything Works)

1. **API:** `curl http://localhost:5001/health` → `{"status":"ok"}`.
2. **UI:** Open `http://localhost:3000`, sign in via Clerk, upload a `.py` file, wait for the report.
3. **Metrics:** Open Grafana (`http://localhost:3001`), check `vishap_http_requests_total` graph.
4. **Traces:** Grafana → Explore → Tempo → query `{ resource.service.name = "vishap" }`.

## 6. Troubleshooting

| Error | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'celery'` | `pip install -r requirements.txt` |
| `ConnectionError: Ollama` | Start Ollama locally (`ollama serve`) or disable LLM provider |
| `Port 5001 already in use` | `netstat -ano | findstr :5001` → `taskkill /PID <PID> /F` |
| `401 Unauthorized` (UI) | Check Clerk keys in `.env.local` |
| `403 Forbidden` (GitHub App) | Check `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET` |

## 7. Documentation & Links

- **Docs:** https://dvddv9.github.io/vishap/
- **Landing:** https://dvddv9.github.io/vishap/landing/
- **GitHub:** https://github.com/dvddv9/vishap
- **Docker Hub:** https://hub.docker.com/r/dvddv9/vishap-analyzer
- **PyPI:** https://pypi.org/project/vishap-analyzer/

## 8. Project Structure

```
vishap/
├── src/                    # Python backend (FastAPI, Celery, pipeline)
├── ui-next/                # Next.js dashboard (React + Clerk)
├── docs-site/              # Docusaurus docs
├── docker/                 # Tempo, Prometheus, Grafana configs
├── docs/                   # Internal docs (HANDOFF, ONBOARDING)
├── tests/                  # 553 tests (pytest)
├── docker-compose.yml      # Full stack
└── pyproject.toml          # Python package config
```

## 9. Support

- **Issues:** https://github.com/dvddv9/vishap/issues
- **Discussions:** https://github.com/dvddv9/vishap/discussions

Happy hacking! 🐉