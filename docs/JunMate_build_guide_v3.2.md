# JunMate — Build Guide v3.2 (операционный слой для Kodik)

> v3.1 → v3.2: добавлен тировый роутинг моделей (§2a) и правило «merge делает код» (§2b).
> Архитектура/схемы/merge-функция/промпты — в `docs/JunMate_plan_v2.1.md`. Правила репо — `.kodikrules`.

---

## 0. North star

JunMate — разговорный ассистент карьерного старта для IT-джунов под РФ-рынок. Загрузка резюме
(или описание текстом, если резюме нет) → трек → честный gap-анализ → дозаполнение в диалоге →
резюме под hh.ru → PDF + курсы под пробелы. Аудитория — любой IT-джун. Без выдуманного опыта.

---

## 1. Чек-лист: руками (минимум)

- [☑️ ] GitHub-репозиторий `JunMate` (приватный; Streamlit Cloud деплоит и из приватных).
- [☑️ ] Аккаунт Streamlit Community Cloud (через GitHub).
- [☑️ ] Аккаунт OpenRouter + API-ключ (этого достаточно — бесплатно).
- [☑️ ] Google-форма (фидбэк+баг), скопировать ссылку.
- [  ] `data/courses.json` — реальные курсы Stepik/ODS/Karpov вручную (агент не выдумывает).
- [  ] Подключить репо к Streamlit Cloud: app.py, OPENROUTER_API_KEY в Secrets, задеплоить «ok» → URL.
- [  ] (ОПЦ., позже) agentplatform.ru + ключ — только если решишь платную модель на демо-день.

Генерит агент: структура репо, requirements.txt, .gitignore, .env.example, .streamlit/secrets.toml (шаблон), весь код.

---

## 2. LLM-провайдеры (по умолчанию — бесплатно)

Сейчас и для всей разработки — только бесплатные модели OpenRouter, затрат ноль. agentplatform — опциональный апгрейд на демо-день (закомментирован ниже).

```python
PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "extra_headers": {"HTTP-Referer": "<url-приложения>", "X-Title": "JunMate"},
    },
    # ОПЦ. позже: "agentplatform": {"base_url": "https://api.agentplatform.ru/v1",
    #              "key_env": "AGENTPLATFORM_API_KEY", "extra_headers": {}},
}
```

Заголовки HTTP-Referer/X-Title — идентификация приложения для OpenRouter, НЕ данные резюме
(текст резюме идёт в теле запроса). На agentplatform они не нужны → extra_headers пустой.

### 2a. Роутинг моделей по тирам (по умолчанию; подтвердить eval'ом)

Имена `:free`-моделей меняются — на TASK 1 пусть Kodik через sub_agent сверит их актуальность
и заменит снятые. Порядок в каждом тире = primary → fallback.

```python
MODEL_TIERS = {
    "light": [   # лёгкие задачи: классификация трека
        {"provider": "openrouter", "model": "google/gemma-4-26b-a4b-it:free"},
        {"provider": "openrouter", "model": "qwen/qwen3-next-80b-a3b-instruct:free"},
        {"provider": "openrouter", "model": "openai/gpt-oss-20b:free"},
    ],
    "heavy": [   # парсинг, gap, диалог, рерайт, критик: русский + JSON
        {"provider": "openrouter", "model": "qwen/qwen3-next-80b-a3b-instruct:free"},
        {"provider": "openrouter", "model": "google/gemma-4-31b-it:free"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
}
AGENT_TIER = {
    "track": "light",
    "parser": "heavy", "matcher": "heavy", "turn": "heavy",
    "rewriter": "heavy", "critic": "heavy",
}
```

`core/llm.py`: `call_llm(system, user, schema, tier)` идёт по списку тира с force-JSON + pydantic +
один repair + fallback на следующую модель. Почему так: Qwen3-Next силён в русском и structured
output → primary на тяжёлое; Gemma-31b — дисципл/инструкции → фоллбэк; Gemma-26b (быстрая) — на
лёгкий A2; gpt-oss — нижний фоллбэк. После eval можно поменять порядок одной строкой.

### 2b. Слияние profile_patch — делает КОД (не модель)

Применение patch к Profile — детерминированная `core/merge.py.merge_profile()` (код в docs/JunMate_plan_v2.1.md §5a):
скаляр-списки append+dedup; объект-списки (experience/projects/education) — матч по ключу и обновление;
скаляры — только непустые. Модель НИКОГДА не перезаписывает Profile целиком. Для существующего
проекта/опыта turn-агент возвращает элемент целиком с полным списком bullets.

---

## 3. Деплой и секреты

Streamlit Community Cloud: код в Kodik → push в GitHub → автодеплой. `.gitignore` исключает `.env` и
`.streamlit/secrets.toml`. Локально — `.env`; на Cloud — Secrets. `core/config.py` читает st.secrets
первым, фоллбэк на .env. Free-tier засыпает — перед демо прогрей.

---

## 4. Вход «нет резюме»

На экране входа — два пути в один пайплайн: st.file_uploader (PDF) ИЛИ st.text_area («нет резюме? опиши себя текстом»). Оба → один parser (A1) → Profile → интервью A4. Для тонкого профиля ценность — gap-анализ + курсы, не переоформление.

---

## 5. Как давать таски Kodik

Прикрепи docs/JunMate_plan_v2.1.md + этот файл; `.kodikrules` — в корень репо. Таски — по одному, по порядку §6.
После каждого: запусти → проверь → коммит → push. «sub_agent» — точечно (ресёрч/анализ).

---

## 6. Готовые таски

**TASK 0 — Каркас + деплой**
```
Не трогай существующие файлы и папки: .gitignore, .kodik/, docs/. Если файл уже существует — не перезаписывай, при необходимости предложи изменения отдельно. Создавай только отсутствующие файлы по структуре docs/JunMate_plan_v2.1.md §6.
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §6. Создай структуру репо, requirements.txt, .gitignore (исключи .env, .streamlit/secrets.toml), .env.example, шаблон .streamlit/secrets.toml. Реализуй app.py (роутинг +
«ok»), core/config.py (ключ из st.secrets, фоллбэк .env), core/state.py, core/schemas.py (docs/JunMate_plan_v2.1.md §5),
core/merge.py (docs/JunMate_plan_v2.1.md §5a), core/llm.py — провайдер-агностичный с тировым роутингом (docs/JunMate_build_guide_v3.2.md §2a:
PROVIDERS/MODEL_TIERS/AGENT_TIER; call_llm(system,user,schema,tier); force-JSON+repair+fallback;
заголовки только на OpenRouter). Запусти streamlit, покажи «ok». Секреты не коммить.
```

**TASK 1 — Приём резюме/текста и анализ**
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §2,5,7. core/pdf_in.py (PDF→текст, pdfplumber, фоллбэк pypdf; скан без
текста → ошибка). Экран входа с ДВУМЯ путями (file_uploader PDF ИЛИ text_area) → один parser (A1) →
Profile. Агенты track (A2, tier=light), matcher (A3, tier=heavy) по промптам §7. Честный progress bar
(парс→трек→gap). Запиши Profile/Track/Gap в session_state, покажи первое сообщение (трек + 1 строка).
Используй sub_agent: сверь актуальность :free-моделей из MODEL_TIERS на OpenRouter, замени снятые.
```

**TASK 2 — Ядро диалога → резюме → PDF**
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §2,5,5a,7. turn-агент A4 (tier=heavy) → TurnResult. Применяй
profile_patch через core/merge.py.merge_profile (НЕ перезапись). Чат chat_message/chat_input, история
в session_state. Лимит вопросов + порог completeness → агент сам предлагает рендер. По «Да»:
rewriter (A5, hh.ru) → critic (A6) → превью → «Да, хорошо» (pdf_out.py: weasyprint → download_button) /
«Нет, доделываем» (назад).
```

**TASK 3 — Critic, стриминг, стоп, сервис**
```
Следуй .kodikrules. Critic A6 в цикле рендера (grounding_ok=false → один повторный A5 с fixes).
Стриминг (write_stream). Сброс (st.dialog → очистить session_state). Ссылка на Google-форму
(фидбэк+баг). Стоп-кнопку — опционально/в конце; перед ней sub_agent для паттерна остановки стрима
(fragment+поток+threading.Event). Сложно — отложи.
```

**TASK 4 — Курсы и авторизация (режется первой)**
```
Следуй .kodikrules. pages/courses.py: читает data/courses.json (наполняю вручную), фильтр по треку/роли.
courses.json НЕ выдумывай — пустой массив + запись-пример в .example. Затем авторизация
(streamlit-authenticator) — отдельной задачей, в последнюю очередь.
```

**TASK 5 — Качество и финал**
```
Следуй .kodikrules. eval/run_eval.py (accuracy трека + grounding/completeness через Critic; вывести
сравнение моделей по тирам, чтобы при необходимости поменять порядок в MODEL_TIERS). pytest на pdf_in,
merge и схемы. README (проблема, запуск, архитектура, переменные, ограничения, roadmap).
```

---

## 7. График (15.06 → дедлайн)

| Фаза | Дни | Таск | Результат |
|---|---|---|---|
| 0 | 15–16.06 | TASK 0 | каркас + «ok» на Streamlit Cloud (URL) |
| 1 | 17–20.06 | TASK 1 | резюме/текст → трек + gap + первое сообщение |
| 2 | 21–25.06 | TASK 2 | диалог → резюме hh.ru → PDF. **← MVP** |
| 3 | 26–28.06 | TASK 3 | critic, стриминг, сброс/фидбэк, (опц.) стоп |
| 4 | 29.06–01.07 | TASK 4 | курсы → авторизация (режется первой) |
| 5 | 02–дедлайн | TASK 5 | eval, README, демо-видео, монетизация |

agentplatform/платная модель — опциональный шаг на демо-день. До тех пор — бесплатно.
