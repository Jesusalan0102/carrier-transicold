"""
licencia.py — activación de la app con un SERIAL KEY firmado.

Cómo funciona
  • Un programa aparte (keygen_licencias.py, que NO vive en este repo) genera los seriales y los firma con una
    llave PRIVADA Ed25519 que solo tú tienes.
  • Esta app solo trae la llave PÚBLICA (variable de entorno LICENSE_PUBLIC_KEY): puede comprobar que un serial es
    auténtico, pero no puede fabricar uno nuevo.
  • Mientras LICENSE_REQUIRED=1, nadie puede iniciar sesión ni usar la API hasta activar un serial válido
    en /activar. Con LICENSE_REQUIRED=0 (por defecto) la app funciona como siempre, sin pedir nada.

Formato del serial:  CTL1.<payload JSON en base64url>.<firma Ed25519 en base64url>
  payload = {"v":1, "id":"a1b2c3d4", "c":"Cliente", "iat":<emitido>, "exp":<vence o 0=indefinida>, "i":"<instalación>"}
  "i" (opcional) liga el serial a UNA instalación concreta (el "ID de instalación" que se ve en /activar).

Variables de entorno
  LICENSE_REQUIRED        1 para exigir licencia (por defecto 0)
  LICENSE_PUBLIC_KEY      llave pública que imprime `keygen_licencias.py init`
  LICENSE_GRACE_DAYS      días de gracia después de vencer (por defecto 7)
  LICENSE_REVOKED_IDS     ids de licencia revocados, separados por comas (opcional)
"""
import base64
import binascii
import json
import logging
import math
import os
import re
import threading
import time
import uuid
from collections import defaultdict, deque

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

logger = logging.getLogger(__name__)

PREFIJO = "CTL1"
CACHE_TTL_SEG = 30
INTENTOS_MAX = 10          # intentos de activación por IP...
INTENTOS_VENTANA_SEG = 600  # ...cada 10 minutos


class LicenciaError(Exception):
    """Serial inválido, vencido, revocado o de otra instalación."""


# ── configuración ──────────────────────────────────────────────────────────
def licencia_requerida() -> bool:
    return os.getenv("LICENSE_REQUIRED", "0").strip().lower() in ("1", "true", "si", "sí", "yes")


def dias_gracia() -> int:
    try:
        return max(0, int(os.getenv("LICENSE_GRACE_DAYS", "7")))
    except ValueError:
        return 7


def _revocadas() -> set:
    return {x.strip().lower() for x in os.getenv("LICENSE_REVOKED_IDS", "").split(",") if x.strip()}


# ── codificación ───────────────────────────────────────────────────────────
def _b64d(texto: str) -> bytes:
    t = texto.strip().replace("+", "-").replace("/", "_")
    t += "=" * (-len(t) % 4)
    try:
        return base64.urlsafe_b64decode(t.encode("ascii"))
    except (binascii.Error, UnicodeEncodeError, ValueError):
        raise LicenciaError("El serial tiene caracteres no válidos.")


def _clave_publica() -> Ed25519PublicKey:
    raw = os.getenv("LICENSE_PUBLIC_KEY", "").strip()
    if not raw:
        raise LicenciaError("El servidor no tiene configurada la clave pública de licencias (LICENSE_PUBLIC_KEY).")
    try:
        return Ed25519PublicKey.from_public_bytes(_b64d(raw))
    except (ValueError, LicenciaError):
        raise LicenciaError("LICENSE_PUBLIC_KEY del servidor no es válida.")


def decodificar(serial: str) -> dict:
    """Verifica la firma y devuelve los datos de la licencia. Lanza LicenciaError si no es auténtico."""
    s = re.sub(r"\s+", "", serial or "")        # los correos suelen partir el texto en varias líneas
    partes = s.split(".")
    if len(partes) != 3 or partes[0] != PREFIJO:
        raise LicenciaError("Formato de serial no válido.")
    payload, firma = _b64d(partes[1]), _b64d(partes[2])
    try:
        _clave_publica().verify(firma, payload)
    except InvalidSignature:
        raise LicenciaError("Serial no válido (la firma no coincide).")
    try:
        d = json.loads(payload.decode("utf-8"))
        if d.get("v") != 1:
            raise ValueError("versión")
        return {
            "id": str(d["id"]).lower(),
            "cliente": str(d["c"]),
            "emitida": int(d.get("iat") or 0),
            "vence": int(d.get("exp") or 0),          # 0 = indefinida
            "instancia": str(d.get("i") or ""),
        }
    except (ValueError, KeyError, TypeError):
        raise LicenciaError("El contenido del serial está dañado.")


# ── evaluación ─────────────────────────────────────────────────────────────
def evaluar(datos: dict, instancia_local: str, ahora: float = None) -> dict:
    """Aplica las reglas (revocación, instalación, vigencia, gracia) a una licencia ya autenticada."""
    ahora = time.time() if ahora is None else ahora
    vence = datos["vence"]
    base = {"cliente": datos["cliente"], "licencia_id": datos["id"], "vence_ts": vence or None,
            "dias_restantes": None}

    if datos["id"] in _revocadas():
        return {**base, "estado": "revocada", "permitido": False,
                "mensaje": "Esta licencia fue revocada. Contacta a tu proveedor."}
    if datos["instancia"] and datos["instancia"] != instancia_local:
        return {**base, "estado": "invalida", "permitido": False,
                "mensaje": "Este serial pertenece a otra instalación."}
    if not vence:
        return {**base, "estado": "activa", "permitido": True, "mensaje": "Licencia indefinida."}

    dias = math.ceil((vence - ahora) / 86400)
    if ahora <= vence:
        return {**base, "estado": "activa", "permitido": True, "dias_restantes": dias,
                "mensaje": f"Licencia vigente ({dias} día(s) restantes)."}
    if ahora <= vence + dias_gracia() * 86400:
        restantes = math.ceil((vence + dias_gracia() * 86400 - ahora) / 86400)
        return {**base, "estado": "en_gracia", "permitido": True, "dias_restantes": 0,
                "mensaje": f"La licencia venció. Quedan {restantes} día(s) de gracia: activa un serial nuevo."}
    return {**base, "estado": "vencida", "permitido": False, "dias_restantes": 0,
            "mensaje": "La licencia venció. Ingresa un serial vigente para continuar."}


# ── almacenamiento (la única parte que toca la base de datos) ──────────────
_tabla_lista = False


def _asegurar_tabla():
    global _tabla_lista
    if _tabla_lista:
        return
    from db import execute_write
    execute_write("""
        CREATE TABLE IF NOT EXISTS licencia_activa (
            id            TINYINT PRIMARY KEY,
            serial_key    TEXT NOT NULL,
            licencia_id   VARCHAR(16)  DEFAULT NULL,
            cliente       VARCHAR(150) DEFAULT NULL,
            activada_ip   VARCHAR(64)  DEFAULT NULL,
            activada_en   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    _tabla_lista = True


def _leer_serial():
    from db import execute_read
    _asegurar_tabla()
    filas = execute_read("SELECT serial_key FROM licencia_activa WHERE id=1") or []
    return filas[0]["serial_key"] if filas else None


def _guardar_serial(serial: str, datos: dict, ip: str):
    from db import execute_write
    _asegurar_tabla()
    execute_write(
        "INSERT INTO licencia_activa (id, serial_key, licencia_id, cliente, activada_ip) VALUES (1,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE serial_key=VALUES(serial_key), licencia_id=VALUES(licencia_id), "
        "cliente=VALUES(cliente), activada_ip=VALUES(activada_ip)",
        (serial, datos["id"], datos["cliente"], ip),
    )


_instancia = None


def instance_id() -> str:
    """ID estable de esta instalación (se genera una vez y se guarda en la base de datos)."""
    global _instancia
    if _instancia:
        return _instancia
    from db import execute_read, execute_write
    execute_write("""
        CREATE TABLE IF NOT EXISTS licencia_instalacion (
            id          TINYINT PRIMARY KEY,
            instance_id VARCHAR(16) NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    execute_write("INSERT IGNORE INTO licencia_instalacion (id, instance_id) VALUES (1, %s)",
                  (uuid.uuid4().hex[:12],))
    filas = execute_read("SELECT instance_id FROM licencia_instalacion WHERE id=1") or []
    _instancia = filas[0]["instance_id"]
    return _instancia


# ── estado ─────────────────────────────────────────────────────────────────
def calcular_estado(ahora: float = None) -> dict:
    requerida = licencia_requerida()
    base = {"requerida": requerida, "instance_id": None, "cliente": None, "licencia_id": None,
            "vence_ts": None, "dias_restantes": None}
    if not requerida:                     # instalación sin licencia: no se toca la BD para nada
        return {**base, "estado": "no_requerida", "permitido": True, "mensaje": "Licencia no requerida."}
    inst = instance_id()
    base["instance_id"] = inst

    serial = _leer_serial()
    if not serial:
        return {**base, "estado": "sin_activar", "permitido": False,
                "mensaje": "Ingresa el serial de activación para usar la aplicación."}
    try:
        datos = decodificar(serial)          # se vuelve a verificar la firma: la BD sola no basta
    except LicenciaError as e:
        return {**base, "estado": "invalida", "permitido": False, "mensaje": str(e)}
    return {**base, **evaluar(datos, inst, ahora)}


_cache = {"t": 0.0, "v": None}
_lock = threading.Lock()


def estado_cacheado() -> dict:
    """Estado con caché de unos segundos. Si la BD falla, conserva el último estado conocido (si lo hay)."""
    ahora = time.time()
    with _lock:
        if _cache["v"] is not None and ahora - _cache["t"] < CACHE_TTL_SEG:
            return _cache["v"]
    try:
        est = calcular_estado()
    except Exception as e:
        logger.error(f"[licencia] no se pudo calcular el estado: {e}")
        with _lock:
            if _cache["v"] is not None:
                return _cache["v"]
        # Sin ningún estado previo no se deja pasar a nadie (si la BD no responde, la app tampoco funcionaría).
        return {"requerida": True, "estado": "desconocido", "permitido": False,
                "mensaje": "No se pudo verificar la licencia. Inténtalo de nuevo en un momento.",
                "instance_id": None, "cliente": None, "licencia_id": None, "vence_ts": None, "dias_restantes": None}
    with _lock:
        _cache["v"], _cache["t"] = est, ahora
    return est


def invalidar_cache():
    with _lock:
        _cache["v"], _cache["t"] = None, 0.0


# ── activación ─────────────────────────────────────────────────────────────
def activar(serial: str, ip: str = "") -> dict:
    """Valida el serial y, si es utilizable, lo deja guardado. Lanza LicenciaError con un mensaje claro."""
    datos = decodificar(serial)
    ev = evaluar(datos, instance_id())
    if not ev["permitido"]:
        raise LicenciaError(ev["mensaje"])
    _guardar_serial(re.sub(r"\s+", "", serial), datos, ip)
    invalidar_cache()
    logger.info(f"[licencia] activada licencia {datos['id']} para '{datos['cliente']}' desde {ip}")
    return calcular_estado()


# ── freno a intentos repetidos ─────────────────────────────────────────────
_intentos = defaultdict(deque)


def demasiados_intentos(ip: str, ahora: float = None) -> bool:
    ahora = time.time() if ahora is None else ahora
    q = _intentos[ip]
    while q and ahora - q[0] > INTENTOS_VENTANA_SEG:
        q.popleft()
    if len(q) >= INTENTOS_MAX:
        return True
    q.append(ahora)
    return False


# ── middleware ─────────────────────────────────────────────────────────────
_EXENTAS = {"/activar", "/sw.js", "/favicon.ico", "/api/health"}
_EXENTAS_PREFIJO = ("/static/", "/.well-known/", "/api/licencia/")


async def middleware_licencia(request, call_next):
    """Si la licencia es obligatoria y no está vigente: la API responde 403 y las páginas redirigen a /activar."""
    from fastapi.responses import JSONResponse, RedirectResponse
    from starlette.concurrency import run_in_threadpool

    path = request.url.path
    if (request.method == "OPTIONS" or path in _EXENTAS or path.startswith(_EXENTAS_PREFIJO)
            or not licencia_requerida()):
        return await call_next(request)

    est = await run_in_threadpool(estado_cacheado)
    if est["permitido"]:
        resp = await call_next(request)
        if est["estado"] == "en_gracia":
            resp.headers["X-Licencia-Estado"] = "en_gracia"
        return resp

    if path.startswith("/api/"):
        return JSONResponse(status_code=403, content={
            "detail": est["mensaje"], "codigo": "LICENCIA_REQUERIDA", "estado": est["estado"]})
    return RedirectResponse("/activar", status_code=302)
