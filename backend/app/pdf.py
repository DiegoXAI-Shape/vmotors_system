"""Helpers compartidos para generar los reportes en PDF con reportlab.

No depende de ningun binario del sistema (a diferencia de weasyprint o
wkhtmltopdf), asi que instalar `pip install reportlab` es suficiente en
cualquier maquina.
"""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#D9531E")
INK = colors.HexColor("#101828")
INK_2 = colors.HexColor("#475467")
INK_3 = colors.HexColor("#8A91A0")
BORDER = colors.HexColor("#E4E7EC")
SURFACE_2 = colors.HexColor("#FAFBFC")
SURFACE_3 = colors.HexColor("#F1F3F6")

_base = getSampleStyleSheet()
MARCA = ParagraphStyle("VMMarca", parent=_base["Normal"], fontName="Helvetica-Bold",
                        fontSize=13, textColor=ACCENT, spaceAfter=4, tracking=1)
TITULO = ParagraphStyle("VMTitulo", parent=_base["Heading1"], fontSize=17, textColor=INK, spaceAfter=2)
SUBTITULO = ParagraphStyle("VMSub", parent=_base["Normal"], fontSize=9.5, textColor=INK_2, spaceAfter=14)
SECCION = ParagraphStyle("VMSeccion", parent=_base["Heading2"], fontSize=11.5, textColor=INK,
                          spaceBefore=16, spaceAfter=6)
NORMAL = ParagraphStyle("VMNormal", parent=_base["Normal"], fontSize=9, textColor=INK, leading=13)
DIM = ParagraphStyle("VMDim", parent=_base["Normal"], fontSize=8.5, textColor=INK_3, leading=12)
KPI_LABEL = ParagraphStyle("VMKpiLabel", parent=_base["Normal"], fontSize=7.5, textColor=INK_3,
                            fontName="Helvetica-Bold")
KPI_VALOR = ParagraphStyle("VMKpiValor", parent=_base["Normal"], fontSize=15, textColor=INK,
                            fontName="Helvetica-Bold", spaceBefore=2)


def encabezado(elementos: list, titulo: str, subtitulo: str) -> None:
    elementos.append(Paragraph("VMOTORS", MARCA))
    elementos.append(Paragraph(titulo, TITULO))
    elementos.append(Paragraph(subtitulo, SUBTITULO))
    elementos.append(HRFlowable(width="100%", color=BORDER, thickness=1))
    elementos.append(Spacer(1, 10))


def seccion(elementos: list, texto: str) -> None:
    elementos.append(Paragraph(texto, SECCION))


def fila_kpis(elementos: list, kpis: list[tuple[str, str]]) -> None:
    """kpis: [(etiqueta, valor), ...] -> una fila de tarjetas simples."""
    celdas = [[Paragraph(label.upper(), KPI_LABEL), ] for label, _ in kpis]
    fila_valores = [Paragraph(valor, KPI_VALOR) for _, valor in kpis]
    fila_labels = [Paragraph(label.upper(), KPI_LABEL) for label, _ in kpis]
    t = Table([fila_labels, fila_valores], colWidths=[(letter[0] - 36 * mm) / len(kpis)] * len(kpis))
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 14))


def tabla(elementos: list, encabezados: list[str], filas: list[list], anchos: list | None = None) -> None:
    if not filas:
        elementos.append(Paragraph("Sin registros para este periodo.", DIM))
        elementos.append(Spacer(1, 10))
        return
    data = [[Paragraph(f"<b>{h}</b>", NORMAL) for h in encabezados]]
    for f in filas:
        data.append([Paragraph(str(c) if c is not None else "—", NORMAL) for c in f])
    t = Table(data, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SURFACE_3),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE_2]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 10))


def pie_de_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(INK_3)
    canvas.drawString(18 * mm, 12 * mm, "Documento generado por el sistema VMotors")
    canvas.drawRightString(letter[0] - 18 * mm, 12 * mm, f"Página {doc.page}")
    canvas.restoreState()


def generar_pdf(construir) -> bytes:
    """`construir(elementos: list)` agrega los flowables del reporte."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    elementos: list = []
    construir(elementos)
    doc.build(elementos, onFirstPage=pie_de_pagina, onLaterPages=pie_de_pagina)
    return buffer.getvalue()
