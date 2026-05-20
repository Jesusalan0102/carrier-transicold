from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import bcrypt

router = APIRouter(prefix="/api/panel", tags=["panel"])

# ============================================================
# MODELOS SIMPLIFICADOS PARA EL PANEL HTML
# ============================================================

class PanelActividad(BaseModel):
    id: Optional[int] = None
    vehiculo: str
    tipo: str
    tecnico: str
    estado: str
    notas: Optional[str] = ""

class PanelUsuario(BaseModel):
    id: Optional[int] = None
    nombre: str
    email: str
    rol: str
    password: Optional[str] = ""

class PanelUnidad(BaseModel):
    id: Optional[int] = None
    placa: str
    modelo: str
    año: int
    estado: str


# ============================================================
# ACTIVIDADES (mapea asignaciones)
# ============================================================

@router.get("/actividades")
def get_actividades(current_user=Depends(verify_token)):
    """Obtiene actividades para el panel"""
    rows = execute_read("""
        SELECT a.id, a.unidad as vehiculo, a.actividad_id as tipo,
               a.tecnico, a.estado
        FROM asignaciones a
        ORDER BY a.id DESC
    """)
    
    for r in rows:
        comentarios = execute_read(
            "SELECT comentario FROM comentarios_actividades WHERE asignacion_id = %s ORDER BY created_at DESC LIMIT 1",
            (r["id"],)
        )
        r["notas"] = comentarios[0]["comentario"] if comentarios else ""
        
        estado_map = {
            "pendiente": "pendiente",
            "solicitado": "solicitado",
            "en_proceso": "pendiente",
            "completada": "completado",
            "cancelado": "cancelado"
        }
        r["estado"] = estado_map.get(r["estado"], r["estado"])
    
    return rows

@router.post("/actividades")
def create_actividad(act: PanelActividad, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    estado_bd = act.estado
    if estado_bd == "completado":
        estado_bd = "completada"
    
    execute_write("""
        INSERT INTO asignaciones (unidad, actividad_id, tecnico, estado, fecha_asignacion)
        VALUES (%s, %s, %s, %s, %s)
    """, (act.vehiculo, act.tipo, act.tecnico, estado_bd, datetime.now()))
    
    new_id = execute_read("SELECT LAST_INSERT_ID() as id")[0]["id"]
    
    if act.notas:
        execute_write("""
            INSERT INTO comentarios_actividades (asignacion_id, tecnico, comentario, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (new_id, act.tecnico, act.notas))
    
    return {"mensaje": "Actividad creada", "id": new_id}

@router.put("/actividades/{act_id}")
def update_actividad(act_id: int, act: PanelActividad, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    estado_bd = act.estado
    if estado_bd == "completado":
        estado_bd = "completada"
    
    execute_write("""
        UPDATE asignaciones 
        SET unidad = %s, actividad_id = %s, tecnico = %s, estado = %s
        WHERE id = %s
    """, (act.vehiculo, act.tipo, act.tecnico, estado_bd, act_id))
    
    if act.notas:
        execute_write("DELETE FROM comentarios_actividades WHERE asignacion_id = %s", (act_id,))
        execute_write("""
            INSERT INTO comentarios_actividades (asignacion_id, tecnico, comentario, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (act_id, act.tecnico, act.notas))
    
    return {"mensaje": "Actividad actualizada"}

@router.delete("/actividades/{act_id}")
def delete_actividad(act_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    execute_write("DELETE FROM comentarios_actividades WHERE asignacion_id = %s", (act_id,))
    execute_write("DELETE FROM asignaciones WHERE id = %s", (act_id,))
    return {"mensaje": "Eliminado"}


# ============================================================
# USUARIOS (mapea users)
# ============================================================

@router.get("/usuarios")
def get_usuarios(current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    rows = execute_read("SELECT id, username as nombre, role as rol FROM users ORDER BY id")
    
    rol_map = {"admin": "administrador", "tecnico": "tecnico", "visor": "operador"}
    for r in rows:
        r["email"] = f"{r['nombre']}@transicold.mx"
        r["rol"] = rol_map.get(r["rol"], r["rol"])
    
    return rows

@router.post("/usuarios")
def create_usuario(usr: PanelUsuario, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    rol_bd = usr.rol
    if rol_bd == "administrador":
        rol_bd = "admin"
    elif rol_bd == "operador":
        rol_bd = "visor"
    
    if rol_bd not in ("admin", "tecnico", "visor"):
        raise HTTPException(status_code=400, detail=f"Rol inválido")
    
    existing = execute_read("SELECT id FROM users WHERE username = %s", (usr.nombre,))
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    hashed = bcrypt.hashpw(usr.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    execute_write("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                  (usr.nombre, hashed, rol_bd))
    
    return {"mensaje": "Usuario creado"}

@router.put("/usuarios/{user_id}")
def update_usuario(user_id: int, usr: PanelUsuario, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    rol_bd = usr.rol
    if rol_bd == "administrador":
        rol_bd = "admin"
    elif rol_bd == "operador":
        rol_bd = "visor"
    
    execute_write("UPDATE users SET username = %s, role = %s WHERE id = %s",
                  (usr.nombre, rol_bd, user_id))
    
    if usr.password and len(usr.password.strip()) >= 4:
        hashed = bcrypt.hashpw(usr.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        execute_write("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
    
    return {"mensaje": "Usuario actualizado"}

@router.delete("/usuarios/{user_id}")
def delete_usuario(user_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    if user_id == current_user.get("user_id"):
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    
    execute_write("DELETE FROM users WHERE id = %s", (user_id,))
    return {"mensaje": "Usuario eliminado"}


# ============================================================
# UNIDADES (mapea unidades)
# ============================================================

@router.get("/unidades")
def get_unidades(current_user=Depends(verify_token)):
    rows = execute_read("""
        SELECT id, unit_number as placa,
               COALESCE(reefer_model, 'No especificado') as modelo,
               COALESCE(YEAR(fecha_registro), 2020) as año,
               CASE WHEN activo = 1 THEN 'activo' ELSE 'inactivo' END as estado
        FROM unidades
        ORDER BY id
    """)
    return rows

@router.post("/unidades")
def create_unidad(uni: PanelUnidad, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    activo = 1 if uni.estado == "activo" else 0
    execute_write("INSERT INTO unidades (unit_number, reefer_model, activo) VALUES (%s, %s, %s)",
                  (uni.placa, uni.modelo, activo))
    return {"mensaje": "Unidad creada"}

@router.put("/unidades/{uni_id}")
def update_unidad(uni_id: int, uni: PanelUnidad, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    activo = 1 if uni.estado == "activo" else 0
    execute_write("UPDATE unidades SET unit_number = %s, reefer_model = %s, activo = %s WHERE id = %s",
                  (uni.placa, uni.modelo, activo, uni_id))
    return {"mensaje": "Unidad actualizada"}

@router.delete("/unidades/{uni_id}")
def delete_unidad(uni_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    unidad = execute_read("SELECT unit_number FROM unidades WHERE id = %s", (uni_id,))
    if unidad:
        unit_number = unidad[0]["unit_number"]
        execute_write("DELETE FROM evidencias WHERE unit_number = %s", (unit_number,))
        execute_write("DELETE FROM asignaciones WHERE unidad = %s", (unit_number,))
    execute_write("DELETE FROM unidades WHERE id = %s", (uni_id,))
    return {"mensaje": "Unidad eliminada"}


# ============================================================
# SQL DIRECTO (solo SELECT)
# ============================================================

@router.post("/sql")
def ejecutar_sql(data: Dict[str, Any], current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    query = data.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Consulta vacía")
    
    if not query.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Solo consultas SELECT permitidas")
    
    try:
        results = execute_read(query)
        return {
            "results": results, 
            "row_count": len(results), 
            "columns": list(results[0].keys()) if results else []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
