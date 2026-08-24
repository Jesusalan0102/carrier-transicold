"""
reportes_semanales.py
----------------------
Resumen semanal automático para gerencia: un correo con KPIs clave de los
últimos 7 días + el Excel maestro completo adjunto, sin que nadie tenga que
entrar al sistema a descargarlo manualmente.

Controlado por variables de entorno (todas opcionales — sin ellas, la
función simplemente no hace nada, no truena el arranque de la app):

  REPORTE_SEMANAL_HABILITADO=1                 → activa el envío automático
  REPORTE_SEMANAL_DESTINATARIOS=a@x.com,b@y.com→ lista separada por comas
  REPORTE_SEMANAL_DIA=0                        → día ISO a enviar (0=lunes … 6=domingo)
  REPORTE_SEMANAL_HORA=8                       → hora local (America/Tijuana) de envío

Requiere que onedrive_service.enviar_correo() funcione, lo cual a su vez
requiere el permiso Mail.Send en Graph (ver docstring de esa función).
"""
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from db import execute_read

TZ = ZoneInfo("America/Tijuana")
logger = logging.getLogger(__name__)


def _semana_iso_actual() -> str:
    y, w, _ = datetime.now(TZ).isocalendar()
    return f"{y}-W{w:02d}"


def _ya_se_envio_esta_semana() -> bool:
    rows = execute_read(
        "SELECT valor FROM system_settings WHERE clave = 'reporte_semanal_ultima_semana'"
    )
    return bool(rows) and rows[0]["valor"] == _semana_iso_actual()


def _marcar_enviado_esta_semana():
    from db import execute_write
    execute_write(
        "INSERT INTO system_settings (clave, valor) VALUES ('reporte_semanal_ultima_semana', %s) "
        "ON DUPLICATE KEY UPDATE valor = %s",
        (_semana_iso_actual(), _semana_iso_actual())
    )


def _generar_resumen_html() -> str:
    """KPIs de los últimos 7 días, en HTML simple listo para email."""
    tickets_semana = execute_read(
        "SELECT atendido, reporte_enviado FROM tickets "
        "WHERE fecha_creacion >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    )
    total_tickets = len(tickets_semana)
    cerrados = sum(1 for t in tickets_semana if t["reporte_enviado"])

    completadas = execute_read(
        "SELECT COUNT(*) AS n FROM asignaciones "
        "WHERE estado='completada' AND fecha_fin >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    )[0]["n"]

    top_tecnicos = execute_read(
        """
        SELECT COALESCE(NULLIF(usr.nombre_completo, ''), a.tecnico) AS tecnico, COUNT(*) AS completadas
        FROM asignaciones a
        LEFT JOIN users usr ON usr.username = a.tecnico
        WHERE a.estado = 'completada' AND a.fecha_fin >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY a.tecnico, usr.nombre_completo
        ORDER BY completadas DESC LIMIT 5
        """
    )

    filas_tecnicos = "".join(
        f"<tr><td style='padding:4px 10px;'>{t['tecnico']}</td>"
        f"<td style='padding:4px 10px;text-align:right;'>{t['completadas']}</td></tr>"
        for t in top_tecnicos
    ) or "<tr><td style='padding:4px 10px;' colspan='2'>Sin actividad esta semana</td></tr>"

    fecha_hoy = datetime.now(TZ).strftime("%d/%m/%Y")
    return f"""
    <div style="font-family:Arial,sans-serif;color:#1a2332;">
        <h2 style="color:#1F4E79;">📊 Resumen semanal — Carrier Transicold ({fecha_hoy})</h2>
        <p>Reporte automático de los últimos 7 días. El detalle completo va adjunto en Excel.</p>
        <table style="border-collapse:collapse;margin:14px 0;">
            <tr><td style="padding:4px 10px;font-weight:bold;">Tickets creados</td><td style="padding:4px 10px;">{total_tickets}</td></tr>
            <tr><td style="padding:4px 10px;font-weight:bold;">Tickets cerrados con reporte</td><td style="padding:4px 10px;">{cerrados}</td></tr>
            <tr><td style="padding:4px 10px;font-weight:bold;">Actividades completadas</td><td style="padding:4px 10px;">{completadas}</td></tr>
        </table>
        <h3 style="color:#1F4E79;">Top técnicos de la semana</h3>
        <table style="border-collapse:collapse;">{filas_tecnicos}</table>
        <p style="color:#8a97ab;font-size:0.85rem;margin-top:20px;">
            Este correo se generó automáticamente. Para el detalle completo, entra al sistema
            o revisa el Excel adjunto.
        </p>
    </div>
    """


def enviar_reporte_semanal(forzar: bool = False) -> dict:
    """
    Genera y envía el resumen semanal si corresponde. `forzar=True` ignora
    el chequeo de "ya se envió esta semana" (para pruebas manuales vía
    endpoint de admin).
    """
    if os.getenv("REPORTE_SEMANAL_HABILITADO", "0") != "1":
        return {"enviado": False, "motivo": "REPORTE_SEMANAL_HABILITADO no está en '1'"}

    destinatarios_raw = os.getenv("REPORTE_SEMANAL_DESTINATARIOS", "")
    destinatarios = [d.strip() for d in destinatarios_raw.split(",") if d.strip()]
    if not destinatarios:
        return {"enviado": False, "motivo": "REPORTE_SEMANAL_DESTINATARIOS está vacío"}

    if not forzar and _ya_se_envio_esta_semana():
        return {"enviado": False, "motivo": "Ya se envió el reporte de esta semana ISO"}

    try:
        from onedrive_service import enviar_correo
    except ImportError:
        return {"enviado": False, "motivo": "onedrive_service no disponible"}

    from routers.dashboard_router import _generar_excel_maestro_bytes

    try:
        excel_bytes = _generar_excel_maestro_bytes()
        html = _generar_resumen_html()
        fecha = datetime.now(TZ).strftime("%Y-%m-%d")
        enviar_correo(
            destinatarios=destinatarios,
            asunto=f"📊 Resumen semanal Carrier Transicold — {fecha}",
            cuerpo_html=html,
            adjunto_nombre=f"Carrier_Reporte_{fecha}.xlsx",
            adjunto_bytes=excel_bytes,
        )
        _marcar_enviado_esta_semana()
        logger.info(f"[reporte_semanal] Enviado a {destinatarios}")
        return {"enviado": True, "destinatarios": destinatarios}
    except Exception as e:
        logger.error(f"[reporte_semanal] Falló el envío: {e}")
        return {"enviado": False, "motivo": str(e)}


async def programador_reporte_semanal():
    """
    Tarea en segundo plano (mismo patrón que monitor_corriendo_6h en ws.py):
    revisa cada hora si es el día/hora configurados y, de ser así, dispara
    el envío. La protección contra duplicados vive en system_settings, así
    que sobrevive a reinicios del proceso.
    """
    import asyncio

    if os.getenv("REPORTE_SEMANAL_HABILITADO", "0") != "1":
        logger.info("[reporte_semanal] Desactivado (REPORTE_SEMANAL_HABILITADO != 1) — programador no se inicia")
        return

    dia_objetivo = int(os.getenv("REPORTE_SEMANAL_DIA", "0"))    # 0 = lunes
    hora_objetivo = int(os.getenv("REPORTE_SEMANAL_HORA", "8"))  # 8am hora Tijuana

    while True:
        try:
            ahora = datetime.now(TZ)
            if ahora.weekday() == dia_objetivo and ahora.hour == hora_objetivo:
                resultado = enviar_reporte_semanal()
                if resultado["enviado"]:
                    logger.info(f"[reporte_semanal] {resultado}")
                elif "Ya se envió" not in resultado.get("motivo", ""):
                    logger.warning(f"[reporte_semanal] No enviado: {resultado['motivo']}")
        except Exception as e:
            logger.error(f"[reporte_semanal] Error en programador: {e}")
        await asyncio.sleep(3600)  # revisa una vez por hora
