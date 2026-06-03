from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Importar routers
from routers.auth_router import router as auth_router
from routers.reportes_router import router as reportes_router
# Agrega aquí otros routers cuando los tengas:
# from routers.inventario_router import router as inventario_router
# etc.

# Importar init_db
from db import init_db

app = FastAPI(title="Carrier Transicold API")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia en producción por dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(reportes_router, prefix="/reportes", tags=["reportes"])

@app.get("/")
async def root():
    return {"message": "API Carrier Transicold funcionando 🚀"}

@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 9000)))
