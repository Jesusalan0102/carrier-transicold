"""Activación por serial: verificación de firma, vigencia/gracia, revocación, instalación, middleware y endpoints."""
import base64
import json
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.testclient import TestClient

import licencia
from routers import licencia_router

DIA = 86400


def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _pub(priv):
    return _b64(priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def emitir(priv, cliente="ACME", exp=0, instancia="", lic_id="a1b2c3d4"):
    p = {"v": 1, "id": lic_id, "c": cliente, "iat": int(time.time()), "exp": exp}
    if instancia:
        p["i"] = instancia
    crudo = json.dumps(p, separators=(",", ":"), ensure_ascii=False).encode()
    return f"CTL1.{_b64(crudo)}.{_b64(priv.sign(crudo))}"


@pytest.fixture
def entorno(monkeypatch):
    """Llave de prueba, 'BD' en memoria y licencia obligatoria."""
    priv = Ed25519PrivateKey.generate()
    monkeypatch.setenv("LICENSE_PUBLIC_KEY", _pub(priv))
    monkeypatch.setenv("LICENSE_REQUIRED", "1")
    monkeypatch.delenv("LICENSE_REVOKED_IDS", raising=False)
    monkeypatch.delenv("LICENSE_GRACE_DAYS", raising=False)
    bd = {"serial": None}
    monkeypatch.setattr(licencia, "_leer_serial", lambda: bd["serial"])
    monkeypatch.setattr(licencia, "_guardar_serial", lambda s, d, ip: bd.__setitem__("serial", s))
    monkeypatch.setattr(licencia, "instance_id", lambda: "inst123abc45")
    licencia.invalidar_cache()
    licencia._intentos.clear()
    yield priv, bd
    licencia.invalidar_cache()


# ── verificación ─────────────────────────────────────────────────────────────
def test_serial_valido_se_decodifica(entorno):
    priv, _ = entorno
    d = licencia.decodificar(emitir(priv, "Cliente Ñandú", exp=int(time.time()) + DIA))
    assert d["cliente"] == "Cliente Ñandú" and d["id"] == "a1b2c3d4"


def test_serial_con_saltos_de_linea_de_un_correo_sigue_valido(entorno):
    priv, _ = entorno
    s = emitir(priv)
    partido = "\n".join(s[i:i + 60] for i in range(0, len(s), 60))
    assert licencia.decodificar("  " + partido + "  ")["id"] == "a1b2c3d4"


def test_firma_de_otra_llave_se_rechaza(entorno):
    with pytest.raises(licencia.LicenciaError, match="firma"):
        licencia.decodificar(emitir(Ed25519PrivateKey.generate()))


def test_serial_alterado_se_rechaza(entorno):
    priv, _ = entorno
    pref, payload, firma = emitir(priv, exp=1).split(".")
    falso = json.loads(base64.urlsafe_b64decode(payload + "=="))
    falso["exp"] = 0                                   # intento de volverla indefinida
    nuevo = _b64(json.dumps(falso, separators=(",", ":")).encode())
    with pytest.raises(licencia.LicenciaError):
        licencia.decodificar(f"{pref}.{nuevo}.{firma}")


@pytest.mark.parametrize("basura", ["", "hola", "CTL1.abc", "XXX.a.b", "CTL1.@@@.@@@"])
def test_basura_se_rechaza_sin_tronar(entorno, basura):
    with pytest.raises(licencia.LicenciaError):
        licencia.decodificar(basura)


def test_sin_llave_publica_en_el_servidor(entorno, monkeypatch):
    priv, _ = entorno
    monkeypatch.delenv("LICENSE_PUBLIC_KEY")
    with pytest.raises(licencia.LicenciaError, match="LICENSE_PUBLIC_KEY"):
        licencia.decodificar(emitir(priv))


# ── vigencia ─────────────────────────────────────────────────────────────────
def test_indefinida_vigente_gracia_y_vencida(entorno):
    priv, _ = entorno
    ahora = time.time()
    ev = lambda exp: licencia.evaluar(licencia.decodificar(emitir(priv, exp=exp)), "inst123abc45", ahora)
    assert ev(0)["estado"] == "activa" and ev(0)["dias_restantes"] is None
    vig = ev(int(ahora) + 10 * DIA)
    assert vig["estado"] == "activa" and vig["dias_restantes"] == 10 and vig["permitido"]
    gra = ev(int(ahora) - 2 * DIA)
    assert gra["estado"] == "en_gracia" and gra["permitido"]
    ven = ev(int(ahora) - 8 * DIA)                     # gracia por defecto = 7 días
    assert ven["estado"] == "vencida" and not ven["permitido"]


def test_gracia_configurable(entorno, monkeypatch):
    priv, _ = entorno
    monkeypatch.setenv("LICENSE_GRACE_DAYS", "0")
    d = licencia.decodificar(emitir(priv, exp=int(time.time()) - 3600))
    assert licencia.evaluar(d, "inst123abc45")["estado"] == "vencida"


def test_revocada(entorno, monkeypatch):
    priv, _ = entorno
    monkeypatch.setenv("LICENSE_REVOKED_IDS", "zzzz, A1B2C3D4")
    d = licencia.decodificar(emitir(priv))
    assert licencia.evaluar(d, "inst123abc45")["estado"] == "revocada"


def test_serial_ligado_a_otra_instalacion(entorno):
    priv, _ = entorno
    d = licencia.decodificar(emitir(priv, instancia="otra99999999"))
    assert licencia.evaluar(d, "inst123abc45")["estado"] == "invalida"
    d2 = licencia.decodificar(emitir(priv, instancia="inst123abc45"))
    assert licencia.evaluar(d2, "inst123abc45")["permitido"]


# ── estado y activación ──────────────────────────────────────────────────────
def test_estados_segun_bd(entorno, monkeypatch):
    priv, bd = entorno
    assert licencia.calcular_estado()["estado"] == "sin_activar"
    bd["serial"] = emitir(priv)
    assert licencia.calcular_estado()["estado"] == "activa"
    bd["serial"] = "CTL1.basura.basura"
    assert licencia.calcular_estado()["estado"] == "invalida"
    monkeypatch.setenv("LICENSE_REQUIRED", "0")
    assert licencia.calcular_estado()["permitido"] and licencia.calcular_estado()["estado"] == "no_requerida"


def test_un_serial_manipulado_directo_en_la_bd_no_sirve(entorno):
    _, bd = entorno
    bd["serial"] = emitir(Ed25519PrivateKey.generate())     # alguien escribe un serial propio en la tabla
    assert not licencia.calcular_estado()["permitido"]


def test_activar_guarda_y_rechaza_vencidos(entorno):
    priv, bd = entorno
    with pytest.raises(licencia.LicenciaError, match="venció"):
        licencia.activar(emitir(priv, exp=int(time.time()) - 30 * DIA))
    assert bd["serial"] is None
    est = licencia.activar(emitir(priv, "ACME", exp=int(time.time()) + 5 * DIA))
    assert est["permitido"] and bd["serial"].startswith("CTL1.")


def test_freno_de_intentos(entorno):
    assert not any(licencia.demasiados_intentos("1.1.1.1", 1000 + i) for i in range(licencia.INTENTOS_MAX))
    assert licencia.demasiados_intentos("1.1.1.1", 1100)
    assert not licencia.demasiados_intentos("2.2.2.2", 1100)
    assert not licencia.demasiados_intentos("1.1.1.1", 1000 + licencia.INTENTOS_VENTANA_SEG + 50)


# ── middleware + endpoints ───────────────────────────────────────────────────
@pytest.fixture
def cliente_http(entorno):
    app = FastAPI()
    app.add_middleware(BaseHTTPMiddleware, dispatch=licencia.middleware_licencia)
    app.include_router(licencia_router.router)

    @app.get("/app")
    def pagina():
        return {"pagina": True}

    @app.post("/api/auth/login")
    def login():
        return {"token": "x"}

    @app.get("/api/health")
    def salud():
        return {"ok": True}

    return TestClient(app, follow_redirects=False)


def test_sin_activar_bloquea_login_y_redirige_paginas(cliente_http):
    r = cliente_http.post("/api/auth/login")
    assert r.status_code == 403 and r.json()["codigo"] == "LICENCIA_REQUERIDA"
    r = cliente_http.get("/app")
    assert r.status_code == 302 and r.headers["location"] == "/activar"
    assert cliente_http.get("/activar").status_code == 200           # la pantalla de activación siempre abre
    assert cliente_http.get("/api/health").status_code == 200
    assert cliente_http.get("/api/licencia/estado").json()["estado"] == "sin_activar"


def test_activar_por_api_y_luego_todo_funciona(entorno, cliente_http):
    priv, _ = entorno
    r = cliente_http.post("/api/licencia/activar", json={"serial": "CTL1.mal.serial"})
    assert r.status_code == 400
    r = cliente_http.post("/api/licencia/activar", json={"serial": emitir(priv, "ACME", exp=int(time.time()) + 9 * DIA)})
    assert r.status_code == 200 and r.json()["cliente"] == "ACME" and r.json()["permitido"]
    assert "licencia_id" not in r.json()                                # no se expone el id interno
    assert cliente_http.post("/api/auth/login").status_code == 200
    assert cliente_http.get("/app").json() == {"pagina": True}


def test_en_gracia_deja_pasar_con_encabezado(entorno, cliente_http):
    priv, bd = entorno
    bd["serial"] = emitir(priv, exp=int(time.time()) - DIA)
    r = cliente_http.post("/api/auth/login")
    assert r.status_code == 200 and r.headers["x-licencia-estado"] == "en_gracia"


def test_sin_licencia_requerida_todo_normal(entorno, cliente_http, monkeypatch):
    monkeypatch.setenv("LICENSE_REQUIRED", "0")
    assert cliente_http.post("/api/auth/login").status_code == 200
    assert cliente_http.post("/api/licencia/activar", json={"serial": "x"}).status_code == 400


def test_la_activacion_se_frena_por_ip(entorno, cliente_http):
    codigos = [cliente_http.post("/api/licencia/activar", json={"serial": "mal"}).status_code
               for _ in range(licencia.INTENTOS_MAX + 2)]
    assert codigos[0] == 400 and codigos[-1] == 429


# ── fallos de la base de datos ───────────────────────────────────────────────
def test_si_la_bd_falla_sin_estado_previo_no_deja_pasar(entorno, monkeypatch):
    monkeypatch.setattr(licencia, "_leer_serial", lambda: (_ for _ in ()).throw(RuntimeError("BD caída")))
    est = licencia.estado_cacheado()
    assert est["estado"] == "desconocido" and not est["permitido"]


def test_si_la_bd_falla_conserva_el_ultimo_estado_bueno(entorno, monkeypatch):
    priv, bd = entorno
    bd["serial"] = emitir(priv)
    assert licencia.estado_cacheado()["permitido"]
    monkeypatch.setattr(licencia, "_leer_serial", lambda: (_ for _ in ()).throw(RuntimeError("BD caída")))
    licencia._cache["t"] = 0                       # fuerza recalcular
    assert licencia.estado_cacheado()["permitido"]


def test_sin_licencia_requerida_no_toca_la_bd(entorno, monkeypatch):
    monkeypatch.setenv("LICENSE_REQUIRED", "0")
    monkeypatch.setattr(licencia, "instance_id", lambda: (_ for _ in ()).throw(AssertionError("tocó la BD")))
    monkeypatch.setattr(licencia, "_leer_serial", lambda: (_ for _ in ()).throw(AssertionError("tocó la BD")))
    assert licencia.calcular_estado()["estado"] == "no_requerida"
