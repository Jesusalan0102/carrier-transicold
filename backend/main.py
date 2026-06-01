import os
import gc
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from routers.auth_router import router as auth_router
from routers.dashboard_router import router as dashboard_router
from routers.asignaciones_router import router as asignaciones_router
from routers.tickets_router import router as tickets_router
from routers.inventario_router import router as inventario_router
from routers.unidades_router import router as unidades_router
from routers.usuarios_router import router as usuarios_router
from routers.evidencias_router import router as evidencias_router
from routers.toma_valores_router import router as toma_valores_router
from routers.comentarios_router import router as comentarios_router
from routers.ws import router as ws_router
from routers.cluster_router import router as cluster_router
from routers.web_router import router as web_router
from db import init_db

from asistencia.routes import router as asistencia_api_router
from asistencia.horarios_routes import router as horarios_router


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


# Routers con /api/ ya en su prefijo propio
app.include_router(auth_router)
app.include_router(asignaciones_router)
app.include_router(tickets_router)
app.include_router(inventario_router)
app.include_router(unidades_router)
app.include_router(usuarios_router)
app.include_router(evidencias_router)
app.include_router(toma_valores_router)
app.include_router(comentarios_router)
app.include_router(cluster_router)
app.include_router(horarios_router)
app.include_router(ws_router)

# Routers sin /api/ — se les agrega aquí
app.include_router(dashboard_router,      prefix="/api")
app.include_router(asistencia_api_router, prefix="/api")

# Web router al final
app.include_router(web_router)
