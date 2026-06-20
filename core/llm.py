"""Провайдер-агностичный LLM-клиент с тировым роутингом."""

import json
import logging
from typing import TypeVar
from openai import OpenAI, APIStatusError, RateLimitError
from pydantic import BaseModel, ValidationError
from core.config import get_api_key, MODEL_TIERS, PROVIDERS, MODEL_PRICING

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def _log_usage(model: str, resp) -> None:
    """Логирует токены и стоимость вызова по resp.usage."""
    usage = getattr(resp, "usage", None)

    if usage is None:
        logger.info("\nusage недоступен для %s\n", model)
        return

    pin = getattr(usage, "prompt_tokens", 0) or 0
    pout = getattr(usage, "completion_tokens", 0) or 0
    price = MODEL_PRICING.get(model, {"in": 0.0, "out": 0.0})
    cost = pin * price["in"] + pout * price["out"]
    logger.info("%s | in=%d out=%d | ~%.4f ₽", model, pin, pout, cost)  # lazy formatting: %s-str, %d-decimal, %.4f - float


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

        client = OpenAI(base_url=cfg["base_url"], api_key=api_key, max_retries=0)   # ровно 1 сетевой запрос
        extra_headers = cfg.get("extra_headers", {})
        raw = "{}"

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
            if not resp.choices or resp.choices[0].message.content is None:
                raise ValueError(f"\nNo content in response from {model}\n")

            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            _log_usage(model, resp)
            return schema.model_validate(data)

        except RateLimitError as e:                                                 # error 429
            logger.error("\nRate limit exceeded for %s: %s\n", model, e)
            raise e  # Сразу наверх

        except APIStatusError as e:                                                 # errors 401/403/404
            logger.warning("\nAPI error %s for %s: %s\n", e.status_code, model, e.message)
            last_error = e
            continue  # К следующей модели

        except (json.JSONDecodeError, ValidationError) as e:
            logger.info("\nParsing error for %s, attempting repair: %s\n", model, e)
            last_error = e
            # Попытка repair: повторный вызов с подсказкой
            try:
                repair_user = (
                    f"Предыдущий ответ был невалидным JSON или не соответствовал схеме. "
                    f"Исправь и верни ТОЛЬКО валидный JSON.\n"
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
                if not resp.choices or resp.choices[0].message.content is None:
                    raise ValueError(f"\nRepair - No content in response from {model}\n") from None

                raw = resp.choices[0].message.content or "{}"
                data = json.loads(raw)
                _log_usage(model, resp)
                return schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as repair_e:
                logger.warning("\nRepair не помог для %s: %s\n", model, repair_e)
                continue
            except RateLimitError as repair_e:
                logger.error("\nRate limit при repair для %s: %s\n", model, repair_e)
                raise repair_e
            except Exception as repair_e:
                logger.warning("\nRepair failed for %s: %s\n", model, repair_e)
                continue

        except Exception as e:
            logger.error("\nUnexpected error for %s: %s\n", model, e)
            last_error = e
            continue

    raise RuntimeError(f"\nВсе модели тира {tier} недоступны. Последняя ошибка: {last_error}\n")
