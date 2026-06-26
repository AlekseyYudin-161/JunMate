"""A6 Critic — проверяет резюме на соответствие фактам (grounding)."""

from core.llm import call_llm
from core.schemas import Profile, Critique

PROMPT = """
Строгий проверяющий резюме (контроль фактологичности). Вход: исходный Profile, история диалога и сгенерированный текст резюме.
Проверь по пунктам:
1. grounding_ok — есть ли в резюме факты (работодатели, должности, цифры, метрики, технологии), которых НЕТ ни в Profile, ни в истории диалога. Любой такой факт → в fabricated_claims. Факты, сказанные пользователем в истории диалога, выдумкой НЕ считаются (даже если их не было в исходном Profile). Переформулировка имеющихся фактов выдумкой НЕ считается.
2. completeness (0..1) — насколько полно резюме отражает Profile и историю диалога.
3. format_ok — структура hh.ru: нужные блоки на месте; pet-проекты и личные/исследовательские проекты (без работодателя) находятся в блоке «Проекты», а НЕ в «Опыте»; пустые блоки (в т.ч. «Опыт» без записей) НЕ выводятся.
4. fixes — конкретные, краткие правки для устранения найденных проблем (что именно перенести/убрать/исправить).
Верни ТОЛЬКО валидный JSON Critique {grounding_ok, fabricated_claims[], completeness, format_ok, fixes[]}.
"""

def critique_resume(
    profile: Profile, 
    history: list[dict], 
    content_markdown: str
) -> Critique:
    """Проверяет резюме на галлюцинации и полноту."""
    user_content = f"""
    Profile: {profile.model_dump_json()}
    History: {history}
    Resume Text:
    {content_markdown}
    """

    return call_llm(
        system=PROMPT,
        user=user_content,
        schema=Critique,
        tier="heavy",
        temperature=0.1,
        agent="critic"
    )
