# backend/routers/pdi_router.py
"""
API de PDI (Pre-Delivery Inspection) — Carrier Transicold.

Flujo:
  1. El admin asigna el tipo de reefer (x4 / vector) a un LOTE completo
     (POST /api/pdi/lotes-config). También se puede omitir: si la unidad
     ya tiene `reefer_model` capturado (p.ej. "X4 7500"), el tipo se
     detecta solo.
  2. Al abrir el PDI de una unidad (GET /api/pdi/unidad/{unit_number}):
       - Si no existe todavía, se crea automáticamente.
       - El encabezado se pre-llena desde la tabla `unidades`.
       - TODO el checklist de las secciones previas a "Unit Registration"
         se marca automáticamente como completado (auto-check).
       - Las lecturas numéricas se pre-llenan buscando coincidencias en
         `toma_valores_datos` (a través de las asignaciones de la unidad).
       - Se devuelve `campos_faltantes`: lecturas del PDI que no
         encontraron ningún campo equivalente en Toma de Valores, para
         poder agregarlos con un clic.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo

from auth import verify_token
from db import execute_read, execute_write, execute_write_with_id
import pdi_templates as PDI
from pdi_pdf import generar_pdi_pdf

router = APIRouter(prefix="/api/pdi", tags=["pdi"])
TZ = ZoneInfo("America/Tijuana")


# ──────────────────────────────────────────────────────────────────────────
# Modelos
# ──────────────────────────────────────────────────────────────────────────
class LoteTipoSet(BaseModel):
    id_lote: str
    tipo_reefer: str  # 'x4' | 'vector'


class DatosGuardar(BaseModel):
    valores: Dict[str, str]


class HeaderUpdate(BaseModel):
    valores: Dict[str, str]
    estado: Optional[str] = None


class CamposFaltantesAdd(BaseModel):
    campos: List[str]


# ──────────────────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────────────────
def _tabla_existe(nombre_tabla: str) -> bool:
    r = execute_read(
        "SELECT COUNT(*) AS c FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
        (nombre_tabla,),
    )
    return bool(r and r[0]["c"])


def _get_unidad(unit_number: str):
    rows = execute_read("SELECT * FROM unidades WHERE unit_number=%s", (unit_number,))
    return rows[0] if rows else None


def _resolver_tipo(unidad: dict) -> str:
    """Determina x4/vector: primero por reefer_model de la unidad, luego por lotes_config."""
    tipo = PDI.detectar_tipo_por_modelo(unidad.get("reefer_model") or "")
    if tipo:
        return tipo
    if unidad.get("id_lote"):
        cfg = execute_read("SELECT tipo_reefer FROM lotes_config WHERE id_lote=%s", (unidad["id_lote"],))
        if cfg and cfg[0]["tipo_reefer"]:
            return cfg[0]["tipo_reefer"]
    return ""


def _valores_toma_de_valores(unit_number: str) -> Dict[str, str]:
    """Junta todos los valores de Toma de Valores de todas las asignaciones de esta unidad.
    Si un campo se repite en varias asignaciones, gana el de la asignación más reciente."""
    asigs = execute_read(
        "SELECT id FROM asignaciones WHERE unidad=%s ORDER BY id ASC", (unit_number,)
    )
    if not asigs:
        return {}
    ids = [a["id"] for a in asigs]
    placeholders = ",".join(["%s"] * len(ids))
    rows = execute_read(
        f"SELECT asignacion_id, campo_nombre, valor FROM toma_valores_datos "
        f"WHERE asignacion_id IN ({placeholders})",
        tuple(ids),
    )
    out = {}
    for r in rows:
        if r["valor"]:
            out[PDI.normalizar(r["campo_nombre"])] = r["valor"]
    return out


def _emparejar_lecturas(lecturas_def: list, valores_tv: Dict[str, str]):
    """Devuelve (valores_encontrados{clave:valor}, campos_faltantes[label])."""
    encontrados = {}
    faltantes = []
    for l in lecturas_def:
        hit = None
        for alias in l["alias"]:
            na = PDI.normalizar(alias)
            if na in valores_tv:
                hit = valores_tv[na]
                break
        if hit is not None:
            encontrados[l["clave"]] = hit
        else:
            faltantes.append(l["label"])
    return encontrados, faltantes


def _crear_pdi(unit_number: str, unidad: dict, tipo: str, usuario: str) -> int:
    tpl = PDI.TEMPLATES[tipo]
    header_defaults = {}
    for hf in tpl["header_fields"]:
        if hf["auto"]:
            header_defaults[hf["clave"]] = unidad.get(hf["auto"]) or ""

    cols = [
        "id_lote", "unit_number", "tipo", "cliente", "direccion", "ciudad_estado_cp",
        "fabricante_trailer", "modelo_trailer", "vin_trailer", "numero_flota", "distribuidor",
        "modelo_unidad", "numero_serie_unidad", "numero_serie_motor", "numero_serie_compresor",
        "numero_serie_ees", "numero_serie_generador", "modelo_2do_evap", "numero_serie_2do_evap",
        "modelo_3er_evap", "numero_serie_3er_evap", "tecnico_instalo", "fecha_instalacion",
        "created_by",
    ]
    valores = [
        unidad.get("id_lote") or "", unit_number, tipo,
        "", "", "", "", "",
        header_defaults.get("vin_trailer", ""), header_defaults.get("numero_flota", unit_number), "",
        header_defaults.get("modelo_unidad", ""), header_defaults.get("numero_serie_unidad", ""),
        header_defaults.get("numero_serie_motor", ""), header_defaults.get("numero_serie_compresor", ""),
        "", header_defaults.get("numero_serie_generador", ""),
        header_defaults.get("modelo_2do_evap", ""), header_defaults.get("numero_serie_2do_evap", ""),
        header_defaults.get("modelo_3er_evap", ""), header_defaults.get("numero_serie_3er_evap", ""),
        "", "", usuario,
    ]
    placeholders = ",".join(["%s"] * len(cols))
    insp_id = execute_write_with_id(
        f"INSERT INTO pdi_inspecciones ({', '.join(cols)}) VALUES ({placeholders})",
        tuple(valores),
    )
    _autocompletar(insp_id, tipo, unit_number)
    return insp_id


def _autocompletar(insp_id: int, tipo: str, unit_number: str):
    """Auto-check de todo el checklist previo a Unit Registration + auto-fill de lecturas
    desde Toma de Valores. Es seguro llamarla varias veces (upsert)."""
    tpl = PDI.TEMPLATES[tipo]

    # 1) Auto-check checklist (todas las secciones con es_registro=False)
    filas = []
    for item_clave, sec_clave, texto, es_registro in PDI.checklist_items_planos(tipo):
        if not es_registro:
            filas.append((insp_id, item_clave, "1", "auto"))

    # 2) Auto-fill lecturas desde toma_valores
    valores_tv = _valores_toma_de_valores(unit_number)
    encontrados, _faltantes = _emparejar_lecturas(tpl["lecturas"], valores_tv)
    for clave, valor in encontrados.items():
        filas.append((insp_id, f"lec_{clave}", str(valor), "auto"))

    for insp, clave, valor, origen in filas:
        execute_write(
            "INSERT INTO pdi_datos (inspeccion_id, campo_clave, valor, origen) VALUES (%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE valor=IF(origen='manual', valor, VALUES(valor))",
            (insp, clave, valor, origen),
        )


def _cargar_datos(insp_id: int) -> Dict[str, str]:
    rows = execute_read("SELECT campo_clave, valor FROM pdi_datos WHERE inspeccion_id=%s", (insp_id,))
    return {r["campo_clave"]: r["valor"] or "" for r in rows}


# ──────────────────────────────────────────────────────────────────────────
# Plantillas
# ──────────────────────────────────────────────────────────────────────────
@router.get("/templates")
def get_templates(current_user=Depends(verify_token)):
    return {"x4": PDI.TEMPLATES["x4"], "vector": PDI.TEMPLATES["vector"]}


# ──────────────────────────────────────────────────────────────────────────
# Configuración de lotes (tipo de reefer)
# ──────────────────────────────────────────────────────────────────────────
@router.get("/lotes-config")
def listar_lotes_config(current_user=Depends(verify_token)):
    lotes = execute_read(
        "SELECT id_lote, COUNT(*) AS total_unidades FROM unidades "
        "WHERE oculto=0 GROUP BY id_lote ORDER BY id_lote"
    )
    cfg = execute_read("SELECT id_lote, tipo_reefer, updated_at FROM lotes_config")
    cfg_map = {c["id_lote"]: c for c in cfg}
    out = []
    for l in lotes:
        c = cfg_map.get(l["id_lote"], {})
        out.append({
            "id_lote": l["id_lote"],
            "total_unidades": l["total_unidades"],
            "tipo_reefer": c.get("tipo_reefer") or "",
            "updated_at": str(c.get("updated_at") or ""),
        })
    return out


@router.post("/lotes-config")
def set_lote_tipo(data: LoteTipoSet, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if data.tipo_reefer not in ("x4", "vector"):
        raise HTTPException(status_code=400, detail="tipo_reefer debe ser 'x4' o 'vector'")
    existe = execute_read("SELECT id FROM unidades WHERE id_lote=%s", (data.id_lote,))
    if not existe:
        raise HTTPException(status_code=404, detail=f"Lote '{data.id_lote}' no encontrado")
    execute_write(
        "INSERT INTO lotes_config (id_lote, tipo_reefer, updated_by) VALUES (%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE tipo_reefer=VALUES(tipo_reefer), updated_by=VALUES(updated_by)",
        (data.id_lote, data.tipo_reefer, current_user["username"]),
    )
    # Resincroniza los PDIs ya creados de este lote (por si cambiaron de tipo antes de tener PDI)
    return {"mensaje": f"Lote '{data.id_lote}' configurado como {data.tipo_reefer.upper()}"}


# ──────────────────────────────────────────────────────────────────────────
# Listado de PDIs
# ──────────────────────────────────────────────────────────────────────────
@router.get("")
def listar_pdis(
    id_lote: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    current_user=Depends(verify_token),
):
    sql = "SELECT * FROM pdi_inspecciones WHERE 1=1"
    params = []
    if id_lote:
        sql += " AND id_lote=%s"
        params.append(id_lote)
    if tipo:
        sql += " AND tipo=%s"
        params.append(tipo)
    if estado:
        sql += " AND estado=%s"
        params.append(estado)
    sql += " ORDER BY updated_at DESC"
    return execute_read(sql, tuple(params))


# ──────────────────────────────────────────────────────────────────────────
# Obtener (o auto-crear) el PDI de una unidad
# ──────────────────────────────────────────────────────────────────────────
@router.get("/unidad/{unit_number}")
def get_pdi_unidad(unit_number: str, current_user=Depends(verify_token)):
    unidad = _get_unidad(unit_number)
    if not unidad:
        raise HTTPException(status_code=404, detail=f"Unidad '{unit_number}' no encontrada")

    existentes = execute_read(
        "SELECT * FROM pdi_inspecciones WHERE unit_number=%s ORDER BY id DESC LIMIT 1",
        (unit_number,),
    )
    tipo = _resolver_tipo(unidad)

    if not existentes:
        if not tipo:
            return {
                "requiere_tipo": True,
                "mensaje": "No se pudo determinar si esta unidad es X4 o Vector. "
                           "Asigna el tipo de reefer al lote o captura el modelo en la unidad.",
                "unidad": unidad,
            }
        insp_id = _crear_pdi(unit_number, unidad, tipo, current_user["username"])
        pdi = execute_read("SELECT * FROM pdi_inspecciones WHERE id=%s", (insp_id,))[0]
    else:
        pdi = existentes[0]
        # Resincroniza auto-check + auto-fill por si hay datos nuevos de Toma de Valores
        _autocompletar(pdi["id"], pdi["tipo"], unit_number)

    tpl = PDI.TEMPLATES[pdi["tipo"]]
    datos = _cargar_datos(pdi["id"])
    valores_tv = _valores_toma_de_valores(unit_number)
    _encontrados, faltantes = _emparejar_lecturas(tpl["lecturas"], valores_tv)

    return {
        "requiere_tipo": False,
        "pdi": pdi,
        "template": tpl,
        "datos": datos,
        "campos_faltantes": faltantes,
    }


@router.post("/unidad/{unit_number}/resincronizar")
def resincronizar(unit_number: str, current_user=Depends(verify_token)):
    pdi = execute_read(
        "SELECT * FROM pdi_inspecciones WHERE unit_number=%s ORDER BY id DESC LIMIT 1", (unit_number,)
    )
    if not pdi:
        raise HTTPException(status_code=404, detail="Esta unidad todavía no tiene PDI")
    _autocompletar(pdi[0]["id"], pdi[0]["tipo"], unit_number)
    return {"mensaje": "PDI resincronizado con Toma de Valores"}


# ──────────────────────────────────────────────────────────────────────────
# Detalle / edición de un PDI puntual
# ──────────────────────────────────────────────────────────────────────────
@router.get("/{insp_id}")
def get_pdi(insp_id: int, current_user=Depends(verify_token)):
    rows = execute_read("SELECT * FROM pdi_inspecciones WHERE id=%s", (insp_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="PDI no encontrado")
    pdi = rows[0]
    tpl = PDI.TEMPLATES[pdi["tipo"]]
    datos = _cargar_datos(insp_id)
    return {"pdi": pdi, "template": tpl, "datos": datos}


@router.put("/{insp_id}")
def actualizar_header(insp_id: int, data: HeaderUpdate, current_user=Depends(verify_token)):
    if current_user["role"] == "visor":
        raise HTTPException(status_code=403, detail="Modo solo lectura")
    rows = execute_read("SELECT * FROM pdi_inspecciones WHERE id=%s", (insp_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="PDI no encontrado")

    campos_validos = {
        "cliente", "direccion", "ciudad_estado_cp", "fabricante_trailer", "modelo_trailer",
        "vin_trailer", "numero_flota", "distribuidor", "modelo_unidad", "numero_serie_unidad",
        "numero_serie_motor", "numero_serie_compresor", "numero_serie_ees", "numero_serie_generador",
        "modelo_2do_evap", "numero_serie_2do_evap", "modelo_3er_evap", "numero_serie_3er_evap",
        "tecnico_instalo", "fecha_instalacion", "dealer_firma", "tecnico_inspecciono", "comentarios",
    }
    sets, params = [], []
    for k, v in data.valores.items():
        if k in campos_validos:
            sets.append(f"{k}=%s")
            params.append(v)
    if data.estado:
        if data.estado not in ("borrador", "completado"):
            raise HTTPException(status_code=400, detail="estado inválido")
        sets.append("estado=%s")
        params.append(data.estado)
    if not sets:
        return {"mensaje": "Sin cambios"}
    params.append(insp_id)
    execute_write(f"UPDATE pdi_inspecciones SET {', '.join(sets)} WHERE id=%s", tuple(params))
    return {"mensaje": "PDI actualizado"}


@router.post("/{insp_id}/datos")
def guardar_datos(insp_id: int, data: DatosGuardar, current_user=Depends(verify_token)):
    if current_user["role"] == "visor":
        raise HTTPException(status_code=403, detail="Modo solo lectura")
    rows = execute_read("SELECT id FROM pdi_inspecciones WHERE id=%s", (insp_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="PDI no encontrado")
    for clave, valor in data.valores.items():
        execute_write(
            "INSERT INTO pdi_datos (inspeccion_id, campo_clave, valor, origen) VALUES (%s,%s,%s,'manual') "
            "ON DUPLICATE KEY UPDATE valor=VALUES(valor), origen='manual'",
            (insp_id, clave, valor),
        )
    execute_write("UPDATE pdi_inspecciones SET updated_at=NOW() WHERE id=%s", (insp_id,))
    return {"mensaje": f"{len(data.valores)} campo(s) guardado(s)"}


@router.post("/{insp_id}/campos-faltantes/agregar")
def agregar_campos_faltantes(insp_id: int, data: CamposFaltantesAdd, current_user=Depends(verify_token)):
    """Crea en toma_valores_campos los campos que el PDI necesita y todavía no existen,
    para que a partir de ahora se puedan capturar en la actividad de Toma de Valores."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    max_orden = execute_read("SELECT MAX(campo_orden) AS m FROM toma_valores_campos")
    orden = 0 if not max_orden or max_orden[0]["m"] is None else max_orden[0]["m"] + 1
    agregados = []
    for nombre in data.campos:
        nombre = (nombre or "").strip()
        if not nombre:
            continue
        existe = execute_read("SELECT id FROM toma_valores_campos WHERE campo_nombre=%s", (nombre,))
        if existe:
            continue
        execute_write(
            "INSERT INTO toma_valores_campos (campo_nombre, campo_orden) VALUES (%s,%s)",
            (nombre, orden),
        )
        orden += 1
        agregados.append(nombre)
    return {"mensaje": f"{len(agregados)} campo(s) agregado(s) a Toma de Valores", "agregados": agregados}


@router.get("/{insp_id}/pdf")
def descargar_pdi_pdf(insp_id: int, current_user=Depends(verify_token)):
    """Genera y descarga el PDF del PDI con el formato oficial de Carrier Transicold."""
    rows = execute_read("SELECT * FROM pdi_inspecciones WHERE id=%s", (insp_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="PDI no encontrado")
    pdi = rows[0]
    tpl = PDI.TEMPLATES[pdi["tipo"]]
    datos = _cargar_datos(insp_id)
    pdf_bytes = generar_pdi_pdf(pdi, tpl, datos)
    filename = f"PDI_{pdi['tipo'].upper()}_{pdi['unit_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{insp_id}")
def eliminar_pdi(insp_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM pdi_datos WHERE inspeccion_id=%s", (insp_id,))
    execute_write("DELETE FROM pdi_inspecciones WHERE id=%s", (insp_id,))
    return {"mensaje": "PDI eliminado"}
