"""A2 Track — классифицирует карьерный трек по профилю."""

from core.llm import call_llm
from core.schemas import Profile, TrackResult

PROMPT = """Классифицируй карьерный трек по профилю.
Треки: Industry (инженерия/прод в компаниях),
Research (наука/публикации/R&D), 
Education (преподавание/менторство), 
Startup (основание/ранний продукт).
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
