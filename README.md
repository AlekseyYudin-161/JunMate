> Required Notice: Copyright 2026 Aleksey Yudin (https://github.com/AlekseyYudin-161)

[![CI](https://github.com/AlekseyYudin-161/JunMate/actions/workflows/ci.yml/badge.svg)](https://github.com/AlekseyYudin-161/JunMate/actions/workflows/ci.yml)

# JunMate — разговорный ассистент-корректор резюме для IT-джунов под российский рынок труда.

Пользователь загружает резюме (а если его нет — описывает себя текстом). JunMate `в диалоге` распознаёт карьерный трек, делает честный анализ пробелов под целевую роль и дозаполняет резюме под формат `hh.ru` — строго по фактам пользователя, без выдуманного опыта. На выходе — готовое к скачиванию PDF-резюме корректной кириллицей и кликабельными ссылками.

**Ценность**: даже из тонкого профиля собрать честное структурированное резюме — не приукрашивая то, чего нет. 
Главный принцип — **GROUNDING**: система не фабрикует факты.

## Демо
📹 [Видео-демонстрация youtube](https://youtu.be/B-h7gtEM6HY) — полный процесс работы.

[Видео-демонстрация googleDrive](https://drive.google.com/file/d/1XxDhgPxNDoJIhsmh0d1YCyrZArZ9bngkr/view?usp=sharing)

🔗 **[Попробовать вживую](https://junmate-resumecopilot.streamlit.app)** — рабочее приложение (может быть на паузе для экономии ресурсов)


## Как это работает

Stateful-диалог над каноническим Profile (JSON). Конвейер из шести специализированных `агентов`:

- **A1 Parser** — извлекает Profile из текста резюме/PDF (только факты, без додумывания).
- **A2 Track** — классифицирует карьерный трек (Industry / Research / Education / Startup).
- **A3 Matcher** — gap-анализ навыков под целевую роль (have / partial / missing).
- **A4 Turn** — ведёт диалог, дозаполняя Profile по одному вопросу за ход.
- **A5 Rewriter** — рендерит резюме под структуру hh.ru.
- **A6 Critic** — проверяет фактологичность результата (LLM-as-a-judge).

**Ключевые принципы:** GROUNDING (агенты не выдумывают факты), слияние данных делает детерминированный код (`core/merge.py`), а не модель; формат hh.ru применяется только на рендере.


## LLM models

LLM — через proxyapi (OpenAI-совместимый), `gpt-4.1-mini` как основная модель, бесплатные модели OpenRouter как фоллбэк. 

Деплой — Streamlit Community Cloud (авто-деплой на push).


## Качество (evaluation)

- **Классификация трека (A2):** 90–100% accuracy на размеченном наборе из 10 резюме, стабильность ответов 100%. Подробности и error-analysis — в [`eval/EVAL_RESULTS.md`](eval/EVAL_RESULTS.md).
- **Grounding (A5→A6):** 3/3 без выдуманных фактов на контрольной выборке.
- **Тесты:** детерминированное ядро (merge, PDF I/O) покрыто юнит-тестами (pytest), автопрогон через `CI` на каждый push.


## Запуск

```bash
git clone https://github.com/AlekseyYudin-161/JunMate.git

cd JunMate

cp .env.example .env

nano .env                                  # Заполните .env файл

python3 -m venv .venv

source .venv/bin/activate                  # On Windows use: .venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py
```


## Архитектура

app.py                 — точка входа, роутинг экранов

screens/               — welcome (загрузка), chat (диалог + рендер + PDF)

core/                  — config, schemas, llm, merge, pdf_in, pdf_out, state

agents/                — parser, track, matcher, turn, rewriter, critic (A1–A6)

agents/prompts/        — эталонные тексты системных промптов (документация)

tests/                 — детерминированные юнит-тесты

eval/                  — датасет, скрипт оценки, EVAL_RESULTS.md


## Ограничения

- **Сканы-PDF** (без текстового слоя) не распознаются — для таких случаев есть ручной ввод текстом.
- **Ссылки-якоря в hh-PDF:** GitHub/Telegram, сохранённые как гиперссылки под видимым текстом, парсер не извлекает напрямую — добираются в диалоге (надёжный фикс — в roadmap).
- Качество извлечения зависит от структурированности исходного резюме; `gpt-4.1-mini` недетерминирован (граница Research/Education для академических джунов размыта).


## Roadmap

**Инфраструктура:**

- Извлечение URL из аннотаций PDF (`/Annots`) — автоматический сбор ссылок-якорей.
- Подбор курсов (Stepik / ODS / Karpov) под выявленные пробелы.
- Расширение покрытия полей hh.ru (контакты-расширения, доп. секции).
- Вынос промптов из кода в загружаемые файлы.
- Миграция UI на NiceGUI (release v2).

**Контент:**

- Загрузка и корректировка **мотивационного письма** под обновлённое резюме (с экспортом в PDF).

**Function-calling (данные вместо догадок модели):**

- `search_courses(track, target_role, gap)` — агент gap-анализа вызывает инструмент поиска курсов под выявленные пробелы (`data/courses.json` или внешние API: Stepik / ODS / Karpov Courses и пр.).
- `fetch_hh_role_requirements(target_role)` — подтягивание типовых требований по роли с hh.ru, чтобы gap-анализ опирался на реальные данные рынка, а не только на знания модели.

**Production observability:**

- База данных (Supabase или отечественные аналоги) с таблицами пользователей и резюме (вход/выход).
- Метрики: число сгенерированных резюме (день/месяц/квартал), расход токенов и стоимость.
- Дашборды мониторинга (Yandex DataLens / Superset) для production-аналитики.

---

Трек `Student` · solo-разработка · хакатон `Kodik Launchpad`.

---

## Технологии проекта

![Python](https://img.shields.io/badge/Python_3.12-FFFFFF?style=for-the-badge&logo=python&logoColor=306998&color=000000)
![Streamlit](https://img.shields.io/badge/Streamlit_1.58.0-FFFFFF?style=for-the-badge&logo=streamlit&logoColor=FF4B4B&color=000000)
![Pydantic](https://img.shields.io/badge/Pydantic_2.13.4-FFFFFF?style=for-the-badge&logo=pydantic&logoColor=306998&color=000000)
![Pylint](https://img.shields.io/badge/Pylint_3.3.5-FFFFFF?style=for-the-badge&logo=Pylint&logoColor=306998&color=000000)
![Pytest](https://img.shields.io/badge/Pytest_9.1.1-FFFFFF?style=for-the-badge&logo=pytest&logoColor=306998&color=000000)


![PDFplumber](https://img.shields.io/badge/PDFplumber_0.11.10-FFFFFF?style=for-the-badge&logo=PDFplumber&logoColor=306998&color=000000)
![fpdf2](https://img.shields.io/badge/fpdf2_2.8.7-FFFFFF?style=for-the-badge&logo=PDFplumber&logoColor=306998&color=000000)


![OpenAI](https://img.shields.io/badge/OpenAI_2.43.0-FFFFFF?style=for-the-badge&logo=ai&logoColor=306998&color=000000)
