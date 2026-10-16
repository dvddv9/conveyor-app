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

### v6.0.3 -- DONE (2026-10-16)

Refactor: JobStore abstraction (Protocol + InMemory).

**Added:**
- `src/api/job_store.py` -- `JobStore` Protocol, `Job` frozen dataclass, `JobStatus` enum.
- `src/api/job_store_memory.py` -- `InMemoryJobStore` (thread-safe via RLock).

**Changed:**
- `src/api/jobs.py` -- now a backward-compat shim. Legacy module-level API
  (create_job, get_job, update_job, delete_job, list_jobs, clear_jobs, job_count)
  delegates to a singleton `JobStore` selected via `JOB_STORE` env
  (memory | postgres; postgres -> v6.1).
- `run_tests.py` -- registered `test_job_store.py` and `test_jobs_shim_iso.py`.

**Fixed:**
- `update_job` now converts ISO-string `started_at`/`finished_at` to `datetime`.
  Production bug: `main.py` passes ISO strings; `_job_to_dict` would call
  `.isoformat()` on a `str` -> AttributeError on `/status/{job_id}`.
  Regression tests: `tests/test_jobs_shim_iso.py` (4 tests).

**Tests:**
- `tests/test_job_store.py` (new) -- 15 tests (Protocol-based).
- `tests/test_jobs_shim_iso.py` (new) -- 4 tests.
- Backward compat: `test_async_api.py` still 20/20 (main.py untouched).
- Full run: 458 passed, 0 failed.

**Foundation for v6.1:** PostgresJobStore via `JOB_STORE=postgres` env.

---

## Блочный автономный режим (v6.1+)

### Что это

Начиная с v6.1 (PostgreSQL), работаем в формате "блоков":

- Блок = большая задача (PostgresJobStore, structlog, Prometheus).
- Senior даёт ОДНУ большую инструкцию на блок.
- Harness (AI-исполнитель) выполняет автономно.
- Senior проверяет ОДИН раз в конце.

### Почему

- Меньше итераций (3-4 на v6.1 вместо 15-20).
- Harness показал надёжность (v6.0.2 + v6.0.3 — 3 бага найдены).
- Чёткие границы (DONE / BLOCKED).

### Формат инструкции блока

Senior даёт инструкцию в формате:

1. БЛОК N: <название>
2. ЦЕЛЬ: <что делаем, зачем>
3. ФАЙЛЫ: (Создать / Изменить / НЕ трогать)
4. ЗАВИСИМОСТИ (добавить в requirements.txt)
5. ШАГИ
6. ТЕСТЫ (test-first): файл + N тестов + ключевые проверки
7. КРИТЕРИЙ ГОТОВНОСТИ
8. ОГРАНИЧЕНИЯ

### Формат отчёта Harness

После блока — ОДИН отчёт:

1. Что сделано
2. Файлы (new / changed)
3. Прогоны (pytest X -v -> N passed)
4. Состояние (git status, ast.parse, cleanup)
5. Заблокировано (если есть)
6. Жду: commit (после approval senior)

### Формат BLOCKED

Если Harness не может продолжить:

1. Что не получилось
2. Что пробовал (попытки)
3. Моя гипотеза
4. Что предлагаю (варианты A/B)
5. Что НЕ трогал
6. Жду: решения от senior

### Границы (Harness НЕ делает без команды)

1. НЕ коммитит, НЕ пушит (только локально).
2. НЕ меняет существующие тесты.
3. НЕ удаляет файлы.
4. НЕ меняет архитектуру (Protocol, shim).
5. НЕ добавляет зависимости без явного списка.
6. НЕ трогает .env, docker-compose.yml (кроме указанного).
7. НЕ запускает docker push, git push.
8. Останавливается при любом риске сломать dev-среду.

### Ограничения среды (DSH sandbox)

Harness работает в песочнице DSH и НЕ может:

- Устанавливать зависимости (pip install) — нет сети.
- Запускать Docker / Postgres.
- Делать git push / docker push.
- Писать за пределами workspace.

Что делает senior (на host):

- Устанавливает зависимости.
- Запускает docker compose up / alembic upgrade.
- Integration-тесты (с живым Postgres).
- git push / docker push.

### Что делает senior после DONE

1. Review отчёта (5-10 минут).
2. Проверить ключевые файлы (git diff).
3. Убедиться, что существующие тесты не тронуты.
4. Approve -> Harness делает commit (локально).
5. Push (host).
6. Integration-тесты (host).

### История (v6.1)

- Блок 1 (PostgresJobStore): 3 BLOCKED (pip, greenlet, cleanup) -> DONE.
  16 unit + 5 integration (skipif) + 39 существующих.

---

### Блок 1 -- DONE (2026-10-16)

PostgresJobStore via SQLAlchemy 2.0 async.

**Создано:**
- src/api/job_store_postgres.py -- PostgresJobStore + JobModel (jobs table)
  - 7 async methods: create/get/update/delete/list_jobs/clear/count
  - ISO-string started_at/finished_at -> datetime in update() (v6.0.3-fix repeated)
- alembic.ini, alembic/env.py, alembic/script.py.mako, alembic/versions/001_initial_jobs.py
- tests/test_job_store_postgres.py -- 16 unit tests (mocks)
- tests/test_job_store_postgres_integration.py -- 5 integration (skipif TEST_POSTGRES_URL)

**Изменено:**
- src/api/jobs.py -- get_store() postgres branch imports PostgresJobStore
- docker-compose.yml -- add postgres:16-alpine + postgres_data volume + healthcheck
- .env.example -- add DATABASE_URL, POSTGRES_PASSWORD
- requirements.txt -- sqlalchemy[asyncio]>=2.0.30, asyncpg>=0.29.0, alembic>=1.13.0
- run_tests.py -- register test_job_store_postgres.py

**Схема БД (table jobs):**
- job_id PK (varchar(32))
- status indexed (varchar(16))
- filename (varchar(255))
- created_at, updated_at (timestamptz)
- started_at, finished_at (timestamptz, nullable)
- tenant_id indexed (varchar(64), nullable)
- result (jsonb)
- error (text)

**Тесты:**
- 16 unit passed
- 5 integration passed (с живым Postgres через docker compose + alembic upgrade head)
- Полный прогон: 478 passed + 5 skipped (integration, если нет env) + 3 e2e

**Commit:** 250155f

**Что в работе (v6.1.x):**
- RLS / multi-tenant isolation
- Prometheus /metrics (Блок 3)
- token counters + Fernet (Блок 4)

### Блок 2 -- DONE (2026-10-16)

structlog + JSON logs + Docker fixes.

**Создано:**
- src/observability/__init__.py, logging.py (setup_logging, get_logger, bind_job_id, bind_request_id, clear_context)
- tests/test_logging.py (15 тестов)

**Изменено:**
- src/config.py: LOG_LEVEL, LOG_FORMAT
- src/main.py: setup_logging + HTTP middleware log_requests
- src/api/job_store_memory.py, job_store_postgres.py: log job events
- src/pipeline/orchestrator.py: _timed_stage + stage events
- requirements.txt: +structlog>=24.0.0
- pyproject.toml: +sqlalchemy[asyncio], asyncpg, alembic, structlog (Docker fix)
- .env.example: +LOG_LEVEL, LOG_FORMAT
- run_tests.py: register test_logging.py

**Docker fixes (попутно, все запушены):**
- docker-compose.yml: vishap-ui healthcheck on 8501
- docker-compose.yml: vishap-ui volume vishap_data + VISHAP_DATA_DIR
- pyproject.toml: 4 deps для Docker pip install .
- streamlit_app.py: file_name без .md

**Тесты:**
- test_logging.py: 15 passed
- test_ui_async.py: 20 passed (+1 download test)
- На host: 494 passed (без e2e). Всего collected: 502.

**Commits:**
- 84534c5 feat(observability): structlog + JSON logs (v6.1-block2)
- 9a0ee1d fix(build): add deps to pyproject.toml
- 13f02d7 fix(docker): mount vishap_data in vishap-ui
- 8847edc fix(ui): remove .md from download_button file_name
- 0c47243 docs(readme): bump tests count 486 -> 502

**Что в работе (следующие сессии):**
- Блок 3: Prometheus /metrics (prometheus-client)
- Блок 4: token counters + Fernet

### Блок 3 -- DONE (2026-10-16)

Prometheus /metrics endpoint.

**Создано:**
- src/observability/metrics.py -- единый CollectorRegistry, 4 метрики
  (vishap_jobs_created_total, vishap_jobs_completed_total,
  vishap_job_duration_seconds, vishap_http_requests_total) + helpers.
- tests/test_metrics.py -- 12 тестов (test-first).

**Изменено:**
- src/main.py -- GET /metrics route (text/plain; version=0.0.4)
  + observe_http_request в middleware log_requests.
- src/api/job_store_memory.py -- observe_job_created + observe_job_finished
  (old != new guard).
- src/api/job_store_postgres.py -- то же (symmetry).
- requirements.txt + pyproject.toml -- prometheus-client>=0.20.0 (symmetry).
- run_tests.py -- register test_metrics.py.

**Тесты:**
- 12 new tests (metrics): endpoint, content-type, job counters,
  duration histogram, http counters, format, robustness.
- Полный прогон: 494 -> 506 passed, 5 skipped (integration).
- collected: 502 -> 514.

**Commit:** d2b7561

**Dogfood (2026-10-16):**
- Integration: 5 passed (с живым Postgres).
- /metrics: 200, text/plain; version=0.0.4.
- # HELP / # TYPE для всех 4 метрик.
- Histogram buckets: 1, 5, 10, 30, 60, 300.
- /health: ok.

**Что в работе (v6.1.x):**
- Блок 4: token counters + Fernet (secret encryption).
- RLS / multi-tenant isolation.

### Блок 4 -- DONE (2026-10-16)

LLM token metrics + Fernet encryption.

**Создано:**
- src/security/__init__.py, fernet.py -- encrypt/decrypt/generate_key/is_configured.
- src/llm/_observe.py -- DRY helper observe_llm_result.
- tests/test_fernet.py (8), test_token_metrics.py (6), test_observe.py (6).

**Изменено:**
- src/observability/metrics.py -- +2 метрики: vishap_llm_tokens_total{model, type},
  vishap_llm_requests_total{model, status}.
- src/llm/client.py + async_client.py -- обёртка observe_llm_result
  (6 + 4 вызова + error-path).
- src/config.py + .env.example -- FERNET_KEY.
- requirements.txt + pyproject.toml -- cryptography>=42.0.0 (symmetry).
- run_tests.py -- register 3 файла.

**Тесты:**
- 20 new tests (8 + 6 + 6).
- Full run (host): 531 passed (494 + 12 Block3 + 20 Block4 + 5 integration).

**Commit:** 072a288

**Dogfood (2026-10-16):**
- Fernet: roundtrip OK, type=bytes, len=100, non-deterministic.
- Integration: 5 passed (Postgres).
- Docker: 3 healthy.

**Что в работе (v6.1.x):**
- RLS / multi-tenant isolation.
- CI (GitHub Actions) -- не настроен.

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

## Грабли (10-21)

10. Anchor без отступа -> IndentationError. ВСЕГДА ast.parse сразу.
11. Не копировать git diff в консоль (PowerShell выполнит).
12. docker compose up -d не пересоздаёт. Нужен --force-recreate.
13. ,, двойная запятая в regex-патче.
14. "test_X.py" in src != в таблице. Проверять точный формат.
15. \\n в heredoc строке -> SyntaxError. Использовать конкатенацию.
16. Inline python -c в PowerShell съедает кавычки. Всегда через .py файл.
17. Get-Content .env в чат -> ключи утекли. Только имена:
    (Get-Content .env | Select-String "^KEY=").Line -replace "^KEY=".
18. PowerShell here-string @"..."@ НЕ обрабатывает \" escape.
    В here-string кавычки пишутся как есть.
19. Out-File -Encoding utf8 (PS 5.1) добавляет BOM.
    Через [System.IO.File]::WriteAllText($path, $msg,
    (New-Object System.Text.UTF8Encoding $false)).
20. GitHub UI переводит контент при русском языке профиля.
    Settings -> Appearance -> Language -> English (обязательно).
21. Copilot review может найти реальные фактические проблемы.
    Проверять факт (curl.se/download) -- не игнорировать, не спорить.

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

## Curl PR #23441 (2026-10-16)

Docs: encourage verifying tarball before unpacking.

**История:**
- Issue #23438 -- closed by Daniel Stenberg after AI-slop complaint.
- Second chance via human reply -> PR accepted.
- PR: https://github.com/curl/curl/pull/23441

**Status:**
- Open, awaiting CI approval (first-time contributor, 5 workflows pending).
- Label: `documentation` (auto).
- Files: docs/INSTALL.md, +17.
- Commit: a8aefa1 (no BOM).

**Обновление (2026-10-16, позже):**
- CI: 13/13 success на head 68e6d27.
- Copilot review: finding про sha256sum (curl не публикует .sha256) -- ИСПРАВЛЕНО.
- HEAD SHA: 68e6d27 (был a8aefa1).
- Status: waiting for human review.
- Наш ответ Copilot: "The download page currently publishes only .asc (GPG),
  not .sha256. I removed the sha256sum example."

**Что делать:**
- НЕ комментировать в issue #23438.
- НЕ пинговать Daniel/Stefan.
- Ждать 7 дней. Если тишина -> один вежливый ping в PR.

**LESSONS.md:** записан.

## Философия

1. Dogfood на каждой фиче.
2. Test-first.
3. Идемпотентные патчи (SKIP не ERROR).
4. Fail-open для новых фич.
5. Не копить расхождение платформ.
6. Case study на сложных кейсах.

Удачи! 252 теста -- не сломай.
