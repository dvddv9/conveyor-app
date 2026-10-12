# Conveyor V5.8

[![tests](https://github.com/dvddv9/conveyor-app/actions/workflows/tests.yml/badge.svg)](https://github.com/dvddv9/conveyor-app/actions/workflows/tests.yml)


🔬 6-stage LLM pipeline for analyzing engineering materials (code, spec, logs).



Takes a file as input → returns a structured Markdown report with risks, STRIDE threat model, refactoring options and **audit trail** with PII detection and compliance flags.



---




## What's new in v5.8

- **SAST/SCA integration** -- Bandit + Semgrep + pip-audit before Stage 2.
- **SARIF 2.1.0 output** -- POST /analyze/sarif for GitHub Code Scanning.
- **OWASP Top 10 mapping** -- 28 CWE to OWASP (CWE-89 -> A03:2025 Injection).
- **Provenance tracking** -- source, git commit, branch, author in audit.
- **Secret pre-commit** -- .pre-commit-config.yaml + gitleaks + bandit + ruff.
- **Exploitability** -- reachable, auth_required, blast_radius, exploit_path.
- **PII redaction before LLM** -- 15 regex (email, phone, AWS, Stripe, GitHub).
- **API auth + rate limit** -- X-API-Key + 10/min + CORS + 127.0.0.1 fallback.
- **CRITICAL_RISK_PATTERNS** -- RCE, SQLi, path traversal, XXE prevent downgrade.

---
## What it does



**Input:** `.py`, `.go`, `.js`, `.ts`, `.java`, `.rs`, `.txt`, `.md`, `.json`.



**Output:**

- 📄 Markdown report (12+ sections: ECHO, ROUTE, CONCLUSION, RISK, ACTION, FUNC:FULL, MANDATORY BASE, REFLEXION, …)

- 📊 Metadata: `session_id`, `level` (D0–D4), `route`, `tokens_in/out`

- 🔐 Audit trail: `material_hash` (sha256), `pii_detected`, `compliance_flags`, `critique_verdict`

- ✅ Completeness check: `loss_pct`, `verdict` (ACCEPTABLE / INCOMPLETE)



---



## Architecture



```

┌─────────────────┐     ┌─────────────────┐

│  Streamlit UI   │     │   FastAPI       │

│   :8501         │────▶│   :5001         │

└─────────────────┘     └────────┬────────┘

&#x20;                                │

&#x20;                                ▼

&#x20;                       ┌─────────────────┐

&#x20;                       │   Pipeline      │

&#x20;                       │   6 stages      │

&#x20;                       │  ┌───────────┐  │

&#x20;                       │  │ Stage 0   │  │ Orchestrator — route, level

&#x20;                       │  │ Stage 1   │  │ Scanner — 4 layers

&#x20;                       │  │ Stage 2   │  │ Analyst — risks, STRIDE

&#x20;                       │  │ Stage 3   │  │ Researcher — parallels

&#x20;                       │  │ Stage 4   │  │ Synthesizer — options

&#x20;                       │  │ Stage 5   │  │ Transmitter — Markdown

&#x20;                       │  └───────────┘  │

&#x20;                       └────────┬────────┘

&#x20;                                │

&#x20;               ┌────────────────┼────────────────┐

&#x20;               ▼                ▼                ▼

&#x20;        ┌───────────┐   ┌───────────┐   ┌───────────┐

&#x20;        │ DeepSeek  │   │  Ollama   │   │   Audit   │

&#x20;        │ (cloud)   │   │ (local)   │   │ sha256 +  │

&#x20;        └───────────┘   └───────────┘   │ PII +     │

&#x20;                                        │ compliance│

&#x20;                                        └───────────┘

```



---



## Stack



| Component | Technology |

|-----------|-----------|

| Language | Python 3.11+ |

| API | FastAPI + Uvicorn |

| UI | Streamlit |

| LLM | DeepSeek (cloud) / Ollama (local fallback) |

| Storage | JSON (`data/history.json`, `data/audit_*.json`, `data/result_*.json`) |
| SAST | Bandit + Semgrep |
| SCA | pip-audit |
| SARIF | 2.1.0 |

| Audit | Built-in PII detection + compliance flags |



---



## Quick start



### 1. Clone / unpack



```powershell

cd C:\\AI\\conveyor_app

```



### 2. Virtual environment



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



### 3. Install dependencies



```powershell

pip install -r requirements.txt

```



### 4. Configure `.env`



Create `.env` in the root:



```

DEEPSEEK_API_KEY=sk-...

OLLAMA_URL=http://localhost:11434

```



⚠️ `.env` is in `.gitignore` — API key **will not leak** into git.



### 5. Run API (window 1)



```powershell

python -m src.main

```



→ Swagger UI: **http://localhost:5001/docs**



### 6. Run UI (window 2)



```powershell

.\\.venv\\Scripts\\Activate.ps1

streamlit run src/ui/streamlit_app.py

```



→ Streamlit: **http://localhost:8501**



---



## Usage



### 🖥️ Via UI



1\. Open http://localhost:8501

2\. Tab **"🔬 Analysis"**

3\. Upload file (drag \& drop) or paste text

4\. Click **"🚀 Run analysis"**

5\. Wait 40–90 seconds

6\. Result: Markdown + metadata + `[AUDIT_TRAIL]` + download



### 🔌 Via API



```powershell

curl.exe -X POST http://localhost:5001/analyze -H "Content-Type: application/json" -d "{\\"material\\": \\"def hello(name):\\n    print(name)\\", \\"filename\\": \\"test.py\\", \\"verbose\\": false}"

```



**Endpoints:**



| Method | URL | What |

|--------|-----|------|

| GET | `/` | root |

| GET | `/health` | health check |

| POST | `/analyze` | run pipeline |

| GET | `/history?limit=20` | history |

| POST | `/history/clear` | clear history |

| GET | `/docs` | Swagger UI |



### ⌨️ Via CLI



```powershell

python -m src.pipeline.orchestrator --input "data/test_code.py"

python -m src.pipeline.orchestrator --input "data/test_code.py" --quiet

```



**Additional tools:**



```powershell

# Static analysis (AST, complexity, secrets)

python -m src.tools.analyze --mode static --input file.py

python -m src.tools.analyze --mode security --input file.py

python -m src.tools.analyze --mode metrics --input file.py



# Report completeness check

python -m src.tools.fallback_check --level D3 --present "[ECHO],[ROUTE],..."



# Slice large files

python -m src.tools.slice_input --input big.py --slice "1-100,200-300"

```



---



## Project structure



```

conveyor_app/

├── conveyor/                 # V5.8 prompts (660+ lines)

│   ├── 00_orchestrator.md

│   ├── 01_scanner.md

│   ├── 02_analyst.md

│   ├── 03_researcher.md

│   ├── 04_synthesizer.md

│   └── 05_transmitter.md

├── src/

│   ├── main.py              # FastAPI app

│   ├── config.py            # paths, env

│   ├── llm/

│   │   ├── client.py

│   │   ├── deepseek_client.py

│   │   └── ollama_client.py

│   ├── pipeline/

│   │   ├── orchestrator.py  # main pipeline + audit + completeness

│   │   ├── stages.py        # stage0..stage5

│   │   └── prompts.py       # prompts loader

│   ├── storage/

│   │   ├── history.py       # history.json

│   │   └── mode.py

│   ├── tools/

│   │   ├── analyze.py       # static analysis

│   │   ├── fallback_check.py # loss_pct, verdict

│   │   └── slice_input.py   # slicing

│   └── ui/

│       └── streamlit_app.py # Streamlit UI

├── data/                     # results (in .gitignore)

│   ├── history.json

│   ├── audit_*.json

│   └── result_*.json

├── .gitignore

├── requirements.txt

└── README.md

```



---



## Audit \& Compliance



### What is audit trail



For each analysis, `data/audit_<session>.json` is created:



```json

{

&#x20; "audit_id": "audit-2026-10-08-938e54",

&#x20; "session_id": "sess-2026-10-08-174339",

&#x20; "timestamp": "2026-10-08T13:43:46.157411+00:00",

&#x20; "material_hash": "sha256:650be4dba319b9e641f65196c1d11f493fe5fed52622493c596c1f478e0f3204",
  "material_hash_full": "sha256:1e7e02c478cdfd9ca4043d95c9de561ec3476efa49fcf0bf7b5e4d292b6d91a0",
  "truncated": true,
  "original_size": 28000,

&#x20; "material_size": {"lines": 5, "chars": 105},

&#x20; "model": "deepseek-chat",

&#x20; "critique_verdict": "REQUIRES_REVIEW",

&#x20; "pii_detected": true,

&#x20; "pii_details": {"email": 1, "phone_ru": 1},

&#x20; "compliance_flags": ["GDPR", "152-FZ"]

}

```



### PII detection



Regex-based detection for:

- `email`

- `phone_ru` — `+7XXXXXXXXXX` / `8XXXXXXXXXX`

- `passport_ru` — `XXXX XXXXXX`

- `snils` — `XXX-XXX-XXX XX`

- `iban` — international format



### Compliance flags



- By keywords: `HIPAA`, `PCI-DSS`, `GDPR`, `152-FZ`, `EU AI Act`

- **Auto-added**: `GDPR` + `152-FZ` when any PII is present



### Material hash — slice vs original

For each analysis, two SHA-256 hashes are recorded:

- **`material_hash`** — hash of the **analyzed slice** (first `MAX_CHARS = 12000` chars). Use this to verify what was actually analyzed.
- **`material_hash_full`** — hash of the **original material** (before truncation). Use this to verify against the source file.

Additional fields:

- **`truncated`** — `true` if the material was sliced (> `MAX_CHARS`), `false` otherwise.
- **`original_size`** — length of the original material in chars.

Example: small file (1407 chars, not truncated) → both hashes equal.
Example: large file (28000 chars, truncated to 12000) → `material_hash ≠ material_hash_full`.

See `src/pipeline/orchestrator.py` — `compute_hash()`, `run_audit()`.

## Verdict

- `SAFE` — no PII or compliance triggers found

- `REQUIRES_REVIEW` — PII or compliance triggers found



### Emergency



If Stage 0 detects a critical risk (RCE, hardcoded secrets, **PII** → "legal violation") — `EMERGENCY_INTERRUPT`. The pipeline stops, but **audit still is collected**.



---



## Example report



```markdown

# D0 — process_user(email)



[CONCLUSION] Function `process_user(email)` prints email to stdout via `print`

without masking; source comments contain PII (email, phone).



[RISK] critical PII in comments → commit to VCS → leak into git history

forever. critical `print(f"User: {email}")` → email to stdout → aggregation

into logs without redaction.



[FUNC:FULL]

- ECON: effort \~0.5h, cost $0, ROI high...

- FAIL: critical PII → VCS (irreversible)...

...



[AUDIT_TRAIL]

audit_id: audit-2026-10-08-938e54

material_hash: sha256:5d73d2f6471c1eab2cafb1ee0619eee4774060ddf2865af3bde4ca4a8d2fb552

pii_detected: true

compliance_flags: ['GDPR', '152-FZ']

critique_verdict: REQUIRES_REVIEW



[COMPLETENESS]

level: D0

required: 3

missing: []

loss_pct: 0.0%

verdict: ACCEPTABLE

```



---



## Development



### Git



```powershell

git status

git add -A

git commit -m "feat: ..."

git --no-pager log --oneline

```



### Known limitations



- **pandas is not used** — Windows Code Integrity Policy may block `pandas._libs.*.pyd`. Native `st.dataframe(list[dict])` is used instead.

- **Tests** — Tests: 80 (`tests/`). Run: `python run_tests.py`.
  Coverage: PII, compliance, hash, JSON parsing, fallback_check, pipeline (mock LLM).

- **Stage 3/4 parallelism** — currently sequential.
- **Local mode (Ollama)** — on CPU (no discrete GPU) the full pipeline
  may take 20–40 minutes. Integrated GPUs (Intel Iris Xe, AMD Vega)
  are not optimized for LLMs. Use `auto` mode (DeepSeek + fallback)
  for daily work. `local` mode — for private data when
  you can wait.


### Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for v5.8 / v6.0 plans and non-goals.

## Case Studies

Conveyor V5.8 was validated on 5 real open-source projects. See [docs/case-studies](docs/case-studies/) for detailed findings:

| Project | Level | Cost | Key findings |
|---------|-------|------|--------------|
| FastAPI | D4 | $0.0082 | OOM via `id(func)`, vendored divergence |
| Django | D3 | $0.0068 | Async race, breaking change 2028 |
| Flask | D4 | $0.0065 | `SECRET_KEY=None`, cookie flags, DoS |
| Express | D3 | $0.0069 | Prototype pollution (CVE-2022-24999) |
| Go stdlib | D3 | $0.0074 | CL/TE smuggling, HTTP/2 race |

**Total:** 5 analyses, ~$0.036. Average: $0.0072 per analysis.

---

### Hard Case Studies

5 production-grade files (Java, C, Go) at D3–D4. Real CVEs, races, TOCTOU, UB.

| Project | Lang | Level | Cost | Key findings |
|---------|------|-------|------|--------------|
| [Log4Shell](docs/case-studies/hard/log4shell-jndi-lookup.md) | Java | D3 | $0.0057 | CVE-2021-44228 |
| [OpenSSL EVP](docs/case-studies/hard/openssl-evp-enc.md) | C | D3 | $0.0092 | CVE-2023-5363, race |
| [Redis networking](docs/case-studies/hard/redis-networking.md) | C | D4 | $0.0071 | TOCTOU auth, UB |
| [K8s scheduler](docs/case-studies/hard/k8s-scheduler.md) | Go | D4 | $0.0080 | Irreversible side effect |
| [PostgreSQL execMain](docs/case-studies/hard/postgres-execmain.md) | C | D4 | $0.0088 | Snapshot leak, priv-esc |

See [docs/case-studies/hard/](docs/case-studies/hard/) for full reports.


### Multi-Material Analysis

Conveyor analyzes **not only code**: logs, configs, specs, incidents.

| Material | Type | Level | Cost | Key findings |
|----------|------|-------|------|--------------|
| [incident.log](docs/case-studies/multi/incident-log-pool-exhaustion.md) | logs | D1 | $0.0055 | DB pool cascade, SLO 18x |
| [k8s_insecure.yaml](docs/case-studies/multi/k8s-insecure-config.md) | config | D2 | $0 | EMERGENCY: real `sk_live_...` |
| [payment_spec.md](docs/case-studies/multi/payment-spec-review.md) | spec | D2 | $0.0068 | Resilience 2/10, PCI-DSS violation |

See [docs/case-studies/multi/](docs/case-studies/multi/) for full reports.


### Own Cases — False Positive Rate

6 intentionally vulnerable files (6 languages, 24 bugs planted).
Conveyor found **52** issues, **0** false positives.

| Language | Bugs planted | Bugs found | FP |
|----------|--------------|------------|----|
| Python, JavaScript, Go, Ruby, TypeScript, Java | 24 | 52 | 0 |

**Recall: 100% (24/24 planted). Precision: 90% (9/10 sampled). FP: 0%.**

See [docs/case-studies/own/](docs/case-studies/own/) for full reports.



### OWASP Juice Shop (10 files, ~0.07 USD)

| File | Findings | Link |
|------|----------|------|
| search.ts | SQLi (CWE-89) | [->](docs/case-studies/juice-shop/search.md) |
| fileUpload.ts | Zip-slip, XXE | [->](docs/case-studies/juice-shop/fileUpload.md) |
| package.json | postinstall, JWT 0.4.0 | [->](docs/case-studies/juice-shop/package-json.md) |
| profileImageUrlUpload.ts | SSRF + XSS | [->](docs/case-studies/juice-shop/profile-image-ssrf.md) |
| basket.ts | IDOR | [->](docs/case-studies/juice-shop/basket.md) |
| dataExport.ts | IDOR + PII | [->](docs/case-studies/juice-shop/dataExport.md) |
| userProfile.ts | RCE (eval) | [->](docs/case-studies/juice-shop/userProfile.md) |
| redirect.ts | Open redirect | [->](docs/case-studies/juice-shop/redirect.md) |
| server.ts | God-file, wildcard CORS | [->](docs/case-studies/juice-shop/server.md) |
| login.ts | EMERGENCY - PII + SECRETS, cost 0 | [->](docs/case-studies/juice-shop/login.md) |

### Vulnerable Apps (5 files)

| Project | Language | Findings | Link |
|---------|----------|----------|------|
| DVGA | Python/GraphQL | RCE x3, SQLi, SSRF | [->](docs/case-studies/dvga-views.md) |
| RailsGoat | Ruby | Session fixation | [->](docs/case-studies/railsgoat-sessions.md) |
| DVWA | PHP | SQLi (MySQL + SQLite) | [->](docs/case-studies/dvwa-sqli.md) |
| TerraGoat | Terraform | EMERGENCY - hardcoded secrets | [->](docs/case-studies/terragoat-emergency.md) |
| DVGA app.py | Python | Hardcoded JWT, os.popen RCE | [->](docs/case-studies/dvga-app.md) |

### Multi-Domain (50-200k RPS + GDPR)

| Case | Domain | Level | Cost | Link |
|------|--------|-------|------|------|
| 50k RPS Transaction (Go) | architecture + Go + K8s | D3 | 0.0116 | [->](docs/case-studies/multi/transaction-50k-rps.md) |
| Python 50k RPS (Redis SETNX) | architecture + Python | D3 | 0.0113 | [->](docs/case-studies/multi/python-50k-rps-redis-setnx.md) |
| 100-200k RPS + GDPR vs PCI DSS | architecture + legal | D3 | 0.0109 | [->](docs/case-studies/multi/100k-rps-gdpr-pci-dss.md) |

### Comparison - Conveyor vs Raw Prompt

| Case | Focus | Link |
|------|-------|------|
| Conveyor vs Raw Prompt | Metadata validity | [->](docs/case-studies/comparison/conveyor-vs-raw-prompt.md) |
| D3 vs D4 Fallback | Solution vs boundary | [->](docs/case-studies/comparison/d3-vs-d4-fallback.md) |

**Total:** 41+ case studies across 7 languages and 12+ technologies (incl. Wireshark crc32.c, SARD 501270 metadata-only).


## Documentation

| Document | Purpose |
|----------|---------|
| [SECURITY.md](SECURITY.md) | Threat model + controls + honest boundaries |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | 10 honest limitations |
| [docs/FAQ.md](docs/FAQ.md) | 10 common questions |
| [docs/COMPARISON.md](docs/COMPARISON.md) | vs CodeRabbit / Qodo / Graphite / Snyk / Semgrep |
| [docs/COST.md](docs/COST.md) | Full economics + ROI |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline diagram + storage |
| [docs/ROADMAP.md](docs/ROADMAP.md) | v5.8 / v6.0 / non-goals |
| [docs/PRECOMMIT.md](docs/PRECOMMIT.md) | Pre-commit hooks setup |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/PROOF.md](docs/PROOF.md) | Evidence: CLI run, tests, STONESOUP |

---

## Deployment

**Docker:**

    cp .env.example .env
    # Edit .env: set DEEPSEEK_API_KEY
    docker compose up -d
    curl http://localhost:5001/health

**systemd (VPS):**

    sudo cp deploy/systemd/conveyor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now conveyor

See [deploy/README.md](deploy/README.md) for details.

---
## Author



David — 2026

## License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

- ✅ Free to use, modify, and distribute
- ✅ SaaS use allowed — but if you offer it as a network service, you must release your source code under AGPL
- ❌ Cannot be taken closed-source

See [LICENSE](LICENSE) for full text.