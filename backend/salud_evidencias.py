"""
Monitor de salud de la evidencia (corre solo, cada 6 h).

Lo que habría evitado que 12 tareas se cerraran sin evidencia durante casi dos semanas sin que nadie
lo notara:
  1. Revisa que OneDrive funcione (token vigente y espacio libre).
  2. Audita: tareas completadas sin evidencia, videos sin archivo, subidas a medias, videos que
     siguen solo en la base de datos.
  3. Si OneDrive está sano, copia unos pocos videos de la base a OneDrive por ciclo (sin borrarlos de la DB).
  4. Avisa por notificación push a los admins cuando aparece o empeora un problema.
El resultado se guarda en `salud_sistema` y se muestra en el panel (banner) y en /api/evidencias/salud.
"""
import asyncio
import json
import logging
import time

from db import execute_read, execute_write

logger = logging.getLogger(__name__)

INTERVALO_SEG = 6 * 3600
PRIMERA_ESPERA_SEG = 90
COPIAR_POR_CICLO = 3          # videos DB -> OneDrive por ciclo (cada uno puede pesar varios MB)
DIAS_AUDITORIA = 14
REALERTA_ONEDRIVE_HORAS = 24
_VIDEO_REGEX = "[.](mp4|mov|webm|m4v|3gp|avi|mkv)$"


# ── almacenamiento del estado ──────────────────────────────────────────────
def _asegurar_tabla():
    execute_write(
        "CREATE TABLE IF NOT EXISTS salud_sistema ("
        "clave VARCHAR(60) PRIMARY KEY, valor LONGTEXT, actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )


def guardar_estado(clave: str, valor: dict) -> None:
    _asegurar_tabla()
    execute_write(
        "REPLACE INTO salud_sistema (clave, valor) VALUES (%s, %s)",
        (clave, json.dumps(valor, ensure_ascii=False, default=str)),
    )


def leer_estado(clave: str):
    try:
        _asegurar_tabla()
        r = execute_read("SELECT valor, actualizado_en FROM salud_sistema WHERE clave=%s", (clave,))
        if not r:
            return None
        d = json.loads(r[0]["valor"])
        d["_actualizado"] = str(r[0]["actualizado_en"])
        return d
    except Exception as e:
        logger.warning(f"[salud] no se pudo leer {clave}: {e}")
        return None


# ── revisiones ──────────────────────────────────────────────────────────────
def revisar_onedrive() -> dict:
    """Token vigente + cuota. Nunca lanza excepción: devuelve ok=False con la razón."""
    try:
        import requests
        import onedrive_service as od
    except Exception as e:
        return {"ok": False, "paso": "importar", "error": str(e)[:300]}
    try:
        od._cached_token["expires_at"] = 0           # forzar token nuevo, sin caché
        token = od._get_token()
    except Exception as e:
        return {"ok": False, "paso": "token", "error": str(e)[:400],
                "que_hacer": "Si dice invalid_grant/expired hay que generar un MS_REFRESH_TOKEN nuevo; "
                             "si dice invalid_client venció el secreto de la app (MS_CLIENT_SECRET_PERSONAL)."}
    try:
        r = requests.get(f"{od.GRAPH_BASE}/me/drive?select=id,driveType,quota",
                         headers={"Authorization": f"Bearer {token}"}, timeout=20)
        if not r.ok:
            return {"ok": False, "paso": "graph", "http": r.status_code, "error": r.text[:300]}
        q = r.json().get("quota") or {}
        gb = lambda b: round((b or 0) / 1024 ** 3, 2)
        estado = {"ok": True, "estado_cuota": q.get("state"), "usado_gb": gb(q.get("used")),
                  "total_gb": gb(q.get("total")), "libre_gb": gb(q.get("remaining"))}
        if q.get("state") in ("critical", "exceeded") or (q.get("total") and (q.get("remaining") or 0) < 0.5 * 1024 ** 3):
            estado["ok"] = False
            estado["paso"] = "espacio"
            estado["error"] = f"OneDrive casi lleno: quedan {estado['libre_gb']} GB"
        return estado
    except Exception as e:
        return {"ok": False, "paso": "graph", "error": str(e)[:300]}


def auditar() -> dict:
    """Busca evidencia faltante o en riesgo. Solo lectura."""
    from datetime import datetime, timedelta
    desde = (datetime.utcnow() - timedelta(days=DIAS_AUDITORIA)).strftime("%Y-%m-%d")
    sin_evidencia = execute_read(
        "SELECT a.id, a.unidad, a.actividad_id, a.tecnico, a.fecha_fin "
        "FROM asignaciones a LEFT JOIN evidencias e ON e.asignacion_id = a.id "
        "WHERE a.estado='completada' AND a.fecha_fin >= %s AND e.id IS NULL "
        "ORDER BY a.fecha_fin DESC LIMIT 100", (desde,)
    ) or []
    perdidos = execute_read(
        "SELECT COUNT(*) AS n FROM evidencias e WHERE (e.tipo='video' OR LOWER(e.nombre_archivo) REGEXP %s) "
        "AND e.contenido IS NULL AND (e.onedrive_item_id IS NULL OR e.onedrive_item_id='') "
        "AND NOT EXISTS (SELECT 1 FROM evidencia_partes p WHERE p.evidencia_id = e.id)", (_VIDEO_REGEX,)
    )
    incompletas = execute_read(
        "SELECT upload_id, tecnico, unidad, asignacion_id, nombre_archivo, tamano, creado_en FROM video_uploads "
        "WHERE evidencia_id IS NULL AND creado_en < (NOW() - INTERVAL 2 HOUR) AND creado_en > (NOW() - INTERVAL 7 DAY) "
        "ORDER BY creado_en DESC LIMIT 50"
    ) or []
    solo_db = execute_read(
        "SELECT COUNT(*) AS n, COALESCE(SUM(LENGTH(contenido)),0) AS b FROM evidencias "
        "WHERE contenido IS NOT NULL AND (onedrive_item_id IS NULL OR onedrive_item_id='') "
        "AND (tipo='video' OR LOWER(nombre_archivo) REGEXP %s)", (_VIDEO_REGEX,)
    )
    return {
        "tareas_sin_evidencia": [
            {"id": r["id"], "unidad": r["unidad"], "actividad": r["actividad_id"], "tecnico": r["tecnico"],
             "fecha_fin": str(r["fecha_fin"] or "")} for r in sin_evidencia],
        "videos_sin_archivo": int(perdidos[0]["n"]) if perdidos else 0,
        "subidas_incompletas": [
            {"upload_id": r["upload_id"], "tecnico": r["tecnico"], "unidad": r["unidad"],
             "asignacion_id": r["asignacion_id"], "archivo": r["nombre_archivo"],
             "mb": round((r["tamano"] or 0) / 1048576, 1), "desde": str(r["creado_en"])} for r in incompletas],
        "videos_solo_en_db": int(solo_db[0]["n"]) if solo_db else 0,
        "mb_videos_solo_en_db": round(float(solo_db[0]["b"]) / 1048576, 1) if solo_db else 0.0,
    }


def problemas(onedrive: dict, auditoria: dict) -> list:
    """Lista corta, legible, de lo que requiere atención. Vacía = todo bien."""
    out = []
    if onedrive and not onedrive.get("ok"):
        out.append(f"OneDrive no funciona ({onedrive.get('paso', '?')}): {onedrive.get('error', '')[:140]}")
    n = len(auditoria.get("tareas_sin_evidencia", []))
    if n:
        out.append(f"{n} tarea(s) completada(s) sin evidencia en los últimos {DIAS_AUDITORIA} días")
    if auditoria.get("videos_sin_archivo"):
        out.append(f"{auditoria['videos_sin_archivo']} video(s) registrados pero sin archivo")
    if auditoria.get("subidas_incompletas"):
        out.append(f"{len(auditoria['subidas_incompletas'])} subida(s) de video a medias (más de 2 h)")
    return out


def evaluar() -> dict:
    """Revisión completa sin efectos secundarios (la usa el panel con ?ahora=true)."""
    od_estado = revisar_onedrive()
    aud = auditar()
    return {"onedrive": od_estado, "auditoria": aud, "problemas": problemas(od_estado, aud)}


# ── avisos ───────────────────────────────────────────────────────────────────
def _avisar_admins(titulo: str, cuerpo: str) -> None:
    try:
        from routers.push_router import send_push_to_users
        admins = [r["username"] for r in (execute_read("SELECT username FROM users WHERE role='admin'") or [])]
        send_push_to_users(admins, titulo, cuerpo, tag="salud-evidencia", url="/app/verificar-videos")
    except Exception as e:
        logger.warning(f"[salud] no se pudo enviar el aviso push: {e}")


def _debe_avisar(prob: list, onedrive_ok: bool, previo: dict | None, ahora: float) -> bool:
    if not prob:
        return False
    firma = "|".join(sorted(prob))
    if not previo or previo.get("firma") != firma:
        return True                                   # problema nuevo o distinto
    horas = (ahora - float(previo.get("ts", 0))) / 3600
    return (not onedrive_ok) and horas >= REALERTA_ONEDRIVE_HORAS   # OneDrive caído: recordar cada día


def ciclo(copiar: bool = True) -> dict:
    """Un ciclo completo: revisar, copiar a OneDrive, guardar estado y avisar si hace falta."""
    ahora = time.time()
    estado = evaluar()
    copiado = None
    if copiar and estado["onedrive"].get("ok") and estado["auditoria"]["videos_solo_en_db"]:
        try:
            from routers.evidencias_router import copiar_videos_a_onedrive
            r = copiar_videos_a_onedrive(aplicar=True, limite=COPIAR_POR_CICLO, desde_id=0,
                                         current_user={"username": "sistema", "role": "admin"})
            copiado = {"migrados": len(r.get("migrados", [])), "errores": len(r.get("errores", [])),
                       "pendientes": r.get("pendientes_restantes")}
        except Exception as e:
            logger.error(f"[salud] copia a OneDrive falló: {e}")
            copiado = {"error": str(e)[:200]}
    estado["copia_a_onedrive"] = copiado
    estado["ts"] = ahora
    guardar_estado("evidencia", estado)

    previo = leer_estado("ultima_alerta")
    if _debe_avisar(estado["problemas"], bool(estado["onedrive"].get("ok")), previo, ahora):
        _avisar_admins("⚠️ Evidencia: requiere atención", " · ".join(estado["problemas"])[:180])
        guardar_estado("ultima_alerta", {"firma": "|".join(sorted(estado["problemas"])), "ts": ahora})
    return estado


async def monitor_salud_evidencias():
    """Tarea de fondo: se registra en el arranque de la app (un solo worker)."""
    from fastapi.concurrency import run_in_threadpool
    await asyncio.sleep(PRIMERA_ESPERA_SEG)
    while True:
        try:
            await run_in_threadpool(ciclo)
        except Exception as e:                        # el monitor nunca debe morir
            logger.error(f"[salud] ciclo falló: {e}")
        await asyncio.sleep(INTERVALO_SEG)
