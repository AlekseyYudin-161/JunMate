import logging
import sys
import os

# Добавляем корень проекта в sys.path для корректных импортов при запуске из любой папки
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from agents.parser import parse_resume

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)   # убрать шум httpx

def test_parser():
    test_text = "Иван Иванов. Frontend разработчик. Обучение: Нетология, 2 года. Стек: Django, Cron, JS, Docker. Языки: Английский B2"
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
