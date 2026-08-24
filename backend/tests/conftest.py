"""
Config compartida de pytest.

Importante: todos los módulos del backend leen sus variables de entorno con
os.getenv(..., valor_por_defecto), así que técnicamente importan sin un .env
real. Aun así fijamos valores dummy aquí para que los tests sean deterministas
y no dependan de lo que haya (o no haya) en el entorno de quien los corre.

Ninguno de estos tests toca la base de datos real: init_db() sólo se ejecuta
en el evento "startup" de FastAPI, y usamos TestClient sin entrar como
context manager, así que ese evento nunca se dispara.
"""
import os
import sys
import pathlib

# Permite "import main", "import db", etc. igual que en producción,
# donde start.sh hace cd al directorio backend/ antes de correr uvicorn.
BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "test-secret-key-no-usar-en-produccion")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("VAPID_EMAIL", "mailto:test@example.com")
# Sin SENTRY_DSN a propósito: así confirmamos que el arranque no requiere Sentry.
