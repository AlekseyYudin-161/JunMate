"""Проверка Генерация PDF из Markdown через fpdf2."""

import logging
from core.pdf_out import generate_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

SAMPLE_OUT = """
# Желаемая должность
Python-разработчик

## О себе
Python-разработчик с 2 годами практики и опытом реализации пет-проектов на Django и Flask.

## Ключевые навыки
* Django
* Flask
* PostgreSQL

## Проекты
Backend интернет-магазина на Django
* Разработал каталог товаров, корзину и оформление заказов.
* Реализовал обработку платежей через API эквайринга на Python.
"""


def main():
    pdf_bytes = generate_pdf(SAMPLE_OUT)
    with open("test_resume.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF создан: test_resume.pdf")

if __name__ == "__main__":
    main()
