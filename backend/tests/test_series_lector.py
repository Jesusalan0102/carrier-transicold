"""
Tests de la lógica que interpreta las etiquetas (series_lector.interpretar).

Trabajan con textos/códigos de ejemplo (sin imágenes ni OCR instalado), así que corren en cualquier
entorno de CI. La lectura real de fotos se probó aparte con fotos de etiquetas de campo.
"""
import series_lector as sl


def L(texto, x0, y, w=120, h=20):
    """Línea de OCR de juguete: caja axial en (x0, y)."""
    return {"texto": texto, "conf": 0.95, "x0": x0, "x1": x0 + w, "y0": y, "y1": y + h, "cy": y + h / 2, "h": float(h)}


def cod(texto, formato="DataMatrix"):
    return {"formato": formato, "texto": texto}


def test_placa_x4_serie_del_codigo_y_modelo_del_texto():
    lineas = [L("Model Name:", 10, 100), L("X47700", 200, 100),
              L("Serial No.:", 10, 140), L("XAG91848255", 200, 140),
              L("Model No.:", 10, 180), L("NDUG7CNO-AH-A", 200, 180)]
    r = sl.interpretar([cod("XAG91848255")], lineas)
    assert r["tipo"] == "placa_unidad"
    assert r["campos"] == {"reefer_serial": "XAG91848255", "reefer_model": "X4 7700"}
    serie = next(d for d in r["detalles"] if d["campo"] == "reefer_serial")
    assert serie["confianza"] == "alta"
    modelo = next(d for d in r["detalles"] if d["campo"] == "reefer_model")
    assert modelo["confianza"] == "revisar"            # el texto por OCR siempre se confirma


def test_placa_solo_con_datamatrix_avisa_que_falta_el_modelo():
    r = sl.interpretar([cod("XAG91848255")], [])
    assert r["campos"] == {"reefer_serial": "XAG91848255"}
    assert any("modelo" in a.lower() for a in r["avisos"])


def test_placa_si_codigo_y_texto_no_coinciden_gana_el_codigo_y_se_avisa():
    lineas = [L("Serial No.:", 10, 140), L("XAG91848256", 200, 140), L("Model Name:", 10, 100), L("X47700", 200, 100)]
    r = sl.interpretar([cod("XAG91848255")], lineas)
    assert r["campos"]["reefer_serial"] == "XAG91848255"
    assert any("confirma" in a.lower() for a in r["avisos"])


def test_controlador_code128_unit_sn_y_pn():
    r = sl.interpretar([cod("12-00843-03", "Code128"), cod("GJTC626120315", "Code128")], [])
    assert r["tipo"] == "controlador"
    assert r["campos"] == {"controller_serial": "GJTC626120315"}
    pn = next(d for d in r["detalles"] if d["etiqueta"].startswith("Número de parte"))
    assert pn["valor"] == "12-00843-03" and pn["confianza"] == "alta"


def test_modulo_ctd_datamatrix_con_numeral():
    r = sl.interpretar([cod("220322500#045681")], [])
    assert r["tipo"] == "modulo_ctd"
    assert r["campos"] == {"ctd_module_serial": "220322500#045681"}
    pn = next(d for d in r["detalles"] if d["etiqueta"].startswith("Número de parte"))
    assert pn["valor"] == "22-03225-00"                 # derivado de los 9 dígitos del serial


def test_display_por_texto_queda_para_revisar_y_avisa_si_el_pn_es_imposible():
    lineas = [L("A1Q-00663-16#2026P0213759", 10, 100, w=300)]
    r = sl.interpretar([], lineas)
    assert r["tipo"] == "display"
    assert r["campos"] == {"display_serial": "A1Q-00663-16#2026P0213759"}
    assert next(d for d in r["detalles"] if d["campo"] == "display_serial")["confianza"] == "revisar"
    assert any("imposible" in a.lower() for a in r["avisos"])


def test_display_con_pn_valido_no_genera_aviso_de_pn():
    r = sl.interpretar([], [L("A12-00663-16#2026P0213759", 10, 100, w=300)])
    assert r["tipo"] == "display"
    assert not any("imposible" in a.lower() for a in r["avisos"])


def test_etiqueta_desconocida_con_codigos_pide_asignar_a_mano():
    r = sl.interpretar([cod("ABC-123")], [])
    assert r["tipo"] == "desconocido" and r["campos"] == {}
    assert r["avisos"]


def test_sin_nada_no_truena():
    r = sl.interpretar([], [])
    assert r["tipo"] == "desconocido" and r["campos"] == {}
