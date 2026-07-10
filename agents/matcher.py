"""A3 Matcher — gap-анализ навыков под целевую роль."""

from core.llm import call_llm
from core.schemas import Profile, SkillMatch

PROMPT = """
Вход: Profile + target_role. have/partial/missing навыки относительно роли —
подтверждай ТОЛЬКО фактами профиля, не приписывай. Дай recommendations. 
Верни JSON SkillMatch {target_role, have[], partial[], missing[], recommendations[]}.
"""

def match_skills(profile: Profile, target_role: str) -> SkillMatch:
    """Анализирует соответствие навыков профиля целевой роли."""

    user_content = f"Profile: {profile.model_dump_json()}\nTarget Role: {target_role}"

    return call_llm(
        system=PROMPT,
        user=user_content,
        schema=SkillMatch,
        tier="heavy",
        temperature=0.1,
        agent="matcher"
    )
