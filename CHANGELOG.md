# Changelog

All notable changes to Conveyor. Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [5.7.1] - 2026-10-12

### Fixed (review + dogfood P0)

- **material_hash collisions** — context (filename + session_id) added to hash input (`ce3953d`)
- **PII redaction before LLM** — 15 regex patterns, placeholders (`<EMAIL_REDACTED>`) before cloud send (`7b23c24`)
- **LLM HTTP timeout** — 60s + tenacity retry with exponential backoff (`9063927`)
- **API auth + rate limit** — X-API-Key + 10/min limiter + CORS + 127.0.0.1 fallback (`fbfb48f`)
- **EMERGENCY-downgrade gate** — CRITICAL_RISK_PATTERNS (RCE, SQLi, path traversal, XXE, SSTI, LDAPi) (`48dddd0`)
- **[AUDIT_TRAIL] dedup** — strip_llm_audit_blocks from LLM output (`2000501`)
- **material_hash_full** — SHA-256 of original (before truncation) (`8ca7f4e`)
- **material_complete** — deterministic `not truncated` (`9459a53`)
- **risk_verdict** — separated from critique_verdict (`e500c80`)
- **emergency path UnboundLocalError** — fixed (`e500c80`)
- **748 material_hash places** — all 64-hex or LEGACY (`71af15f`, `0e68b05`, `08ce35d`)

### Added

- **PROOF.md** — 13 evidence sections (`e6d3829`, `0e68b05`)
- **FINDINGS.md** — dogfood findings, 5 P0 bugs (`a5b444f`)
- **8 dogfood reports** — code, config, spec, data (`27aabb4`)
- **STONESOUP CWE-129B** — SARD case study (`a48b228`)
- **deployment/** — Dockerfile, docker-compose, systemd, .env.example (`003f9a8`)
- **SECURITY.md** — threat model + controls + honest boundaries (`7929f1e`)
- **docs/LIMITATIONS.md** — 10 honest boundaries (`ce7cf19`)
- **docs/FAQ.md** — 10 common questions (`acba0af`)
- **src/api/auth.py** — X-API-Key dependency
- **src/api/rate_limit.py** — in-memory sliding window
- **src/tools/redact.py** — pre-LLM redaction
- **src/tools/patterns.py** — PII_PATTERNS + CRITICAL_RISK_PATTERNS

### Changed

- `compute_hash` — added `context` param
- `run_audit` — added `force_emergency`, `context`, `redaction_map` params
- `AnalyzeResponse` — added `audit`, `completeness`, `material_hash_full`, `truncated`, `original_size`
- `run_pipeline` — redaction before Stage 0
- `uvicorn.run` — dynamic host (127.0.0.1 if no API key)

### Security

- API key from `CONVEYOR_API_KEY` env var
- CORS restricted to `localhost:8501`
- Rate limit 10/min for /analyze
- PII/secrets redacted before cloud LLM

---

## [5.7.0] - 2026-10-08

### Added

- **6-stage LLM pipeline** — Orchestrator, Scanner, Analyst, Researcher, Synthesizer, Transmitter
- **Multi-material** — code (.py, .go, .js, .ts, .java, .rs), spec (.md), logs (.txt), config (.yaml, .json), data (.json)
- **Audit trail** — SHA-256 material_hash, pii_detected, compliance_flags, critique_verdict
- **EMERGENCY interrupt** — Stage 0 stops pipeline on critical risk
- **FastAPI API** — /analyze, /analyze/batch, /history, /mode, /health
- **Streamlit UI** — file upload, history, download markdown
- **DeepSeek cloud** + **Ollama local** fallback
- **41 tests** — PII, compliance, JSON, pipeline mock, e2e
- **39 case studies** — FastAPI, Django, Flask, Express, Go stdlib, Log4Shell, OpenSSL, Redis, K8s, PostgreSQL, Juice Shop, DVGA, RailsGoat, DVWA, TerraGoat
- **CI** — GitHub Actions, py3.11 + py3.12

### Known limitations

- Truncation at 12 000 chars
- LLM-based (may produce false positives)
- No SAST/SCA integration
- No SARIF output
- No formal threat model (added in 5.7.1)

---

[5.7.1]: https://github.com/dvddv9/vishap/compare/v5.7.0...v5.7.1
[5.7.0]: https://github.com/dvddv9/vishap/releases/tag/v5.7.0

*Conveyor V5.7.1 - production-ready.*