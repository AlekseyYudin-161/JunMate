# Навык: Profile и детерминированное слияние patch

Специализируется на работе с Profile JSON, profile_patch и слиянием в диалоге A4:
схемы Profile/TurnResult и функция merge_profile (core/merge.py).
Активируй при реализации turn-агента, применении profile_patch, правке схем, работе с core/merge.py.

## Инструкции
- Модель только ПРЕДЛАГАЕТ profile_patch. Применяет его детерминированный код (core/merge.py). Модель НИКОГДА не перезаписывает Profile целиком.
- Для существующего проекта/опыта turn-агент возвращает элемент ЦЕЛИКОМ с полным списком bullets (merge заменяет элемент по ключу).
- Оси не путать: track = направление (enum Industry/Research/Education/Startup); target_role = специализация, открытое поле (NLP/ML/CV/Backend/Frontend/Fullstack/Data Engineer…); сектор (Retail/FinTech) в MVP не моделируется.
- Тесты pytest: append+dedup скаляр-списков; обновление элемента по ключу; добавление нового; пустой скаляр не перезаписывает.

## Схемы (core/schemas.py, pydantic v2)
```python
class Profile(BaseModel):
    full_name: Optional[str] = None
    contacts: dict[str, str] = Field(default_factory=dict)
    target_role: Optional[str] = None
    summary: Optional[str] = None
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

class TurnResult(BaseModel):
    reply: str
    profile_patch: dict = Field(default_factory=dict)
    completeness: float = Field(ge=0, le=1)
    ready_to_render: bool = False
```
(Education/Experience/Project/TrackResult/SkillMatch/ResumeOutput/Critique — см. docs/JunMate_plan_v2.1.md). §5.)

## Функция слияния (core/merge.py)
```python
from copy import deepcopy

SCALAR_LISTS = {"skills", "achievements", "languages"}
KEYED_LISTS = {"experience": ("org", "role"), "projects": ("name",), "education": ("institution",)}

def _key(item: dict, fields: tuple) -> tuple:
    return tuple((item or {}).get(f) for f in fields)

def merge_profile(profile: dict, patch: dict) -> dict:
    result = deepcopy(profile)
    for k, v in (patch or {}).items():
        if k in SCALAR_LISTS and isinstance(v, list):
            cur = result.get(k) or []
            result[k] = cur + [x for x in v if x not in cur]
        elif k in KEYED_LISTS and isinstance(v, list):
            cur = result.get(k) or []
            idx = {_key(it, KEYED_LISTS[k]): i for i, it in enumerate(cur)}
            for item in v:
                kk = _key(item, KEYED_LISTS[k])
                if kk in idx:
                    cur[idx[kk]] = {**cur[idx[kk]], **item}
                else:
                    idx[kk] = len(cur); cur.append(item)
            result[k] = cur
        elif isinstance(v, dict):
            base = result.get(k) or {}; base.update(v); result[k] = base
        elif v not in (None, "", []):
            result[k] = v
    return result
```
