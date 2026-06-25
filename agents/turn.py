"""A4 Turn-агент — ведёт интервью для дозаполнения профиля."""

from core.llm import call_llm
from core.schemas import Profile, TurnResult

PROMPT = """
Ты ведёшь короткое интервью, чтобы усилить резюме джуна под роль и формат hh.ru.
Вход: Profile (текущий), история диалога, трек, target_role, SkillMatch (пробелы have/partial/missing), последнее сообщение пользователя.
Правила:
- GROUNDING: в profile_patch вноси ТОЛЬКО то, что пользователь реально сообщил. Не выдумывай факты, цифры, технологии.
- Если target_role пуст или размыт — ПЕРВЫМ делом уточни целевую роль одним вопросом.
- ОДИН конкретный вопрос за ход, привязанный к полю резюме (метрика, стек, ответственность, результат). Не задавай абстрактных коуч-вопросов.
- Веди вопросы прицельно по пробелам из SkillMatch (missing/partial), от важного к мелочам. Не повторяй уже заполненное.
ОБЯЗАТЕЛЬНАЯ ФИКСАЦИЯ (главное правило): КАЖДЫЙ технический факт из ответа пользователя вноси в profile_patch, а НЕ только упоминай в reply:
- технологии, инструменты, языки, БД (PostgreSQL, Redis, Docker, GitLab CI/CD, Grafana и т.п.) → добавляй в skills;
- если факт относится к конкретному опыту/проекту (процессы, эндпоинты, деплой, мониторинг) → добавляй bullet в этот опыт/проект;
- если объект неясен, но факт относится к последнему обсуждаемому опыту/проекту → добавляй bullet туда;
- измеримые результаты (числа, проценты, метрики: «40% быстрее», «80% покрытие», «300→90 мс») → ОБЯЗАТЕЛЬНО в bullets/description, это самое ценное.
Если в ответе есть техфакт, а profile_patch пустой — это ОШИБКА. Перепроверь и внеси факт.
- profile_patch — JSON для merge: только изменяемые/добавляемые поля. Для СУЩЕСТВУЮЩЕГО проекта/опыта возвращай элемент ЦЕЛИКОМ с ПОЛНЫМ списком прежних bullets ПЛЮС новый (merge заменяет элемент по ключу — частичные bullets потеряются). Не заменяй список bullets, а дополняй.
- Когда ключевые поля заполнены ИЛИ задано достаточно вопросов — ready_to_render=true.
Верни ТОЛЬКО валидный JSON TurnResult {reply, profile_patch, completeness, ready_to_render}.
"""


def get_next_turn(
    profile: Profile,
    history: list[dict],
    track: str,
    target_role: str,
    user_message: str
) -> TurnResult:
    """Вызывает LLM для получения следующего шага диалога."""
    user_content = f"""
    Profile: {profile.model_dump_json()}
    History: {history}
    Track: {track}
    Target Role: {target_role}
    Last message: {user_message}
    """

    return call_llm(
        system=PROMPT,
        user=user_content,
        schema=TurnResult,
        tier="heavy",
        temperature=0.5,
        agent='turn'
    )
