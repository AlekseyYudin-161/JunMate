"""A1 Parser — извлекает Profile из текста резюме."""
from core.llm import call_llm
from core.schemas import Profile

PROMPT = """Ты — парсер резюме. Вход — текст из PDF или описание себя текстом.
Извлеки ТОЛЬКО явно присутствующие факты, ничего не додумывай.
Нет поля — null/пусто. Верни ТОЛЬКО валидный JSON по схеме Profile.
Без markdown и текста вне JSON."""


def parse_resume(text: str) -> Profile:
    """Парсит текст резюме в Profile."""
    return call_llm(
        system=PROMPT,
        user=text,
        schema=Profile,
        tier="heavy",
        temperature=0.1,
    )
