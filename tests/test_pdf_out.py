"""Тесты генерации PDF (core/pdf_out.py).
Проверяют, что рендер не падает на разном markdown (заголовки, кириллица,
разделители ---) и отдаёт валидный PDF. Защита от багов рендера вроде «• --».
"""

from core.pdf_out import generate_pdf

def test_returns_valid_pdf():
    """Проверка, возвращаются байты валидного PDF (сигнатура %PDF)."""

    result = generate_pdf("# Заголовок\nТекст")
    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF")

def test_separator_skipped():
    """Проверка, что Markdown-разделитель --- не ломает рендер."""

    result = generate_pdf("Текст\n---\nЕще текст")
    assert result.startswith(b"%PDF")

def test_cyrillic_ok():
    """Проверка, что Кириллица рендерится без исключений, PDF непустой."""

    result = generate_pdf("Привет, мир!")
    assert len(result) > 0
    assert result.startswith(b"%PDF")
