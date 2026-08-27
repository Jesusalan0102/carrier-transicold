from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from models import AsignacionCreate, AsignacionUpdate
from datetime import datetime
from zoneinfo import ZoneInfo
import corriendo_tracking
import asyncio
TZ = ZoneInfo("America/Tijuana")

def _notify(event: str, payload: dict = None):
    """Emite evento WebSocket+Push desde endpoint síncrono."""
    import threading
    def _run():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from routers.ws import notify
            loop.run_until_complete(notify(event, payload))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"_notify error: {e}")
        finally:
            loop.close()
    threading.Thread(target=_run, daemon=True).start()

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])

# ── LISTAR (admin/lider/visor ven todo, técnico ve solo las suyas) ─────────
@router.get("/")
def listar_asignaciones(estado: str = None, tecnico: str = None, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor", "lider"):
        tecnico = current_user["username"]
    query = "SELECT * FROM asignaciones WHERE 1=1"
    params = []
    if estado:
        query += " AND estado=%s"
        params.append(estado)
    if tecnico:
        query += " AND tecnico=%s"
        params.append(tecnico)
    query += " ORDER BY id DESC"
    return execute_read(query, tuple(params))

# ── SOLICITUDES PENDIENTES DE APROBACIÓN (admin y líder) ───────────────────
@router.get("/solicitudes")
def listar_solicitudes(current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")
    solicitudes = execute_read(
        "SELECT * FROM asignaciones WHERE estado='solicitado' ORDER BY id DESC"
    )
    resultado = []
    for s in solicitudes:
        dup_comp = execute_read(
            "SELECT tecnico FROM asignaciones WHERE unidad=%s AND actividad_id=%s AND estado='completada'",
            (s["unidad"], s["actividad_id"])
        )
        dup_activa = execute_read(
            "SELECT tecnico, estado FROM asignaciones "
            "WHERE unidad=%s AND actividad_id=%s AND estado IN ('pendiente','en_proceso') AND id != %s",
            (s["unidad"], s["actividad_id"], s["id"])
        )
        resultado.append({
            **s,
            "alerta_completada": [d["tecnico"] for d in dup_comp],
            "alerta_duplicada":  [{"tecnico": d["tecnico"], "estado": d["estado"]} for d in dup_activa],
        })
    return resultado

# ── HISTORIAL DE UN TÉCNICO ────────────────────────────────────────────────
@router.get("/historial")
def historial(current_user=Depends(verify_token)):
    tecnico = current_user["username"]
    return execute_read(
        "SELECT unidad, actividad_id, estado, fecha_inicio, fecha_fin "
        "FROM asignaciones WHERE tecnico=%s ORDER BY id DESC LIMIT 30",
        (tecnico,)
    )

# ── MIS TAREAS ACTIVAS (técnico) ───────────────────────────────────────────
@router.get("/mis-tareas")
def mis_tareas(current_user=Depends(verify_token)):
    return execute_read(
        "SELECT * FROM asignaciones WHERE tecnico=%s AND estado IN ('pendiente','en_proceso') ORDER BY id DESC",
        (current_user["username"],)
    )

# ── CREAR (admin o líder asigna directo) ───────────────────────────────────
@router.post("/")
def crear_asignacion(asig: AsignacionCreate, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes pueden asignar directamente")
    execute_write(
        "INSERT INTO asignaciones (unidad, actividad_id, tecnico, estado, fecha_asignacion) VALUES (%s,%s,%s,%s,%s)",
        (asig.unidad, asig.actividad_id, asig.tecnico, asig.estado, datetime.now(TZ))
    )
    _notify("asignacion_nueva", {"tecnico": asig.tecnico, "unidad": asig.unidad})
    return {"mensaje": "Asignación creada"}

# ── SOLICITAR (técnico pide aprobación) ────────────────────────────────────
@router.post("/solicitar")
def solicitar_actividad(asig: AsignacionCreate, current_user=Depends(verify_token)):
    tecnico = current_user["username"]
    # Validar si ya tiene esa actividad activa
    activa = execute_read(
        "SELECT id, estado FROM asignaciones WHERE tecnico=%s AND unidad=%s AND actividad_id=%s "
        "AND estado IN ('solicitado','pendiente','en_proceso')",
        (tecnico, asig.unidad, asig.actividad_id)
    )
    if activa:
        estado_act = activa[0]["estado"]
        etiquetas = {
            "solicitado": "esperando aprobación del administrador",
            "pendiente":  "pendiente de iniciar",
            "en_proceso": "actualmente en proceso",
        }
        raise HTTPException(
            status_code=400,
            detail=f"Ya tienes esta actividad registrada ({etiquetas.get(estado_act, estado_act)})"
        )
    execute_write(
        "INSERT INTO asignaciones (unidad, actividad_id, tecnico, estado, fecha_asignacion) VALUES (%s,%s,%s,'solicitado',%s)",
        (asig.unidad, asig.actividad_id, tecnico, datetime.now(TZ))
    )
    _notify("solicitud_nueva", {"tecnico": tecnico, "unidad": asig.unidad})
    return {"mensaje": "Solicitud enviada, pendiente de aprobación"}

# ── APROBAR (admin o líder) ─────────────────────────────────────────────────
@router.post("/{asig_id}/aprobar")
def aprobar(asig_id: int, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")
    execute_write("UPDATE asignaciones SET estado='pendiente' WHERE id=%s", (asig_id,))
    _notify("solicitud_aprobada", {"asignacion_id": asig_id})
    return {"mensaje": "Solicitud aprobada"}

# ── RECHAZAR/ELIMINAR (admin o líder) ──────────────────────────────────────
@router.delete("/{asig_id}/rechazar")
def rechazar(asig_id: int, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")
    execute_write("DELETE FROM asignaciones WHERE id=%s", (asig_id,))
    return {"mensaje": "Solicitud rechazada y eliminada"}

# ── INICIAR (técnico) ──────────────────────────────────────────────────────
@router.patch("/{asig_id}/iniciar")
def iniciar(asig_id: int, current_user=Depends(verify_token)):
    rows = execute_read("SELECT unidad, actividad_id FROM asignaciones WHERE id=%s", (asig_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    unidad, actividad_id = rows[0]["unidad"], rows[0]["actividad_id"]
    execute_write(
        "UPDATE asignaciones SET estado='en_proceso', fecha_inicio=%s, alerta_6h_enviada=0 WHERE id=%s",
        (datetime.now(TZ), asig_id)
    )
    if actividad_id == "Corriendo":
        # Arranca o reanuda el contador acumulado de horas corriendo de la unidad
        corriendo_tracking.iniciar(unidad)
    _notify("actividad_iniciada", {"asignacion_id": asig_id})
    return {"mensaje": "Actividad iniciada"}

# ── PAUSAR (técnico: detiene sin marcar como completada) ───────────────────
@router.patch("/{asig_id}/pausar")
def pausar(asig_id: int, current_user=Depends(verify_token)):
    rows = execute_read("SELECT unidad, actividad_id, estado FROM asignaciones WHERE id=%s", (asig_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    row = rows[0]
    if row["estado"] != "en_proceso":
        raise HTTPException(status_code=400, detail="Solo se puede pausar una actividad en proceso")
    execute_write(
        "UPDATE asignaciones SET estado='pendiente', fecha_inicio=NULL WHERE id=%s",
        (asig_id,)
    )
    if row["actividad_id"] == "Corriendo":
        # Guarda el tiempo transcurrido en el acumulado para retomarlo después
        corriendo_tracking.pausar(row["unidad"])
    _notify("actividad_pausada", {"asignacion_id": asig_id, "unidad": row["unidad"]})
    return {"mensaje": "Actividad pausada; tiempo acumulado guardado"}

# ── PAUSAR TODAS (técnico: pausa de una vez todas sus actividades en proceso,
#    pensado para el receso/hora de comida) ─────────────────────────────────
@router.patch("/pausar-todas")
def pausar_todas(current_user=Depends(verify_token)):
    rows = execute_read(
        "SELECT id, unidad, actividad_id FROM asignaciones WHERE tecnico=%s AND estado='en_proceso'",
        (current_user["username"],)
    )
    if not rows:
        return {"mensaje": "No tienes actividades en proceso para pausar", "pausadas": 0}

    ids = [r["id"] for r in rows]
    execute_write(
        f"UPDATE asignaciones SET estado='pendiente', fecha_inicio=NULL "
        f"WHERE id IN ({','.join(['%s'] * len(ids))})",
        tuple(ids)
    )
    for r in rows:
        if r["actividad_id"] == "Corriendo":
            # Guarda el tiempo transcurrido en el acumulado de cada unidad afectada
            corriendo_tracking.pausar(r["unidad"])
        _notify("actividad_pausada", {"asignacion_id": r["id"], "unidad": r["unidad"]})

    return {"mensaje": f"{len(ids)} actividad(es) pausada(s) por receso", "pausadas": len(ids)}

# ── FINALIZAR (técnico, comentario obligatorio) ────────────────────────────
@router.patch("/{asig_id}/finalizar")
def finalizar(asig_id: int, data: dict, current_user=Depends(verify_token)):
    comentario = data.get("comentario", "").strip()
    if not comentario:
        raise HTTPException(status_code=400, detail="El comentario es obligatorio para finalizar")
    ticket_id = data.get("ticket_id")
    now = datetime.now(TZ)
    asig_rows = execute_read("SELECT unidad, actividad_id FROM asignaciones WHERE id=%s", (asig_id,))
    execute_write(
        "UPDATE asignaciones SET estado='completada', fecha_fin=%s WHERE id=%s",
        (now, asig_id)
    )
    if asig_rows and asig_rows[0]["actividad_id"] == "Corriendo":
        # Guarda el tiempo transcurrido en el acumulado, aunque se termine antes de las 6h
        corriendo_tracking.pausar(asig_rows[0]["unidad"])
    execute_write(
        "INSERT INTO comentarios_actividades (asignacion_id, tecnico, comentario) VALUES (%s,%s,%s)",
        (asig_id, current_user["username"], comentario)
    )
    if ticket_id:
        execute_write(
            "UPDATE tickets SET atendido=TRUE, fecha_atencion=%s WHERE id=%s",
            (now, ticket_id)
        )
    _notify("actividad_completada", {"asignacion_id": asig_id, "tecnico": current_user["username"]})
    return {"mensaje": "Actividad finalizada"}

# ── EDITAR (admin o líder: cambiar estado/técnico/actividad + comentario) ──
@router.put("/{asig_id}")
def editar_asignacion(asig_id: int, update: AsignacionUpdate, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")
    fields, params = [], []
    if update.estado is not None:
        fields.append("estado=%s"); params.append(update.estado)
    if update.tecnico is not None:
        fields.append("tecnico=%s"); params.append(update.tecnico)
    if update.actividad_id is not None:
        fields.append("actividad_id=%s"); params.append(update.actividad_id)
    if fields:
        params.append(asig_id)
        execute_write(f"UPDATE asignaciones SET {', '.join(fields)} WHERE id=%s", tuple(params))
    if update.comentario and update.comentario.strip():
        execute_write(
            "INSERT INTO comentarios_actividades (asignacion_id, tecnico, comentario) VALUES (%s,%s,%s)",
            (asig_id, current_user["username"], update.comentario.strip())
        )
    return {"mensaje": "Asignación actualizada"}

# ── ELIMINAR (admin o líder) ────────────────────────────────────────────────
@router.delete("/{asig_id}")
def eliminar_asignacion(asig_id: int, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")
    execute_write("DELETE FROM comentarios_actividades WHERE asignacion_id=%s", (asig_id,))
    execute_write("DELETE FROM asignaciones WHERE id=%s", (asig_id,))
    return {"mensaje": "Asignación eliminada"}
