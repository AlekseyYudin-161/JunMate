"""Извлечение текста из PDF (pdfplumber + pypdf)."""

import logging
from io import BytesIO
import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)
logging.getLogger("pdfminer").setLevel(logging.ERROR)   # заглушение warning'и FontBBox на резюме, написанных нейронками


def extract_text(pdf_bytes: bytes) -> str:
    """Извлекает текст из PDF. Если текста нет (скан) — выбрасывает ValueError."""
    text_content = ""

    # 1. Попытка через pdfplumber (лучше сохраняет структуру)
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            text_content = "\n".join(pages).strip()
    except Exception as e:
        logger.warning("\npdfplumber failed: %s", e)

    # 2. Фоллбэк на pypdf, если первый метод не дал текста
    if not text_content:
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text_content = "\n".join(pages).strip()
        except Exception as e:
            logger.warning("\npypdf failed: %s", e)

    if not text_content:
        raise ValueError(
            "Не удалось извлечь текст из PDF. Возможно, это скан или защищённый файл. "
            "Пожалуйста, используйте текстовый PDF или введите данные вручную."
        )

    return text_content
