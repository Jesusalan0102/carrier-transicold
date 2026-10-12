"""Copia de videos de la DB a OneDrive (sin borrar de la DB), con DB y OneDrive simulados."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import verify_token
from routers import evidencias_router as er
import onedrive_service as od

CONTENIDO = {1: b"A" * 1000, 2: b"B" * 2000, 3: b"C" * 3000}


@pytest.fixture
def env(monkeypatch):
    log, subidas = [], []
    tamanos = {}

    def read(sql, p=None):
        if "COUNT(*)" in sql:
            return [{"n": 3, "bytes": 6000}]
        if "LENGTH(contenido) AS bytes" in sql:
            return [{"id": i, "unit_number": "U1", "nombre_archivo": f"v{i}.mp4",
                     "asignacion_id": 7, "mime_type": "", "bytes": len(c)} for i, c in CONTENIDO.items()]
        if "SELECT contenido FROM evidencias" in sql:
            return [{"contenido": CONTENIDO[p[0]]}]
        raise AssertionError(sql)

    def subir(unit, nombre, contenido, unit_meta=None):
        item = f"ITEM{len(subidas) + 1}"
        subidas.append(nombre)
        tamanos[item] = len(contenido)
        return {"item_id": item, "webUrl": "https://od/" + nombre}

    monkeypatch.setattr(er, "execute_read", read)
    monkeypatch.setattr(er, "execute_write", lambda sql, p=None: log.append((sql, p)) or 1)
    monkeypatch.setattr(er, "ONEDRIVE_ENABLED", True)
    monkeypatch.setattr(er, "sync_video_evidencia", subir, raising=False)
    monkeypatch.setattr(od, "tamano_item", lambda item_id: tamanos[item_id])

    app = FastAPI()
    app.include_router(er.router)
    app.dependency_overrides[verify_token] = lambda: {"username": "admin", "role": "admin"}
    c = TestClient(app)
    c.log, c.subidas, c.tamanos = log, subidas, tamanos
    return c


def test_simulacion_no_sube_ni_escribe(env):
    j = env.post("/api/evidencias/copiar-videos-a-onedrive?limite=5").json()
    assert env.log == [] and env.subidas == []
    assert j["pendientes_en_db"] == 3 and len(j["tanda"]) == 3
    assert "migrados" not in j


def test_aplicar_sube_y_enlaza_sin_borrar_el_blob(env):
    j = env.post("/api/evidencias/copiar-videos-a-onedrive?aplicar=true&limite=5").json()
    assert len(j["migrados"]) == 3 and j["errores"] == []
    assert len(env.subidas) == 3
    # Enlaza la fila pero NUNCA toca el blob (contenido) ni borra filas
    assert len(env.log) == 3
    assert all("onedrive_item_id=%s" in sql and "contenido" not in sql and "DELETE" not in sql.upper()
               for sql, _ in env.log)
    assert j["pendientes_restantes"] == 0 and j["siguiente_desde_id"] == 3
    # nombre único (prefijo A<asignación>_<id corto>_) para que OneDrive no pise archivos
    assert all(n.startswith("A7_") for n in env.subidas)


def test_si_el_tamano_no_coincide_no_borra_de_la_db(env, monkeypatch):
    monkeypatch.setattr(od, "tamano_item", lambda item_id: 1)   # OneDrive dice 1 byte
    j = env.post("/api/evidencias/copiar-videos-a-onedrive?aplicar=true&limite=5").json()
    assert j["migrados"] == [] and len(j["errores"]) == 3
    assert env.log == []                                        # ninguna fila tocada
    assert "tamaño distinto" in j["errores"][0]["error"]


def test_error_de_onedrive_en_un_video_no_detiene_los_demas(env, monkeypatch):
    original = er.sync_video_evidencia

    def falla_el_segundo(unit, nombre, contenido, unit_meta=None):
        if "v2" in nombre:
            raise RuntimeError("OneDrive caído")
        return original(unit, nombre, contenido)

    monkeypatch.setattr(er, "sync_video_evidencia", falla_el_segundo, raising=False)
    j = env.post("/api/evidencias/copiar-videos-a-onedrive?aplicar=true&limite=5").json()
    assert [m["id"] for m in j["migrados"]] == [1, 3]
    assert [e["id"] for e in j["errores"]] == [2]
    assert len(env.log) == 2                                    # solo 1 y 3 se actualizaron


def test_sin_onedrive_responde_503(env, monkeypatch):
    monkeypatch.setattr(er, "ONEDRIVE_ENABLED", False)
    assert env.post("/api/evidencias/copiar-videos-a-onedrive").status_code == 503


def test_solo_admin(env):
    env.app.dependency_overrides[verify_token] = lambda: {"username": "t", "role": "tecnico"}
    assert env.post("/api/evidencias/copiar-videos-a-onedrive").status_code == 403
