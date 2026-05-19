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
app.include_router(web_router)

@app.get("/")
def root():
    return {"mensaje": "API Carrier Transicold operativa", "docs": "/docs"}

@app.get("/test-onedrive")
def test_onedrive():
    import os
    try:
        import onedrive_service
        return {
            "status": "OK ✅",
            "onedrive_enabled": True,
            "MS_REFRESH_TOKEN": bool(os.getenv("MS_REFRESH_TOKEN")),
            "MS_CLIENT_ID_PERSONAL": bool(os.getenv("MS_CLIENT_ID_PERSONAL")),
            "MS_CLIENT_SECRET_PERSONAL": bool(os.getenv("MS_CLIENT_SECRET_PERSONAL")),
        }
    except Exception as e:
        return {
            "status": "ERROR ❌",
            "error": str(e),
            "MS_REFRESH_TOKEN": bool(os.getenv("MS_REFRESH_TOKEN")),
            "MS_CLIENT_ID_PERSONAL": bool(os.getenv("MS_CLIENT_ID_PERSONAL")),
            "MS_CLIENT_SECRET_PERSONAL": bool(os.getenv("MS_CLIENT_SECRET_PERSONAL")),
        }

@app.get("/auth/onedrive/callback")
def onedrive_callback(code: str = None, error: str = None):
    if error:
        return {"error": error}
    if not code:
        return {"error": "No se recibió código"}
    import requests, os
    client_id     = "dc1c0d4f-0f48-44db-9fde-a63178fb8ab0"
    client_secret = os.getenv("MS_CLIENT_SECRET_PERSONAL", "")
    redirect_uri  = "https://carrier-transicold.onrender.com/auth/onedrive/callback"
    resp = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "client_id":     client_id,
            "client_secret": client_secret,
            "code":          code,
            "redirect_uri":  redirect_uri,
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
