# Vishap V6.0.3

<img src="docs/logo.png" alt="Vishap dragon" width="128" height="128" align="right">


**Vishap — multi-material IT analyst.** Code, config, spec, logs, data. 6-stage LLM pipeline with SAST/SCA, SARIF 2.1.0, OWASP Top 10, audit trail (SHA-256), provenance, exploitability. 2 CVEs found (Log4Shell, OpenSSL). Recall 100%, Precision 90%, FP 0%.

---


[![tests](https://github.com/dvddv9/vishap/actions/workflows/tests.yml/badge.svg)](https://github.com/dvddv9/vishap/actions/workflows/tests.yml)


🔬 6-stage LLM pipeline for analyzing engineering materials (code, spec, logs).



Takes a file as input → returns a structured Markdown report with risks, STRIDE threat model, refactoring options and **audit trail** with PII detection and compliance flags.



---




## What's new in v6.0.3

JobStore abstraction -- foundation for v6.1 (PostgreSQL).

- src/api/job_store.py (new) -- JobStore Protocol, Job frozen dataclass, JobStatus enum.
- src/api/job_store_memory.py (new) -- InMemoryJobStore (thread-safe via RLock).
- src/api/jobs.py -- backward-compat shim; legacy API delegates to JobStore singleton
  (JOB_STORE=memory|postgres env; postgres -> v6.1).
- tests/test_job_store.py (new) -- 15 tests (Protocol-based).
- tests/test_jobs_shim_iso.py (new) -- 4 tests (regression for ISO conversion).
- Fixed: update_job now converts ISO-string started_at/finished_at to datetime
  (production bug: /status/{job_id} would crash on .isoformat()).
- 461 tests passing, 0 failed.

## What's new in v6.0.2

Bugfix: test isolation + version test drift.

- tests/test_ui_async.py::test_ui_has_v6_version now reads version from pyproject.toml.
- tests/conftest.py (new) -- pytest_configure sets VISHAP_DATA_DIR to tmp
  (fixes PermissionError on Windows: tests wrote audit files to ~/.vishap/data).
- tests/test_conftest_data_dir.py (new) -- 4 tests.
- 456 tests passing at v6.0.2 (was 435 in handoff).

## What's new in v6.0.1

- **UI: async analysis, LLM mode sidebar, dataflow rendering, custom theme** -- UI caught up with v6.0.0 async backend.
  - `src/ui/streamlit_app.py`: custom header (🐉 gradient), CSS theme.
  - Sidebar: LLM mode selector (`auto` / `cloud` / `local`).
  - Async button `⚡ Async` -- uses `POST /analyze/async` + polling `/status/{job_id}` + `/report/{job_id}`.
  - Dataflow expander -- shows `dataflow_path` (source -> intermediate -> sink) for Java/C.
  - Version bumped to V6.0.1.
  - Tests: `tests/test_ui_async.py` (new, 19 tests).

- **+19 tests** (416 -> 435).

## What's new in v6.0.0

- **Async API -- job-based analysis (v6.0)** -- `POST /analyze` blocked for 30-90 seconds. Now async: submit, poll status, fetch report. Foundation for SaaS.
  - `src/api/jobs.py` (new) -- in-memory job store. `create_job`, `get_job`, `update_job`, `delete_job`, `list_jobs`, `clear_jobs`, `job_count`. Thread-safe (`Lock`).
  - `src/main.py`: 3 new endpoints:
    - `POST /analyze/async` -> `{job_id, status: "queued"}` immediately.
    - `GET /status/{job_id}` -> `{status, created_at, started_at, finished_at, error}`.
    - `GET /report/{job_id}` -> full result (409 if not done).
  - `BackgroundTasks` -- pipeline runs in background via existing `run_pipeline_async`.
  - Old `/analyze` (sync) unchanged -- backward compatible.
  - Dogfood: POST -> job_id -> poll (42s) -> report with full audit.
  - Tests: `tests/test_async_api.py` (new, 20 tests).

- **+20 tests** (396 -> 416).

## What's new in v5.11.6

- **P2-7: C taint patterns (regex-based data flow)** -- P2-7 was blind on C. Now detects stdin/argv/env/socket taint sources, cmd/buffer/file sinks, and entry points.
  - `patterns.py`: `TAINT_SOURCES["source_c"]` -- scanf/fgets/gets/read/recv, argv[], getenv.
  - `patterns.py`: `TAINT_SINKS["sink_c_cmd|buffer|file"]` -- system/popen/exec*, strcpy/strcat/sprintf/memcpy/gets, fopen/open/fread.
  - `patterns.py`: `EXPLOIT_PATTERNS["entrypoint_c_main|jni"]`, `blast_c_cmd|buffer|file`.
  - `reachability.py`: `_LANG_ENTRYPOINTS["c"]`, `trace_taint` auto-detects C.
  - Dogfood: `c_cmd_injection.c` path = `main -> argv[1] -> strcpy -> system` (blast_radius: high).
  - Tests: `tests/test_patterns_c.py` (new, 35 tests).

- **+35 tests** (361 -> 396).

## What's new in v5.11.5

- **P2-7: Java taint patterns (regex-based data flow)** -- P2-7 was blind on Java. Now detects Servlet/Spring taint sources, SQL/cmd/file/reflection/deserialization sinks, and entry points.
  - `patterns.py`: `TAINT_SOURCES["source_java"]` -- request.getParameter/getHeader/getCookies, System.in/getenv/getProperty, Scanner, BufferedReader, @RequestParam/@PathVariable/@RequestBody.
  - `patterns.py`: `TAINT_SINKS["sink_java_sql|cmd|file|reflect|deser|jndi"]` -- executeQuery/executeUpdate/createStatement, Runtime.exec/ProcessBuilder, new File/FileInputStream/Paths.get, Class.forName/Method.invoke, ObjectInputStream/readObject, JndiManager/InitialContext/Context.lookup (Log4Shell).
  - `patterns.py`: `EXPLOIT_PATTERNS["entrypoint_java_main|spring|servlet"]` -- public static void main, @RestController/@GetMapping, doGet/doPost.
  - `reachability.py`: `_LANG_ENTRYPOINTS["java"]`, `trace_taint` auto-detects Java, comment lines (// # * /*) are skipped.
  - Dogfood: `ServletSqli.java` path = `doGet -> request.getParameter("id") -> Statement.createStatement`.
  - Tests: `tests/test_patterns_java.py` (new, 41 tests).

- **+41 tests** (320 -> 361).

## What's new in v5.11.3

- **Refactor: UI api_client.py -- centralized HTTP client** -- `streamlit_app.py` had 8 duplicated `requests.*` calls, each passing `headers=HEADERS` manually (v5.10.5 fix). Headers were defined in 3 places.
  - New module: `src/ui/api_client.py` -- `get()`, `post()`, `_url()`. Auto-injects `X-API-Key` header + default timeouts.
  - `src/config.py`: added `API_URL`, `CONVEYOR_API_KEY`, `API_TIMEOUT_SHORT/DEFAULT/LONG/BATCH`.
  - `src/ui/streamlit_app.py`: 8 calls replaced with `api_client.get/post(...)`. Removed local `API_URL`, `API_KEY`, `HEADERS`, `import requests`, `import os`.
  - Tests: `tests/test_api_client.py` (new, 16 tests), `tests/test_ui_headers.py` (rewritten, 13 tests -- now checks `api_client` + no direct `requests.*` in UI).
  - No behavior change for end users.

- **+23 tests** (297 -> 320).

## What's new in v5.11.2

- **Refactor: consolidated risk verdict computation** -- `run_audit()` inlined ~45 lines of verdict logic (v5.10.6 risk_nodes + v5.11.1 security.findings) with duplicated `critique` / `risk_verdict` branches.
  - New module: `src/pipeline/verdict.py` -- `compute_risk_verdict()` single source of truth.
  - New function: `_has_critical_priority()`, `_has_critical_risk_nodes()`, `_has_critical_security()`.
  - Behavior change: `critique_verdict` now correctly reflects `EMERGENCY` (was `SAFE` in emergency path -- bugfix).
  - Behavior preserved: `pii`/`compliance`/`cwe_ids` -> `REQUIRES_REVIEW`; critical `risk_nodes` or `security.findings` -> `REQUIRES_REVIEW`; else -> `SAFE`.
  - Regression tests: `tests/test_verdict.py` (26 tests).
  - `run_audit()` shrunk from ~119 to ~75 lines.

- **No API/behavior changes for end users.** Fully backward compatible.
- +26 tests. Total: 297 passing.

## What's new in v5.11.1

- **Bugfix: risk_verdict ignored stage2.security.findings (dogfood find)** -- `run_audit()` set `REQUIRES_REVIEW` only when `stage2.risk_nodes` contained a critical node (v5.10.6 fix). Security findings in `stage2.security.findings` (e.g. `SEC-1` command injection) were ignored. A file with a critical `SEC-N` but no critical `RN-N` got a **false SAFE**.
  - Fix: `run_audit()` now also scans `stage2.security.findings` for `priority in (kritichno, critical)`. Short-circuits on critical `risk_nodes`. Fail-open on malformed `security` data.
  - Regression tests: `tests/test_risk_verdict_security.py` (8 tests).
  - Dogfood case: `docs/case-studies/dogfood/wcurl-sh/` (`SEC-1` command-line injection via `--curl-options`).

- **No API/behavior changes.** Fully backward compatible.
- +8 tests. Total: 271 passing.

## What's new in v5.10.7

- **Bugfix: PII false positive on copyright headers (dogfood find)** -- `detect_pii` flagged emails in Wireshark copyright header (`packet-btl2cap.c`: `scholz@cs.uni-bonn.de`, `gerald@wireshark.org`) as PII -> false positive GDPR/152-FZ.
  - Fix: `_filter_copyright_emails()` -- skip emails in lines with `copyright`, `(c)`, `license`, `author`, or common OSS domains (`@wireshark.org`, `@gnu.org`, `@apache.org`, etc.).
  - Regression tests: `tests/test_pii_copyright.py` (6 tests).
  - Dogfood case: `docs/case-studies/dogfood/packet-btl2cap-c/`.

- **Bugfix: anomaly detection on source code (dogfood find)** -- `enrich_anomaly` ran on C code (`packet-btl2cap.c`), finding revision numbers and hex constants as "numbers" (samples=310, mean=141, std=1684, ratio=11.9). v5.10.6 density guard was insufficient (density 0.026 > 0.01).
  - Fix: std-ratio guard v2 -- skip if `std > 10 * mean` OR (`mean > 1000` AND `std > 1000`).
  - Regression tests: `tests/test_anomaly_code.py` (5 tests).

- **No API/behavior changes for real metrics.** Fully backward compatible.
- +11 tests (`tests/test_pii_copyright.py`, `tests/test_anomaly_code.py`). Total: 263 passing.

## What's new in v5.10.6

- **Bugfix: risk_verdict ignored critical risk_nodes (dogfood find)** -- `run_audit()` computed `risk_verdict` only from `pii` / `compliance` / `cwe_ids`, ignoring `stage2.risk_nodes` from the LLM analyst. When the LLM found critical findings (`priority: критично`) but the code had no PII/CWE/compliance triggers, `risk_verdict` stayed `SAFE` -- UI showed green SAFE despite a report full of critical risks.
  - Fix: `run_audit()` now accepts `stage2_result` and checks `risk_nodes` for `priority in (критично, critical)`. If found, `risk_verdict = REQUIRES_REVIEW` and `critique_verdict = REQUIRES_REVIEW`.
  - All 3 call sites updated (sync, async, emergency).
  - Regression tests: `tests/test_risk_verdict.py` (7 tests).
  - Dogfood case: `docs/case-studies/dogfood/RequestFilter-java/` (Sakai RequestFilter.java, 3 critical nodes RN-1/RN-8/RN-11).

- **Bugfix: anomaly detection on non-numeric text (dogfood find)** -- `enrich_anomaly()` ran on Java/C/Python source code, treating line numbers and hex constants as "numbers" (e.g. RequestFilter.java: samples=22, mean=645, std=794). Harmless but noisy.
  - Fix: density guard -- if `len(numbers) / len(text) < 0.01`, return `{"anomaly": {}}`.
  - Also: if `detect_anomaly` returns `INSUFFICIENT_DATA`, return `{"anomaly": {}}` (no noise in audit).
  - Regression tests: `tests/test_anomaly_density.py` (5 tests).

- **No API/behavior changes for numeric data.** Fully backward compatible.
- +12 tests (`tests/test_risk_verdict.py`, `tests/test_anomaly_density.py`). Total: 252 passing.

## What's new in v5.10.5

- **Bugfix: async pipeline imports (dogfood find)** -- `src/pipeline/async_stages.py` used `MAX_TOKENS_STAGE4` without importing it. Any `/analyze` request via API (async branch) failed with `NameError: name 'MAX_TOKENS_STAGE4' is not defined`. The async branch was broken since v5.8; sync CLI worked because `stages.py` imported it correctly.
  - Fix: `from src.config import MAX_TOKENS, MAX_TOKENS_STAGE4` in `async_stages.py`.
  - Regression tests: `tests/test_async_imports.py` (4 tests) -- AST-based check that async and sync pipelines import every config constant they use.
- **Bugfix: Streamlit UI missing X-API-Key (dogfood find)** -- `src/ui/streamlit_app.py` called `requests.get/post` without the `X-API-Key` header. Every protected endpoint (`/analyze`, `/analyze/batch`, `/history`, `/mode`) returned `401 X-API-Key required`. UI was non-functional via FastAPI since v5.8.
  - Fix: read `CONVEYOR_API_KEY` from env, build `HEADERS = {"X-API-Key": API_KEY}`, pass `headers=HEADERS` in all 8 requests.
  - Regression tests: `tests/test_ui_headers.py` (6 tests) -- AST-based check that every `requests.*` referencing `API_URL` passes headers, no double commas.
- **No API/behavior changes.** Fully backward compatible.
- +10 tests (`tests/test_async_imports.py`, `tests/test_ui_headers.py`). Total: 240 passing.

## What's new in v5.10.4

- **Anomaly Detection (P2-12)** -- statistical outlier detection in numeric series (logs, metrics, CSV).
  Audit trail now includes:
  - `anomaly_verdict: ANOMALIES_FOUND | NORMAL | INSUFFICIENT_DATA`
  - `anomaly_count: N`
  - `anomaly_method: zscore | iqr | ewma`
  - `anomaly_top: [{index, value, score, reason}, ...]` (top-3 in audit)
- **3 methods** (deterministic, no LLM):
  - **z-score** -- |x - mean| / std > threshold (default 3.0).
  - **IQR** -- outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR].
  - **EWMA** -- |x_t - EWMA_{t-1}| > 3*std (trend detection).
- **`src/tools/anomaly.py`** (new): `parse_numbers()`, `detect_anomaly()`, `enrich_anomaly()`. Stdlib only (`statistics`, `re`). Fail-open.
- **`patterns.py`:** added `ANOMALY_CONFIG` (min_samples=10, max_anomalies=20, top_in_audit=3).
- **`orchestrator.py`:** 4 edits -- import, call, audit entry, 3 audit-trail blocks.
- **Dogfood:** 3 cases -- latency (5000ms vs ~50ms), error rate (87 vs ~12), memory trend (500 vs ~200). All detected.
- **Known limitation:** `parse_numbers()` is heuristic (regex + timestamp filter). One numeric series per material. Multi-variate anomalies -- future.
- +17 tests (`tests/test_anomaly.py`). Total: 230 passing.

## What's new in v5.10.2

- **Data-flow Analysis (P2-7b)** -- AST-based taint tracking. Extends reachability (P2-7, regex + line-based) with real Python AST parsing.
  Audit trail now includes:
  - `dataflow_path: [{line, type, name, content}, ...]` -- full flow: source -> intermediate -> sink, with line numbers.
  - `dataflow_source_count: N` -- number of sources (function args included).
  - `dataflow.sink`, `dataflow.intermediate` -- structural view.
  Backward compatible: `exploitability` (P2-7) preserved.
- **What it adds over regex (P2-7):**
  - **Sources via function arguments** (regex cannot see this).
  - **Flow through intermediate variables** (a -> b -> sink).
  - **Full path with line numbers** for every hop.
- **`patterns.py`:** added `AST_TAINT_SOURCES` (4 groups: flask_request, builtin_input, env, file_read) and `AST_TAINT_SINKS` (3 groups: sql_execute, cmd_exec, file_write). Separate from regex-based `TAINT_SOURCES` / `TAINT_SINKS` (P2-7).
- **`src/tools/dataflow.py`** (new): `analyze_dataflow()`, `enrich_dataflow()`. Deterministic (`ast` only, no LLM). Fail-open (parse error -> `{}`). Python-only for now (Go/JS via P2-7 regex).
- **`orchestrator.py`:** 4 edits -- import, call, audit entry, and 3 audit-trail blocks. `dataflow_*` fields appear alongside `exploitability_*`.
- **Dogfood:** `examples/own/auth_service.py` -- SQL injection via f-string. P2-7 `exploitability_path: []` (regex cannot see source), P2-7b `dataflow_path: [source(username, L7) -> intermediate(query, L12) -> sink(cursor.execute, L13)]`. **P2-7b proves its value.**
- **Known limitation:** AST for Python only in v5.10.2. Go/JS covered by P2-7 regex. Non-Python returns `{}` (fail-open).
- +16 tests (`tests/test_dataflow.py`). Total: 213 passing.

## What's new in v5.10.1

- **Pluggable LLM providers** -- Vishap now works with **any OpenAI-compatible API**, not just DeepSeek:
  - OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
  - Anthropic Claude (via OpenAI-compat shim)
  - Groq, Together, Fireworks, OpenRouter
  - Local: LM Studio, vLLM, llama.cpp server, Ollama
  Configure via `VISHAP_LLM_PROVIDER` (auto | deepseek | openai | custom | ollama) + `CUSTOM_*` / `OPENAI_*` env vars.
- **`src/llm/openai_compatible.py`** (new): universal client for any OpenAI-compatible endpoint. `chat()`, `get_client()`, `is_configured()`, `provider_name()`.
- **`src/llm/async_openai_compatible.py`** (new): async mirror (`achat()`, `get_async_client()`).
- **`src/llm/client.py`**: new provider factory with auto-detect (`custom -> openai -> deepseek -> ollama`). Legacy `mode` (local/cloud/auto) still works as an alias.
- **`src/config.py`**: 7 new env vars (`VISHAP_LLM_PROVIDER`, `OPENAI_*`, `CUSTOM_*`).
- **`.env.example`**: rewritten with 4 provider examples (Groq, LM Studio, vLLM, OpenRouter).
- +16 tests (`tests/test_llm_providers.py`). Total: 197 passing.

## What's new in v5.10.0

- **Formal Threat Model (P2-10)** -- completes the P2 plan. `SECURITY.md` now contains a full formal threat model (ENISA / NIST SP 800-154 methodology):
  - **Scope** -- in scope / out of scope.
  - **Assets** -- 6 assets with type, impact, owner.
  - **Trust boundaries** -- TB-1 ... TB-5 with controls.
  - **Abuse Cases (STRIDE)** -- 10 cases: `abuse case -> control -> test`.
  - **Verification** -- each control maps to a test.
  - **Compliance Readiness** -- SOC 2 / ISO 27001 / PCI-DSS / GDPR / HIPAA.
  - **Known Limitations (formal)** -- L1 ... L5.
- **`tests/test_security_md.py`** (new): 5 doc-guard tests -- prevent regressions (deleted sections, broken test references).
- **P2 closed 4/4.** Reachability, Compliance, Runbook, Threat Model -- all shipped.
- +5 tests. Total: 181 passing.

## What's new in v5.9.9

- **Runbook Generation (P2-9)** -- incident response steps per CWE (`immediate` / `short_term` / `long_term` / `escalation`).
  Audit trail now includes:
  - `runbook: {CWE-89: {...}, ...}`
  - `runbook_cwes: [CWE-22, CWE-89, ...]`
  - `runbook_steps_count: N`
  A `[RUNBOOK]` section is added to the Markdown report (after `[COMPLETENESS]`). Omitted when no CWE is detected (fail-quiet).
- **`patterns.py`:** added `RUNBOOKS` -- 10 CWEs covered: CWE-89 (SQLi), CWE-79 (XSS), CWE-78 (OS Cmd), CWE-352 (CSRF), CWE-22 (Path Traversal), CWE-502 (Deserialization), CWE-611 (XXE), CWE-287 (Auth), CWE-778 (Logging), CWE-311 (Encryption).
- **`src/tools/runbook.py`** (new): `generate_runbook()`, `enrich_runbook()`. Deterministic (dict-lookup), fail-open.
- **`orchestrator.py`:** added `format_runbook_md()` helper + 2 insertion points (sync + async). Also fixed a duplicate `generator:` line in `[AUDIT_TRAIL]` (P2-9b bugfix).
- **Dogfood:** 4 cases -- single CWE (9 steps), multiple CWEs (21 steps), full `[RUNBOOK]` render, empty (no section).
- +16 tests (`tests/test_runbook.py`). Total: 176 passing.

## What's new in v5.9.8

- **Compliance Mapping (P2-8)** -- CWE -> concrete standard controls. Extends `compliance_flags` (list[str]) with `compliance_controls` (dict) and `compliance_standards` (sorted list).
  Audit trail now includes:
  - `compliance_controls: {PCI-DSS: [Req 6.5.1], GDPR: [Art. 32], ...}`
  - `compliance_standards: [ISO27001, PCI-DSS, SOC2]`
  Backward compatible: `compliance_flags` preserved.
- **`patterns.py`:** added `COMPLIANCE_MAP` -- CWE -> controls for 5 standards: PCI-DSS 3.2.1 (Req 6.5.x), GDPR (Art. 32), SOC 2 (CC6.x, CC7.x), ISO/IEC 27001 (A.10.x, A.14.x), HIPAA (164.312.x).
- **`src/tools/compliance.py`** (new): `map_compliance()`, `enrich_compliance()`. Deterministic (dict-lookup), fail-open.
- **Dogfood:** 3 cases -- SQLi (CWE-89 -> PCI Req 6.5.1 + SOC2 CC6.1 + ISO A.14.2.5), SQLi+XSS (multiple controls), full coverage (5 standards in one query).
- +15 tests (`tests/test_compliance.py`). Total: 160 passing.

## What's new in v5.9.7

- **Reachability (P2-7)** -- line-level taint path (entry_point -> source -> sink). Extends `detect_exploitability()` (boolean) with `path` and `source_count`.
  Audit trail now includes:
  - `exploitability_source_count: N`
  - `exploitability_path: [{"line": L, "type": "...", "content": "..."}, ...]`
  Backward compatible: all old fields preserved.
- **`patterns.py`:** added Go (`func main`, `http.HandleFunc`) and JS (`app.get`, `router.post`) entry points. Added `TAINT_SOURCES` and `TAINT_SINKS` regex dicts.
- **`src/tools/reachability.py`** (new): `find_entry_points()`, `find_taint_sources()`, `find_taint_sinks()`, `trace_taint()`, `enrich_exploitability()`. Deterministic (regex + line-based), fail-open.
- **Dogfood:** Flask demo (`@app.route` + `request.args` + `cursor.execute`) produced a full path with line numbers: `[{line: 9, entry_point}, {line: 11, source}, {line: 14, sink}]`.
- **Known limitations:** detects **explicit** taint sources (`request.args`, `input(`) and entry points (`@app.route`, `if __name__`). Does **not** detect implicit sources (function arguments) or flow through intermediate variables/files -- planned for P2-7b.
- +20 tests (`tests/test_patterns.py`, `tests/test_reachability.py`). Total: 145 passing.

## What's new in v5.9.6

- **Fix:** diff-aware skip-path (`--diff` / `--changed-only`) no longer
  produces a false PASS in CI when `--gate` is active. Skip now returns
  exit code **3** (SKIPPED) instead of 0 -- CI can decide fail-closed
  or ignore. Bug found via inter-file dogfood (RN-8/T-8).
- **Exit codes (final):**
  - `0` -- gate passed / analyze ok
  - `1` -- gate failed
  - `2` -- internal error
  - `3` -- skipped (file unchanged + `--gate`)
- **GitHub Action:** gate step now treats exit 3 as `[gate] skip`.

## What was new in v5.9.5

- **Inter-file analysis** (`--context-root DIR`) -- Stage 2 now receives
  imported modules as context. LLM can trace data flow across files
  (taint analysis), reducing false positives. See
  [Inter-file analysis](#inter-file-analysis-v595) below.
- **Dogfood:** on `src/cli.py --context-root src/`, LLM detected cross-file
  risks (RN-8, T-8: skip-path ignores --gate -> false PASS in CI).
- +17 tests (`tests/test_deps.py`). Total: 125 passing.

## What was new in v5.9.4

- **Quality Gates** (`--gate` / `--config PATH`) -- CI gate with exit codes:
  0 = pass, 1 = fail (thresholds exceeded), 2 = error. Config in `.vishap.yml`
  (thresholds, ignore rules/paths, fail_on_reachable). See
  [Quality Gates](#quality-gates-v594) below.
- **Fix:** Windows `UnicodeEncodeError` on cp1251 console -- stdout/stderr
  reconfigured to UTF-8 with `errors=replace`.
- **GitHub Action:** added quality gate step (`vishap analyze --gate`).
- +15 tests (`tests/test_quality_gate.py`). Total: 108 passing.

## What was new in v5.9.3

- **SARIF 2.1.0 output** for GitHub Code Scanning (`analyze --sarif PATH`).
  Stage 2 risk nodes are now emitted as SARIF `vishap/risk/*` rules with
  `partialFingerprints` (GitHub tracks same finding moved across lines).
- **GitHub Action** (`.github/workflows/vishap.yml`) -- diff-aware scan on
  PR/push with `upload-sarif@v3` + SBOM artifact.
- +9 tests (`tests/test_sarif.py`). Total: 93 passing.

## What was new in v5.9.2

- **SBOM generation** (`vishap sbom` / `analyze --sbom PATH`) -- CycloneDX 1.6
  Software Bill of Materials. Full dependency graph from venv, compatible
  with Dependency-Track, GitHub Dependency Graph, Snyk. See [SBOM](#sbom-v592)
  below.
- **CLI:** `vishap sbom --output sbom.json --source environment`
- **CLI:** `vishap analyze <file> --sbom sbom.json` -- SBOM alongside analysis.
- +14 tests (`tests/test_sbom.py`). Total: 84 passing.

## What was new in v5.9.1

- **Diff-aware scan** (`--diff REF` / `--changed-only`) -- analyze only files
  changed since a git ref (or uncommitted). CI-friendly: skips unchanged files.
  See [Diff-aware scan](#diff-aware-scan-v591) below.
  +15 tests (`tests/test_diff.py`). Total: 70 passing.

## What was new in v5.9

- **Baseline** (`--save-baseline` / `--baseline`) -- fingerprint-based suppression
  of known findings in CI. Save once, report only new findings on subsequent runs.
  See [Baseline](#baseline-v590) below.
- **Fix:** `stage4.collision` as list no longer crashes audit trail
  (`_safe_escalation_note` helper).
- **Fix:** audit-trail `[BASELINE]` block placement in sync + async pipelines.
- **Infra:** `.gitignore` root-only patterns for temporary scripts
  (`/test_*.py`, `/fix_*.py`, `/patch_*.py`) -- prevents shadowing `tests/`.
- **Infra:** `.gitignore` ignores `.vishap-baseline.json`.
- **Tests:** 55 passing (was 41) -- +14 baseline tests.

## What was new in v5.8

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

cd /path/to/vishap

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

vishap/

├── vishap/                 # V5.9 prompts (660+ lines)

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

- **Tests** — 465 (`tests/`). Run: `python run_tests.py`.
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

Vishap V5.8 was validated on 5 real open-source projects. See [docs/case-studies](docs/case-studies/) for detailed findings:

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

Vishap analyzes **not only code**: logs, configs, specs, incidents.

| Material | Type | Level | Cost | Key findings |
|----------|------|-------|------|--------------|
| [incident.log](docs/case-studies/multi/incident-log-pool-exhaustion.md) | logs | D1 | $0.0055 | DB pool cascade, SLO 18x |
| [k8s_insecure.yaml](docs/case-studies/multi/k8s-insecure-config.md) | config | D2 | $0 | EMERGENCY: real `sk_live_...` |
| [payment_spec.md](docs/case-studies/multi/payment-spec-review.md) | spec | D2 | $0.0068 | Resilience 2/10, PCI-DSS violation |

See [docs/case-studies/multi/](docs/case-studies/multi/) for full reports.


### Own Cases — False Positive Rate

6 intentionally vulnerable files (6 languages, 24 bugs planted).
Vishap found **52** issues, **0** false positives.

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

### Comparison - Vishap vs Raw Prompt

| Case | Focus | Link |
|------|-------|------|
| Vishap vs Raw Prompt | Metadata validity | [->](docs/case-studies/comparison/vishap-vs-raw-prompt.md) |
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

    sudo cp deploy/systemd/vishap.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now vishap

See [deploy/README.md](deploy/README.md) for details.

---
## Author



David — 2026


## Anomaly Detection (v5.10.4)

Statistical outlier detection in numeric series. Complements the LLM pipeline with deterministic math -- finds anomalies that LLM cannot quantify ("5000ms is 100x the baseline").

### 3 Methods

**z-score** (default):

    z = (x - mean) / std
    Anomaly if |z| > 3.0

**IQR** (robust to outliers):

    Q1, Q3 = 25th, 75th percentile
    IQR = Q3 - Q1
    Anomaly if x < Q1 - 1.5*IQR or x > Q3 + 1.5*IQR

**EWMA** (catches trends):

    EWMA_t = alpha * x_t + (1-alpha) * EWMA_{t-1}
    Anomaly if |x_t - EWMA_{t-1}| > 3*std

### In `[AUDIT_TRAIL]`

    anomaly_verdict: ANOMALIES_FOUND
    anomaly_count: 1
    anomaly_method: zscore
    anomaly_top: [{"index": 20, "value": 5000.0, "score": 4.364, "reason": "z-score 4.36 > 3.0"}]

### Scope

**In scope:**
- Numeric series in material: logs (`latency=50ms`), metrics (`error_rate: 0.5`), CSV.
- Timestamps filtered out (`2026-10-14`, `14:32:00`).
- Three methods with configurable thresholds.
- Fail-open: insufficient data (< 10 samples) returns `INSUFFICIENT_DATA`.

**Not in scope (v5.10.4):**
- Multi-variate anomalies (correlation between metrics).
- Streaming / online detection.
- Domain-specific thresholds (auto-tuning).
- Non-numeric anomaly detection (text, logs semantic).

### Implementation

- `src/tools/anomaly.py` -- `parse_numbers()`, `detect_anomaly()`, `enrich_anomaly()`. Deterministic (stdlib `statistics`, `re`). Fail-open.
- `patterns.py` -- `ANOMALY_CONFIG` (min_samples=10, max_anomalies=20, top_in_audit=3, methods config).
- `orchestrator.py` -- `anomaly_*` fields in audit trail, alongside `dataflow_*`, `exploitability_*`.
- 17 tests (`tests/test_anomaly.py`).

## LLM Providers (v5.10.1)

Vishap works with **any OpenAI-compatible API** -- cloud, self-hosted, or local.

### Configuration

Set `VISHAP_LLM_PROVIDER` and provider-specific env vars.

**Groq (fast, free tier):**

```bash
VISHAP_LLM_PROVIDER=custom
CUSTOM_API_KEY=gsk_...
CUSTOM_BASE_URL=https://api.groq.com/openai/v1
CUSTOM_MODEL=llama-3.3-70b-versatile
```

**LM Studio (local GUI):**

```bash
VISHAP_LLM_PROVIDER=custom
CUSTOM_API_KEY=not-needed
CUSTOM_BASE_URL=http://localhost:1234/v1
CUSTOM_MODEL=local-model
```

**vLLM (local server):**

```bash
VISHAP_LLM_PROVIDER=custom
CUSTOM_API_KEY=not-needed
CUSTOM_BASE_URL=http://localhost:8000/v1
CUSTOM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**OpenAI:**

```bash
VISHAP_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**DeepSeek (existing, default):**

```bash
DEEPSEEK_API_KEY=sk-...
# VISHAP_LLM_PROVIDER=auto (default)
```

### Auto-detection

When `VISHAP_LLM_PROVIDER=auto` (default), Vishap picks the first available provider:

```
custom (CUSTOM_BASE_URL set) -> openai (OPENAI_API_KEY set) -> deepseek (DEEPSEEK_API_KEY set) -> ollama (default)
```

Legacy `mode=local/cloud/auto` still works as an alias (`cloud` -> deepseek, `local` -> ollama).

### Diagnostics

```python
from src.llm.client import current_provider
print(current_provider())
```

## Runbook Generation (v5.9.9)

Incident response steps per CWE (actionable).

In `[AUDIT_TRAIL]`:

```
runbook_cwes: [CWE-22, CWE-89, CWE-352]
runbook_steps_count: 21
```

In the Markdown report (after `[COMPLETENESS]`):

```
[RUNBOOK]

## CWE-89 — SQL Injection (critical)

**IMMEDIATE (0-1h):**
  1. Block the endpoint (feature flag / WAF rule).
  2. Check DB logs for anomalous queries (last 24h).
  3. Notify on-call security engineer.

**SHORT-TERM (1-3 days):**
  1. Replace string concatenation with parameterized queries.
  ...

**LONG-TERM (1-4 weeks):**
  1. Migrate to ORM (SQLAlchemy / Django ORM).
  ...

**ESCALATION:** Security team + DBA
```

**Coverage (10 CWEs):** SQLi, XSS, OS Command Injection, CSRF, Path Traversal, Insecure Deserialization, XXE, Improper Auth, Insufficient Logging, Missing Encryption.

**Note:** `[RUNBOOK]` section is omitted when no CWE is detected (fail-quiet).

## Compliance Mapping (v5.9.8)

CWE -> concrete standard controls (PCI-DSS, GDPR, SOC 2, ISO 27001, HIPAA).

In `[AUDIT_TRAIL]`:

```
compliance_flags: ['PCI-DSS']
compliance_controls: {'PCI-DSS': ['Req 6.5.1'], 'SOC2': ['CC6.1'], 'ISO27001': ['A.14.2.5']}
compliance_standards: ['ISO27001', 'PCI-DSS', 'SOC2']
```

**Mapping (sample):**

| CWE | PCI-DSS | GDPR | SOC 2 | ISO 27001 | HIPAA |
|---|---|---|---|---|---|
| CWE-89 (SQLi) | Req 6.5.1 | -- | CC6.1 | A.14.2.5 | -- |
| CWE-79 (XSS) | Req 6.5.7 | -- | CC6.1 | A.14.2.5 | -- |
| CWE-78 (OS Cmd) | Req 6.5.1 | -- | -- | -- | -- |
| CWE-311 (No Encrypt) | -- | Art. 32 | -- | A.10.1.1 | 164.312(a)(2)(iv) |
| CWE-778 (No Logging) | -- | -- | CC7.2 | -- | -- |

**Note:** Compliance mapping only triggers when CWE IDs are detected by the pipeline. If `cwe_ids` is empty, `compliance_controls` will be `{}`.

## Reachability (v5.9.7)

Line-level taint path from entry point to sink.

```bash
vishap analyze src/api.py --context-root src/
```

In `[AUDIT_TRAIL]`:

```
exploitability_reachable: True
exploitability_auth_required: False
exploitability_blast_radius: medium
exploitability_source_count: 1
exploitability_path: [{"line": 9, "type": "entry_point", "content": "@app.route('/user')"},
                      {"line": 11, "type": "source", "content": "email = request.args.get('email')"},
                      {"line": 14, "type": "sink", "content": "cursor.execute(...)"}]
```

**Scope:** explicit sources (`request.args`, `request.form`, `input(`,
`sys.argv`, `os.environ`) and entry points (`@app.route`, `if __name__`,
`func main`, `http.HandleFunc`, `app.get`). **Not** in scope: implicit
sources (function arguments), flow through intermediate variables/files.

## Inter-file analysis (v5.9.5)

Analyze a target file together with its imported modules. Stage 2 receives
related files as context -- LLM can trace data flow across files (taint
analysis from entry point to sink) and detect cross-file risks.

    vishap analyze src/api.py --context-root src/

The pipeline builds an import graph (AST), resolves dependencies up to
depth 2, and passes the relevant files to Stage 2 as context.

### How it works

1. `src/tools/deps.py` scans `--context-root` via AST.
2. Builds `{file: [imports]}` graph, filtering stdlib.
3. BFS-resolves dependencies up to depth 2 (default).
4. Collects contents, capped at 10 files and 10 KB each.
5. Stage 2 receives them in a dedicated `## Related files (import context)`
   prompt section.

### Security caps

- `max_files=10` -- prevent prompt bloat.
- `max_file_bytes=10000` -- truncate each file.
- Stdlib imports (`os`, `sys`, ...) filtered out.
- Circular imports handled (visited set).

### Output

    [Inter-file] 6 related files

### Implementation

- `src/tools/deps.py` -- `find_imports()`, `build_import_graph()`,
  `resolve_dependencies()`, `collect_context_files()`.
- CLI: `vishap analyze <file> --context-root DIR`.
- 17 tests (`tests/test_deps.py`).

---

## Quality Gates (v5.9.4)

Gate CI builds on critical findings only. Non-critical findings still appear
in the report but do not fail the build.

    vishap analyze src/file.py --gate
    # exit 0 = pass, exit 1 = fail, exit 2 = error, exit 3 = skipped

### Configuration

Copy `.vishap.yml.example` to `.vishap.yml` in your project root:

    quality_gate:
      fail_on: [critical]
      warn_on: [high, medium]
      ignore: [low, info]
      ignore_rules: [CWE-79]
      ignore_paths: [tests/, examples/]
      max_critical: 0
      max_high: 10
      fail_on_reachable: false

### Severity mapping

- критично / critical -> critical
- важно / high -> high
- опционально / medium -> medium
- anything else -> low

### Output

    gate:          PASSED (critical=0, high=3, total=11, ignored=2)
    # or
    gate:          FAILED
      - critical: 6 > max 0

### Implementation

- `src/tools/quality_gate.py` -- `load_quality_gate(path)`,
  `evaluate_gate(findings, config, reachable=False)`, `normalize_priority(s)`.
- CLI: `vishap analyze <file> --gate [--config PATH]`.
- 15 tests (`tests/test_quality_gate.py`).

---

## SARIF + GitHub Code Scanning (v5.9.3)

Vishap emits SARIF 2.1.0 findings compatible with GitHub Code Scanning,
Azure DevOps, and IDE SARIF viewers.

    vishap analyze src/file.py --sarif out.sarif

Each Stage 2 risk node is emitted as a SARIF rule (`vishap/risk/<slug>`) with:

- `partialFingerprints.vishapFingerprint/v1` -- stable 16-char fingerprint,
  shared with `--baseline` (GitHub tracks same finding across line shifts).
- Severity mapped: критично/high -> error, важно/medium -> warning,
  опционально/low -> note.
- Audit metadata (audit_id, material_hash, risk_verdict) in `runs[].properties.vishap`.

### GitHub Action

`.github/workflows/vishap.yml` runs on every PR/push:

1. checkout (fetch-depth: 0)
2. setup Python 3.12
3. pip install git+https://github.com/dvddv9/vishap.git cyclonedx-bom
4. **diff-aware scan** -- only changed files are analyzed
5. `upload-sarif@v3` with `category: vishap`
6. SBOM uploaded as artifact

Findings appear inline in the PR (Code Scanning annotations).

Implementation:

- `src/tools/sarif.py` -- `to_sarif(audit, sast_result, sca_result, source_file, risk_nodes)`.
- CLI: `vishap analyze <file> --sarif PATH`.
- 9 tests (`tests/test_sarif.py`).

---

## SBOM (v5.9.2)

Generate a CycloneDX Software Bill of Materials (CycloneDX 1.6 JSON).
Full dependency graph from the current Python environment -- compatible with
Dependency-Track, GitHub Dependency Graph, Snyk, and any CycloneDX-aware tool.

    # Standalone command (default source: environment)
    vishap sbom --output sbom.json

    # Alternative sources
    vishap sbom --source requirements --output sbom.json
    vishap sbom --source poetry --output sbom.json

    # Alongside analysis
    vishap analyze src/file.py --sbom sbom.json

Output example:

    SBOM written: sbom.json
      format:       CycloneDX
      spec version: 1.6
      components:   168
      serial:       urn:uuid:f225c8d8-f98b-4b33-b429-715eee79170a

Implementation:

- `src/tools/sbom.py` -- `generate_sbom(output_path, source)`, `parse_sbom(sbom)`,
  `is_cyclonedx_available()`.
  Wraps `cyclonedx-py` CLI. Tolerant to missing tool / errors -- never raises.
- CLI: `vishap sbom` subcommand + `--sbom PATH` flag for `analyze`.
- 14 tests (`tests/test_sbom.py`).

Requires: `cyclonedx-bom>=7.0.0` (installed automatically as a dependency).

---

## Diff-aware scan (v5.9.1)

Analyze only files changed since a git ref (or uncommitted). Ideal for CI --
skips unchanged files, so a 1000-file repo with 1 change runs in seconds.

    # Files changed since origin/main
    vishap analyze path/to/file.py --diff origin/main

    # Files with uncommitted changes
    vishap analyze path/to/file.py --changed-only

If the input file is unchanged, the pipeline exits with code 0 and prints:

    [Diff] path/to/file.py not changed since origin/main -- skip

This is intentional: in CI, unchanged files must not fail the build.

Implementation:

- `src/tools/diff.py` -- `get_changed_files(ref)`, `get_uncommitted_files()`,
  `get_changed_files_pr()`, `is_changed()`.
- CLI flags: `--diff REF`, `--changed-only`.
- 15 tests (`tests/test_diff.py`).

---

## Baseline (v5.9.0)

Vishap supports fingerprint-based baseline to suppress known findings in CI.

First run - save baseline:
    vishap analyze src/ --save-baseline .vishap-baseline.json

Subsequent runs - report only new findings:
    vishap analyze src/ --baseline .vishap-baseline.json

In the report:

    [BASELINE]
    baseline_used: true
    baseline_new: 0
    baseline_known: 11

### Baseline limitations

- Fingerprint stability depends on LLM determinism. Risk nodes from Stage 2
  are generated by an LLM (DeepSeek), which may rephrase name/note between runs.
  This is a fundamental limitation of baseline on LLM-generated findings.

- Mitigation planned (P0-1b): constrain the Stage 2 prompt to emit a stable
  category / rule_id from a fixed taxonomy (idempotency, sharding, gdpr).
  Then fingerprints become filename | category | priority - stable.

- Fingerprint components: filename | name | priority | note[:100],
  normalized (lowercase, whitespace collapsed). IDs are intentionally ignored.

- Baseline file format: JSON, versioned (v1.0), git-friendly.


## License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

- ✅ Free to use, modify, and distribute
- ✅ SaaS use allowed — but if you offer it as a network service, you must release your source code under AGPL
- ❌ Cannot be taken closed-source

See [LICENSE](LICENSE) for full text.


## Test Suite

**465 tests passing** across 35 files:

| File | Tests |
|---|---|
| tests/test_anomaly.py | 17 |
| tests/test_anomaly_code.py | 5 |
| tests/test_anomaly_density.py | 5 |
| tests/test_api_client.py | 16 |
| tests/test_async_api.py | 20 |
| tests/test_async_imports.py | 4 |
| tests/test_baseline.py | 14 |
| tests/test_compliance.py | 15 |
| tests/test_conftest_data_dir.py | 4 |
| tests/test_dataflow.py | 16 |
| tests/test_deps.py | 17 |
| tests/test_diff.py | 15 |
| tests/test_e2e.py | 3 |
| tests/test_job_store.py | 15 |
| tests/test_jobs_shim_iso.py | 4 |
| tests/test_llm_providers.py | 16 |
| tests/test_patterns.py | 9 |
| tests/test_patterns_c.py | 35 |
| tests/test_patterns_java.py | 41 |
| tests/test_pii_copyright.py | 6 |
| tests/test_pipeline_mock.py | 8 |
| tests/test_quality_gate.py | 15 |
| tests/test_reachability.py | 11 |
| tests/test_risk_verdict.py | 7 |
| tests/test_risk_verdict_security.py | 8 |
| tests/test_runbook.py | 16 |
| tests/test_sarif.py | 9 |
| tests/test_sbom.py | 14 |
| tests/test_security_md.py | 5 |
| tests/test_tools.py | 33 |
| tests/test_ui_async.py | 19 |
| tests/test_ui_badge_version.py | 2 |
| tests/test_ui_headers.py | 13 |
| tests/test_verdict.py | 26 |
| tests/test_version_sync.py | 2 |

Run:

```bash
python run_tests.py
```

## Contributors

- **dvddv9** — creator, maintainer ([@dvddv9](https://github.com/dvddv9))
