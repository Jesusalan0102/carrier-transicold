from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from db import init_db
from routers.cluster_router import router as cluster_router
from routers.web_router import router as web_router

app = FastAPI(
    title="Carrier Transicold API",
    version="2.0",
    description="Sistema Operativo Carrier Transicold — API REST"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(asignaciones_router)
app.include_router(tickets_router)
app.include_router(inventario_router)
app.include_router(unidades_router)
app.include_router(usuarios_router)
app.include_router(evidencias_router)
app.include_router(toma_valores_router)
app.include_router(comentarios_router)
app.include_router(ws_router)
app.include_router(cluster_router)
app.include_router(web_router)

@app.get("/")
def root():
    return {"mensaje": "API Carrier Transicold operativa", "docs": "/docs"}

@app.get("/test-onedrive")
def test_onedrive():
    import os
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
            "token_preview": token[:20] + "..."
        }
    except Exception as e:
        return {
            "status": "ERROR ❌",
            "variables": vars_presentes,
            "detalle": str(e)
        }
