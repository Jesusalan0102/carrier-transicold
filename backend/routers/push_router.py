"""
push_router.py — Web Push Notifications (VAPID)
Gestiona suscripciones y el envío de notificaciones push.
"""
from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write, get_db_connection
from auth import verify_token
from pydantic import BaseModel
import os, json, logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/push", tags=["push"])

# Claves VAPID — también hardcodeadas como fallback si el .env no carga
_VAPID_PRIVATE_DEFAULT = "B4J2etCPRETTelmCuPZ4zK45_9xa3xFjGuKRZ55tUxI"
_VAPID_PUBLIC_DEFAULT  = "BLSYNF4Fq1lNklFX-RjjAMVCVUetUM-U9ikZvc8IK--e4noIYJXk_TEEAeGR8_vrUG0vKs3TbE3VSmonmejhVN8"

VAPID_PRIVATE = os.getenv("VAPID_PRIVATE_KEY", _VAPID_PRIVATE_DEFAULT)
VAPID_PUBLIC  = os.getenv("VAPID_PUBLIC_KEY",  _VAPID_PUBLIC_DEFAULT)
VAPID_EMAIL   = os.getenv("VAPID_EMAIL", "mailto:admin@carrier-transicold.com")


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict          # {p256dh: str, auth: str}


# ── Crear tabla si no existe ──────────────────────────────────────────────────
def ensure_push_table():
    execute_write("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            username    VARCHAR(100) NOT NULL,
            endpoint    TEXT NOT NULL,
            p256dh      TEXT NOT NULL,
            auth        VARCHAR(255) NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username)
        )
    """)


# ── Clave pública VAPID (necesaria para el cliente) ───────────────────────────
@router.get("/vapid-public-key")
def get_vapid_public_key():
    return {"publicKey": VAPID_PUBLIC}


# ── Registrar suscripción ─────────────────────────────────────────────────────
@router.post("/subscribe")
def subscribe(sub: PushSubscription, current_user=Depends(verify_token)):
    ensure_push_table()
    username = current_user["username"]
    endpoint = sub.endpoint
    p256dh   = sub.keys.get("p256dh", "")
    auth     = sub.keys.get("auth", "")

    if not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Claves de suscripción inválidas")

    # Borrar suscripciones anteriores del mismo endpoint para este usuario
    execute_write(
        "DELETE FROM push_subscriptions WHERE username=%s AND endpoint=%s",
        (username, endpoint)
    )
    execute_write(
        "INSERT INTO push_subscriptions (username, endpoint, p256dh, auth) VALUES (%s,%s,%s,%s)",
        (username, endpoint, p256dh, auth)
    )
    return {"mensaje": "Suscripción registrada"}


# ── Eliminar suscripción ──────────────────────────────────────────────────────
@router.post("/unsubscribe")
def unsubscribe(sub: PushSubscription, current_user=Depends(verify_token)):
    ensure_push_table()
    execute_write(
        "DELETE FROM push_subscriptions WHERE username=%s AND endpoint=%s",
        (current_user["username"], sub.endpoint)
    )
    return {"mensaje": "Suscripción eliminada"}


# ── Enviar push a todos los suscriptores ─────────────────────────────────────
def send_push_to_all(title: str, body: str, tag: str = "carrier-event", url: str = "/app"):
    """Llamar desde ws.notify() para enviar push a todos los suscriptores."""
    if not VAPID_PRIVATE or not VAPID_PUBLIC:
        return

    try:
        ensure_push_table()
        subs = execute_read("SELECT * FROM push_subscriptions")
    except Exception:
        return

    if not subs:
        return

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return

    dead_endpoints = []
    payload = json.dumps({
        "title": title,
        "body":  body,
        "tag":   tag,
        "url":   url,
    })

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {
                        "p256dh": sub["p256dh"],
                        "auth":   sub["auth"],
                    },
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE,
                vapid_claims={"sub": VAPID_EMAIL},
            )
        except Exception as e:
            err_str = str(e)
            # 410 Gone o 404 = suscripción expirada, limpiar
            if "410" in err_str or "404" in err_str:
                dead_endpoints.append(sub["endpoint"])
            else:
                logger.warning(f"Push failed for {sub['username']}: {e}")

    for ep in dead_endpoints:
        try:
            execute_write("DELETE FROM push_subscriptions WHERE endpoint=%s", (ep,))
        except Exception:
            pass
