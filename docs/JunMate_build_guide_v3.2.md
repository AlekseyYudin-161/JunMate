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
- [☑️ ] Подключить репо к Streamlit Cloud: app.py, OPENROUTER_API_KEY в Secrets, задеплоить «ok» → URL.

Генерит агент: структура репо, requirements.txt, .gitignore, .env.example, .streamlit/secrets.toml (шаблон), весь код.

---

## 2. LLM-провайдеры (основной — proxyapi (платный), фоллбэк — openrouter free)

```python
PROVIDERS = {
    "proxyapi": {
        "base_url": "https://api.proxyapi.ru/openai/v1",
        "key_env": "PROXIAPI_API_KEY",
        "extra_headers": {},
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "extra_headers": {"HTTP-Referer": "https://junmate.streamlit.app", "X-Title": "JunMate"},
    },
}
```

Заголовки HTTP-Referer/X-Title — идентификация приложения для OpenRouter, НЕ данные резюме
(текст резюме идёт в теле запроса). На agentplatform/proxyapi они не нужны → extra_headers пустой.

### 2a. Роутинг моделей по тирам (по умолчанию; подтвердить eval'ом)

Порядок в каждом тире = primary → fallback.

```python
MODEL_TIERS = {
    "light": [
        {"provider": "proxyapi", "model": "gpt-4.1-nano"},
        {"provider": "proxyapi", "model": "gpt-4.1-mini"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
    "heavy": [
        {"provider": "proxyapi", "model": "gpt-4.1-mini"},
        {"provider": "openrouter", "model": "openai/gpt-oss-120b:free"},
    ],
}

AGENT_TIER = {
    "track": "light",
    "parser": "heavy",
    "matcher": "heavy",
    "turn": "heavy",
    "rewriter": "heavy",
    "critic": "heavy",
}
```

`core/llm.py`: `call_llm(system, user, schema, tier)` идёт по списку тира с force-JSON + pydantic + один repair + fallback на следующую модель. 

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

TASK 1.1
```
Не трогай и не переписывай готовые файлы: agents/parser.py (A1 отлажен) и core/schemas.py (валидаторы). A1 используй как есть.
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §2,5. Создай core/pdf_in.py: PDF→текст через pdfplumber
(фоллбэк pypdf); если текста нет/скан → верни понятную ошибку, без OCR. 
Сделай экран входа с ДВУМЯ путями: st.file_uploader (PDF) ИЛИ st.text_area («нет резюме? опиши себя текстом»). Оба пути → один parse_resume (A1) → Profile. Покажи полученный Profile через st.json для проверки. Запиши Profile в st.session_state.
Не запускай лишних сетевых вызовов. Запусти streamlit, дай проверить.
```

TASK 1.2
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §5,7. Реализуй только agents/track.py по образцу parser.py:
функция определяет TrackResult из Profile, промпт A2 из §7, вызов через call_llm с tier="heavy".
Имена моделей не хардкодь — только из MODEL_TIERS. После парса вызови track в welcome.py, результат покажи (st.json) и запиши в st.session_state. Matcher НЕ трогай — он будет отдельной задачей. Не трогай parser/schemas. Запусти, дай проверить.
```

TASK 1.3
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §5,7. Реализуй agents/matcher.py по образцу parser.py/track.py:
SkillMatch из Profile + target_role, промпт A3 из §7, call_llm с tier="heavy", agent="matcher".
ВАЖНО: если target_role пуст (null) — НЕ выдумывай роль; пропусти gap с пометкой «роль уточним в диалоге»
или используй track как грубый ориентир.
Собери полный вход-пайплайн:
парс → трек → gap, с честным progress bar по реальным стадиям (парс 33% → трек 66% → gap 100%). Запиши Profile/Track/Gap в st.session_state. Покажи первое сообщение пользователю СТАТИЧНЫМ текстом
(трек + краткая сводка gap), без вызова диалогового агента A4 — его ещё нет. Не трогай готовые файлы (parser.py, track.py, schemas.py, llm.py, pdf_in.py, config.py).
Запусти, дай проверить.
```

**TASK 2 — Ядро диалога → резюме → PDF**

TASK 2.1 - Ядро диалога (A4 + merge)
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §2,5,5a,7. Реализуй agents/turn.py: turn-агент A4
(tier="heavy", agent="turn") по промпту §7 → TurnResult. Применяй profile_patch ТОЛЬКО через
core/merge.py.merge_profile (НЕ перезапись Profile). Чат на st.chat_message/st.chat_input, история
диалога и Profile — в st.session_state. Каждый ход показывай обновлённый Profile (временно st.json)
для проверки merge. Лимит вопросов (например 6) ИЛИ completeness ≥ порог → ready_to_render=true,
покажи кнопку «Показать резюме» (пока без рендера). Не трогай готовые файлы. Запусти, дай проверить.
```

TASK 2.2 - Рендер hh.ru (A5) + превью
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §5,7. Реализуй agents/rewriter.py: A5 (tier="heavy", agent="rewriter") по промпту §7
→ ResumeOutput. По кнопке «Показать резюме»: rewriter(Profile + Track + SkillMatch + история диалога)
→ превью content_markdown через st.markdown + показать warnings. Историю диалога передавай в A5, чтобы он мог восстановить описания проектов/опыта, проговорённые в диалоге, но не попавшие в Profile
(строго в рамках GROUNDING — только реально сказанное). Кнопки «Хорошо» / «Доделать» (назад в диалог).
Не трогай готовые файлы (parser, track, matcher, turn, schemas, llm, merge, pdf_in).
```

TASK 2.3a - Critic (A6) + цикл (без PDF)
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §5,7. Реализуй agents/critic.py: A6 (tier="heavy", agent="critic") → Critique по промпту §7. A6 получает на вход Profile + историю диалога + текст резюме (история обязательна, иначе факты, взятые A5 из диалога, ложно помечаются выдумкой).
Логика цикла в коде (НЕ в промпте): после A5 вызови A6; если grounding_ok=false — сделай РОВНО ОДИН повторный вызов A5, передав ему critique.fixes; больше не повторяй (без петли). 
Результат A6 (warnings/fixes) покажи пользователю в превью под резюме.
Не трогай готовые файлы (parser, track, matcher, turn, rewriter, schemas, llm, merge, pdf_in, welcome).
Сделай, я сам проверю.
```

TASK 2.3b — PDF (отдельно, после того как A6 заработает)
```
Следуй .kodikrules и docs/JunMate_plan_v2.1.md §5,6. Реализуй core/pdf_out.py через библиотеку fpdf2 (weasyprint удалён — не работает на Streamlit Cloud, используем fpdf2).
Функция принимает markdown-текст финального резюме (res["content_markdown"]) и рендерит PDF: парсит строки markdown — заголовки (# / ##) делает крупнее, буллеты (• / - / *) выводит с отступом, обычный текст абзацами. ОБЯЗАТЕЛЬНО подключи кириллический шрифт из репозитория:
pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf") и pdf.set_font("DejaVu") — иначе русский текст будет квадратиками. Используй multi_cell для переноса длинных строк.
Подключи в screens/chat.py: по кнопке «Хорошо» вызови pdf_out(res["content_markdown"]) и отдай через st.download_button с именем resume.pdf (mime "application/pdf").
Не трогай другие готовые файлы (agents/*, core/* кроме нового pdf_out, schemas, llm, merge, welcome).
Сделай, я сам проверю.
```

**TASK 3 — UI/UX, кнопки feedback/Сброс диалога**
```
Следуй .kodikrules. Доработки UI в screens/chat.py и app.py. НЕ трогай agents/*, core/*, логику диалога/рендера, рендер резюме, критика, PDF.
1. Убери кнопку «Сбросить всё» из app.py (sidebar).
2. В screens/chat.py над полем st.chat_input («Ваш ответ») размести две кнопки в одну строку
   через st.columns([1, 4, 2]) (узкая слева — распорка посередине — колонка справа):
   - в левой (узкой) колонке: st.popover с иконкой «➕», внутри две ссылки друг под другом —
     st.link_button «Сообщить о баге» (https://forms.gle/R4FPFTnoy6sjt7Mj7) и st.link_button «Обратная связь» (https://forms.gle/7oikcFZEs5QupgJC9) на две разные Google-формы;
   - в правой колонке: кнопка «Сбросить диалог» (type="primary").
   Средняя колонка пустая — распорка, чтобы «➕» был слева, «Сбросить диалог» справа.
3. По «Сбросить диалог» открывай st.dialog «Сбросить диалог» с текстом:
   «Сбросить диалог? Улучшение вашего резюме сбросится и диалог начнётся заново.
   Это действие необратимо.» и двумя кнопками внутри модалки:
   - «Отмена» (type="secondary") — просто закрывает модалку;
   - «Сбросить» (type="primary") — очищает весь session_state и делает st.rerun
     (возврат на welcome-экран).
4. Debug-панель Profile (st.json в сайдбаре) ОСТАВЬ как есть — без кнопки сброса.
   Цвета кнопок — штатные type=primary/secondary, НЕ CSS (Streamlit сам адаптирует под тему).
Сделай, я сам проверю.
```

**TASK 4 — Курсы и авторизация (режется первой)**
```
Следуй .kodikrules. pages/courses.py: читает data/courses.json (наполняю вручную), фильтр по треку/роли.
courses.json НЕ выдумывай — пустой массив + запись-пример в .example. Затем авторизация
(streamlit-authenticator) — отдельной задачей, в последнюю очередь.
```

**TASK 5 — Качество и финал**

TASK 5a - Unit-tests
```
Следуй .kodikrules. Создай детерминированные тесты (pytest) — БЕЗ вызовов LLM/API.
НЕ трогай логику в agents/, core/ — только добавь файлы в tests/.

tests/test_merge.py — тестируй core.merge.merge_profile:
- test_add_skill_no_overwrite: в профиль со skills=["Python"] патч skills=["Docker"] →
  результат содержит и "Python", и "Docker" (не затёрся).
- test_update_project_keeps_bullets: профиль с проектом, у которого 2 bullets; патч обновляет
  тот же проект с 3 bullets → в результате у проекта 3 bullets (полная замена элемента, не потеря).
- test_contacts_preserved: профиль с contacts={"email":"a@b.ru","phone":"123"}; патч
  contacts={"email":"a@b.ru","phone":"123","github":"url"} → email и phone на месте, github добавлен.
- test_empty_patch: пустой патч {} → профиль не изменился.

tests/test_pdf_out.py — тестируй core.pdf_out.generate_pdf:
- test_returns_valid_pdf: generate_pdf("# Заголовок\nтекст") возвращает bytes, начинающиеся с b"%PDF".
- test_separator_skipped: в выводе для "---" не падает и не крашится (markdown-разделитель).
- test_cyrillic_ok: generate_pdf с кириллицей не кидает исключение, возвращает непустые байты.

tests/test_pdf_in.py — тестируй core.pdf_in.extract_text:
- test_extract_simple: создай минимальный PDF в фикстуре (через fpdf2), извлеки текст,
  проверь, что вернулась непустая строка.
- test_broken_pdf: на байтах-не-PDF (b"not a pdf") extract_text кидает понятную ошибку (ValueError).

Сделай, дай инструкцию по запуску. Я сам проверю.
```

TASK 5b - eval agents (LLM)
```
Следуй .kodikrules. Создай eval/run_eval.py — скрипт оценки качества (запускается вручную,
НЕ в CI, требует API-ключа). НЕ трогай agents/, core/ — только читай и вызывай.

Структура скрипта:

1. ЗАГРУЗКА: прочитай eval/labels.json (список {id, file, true_track}).
   Для каждого прочитай текст резюме из eval/dataset/{file}.

2. ШАГ 3 — ACCURACY ТРЕКА (2 прогона каждого резюме):
   Для каждого резюме дважды:
     - profile = parse_resume(text)        # A1
     - track_result = classify_track(profile)  # A2
     - сравни track_result.track с true_track
   Замеряй time.time() вокруг каждого вызова (для шага 5).
   Считай: accuracy по каждому прогону (верные/всего), стабильность (совпали ли 2 прогона).
   Печатай таблицу: id | true_track | прогон1 | прогон2 | совпало с эталоном.
   Выведи итоговую accuracy и confusion (какой трек с каким путается).

3. ШАГ 4 — GROUNDING (только 3 резюме: ivan, dudii, ilia — по id):
   Для каждого:
     - profile = parse_resume(text)           # A1 (history пустая — без диалога)
     - resume = rewrite_resume(profile, track, gap=None, history=[])  # A5
     - critique = critique_resume(profile, history=[], content_markdown=resume.content_markdown)  # A6
     - запиши critique.grounding_ok и critique.fabricated_claims
   Печатай: id | grounding_ok | fabricated_claims.
   Выведи долю grounding_ok=true.

4. ШАГ 5 — LATENCY (попутно, из замеров time в шаге 2-3):
   Печатай среднее время на агента (A1, A2, A5, A6).
   Если core/llm возвращает usage-токены — собери и их; если нет, только время.

5. Все результаты печатай в консоль структурированно (таблицы текстом).
   Оберни каждый вызов агента в try/except, чтобы один сбой не уронил весь прогон.

6. В САМОМ КОНЦЕ напечатай отдельный блок "=== ИТОГ ДЛЯ EVAL_RESULTS ===" с агрегатами:
   accuracy трека (X/N = %), доля стабильных (2 прогона совпали), grounding-rate (M/3),
   средняя latency по агентам. Этот блок — для копирования в EVAL_RESULTS.md.

НЕ запускай скрипт (он тратит API-баланс) — только создай, я сам проверю.
```

---

## 7. График (15.06 → дедлайн)

| Фаза | Таск | Результат |
|---|---|---|---|
| 0 | TASK 0 | каркас + «ok» на Streamlit Cloud (URL) |
| 1 | TASK 1 | резюме/текст → трек + gap + первое сообщение |
| 2 | TASK 2 | диалог → резюме hh.ru → PDF. **← MVP** |
| 3 | TASK 3 | critic, стриминг, сброс/фидбэк, (опц.) стоп |
| 4 | TASK 4 | курсы → авторизация (режется первой) |
| 5 | TASK 5 | eval, README, демо-видео, монетизация |
