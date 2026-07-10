"""Конфиг: ключи из st.secrets с фоллбэком на .env."""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

MAX_QUESTIONS = 6                                          # основных вопросов в первом проходе
REFINE_QUESTIONS = 3                                       # вопросов добора после «Доделать»

PROVIDERS = {
    "proxyapi": {
        "base_url": "https://api.proxyapi.ru/openai/v1",
        "key_env": "PROXYAPI_API_KEY",
        "extra_headers": {},
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "extra_headers": {"HTTP-Referer": "https://junmate.streamlit.app", "X-Title": "JunMate"},
    },
}

# ₽ за 1 токен (input, output).
MODEL_PRICING = {
    # agentplatform
    # "openai/gpt-5-mini":   {"in": 27 / 1_000_000, "out": 216 / 1_000_000},
    # "openai/gpt-4.1-mini": {"in": 44 / 1_000_000, "out": 173 / 1_000_000},

    # proxyapi
    "gpt-4.1-nano": {"in": 26 / 1_000_000, "out": 104 / 1_000_000},
    "gpt-4.1-mini": {"in": 104 / 1_000_000, "out": 413 / 1_000_000},

    # free-модели OpenRouter:
    "openai/gpt-oss-120b:free": {"in": 0.0, "out": 0.0},
}

MODEL_TIERS = {
    "light": [
        {"provider": "proxyapi", "model": "gpt-4.1-nano"},
        {"provider": "proxyapi", "model": "gpt-4.1-mini"},
    ],
    "heavy": [
        {"provider": "proxyapi", "model": "gpt-4.1-mini"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
}

AGENT_TIER = {
    "track": "heavy",
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
