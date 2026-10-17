# Harness (DSH) Integration

Vishap can use **DeepSeek Harness (DSH)** as an LLM provider instead of
direct DeepSeek API or Ollama.

## Requirements

- DSH installed (desktop app or @deepseek-ai/dsh CLI).
- dsh web running (port 3080):

    & "C:\Users\<user>\AppData\Local\Programs\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd" web

- Copy the printed token from dsh web: http://127.0.0.1:3080/?token=<TOKEN>

## Configuration (.env)

    HARNESS_URL=http://127.0.0.1:3080
    HARNESS_TOKEN=<token from dsh web>
    VISHAP_LLM_PROVIDER=auto
    VISHAP_DATA_DIR=C:\AI\conveyor_app\data

## Switching mode

UI: Streamlit sidebar "Режим LLM" -> Harness (DSH) -> "Применить".

API:

    $body = @{ mode = "harness" } | ConvertTo-Json
    Invoke-WebRequest -Uri "http://127.0.0.1:5001/mode" -Method POST -Body $body -ContentType "application/json" -Headers @{ "X-API-Key" = "test-key-12345" } -UseBasicParsing

Env: VISHAP_LLM_PROVIDER=auto (reads mode.json).

## How it works

1. client.chat() / async_chat() -> _resolve_provider() -> harness.
2. HarnessClient.chat():
   - GET /?token=... -- sets dsh-auth-* cookie.
   - POST /api/session/create -- new session with cwd.
   - POST /api/session/prompt -- UTF-8 prompt, mode=queue.
   - Polls ~/.dsh/sessions/<slug>/<sid>/session.v4.jsonl.zstd.
3. Returns {"text": ..., "model": "harness", ...}.

Async wraps sync client in loop.run_in_executor.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| HARNESS_URL | http://127.0.0.1:3080 | DSH web endpoint |
| HARNESS_TOKEN | -- | auth token from dsh web |
| VISHAP_DATA_DIR | ~/.vishap/data | mode.json location |
| VISHAP_LLM_PROVIDER | auto | provider override |

## Timeouts

POLL_TIMEOUT=600.0 in harness_client.py. Large files take 3-5 min.

## Troubleshooting

- 401 auth failed -- restart dsh web (new token) + update .env.
- timeout -- increase POLL_TIMEOUT.
- PermissionError ~/.vishap/data -- set VISHAP_DATA_DIR.
- UI "Применить" doesn't work -- restart Streamlit (no hot reload).

## Limitations

- DSH is developer preview; RPC format may change.
- session.v4.jsonl.zstd versioned; DSH update may rename.
- No fallback (recommended future work).

## Files

- src/llm/harness_client.py -- sync client.
- src/llm/client.py -- harness branch (sync).
- src/llm/async_client.py -- harness branch (async).
- src/storage/mode.py -- harness in VALID_MODES.
- src/ui/streamlit_app.py -- dropdown option.
