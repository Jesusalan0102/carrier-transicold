import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import pymysql
import pymysql.cursors
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

# Inicialización del enrutador de FastAPI
router = APIRouter()

def get_db_connection():
    """
    Establece y retorna una conexión limpia a la base de datos TiDB / MySQL
    utilizando las variables de entorno inyectadas en Clever Cloud.
    """
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "carrier_db"),
            port=int(os.getenv("DB_PORT", 3306)),
            autocommit=True,  # Crucial para evitar bloqueos de hilos en consultas concurrentes
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"❌ [DATABASE ERROR] No se pudo conectar a la base de datos: {e}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# 0. ENDPOINT DE VERIFICACIÓN DE ESTADO (HEALTH CHECK)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/")
def health_check():
    """
    Endpoint requerido por los balanceadores de carga de Clever Cloud (GET /).
    Garantiza que el contenedor responda con HTTP 200 OK de manera constante.
    """
    return {"status": "online", "environment": "production", "service": "carrier-backend"}

# ──────────────────────────────────────────────────────────────────────────────
# 1. ENDPOINT: OBTENER TODOS LOS LOGS DE ASISTENCIA (HISTORIAL LINEAL)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/registros")
def obtener_registros(fecha: Optional[str] = Query(None, description="Filtrar por fecha en formato YYYY-MM-DD")):
    """
    Retorna la lista completa y plana de marcados históricos individuales.
    Filtra opcionalmente por un día específico si el parámetro viene provisto.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="No hay conexión disponible con el servidor de base de datos"
        )
    
    try:
        with connection.cursor() as cursor:
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
            resultado_limpio = []
            
            for registro in registros:
                fila = dict(registro)
                
                # Saneamiento anti-null/vacíos celda por celda
                for columna, valor in fila.items():
                    if valor is None or str(valor).strip().lower() == "null" or str(valor).strip() == "":
                        fila[columna] = "—"
                
                # Conversión segura y serialización de objetos tipo Date de Python
                if 'fecha' in fila and isinstance(registro.get('fecha'), (date, datetime)):
                    fila['fecha'] = registro['fecha'].strftime('%Y-%m-%d')
                
                # Conversión segura de objetos tipo Time/Timedelta a String legible de 8 caracteres (HH:MM:SS)
                if 'hora_checkin' in fila and registro.get('hora_checkin') and fila['hora_checkin'] != "—":
                    fila['hora_checkin'] = str(registro['hora_checkin'])[:8]
                
                resultado_limpio.append(fila)
                
            return resultado_limpio
            
    except Exception as e:
        print(f"❌ [ERROR EN /registros]: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()

# ──────────────────────────────────────────────────────────────────────────────
# 2. ENDPOINT: MATRIZ DEL DASHBOARD SEMANAL (RESUELVE EL BUG DE LOS BADGES VERDES)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/dashboard/semanal")
def obtener_dashboard_semanal(fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio de la semana YYYY-MM-DD")):
    """
    Construye la matriz semanal agrupada por usuario y día de la semana.
    Si un usuario no tiene asistencia un día, se inyecta un guion plano '—' explícito.
    Evita que el frontend reciba texto 'null' y dibuje botones de asistencia verdes erróneos.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="No hay conexión disponible con el servidor de base de datos"
        )
        
    try:
        # Calcular el rango de la semana (Lunes a Domingo)
        if fecha_inicio:
            try:
                lunes_fecha = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="El formato de fecha_inicio debe ser YYYY-MM-DD")
        else:
            hoy = date.today()
            lunes_fecha = hoy - timedelta(days=hoy.weekday())
        
        # Array con las 7 fechas de la semana en formato texto YYYY-MM-DD
        lista_dias = [(lunes_fecha + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        
        with connection.cursor() as cursor:
            # 1. Traer todos los usuarios del catálogo de la empresa
            cursor.execute("SELECT id, name FROM users ORDER BY name ASC")
            usuarios_sistema = cursor.fetchall()
            
            # 2. Consultar todos los marcados que caen en este rango semanal
            query_marcados = """
                SELECT nombre, DATE_FORMAT(fecha, '%%Y-%%m-%%d') as fecha_formato, hora_checkin, tipo_marcado 
                FROM registros_asistencia 
                WHERE fecha BETWEEN %s AND %s
            """
            cursor.execute(query_marcados, (lista_dias[0], lista_dias[6]))
            marcados_semana = cursor.fetchall()
            
        # Agrupar los marcados de asistencia indexándolos por una tupla (nombre_empleado, fecha_dia)
        diccionario_asistencias = {}
        for marcado in marcados_semana:
            clave_compuesta = (marcado['nombre'], marcado['fecha_formato'])
            if clave_compuesta not in diccionario_asistencias:
                diccionario_asistencias[clave_compuesta] = []
            diccionario_asistencias[clave_compuesta].append(marcado)
            
        matriz_final = []
        
        # 3. Construcción iterativa renglón por renglón (Usuario por Usuario)
        for usuario in usuarios_sistema:
            nombre_tecnico = usuario['name']
            fila_usuario = {
                "usuario": nombre_tecnico,
                "user_id": usuario['id']
            }
            
            # Recorrer cada uno de los 7 días para verificar si asistió o no
            for dia in lista_dias:
                clave_busqueda = (nombre_tecnico, dia)
                
                if clave_busqueda in diccionario_asistencias:
                    eventos_del_dia = diccionario_asistencias[clave_busqueda]
                    
                    # Buscamos prioritariamente el registro marcado como 'Entrada'
                    marcado_principal = next(
                        (evento for evento in eventos_del_dia if evento['tipo_marcado'].lower() == 'entrada'), 
                        eventos_del_dia[0]
                    )
                    
                    hora_cruda = marcado_principal.get('hora_checkin')
                    if hora_cruda:
                        # Formatear la hora a HH:MM de forma segura
                        valor_celda = str(hora_cruda)[:5]
                    else:
                        valor_celda = "Asistió"
                else:
                    # Si no hay registros en la BD para este técnico y este día, enviamos guion estricto
                    valor_celda = "—"
                
                # FILTRO DE BLINDAJE CRÍTICO:
                # Si por alguna anomalía previa el valor_celda es None, vacío o el string "null",
                # lo destruimos y forzamos a guion limpio para desarmar el badge verde del frontend.
                if valor_celda is None or str(valor_celda).strip().lower() == "null" or str(valor_celda).strip() == "":
                    valor_celda = "—"
                    
                # Añadir la columna del día a la fila del usuario
                fila_usuario[dia] = valor_celda
                
            matriz_final.append(fila_usuario)
            
        return {
            "rango": {
                "lunes_inicio": lista_dias[0], 
                "domingo_fin": lista_dias[6]
            },
            "columnas_fecha": lista_dias,
            "rows": matriz_final
        }
        
    except Exception as e:
        print(f"❌ [ERROR EN /dashboard/semanal]: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()
