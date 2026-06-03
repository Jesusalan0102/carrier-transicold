from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date, timedelta
import pymysql
import os

router = APIRouter()

def get_db_connection():
    """Establece la conexión con la base de datos TiDB / MySQL utilizando variables de entorno."""
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "carrier_db"),
            port=int(os.getenv("DB_PORT", 3306)),
            autocommit=True
        )
        return connection
    except Exception as e:
        print(f"Error crítico de conexión a la base de datos: {e}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# 1. ENDPOINT: OBTENER LOGS DE ASISTENCIA INDIVIDUALES
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/registros")
def obtener_registros(fecha: str = Query(None)):
    """Retorna el historial lineal de marcados filtrado opcionalmente por fecha."""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if fecha:
                query = """
                    SELECT id, empleado_id, nombre, fecha, hora_checkin, tipo_marcado, latitud, longitud 
                    FROM registros_asistencia 
                    WHERE DATE(fecha) = %s 
                    ORDER BY fecha DESC, hora_checkin DESC
                """
                cursor.execute(query, (fecha,))
            else:
                query = """
                    SELECT id, empleado_id, nombre, fecha, hora_checkin, tipo_marcado, latitud, longitud 
                    FROM registros_asistencia 
                    ORDER BY fecha DESC, hora_checkin DESC
                """
                cursor.execute(query)

            registros = cursor.fetchall()
            result = []
            
            for r in registros:
                row = dict(r)
                
                # Sanitización preventiva campo por campo
                for key, value in row.items():
                    if value is None or str(value).strip().lower() == "null" or str(value).strip() == "":
                        row[key] = "—"
                
                # Formateo seguro de objetos datetime/date a texto nativo
                if 'fecha' in row and isinstance(r.get('fecha'), (date, datetime)):
                    row['fecha'] = r['fecha'].strftime('%Y-%m-%d')
                
                if 'hora_checkin' in row and r.get('hora_checkin') and row['hora_checkin'] != "—":
                    row['hora_checkin'] = str(r['hora_checkin'])[:8]
                
                result.append(row)
                
            return result
            
    except Exception as e:
        print(f"Error en obtener_registros: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# ──────────────────────────────────────────────────────────────────────────────
# 2. ENDPOINT: DASHBOARD MATRIZ SEMANAL (ELIMINA EL BUG "✓ null")
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/dashboard/semanal")
def obtener_dashboard_semanal(fecha_inicio: str = Query(None)):
    """
    Genera la estructura matricial de la semana para los técnicos.
    Cualquier ausencia o celda vacía se envía como '—' para evitar que el frontend pinte un badge 'null'.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
        
    try:
        # Si no se envía fecha, calculamos el lunes de la semana actual por defecto
        if datetime:
            if fecha_inicio:
                lunes = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            else:
                hoy = date.today()
                lunes = hoy - timedelta(days=hoy.weekday())
        
        # Generamos el arreglo de los 7 días de la semana en formato YYYY-MM-DD
        dias_semana = [(lunes + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Obtenemos el catálogo único de usuarios activos para iterar la matriz
            cursor.execute("SELECT id, name FROM users ORDER BY name ASC")
            usuarios = cursor.fetchall()
            
            # 2. Obtenemos todos los marcados válidos de la semana en cuestión
            query_asistencia = """
                SELECT nombre, DATE_FORMAT(fecha, '%%Y-%%m-%%d') as fecha_texto, hora_checkin, tipo_marcado 
                FROM registros_asistencia 
                WHERE fecha BETWEEN %s AND %s
            """
            cursor.execute(query_asistencia, (dias_semana[0], dias_semana[6]))
            asistencias = cursor.fetchall()
            
        # Agrupamos las asistencias en un diccionario mapeado por (nombre, fecha)
        mapa_asistencia = {}
        for asis in asistencias:
            llave = (asis['nombre'], asis['fecha_texto'])
            if llave not in mapa_asistencia:
                mapa_asistencia[llave] = []
            mapa_asistencia[llave].append(asis)
            
        matrix_response = []
        
        # 3. Construcción de la matriz fila por fila (Usuario por Usuario)
        for u in usuarios:
            nombre_usuario = u['name']
            fila = {
                "usuario": nombre_usuario,
                "detalles": u
            }
            
            # Evaluamos cada uno de los 7 días para este usuario específico
            for dia in dias_semana:
                llave_busqueda = (nombre_usuario, dia)
                
                if llave_busqueda in mapa_asistencia:
                    # El técnico asistió. Extraemos, por ejemplo, el primer marcado del día (Entrada)
                    eventos_dia = mapa_asistencia[llave_busqueda]
                    marcado_entrada = next((e for e in eventos_dia if e['tipo_marcado'].lower() == 'entrada'), eventos_dia[0])
                    
                    # Extraemos la hora formateada
                    hora_cruda = marcado_entrada.get('hora_checkin')
                    valor_celda = str(hora_cruda)[:5] if hora_cruda else "OK"
                else:
                    # El técnico no tiene registros ese día. Enviamos un guion plano.
                    valor_celda = "—"
                
                # BLINDAJE ABSOLUTO: Si por algún motivo el valor resultó nulo o es un string corrupto, lo forzamos a guion
                if valor_celda is None or str(valor_celda).strip().lower() == "null" or str(valor_celda).strip() == "":
                    valor_celda = "—"
                    
                # Guardamos el resultado del día en la estructura dinámica de la fila
                fila[dia] = valor_celda
                
            matrix_response.append(fila)
            
        return {
            "rango_semana": {"desde": dias_semana[0], "hasta": dias_semana[6]},
            "dias_columnas": dias_semana,
            "data": matrix_response
        }
        
    except Exception as e:
        print(f"Error en obtener_dashboard_semanal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()
