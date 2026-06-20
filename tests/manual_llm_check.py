import logging
from agents.parser import parse_resume


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)   # убрать шум httpx


def test_parser():
    # test_text = """
    # Иван Петров, Backend разработчик. Обучение: РТУ МИРЭА: 2024 г. - настоящее время; 1.5 года стажировки в Яндекс на позиции backend разработчика. Стек: Django, Cron, Frenos, JS, Docker. Языки: Английский C1
    # """
    test_text = """
    Харченко Владислав, Data Scientist
    Phone: +7-906-922-50-45
    Email: vlad_harchenko5555555@mail.ru Tg: @yhyzys
    Moscow
    Обо мне
    Специализируюсь на работе с данными и машинном обучении. Имею глубокое понимание современных архитектур нейросетей и сильную алгоритмическую базу. Нацелен на решение сложных бизнес-задач и эффективную работу в команде.
    Навыки
    Tech stack: Python, SQL, Docker, Git, CI/CD, Nginx, centrifuge Linux, FastAPI, Django
    ML/Data: PyTorch, NumPy, Pandas, HuggingFace, Scikit-learn, LangChain,
    Опыт
    • Участвовал в конференции в рамках университета. git
    • Участвовал в соревновании codenrock по машинному обучению. git Детекция аномалий в SQL-запросах
    • Реализовал ML-модель для автоматического выявления потенциальных уязвимостей, анализируя статистику запросов и системные метрики
    • Результат: Валидированы на 30+ сценариях атак, добился минимума ложных тревог (FPR < 5%) при средней задержке 6.4 сек.
    Разработка RAG-системы для технической документации
    • Спроектировал вопросно-ответного бота (LangChain, FAISS, OpenAI API) для работы с базой знаний объемом более 50 страниц
    • Настроил пайплайн извлечения информации, сократив среднее время поиска точного ответа по документации с нескольких минут до 10–12 секунд
    • Добился высокой релевантности ответов бота, снизив количество галлюцинаций LLM за счет тонкой настройки промптов и параметров поиска (Top-K).
    Рекомендательная система (RecSys)
    • Разработал систему рекомендаций блюд/товаров, обучив модели ранжирования (CatBoost, YetiRank) на датасете из более 8000 записей.
    • Улучшил качество выдачи (по метрике NDCG@10 на ~12-15% по сравнению с базовым алгоритмом рекомендаций)
    • Провел тщательный разведочный анализ (EDA) и Feature Engineering, обработав около 20 категориальных и числовых признаков.
    """

    print(f"--- Starting test with text: {test_text} ---")

    try:
        profile = parse_resume(test_text)
        print("--- Success! Profile: ---")
        print(profile.model_dump_json(indent=2))
    except Exception as e:
        print("--- Failed! ---")
        # Ошибка уже залогирована в core/llm.py, здесь просто выводим тип и сообщение
        print(f"{type(e).__name__}: {e}")

if __name__ == "__main__":
    test_parser()
