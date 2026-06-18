# Навык: LLM-клиент и роутинг моделей JunMate

Специализируется на LLM-слое: core/llm.py, core/config.py, провайдеры OpenRouter/agentplatform,
тировый выбор моделей, force-JSON, repair, fallback, гейтинг заголовков.
Активируй при реализации/правке LLM-клиента, выборе модели для агента, добавлении провайдера.

## Инструкции
- По умолчанию — только бесплатные модели OpenRouter, затрат ноль. agentplatform — опционально, позже (демо-день, платно).
- Имена :free-моделей НЕ зашивать намертво — только через MODEL_TIERS; каталог меняется, сверять и заменять снятые.
- Ключи — из st.secrets (фоллбэк .env), НИКОГДА не хардкодить.
- Заголовки HTTP-Referer/X-Title — идентификация приложения для OpenRouter, НЕ данные резюме (текст резюме идёт в теле запроса). Слать ТОЛЬКО на OpenRouter; на agentplatform extra_headers пустой.
- Температура: извлечение/классификация 0–0.2; диалог/рерайт 0.4–0.6.

## Провайдеры
```python
PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "extra_headers": {"HTTP-Referer": "<url-приложения>", "X-Title": "JunMate"},
    },
    # ОПЦ. позже: "agentplatform": {"base_url": "https://api.agentplatform.ru/v1",
    #              "key_env": "AGENTPLATFORM_API_KEY", "extra_headers": {}},
}
```

## Тиры моделей (по умолчанию; порядок подтвердить eval'ом)
```python
MODEL_TIERS = {
    "light": [   # лёгкие задачи: классификация трека
        {"provider": "openrouter", "model": "google/gemma-4-26b-a4b-it:free"},
        {"provider": "openrouter", "model": "qwen/qwen3-next-80b-a3b-instruct:free"},
        {"provider": "openrouter", "model": "openai/gpt-oss-20b:free"},
    ],
    "heavy": [   # парсинг, gap, диалог, рерайт, критик: русский + JSON
        {"provider": "openrouter", "model": "qwen/qwen3-next-80b-a3b-instruct:free"},
        {"provider": "openrouter", "model": "google/gemma-4-31b-it:free"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
}
AGENT_TIER = {"track": "light", "parser": "heavy", "matcher": "heavy",
              "turn": "heavy", "rewriter": "heavy", "critic": "heavy"}
```

## Контракт вызова
call_llm(system, user, schema, tier) идёт по списку тира: force-JSON (response_format json_object где
поддерживается, иначе строгий промпт) → валидация pydantic → при ошибке ОДИН repair-вызов → при
повторной ошибке/лимите следующая модель тира.
