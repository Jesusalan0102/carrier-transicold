# backend/pdi_pdf.py
"""
Generación del PDF de PDI (Pre-Delivery Inspection) con el layout del
formato oficial de Carrier Transicold (62-90493-00 para X4, equivalente
para Vector): membrete con logo, tabla de identificación de unidad,
checklist por secciones con casillas, tabla de lecturas del run-test,
tabla de configuración (Ajuste de Fábrica / Cambiado a) y bloque de
firma / comentarios.

Este módulo NO toca la base de datos: recibe el `pdi` (row de
pdi_inspecciones), el `tpl` (de pdi_templates.TEMPLATES) y `datos`
(dict campo_clave -> valor de pdi_datos), y devuelve los bytes del PDF.
"""
import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, FrameBreak, NextPageTemplate, PageBreak, Image, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

TZ = ZoneInfo("America/Tijuana")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "carrier_logo.png")

DOC_NUM = {"x4": "62-90493-00 Rev B", "vector": "62-90494-00 Rev B"}

styles = getSampleStyleSheet()
STY_TITLE = ParagraphStyle("pdi_title", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=11, leading=13, alignment=TA_CENTER)
STY_TITLE_SUB = ParagraphStyle("pdi_title_sub", parent=styles["Normal"], fontName="Helvetica-BoldOblique",
                                fontSize=9, leading=11, alignment=TA_CENTER)
STY_LABEL = ParagraphStyle("pdi_label", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=7.5, leading=9)
STY_VALUE = ParagraphStyle("pdi_value", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=8.5, leading=10)
STY_SECTION = ParagraphStyle("pdi_section", parent=styles["Normal"], fontName="Helvetica-Bold",
                              fontSize=9.5, leading=12, spaceBefore=8, spaceAfter=4,
                              textColor=colors.HexColor("#8B0000"))
STY_ITEM = ParagraphStyle("pdi_item", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=8, leading=10.5)
STY_SMALL = ParagraphStyle("pdi_small", parent=styles["Normal"], fontName="Helvetica-Oblique",
                            fontSize=7, leading=8.5)


def _fmt_date(v):
    if not v:
        return ""
    try:
        return v.strftime("%d/%m/%Y")
    except AttributeError:
        return str(v)


def _header_footer(canvas, doc, tpl, pdi):
    canvas.saveState()
    width, height = letter
    top = height - 0.4 * inch
    box_h = 0.95 * inch

    # Recuadro del membrete (repetido en cada página)
    canvas.setLineWidth(0.75)
    canvas.rect(0.5 * inch, top - box_h, width - 1.0 * inch, box_h)
    canvas.line(0.5 * inch + 1.55 * inch, top - box_h, 0.5 * inch + 1.55 * inch, top)

    if os.path.exists(LOGO_PATH):
        try:
            canvas.drawImage(LOGO_PATH, 0.62 * inch, top - box_h + 0.16 * inch,
                              width=1.25 * inch, height=0.62 * inch,
                              preserveAspectRatio=True, mask="auto", anchor="c")
        except Exception:
            pass

    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(width / 2 + 0.75 * inch, top - 0.22 * inch,
                              "Unit Installation & Pre-Delivery Inspection")
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawCentredString(width / 2 + 0.75 * inch, top - 0.35 * inch, tpl["nombre"])
    canvas.setFont("Helvetica-BoldOblique", 8)
    canvas.drawCentredString(width / 2 + 0.75 * inch, top - 0.48 * inch,
                              "Instalación de Unidad e Inspección Pre-entrega")
    canvas.setFont("Helvetica-Oblique", 7.5)
    canvas.drawCentredString(width / 2 + 0.75 * inch, top - 0.60 * inch,
                              "Unidades de Refrigeración Trailer")
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(width / 2 + 0.75 * inch, top - 0.75 * inch,
                              f"Unidad: {pdi.get('unit_number', '')}   |   Folio PDI #{pdi.get('id', '')}")

    # Pie de página
    footer_y = 0.42 * inch
    canvas.setLineWidth(0.5)
    canvas.line(0.5 * inch, footer_y + 0.12 * inch, width - 0.5 * inch, footer_y + 0.12 * inch)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(0.5 * inch, footer_y, DOC_NUM.get(pdi.get("tipo"), ""))
    canvas.drawCentredString(width / 2, footer_y,
                              datetime.now(TZ).strftime("Generado %d/%m/%Y %H:%M"))
    canvas.drawRightString(width - 0.5 * inch, footer_y, f"Página {doc.page}")
    canvas.restoreState()


def _header_table(tpl, pdi):
    """Tabla de identificación de cliente/unidad, 2 columnas (como el formato oficial)."""
    fields = tpl["header_fields"]
    rows = []
    for i in range(0, len(fields), 2):
        left = fields[i]
        right = fields[i + 1] if i + 1 < len(fields) else None
        left_cell = [
            Paragraph(left["label"], STY_LABEL),
            Paragraph(str(pdi.get(left["clave"], "") or "&nbsp;"), STY_VALUE),
        ]
        if right:
            right_cell = [
                Paragraph(right["label"], STY_LABEL),
                Paragraph(str(pdi.get(right["clave"], "") or "&nbsp;"), STY_VALUE),
            ]
        else:
            right_cell = ""
        rows.append([left_cell, right_cell])

    t = Table(rows, colWidths=[3.65 * inch, 3.65 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


STY_CHECK = ParagraphStyle("pdi_check", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=8, leading=10, alignment=TA_CENTER)


def _checklist_flowables(tpl, datos):
    flow = []
    for sec in tpl["secciones"]:
        flow.append(Paragraph(sec["titulo"], STY_SECTION))
        rows = []
        checked_flags = []
        for i, texto in enumerate(sec["items"]):
            clave = f"chk_{sec['clave']}_{i + 1}"
            checked = datos.get(clave) == "1"
            checked_flags.append(checked)
            mark = Paragraph("X" if checked else "&nbsp;", STY_CHECK)
            rows.append([mark, Paragraph(texto, STY_ITEM)])
        t = Table(rows, colWidths=[0.22 * inch, 7.08 * inch])
        style_cmds = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ]
        for i in range(len(rows)):
            style_cmds.append(("BOX", (0, i), (0, i), 0.75, colors.black))
        t.setStyle(TableStyle(style_cmds))
        flow.append(t)
        flow.append(Spacer(1, 4))
    return flow


def _lecturas_table(tpl, datos):
    lecturas = tpl["lecturas"]
    grupos = {}
    for l in lecturas:
        grupos.setdefault(l["grupo"], []).append(l)

    flow = [Paragraph("Lecturas del Run-Test / Readings", STY_SECTION)]
    for grupo, items in grupos.items():
        rows = [[
            Paragraph("<b>Lectura</b>", STY_LABEL),
            Paragraph("<b>Valor</b>", STY_LABEL),
            Paragraph("<b>Unidad</b>", STY_LABEL),
        ]]
        for l in items:
            valor = datos.get(f"lec_{l['clave']}", "")
            rows.append([
                Paragraph(l["label"], STY_ITEM),
                Paragraph(str(valor) if valor else "&nbsp;", STY_VALUE),
                Paragraph(l["unidad"], STY_ITEM),
            ])
        t = Table(rows, colWidths=[3.6 * inch, 2.4 * inch, 1.3 * inch])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        flow.append(Paragraph(grupo, STY_SMALL))
        flow.append(t)
        flow.append(Spacer(1, 6))
    return flow


def _config_table(tpl, datos):
    config = tpl["config_table"]
    flow = [Paragraph("Tabla de Configuración / Configuration Table", STY_SECTION)]
    rows = [[
        Paragraph("<b>Sección / Campo</b>", STY_LABEL),
        Paragraph("<b>Ajuste de Fábrica</b>", STY_LABEL),
        Paragraph("<b>Cambiado a</b>", STY_LABEL),
    ]]
    last_seccion = None
    for i, (seccion, campo, ajuste_fabrica) in enumerate(config):
        cambio = datos.get(f"cfg_{i}", "")
        if seccion != last_seccion:
            rows.append([Paragraph(f"<b>{seccion}</b>", STY_LABEL), "", ""])
            last_seccion = seccion
        rows.append([
            Paragraph(campo, STY_ITEM),
            Paragraph(ajuste_fabrica or "&nbsp;", STY_ITEM),
            Paragraph(str(cambio) if cambio else "&nbsp;", STY_VALUE),
        ])
    t = Table(rows, colWidths=[3.9 * inch, 1.9 * inch, 1.5 * inch], repeatRows=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    for idx, row in enumerate(rows):
        if idx > 0 and row[1] == "" and row[2] == "":
            style.append(("SPAN", (0, idx), (-1, idx)))
            style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f5f5f5")))
    t.setStyle(TableStyle(style))
    flow.append(t)
    return flow


def _firma_table(pdi):
    rows = [
        [Paragraph("Dealer / Distribuidor", STY_LABEL), Paragraph(pdi.get("dealer_firma") or "&nbsp;", STY_VALUE)],
        [Paragraph("Técnico que Inspeccionó", STY_LABEL), Paragraph(pdi.get("tecnico_inspecciono") or "&nbsp;", STY_VALUE)],
        [Paragraph("Comentarios / Comments", STY_LABEL), Paragraph(pdi.get("comentarios") or "&nbsp;", STY_VALUE)],
        [Paragraph("Estado del PDI", STY_LABEL), Paragraph((pdi.get("estado") or "borrador").upper(), STY_VALUE)],
    ]
    t = Table(rows, colWidths=[2.0 * inch, 5.3 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def generar_pdi_pdf(pdi: dict, tpl: dict, datos: dict) -> bytes:
    """Genera el PDF completo del PDI (identificación + checklist + lecturas +
    tabla de configuración + firma), replicando el layout oficial de Carrier
    Transicold. Devuelve los bytes del archivo."""
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=letter,
        topMargin=1.35 * inch, bottomMargin=0.65 * inch,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        title=f"PDI {pdi.get('unit_number', '')} - {tpl.get('nombre', '')}",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")

    def on_page(canvas, d):
        _header_footer(canvas, d, tpl, pdi)

    doc.addPageTemplates([PageTemplate(id="pdi", frames=[frame], onPage=on_page)])

    story = []
    story.append(Spacer(1, 4))
    story.append(_header_table(tpl, pdi))
    story.append(Spacer(1, 8))
    story.extend(_checklist_flowables(tpl, datos))
    story.append(PageBreak())
    story.extend(_lecturas_table(tpl, datos))
    story.append(Spacer(1, 8))
    story.extend(_config_table(tpl, datos))
    story.append(PageBreak())
    story.append(Paragraph("Cierre de Inspección / Inspection Closeout", STY_SECTION))
    story.append(Spacer(1, 4))
    story.append(_firma_table(pdi))

    doc.build(story)
    return buf.getvalue()
