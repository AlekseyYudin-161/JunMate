"""Провайдер-агностичный LLM-клиент с тировым роутингом."""
import json
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

from core.config import get_api_key, MODEL_TIERS, PROVIDERS

T = TypeVar("T", bound=BaseModel)


def call_llm(
    system: str,
    user: str,
    schema: type[T],
    tier: str = "heavy",
    temperature: float = 0.4,
) -> T:
    """Вызывает LLM с force-JSON, pydantic-валидацией, repair и fallback по тиру."""
    models = MODEL_TIERS.get(tier, MODEL_TIERS["heavy"])
    last_error = None

    for entry in models:
        provider = entry["provider"]
        model = entry["model"]
        cfg = PROVIDERS[provider]
        api_key = get_api_key(provider)
        if not api_key:
            continue

        client = OpenAI(base_url=cfg["base_url"], api_key=api_key)
        extra_headers = cfg.get("extra_headers", {})

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
                extra_headers=extra_headers if provider == "openrouter" else None,
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            return schema.model_validate(data)
        except Exception as e:
            last_error = e
            # Попытка repair: повторный вызов с подсказкой
            try:
                repair_user = (
                    f"Предыдущий ответ был невалидным JSON. Исправь и верни ТОЛЬКО JSON.\n"
                    f"Ошибка: {e}\n"
                    f"Текст: {raw}"
                )
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": repair_user},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    extra_headers=extra_headers if provider == "openrouter" else None,
                )
                raw = resp.choices[0].message.content or "{}"
                data = json.loads(raw)
                return schema.model_validate(data)
            except Exception:
                continue

    raise RuntimeError(f"Все модели тира {tier} недоступны: {last_error}")
