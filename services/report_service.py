# services/report_service.py
"""
Генерация PDF-отчётов по инцидентам с поддержкой кириллицы.
Использует локальные шрифты DejaVu из папки fonts.
"""

import os
from datetime import date
from fpdf import FPDF
from typing import List


# --- Пути к шрифтам ---
current_dir = os.path.dirname(__file__)
ttf_dir = os.path.join(current_dir, "..", "fonts", "dejavu-fonts-ttf-2.37", "ttf")

FONT_PATH_REGULAR = os.path.join(ttf_dir, "DejaVuSans.ttf")
FONT_PATH_BOLD = os.path.join(ttf_dir, "DejaVuSans-Bold.ttf")
FONT_PATH_ITALIC = os.path.join(ttf_dir, "DejaVuSans-Oblique.ttf")  # опционально

# Проверка существования
for path in [FONT_PATH_REGULAR, FONT_PATH_BOLD]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Шрифт не найден: {path}")


class IncidentPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Регистрируем шрифты
        self.add_font("DejaVu", "", FONT_PATH_REGULAR, uni=True)      # Обычный
        self.add_font("DejaVu", "B", FONT_PATH_BOLD, uni=True)         # Жирный
        self.add_font("DejaVu", "I", FONT_PATH_ITALIC, uni=True)       # Курсив (опционально)
        self.set_font("DejaVu", size=10)

    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.cell(0, 10, "Отчёт по инцидентам", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Страница {self.page_no()}", 0, 0, "C")


def generate_incident_report_pdf(incidents: List[dict], report_date: date) -> bytes:
    pdf = IncidentPDF()
    pdf.add_page()

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, f"Дата: {report_date.strftime('%d.%m.%Y')}", 0, 1)
    pdf.ln(5)

    if not incidents:
        pdf.set_font("DejaVu", size=12)
        pdf.cell(0, 10, "Инцидентов не зафиксировано.", 0, 1, "C")
    else:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(30, 8, "Время", 1)
        pdf.cell(50, 8, "Сотрудник", 1)
        pdf.cell(80, 8, "Описание", 1)
        pdf.ln()

        pdf.set_font("DejaVu", size=10)
        for inc in incidents:
            created_at = inc["created_at"]
            time_str = created_at.strftime("%H:%M")
            name = inc["full_name"]
            desc = inc["description"]
            if len(desc) > 40:
                desc = desc[:37] + "..."

            pdf.cell(30, 8, time_str, 1)
            pdf.cell(50, 8, name, 1)
            pdf.cell(80, 8, desc, 1)
            pdf.ln()

    return pdf.output()