"""A1 Parser — извлекает Profile из текста резюме."""
from core.llm import call_llm
from core.schemas import Profile

PROMPT = """Ты — парсер резюме. Вход — текст из PDF или описание себя текстом.
Извлеки ТОЛЬКО явно присутствующие факты, ничего не додумывай.
full_name — ФИО кандидата, если есть. target_role — желаемая/текущая должность или
специализация (например «Frontend разработчик»), если указана.
contacts — словарь вида {"email": "...", "phone": "...", "telegram": "...", "github": "..."}, только указанные.
summary — краткое «О себе» одной-двумя фразами, если есть.
education — список объектов вида {"institution": "...", "degree": "...", "field": "...", "years": "..."}.
experience — ТОЛЬКО работа с работодателем (есть компания и должность). Объект {"org": "...", "role": "...", "period": "...", "bullets": ["...", "..."]}. Если компании/должности нет — это НЕ experience.
projects — личные/учебные/pet-проекты (есть название, нет работодателя). Объект {"name": "...", "description": "...", "stack": ["..."], "link": "..."}. Каждый проект — ОТДЕЛЬНЫЙ объект, не объединяй разные проекты.
skills — список строк из стека/технологий (например "Django", "Docker").
achievements — список строк (хакатоны, соревнования, награды, публикации).
languages — список строк вида "Английский B2".
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
