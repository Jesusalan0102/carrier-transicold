from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(name)s]: %(message)s')
logger = logging.getLogger(__name__)

# ── Sentry (monitoreo de errores) ─────────────────────────────────────────────
# Se activa solo si existe SENTRY_DSN en el entorno; en local sin la variable
# simplemente no hace nada (no truena, no manda datos a ningún lado).
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        release=os.getenv("SENTRY_RELEASE"),  # opcional: p.ej. el SHA del commit
        # % de requests para las que se guarda traza de performance.
        # 0.2 = 20% es un punto de partida razonable para no gastar cuota gratis
        # de un proyecto de este tamaño; se puede subir/bajar desde el .env.
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
        send_default_pii=False,  # no mandar datos personales de usuarios por defecto
    )
    logger.info("Sentry inicializado (environment=%s)", os.getenv("SENTRY_ENVIRONMENT", "production"))
else:
    sentry_sdk = None
    logger.info("SENTRY_DSN no configurado — monitoreo de errores desactivado")

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
from routers.pdi_router         import router as pdi_router
from routers.comentarios_router import router as comentarios_router
from routers.alarmas_router     import router as alarmas_router
from routers.juegos_router      import router as juegos_router
from routers.schedule_router    import router as schedule_router
from routers.ws                 import router as ws_router
from routers.push_router        import router as push_router
from routers.search_router      import router as search_router

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

# ── Manejador global de errores ───────────────────────────────────────────────
# Sin esto, cualquier excepción no controlada (p.ej. la BD rechaza un INSERT
# por un tipo de dato/ENUM no actualizado) regresa el 500 de texto plano de
# Starlette -- el frontend hace res.json() sobre eso y truena con un
# "Unexpected token... is not valid JSON" que no dice nada del error real.
# Con esto, cualquier crash no controlado sigue devolviendo JSON, así se
# puede leer el mensaje real en la consola del navegador en vez de adivinar.
@app.exception_handler(Exception)
async def manejador_global_de_errores(request: Request, exc: Exception):
    logger.error(f"Error no controlado en {request.method} {request.url.path}: {exc}", exc_info=True)
    # Como este handler intercepta la excepción antes de que llegue al
    # middleware ASGI, la captura automática de Sentry nunca se dispara sola;
    # hay que mandarle el error explícitamente para que aparezca en el dashboard.
    if sentry_sdk is not None:
        with sentry_sdk.push_scope() as scope:
            scope.set_context("request", {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
            })
            sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno del servidor: {exc}"}
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
app.include_router(pdi_router)
app.include_router(comentarios_router)
app.include_router(alarmas_router)
app.include_router(juegos_router)
app.include_router(schedule_router)
app.include_router(ws_router)
app.include_router(push_router)
app.include_router(search_router)

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
    import asyncio
    from routers.ws import monitor_corriendo_6h
    from reportes_semanales import programador_reporte_semanal
    asyncio.create_task(monitor_corriendo_6h())
    asyncio.create_task(programador_reporte_semanal())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 9000)))
