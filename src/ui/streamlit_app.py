# -*- coding: utf-8 -*-
"""
Vishap V5.8 — Streamlit UI.
Запуск: streamlit run src/ui/streamlit_app.py
"""
import os
import json
from pathlib import Path
from datetime import datetime
...
import requests
import streamlit as st
from src.config import DATA_DIR


API_URL = os.getenv("API_URL", "http://localhost:5001")
API_KEY = os.getenv("CONVEYOR_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}
HISTORY_LIMIT = 20


st.set_page_config(
    page_title="Vishap V5.8",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Vishap V5.8")
st.caption("6-стадийный LLM-конвейер для анализа кода")

try:
    health = requests.get(f"{API_URL}/health", timeout=5, headers=HEADERS).json()
    st.success(f"✅ API работает · {health.get('status', 'unknown')}")
except Exception as e:
    st.error(f"❌ API не отвечает: {e}")
    st.info("Запусти: python -m src.main в другом окне PowerShell")
    st.stop()


tab_analyze, tab_history, tab_about = st.tabs(["🔬 Анализ", "📜 История", "ℹ️ О проекте"])


# Defaults — на случай, если пользователь в batch-режиме
analyze_btn = False
material = ""
filename = "input.txt"
result_placeholder = None


with tab_analyze:
    # === Выбор режима ===
    mode = st.radio(
        "Режим анализа",
        ["📁 Один файл", "📚 Несколько файлов (batch)"],
        horizontal=True,
        key="analyze_mode",
    )

    # ============================================================
    # === Режим «Один файл» ===
    # ============================================================
    if mode == "📁 Один файл":
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("Входные данные")

            input_mode = st.radio(
                "Как передать материал?",
                ["📁 Загрузить файл", "✍️ Вставить текст"],
                horizontal=True,
                key="single_input_mode",
            )

            material = ""
            filename = "input.txt"

            if input_mode == "📁 Загрузить файл":
                uploaded = st.file_uploader(
                    "Выбери файл",
                    type=["py", "go", "js", "ts", "java", "rs", "txt", "md", "json"],
                    key="single_file",
                )
                if uploaded is not None:
                    try:
                        material = uploaded.read().decode("utf-8", errors="replace")
                        filename = uploaded.name
                        st.success(f"✅ Загружено: {filename} ({len(material)} символов)")
                    except Exception as e:
                        st.error(f"Ошибка чтения: {e}")
            else:
                filename = st.text_input("Имя файла (для контекста)", value="input.txt", key="single_name")
                material = st.text_area(
                    "Код / spec / logs",
                    height=300,
                    placeholder="Вставь код сюда...",
                    key="single_text",
                )
                if material:
                    st.caption(f"{len(material)} символов")

            col_btn, col_force = st.columns([3, 1])
            with col_btn:
                analyze_btn = st.button(
                "🚀 Запустить анализ",
                type="primary",
                width="stretch",
                disabled=not material.strip(),
                key="single_analyze_btn",
                )
            with col_force:
                force_flag = st.checkbox(
                    "Force re-analyze",
                    value=False,
                    key="single_force_flag",
                    help="Ignore cache and re-run analysis",
                )

        with col_right:
            st.subheader("Результат")
            result_placeholder = st.empty()
            result_placeholder.info("👈 Загрузи файл и нажми Анализ")

    # ============================================================
    # === Режим «Несколько файлов (batch)» ===
    # ============================================================
    else:
        st.subheader("Batch-анализ")
        st.caption("Загрузи несколько файлов — они обработаются параллельно. Быстрее в ~N раз (N = параллельных потоков).")

        uploaded_files = st.file_uploader(
            "Выбери файлы (можно несколько)",
            type=["py", "go", "js", "ts", "java", "rs", "txt", "md", "json"],
            accept_multiple_files=True,
            key="batch_files",
        )

        if uploaded_files:
            st.success(f"✅ Загружено файлов: {len(uploaded_files)}")

            # Список файлов
            with st.expander(f"📋 Список файлов ({len(uploaded_files)})", expanded=False):
                for i, f in enumerate(uploaded_files, 1):
                    st.write(f"{i}. **{f.name}** — {f.size} байт")

            # Настройки
            col_a, col_b = st.columns([1, 3])
            with col_a:
                max_conc = st.slider(
                    "Параллельно",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Сколько файлов обрабатывать одновременно. Больше 10 — риск rate limit DeepSeek.",
                    key="batch_max_conc",
                )

            batch_btn = st.button(
                f"🚀 Анализ всех ({len(uploaded_files)} файлов)",
                type="primary",
                width="stretch",
                key="batch_analyze_btn",
            )

            if batch_btn:
                # Собрать items
                items = []
                for f in uploaded_files:
                    try:
                        content = f.read().decode("utf-8", errors="replace")
                        items.append({"material": content, "filename": f.name})
                    except Exception as e:
                        st.error(f"Ошибка чтения {f.name}: {e}")

                if items:
                    with st.spinner(f"⏳ Обработка {len(items)} файлов (параллельно до {max_conc})..."):
                        try:
                            resp = requests.post(
                                f"{API_URL}/analyze/batch",
                                json={"items": items, "max_concurrent": max_conc},
                                timeout=900, headers=HEADERS
                            )

                            if resp.status_code != 200:
                                st.error(f"Ошибка API: {resp.status_code}\n\n{resp.text}")
                            else:
                                data = resp.json()
                                results = data.get("results", [])

                                # Сводка
                                st.success(f"✅ Обработано: {data.get('count', 0)} файлов")
                                safe = sum(1 for r in results if r.get("verdict") == "SAFE")
                                review = sum(1 for r in results if r.get("verdict") == "REQUIRES_REVIEW")
                                pii_count = sum(1 for r in results if r.get("pii_detected"))
                                errors = sum(1 for r in results if r.get("error"))

                                m1, m2, m3, m4, m5 = st.columns(5)
                                m1.metric("Всего", len(results))
                                m2.metric("SAFE", safe)
                                m3.metric("REVIEW", review)
                                m4.metric("PII", pii_count)
                                m5.metric("Ошибки", errors)

                                st.divider()

                                # Результаты — expander для каждого
                                for r in results:
                                    fn = r.get("filename", "?")
                                    vd = r.get("verdict") or "ERROR"
                                    pii = r.get("pii_detected")

                                    # Иконка
                                    if r.get("error"):
                                        icon = "❌"
                                    elif pii:
                                        icon = "🔴"
                                    elif vd == "SAFE":
                                        icon = "✅"
                                    else:
                                        icon = "🟡"

                                    title = f"{icon} {fn} — {vd}"
                                    with st.expander(title, expanded=False):
                                        if r.get("error"):
                                            st.error(f"Ошибка: {r['error']}")
                                        else:
                                            c1, c2, c3 = st.columns(3)
                                            c1.markdown(f"**Level:** {r.get('level', '?')}")
                                            c2.markdown(f"**Verdict:** {vd}")
                                            c3.markdown(f"**PII:** {'да' if pii else 'нет'}")
                                            st.caption(f"Session: {r.get('session_id', '?')}")
                                            st.divider()
                                            st.markdown((r.get("final_markdown", "") or "_пусто_").replace("$", "\\$"))
                                            st.download_button(
                                                "💾 Скачать Markdown",
                                                data=r.get("final_markdown", "") or "",
                                                file_name=f"report_{fn}.md",
                                                mime="text/markdown",
                                                key=f"dl_{fn}_{r.get('session_id', '')}",
                                            )

                        except Exception as e:
                            st.error(f"Ошибка запроса: {e}")
        else:
            st.info("👆 Загрузи файлы, чтобы начать batch-анализ")


with tab_history:
    st.subheader("История анализов")

    col_refresh, col_clear = st.columns([3, 1])

    with col_refresh:
        if st.button("🔄 Обновить"):
            st.rerun()

    with col_clear:
        if st.button("🗑️ Очистить", type="secondary"):
            try:
                requests.post(f"{API_URL}/history/clear", timeout=5, headers=HEADERS)
                st.success("История очищена")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")

    try:
        history = requests.get(
            f"{API_URL}/history",
            params={"limit": HISTORY_LIMIT},
            timeout=10, headers=HEADERS
        ).json()

        if not history:
            st.info("История пуста")
        else:
            # Prepare display rows (fill defaults for old records)
            display_rows = []
            for row in history:
                r = dict(row)
                if isinstance(r.get("route"), list):
                    r["route"] = ", ".join(r["route"])
                if not r.get("verdict"):
                    r["verdict"] = "—"
                if r.get("pii_detected") is None:
                    r["pii_detected"] = False
                display_rows.append(r)

            # === Filters ===
            st.markdown("**Фильтры**")
            f_col1, f_col2, f_col3, f_col4 = st.columns([1, 1, 1, 2])

            with f_col1:
                levels_all = sorted({r.get("level", "?") for r in display_rows})
                levels_sel = st.multiselect("Level", levels_all, default=levels_all)

            with f_col2:
                verdicts_all = sorted({str(r.get("verdict", "—")) for r in display_rows})
                verdicts_sel = st.multiselect("Verdict", verdicts_all, default=verdicts_all)

            with f_col3:
                only_pii = st.checkbox("Только PII", value=False)

            with f_col4:
                fname_query = st.text_input("Поиск по filename", value="").strip().lower()

            # Apply filters
            filtered = []
            for r in display_rows:
                if r.get("level") not in levels_sel:
                    continue
                if str(r.get("verdict", "—")) not in verdicts_sel:
                    continue
                if only_pii and not r.get("pii_detected"):
                    continue
                if fname_query and fname_query not in str(r.get("filename", "")).lower():
                    continue
                filtered.append(r)

            st.dataframe(filtered, width="stretch")
            st.caption(f"Показано: {len(filtered)} из {len(display_rows)}")          
            # === Download Markdown from history ===
            st.divider()
            st.markdown("**Download Markdown**")
            dl_session = st.selectbox(
                "Select session",
                [r.get("session_id", "?") for r in filtered],
                key="history_dl_session",
            )
            if dl_session:
                _rp = DATA_DIR / f"result_{dl_session}.json"
                if _rp.exists():
                    _d = json.loads(_rp.read_text(encoding="utf-8"))
                    _md = _d.get("final_markdown", "")
                    if _md:
                        st.download_button(
                            "💾 Download Markdown",
                            data=_md,
                            file_name=f"report_{dl_session}.md",
                            mime="text/markdown",
                            key=f"dl_hist_{dl_session}",
                        )
                    else:
                        st.warning("No final_markdown in result file")
                else:
                    st.warning(f"Result file not found: {_rp}")

    except Exception as e:
        st.error(f"Ошибка загрузки истории: {e}")


with tab_about:
    st.subheader("ℹ️ Vishap V5.8")

    # === Режим LLM ===
    st.markdown("### 🔧 Режим LLM")

    current_mode = "auto"
    try:
        r = requests.get(f"{API_URL}/mode", timeout=5, headers=HEADERS)
        if r.status_code == 200:
            current_mode = r.json().get("mode", "auto")
    except Exception:
        pass

    mode_options = {
        "auto": "🔄 Auto (DeepSeek → Ollama fallback)",
        "cloud": "☁️ Cloud (только DeepSeek)",
        "local": "💻 Local (только Ollama)",
    }
    mode_keys = list(mode_options.keys())

    selected = st.radio(
        "Выбери режим",
        mode_keys,
        index=mode_keys.index(current_mode) if current_mode in mode_keys else 0,
        format_func=lambda x: mode_options[x],
        horizontal=False,
        key="llm_mode_radio",
    )

    if selected != current_mode:
        if st.button("✅ Применить", type="primary"):
            try:
                r = requests.post(f"{API_URL}/mode", json={"mode": selected}, timeout=5, headers=HEADERS)
                if r.status_code == 200:
                    st.success(f"Режим изменён на: {selected}")
                    st.rerun()
                else:
                    st.error(f"Ошибка: {r.text}")
            except Exception as e:
                st.error(f"Ошибка запроса: {e}")

    st.caption(f"**Текущий режим:** `{current_mode}`")
    st.info(
        "**Auto** — DeepSeek (быстро), при ошибке → Ollama (медленно)\n\n"
        "**Cloud** — только DeepSeek\n\n"
        "**Local** — только Ollama (медленно, для приватности)"
    )

    st.divider()

    st.markdown("""
**Vishap V5.8** — 6-стадийный LLM-конвейер для анализа инженерного материала.

### Архитектура

Streamlit UI -> FastAPI (:5001) -> Pipeline (6 стадий) -> DeepSeek/Ollama

### Возможности

- 🔬 6 стадий анализа
- 📊 JSON-structured output
- 🎯 Risk nodes, STRIDE, COVE
- 📝 Финальный Markdown-отчёт
- 🔄 Fallback на локальный LLM
- 📜 История анализов

### Endpoints

- POST /analyze — анализ
- GET /history — история
- GET /health — проверка
- /docs — Swagger UI
    """)
    st.caption(f"API: {API_URL}")


if analyze_btn and material.strip() and result_placeholder is not None:
    with st.spinner("⏳ Анализ идёт... 6 стадий, ~40-90 секунд"):

        progress = st.progress(0)
        status = st.empty()

        stages = [
            "Stage 0: Orchestrator...",
            "Stage 1: Scanner...",
            "Stage 2: Analyst...",
            "Stage 4: Synthesizer...",
            "Stage 5: Transmitter...",
        ]

        for i, stage_name in enumerate(stages):
            status.info(f"⏳ {stage_name}")
            progress.progress((i + 1) * 20)

        try:
            response = requests.post(
                f"{API_URL}/analyze",
                json={
                    "material": material,
                    "filename": filename,
                    "verbose": False,
                    "force": force_flag,
                },
                timeout=300, headers=HEADERS
            )
            progress.progress(100)
            status.success("✅ Анализ завершён!")

            if response.status_code == 200:
                data = response.json()
                result_placeholder.empty()

                with result_placeholder.container():
                    st.markdown("### 📊 Метаданные")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Session", data.get("session_id", "?"))
                    c2.metric("Level", data.get("level", "?"))
                    c3.metric("Tokens", f"{data.get('tokens_in', 0)}+{data.get('tokens_out', 0)}")

                    st.caption(f"Route: {data.get('route', [])}")

                    st.divider()
                    st.markdown("### 📄 Отчёт")
                    st.markdown(data.get("final_markdown", "").replace("$", "\\$"))

                    st.divider()
                    st.download_button(
                        "💾 Скачать Markdown",
                        data=data.get("final_markdown", ""),
                        file_name=f"report_{data.get('session_id', 'unknown')}.md",
                        mime="text/markdown",
                    )

                    # === v5.8: SARIF download ===
                    if st.button("📋 Скачать SARIF 2.1.0", key="sarif_btn"):
                        try:
                            sarif_resp = requests.post(
                                f"{API_URL}/analyze/sarif",
                                json={
                                    "material": material,
                                    "filename": filename,
                                    "verbose": False,
                                    "force": False,
                                },
                                timeout=300, headers=HEADERS
                            )
                            if sarif_resp.status_code == 200:
                                st.download_button(
                                    "💾 Скачать SARIF",
                                    data=sarif_resp.text,
                                    file_name=f"sarif_{data.get('session_id', 'unknown')}.json",
                                    mime="application/json",
                                    key="sarif_dl",
                                )
                            else:
                                st.error(f"SARIF error: {sarif_resp.status_code}")
                        except Exception as e:
                            st.error(f"SARIF exception: {e}")

                    # === v5.8: SAST/SCA ===
                    audit = data.get("audit", {}) if isinstance(data.get("audit"), dict) else {}
                    sast_findings = audit.get("sast_findings", 0)
                    sast_high = audit.get("sast_high_priority", 0)
                    sast_tools = audit.get("sast_tools", {})
                    sca_vulns = audit.get("sca_vulnerabilities", 0)

                    if sast_findings or sca_vulns or sast_tools:
                        with st.expander(f"🔬 SAST/SCA — {sast_findings} findings ({sast_high} high), {sca_vulns} CVEs", expanded=False):
                            c1, c2, c3 = st.columns(3)
                            c1.metric("SAST findings", sast_findings)
                            c2.metric("SAST high", sast_high)
                            c3.metric("SCA vulnerabilities", sca_vulns)
                            if sast_tools:
                                st.markdown("**Tools summary:**")
                                st.json(sast_tools)

                    # === v5.8: OWASP + CWE ===
                    cwe_ids = audit.get("cwe_ids", [])
                    owasp_categories = audit.get("owasp_categories", [])
                    if cwe_ids or owasp_categories:
                        with st.expander(f"🛡️ OWASP — {len(owasp_categories)} categories, {len(cwe_ids)} CWEs", expanded=False):
                            if cwe_ids:
                                st.markdown(f"**CWE IDs:** `{', '.join(cwe_ids)}`")
                            if owasp_categories:
                                st.markdown("**OWASP Top 10 (2025):**")
                                for cat in owasp_categories:
                                    st.markdown(f"- {cat}")

                    # === v5.8: Exploitability ===
                    exploit = audit.get("exploitability", {})
                    if exploit and exploit.get("reachable"):
                        blast = exploit.get("blast_radius", "none")
                        auth = "yes" if exploit.get("auth_required") else "NO"
                        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(blast, "⚪")
                        with st.expander(f"{emoji} Exploitability — blast: {blast}, auth: {auth}", expanded=False):
                            c1, c2 = st.columns(2)
                            c1.metric("Reachable", "Yes" if exploit.get("reachable") else "No")
                            c2.metric("Auth required", "Yes" if exploit.get("auth_required") else "No")
                            st.caption(f"**Blast radius:** {blast}")
                            st.caption(f"**Exploit path:** `{exploit.get('exploit_path', 'n/a')}`")
                            if exploit.get("entry_points"):
                                st.caption(f"**Entry points:** {exploit.get('entry_points')}")
                            if exploit.get("blast_indicators"):
                                st.caption(f"**Blast indicators:** {exploit.get('blast_indicators')}")

                    # === v5.8: Provenance ===
                    prov = audit.get("provenance", {})
                    if prov:
                        source = prov.get("source", "unknown")
                        commit = prov.get("git_commit_short", "")
                        branch = prov.get("git_branch", "")
                        st.caption(f"📍 Provenance: `{source}` | commit: `{commit}` | branch: `{branch}`")

                    # === v5.8: Redaction ===
                    if audit.get("redaction_applied"):
                        redaction_map = audit.get("redaction_map", {})
                        if redaction_map:
                            st.caption(f"🔒 Redacted before LLM: {redaction_map}")

                    # === v5.8: Download JSON (полный result) ===
                    import json as _json
                    json_data = _json.dumps(data, ensure_ascii=False, indent=2)
                    st.download_button(
                        "📥 Скачать JSON (полный result)",
                        data=json_data,
                        file_name=f"result_{data.get('session_id', 'unknown')}.json",
                        mime="application/json",
                        key="json_dl",
                    )

                    # === v5.8: Детали аудита ===
                    with st.expander("🔍 Детали аудита (JSON)", expanded=False):
                        st.markdown("**audit:**")
                        st.json(audit)
                        st.markdown("**Provenance:**")
                        st.json(audit.get("provenance", {}))
                        st.markdown("**Exploitability:**")
                        st.json(audit.get("exploitability", {}))
            else:
                result_placeholder.error(
                    f"Ошибка API: {response.status_code}"
                )
        except Exception as e:
            progress.empty()
            status.error(f"❌ Ошибка: {e}")
            result_placeholder.error(f"Ошибка запроса: {e}")
