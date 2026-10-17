# Vishap

[![CI](https://github.com/dvddv9/vishap/actions/workflows/ci.yml/badge.svg)](https://github.com/dvddv9/vishap/actions/workflows/ci.yml)
[![Docs](https://github.com/dvddv9/vishap/actions/workflows/docs.yml/badge.svg)](https://dvddv9.github.io/vishap/)
[![PyPI version](https://badge.fury.io/py/vishap.svg)](https://badge.fury.io/py/vishap)
[![Docker Pulls](https://img.shields.io/docker/pulls/dvddv9/vishap-analyzer.svg)](https://hub.docker.com/r/dvddv9/vishap-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🔬 6-stage LLM pipeline for analyzing engineering materials (code, spec, logs).

**Vishap** takes a file as input → returns a structured Markdown report with risks, STRIDE threat model, refactoring options and **audit trail** with PII detection and compliance flags.

## 🌐 Links

- **Documentation:** [https://dvddv9.github.io/vishap/](https://dvddv9.github.io/vishap/)
- **Landing Page:** [https://dvddv9.github.io/vishap/landing/](https://dvddv9.github.io/vishap/landing/)
- **GitHub App:** Auto-analyze PR diffs and comment on findings.

## 🚀 What's new in v6.1.0 (SaaS Release)

We have transformed Vishap from a local tool into a full-fledged SaaS platform:

- **Queue (Celery + Redis):** Production-ready async processing (`/analyze/async`).
- **GitHub App:** Webhooks + PR auto-analyze with inline comments.
- **Auth (Clerk):** Multi-tenant JWT authentication (`/analyze/secure`).
- **Billing (Stripe):** Subscriptions + usage-based billing (Checkout API).
- **Docs (Docusaurus):** Full documentation site on GitHub Pages.
- **Landing (HTML/Tailwind):** Static marketing page.
- **Observability (OTel):** Distributed tracing (Tempo) + metrics (Prometheus) + Grafana dashboards.
- **PostgreSQL:** JobStore abstraction for persistent job tracking.

## 🛠 Features

- **6-stage pipeline:** Ingestion → Taint Analysis → Dataflow → Risk Assessment → Verdict → Report.
- **Multi-language:** Python, Java, C (AST + taint patterns).
- **Async API:** FastAPI with Celery workers.
- **Security:** Fernet encryption for secrets, HMAC for webhooks.
- **Observability:** Structlog (JSON), Prometheus `/metrics`, OpenTelemetry traces.
- **CI/CD:** GitHub Actions (tests, lint, docs deploy, dogfood).

## 📦 Quick Start

### Docker (recommended)

git clone https://github.com/dvddv9/vishap.git
cd vishap
cp .env.example .env
docker compose up -d

- UI: `http://localhost:8501`
- API: `http://localhost:5001/docs`
- Grafana: `http://localhost:3001`

## 🧪 Testing

python -m pytest tests/ --ignore=tests/test_e2e.py -q
# 553 passed

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
