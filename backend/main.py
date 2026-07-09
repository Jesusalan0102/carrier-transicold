from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(name)s]: %(message)s')

# ── Autenticación ────────────────────────────────────────────────────────────
from routers.auth_router import router as auth_router
from routers.auth_router import refresh_router

# ── Páginas web /app/* ────────────────────────────────────────────────────────
from routers.web_router import router as web_router

# ── Routers de API ────────────────────────────────────────────────────────────
from routers.dashboard_router   import router as dashboard_router
from routers.reporte_router     import router as reporte_router
from routers.tickets_router     import router as tickets_router
from routers.unidades_router    import router as unidades_router
from routers.usuarios_router    import router as usuarios_router
from routers.inventario_router  import router as inventario_router
from routers.asignaciones_router import router as asignaciones_router
from routers.evidencias_router  import router as evidencias_router
from routers.toma_valores_router import router as toma_valores_router
from routers.comentarios_router import router as comentarios_router
from routers.alarmas_router     import router as alarmas_router
from routers.schedule_router    import router as schedule_router
from routers.ws                 import router as ws_router
from routers.push_router        import router as push_router

# ── Asistencia / QR ──────────────────────────────────────────────────────────
from asistencia.routes          import router as asistencia_router
from asistencia.horarios_routes import router as horarios_router

# ── DB ───────────────────────────────────────────────────────────────────────
from db import init_db

app = FastAPI(
    title="Carrier Transicold API",
    version="2.1",
    description="Sistema Operativo Carrier Transicold — API REST"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registro de routers ───────────────────────────────────────────────────────
app.include_router(auth_router,          prefix="/api/auth",     tags=["auth"])
app.include_router(refresh_router,       prefix="/api/auth",     tags=["auth"])

# web_router primero (rutas /app/* no deben ceder a los de /api)
app.include_router(web_router)

app.include_router(dashboard_router)
app.include_router(reporte_router,       prefix="/api")

app.include_router(tickets_router)
app.include_router(unidades_router)
app.include_router(usuarios_router)
app.include_router(inventario_router)
app.include_router(asignaciones_router)
app.include_router(evidencias_router)
app.include_router(toma_valores_router)
app.include_router(comentarios_router)
app.include_router(alarmas_router)
app.include_router(schedule_router)
app.include_router(ws_router)
app.include_router(push_router)

app.include_router(asistencia_router,    prefix="/api")
app.include_router(horarios_router)

# ── Archivos estáticos (iconos, manifest, sw.js) ──────────────────────────────
import pathlib
_STATIC_DIR = pathlib.Path(__file__).parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# sw.js debe estar en la raíz para que el Service Worker controle todo /app/*
@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    sw_path = _STATIC_DIR / "sw.js"
    return FileResponse(str(sw_path), media_type="application/javascript")

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def root():
    return {"message": "API Carrier Transicold funcionando 🚀", "version": "2.1"}

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 9000)))
