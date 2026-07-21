# backend/corriendo_tracking.py
"""
Lógica del contador acumulado de horas 'Corriendo' por unidad.

Vive en su propia tabla (corriendo_tracking), independiente de `asignaciones`,
para poder acumular tiempo a través de múltiples pausas/reinicios hasta
completar exactamente las 6 horas objetivo.

Todo el cálculo de tiempo transcurrido se hace del lado de MySQL (NOW(),
TIMESTAMPDIFF) para evitar errores de zona horaria al comparar datetimes
naive/aware en Python.
"""
from db import execute_read, execute_write

UMBRAL_SEGUNDOS = 6 * 3600  # 6 horas


def iniciar(unidad: str):
    """
    Arranca o reanuda el conteo para una unidad. Si ya existe un registro
    pausado, retoma desde el tiempo acumulado (no lo reinicia). Si no existe
    fila, la crea.
    """
    execute_write(
        """
        INSERT INTO corriendo_tracking (unidad, corriendo_desde)
        VALUES (%s, NOW())
        ON DUPLICATE KEY UPDATE
            corriendo_desde = IF(corriendo_desde IS NULL, NOW(), corriendo_desde)
        """,
        (unidad,)
    )


def pausar(unidad: str):
    """
    Pausa el conteo (por pausa manual o por finalizar la actividad antes de
    las 6 horas), sumando el tiempo transcurrido desde el último arranque al
    total acumulado. Deja corriendo_desde en NULL hasta el próximo iniciar().
    """
    execute_write(
        """
        UPDATE corriendo_tracking
        SET segundos_acumulados = segundos_acumulados
            + IF(corriendo_desde IS NOT NULL, GREATEST(TIMESTAMPDIFF(SECOND, corriendo_desde, NOW()), 0), 0),
            corriendo_desde = NULL
        WHERE unidad = %s
        """,
        (unidad,)
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
    (acumulado + tiempo corriendo actual, si aplica) calculado en SQL.
    """
    return execute_read(
        """
        SELECT unidad, segundos_acumulados, corriendo_desde, alerta_6h_enviada,
               segundos_acumulados
                 + IF(corriendo_desde IS NOT NULL, GREATEST(TIMESTAMPDIFF(SECOND, corriendo_desde, NOW()), 0), 0)
                 AS total_segundos
        FROM corriendo_tracking
        """
    )


def obtener_pendientes_de_alerta():
    """
    Unidades actualmente corriendo que ya alcanzaron el umbral de 6h y aún
    no se les ha enviado la alerta.
    """
    return execute_read(
        """
        SELECT unidad, segundos_acumulados, corriendo_desde,
               segundos_acumulados + TIMESTAMPDIFF(SECOND, corriendo_desde, NOW()) AS total_segundos
        FROM corriendo_tracking
        WHERE corriendo_desde IS NOT NULL
          AND alerta_6h_enviada = 0
          AND (segundos_acumulados + TIMESTAMPDIFF(SECOND, corriendo_desde, NOW())) >= %s
        """,
        (UMBRAL_SEGUNDOS,)
    )


def marcar_alerta_enviada(unidad: str):
    execute_write(
        "UPDATE corriendo_tracking SET alerta_6h_enviada=1 WHERE unidad=%s",
        (unidad,)
    )
