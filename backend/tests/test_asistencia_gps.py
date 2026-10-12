"""
Tests de la validación de GPS al registrar asistencia.

Cubren que el endpoint POST /api/asistencia/registrar rechace registros sin
ubicación, con ubicación vieja/reutilizada, con precisión baja o fuera de la
geocerca, y que acepte un registro válido. No tocan la base de datos real:
se reemplazan la conexión, la geocerca y el token.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

GEOCERCA = {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}


class _FakeCursor:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))


class _FakeConnection:
    def __init__(self):
        self.log = []
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return _FakeCursor(self.log)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def cliente(monkeypatch):
    from main import app
    from auth import verify_token
    from asistencia import routes

    conexion = _FakeConnection()
    monkeypatch.setattr(routes, "obtener_configuracion", lambda: dict(GEOCERCA))
    monkeypatch.setattr(routes, "get_db_connection", lambda: conexion)
    monkeypatch.setattr(routes, "execute_read", lambda *a, **k: [])
    app.dependency_overrides[verify_token] = lambda: {"username": "tecnico1", "role": "tecnico"}

    c = TestClient(app)
    c.conexion = conexion
    yield c
    app.dependency_overrides.clear()


def _body(**cambios):
    """Cuerpo válido: dentro de la geocerca, buena precisión, lectura fresca."""
    base = {
        "tipo": "entrada",
        "lat": GEOCERCA["lat_fija"],
        "lon": GEOCERCA["lon_fija"],
        "accuracy": 12.0,
        "gps_edad_seg": 2.0,
        "foto_base64": None,
    }
    base.update(cambios)
    return base


def _detalle(resp):
    d = resp.json()["detail"]
    return d if isinstance(d, str) else str(d)


def test_registro_valido_se_acepta_y_se_guarda(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body())
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert len(cliente.conexion.log) == 1
    assert cliente.conexion.commits == 1


def test_sin_coordenadas_se_rechaza_con_mensaje_claro(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body(lat=None, lon=None))
    assert r.status_code == 422
    assert "ubicación" in _detalle(r)
    assert cliente.conexion.log == []


def test_sin_campos_gps_se_rechaza(cliente):
    r = cliente.post("/api/asistencia/registrar", json={"tipo": "entrada"})
    assert r.status_code == 422
    assert cliente.conexion.log == []


def test_coordenadas_fuera_de_rango_se_rechazan(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body(lat=123.0))
    assert r.status_code == 422
    assert "inválidas" in _detalle(r)


def test_sin_edad_de_lectura_se_rechaza(cliente):
    # Cliente viejo (página en caché) que no manda gps_edad_seg
    r = cliente.post("/api/asistencia/registrar", json=_body(gps_edad_seg=None))
    assert r.status_code == 422
    assert "Recarga" in _detalle(r)
    assert cliente.conexion.log == []


@pytest.mark.parametrize("edad", [31, 120, 3600, -5])
def test_lectura_gps_vieja_o_invalida_se_rechaza(cliente, edad):
    r = cliente.post("/api/asistencia/registrar", json=_body(gps_edad_seg=edad))
    assert r.status_code == 422
    assert "actualizada" in _detalle(r)
    assert cliente.conexion.log == []


def test_lectura_justo_en_el_limite_se_acepta(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body(gps_edad_seg=30))
    assert r.status_code == 200, r.text


def test_sin_precision_se_rechaza(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body(accuracy=None))
    assert r.status_code == 422
    assert "GPS" in _detalle(r)


def test_precision_baja_se_rechaza(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body(accuracy=200.0))
    assert r.status_code == 422
    assert "Precisión" in _detalle(r)


def test_fuera_de_la_geocerca_se_rechaza(cliente):
    # ~1.1 km al norte del punto fijo (radio permitido: 200 m)
    r = cliente.post("/api/asistencia/registrar", json=_body(lat=GEOCERCA["lat_fija"] + 0.01))
    assert r.status_code == 422
    assert "fuera del área" in _detalle(r)
    assert cliente.conexion.log == []


def test_tipo_invalido_se_rechaza(cliente):
    r = cliente.post("/api/asistencia/registrar", json=_body(tipo="comida"))
    assert r.status_code == 400


def test_pagina_de_checkin_pide_gps_nuevo_en_cada_registro():
    """El HTML del check-in debe resetear la lectura al abrir el modal, capturar
    una nueva al confirmar y mandar su antigüedad al servidor."""
    from routers.web_router import checkin_tecnico

    # Loop propio: asyncio.run() dejaría cerrado el loop global y rompería
    # otros tests que usan asyncio.get_event_loop().
    loop = asyncio.new_event_loop()
    try:
        html = loop.run_until_complete(checkin_tecnico()).body.decode("utf-8")
    finally:
        loop.close()
    assert "function _ctIniciarGPS" in html
    assert "_ctGeocoords = null" in html            # se descarta la lectura previa
    assert "function _ctCapturarGPSFresco" in html
    assert "gps_edad_seg" in html
    assert "maximumAge: 0" in html
