---
name: deploy
description: Закоммитить текущие изменения, запушить в GitHub и проверить автодеплой на Streamlit Community Cloud.
---

Последовательность для публикации текущего рабочего состояния.

## Предусловия (проверить один раз, в Фазе 0)
- Репозиторий подключён к Streamlit Community Cloud, указан app.py.
- В Secrets приложения на Cloud задан OPENROUTER_API_KEY.
- .gitignore исключает .env и .streamlit/secrets.toml (секреты НЕ коммитим).

## Шаги
1. Убедиться, что приложение запускается локально: `streamlit run app.py` — без ошибок.
2. Проверить, что в staged-изменениях нет секретов:
   `git status` и `git diff --cached --name-only` (не должно быть .env, secrets.toml).
3. Коммит и пуш:
   ```bash
   git add -A
   git commit -m "<краткое описание изменений>"
   git push
   ```
4. Streamlit Cloud подхватит push и пересоберёт приложение автоматически.
   Открыть публичный URL, дождаться завершения редеплоя, проверить, что страница работает.
5. Если сборка упала — посмотреть логи на Cloud (обычно: отсутствует пакет в requirements.txt
   или системная либа для weasyprint → добавить в requirements.txt / packages.txt и повторить /deploy).

## Перед демо
Открыть приложение заранее — free-tier засыпает при простое (холодный старт).
