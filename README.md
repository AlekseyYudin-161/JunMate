> Required Notice: Copyright 2026 Aleksey Yudin (https://github.com/AlekseyYudin-161)

[![CI](https://github.com/AlekseyYudin-161/JunMate/actions/workflows/ci.yml/badge.svg)](https://github.com/AlekseyYudin-161/JunMate/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit-FF4B4B?logo=streamlit)](https://junmate-resumecopilot.streamlit.app)

# JunMate — разговорный ассистент исправления резюме для IT-джунов под российский рынок труда.

Пользователь загружает резюме (а если его нет — описывает себя текстом). JunMate `в диалоге` распознаёт карьерный трек, делает честный анализ пробелов под целевую роль и дозаполняет резюме под формат `hh.ru` — строго по фактам пользователя, без выдуманного опыта. На выходе — готовое к скачиванию PDF-резюме и подборка курсов (Stepik/ODS/Karpov) под выявленные пробелы. 

**Ценность**: даже из тонкого профиля собрать честное резюме и показать конкретный следующий шаг, а не приукрасить то, чего нет.


## Как это работает

Stateful-диалог над каноническим Profile (JSON). Конвейер из шести специализированных `агентов`:

- **A1 Parser** — извлекает Profile из текста резюме/PDF (только факты, без додумывания).
- **A2 Track** — классифицирует карьерный трек (Industry / Research / Education / Startup).
- **A3 Matcher** — gap-анализ навыков под целевую роль (have / partial / missing).
- **A4 Turn** — ведёт диалог, дозаполняя Profile по одному вопросу за ход.
- **A5 Rewriter** — рендерит резюме под структуру hh.ru.
- **A6 Critic** — проверяет фактологичность результата (LLM-as-a-judge).

**Ключевые принципы:** GROUNDING (агенты не выдумывают факты), слияние данных делает детерминированный код (`core/merge.py`), а не модель; формат hh.ru применяется только на рендере.


## Стек

Python 3.12 · Streamlit · pydantic v2 · pdfplumber (вход) · weasyprint (PDF-выход). 

LLM — через proxyapi (OpenAI-совместимый), `gpt-4.1-mini` как основная модель, бесплатные модели OpenRouter как фоллбэк. 

Деплой — Streamlit Community Cloud.


## Запуск

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Ограничения

Сканы-PDF (без текстового слоя) не распознаются — для таких случаев есть ручной ввод текстом. Качество извлечения зависит от структурированности исходного резюме.


# Статус разработки согласно `JunMate_build_guide_v3.2.md`

Проект в активной разработке (трек Student, SOLO разработчик).

### Реализовано 4/5 проекта: 

- ✅ Каркас приложения, провайдер-агностичный LLM-клиент (force-JSON, repair, fallback по тирам, учёт токенов/стоимости).
- ✅ Приём резюме (PDF/текст), парсинг (A1), классификация трека (A2).
- gap-анализ (A3). Проверено на реальных hh.ru-резюме.
- Ядро диалога (A4), рендер hh.ru (A5) и PDF — целевой MVP.
- Критик (A6)

### Еще реализовать (TASK 1.3 - TASK 5)
- курсы под пробелы, eval.

