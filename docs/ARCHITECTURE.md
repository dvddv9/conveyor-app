# Architecture — Conveyor V5.7.1

**Схема pipeline, где LLM, где audit, где хранилище.**

---

## 1. High-level

```
┌──────────────────┐   ┌──────────────────┐
│  Streamlit UI    │   │   FastAPI        │
│   :8501          │──>│   :5001          │
└──────────────────┘   └────────┬─────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │  Pipeline (6 stages) │
                    │  00 → 01 → 02 → 03   │
                    │       → 04 → 05      │
                    └────────┬─────────────┘
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │ DeepSeek  │   │  Ollama   │   │  Audit    │
      │ (cloud)   │   │ (local)   │   │ SHA-256 + │
      └───────────┘   └───────────┘   │ PII +     │
                                       │ compliance│
                                       └───────────┘
```

---

## 2. Pipeline — 6 stages

```
material ──┐
           │
           ▼
    ┌───────────────┐
    │ Redaction     │  src/tools/redact.py
    │ (PII/secrets) │  → material_redacted
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Stage 0       │  conveyor/00_orchestrator.md
    │ Orchestrator  │  → route, level, task_type
    │               │  → flags (EMERGENCY_INTERRUPT)
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Stage 1       │  conveyor/01_scanner.md
    │ Scanner       │  → 4 layers, stack
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Stage 2       │  conveyor/02_analyst.md
    │ Analyst       │  → risk nodes, STRIDE
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Stage 3       │  conveyor/03_researcher.md
    │ Researcher    │  → industry parallels
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Stage 4       │  conveyor/04_synthesizer.md
    │ Synthesizer   │  → options, refactoring, force_emergency
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Stage 5       │  conveyor/05_transmitter.md
    │ Transmitter   │  → Markdown
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Audit         │  src/pipeline/orchestrator.py
    │ + Completeness│  → SHA-256, PII, compliance
    └───────┬───────┘
            │
            ▼
        final report
```

---

## 3. Где LLM, где pipeline

| Компонент | LLM | Pipeline (deterministic) |
|-----------|-----|--------------------------|
| Stage 0 route | Да | — |
| Stage 1 scanner | Да | — |
| Stage 2 analyst | Да | — |
| Stage 3 researcher | Да | — |
| Stage 4 synthesizer | Да | — |
| Stage 5 transmitter | Да | — |
| **Redaction** | — | **Да** (15 regex) |
| **Audit (hash, PII, compliance)** | — | **Да** |
| **Completeness (loss_pct)** | — | **Да** |
| **EMERGENCY gate** | — | **Да** (CRITICAL_RISK_PATTERNS) |

**LLM отвечает за анализ. Pipeline — за audit, redaction, gates.**

---

## 4. Хранилище

| Что | Где | Формат |
|-----|-----|--------|
| Result | data/result_sess-*.json | JSON |
| Audit | data/audit_sess-*.json | JSON |
| History | data/history.json | JSON |
| Mode | data/mode.json | JSON |
| Case studies | docs/case-studies/**/*.md | Markdown |

**data/** — в .gitignore.** Не коммитится.

---

## 5. Audit trail

Каждый анализ создаёт `data/audit_sess-*.json`:

```json
{
  "audit_id": "audit-2026-10-12-3077e9",
  "session_id": "sess-2026-10-12-042806",
  "timestamp": "2026-10-12T04:28:06.157411+00:00",
  "material_hash": "sha256:...64hex",
  "material_hash_full": "sha256:...64hex",
  "truncated": false,
  "original_size": 11317,
  "critique_verdict": "REQUIRES_REVIEW",
  "risk_verdict": "SAFE",
  "pii_detected": false,
  "compliance_flags": ["EU AI Act"],
  "redaction_applied": true,
  "redaction_map": {"email": 2}
}
```

---

## 6. API endpoints

| Method | URL | Auth | Rate limit |
|--------|-----|------|-----------|
| GET | / | No | No |
| GET | /health | No | No |
| POST | /analyze | X-API-Key | 10/min |
| POST | /analyze/batch | X-API-Key | 10/min |
| GET | /history | No | 30/min |
| POST | /history/clear | X-API-Key | 30/min |
| GET | /mode | No | 30/min |
| POST | /mode | X-API-Key | 30/min |

---

## 7. Deployment modes

| Mode | LLM | Приватность | Скорость |
|------|-----|-------------|----------|
| auto (default) | DeepSeek cloud + Ollama fallback | Cloud | 40-90 сек |
| cloud | DeepSeek only | Cloud | 40-90 сек |
| local | Ollama only | Local | 20-40 мин |

**local** — для sensitive data.

---

## 8. Зависимости

**Runtime:**
- Python 3.12
- fastapi, uvicorn, pydantic
- streamlit
- openai (для DeepSeek)
- ollama
- tree-sitter (парсинг)
- radon, black
- tenacity (retry)

**Dev:**
- pytest, pytest-asyncio
- httpx

---

*Last updated: 2026-10-12 | Conveyor V5.7.1*