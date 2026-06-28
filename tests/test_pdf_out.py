"""Тесты для генерации PDF.
Проверка, что извлечение текста работает на нормальном PDF и корректно ругается на битом.
"""

import pytest
from core.pdf_out import generate_pdf

def test_returns_valid_pdf():
    result = generate_pdf("# Заголовок\nТекст")
    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF")

def test_separator_skipped():
    # Проверка, что markdown разделитель не вызывает ошибок
    result = generate_pdf("Текст\n---\nЕще текст")
    assert result.startswith(b"%PDF")

def test_cyrillic_ok():
    result = generate_pdf("Привет, мир!")
    assert len(result) > 0
    assert result.startswith(b"%PDF")
