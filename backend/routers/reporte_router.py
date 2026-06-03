import io
import pymysql
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from db import get_db_connection
from auth import verify_token

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes Maestros"]
)

@router.get("/exportar-maestro")
def exportar_sistema_completo(current_user=Depends(verify_token)):
    """
    Exporta TODAS las tablas del sistema de Carrier Transicold a un único archivo Excel (.xlsx).
    Cada tabla de la base de datos se convierte automáticamente en una pestaña diferente.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
        
    try:
        # Crear libro de trabajo de openpyxl
        wb = Workbook()
        # Eliminar la pestaña por defecto que crea openpyxl
        default_sheet = wb.active
        wb.remove(default_sheet)
        
        # Lista completa de las 22 tablas detectadas en tu base de datos carrier_db
        tablas_a_exportar = [
            "actividades", "asignaciones", "asistencia", "asistencia_config", 
            "asistencia_registros", "comentarios_actividades", "config_sistema", 
            "configuracion_geocerca", "evidencias", "horarios", "inventario", 
            "inventario_columnas", "inventario_data", "inventarios", "lotes", 
            "registros_asistencia", "tickets", "toma_valores_campos", 
            "toma_valores_datos", "unidades", "users", "valores_registrados"
        ]
        
        # Estilos visuales para los encabezados de las tablas en Excel
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid") # Azul corporativo
        alignment_center = Alignment(horizontal="center", vertical="center")
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            for nombre_tabla in tablas_a_exportar:
                # 1. Ejecutar query para obtener toda la info de la tabla
                cursor.execute(f"SELECT * FROM `{nombre_tabla}`")
                filas = cursor.fetchall()
                
                # Crear una nueva pestaña con el nombre de la tabla (máx 31 caracteres permitido por Excel)
                ws = wb.create_sheet(title=nombre_tabla[:31])
                
                if len(filas) > 0:
                    # 2. Extraer los nombres de las columnas a partir del primer registro
                    columnas = list(filas[0].keys())
                    
                    # Escribir encabezados
                    ws.append(columnas)
                    
                    # Dar estilo a la fila de encabezados
                    for col_num in range(1, len(columnas) + 1):
                        cell = ws.cell(row=1, column=col_num)
                        cell.font = font_header
                        cell.fill = fill_header
                        cell.alignment = alignment_center
                    
                    # 3. Escribir los datos de cada registro
                    for fila in filas:
                        valores_fila = []
                        for col in columnas:
                            valor = fila[col]
                            # Si hay datos de fotos, binarios largos o bytes base64, los omitimos o truncamos
                            if isinstance(valor, (bytes, bytearray)):
                                valor = "[Archivo Binario / Foto]"
                            elif valor is not None:
                                valor = str(valor)
                            valores_fila.append(valor)
                        ws.append(valores_fila)
                else:
                    # Si la tabla está vacía, solo dejamos una nota en la pestaña
                    ws.cell(row=1, column=1, value="Esta tabla no contiene registros actualmente.").font = Font(italic=True)
                
                # Auto-ajustar el ancho de las columnas de manera dinámica según el contenido
                for col in ws.columns:
                    max_len = 0
                    col_letter = get_column_letter(col[0].column)
                    for cell in col:
                        if cell.value:
                            max_len = max(max_len, len(str(cell.value)))
                    ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
        # Guardar todo el archivo Excel generado en un búfer de memoria (BytesIO)
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        # Enviar el archivo binario directamente al navegador del cliente como descarga (.xlsx)
        filename = "Reporte_Maestro_Carrier_Transicold.xlsx"
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        print(f"Error al generar reporte maestro: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
    finally:
        connection.close()
