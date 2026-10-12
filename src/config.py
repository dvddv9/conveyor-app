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
DATA_DIR = ROOT_DIR / "data"
PROMPTS_DIR = ROOT_DIR / "vishap"
TOOLS_DIR = ROOT_DIR / "src" / "tools"

# === DeepSeek API ===
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# === Ollama (локально) ===
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434"

# === Режим LLM ===
MODE = "auto"

# === Генерация ===
TEMPERATURE = 0.0
TEMPERATURE_CREATIVE = 0.3
MAX_TOKENS = 8000

# === Сервер ===
PORT = 5001
APP_NAME = "Vishap"

# === Данные ===
DATA_DIR.mkdir(exist_ok=True)
