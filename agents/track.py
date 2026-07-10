"""A2 Track — классифицирует карьерный трек по профилю."""

from core.llm import call_llm
from core.schemas import Profile, TrackResult

PROMPT = """
Классифицируй карьерный трек по профилю.
Треки:
- Industry — инженерия/разработка/продукт в компаниях, коммерческий опыт.
- Research — научная работа: публикации, конференции, R&D-лаборатории, исследовательские проекты с метриками, диплом/работа с научным руководителем.
- Education — ОБУЧЕНИЕ ДРУГИХ: преподавание, менторство, разработка курсов. НЕ относить сюда тех, кто сам учится (студент/курсы — это не Education).
- Startup — основание/ранний сотрудник/MVP-продукт.
Если профиль и научный, и преподавательский — выбирай по ДОМИНИРУЮЩЕМУ признаку (публикации/R&D перевешивают разовое ассистентство).
Опирайся ТОЛЬКО на факты профиля. Верни JSON TrackResult {track, confidence, evidence[], runner_up}.
"""


def classify_track(profile: Profile) -> TrackResult:
    """Определяет трек (Industry/Research/Education/Startup) через LLM."""

    return call_llm(
        system=PROMPT,
        user=profile.model_dump_json(),
        schema=TrackResult,
        tier="heavy",
        temperature=0.1,
        agent="track"
    )
