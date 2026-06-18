"""Конфиг: ключи из st.secrets с фоллбэком на .env."""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "extra_headers": {"HTTP-Referer": "https://junmate.streamlit.app", "X-Title": "JunMate"},
    },
}

MODEL_TIERS = {
    "light": [
        {"provider": "openrouter", "model": "google/gemma-4-26b-a4b-it:free"},
        {"provider": "openrouter", "model": "qwen/qwen3-next-80b-a3b-instruct:free"},
        {"provider": "openrouter", "model": "openai/gpt-oss-20b:free"},
    ],
    "heavy": [
        {"provider": "openrouter", "model": "qwen/qwen3-next-80b-a3b-instruct:free"},
        {"provider": "openrouter", "model": "google/gemma-4-31b-it:free"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
}

AGENT_TIER = {
    "track": "light",
    "parser": "heavy",
    "matcher": "heavy",
    "turn": "heavy",
    "rewriter": "heavy",
    "critic": "heavy",
}


def get_api_key(provider: str) -> str:
    """Возвращает API-ключ провайдера: st.secrets → .env."""
    key_env = PROVIDERS[provider]["key_env"]
    if hasattr(st, "secrets") and key_env in st.secrets:
        return st.secrets[key_env]
    return os.getenv(key_env, "")
