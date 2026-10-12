# FAQ - Conveyor V5.7

**Ответы на частые вопросы.**

---

## Почему DeepSeek, а не GPT-4?

**Цена.** DeepSeek - ~$0.007 за анализ. GPT-4 - ~$0.30 за тот же объём. В 40 раз дешевле.

**Качество.** На SARD-кейсах (STONESOUP CWE-129B) DeepSeek находит CWE-129 + CWE-787 + doc/code drift.

**Что если нужен GPT-4:** src/llm/client.py - абстракция. Можно подключить любой OpenAI-совместимый API.

## Почему 6 стадий, а не одна?

**Разделение ответственности:**

| Stage | Роль | Не делает |
|-------|------|-----------|
| 0 Orchestrator | Route, level, task_type | Не анализирует |
| 1 Scanner | 4 слоя, стек | Не находит риски |
| 2 Analyst | Risk nodes, STRIDE | Не пишет отчёт |
| 3 Researcher | Industry parallels | Не синтезирует |
| 4 Synthesizer | Options, refactoring | Не форматирует |
| 5 Transmitter | Markdown | Не анализирует |

**Одна стадия** = смешение всего -> хуже качество, труднее debug.

## Почему AGPL, а не MIT?

**AGPL** - free to use, modify, distribute. **SaaS allowed**, но если Conveyor - network service - нужно открыть source.

**MIT** позволяет closed-source SaaS. Для security-инструмента AGPL - правильнее: transparency.

## Как масштабируется на 1000 файлов?

**Batch mode:** POST /analyze/batch с массивом materials.

**Ограничения:**
- Rate limit: 10 req/min per IP (по умолчанию)
- LLM: 40-90 сек на файл
- Параллелизм: max_concurrent 1..10 (по умолчанию 3)

**1000 файлов x 90 сек / 3 concurrent = ~8 часов.** Для больших объёмов - увеличить max_concurrent или очередь.

## Что если LLM недоступен?

**Retry:** 3 попытки, exponential backoff (2s -> 30s).

**Fallback:** auto mode = DeepSeek cloud + Ollama local fallback.

**Если оба недоступны:** pipeline вернёт ошибку. Audit не создаётся.

**Что делать:** режим local (Ollama) - работает без интернета. Требует GPU/CPU.

## Как обновляется, если появится новый CVE?

**Conveyor не имеет встроенной CVE базы.** Он анализирует код - не сверяет с базой.

**Что делать:**
- Для CVE зависимостей - pip-audit, npm audit, govulncheck отдельно.
- Для CVE в коде - LLM может найти известные паттерны (Log4Shell, OpenSSL).
- Регулярно обновлять: git pull && pip install -r requirements.txt.

## Чем отличается от CodeRabbit / Qodo / Graphite?

| Tool | Что анализирует | Multi-material | Audit trail | Self-hosted |
|------|-----------------|----------------|-------------|-------------|
| CodeRabbit | Code (PR review) | Code only | No | No |
| Qodo | Code | Code only | No | No |
| Graphite | Code (PR stack) | Code only | No | No |
| Snyk | Deps + code (SAST) | Deps + code | Partial | Partial |
| Semgrep | Code (SAST) | Code only | No | Yes |
| **Conveyor** | Code, config, spec, data, logs | **5 types** | **Yes (SHA-256)** | **Yes (AGPL)** |

**Где Conveyor сильнее:** multi-material, audit trail, self-hosted, determinism.

**Где проигрывает:** CI-интеграция (у CodeRabbit/Graphite - готовая), SARIF output, IDE integration.

## Сколько стоит один анализ?

**LLM:** ~$0.007 (DeepSeek). Зависит от длины материала.
**Инфраструктура:** $0 (если локально).
**CI:** $0 (GitHub Actions free tier).

**Сравнение с senior-аналитиком:** $800/день x 1 час = $100 за один ручной анализ. Conveyor - $0.007. **14 000x дешевле.**

## Можно ли использовать локально без интернета?

**Да**, через mode=local (Ollama).

**Требования:** CPU/GPU, ~7B модель (llama3, qwen, deepseek-coder).

**Минусы:** 20-40 минут на файл (CPU). Slow.

**Плюсы:** приватный код не уходит в облако. Для sensitive data.

**Как:** POST /mode -> {"mode": "local"}.

## Что делать, если Conveyor нашёл ложное срабатывание?

**Проверить вручную** - LLM может ошибаться.

**Использовать VERIFY-пометки** - Conveyor явно помечает «не проверено».

**Сравнить с SAST** - если Semgrep/Bandit не подтверждает - вероятно FP.

**Сообщить** - GitHub issue с описанием.

---

*Last updated: 2026-10-12 | Conveyor V5.7*