"""
series_lector.py
----------------
Lee números de serie a partir de una FOTO de una etiqueta Carrier.

Capas, de la más segura a la más flexible:
  1. Códigos (zxing-cpp): DataMatrix, Code128, QR... Lectura exacta, sin errores de OCR.
     Es la capa principal y la única obligatoria.
  2. OCR de texto (RapidOCR, opcional): lee lo impreso ("Model Name", "Serial No.", "SN:", ...)
     y rescata etiquetas cuyo código de barras salió borroso. Si la foto viene inclinada, se
     endereza sola y se vuelve a intentar.

Cada dato devuelto trae su origen y un nivel de confianza:
  'alta'    -> salió de un código de barras / DataMatrix (o coincide con el texto impreso)
  'revisar' -> salió solo del texto por OCR: el técnico debe confirmarlo contra la etiqueta

Para reconocer un tipo de etiqueta nuevo basta agregar su número de parte en NUCLEO_A_TIPO.
"""
import io
import logging
import math
import re
import threading
import time
from typing import List, Optional

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

try:                                    # capa 1 (obligatoria para leer códigos)
    import zxingcpp
except Exception as _e:                 # pragma: no cover
    zxingcpp = None
    logger.warning(f"[series_lector] zxing-cpp no disponible: {_e}")

# ── Configuración ────────────────────────────────────────────────────────────
MAX_LADO_PX = 2200            # las fotos de celular se reducen a este lado largo
PRESUPUESTO_OCR_SEG = 14.0    # tiempo máximo total dedicado al OCR por foto
# Lado largo con que se pasa la foto al OCR. La 1ª pasada es liviana (poca memoria); la resolución
# alta se usa solo para rescatar fotos difíciles (borrosas o inclinadas), que es cuando hace falta.
LADO_OCR_RAPIDO = 1400
LADO_OCR_RESCATE = 1800

# Tipos de etiqueta -> campo de la tabla unidades donde se guarda la serie.
TIPOS = {
    "placa_unidad": {"titulo": "Placa de la unidad (reefer)"},
    "controlador":  {"titulo": "Controlador (CTD)",  "campo": "controller_serial",
                     "nombre": "Serie del controlador"},
    "display":      {"titulo": "Display Module",     "campo": "display_serial",
                     "nombre": "Serie del display"},
    "modulo_ctd":   {"titulo": "Módulo CTD",         "campo": "ctd_module_serial",
                     "nombre": "Serie del módulo CTD"},
}
# Bloque central de 5 dígitos del número de parte Carrier (NN-NNNNN-NN) -> tipo de etiqueta.
NUCLEO_A_TIPO = {
    "00843": "controlador",     # CTD P/N 12-00843-03
    "00663": "display",         # DISPLAY MODULE A12-00663-16
    "03225": "modulo_ctd",      # CTD P/N 22-03225-00
}

# ── Patrones ─────────────────────────────────────────────────────────────────
RE_PN = re.compile(r"([A-Z]?[0-9A-Z]{2})-(\d{5})-(\d{2})")
RE_SERIE_REEFER = re.compile(r"^[A-Z]{3}\d{7,9}$")                      # XAG91848255
RE_SERIE_UNIT_SN = re.compile(r"^(?=.*[A-Z]{2})(?=.*\d{4})[A-Z0-9]{9,16}$")   # GJTC626120315
RE_SN_CTD = re.compile(r"^(\d{9})#(\d{4,8})$")                         # 220322500#045681
RE_SN_DISPLAY = re.compile(r"([A-Z]?[0-9A-Z]{2}-\d{5}-\d{2})#([0-9A-Z]{6,14})")  # A12-00663-16#2026P0213759
RE_MODELO_X4 = re.compile(r"^([A-Z]\d)\s?(\d{4})$")                     # X47700 -> X4 7700


def _compactar(s: str) -> str:
    return re.sub(r"\s+", "", str(s or "").upper())


def _letras(s: str) -> str:
    return re.sub(r"[^A-Z]", "", str(s or "").upper())


# ── Imagen ───────────────────────────────────────────────────────────────────
def preparar_imagen(datos: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(datos))
    img = ImageOps.exif_transpose(img)          # respeta la orientación con que se tomó la foto
    img = img.convert("RGB")
    mayor = max(img.size)
    if mayor > MAX_LADO_PX:
        k = MAX_LADO_PX / mayor
        img = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    return img


# ── Capa 1: códigos ──────────────────────────────────────────────────────────
def leer_codigos(img: Image.Image) -> List[dict]:
    if zxingcpp is None:
        return []
    vistos, salida = set(), []

    def _pasada(im):
        try:
            for r in zxingcpp.read_barcodes(im, try_rotate=True, try_downscale=True, try_invert=True):
                if not r.valid or not r.text:
                    continue
                k = (r.format.name, r.text)
                if k not in vistos:
                    vistos.add(k)
                    salida.append({"formato": r.format.name, "texto": r.text.strip()})
        except Exception as e:                  # pragma: no cover
            logger.debug(f"[series_lector] zxing falló: {e}")

    _pasada(img)
    if not salida:                              # 2ª pasada: gris con contraste automático
        _pasada(ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1))
    return salida


# ── Capa 2: OCR ──────────────────────────────────────────────────────────────
_ocr = None
_ocr_error: Optional[str] = None
_ocr_init_lock = threading.Lock()
_ocr_run_lock = threading.Semaphore(1)          # un OCR a la vez: cuida memoria y CPU del servidor


def _motor_ocr():
    global _ocr, _ocr_error
    if _ocr is not None or _ocr_error:
        return _ocr
    with _ocr_init_lock:
        if _ocr is None and not _ocr_error:
            try:
                from rapidocr_onnxruntime import RapidOCR
                _ocr = RapidOCR()
            except Exception as e:
                _ocr_error = str(e)
                logger.warning(f"[series_lector] OCR no disponible (solo se leerán códigos): {e}")
    return _ocr


def estado_motores() -> dict:
    return {"codigos": zxingcpp is not None, "ocr": _motor_ocr() is not None}


def _a_arreglo(img: Image.Image):
    import numpy as np
    return np.asarray(img)[:, :, ::-1].copy()   # RGB -> BGR


def _ocr_lineas(ocr, img: Image.Image) -> List[dict]:
    res, _ = ocr(_a_arreglo(img))
    lineas = []
    for caja, texto, conf in (res or []):
        xs = [p[0] for p in caja]
        ys = [p[1] for p in caja]
        lineas.append({
            "texto": str(texto).strip(), "conf": float(conf),
            "x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
            "cy": (min(ys) + max(ys)) / 2, "h": max(1.0, max(ys) - min(ys)),
        })
    return lineas


def _angulos_candidatos(ocr, img: Image.Image) -> List[float]:
    """Estima la inclinación del texto con el detector (rápido, sin reconocer) y propone giros."""
    try:
        res, _ = ocr(_a_arreglo(img), use_det=True, use_cls=False, use_rec=False)
    except Exception:
        return []
    medidas = []
    for caja in (res or []):
        p = [list(map(float, q)) for q in caja]
        d01 = (p[1][0] - p[0][0], p[1][1] - p[0][1])
        d12 = (p[2][0] - p[1][0], p[2][1] - p[1][1])
        d = d01 if math.hypot(*d01) >= math.hypot(*d12) else d12
        ang = math.degrees(math.atan2(d[1], d[0]))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        medidas.append((math.hypot(*d), ang))
    if not medidas:
        return []
    medidas.sort(reverse=True)
    base = round(medidas[0][1] / 5) * 5
    cands = []
    for a in (base, base - 10, base - 20, base + 10, base - 30):
        if -75 <= a <= 75 and abs(a) >= 5 and a not in cands:
            cands.append(float(a))
    return cands


def _girar(img: Image.Image, grados: float) -> Image.Image:
    return img.rotate(grados, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))


def _ampliar(img: Image.Image, lado_objetivo: int) -> Image.Image:
    """Deja la imagen con el lado largo en `lado_objetivo` (amplía hasta 2x o reduce)."""
    mayor = max(img.size)
    k = min(2.0, lado_objetivo / mayor)
    if abs(k - 1.0) < 0.02:
        return img
    return img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.BICUBIC)


# ── Interpretación ───────────────────────────────────────────────────────────
def _valor_de(lineas: List[dict], clave_letras: str) -> Optional[str]:
    """Valor impreso junto a una etiqueta (misma línea, a la derecha o la siguiente en el orden)."""
    for i, l in enumerate(lineas):
        pura = _letras(l["texto"])
        if not pura.startswith(clave_letras):
            continue
        if ":" in l["texto"]:                           # 'SN:220322500#045681'
            resto = l["texto"].split(":", 1)[1].strip()
            if resto:
                return resto
        derecha = [m for j, m in enumerate(lineas)
                   if j != i and m["x0"] >= l["x1"] - 6 and abs(m["cy"] - l["cy"]) <= 0.7 * max(l["h"], m["h"])]
        if derecha:
            return min(derecha, key=lambda m: m["x0"])["texto"]
        if i + 1 < len(lineas):
            return lineas[i + 1]["texto"]
    return None


def _normalizar_serie_reefer(txt: str) -> str:
    s = _compactar(txt)
    if len(s) > 3:                                      # la cola numérica no lleva letras O/I
        s = s[:3] + s[3:].replace("O", "0").replace("I", "1")
    return s


def _normalizar_modelo(txt: str) -> str:
    s = re.sub(r"\s+", " ", str(txt).strip().upper())
    m = RE_MODELO_X4.match(s.replace(" ", ""))
    return f"{m.group(1)} {m.group(2)}" if m else s


def _pn_de(texto: str):
    m = RE_PN.search(_compactar(texto))
    return (f"{m.group(1)}-{m.group(2)}-{m.group(3)}", m.group(2)) if m else (None, None)


def _det(etiqueta, valor, campo, origen, confianza, extra=None):
    d = {"etiqueta": etiqueta, "valor": valor, "campo": campo, "origen": origen, "confianza": confianza}
    if extra:
        d["nota"] = extra
    return d


def interpretar(codigos: List[dict], lineas: List[dict]) -> dict:
    textos_cod = [c["texto"] for c in codigos]
    cod_compactos = [_compactar(t) for t in textos_cod]
    texto_ocr = " ".join(l["texto"] for l in lineas)
    ocr_letras = _letras(texto_ocr)
    avisos, detalles, campos = [], [], {}

    # ===== Placa de la unidad (reefer): 'Model Name / Serial No. / Model No.' =====
    serie_cod = next((c for c in cod_compactos if RE_SERIE_REEFER.match(c)), None)
    v_serie = _valor_de(lineas, "SERIALNO")
    serie_txt = _normalizar_serie_reefer(v_serie) if v_serie else None
    if serie_txt and not RE_SERIE_REEFER.match(serie_txt):
        serie_txt = None
    es_placa = ("MODELNAME" in ocr_letras or "SERIALNO" in ocr_letras) and (serie_cod or serie_txt)
    if es_placa or (serie_cod and not lineas and not any(RE_PN.search(c) for c in cod_compactos)):
        serie = serie_cod or serie_txt
        if serie_cod and serie_txt and serie_cod != serie_txt:
            avisos.append(f"El código dice {serie_cod} pero el texto impreso se leyó como {serie_txt}. "
                          "Se usó el código; confirma contra la placa.")
        campos["reefer_serial"] = serie
        nota = ("coincide con el texto impreso" if serie_cod and serie_cod == serie_txt else None)
        detalles.append(_det("Número de serie", serie, "reefer_serial",
                             "codigo" if serie_cod else "texto", "alta" if serie_cod else "revisar", nota))
        v_modelo = _valor_de(lineas, "MODELNAME")
        if v_modelo:
            modelo = _normalizar_modelo(v_modelo)
            campos["reefer_model"] = modelo
            detalles.append(_det("Modelo", modelo, "reefer_model", "texto", "revisar"))
        else:
            avisos.append("No se alcanzó a leer el modelo impreso: captúralo manualmente.")
        v_mno = _valor_de(lineas, "MODELNO")
        if v_mno:
            detalles.append(_det("Model No.", _compactar(v_mno), None, "texto", "revisar",
                                 "Solo informativo; verifica 0/O en la etiqueta."))
        return {"tipo": "placa_unidad", "titulo": TIPOS["placa_unidad"]["titulo"],
                "campos": campos, "detalles": detalles, "avisos": avisos}

    # ===== Etiquetas CTD / Display: número de parte + serie =====
    pn = nucleo = None
    for t in cod_compactos + [_compactar(l["texto"]) for l in lineas]:
        pn, nucleo = _pn_de(t)
        if pn:
            break

    serie, origen, confianza, nota = None, None, None, None
    # a) DataMatrix del módulo CTD: '220322500#045681'
    for c in cod_compactos:
        m = RE_SN_CTD.match(c)
        if m:
            serie, origen, confianza = c, "codigo", "alta"
            pn_dig = m.group(1)
            pn_derivado = f"{pn_dig[:2]}-{pn_dig[2:7]}-{pn_dig[7:]}"
            if not pn:
                pn, nucleo = pn_derivado, pn_dig[2:7]
            break
    # b) Code128 'UNIT S/N' del controlador: 'GJTC626120315' (distinto del número de parte)
    if not serie:
        for c in cod_compactos:
            if not RE_PN.fullmatch(c) and RE_SERIE_UNIT_SN.match(c):
                serie, origen, confianza = c, "codigo", "alta"
                break
    # c) Texto por OCR: 'SN:xxxx#yyyy', 'UNIT S/N:xxxx' o 'Pnn-nnnnn-nn#serie' (display)
    if not serie:
        for l in lineas:
            t = _compactar(l["texto"])
            m = RE_SN_DISPLAY.search(t)
            if m:
                serie, origen, confianza = m.group(0), "texto", "revisar"
                if not pn:
                    pn, nucleo = _pn_de(m.group(1))
                nota = "El número de parte (antes del #) puede traer errores de lectura; la serie después del # es la importante."
                break
        if not serie:
            v = _valor_de(lineas, "UNITSN") or _valor_de(lineas, "SN")
            if v:
                v = _compactar(v)
                if RE_SN_CTD.match(v) or RE_SERIE_UNIT_SN.match(v):
                    serie, origen, confianza = v, "texto", "revisar"

    tipo = NUCLEO_A_TIPO.get(nucleo) if nucleo else None
    if not tipo and "DISPLAYMODULE" in ocr_letras and serie:
        tipo = "display"

    if not serie:
        if codigos:
            avisos.append("Se leyeron códigos pero no reconocí el formato de la etiqueta; "
                          "asigna el valor al campo que corresponda.")
        return {"tipo": "desconocido", "titulo": "Etiqueta no reconocida", "campos": {},
                "detalles": [], "avisos": avisos}

    etiqueta_serie = TIPOS[tipo]["nombre"] if tipo else "Número de serie"
    campo = TIPOS[tipo]["campo"] if tipo else None
    if campo:
        campos[campo] = serie
    detalles.append(_det(etiqueta_serie, serie, campo, origen, confianza, nota))
    if pn:
        confianza_pn = "alta" if any(pn.replace("-", "") in c.replace("-", "") for c in cod_compactos) else "revisar"
        detalles.append(_det("Número de parte (P/N)", pn, None, "codigo" if confianza_pn == "alta" else "texto",
                             confianza_pn))
    v_sup = _valor_de(lineas, "SUPPLIERCODE")
    if v_sup:
        detalles.append(_det("Código de proveedor", _compactar(v_sup), None, "texto", "revisar"))
    v_fecha = _valor_de(lineas, "MANUFACTURINGDATE")
    if v_fecha:
        detalles.append(_det("Fecha de fabricación", _compactar(v_fecha), None, "texto", "revisar"))
    # Un número de parte Carrier lleva SOLO dígitos antes del primer guion (con una letra opcional al inicio).
    if pn and not re.fullmatch(r"[A-Z]?\d{2}", pn.split("-")[0]):
        avisos.append(f"El número de parte se leyó como {pn}, pero tiene un carácter imposible: la lectura de "
                      "texto pudo confundirse. Compara contra la etiqueta y corrígelo si hace falta.")
    if not tipo:
        avisos.append("Número de parte desconocido: elige a qué campo corresponde esta serie.")
    return {"tipo": tipo or "desconocido",
            "titulo": TIPOS[tipo]["titulo"] if tipo else "Etiqueta CTD (tipo por confirmar)",
            "campos": campos, "detalles": detalles, "avisos": avisos}


# ── API principal ────────────────────────────────────────────────────────────
def leer_etiqueta(datos: bytes) -> dict:
    t0 = time.monotonic()
    img = preparar_imagen(datos)
    metodos = []

    codigos = leer_codigos(img)
    if codigos:
        metodos.append("codigo")
    resultado = interpretar(codigos, [])

    # ¿Alcanza con los códigos? Placa: serie leída; el modelo viene del texto, así que se sigue al OCR.
    completo = resultado["tipo"] in ("controlador", "modulo_ctd") and resultado["campos"]
    ocr = None if completo else _motor_ocr()
    lineas: List[dict] = []
    if ocr is not None:
        with _ocr_run_lock:
            fin = t0 + PRESUPUESTO_OCR_SEG
            lineas = _ocr_lineas(ocr, _ampliar(img, LADO_OCR_RAPIDO))
            metodos.append("ocr")
            resultado = interpretar(codigos, lineas)
            # Foto inclinada y sin resultado: enderezar y reintentar (el mismo detector sugiere el ángulo)
            if not resultado["campos"] and time.monotonic() < fin:
                base = _ampliar(img, LADO_OCR_RESCATE)
                for ang in _angulos_candidatos(ocr, base):
                    if time.monotonic() >= fin:
                        break
                    lineas_g = _ocr_lineas(ocr, _girar(base, ang))
                    r = interpretar(codigos, lineas_g)
                    if r["campos"]:
                        resultado, lineas = r, lineas_g
                        metodos.append(f"ocr-giro{int(ang)}")
                        break

    resultado.update({
        "ok": bool(resultado["campos"]),
        "metodos": metodos,
        "motores": estado_motores(),
        "codigos": codigos,
        "texto_leido": [l["texto"] for l in lineas][:40],
        "ms": int((time.monotonic() - t0) * 1000),
    })
    if not resultado["ok"] and ocr is None and not codigos:
        resultado["avisos"].append("No se encontró ningún código en la foto y el lector de texto no está instalado "
                                   "en el servidor. Acércate al código de barras/DataMatrix o captura a mano.")
    elif not resultado["ok"] and not resultado["avisos"]:
        resultado["avisos"].append("No se pudo leer la etiqueta. Intenta de nuevo más cerca, sin reflejos y con la "
                                   "etiqueta derecha en la foto.")
    return resultado
