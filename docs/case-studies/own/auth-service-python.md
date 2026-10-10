# Case Study: Auth Service (Python) — SQLi, Timing Attack, MD5

**Language:** Python
**Level:** D2
**Cost:** $0.006282
**Verdict:** SAFE
**Session:** sess-2026-10-10-152757
**Bugs planted:** 4 — SQL injection, Timing attack, MD5 без salt, No rate limit
**Bugs found:** 7
**False positives:** 0

**Key findings:** SQLi через f-string, MD5 без salt (мгновенный крак), reset_password без authz (account takeover). Комбинация SQLi + MD5 = утечка паролей в открытом виде. Resilience 2/10.

---

## Conveyor Output

# Auth Service Review — EMERGENCY

[ECHO] Python auth service (~35 строк): `check_password` + `reset_password`, SQLite `users.db`, MD5, f-string SQL. Уровень D2, но `EMERGENCY_INTERRUPT` (SQLi + broken crypto + missing authz) переопределяет маршрут. Stage4: `force_emergency: true`, `return_to_stage2: true` (2 критичных конфликта).

[ROUTE] stage0 → stage2 → stage4 → stage5 (transmitter). stage3 пропущен (emergency). `return_to_stage2` зафиксирован, но не выполнен — материал исчерпан, контекст вызывающего отсутствует.

[CONCLUSION] Сервис в проде с тремя независимо достаточными критическими уязвимостями: SQLi в `check_password` (обход аутентификации), MD5 без salt (мгновенный крак при утечке), `reset_password` без авторизации (account takeover любого пользователя). Комбинация SQLi + MD5 превращает утечку хешей в утечку паролей в открытом виде. Resilience 2/10. Немедленные действия: заблокировать `reset_password`, параметризовать SQL, включить audit log.

[RISK_NODES]
- **критично** RN-1: SQLi через f-string в `check_password` — точка невозврата `cursor.execute(query)`.
- **критично** RN-2: MD5 без salt — все хеши сломаны, миграция необратима (RN-11).
- **критично** RN-6: `reset_password` без проверки identity — account takeover.
- **критично** RN-11: MD5 → argon2id инвалидирует все хеши; без активных сессий — принудительный сброс.
- **важно** RN-8: нет try/finally — утечка дескрипторов.
- **важно** RN-10: TOCTOU между SELECT и UPDATE.
- **опционально** RN-7: SQLite contention (нет метрик нагрузки).

[THREAT_MODEL] 3 trust boundary (TB-1 caller→check, TB-2 caller→reset, TB-3 service→db). 10 threats: 5 критично, 4 важно, 1 опционально. Top-3: SEC-4 (E: reset без authz), SEC-1 (S: SQLi), SEC-2 (I: MD5). STRIDE покрыт: S/T/I/D/E/R.

[SILENCE_LAYERS]
- **input_silence**: нет RPS, числа пользователей, размера БД, SLA → невозможно оценить SQLite-контеншн и стоимость.
- **assumption_silence**: «вызывающий `reset_password` авторизован» — неявно, не проверено, ложно по умолчанию.
- **consequence_silence**: при утечке БД все пароли восстановимы; необратимо (переиспользование паролей).

[INTERSECTION_RISKS]
1. SQLi + MD5 → утечка хешей = утечка паролей в открытом виде.
2. reset без authz + нет audit → account takeover без форензики.
3. timing attack + нет rate limit → статистически значимый timing-анализ возможен.
4. SQLite + TOCTOU → недетерминированное поведение под нагрузкой.
5. MD5→argon2 миграция + нет audit → невозможно доказать, какие аккаунты скомпрометированы.

[ASSEMBLY] Плоские функции без слоёв. Core (`check_password`, `reset_password`) напрямую обращаются к infra (`sqlite3`, `hashlib`) без service/repository. Граф зависимостей — дерево, циклов нет. Критический путь: `caller → reset_password → users.db (UPDATE)`.

[REFACTORING] Три опции:
- **A (hotfix in place)**: параметризация, argon2id + rehash-on-login, `hmac.compare_digest`, `actor_id` в reset, try/finally, audit. Дни. SQLite остаётся bottleneck.
- **B (layered refactor)**: repository + service + policy (PasswordPolicy, RateLimiter, AuditLogger). Недели. Тестируемость, замена хранилища без правки core.
- **C (lockdown + rebuild)**: feature flag off на reset, hotfix SQLi, миграция на managed Postgres + argon2id + pepper + rate limit на gateway, принудительный сброс. Высокий риск (UX-удар), но устраняет account takeover немедленно.

[PARALLELS] Паттерн «ревью проведено, дефекты зафиксированы, не исправлены» (комментарии BUG 1/2/3) — классический tech-debt-паралич. Аналогия: auth-сервис без identity-слоя = «проверка пароля без пользователя». MD5 в 2025 — эквивалент plaintext.

[TESTS] Coverage 0%. Отсутствуют edge-cases: SQLi-payload, пустой password, несуществующий username, конкурентные reset, `new_password == username`, длина 0/1/10000, SQLite locked. Для auth-сервиса — критично.

[ACTION]
- **NOW**: заблокировать внешний доступ к `reset_password` (feature flag). Параметризовать SQL (1 строка). Включить audit log на reset.
- **TODAY**: `hmac.compare_digest`, try/finally, `timeout=10.0` в `sqlite3.connect`.
- **TOMORROW**: argon2id + rehash-on-login, `actor_id` обязателен, PasswordPolicy, RateLimiter.
- **LATER**: миграция на Postgres, SLO, on-call, observability.

[QUESTIONS]
1. Кто вызывает `reset_password` и как проверяется право на сброс? (критично — блокирует выбор A/B/C)
2. RPS, число пользователей, размер `users.db`, SLA? (критично — блокирует планирование миграции)
3. Права файла `users.db` в проде? (TB-3, VERIFY)
4. Есть ли активные сессии пользователей для rehash-on-login?

[FUNC:FULL]
- **ECON**: effort ~2–5 дней (Option A) / 2–4 недели (B) / 4–8 недель (C); cost $0 (A) / managed Postgres + gateway (C, оценка невозможна без данных о хостинге); ROI критический — предотвращение account takeover; cost of delay = необратимая компрометация паролей.
- **FAIL**: критично — `cursor.execute(query)` (SQLi, точка невозврата), `reset_password` без authz (takeover), `hashlib.md5` (все хеши сломаны); cascade: SQLi → выгрузка хешей → MD5-крак → пароли в открытом виде; recovery: параметризация + argon2id + принудительный сброс (необратимо).
- **METRICS**: ~35 строк, 2 функции, 2 stdlib-зависимости, 0 тестов (coverage 0%), 0 метрик/логов/трейсинга, resilience 2/10, 7 уязвимостей (3 критично), 10 threats (5 критично).
- **ALTERNATIVES**: языки — Python (текущий, ок); фреймворки — FastAPI/Flask + passlib (вместо ручного hashlib); БД — Postgres (managed) вместо SQLite; инфра — API gateway с rate limit; паттерны — repository + service + policy (Option B), либо внешний IdP (Option C).
- **EVOLVE**: coupling 2/10 (жёсткая привязка к sqlite3 и схеме users), abstractions 1/10 (нет слоёв, DIP нарушен), growth 2/10 (MFA требует правки обеих функций), friction высокий (дублирование boilerplate, нет DI).
- **COMPARE**: A — дни, $0, средний риск (миграция хешей необратима); B — недели, $0–низкий, средний риск (рефакторинг + миграция одновременно); C — недели, $managed DB, высокий риск (принудительный сброс паролей, UX-удар).

[MANDATORY BASE]
1. **ECONOMICS**: time 2–5 дней (Option A), cost $0 при условии отсутствия managed-инфраструктуры; при Option C — cost не оценён (нет данных о хостинге).
2. **RISKS**: критично — SQLi, MD5, reset без authz; важно — timing, TOCTOU, утечка дескрипторов; при условии, что `reset_password` вызывается из недоверенного контекста — account takeover реализуем.
3. **INFRASTRUCTURE**: pool_size ≥ 50 (рекомендация), при условии смены хранилища на Postgres; для SQLite пул ограничен файловой блокировкой.
4. **CODE**: change ~35 строк (полная переработка), при условии сохранения сигнатур `check_password`/`reset_password` — breaking change только для `reset_password` (добавление `actor_id`).
5. **ACTION**: now — блокировка reset + параметризация SQL; tomorrow — argon2id + audit + rate limit.
6. **TIMELINE**: NOW — feature flag off на reset, hotfix SQLi; TODAY — compare_digest, try/finally, timeout; TOMORROW — argon2id, actor_id, policy; LATER — Postgres, SLO, on-call.
7. **PRODUCTION IMPACT**: users N (неизвестно — input_silence), deploy window не определён, rollback кода N min (не оценён), rollback хешей — невозможен.
8. **SLO IMPACT**: current не определены (0%), after — предложено 99.9% availability / p99 < 100ms / error rate < 0.1%, при условии тюнинга argon2id под p99.
9. **CLOUD COST**: current $N (неизвестно), projected $N (не оценено), delta ±$N — mode_cost не запускался, spec пустой.
10. **ON-CALL**: new alerts — auth_failures > 100/min, reset_password > 10/h, db_lock_errors > 5/min; runbook отсутствует; escalation не определён.

[REFLEXION]
1. Слабое место: `cloud_cost` delta = 0 при Option C (managed Postgres + gateway стоят денег) → исправлено: явно указано «не оценено, mode_cost не запускался», не выдаётся за ноль.
2. Слабое место: `pool_size ≥ 50` без источника → исправлено: помечено как рекомендация с условием смены хранилища; для SQLite пул ограничен файловой блокировкой.
3. Слабое место: `return_to_stage2: true` в stage4 не выполнен → исправлено: зафиксировано в [ROUTE] и [QUESTIONS] как блокирующее уточнение, не скрыто.
Итог: accepted

---

**FALLBACK MODE: Reason: EMERGENCY_INTERRUPT + return_to_stage2 (2 критичных конфликта, контекст вызывающего и метрики отсутствуют).**
[TRIGGER]: force_emergency=true, return_to_stage2=true, input_silence (RPS/пользователи/SLA).
Delivering reduced final: полный D2-набор блоков сохранён, D3/D4-блоки (COMPLEXITY, STRUCTURE, TEXTURE, SHADOWS, SECURITY, TEST_ANALYSIS, DEPENDENCIES, FAILURE_POINTS, EVOLVABILITY, AUTHOR_SOLUTIONS, REFACTORING_PLAN, ECONOMICS, FAILURE_SCENARIO, CONFLICT_RESOLUTION, INVERSION, THRESHOLDS, CONSTRAINTS, SECOND_OPINION, COLLISION, FINAL_METRICS, FINAL_CALCULATIONS, COMPLETENESS_CHECK, GRADUATED_CONCLUSION) не генерируются — уровень D2.

**loss_pct**: не вычислен вручную — требуется `python tools/fallback_check.py --level D2 --present "[ECHO][ROUTE][CONCLUSION][RISK_NODES][ASSEMBLY][REFACTORING][PARALLELS][TESTS][ACTION][QUESTIONS][FUNC:FULL][MANDATORY BASE]"`.

[AUDIT_TRAIL]
audit_id: audit-2026-10-10-c82f99
material_hash: sha256:22eb5cb50542fd29
pii_detected: false
compliance_flags: []
critique_verdict: SAFE


[COMPLETENESS]
level: D2
required: 12
missing: []
loss_pct: 0.0%
verdict: ACCEPTABLE

---

## Reproduce

    conveyor analyze data/real_cases/own/auth_service.py
