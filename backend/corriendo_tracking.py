# backend/corriendo_tracking.py
"""
Lógica del contador acumulado de horas 'Corriendo' por unidad.

Vive en su propia tabla (corriendo_tracking), independiente de `asignaciones`,
para poder acumular tiempo a través de múltiples pausas/reinicios hasta
completar exactamente las 6 horas objetivo.

IMPORTANTE: todo el cálculo de tiempo se hace con datetimes generados en
Python usando America/Tijuana (ZoneInfo), NUNCA con NOW()/TIMESTAMPDIFF de
MySQL. El servidor MySQL gestionado corre en UTC por defecto, mientras que
el resto del proyecto (asignaciones, tickets, etc.) usa
datetime.now(ZoneInfo("America/Tijuana")). Si aquí se usara NOW() de MySQL,
`corriendo_desde` quedaría guardado en UTC pero el frontend lo interpreta
como hora local de Tijuana, haciendo que el timestamp parezca estar horas
en el futuro y el contador nunca avance (se queda en 00:00:00).
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from db import execute_read, execute_write

TZ = ZoneInfo("America/Tijuana")
UMBRAL_SEGUNDOS = 6 * 3600  # 6 horas


def iniciar(unidad: str):
    """
    Arranca o reanuda el conteo para una unidad. Si ya existe un registro
    pausado, retoma desde el tiempo acumulado (no lo reinicia). Si no existe
    fila, la crea.
    """
    ahora = datetime.now(TZ).replace(tzinfo=None)
    execute_write(
        """
        INSERT INTO corriendo_tracking (unidad, corriendo_desde)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            corriendo_desde = IF(corriendo_desde IS NULL, %s, corriendo_desde)
        """,
        (unidad, ahora, ahora)
    )


def pausar(unidad: str):
    """
    Pausa el conteo (por pausa manual o por finalizar la actividad antes de
    las 6 horas), sumando el tiempo transcurrido desde el último arranque al
    total acumulado. Deja corriendo_desde en NULL hasta el próximo iniciar().
    """
    ahora = datetime.now(TZ).replace(tzinfo=None)
    execute_write(
        """
        UPDATE corriendo_tracking
        SET segundos_acumulados = segundos_acumulados
            + IF(corriendo_desde IS NOT NULL, GREATEST(TIMESTAMPDIFF(SECOND, corriendo_desde, %s), 0), 0),
            corriendo_desde = NULL
        WHERE unidad = %s
        """,
        (ahora, unidad)
    )


def reiniciar(unidad: str):
    """Resetea el contador de una unidad a cero (p. ej. tras darle servicio)."""
    execute_write(
        """
        UPDATE corriendo_tracking
        SET segundos_acumulados = 0, corriendo_desde = NULL, alerta_6h_enviada = 0
        WHERE unidad = %s
        """,
        (unidad,)
    )


def obtener_todos():
    """
    Devuelve el tracking de todas las unidades con el total de segundos
    (acumulado + tiempo corriendo actual, si aplica) calculado contra la
    hora actual de Tijuana, consistente con cómo se guardó corriendo_desde.
    """
    ahora = datetime.now(TZ).replace(tzinfo=None)
    return execute_read(
        """
        SELECT unidad, segundos_acumulados, corriendo_desde, alerta_6h_enviada,
               segundos_acumulados
                 + IF(corriendo_desde IS NOT NULL, GREATEST(TIMESTAMPDIFF(SECOND, corriendo_desde, %s), 0), 0)
                 AS total_segundos
        FROM corriendo_tracking
        """,
        (ahora,)
    )


def obtener_pendientes_de_alerta():
    """
    Unidades actualmente corriendo que ya alcanzaron el umbral de 6h y aún
    no se les ha enviado la alerta.
    """
    ahora = datetime.now(TZ).replace(tzinfo=None)
    return execute_read(
        """
        SELECT unidad, segundos_acumulados, corriendo_desde,
               segundos_acumulados + TIMESTAMPDIFF(SECOND, corriendo_desde, %s) AS total_segundos
        FROM corriendo_tracking
        WHERE corriendo_desde IS NOT NULL
          AND alerta_6h_enviada = 0
          AND (segundos_acumulados + TIMESTAMPDIFF(SECOND, corriendo_desde, %s)) >= %s
        """,
        (ahora, ahora, UMBRAL_SEGUNDOS)
    )


def marcar_alerta_enviada(unidad: str):
    execute_write(
        "UPDATE corriendo_tracking SET alerta_6h_enviada=1 WHERE unidad=%s",
        (unidad,)
    )
