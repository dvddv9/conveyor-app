# Conveyor V5.7

[![tests](https://github.com/dvddv9/conveyor-app/actions/workflows/tests.yml/badge.svg)](https://github.com/dvddv9/conveyor-app/actions/workflows/tests.yml)


🔬 6-stage LLM pipeline for analyzing engineering materials (code, spec, logs).



Takes a file as input → returns a structured Markdown report with risks, STRIDE threat model, refactoring options and **audit trail** with PII detection and compliance flags.



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

├── conveyor/                 # V5.7 prompts (660+ lines)

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

&#x20; "material_hash": "sha256:4f87e43baa8f2253",

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



### Verdict



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

material_hash: sha256:4f87e43baa8f2253

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

- **Tests** — 44 tests (`tests/`). Run: `python run_tests.py`.
  Coverage: PII, compliance, hash, JSON parsing, fallback_check, pipeline (mock LLM).

- **Stage 3/4 parallelism** — currently sequential.
- **Local mode (Ollama)** — on CPU (no discrete GPU) the full pipeline
  may take 20–40 minutes. Integrated GPUs (Intel Iris Xe, AMD Vega)
  are not optimized for LLMs. Use `auto` mode (DeepSeek + fallback)
  for daily work. `local` mode — for private data when
  you can wait.


### Roadmap

## Case Studies

Conveyor V5.7 was validated on 5 real open-source projects. See [docs/case-studies](docs/case-studies/) for detailed findings:

| Project | Level | Cost | Key findings |
|---------|-------|------|--------------|
| FastAPI | D4 | $0.0082 | OOM via `id(func)`, vendored divergence |
| Django | D3 | $0.0068 | Async race, breaking change 2028 |
| Flask | D4 | $0.0065 | `SECRET_KEY=None`, cookie flags, DoS |
| Express | D3 | $0.0069 | Prototype pollution (CVE-2022-24999) |
| Go stdlib | D3 | $0.0074 | CL/TE smuggling, HTTP/2 race |

**Total:** 5 analyses, ~$0.036. Average: $0.0072 per analysis.

---

### Roadmap

- [x] Tests — 44 (41 unit + 3 E2E)
- [x] GitHub Actions (CI)
- [x] UI filters (by level, verdict, pii_detected)
- [x] `pyproject.toml` + CLI (`conveyor analyze/info`)
- [x] Truncate large files (>12000 chars)
- [x] Secrets detection (AWS, Stripe, GitHub, Slack, passwords, private keys)
- [x] Cost tracker ($ per analysis)
- [x] Idempotency (`cached: true`)
- [x] Mode switcher (auto/cloud/local)
- [ ] Stage 3/4 parallelism (`asyncio.gather`)
- [ ] Streaming output (SSE)
- [ ] Integrate `slice_input` into orchestrator
- [ ] GitHub App (webhook on PR)
\

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

## License



AGPL-3.0 (see LICENSE).



---



## Author



David — 2026

## License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

- ✅ Free to use, modify, and distribute
- ✅ SaaS use allowed — but if you offer it as a network service, you must release your source code under AGPL
- ❌ Cannot be taken closed-source

See [LICENSE](LICENSE) for full text.