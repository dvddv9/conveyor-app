# -*- coding: utf-8 -*-
"""
Conveyor V5.7 — Streamlit UI.
Запуск: streamlit run src/ui/streamlit_app.py
"""
import json
from datetime import datetime

import requests
import streamlit as st


API_URL = "http://localhost:5001"
HISTORY_LIMIT = 20


st.set_page_config(
    page_title="Conveyor V5.7",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Conveyor V5.7")
st.caption("6-стадийный LLM-конвейер для анализа кода")

try:
    health = requests.get(f"{API_URL}/health", timeout=5).json()
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

            analyze_btn = st.button(
                "🚀 Запустить анализ",
                type="primary",
                width="stretch",
                disabled=not material.strip(),
                key="single_analyze_btn",
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
                                timeout=900,
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
                                            st.markdown(r.get("final_markdown", "") or "_пусто_")
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
                requests.post(f"{API_URL}/history/clear", timeout=5)
                st.success("История очищена")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")

    try:
        history = requests.get(
            f"{API_URL}/history",
            params={"limit": HISTORY_LIMIT},
            timeout=10,
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

    except Exception as e:
        st.error(f"Ошибка загрузки истории: {e}")


with tab_about:
    st.subheader("ℹ️ Conveyor V5.7")
    st.markdown("""
**Conveyor V5.7** — 6-стадийный LLM-конвейер для анализа инженерного материала.

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
                },
                timeout=300,
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
                    st.markdown(data.get("final_markdown", ""))

                    st.divider()
                    st.download_button(
                        "💾 Скачать Markdown",
                        data=data.get("final_markdown", ""),
                        file_name=f"report_{data.get('session_id', 'unknown')}.md",
                        mime="text/markdown",
                    )
            else:
                result_placeholder.error(
                    f"Ошибка API: {response.status_code}"
                )
        except Exception as e:
            progress.empty()
            status.error(f"❌ Ошибка: {e}")
            result_placeholder.error(f"Ошибка запроса: {e}")
