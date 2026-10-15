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

### v5.11.2 -- TODO
Java/C patterns для P2-7. Оценка: 2-3 дня.
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
