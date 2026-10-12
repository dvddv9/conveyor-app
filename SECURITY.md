# Security Policy — Conveyor V5.7

**Conveyor is a security-analysis tool. Its own security is documented here.**

---

## Threat Model

### What we protect

| Asset | Boundary | Threat |
|-------|----------|--------|
| Material (code, spec, logs) | User -> API -> LLM | May contain PII, secrets, prompt injection |
| API (:5001) | External -> FastAPI | Unauthenticated access, DoS |
| LLM (DeepSeek cloud) | Conveyor -> DeepSeek | Data exfiltration |
| API key (DEEPSEEK_API_KEY) | .env -> process | Leak via git, logs |
| Audit trail (data/*.json) | Pipeline -> disk | Hash collisions, PII in logs |

### Trust boundaries

- TB-1: User -> API (:5001) — protected by X-API-Key
- TB-2: API -> LLM (DeepSeek) — protected by PII redaction
- TB-3: Material -> Pipeline — partial (SUBST_MAX_ATTEMPTS=2)
- TB-4: Pipeline -> disk — 64-hex SHA-256 audit trail

---

## What is implemented

### 1. PII/secrets redaction BEFORE LLM

**Location:** `src/tools/redact.py`

15 regex patterns replace PII/secrets with placeholders before sending to LLM:

```
email           -> <EMAIL_REDACTED>
phone_ru        -> <PHONE_REDACTED>
passport_ru     -> <PASSPORT_REDACTED>
snils           -> <SNILS_REDACTED>
iban            -> <IBAN_REDACTED>
aws_access_key  -> <AWS_ACCESS_KEY_REDACTED>
stripe_live_key -> <STRIPE_LIVE_KEY_REDACTED>
github_token    -> <GITHUB_TOKEN_REDACTED>
```

Audit trail keeps redaction_applied + redaction_map for compliance.

### 2. API authentication

**Location:** `src/api/auth.py`

- If CONVEYOR_API_KEY set -> X-API-Key header required.
- If empty -> API binds to 127.0.0.1 only.

### 3. API rate limiting

**Location:** `src/api/rate_limit.py`

- /analyze: 10 req/min per IP
- /history, /mode: 30 req/min per IP

### 4. CORS restriction

**Location:** `src/main.py`

CORS allows only localhost:8501 / 127.0.0.1:8501.

### 5. LLM timeout + retry

**Location:** `src/llm/deepseek_client.py`

- HTTP timeout: 60s
- Retry: 3 attempts, exponential backoff 2s -> 30s
- Retries on: APIConnectionError, RateLimitError, APIStatusError, TimeoutError

### 6. EMERGENCY-downgrade protection

**Location:** `src/pipeline/orchestrator.py`

EMERGENCY_INTERRUPT is NOT downgraded if:
- Secrets/PII found, OR
- CRITICAL_RISK_PATTERNS match (RCE, SQLi, path traversal, XXE, SSTI, LDAPi)

### 7. Deterministic audit trail

- material_hash = SHA-256 of analyzed slice (64 hex)
- material_hash_full = SHA-256 of original (64 hex)
- material_hash = sha256(context + material), context = filename:session_id -> no collisions

### 8. Secret storage

- .env in .gitignore
- .env.example for docs
- API key never logged

---

## What is NOT implemented (honest boundaries)

### 1. Material sandbox - NOT implemented
Conveyor does not execute material. But private code goes to DeepSeek cloud. Use mode=local (Ollama) for private data.

### 2. Prompt injection detection - PARTIAL
SUBST_MAX_ATTEMPTS=2 threshold. No semantic detection.

### 3. Pre-commit hook for secrets - NOT implemented
Redaction at analysis time, not commit time. Use gitleaks/TruffleHog separately.

### 4. SAST integration - NOT implemented
Conveyor is LLM-based. For deterministic SAST, add Bandit/Semgrep in CI.

### 5. Dependency CVE scanning - NOT implemented
requirements.txt uses >= without pinning. Use pip-audit separately.

---

## Responsible disclosure

1. Do NOT open a public issue.
2. Email: dvddv9@users.noreply.github.com
3. Include description, steps, impact.
4. We respond within 7 days.

---

## Supported versions

| Version | Supported |
|---------|-----------|
| 5.7.x | YES |
| < 5.7 | NO (upgrade) |

---

## Security checklist for deployment

- [ ] CONVEYOR_API_KEY set (not empty)
- [ ] .env NOT in git
- [ ] DEEPSEEK_API_KEY rotated if leaked
- [ ] CORS restricted to your UI origin
- [ ] Reverse proxy terminates TLS
- [ ] data/ backed up + access-controlled
- [ ] Rate limit appropriate for traffic

---

*Last updated: 2026-10-12 | Conveyor V5.7*