"""Генерация PDF из Markdown через fpdf2."""

import os
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _clean(text: str) -> str:
    """Убирает markdown-звёздочки (**bold**, *italic*, _underscore_) — fpdf2 их не парсит."""
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    return text


def generate_pdf(markdown_text: str) -> bytes:
    """Рендерит Markdown-текст в PDF байты."""
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)                     # явные поля слева/сверху/справа
    pdf.add_page()

    # Подключаем кириллический шрифт
    font_path = "fonts/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        # Если запуск не из корня, пробуем найти шрифт относительно файла
        font_path = os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf")

    pdf.add_font("DejaVu", "", font_path)
    pdf.set_font("DejaVu", size=12)

    # ── Постобработка: убрать пустые блоки (заголовок без содержимого) ──
    block_titles = {"Опыт работы", "Проекты", "Образование", "Контакты",
                    "Ключевые навыки", "Знание языков", "Достижения", "О себе"}
    raw_lines = [ln.strip() for ln in markdown_text.split("\n")]
    lines = []
    for i, ln in enumerate(raw_lines):
        # если строка — название блока, проверяем, есть ли под ним содержимое
        clean_ln = ln.lstrip("# ").strip().rstrip(":")
        if clean_ln in block_titles:
            # ищем следующую непустую строку
            nxt = next((raw_lines[j].lstrip("# ").strip().rstrip(":")
                        for j in range(i + 1, len(raw_lines)) if raw_lines[j].strip()), "")
            # если следующая значимая строка — тоже название блока (или конец), блок пуст → пропускаем заголовок
            if nxt in block_titles or nxt == "":
                continue
        lines.append(ln)

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
        # пропускаем markdown-разделители (---, ***, ___)
        if set(line) <= {"-", "*", "_"} and len(line) >= 2:
            pdf.ln(3)
            continue

        # Заголовки
        if line.startswith("###"):
            pdf.set_font("DejaVu", size=14)
            pdf.multi_cell(pdf.epw, 10, _clean(line.lstrip("# ").strip()),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("DejaVu", size=12)
        elif line.startswith("##"):
            pdf.set_font("DejaVu", size=16)
            pdf.multi_cell(pdf.epw, 12, _clean(line.lstrip("# ").strip()),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("DejaVu", size=12)
        elif line.startswith("#"):
            pdf.set_font("DejaVu", size=20)
            pdf.multi_cell(pdf.epw, 15, _clean(line.lstrip("# ").strip()),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("DejaVu", size=12)
        # ВСТАВИТЬ ЗДЕСЬ — болд-заголовок (название проекта **...**) до буллетов:
        elif line.startswith("**") and line.endswith("**"):
            pdf.set_font("DejaVu", size=13)
            pdf.multi_cell(pdf.epw, 9, _clean(line),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("DejaVu", size=12)

        # Буллеты
        elif line.startswith(("•", "-", "*")):
            text = _clean(line[1:].strip())
            pdf.multi_cell(pdf.epw, 8, f"•  {text}",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Обычный текст
        else:
            pdf.multi_cell(pdf.epw, 8, _clean(line),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())
