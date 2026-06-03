from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# ── Routers de autenticación y páginas web ──────────────────────────────────
from routers.auth_router import router as auth_router
from routers.web_router import router as web_router          # Todas las rutas /app/*

# FIX Bug 5: refresh_router vive dentro de auth.py (no es un archivo separado)
from auth import refresh_router

# ── Routers de API (cada uno ya trae su propio prefix /api/...) ─────────────
from routers.dashboard_router import router as dashboard_router       # /api/dashboard/...
from routers.reporte_router import router as reporte_router           # /api/reportes/exportar-maestro (22 tablas)
from routers.tickets_router import router as tickets_router           # /api/tickets/...
from routers.unidades_router import router as unidades_router         # /api/unidades/...
from routers.usuarios_router import router as usuarios_router         # /api/usuarios/...
from routers.inventario_router import router as inventario_router     # /api/inventario/...
from routers.asignaciones_router import router as asignaciones_router # /api/asignaciones/...
from routers.evidencias_router import router as evidencias_router     # /api/evidencias/...
from routers.toma_valores_router import router as toma_valores_router # /api/toma-valores/...
from routers.comentarios_router import router as comentarios_router   # /api/comentarios/...
from routers.cluster_router import router as cluster_router           # /api/cluster/...

# ── FIX Bug 1: Asistencia router (prefix /api para que coincida con el frontend) ──
from asistencia.routes import router as asistencia_router             # /api/asistencia/...

# ── FIX Bug 2: Horarios router (nunca había sido registrado) ──────────────────
from asistencia.horarios_routes import router as horarios_router      # /api/horarios/...

# ── Init DB ─────────────────────────────────────────────────────────────────
from db import init_db

app = FastAPI(title="Carrier Transicold API")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza por tu dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registro de routers ───────────────────────────────────────────────────────

# auth_router no tiene prefix propio → se le asigna aquí
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# FIX Bug 5: endpoint POST /api/auth/refresh para renovar tokens sin re-login
app.include_router(refresh_router, prefix="/api/auth", tags=["auth"])

# web_router no tiene prefix propio → sirve las páginas /app/* directamente
# IMPORTANTE: web_router debe ir ANTES que los routers de API para que las
# rutas de página no colisionen con las de API.
app.include_router(web_router)

# dashboard_router ya tiene prefix="/dashboard" → con prefix /api queda en /api/dashboard/...
app.include_router(dashboard_router, prefix="/api")

# FIX Bug 3: reporte_router ya tiene prefix="/reportes".
# Se le agrega prefix="/api" para consistencia → /api/reportes/exportar-maestro
# El frontend también se actualiza para llamar esta URL (ver parche frontend_patches.js).
app.include_router(reporte_router, prefix="/api")

# Todos los siguientes ya traen prefix="/api/..." definido internamente
app.include_router(tickets_router)
app.include_router(unidades_router)
app.include_router(usuarios_router)
app.include_router(inventario_router)
app.include_router(asignaciones_router)
app.include_router(evidencias_router)
app.include_router(toma_valores_router)
app.include_router(comentarios_router)
app.include_router(cluster_router)

# FIX Bug 1: asistencia_router tiene prefix="/asistencia"; con prefix "/api"
# queda en /api/asistencia/... → coincide con todas las llamadas del frontend.
app.include_router(asistencia_router, prefix="/api")

# FIX Bug 2: horarios_router ya tiene prefix="/api/horarios" definido internamente
# → queda en /api/horarios/... sin necesitar prefix extra aquí.
app.include_router(horarios_router)

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "API Carrier Transicold funcionando 🚀"}

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 9000)))
