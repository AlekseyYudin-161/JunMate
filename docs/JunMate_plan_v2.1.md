# JunMate — MVP-спека v2.1 (архитектура, схемы, промпты)

> Справочник архитектуры (контекст для агента Kodik). Операционный слой (деплой, провайдеры, роутинг моделей, таски) — в `docs/JunMate_build_guide_v3.2.md`. Правила репо — в `.kodikrules`.
> Изменения v2 → v2.1: явно зафиксировано «формат hh.ru только на рендере»;
> добавлена детерминированная merge-функция (§5a); уточнён контракт TurnResult.

---

## 1. Позиционирование (north star)

JunMate — разговорный ассистент карьерного старта для IT-джунов под российский рынок труда.
Загрузка резюме (или, если его нет, описание себя текстом) → распознавание трека → честный gap-анализ
под целевую роль → дозаполнение Profile в диалоге → рендер резюме под hh.ru → скачивание PDF + курсы
под пробелы. Аудитория — любой IT-джун (NLP/ML/frontend/backend/…). Без выдуманного опыта.

---

## 2. Архитектура: stateful-диалог над Profile JSON

Источник правды — Profile JSON в st.session_state. Формат hh.ru применяется ТОЛЬКО на рендере (A5).
В диалоге правится Profile (данные), а не текст резюме — это снимает дрейф/коллизии.

```
Загрузка PDF/текста
   │ (один раз)
   ▼
A1 Parser ─▶ Profile ─▶ A2 Track ─▶ A3 Gap(под роль) ─▶ первое сообщение
                 ▲                                              │
                 │ merge_profile(profile, patch)  ← КОД         ▼
                 └────── A4 Turn-агент ◀──── сообщения пользователя (диалог)
                              │ {reply, profile_patch, completeness, ready_to_render}
                              ▼  (по кнопке «Показать резюме»)
                    A5 Rewriter(hh.ru) ─▶ A6 Critic(grounding) ─▶ превью ─▶ PDF
```

- **A4 Turn-агент** (каждый ход, один дешёвый вызов): заполняет Profile через диалог, формат-агностично.
  Вопросы — только по конкретным полям резюме (метрики, стек, ответственность), не абстрактный коучинг.
  При достижении порога/лимита вопросов — ready_to_render=true.
- Тяжёлые A2/A3 — один раз на входе (не каждый ход), результат кэшируется в session_state.
- Слияние patch в Profile — детерминированная функция (§5a), НЕ модель.

---

## 3. Стек

Python 3.12, 
Streamlit (chat_message/chat_input/write_stream/session_state/fragment/progress/dialog/download_button), 
pydantic v2, 
OpenRouter (httpx/openai SDK), 
pdfplumber (pypdf фоллбэк),
weasyprint (PDF), 
streamlit-authenticator (опц.). 
Деплой — Streamlit Community Cloud (см. docs/JunMate_build_guide_v3.2.md §3).

Streamlit-нюансы: всё состояние в session_state; honest progress по стадиям; стоп-кнопка — непростой паттерн (fragment+поток+флаг), помечена опциональной.

---

## 4. Streamlit-специфика (кратко)

1. Rerun-модель: состояние только в session_state.
2. Honest progress: парс 33% → трек 66% → gap 100% (по реальным стадиям).
3. Стоп-кнопка (SHOULD): наивная не прервёт синхронный вызов; настоящий стоп — st.fragment + фоновый
   поток/очередь + threading.Event. Сначала стриминг (write_stream), стоп — потом.
4. Модалки — st.dialog; ссылки — st.link_button; скачивание — st.download_button.

---

## 5. Контракты данных (pydantic v2, core/schemas.py)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    years: Optional[str] = None

class Experience(BaseModel):
    org: str
    role: str
    period: Optional[str] = None
    bullets: list[str] = Field(default_factory=list)

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    stack: list[str] = Field(default_factory=list)
    link: Optional[str] = None

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

class TrackResult(BaseModel):
    track: Literal["Industry", "Research", "Education", "Startup"]
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    runner_up: Optional[str] = None

> Три РАЗНЫЕ оси, не путать:
> - track (направление, фикс. enum): Industry / Research / Education / Startup — тип карьерного пути/среды.
> - target_role (специализация, ОТКРЫТОЕ поле в Profile): NLP / CV / ML / Backend / Frontend / Fullstack /
>   Data Engineer… — задаётся пользователем, ведёт gap-анализ (A3).
> - сектор/индустрия (домен): Retail / FinTech… — в MVP отдельно не моделируется.
> NLP/ML/CV/Backend и т.п. — это target_role (свободный текст), НЕ значения track.

class SkillMatch(BaseModel):
    target_role: str
    have: list[str]
    partial: list[str]
    missing: list[str]
    recommendations: list[str]

class TurnResult(BaseModel):                 # ядро диалога (A4)
    reply: str
    profile_patch: dict = Field(default_factory=dict)   # JSON-merge в Profile (grounded)
    completeness: float = Field(ge=0, le=1)
    ready_to_render: bool = False

class ResumeOutput(BaseModel):
    fmt: Literal["hh", "habr_career", "linkedin"] = "hh"
    content_markdown: str
    warnings: list[str] = Field(default_factory=list)

class Critique(BaseModel):
    grounding_ok: bool
    fabricated_claims: list[str]
    completeness: float = Field(ge=0, le=1)
    format_ok: bool
    fixes: list[str]
```

### 5a. Детерминированное слияние patch → Profile (core/merge.py)

Модель только ПРЕДЛАГАЕТ profile_patch. Слияние делает код:

```python
from copy import deepcopy

SCALAR_LISTS = {"skills", "achievements", "languages"}
# объект-списки: матч по ключу, обновление существующего / добавление нового
KEYED_LISTS = {"experience": ("org", "role"), "projects": ("name",), "education": ("institution",)}

def _key(item: dict, fields: tuple) -> tuple:
    return tuple((item or {}).get(f) for f in fields)

def merge_profile(profile: dict, patch: dict) -> dict:
    """Применяет patch к profile детерминированно. Модель НЕ перезаписывает profile целиком."""
    result = deepcopy(profile)
    for k, v in (patch or {}).items():
        if k in SCALAR_LISTS and isinstance(v, list):
            cur = result.get(k) or []
            result[k] = cur + [x for x in v if x not in cur]            # append + dedup
        elif k in KEYED_LISTS and isinstance(v, list):
            cur = result.get(k) or []
            idx = {_key(it, KEYED_LISTS[k]): i for i, it in enumerate(cur)}
            for item in v:
                kk = _key(item, KEYED_LISTS[k])
                if kk in idx:
                    cur[idx[kk]] = {**cur[idx[kk]], **item}             # обновить элемент целиком
                else:
                    idx[kk] = len(cur); cur.append(item)               # добавить новый
            result[k] = cur
        elif isinstance(v, dict):
            base = result.get(k) or {}; base.update(v); result[k] = base  # contacts и т.п.
        elif v not in (None, "", []):
            result[k] = v                                              # скаляр — только непустой
    return result
```

Правило для A4: для СУЩЕСТВУЮЩЕГО проекта/опыта возвращай элемент целиком с ПОЛНЫМ списком bullets
(merge заменяет элемент по ключу, частичные bullets потеряются).

---

## 6. Структура репозитория

```
junmate/
  app.py
  screens/ chat.py courses.py auth.py welcome.py
  core/ config.py schemas.py llm.py merge.py pdf_in.py pdf_out.py state.py
  agents/ parser.py track.py matcher.py turn.py rewriter.py critic.py
          prompts/ parser.txt track.txt matcher.txt turn.txt rewriter_hh.txt critic.txt
  data/ courses.json
  docs/ JunMate_build_guide_v3.2.md JunMate_plan_v2.1.md
  eval/ samples/ run_eval.py
  tests/ manual_llm_check.py
  .kodikrules .env.example requirements.txt
```

---

## 7. Системные промпты (ключи JSON — англ., инструкции — рус., запрет выдумки везде)

### A1 Parser (prompts/parser.txt)
```
Ты — парсер резюме. Вход — текст из PDF или описание себя текстом.
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
Без markdown и текста вне JSON.
```

### A2 Track (prompts/track.txt)
```
Классифицируй карьерный трек по профилю. 
Треки: Industry (инженерия/прод в компаниях),
Research (наука/публикации/R&D), 
Education (преподавание/менторство), 
Startup (основание/ранний продукт).
Опирайся ТОЛЬКО на факты профиля. Верни JSON TrackResult {track, confidence, evidence[], runner_up}.
```

### A3 Matcher (prompts/matcher.txt)
```
Вход: Profile + target_role. have/partial/missing навыки относительно роли — подтверждай ТОЛЬКО фактами профиля, не приписывай. Дай recommendations.
Если target_role пуст — определи целевую роль по навыкам и проектам профиля (target_role = наиболее вероятная специализация), и в recommendations отметь, что роль предполагаемая и будет уточнена.
Верни JSON SkillMatch {target_role, have[], partial[], missing[], recommendations[]}.
```

### A4 Turn-агент (prompts/turn.txt) — ЯДРО
```
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
```

### A5 Rewriter hh.ru (prompts/rewriter_hh.txt)
```
Редактор резюме под hh.ru. Вход: Profile + Track + SkillMatch.
GROUNDING: используй ТОЛЬКО факты Profile. Запрещено выдумывать опыт/навыки/цифры/работодателей.
Можно: переформулировать, структурировать, акцентировать под роль, усиливать глаголами действия.
Блоки hh.ru: «Желаемая должность», «О себе» (3-5 строк), «Ключевые навыки» (из have/partial;
отдельным подблоком «Знание языков» из Profile.languages, если есть),
«Опыт» (буллеты с глаголами), «Проекты», «Образование». Деловой тон, по-русски.
Если target_role пуст — используй вероятную роль из навыков/проектов или общую формулировку, не выдумывая.
Если опыта работы (experience) нет — блок «Опыт» опусти, сделай акцент на «Проектах». Не перемещай проекты в опыт.
Названия технологий, инструментов и языков — на английском (Python, Docker, SQL); общие слова — по-русски.
Пробелы (missing) НЕ вписывай в опыт — вынеси в warnings.
Верни ТОЛЬКО JSON ResumeOutput {fmt:"hh", content_markdown, warnings[]}.
```

### A6 Critic (prompts/critic.txt)
```
Строгий проверяющий резюме (контроль фактологичности). Вход: исходный Profile и сгенерированный текст резюме.
Проверь по пунктам:
1. grounding_ok — есть ли в резюме факты (работодатели, должности, цифры, метрики, технологии), которых НЕТ в Profile. Любой такой факт → в fabricated_claims. Переформулировка имеющихся фактов выдумкой НЕ считается.
2. completeness (0..1) — насколько полно резюме отражает Profile.
3. format_ok — соответствие структуре hh.ru (нужные блоки на месте).
4. fixes — конкретные правки для устранения проблем.
Верни ТОЛЬКО JSON Critique {grounding_ok, fabricated_claims[], completeness, format_ok, fixes[]}.
grounding_ok=false → оркестратор делает ОДИН повторный рендер A5 с fixes.
```

---

## 8. LLM-надёжность

Force-JSON + pydantic-валидация + один repair-вызов + fallback по тиру модели (см. docs/JunMate_build_guide_v3.2.md §2a).
Имена :free-моделей не зашивать намертво. Температура: извлечение/классификация 0–0.2, диалог/рерайт 0.4–0.6.
Заголовки HTTP-Referer/X-Title — только на OpenRouter.
