"""Провайдер-агностичный LLM-клиент с тировым роутингом."""

import json
import logging
from typing import TypeVar
from openai import OpenAI, APIStatusError, RateLimitError
from pydantic import BaseModel, ValidationError
from core.config import get_api_key, MODEL_TIERS, PROVIDERS, MODEL_PRICING

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def _log_usage(agent: str, model: str, resp) -> None:
    """Логирует токены и стоимость вызова по resp.usage."""

    usage = getattr(resp, "usage", None)

    if usage is None:
        logger.info("\n[%s] usage недоступен для %s\n", agent, model)
        return

    pin = getattr(usage, "prompt_tokens", 0) or 0
    pout = getattr(usage, "completion_tokens", 0) or 0
    price = MODEL_PRICING.get(model, {"in": 0.0, "out": 0.0})
    cost = pin * price["in"] + pout * price["out"]
    logger.info("[%s] %s | in=%d out=%d | ~%.4f ₽", agent, model, pin, pout, cost)


def call_llm(
    system: str,
    user: str,
    schema: type[T],
    tier: str = "heavy",
    temperature: float = 0.4,
    agent: str = "?",
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

        # ровно 1 сетевой запрос
        client = OpenAI(base_url=cfg["base_url"], api_key=api_key, max_retries=0)
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
            _log_usage(agent, model, resp)
            return schema.model_validate(data)

        except RateLimitError as e:
            logger.error("\n[%s] Rate limit exceeded for %s: %s\n", agent, model, e)
            raise e  # Сразу наверх

        except APIStatusError as e:
            logger.warning("\n[%s] API error %s for %s: %s\n", agent, e.status_code, model, e.message)
            last_error = e
            continue                                            # К следующей модели

        except (json.JSONDecodeError, ValidationError) as e:
            logger.info("\n[%s] Parsing error for %s, attempting repair: %s\n", agent, model, e)
            last_error = e

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
                _log_usage(agent, model, resp)
                return schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as repair_e:
                logger.warning("\n[%s] Repair не помог для %s: %s\n", agent, model, repair_e)
                continue
            except RateLimitError as repair_e:
                logger.error("\n[%s] Rate limit при repair для %s: %s\n", agent, model, repair_e)
                raise repair_e
            except Exception as repair_e:
                logger.warning("\n[%s] Repair failed for %s: %s\n", agent, model, repair_e)
                continue

        except Exception as e:
            logger.error("\n[%s] Unexpected error for %s: %s\n", agent, model, e)
            last_error = e
            continue

    raise RuntimeError(f"\nВсе модели тира {tier} недоступны. Последняя ошибка: {last_error}\n")
