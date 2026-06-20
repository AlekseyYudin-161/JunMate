import logging
from agents.parser import parse_resume


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)   # убрать шум httpx


def test_parser():
    test_text = """
    Иван Петров, Backend разработчик. Обучение: РТУ МИРЭА: 2024 г. - настоящее время; 1.5 года стажировки в Яндекс на позиции backend разработчика. Стек: Django, Cron, Frenos, JS, Docker. Языки: Английский C1
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
