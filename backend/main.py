import os
import gc
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from routers.auth_router import router as auth_router           # prefijo propio: /api/auth
from routers.dashboard_router import router as dashboard_router # prefijo propio: /dashboard  → necesita /api
from routers.asignaciones_router import router as asignaciones_router  # /api/asignaciones
from routers.tickets_router import router as tickets_router     # /api/tickets
from routers.inventario_router import router as inventario_router  # /api/inventario
from routers.unidades_router import router as unidades_router   # /api/unidades
from routers.usuarios_router import router as usuarios_router   # /api/usuarios
from routers.evidencias_router import router as evidencias_router  # /api/evidencias
from routers.toma_valores_router import router as toma_valores_router  # /api/toma-valores
from routers.comentarios_router import router as comentarios_router  # /api/comentarios
from routers.ws import router as ws_router                      # /ws (sin prefijo)
from routers.cluster_router import router as cluster_router     # /api/cluster
from routers.web_router import router as web_router             # páginas HTML /app/...
from db import init_db

from asistencia.routes import router as asistencia_api_router   # prefijo propio: /asistencia → necesita /api
from asistencia.horarios_routes import router as horarios_router # /api/horarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ [STARTUP] Inicializando conexiones de infraestructura...")
    try:
        init_db()
        print("✅ [STARTUP] Base de datos TiDB conectada con éxito.")
    except Exception as db_err:
        print(f"❌ [CRITICAL] Falló la inicialización de la base de datos: {db_err}")
    gc.collect()
    print("🧹 [RAM] Memoria residual de compilación liberada correctamente.")
    yield
    print("🛑 [SHUTDOWN] Cerrando recursos...")


app = FastAPI(
    title="Carrier Transicold API",
    version="2.0",
    description="Sistema Operativo Carrier Transicold — API REST",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    if not os.path.exists(path):
        return Response(status_code=204)
    return FileResponse(path)


@app.get("/")
def root():
    return {"mensaje": "API Carrier Transicold operativa", "docs": "/docs"}


@app.get("/test-onedrive")
def test_onedrive():
    vars_presentes = {
        "MS_CLIENT_ID":     bool(os.getenv("MS_CLIENT_ID")),
        "MS_CLIENT_SECRET": bool(os.getenv("MS_CLIENT_SECRET")),
        "MS_TENANT_ID":     bool(os.getenv("MS_TENANT_ID")),
        "MS_USER_EMAIL":    os.getenv("MS_USER_EMAIL", "NO DEFINIDO"),
    }
    try:
        from onedrive_service import _get_token
        token = _get_token()
        return {
            "status": "OK ✅ — Conexión con OneDrive exitosa",
            "variables": vars_presentes,
            "token_preview": token[:20] + "..." if token else "None"
        }
    except Exception as e:
        return {"status": "ERROR ❌", "variables": vars_presentes, "detalle": str(e)}


@app.get("/auth/onedrive/callback")
def onedrive_callback(code: str = None, error: str = None):
    if error:
        return {"error": error}
    if not code:
        return {"error": "No se recibió código"}
    import requests
    resp = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "client_id":     "dc1c0d4f-0f48-44db-9fde-a63178fb8ab0",
            "client_secret": os.getenv("MS_CLIENT_SECRET_PERSONAL", ""),
            "code":          code,
            "redirect_uri":  "https://carrier-transicold.onrender.com/auth/onedrive/callback",
            "grant_type":    "authorization_code",
            "scope":         "https://graph.microsoft.com/Files.ReadWrite offline_access User.Read",
        }
    )
    data = resp.json()
    if "refresh_token" in data:
        return {
            "status": "✅ ÉXITO — Copia este refresh_token y guárdalo en Render como MS_REFRESH_TOKEN",
            "refresh_token": data["refresh_token"],
            "access_token_preview": data.get("access_token", "")[:30] + "..."
        }
    return {"error": data}


# ── Routers que YA tienen /api/ en su propio prefijo — se registran SIN prefix extra
app.include_router(auth_router)           # → /api/auth/...
app.include_router(asignaciones_router)   # → /api/asignaciones/...
app.include_router(tickets_router)        # → /api/tickets/...
app.include_router(inventario_router)     # → /api/inventario/...
app.include_router(unidades_router)       # → /api/unidades/...
app.include_router(usuarios_router)       # → /api/usuarios/...
app.include_router(evidencias_router)     # → /api/evidencias/...
app.include_router(toma_valores_router)   # → /api/toma-valores/...
app.include_router(comentarios_router)    # → /api/comentarios/...
app.include_router(cluster_router)        # → /api/cluster/...
app.include_router(horarios_router)       # → /api/horarios/...
app.include_router(ws_router)             # → /ws

# ── Routers que NO tienen /api/ en su propio prefijo — se les agrega aquí
app.include_router(dashboard_router,      prefix="/api")   # → /api/dashboard/...
app.include_router(asistencia_api_router, prefix="/api")   # → /api/asistencia/...

# ── Web router al final (sirve el HTML de /app/...)
app.include_router(web_router)
