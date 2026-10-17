# -*- coding: utf-8 -*-
"""
Конфигурация Vishap.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Пути ===
ROOT_DIR = Path(__file__).parent.parent

# DATA_DIR — вне site-packages (env > ~/.vishap/data)
_env_data = os.getenv("VISHAP_DATA_DIR")
if _env_data:
    DATA_DIR = Path(_env_data)
else:
    DATA_DIR = Path.home() / ".vishap" / "data"

# PROMPTS_DIR — внутри пакета vishap/ (installed) или ROOT/vishap (dev)
try:
    import vishap as _vishap_pkg
    PROMPTS_DIR = Path(_vishap_pkg.__file__).parent
except ImportError:
    PROMPTS_DIR = ROOT_DIR / "vishap"

TOOLS_DIR = ROOT_DIR / "src" / "tools"

# === DeepSeek API ===
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# === Ollama (локально) ===
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434"

# === LLM Provider selection (v5.10.1) ===
# auto | deepseek | openai | custom | ollama
VISHAP_LLM_PROVIDER = os.getenv("VISHAP_LLM_PROVIDER", "auto")

# --- OpenAI (or any OpenAI-compatible endpoint) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# --- Custom OpenAI-compatible (Groq, Together, LM Studio, vLLM, OpenRouter, ...) ---
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "")
CUSTOM_MODEL = os.getenv("CUSTOM_MODEL", "")
CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL", "")

# === FastAPI (UI -> API) ===
API_URL = os.getenv("API_URL", "http://localhost:5001")
CONVEYOR_API_KEY = os.getenv("CONVEYOR_API_KEY", "")
API_TIMEOUT_SHORT = 5
API_TIMEOUT_DEFAULT = 10
API_TIMEOUT_LONG = 300
API_TIMEOUT_BATCH = 900

# === Tavily Web Search ===
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
SEARCH_DEPTH = os.getenv("SEARCH_DEPTH", "basic")

# === Режим LLM ===
MODE = "auto"

# === Генерация ===
TEMPERATURE = 0.0
TEMPERATURE_CREATIVE = 0.3
MAX_TOKENS = 8000
MAX_TOKENS_STAGE4 = 16000

# === Сервер ===
PORT = 5001
APP_NAME = "Vishap"

# === Логирование (structlog, v6.1) ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "pretty")  # pretty | json

# === Безопасность (Fernet, v6.1) ===
FERNET_KEY = os.getenv("FERNET_KEY", "")

# === GitHub App (v6.1) ===
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID", "")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# === Clerk auth (v6.1) ===
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")

# === Stripe billing (v6.1) ===
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")

# === Данные ===
DATA_DIR.mkdir(parents=True, exist_ok=True)
