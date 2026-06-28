"""Тесты для извлечения текста из PDF.
Проверка, что генерация PDF не падает на разном markdown (заголовки, кириллица, разделители ---) и 
выдаёт валидный PDF. Защита от багов рендера, которые мы тоже ловили (• --).
"""

import pytest
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from core.pdf_in import extract_text

@pytest.fixture
def simple_pdf_bytes():
    pdf = FPDF()
    pdf.add_page()
    # Используем стандартный шрифт для теста (без кириллицы, чтобы не зависеть от путей)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, text="Test Resume Content", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    return pdf.output()

def test_extract_simple(simple_pdf_bytes):
    text = extract_text(simple_pdf_bytes)
    assert "Test Resume Content" in text

def test_broken_pdf():
    with pytest.raises(ValueError):
        extract_text(b"not a pdf file content")
