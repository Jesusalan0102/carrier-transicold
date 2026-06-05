from fastapi import APIRouter
from db import execute_write, execute_read

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.delete("/reset-all-data")
def reset_all_data():
    """Borra todos los datos excepto usuarios."""
    tablas = [
        "toma_valores_datos",
        "comentarios_actividades",
        "evidencias",
        "asignaciones",
        "tickets",
        "unidades",
        "inventario_columnas",
        "toma_valores_campos",
        "registros_asistencia",
        "horarios",
        "configuracion_geocerca",
    ]
    results = {}
    for tabla in tablas:
        try:
            affected = execute_write(f"DELETE FROM `{tabla}`")
            results[tabla] = f"✅ {affected} filas borradas"
        except Exception as e:
            results[tabla] = f"⚠️ {e}"

    # Intentar también una tabla dinámica de inventario si existe
    try:
        execute_write("DELETE FROM `inventario_datos`")
        results["inventario_datos"] = "✅ borrada"
    except:
        results["inventario_datos"] = "no existe (ok)"

    usuarios = execute_read("SELECT id, username, role FROM users")
    return {
        "status": "limpieza completada",
        "tablas": results,
        "usuarios_conservados": usuarios
    }
