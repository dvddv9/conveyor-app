# Conveyor V5.7



🔬 6-стадийный LLM-конвейер для анализа инженерного материала (код, spec, logs).



Принимает файл на вход → возвращает структурированный Markdown-отчёт с рисками, STRIDE-моделью, вариантами рефакторинга и **audit trail** с PII-детекцией и compliance-флагами.



---



## Что делает



**Вход:** `.py`, `.go`, `.js`, `.ts`, `.java`, `.rs`, `.txt`, `.md`, `.json`.



**Выход:**

- 📄 Markdown-отчёт (12+ секций: ECHO, ROUTE, CONCLUSION, RISK, ACTION, FUNC:FULL, MANDATORY BASE, REFLEXION, …)

- 📊 Метаданные: `session_id`, `level` (D0–D4), `route`, `tokens_in/out`

- 🔐 Audit trail: `material_hash` (sha256), `pii_detected`, `compliance_flags`, `critique_verdict`

- ✅ Completeness check: `loss_pct`, `verdict` (ACCEPTABLE / INCOMPLETE)



---



## Архитектура



```

┌─────────────────┐     ┌─────────────────┐

│  Streamlit UI   │     │   FastAPI       │

│   :8501         │────▶│   :5001         │

└─────────────────┘     └────────┬────────┘

&#x20;                                │

&#x20;                                ▼

&#x20;                       ┌─────────────────┐

&#x20;                       │   Pipeline      │

&#x20;                       │   6 стадий      │

&#x20;                       │  ┌───────────┐  │

&#x20;                       │  │ Stage 0   │  │ Orchestrator — route, level

&#x20;                       │  │ Stage 1   │  │ Scanner — 4 слоя

&#x20;                       │  │ Stage 2   │  │ Analyst — риски, STRIDE

&#x20;                       │  │ Stage 3   │  │ Researcher — параллели

&#x20;                       │  │ Stage 4   │  │ Synthesizer — варианты

&#x20;                       │  │ Stage 5   │  │ Transmitter — Markdown

&#x20;                       │  └───────────┘  │

&#x20;                       └────────┬────────┘

&#x20;                                │

&#x20;               ┌────────────────┼────────────────┐

&#x20;               ▼                ▼                ▼

&#x20;        ┌───────────┐   ┌───────────┐   ┌───────────┐

&#x20;        │ DeepSeek  │   │  Ollama   │   │   Audit   │

&#x20;        │ (облако)  │   │ (локально)│   │ sha256 +  │

&#x20;        └───────────┘   └───────────┘   │ PII +     │

&#x20;                                        │ compliance│

&#x20;                                        └───────────┘

```



---



## Стек



| Компонент | Технология |

|-----------|-----------|

| Язык | Python 3.11+ |

| API | FastAPI + Uvicorn |

| UI | Streamlit |

| LLM | DeepSeek (облако) / Ollama (локальный fallback) |

| Хранилище | JSON (`data/history.json`, `data/audit_*.json`, `data/result_*.json`) |

| Audit | Собственная PII-детекция + compliance-флаги |



---



## Быстрый старт



### 1. Клонировать / распаковать



```powershell

cd C:\\AI\\conveyor_app

```



### 2. Виртуальное окружение



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



### 3. Установить зависимости



```powershell

pip install -r requirements.txt

```



### 4. Настроить `.env`



Создай `.env` в корне:



```

DEEPSEEK_API_KEY=sk-...

OLLAMA_URL=http://localhost:11434

```



⚠️ `.env` в `.gitignore` — API-ключ **не уйдёт** в git.



### 5. Запустить API (окно 1)



```powershell

python -m src.main

```



→ Swagger UI: **http://localhost:5001/docs**



### 6. Запустить UI (окно 2)



```powershell

.\\.venv\\Scripts\\Activate.ps1

streamlit run src/ui/streamlit_app.py

```



→ Streamlit: **http://localhost:8501**



---



## Использование



### 🖥️ Через UI



1\. Открой http://localhost:8501

2\. Tab **«🔬 Анализ»**

3\. Загрузи файл (drag \& drop) или вставь текст

4\. Нажми **«🚀 Запустить анализ»**

5\. Жди 40–90 секунд

6\. Результат: Markdown + метаданные + `[AUDIT_TRAIL]` + download



### 🔌 Через API



```powershell

curl.exe -X POST http://localhost:5001/analyze -H "Content-Type: application/json" -d "{\\"material\\": \\"def hello(name):\\n    print(name)\\", \\"filename\\": \\"test.py\\", \\"verbose\\": false}"

```



**Endpoints:**



| Метод | URL | Что |

|-------|-----|-----|

| GET | `/` | root |

| GET | `/health` | health check |

| POST | `/analyze` | запуск pipeline |

| GET | `/history?limit=20` | история |

| POST | `/history/clear` | очистка истории |

| GET | `/docs` | Swagger UI |



### ⌨️ Через CLI



```powershell

python -m src.pipeline.orchestrator --input "data/test_code.py"

python -m src.pipeline.orchestrator --input "data/test_code.py" --quiet

```



**Дополнительные утилиты:**



```powershell

# Статический анализ (AST, сложность, secrets)

python -m src.tools.analyze --mode static --input file.py

python -m src.tools.analyze --mode security --input file.py

python -m src.tools.analyze --mode metrics --input file.py



# Проверка полноты отчёта

python -m src.tools.fallback_check --level D3 --present "[ECHO],[ROUTE],..."



# Нарезка больших файлов

python -m src.tools.slice_input --input big.py --slice "1-100,200-300"

```



---



## Структура проекта



```

conveyor_app/

├── conveyor/                 # промпты V5.7 (660+ строк)

│   ├── 00_orchestrator.md

│   ├── 01_scanner.md

│   ├── 02_analyst.md

│   ├── 03_researcher.md

│   ├── 04_synthesizer.md

│   └── 05_transmitter.md

├── src/

│   ├── main.py              # FastAPI app

│   ├── config.py            # пути, env

│   ├── llm/

│   │   ├── client.py

│   │   ├── deepseek_client.py

│   │   └── ollama_client.py

│   ├── pipeline/

│   │   ├── orchestrator.py  # главный pipeline + audit + completeness

│   │   ├── stages.py        # stage0..stage5

│   │   └── prompts.py       # загрузчик промптов

│   ├── storage/

│   │   ├── history.py       # history.json

│   │   └── mode.py

│   ├── tools/

│   │   ├── analyze.py       # статический анализ

│   │   ├── fallback_check.py # loss_pct, verdict

│   │   └── slice_input.py   # нарезка

│   └── ui/

│       └── streamlit_app.py # Streamlit UI

├── data/                     # результаты (в .gitignore)

│   ├── history.json

│   ├── audit_*.json

│   └── result_*.json

├── .gitignore

├── requirements.txt

└── README.md

```



---



## Audit \& Compliance



### Что такое audit trail



На каждый анализ создаётся `data/audit_<session>.json`:



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

&#x20; "compliance_flags": ["GDPR", "152-ФЗ"]

}

```



### PII-детекция



Регулярками ловит:

- `email`

- `phone_ru` — `+7XXXXXXXXXX` / `8XXXXXXXXXX`

- `passport_ru` — `XXXX XXXXXX`

- `snils` — `XXX-XXX-XXX XX`

- `iban` — международный формат



### Compliance-флаги



- По ключевым словам: `HIPAA`, `PCI-DSS`, `GDPR`, `152-ФЗ`, `EU AI Act`

- **Автоматически** добавляются: `GDPR` + `152-ФЗ` при наличии любого PII



### Verdict



- `SAFE` — PII и compliance не найдены

- `REQUIRES_REVIEW` — найдено PII или compliance-триггеры



### Emergency



Если Stage 0 видит критический риск (RCE, hardcoded secrets, **PII** → «нарушение закона») — `EMERGENCY_INTERRUPT`. Pipeline останавливается, но **audit всё равно собирается**.



---



## Пример отчёта



```markdown

# D0 — process_user(email)



[CONCLUSION] Функция `process_user(email)` выводит email в stdout через `print`

без маскирования; в комментариях исходника — PII (email, телефон).



[RISK] критично PII в комментариях → коммит в VCS → утечка в git-историю

навсегда. критично `print(f"User: {email}")` → email в stdout → агрегация

в логи без redaction.



[FUNC:FULL]

- ECON: effort \~0.5h, cost $0, ROI высокий...

- FAIL: критично PII → VCS (необратимо)...

...



[AUDIT_TRAIL]

audit_id: audit-2026-10-08-938e54

material_hash: sha256:4f87e43baa8f2253

pii_detected: true

compliance_flags: ['GDPR', '152-ФЗ']

critique_verdict: REQUIRES_REVIEW



[COMPLETENESS]

level: D0

required: 3

missing: []

loss_pct: 0.0%

verdict: ACCEPTABLE

```



---



## Разработка



### Git



```powershell

git status

git add -A

git commit -m "feat: ..."

git --no-pager log --oneline

```



### Известные ограничения



- **pandas не используется** — Windows Code Integrity Policy может блокировать `pandas._libs.*.pyd`. Вместо pandas используется нативный `st.dataframe(list[dict])`.

- **Тесты** — пока не написаны (`pytest` в `requirements.txt`, но тестов нет).

- **Параллелизм Stage 3/4** — пока последовательный.



### Roadmap



- [ ] Тесты (`pytest`, smoke-test pipeline)

- [ ] Параллелизм Stage 3/4 (`asyncio.gather`)

- [ ] Streaming output (SSE)

- [ ] `slice_input` интегрировать в orchestrator

- [ ] `audit` в JSON-ответ API

- [ ] GitHub Actions (CI)

- [ ] GitHub App (webhook на PR)

- [ ] Фильтры в UI (по level, verdict, pii_detected)



---



## Лицензия



Private / not specified.



---



## Автор



David — 2026

