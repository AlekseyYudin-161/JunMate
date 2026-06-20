# Навык: LLM-клиент и роутинг моделей JunMate

Специализируется на LLM-слое: core/llm.py, core/config.py, провайдеры OpenRouter/agentplatform,
тировый выбор моделей, force-JSON, repair, fallback, гейтинг заголовков.
Активируй при реализации/правке LLM-клиента, выборе модели для агента, добавлении провайдера.

## Инструкции
- основной провайдер — proxyapi (платный), openrouter free — нижний фоллбэк.
- Имена моделей НЕ зашивать намертво — только через MODEL_TIERS.
- Ключи — из st.secrets (фоллбэк .env), НИКОГДА не хардкодить.
- Заголовки HTTP-Referer/X-Title — идентификация приложения для OpenRouter, НЕ данные резюме (текст резюме идёт в теле запроса). Слать ТОЛЬКО на OpenRouter; на proxyapi extra_headers пустой.
- Температура: извлечение/классификация 0–0.2; диалог/рерайт 0.4–0.6.

## Провайдеры
```python
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
```

## Тиры моделей (по умолчанию; порядок подтвердить eval'ом)
```python
MODEL_TIERS = {
    "light": [
        {"provider": "proxyapi", "model": "gpt-4.1-mini"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
    "heavy": [
        {"provider": "proxyapi", "model": "gpt-4.1-mini"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],

}
AGENT_TIER = {
    "track": "light",
    "parser": "heavy",
    "matcher": "heavy",
    "turn": "heavy",
    "rewriter": "heavy",
    "critic": "heavy"}
```

## Контракт вызова
call_llm(system, user, schema, tier) идёт по списку тира: force-JSON (response_format json_object где
поддерживается, иначе строгий промпт) → валидация pydantic → при ошибке ОДИН repair-вызов → при
повторной ошибке/лимите следующая модель тира.
