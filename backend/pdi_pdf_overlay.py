# backend/pdi_pdf_overlay.py
"""
Overlay del PDI sobre el PDF OFICIAL de Carrier Transicold (no una
recreación): abrimos la plantilla real (assets/templates/pdi_x4_oficial.pdf,
tal cual la entrega Carrier) y dibujamos encima los valores capturados en
el sistema -- casillas, encabezado de identificación, lecturas del run-test
y el bloque de firma/comentarios -- en las coordenadas exactas de cada
campo/casilla de ese PDF.

Validado 1:1 contra el documento oficial 62-90493-00 Rev B (X4 7300 & 7500):
las 49 casillas del checklist (A-F) se mapean en el mismo orden en que
aparecen los 49 ítems de PDI.TEMPLATES['x4'] (columna izquierda de arriba
a abajo, luego columna derecha, página por página).

La tabla de configuración (páginas 5-7, ~99 filas) todavía NO se overlea
-- se deja tal cual la imprime Carrier (con sus valores de fábrica) porque
mapear con certeza cada una de esas filas requiere validación fila por
fila que no se ha hecho aún. Ver README al final del archivo.
"""
import os
import pymupdf as fitz

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
TEMPLATES_DIR = os.path.join(ASSETS_DIR, "templates")
X4_OFICIAL = os.path.join(TEMPLATES_DIR, "pdi_x4_oficial.pdf")

FONT = "helv"
INK = (0, 0, 0.55)  # tinta azul oscura para distinguir de lo impreso

# ── Encabezado de identificación (página 1, índice 0) ──────────────────────
# clave (columna de pdi_inspecciones) -> texto ancla a buscar en el PDF
HEADER_ANCHORS_X4 = [
    ("cliente", "Customer Name"),
    ("direccion", "Address"),
    ("ciudad_estado_cp", "City, State, Zip"),
    ("fabricante_trailer", "Trailer Manufacturer"),
    ("modelo_trailer", "Trailer Model"),
    ("vin_trailer", "Trailer VIN"),
    ("numero_flota", "Fleet No"),
    ("distribuidor", "Dealer Name"),
    ("modelo_unidad", "Unit Model"),
    ("numero_serie_unidad", "Unit Serial Number"),
    ("numero_serie_motor", "Engine Serial Number"),
    ("numero_serie_compresor", "Compressor Serial Number"),
    ("numero_serie_ees", "EES Serial Number"),
    ("tecnico_instalo", "Installing Technician"),
    ("fecha_instalacion", "Date Installed"),
]

# ── Lecturas (dentro del checklist, páginas 3 y 4 / índices 2 y 3) ─────────
# clave de LECTURAS_X4 -> (página_idx, texto ancla único en esa página)
LECTURA_ANCHORS_X4 = {
    "discharge_pressure": (2, "Discharge Pressure @ gauges"),
    "suction_pressure": (2, "Suction  Pressure @ gauges"),
    "ambient_temp": (2, "Ambient Temp. @ micro"),
    "return_air_temp": (2, "Return Air Temp @ micro"),
    "rt_suction_pressure": (3, "SUCTION PRESSURE"),
    "rt_discharge_pressure": (3, "DISCHARGE PRESSURE"),
    "engine_coolant_temp": (3, "ENGINE COOLANT TEMP"),
    "rt_return_air_temp": (3, "RETURN AIR TEMP"),
    "supply_air_temp": (3, "SUPPLY AIR TEMP"),
    "rt_ambient_air_temp": (3, "AMBIENT AIR TEMP"),
    "defrost_term_temp": (3, "DEFROST TERM TEMP"),
    "comp_disch_temp": (3, "COMP DISCH TEMP"),
    "battery": (3, "BATTERY"),
    "current_draw": (3, "CURRENT DRAW"),
    "engine_rpm": (3, "ENGINE RPM"),
    "software_revision": (3, "SOFTWARE REVISION"),
    "control_serial": (3, "CONTROL SERIAL #"),
    "unit_model": (3, "UNIT MODEL #"),
    "high_speed_rpm": (3, "High Speed"),
    "low_speed_rpm": (3, "Low Speed"),
}

CHECKBOX_SIZE = 9.2
CHECKBOX_PAGES_X4 = [2, 3]  # índices 0-based de las páginas 3 y 4


def _checkbox_positions(page, col_threshold=200):
    """Devuelve los rects de casillas de una página, en orden de lectura
    real del documento: columna izquierda de arriba a abajo, luego columna
    derecha de arriba a abajo (igual que como se leería el PDF impreso)."""
    drawings = page.get_drawings()
    boxes = [
        d["rect"] for d in drawings
        if abs(d["rect"].width - CHECKBOX_SIZE) < 0.4 and abs(d["rect"].height - CHECKBOX_SIZE) < 0.4
    ]
    left = sorted([b for b in boxes if b.x0 < col_threshold], key=lambda r: r.y0)
    right = sorted([b for b in boxes if b.x0 >= col_threshold], key=lambda r: r.y0)
    return left + right


def _all_checkbox_positions_x4(doc):
    ordered = []
    for pidx in CHECKBOX_PAGES_X4:
        for rect in _checkbox_positions(doc[pidx]):
            ordered.append((pidx, rect))
    return ordered


ROW_BOUNDS_HEADER_X4 = [
    (89.9, 126.8), (126.8, 153.4), (153.4, 175.8), (175.8, 202.8),
    (202.8, 225.2), (225.2, 252.1), (252.1, 274.6), (274.6, 297.1),
]
VALUE_COL_LEFT_X4 = 155.0
VALUE_COL_RIGHT_X4 = 438.0


def _header_value_pos(rect, row_index):
    """La columna de valor está A LA DERECHA del label (no debajo), en
    bloques izquierdo/derecho de la tabla de identificación. row_index se
    calcula por posición (0-7) ya que los labels se detectan en orden."""
    row = ROW_BOUNDS_HEADER_X4[row_index]
    x = VALUE_COL_LEFT_X4 if rect.x0 < 300 else VALUE_COL_RIGHT_X4
    y = row[1] - 8
    return x, y


def _draw_value(page, rect, value, dy=10, size=8, max_width=None):
    if not value:
        return
    text = str(value)
    x = rect.x0
    y = rect.y1 + dy
    if max_width:
        # recorte simple si el valor es muy largo para el ancho disponible
        while fitz.get_text_length(text, fontname=FONT, fontsize=size) > max_width and len(text) > 3:
            text = text[:-1]
    page.insert_text((x, y), text, fontsize=size, fontname=FONT, color=INK)


def _draw_wrapped(page, x, y, width, height, text, size=8):
    if not text:
        return
    rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_textbox(rect, str(text), fontsize=size, fontname=FONT, color=INK, align=0)


def generar_pdi_pdf_overlay_x4(pdi: dict, datos: dict) -> bytes:
    doc = fitz.open(X4_OFICIAL)

    # 1) Encabezado de identificación (página 1)
    p0 = doc[0]
    left_row = 0
    right_row = 0
    for clave, anchor in HEADER_ANCHORS_X4:
        hits = p0.search_for(anchor)
        if not hits:
            continue
        rect = hits[0]
        is_left = rect.x0 < 300
        row_index = left_row if is_left else right_row
        if is_left:
            left_row += 1
        else:
            right_row += 1
        valor = pdi.get(clave, "")
        if not valor:
            continue
        x, y = _header_value_pos(rect, row_index)
        text = str(valor)
        while fitz.get_text_length(text, fontname=FONT, fontsize=8.5) > 138 and len(text) > 3:
            text = text[:-1]
        p0.insert_text((x, y), text, fontsize=8.5, fontname=FONT, color=INK)

    # Folio / unidad como referencia rápida en el margen inferior (no pisa nada oficial)
    p0.insert_text((42, 778), f"Folio PDI #{pdi.get('id','')}  |  Unidad: {pdi.get('unit_number','')}  |  Generado por sistema",
                    fontsize=6.5, fontname=FONT, color=INK)

    # 2) Firma / comentarios (página 2)
    p1 = doc[1]
    dealer_hits = [r for r in p1.search_for("Dealer") if abs(r.y0 - 280.3) < 3]
    if dealer_hits:
        r = dealer_hits[0]
        _draw_value(p1, fitz.Rect(111.8, r.y0, 111.8, r.y0), pdi.get("dealer_firma", ""), dy=10, size=8, max_width=170)
    insp_hits = p1.search_for("Inspecting")
    if insp_hits:
        r = insp_hits[0]
        _draw_value(p1, fitz.Rect(111.8, r.y0, 111.8, r.y0), pdi.get("tecnico_inspecciono", ""), dy=24, size=8, max_width=170)
    comments_hits = p1.search_for("Comments:")
    if comments_hits:
        r = comments_hits[0]
        _draw_wrapped(p1, 296, r.y1 + 24, 260, 90, pdi.get("comentarios", ""), size=8)

    # 3) Checklist: casillas marcadas (páginas 3 y 4)
    checkbox_positions = _all_checkbox_positions_x4(doc)
    import pdi_templates as PDI
    tpl = PDI.TEMPLATES["x4"]
    idx = 0
    for sec in tpl["secciones"]:
        for i in range(len(sec["items"])):
            clave = f"chk_{sec['clave']}_{i + 1}"
            if idx >= len(checkbox_positions):
                break
            pidx, rect = checkbox_positions[idx]
            if datos.get(clave) == "1":
                page = doc[pidx]
                cx = (rect.x0 + rect.x1) / 2
                cy = (rect.y0 + rect.y1) / 2
                page.insert_text((cx - 3.2, cy + 3.2), "X", fontsize=9, fontname="helv-bold" if False else FONT,
                                  color=(0, 0, 0))
            idx += 1

    # 4) Lecturas del run-test (páginas 3 y 4, inline)
    for clave, (pidx, anchor) in LECTURA_ANCHORS_X4.items():
        valor = datos.get(f"lec_{clave}", "")
        if not valor:
            continue
        page = doc[pidx]
        hits = page.search_for(anchor)
        if not hits:
            continue
        r = hits[0]
        page.insert_text((r.x1 + 8, r.y1 - 1), str(valor), fontsize=8, fontname=FONT, color=INK)

    return doc.tobytes()


# ── Notas de alcance ────────────────────────────────────────────────────
# Lo overleado y VALIDADO 1:1 contra el PDF oficial:
#   - Encabezado de identificación (15 campos, página 1)
#   - Las 49 casillas del checklist A-F (páginas 3-4), verificado que el
#     orden columna-izq/columna-der/página coincide exactamente con el
#     orden de PDI.TEMPLATES['x4']['secciones'].
#   - Bloque de firma/comentarios (página 2)
#   - Lecturas inline del run-test (páginas 3-4), vía búsqueda de texto
#     ancla único por lectura.
#
# Pendiente (no incluido en esta versión, para no arriesgar overlay
# incorrecto sobre un documento de garantía real):
#   - Tabla de Configuración (páginas 5-7, ~99 filas) -- se imprime tal
#     cual la entrega Carrier, con sus valores de fábrica, sin la columna
#     "Cambiado a" rellenada.
#   - La plantilla Vector (10 páginas) -- tiene tablas de lecturas
#     incrustadas a mitad del checklist que no calzan con el modelo de
#     datos actual; requiere remodelar pdi_templates.py primero.
