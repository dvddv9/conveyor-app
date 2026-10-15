# HANDOFF: Vishap v5.10.6

**Дата:** 2026-10-14
**От:** senior-разработчик (сессия 3)
**Кому:** следующий senior-разработчик

## Состояние

- **Версия:** v5.10.6
- **HEAD:** 7c9c48a
- **Тесты:** 252 passing (было 197)
- **Все платформы:** GitHub + PyPI + Docker Hub = 5.10.6

## 5 релизов за сессию

| Релиз | Что | Тесты |
|---|---|---|
| v5.10.2 | P2-7b AST data-flow | 213 |
| v5.10.3 | Test Suite sync | 213 |
| v5.10.4 | P2-12 Anomaly detection | 230 |
| v5.10.5 | Fix: async import + UI X-API-Key + compose env | 240 |
| v5.10.6 | Fix: risk_verdict + anomaly density | 252 |

## 6 багов dogfood

1. async_stages MAX_TOKENS_STAGE4 (v5.10.5)
2. UI missing X-API-Key (v5.10.5)
3. compose missing CONVEYOR_API_KEY (v5.10.5)
4. risk_verdict ignores risk_nodes (v5.10.6)
5. anomaly on non-numeric code (v5.10.6)
6. Test Suite stale (v5.10.3)

## Что дальше

### v5.11 -- Java/C паттерны
P2-7 regex не работает на Java/C. Добавить:
- request.getParameter, request.getHeader
- Runtime.exec, ProcessBuilder
- new File, FileInputStream

### v5.11.1 -- DONE (2026-10-15)
risk_verdict + security section -- реализовано.
- orchestrator.py: scan both risk_nodes AND security.findings

### v5.11.2 -- DONE (2026-10-15)
Refactor: consolidate risk verdict into verdict.py.
- src/pipeline/verdict.py (new): compute_risk_verdict()
- tests/test_verdict.py (new): 26 tests
- orchestrator.py: -45 lines, calls compute_risk_verdict()
- 297 passing (was 271)

### v5.11.3 -- DONE (2026-10-15)
UI api_client.py -- centralized HTTP client.
- src/ui/api_client.py (new): get()/post()/_url()
- src/config.py: +API_URL, CONVEYOR_API_KEY, API_TIMEOUT_*
- src/ui/streamlit_app.py: 8 calls refactored, removed requests/os
- tests/test_api_client.py (new): 16 tests
- tests/test_ui_headers.py: rewritten (13 tests)
- 320 passing (was 297)

### v5.11.4 -- TODO
anomaly: is_numeric_context() -- единый предикат вместо density+std-ratio guard'ов.
Оценка: 0.5 дня.

### v5.11.5 -- DONE (2026-10-15)
P2-7 Java taint patterns.
- patterns.py: TAINT_SOURCES["source_java"], TAINT_SINKS["sink_java_*"]
- patterns.py: EXPLOIT_PATTERNS["entrypoint_java_*"]
- reachability.py: _LANG_ENTRYPOINTS["java"], _is_comment_line()
- tests/test_patterns_java.py (new): 41 tests
- 361 passing (was 320)
- Dogfood: ServletSqli.java path = doGet -> getParameter -> createStatement
- Known limitation: DbConnection.java (source via method arg) -> path empty

### v5.11.6 -- DONE (2026-10-15)
P2-7 C taint patterns.
- patterns.py: TAINT_SOURCES["source_c"], TAINT_SINKS["sink_c_*"]
- patterns.py: EXPLOIT_PATTERNS["entrypoint_c_main|jni"], blast_c_*
- patterns.py: detect_exploitability -- extended blast for c_cmd/c_buffer/c_file
- reachability.py: _LANG_ENTRYPOINTS["c"], trace_taint + "c"
- tests/test_patterns_c.py (new): 35 tests
- 396 passing (was 361)
- Dogfood: c_cmd_injection.c path = main -> argv[1] -> strcpy -> system
- Known limitation: cwe122 (heap logic bug, not taint flow) -- correctly skipped

### v5.11.7 -- TODO
Java AST (P2-7b) -- JavaParser. Оценка: 2-3 дня.
Проблема: DbConnection.java (source via method arg) -> path empty.
Решение: Java AST -- аналог Python AST (dataflow.py).

### v6.0.0 -- DONE (2026-10-15)
Async API -- job-based analysis.
- src/api/jobs.py (new): in-memory job store, thread-safe
- src/main.py: POST /analyze/async, GET /status/{job_id}, GET /report/{job_id}
- BackgroundTasks -- pipeline runs in background
- tests/test_async_api.py (new): 20 tests
- 416 passing (was 396)
- Dogfood: full end-to-end (POST -> poll 42s -> report)

### v6.0.1 -- DONE (2026-10-15)
UI: async analysis, LLM mode sidebar, dataflow rendering, custom theme.
- src/ui/streamlit_app.py: header + CSS, sidebar mode, async button, dataflow expander
- tests/test_ui_async.py (new): 19 tests
- 435 passing (was 416)
- Async UI works end-to-end (34k chars, 42s)

### v6.0.2 -- DONE (2026-10-16)

Bugfix: test isolation + version test drift.

**Fixed:**
- `tests/test_ui_async.py::test_ui_has_v6_version` -- now reads version from
  `pyproject.toml` via `tomllib`, resilient to future bumps (was hardcoded
  V6.0.0, drifted at v6.0.1).
- `tests/conftest.py` -- sets `VISHAP_DATA_DIR` to a session-scoped tmp dir
  via `pytest_configure` hook, BEFORE collection. Fixes PermissionError on
  Windows: tests wrote audit files to `~/.vishap/data` (outside workspace,
  blocked by Defender / sandbox / file locks).

**Real test count:** 456 passed, 0 failed (handoff previously claimed 435).

**New test file:** `tests/test_conftest_data_dir.py` (4 tests).

**Note:** `run_tests.py` uses `subprocess.run([...])` without `env=`; it
inherits the parent env. `conftest.py` works because `pytest_configure`
runs before collection, not because env is propagated.

---

### v6.1 -- TODO
PostgreSQL + Observability + Security. Оценка: 1 неделя.
- Replace in-memory job store with PostgreSQL
- Multi-tenant schema (tenant_id)
- Structured logging + token counters
- /metrics endpoint (Prometheus)
- Secret encryption

### v6.2 -- TODO
UI (Next.js) + Auth (Clerk) + Docs (Docusaurus). Оценка: 1.5 недели.

### v6.3 -- TODO
GitHub App + Billing (Stripe). Оценка: 1 неделя.

### v5.11.7 -- TODO (deferred)
Java AST (P2-7b) via javalang. Оценка: 2-3 дня.

### v5.11.4 -- TODO
anomaly: is_numeric_context() -- единый предикат вместо density+std-ratio guard'ов.
Оценка: 0.5 дня.

### v5.11.5 -- TODO
Java/C patterns для P2-7 (regex). Оценка: 2-3 дня.
### v6.0 -- React UI + Multi-tenant
Streamlit заменить на React. 1-2 недели.

## Грабли (10-16)

10. Anchor без отступа -> IndentationError. ВСЕГДА ast.parse сразу.
11. Не копировать git diff в консоль (PowerShell выполнит).
12. docker compose up -d не пересоздаёт. Нужен --force-recreate.
13. ,, двойная запятая в regex-патче.
14. "test_X.py" in src != в таблице. Проверять точный формат.
15. \\n в heredoc строке -> SyntaxError. Использовать конкатенацию.
16. Inline python -c в PowerShell съедает кавычки. Всегда через .py файл.

## Ключи

Ротированы 2026-10-14:
- DeepSeek: .env
- PyPI: ~/.pypirc
- Docker Hub: docker login -u dvddv9

## Запуск

    cd C:\AI\conveyor_app
    .\.venv\Scripts\Activate.ps1
    python run_tests.py
    python -m src.cli analyze file.py
    python -m src.main
    docker compose up -d

## Case study

docs/case-studies/dogfood/RequestFilter-java/
- Реальный Sakai Java код.
- D3, $0.008, 11 risk_nodes (3 critical).
- Триггер для v5.10.5 + v5.10.6.

## Философия

1. Dogfood на каждой фиче.
2. Test-first.
3. Идемпотентные патчи (SKIP не ERROR).
4. Fail-open для новых фич.
5. Не копить расхождение платформ.
6. Case study на сложных кейсах.

Удачи! 252 теста -- не сломай.
