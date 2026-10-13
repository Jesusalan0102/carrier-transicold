"""Videos grandes: la DB rechaza filas > 6 MB (error 8025), así que van en trozos."""
import asyncio, io
import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
from auth import verify_token
import evidencia_partes as ep
from routers import evidencias_router as er

MB = 1024 * 1024


class FakeParts:
    def __init__(self): self.t = {}
    def read(self, sql, p=None):
        if "SELECT orden, LENGTH" in sql:
            return [{"orden": o, "n": len(c)} for (e, o), c in sorted(self.t.items()) if e == p[0]]
        if "SELECT contenido FROM evidencia_partes" in sql:
            return [{"contenido": self.t[(p[0], p[1])]}] if (p[0], p[1]) in self.t else []
        raise AssertionError(sql)
    def write(self, sql, p=None):
        if sql.startswith("INSERT INTO evidencia_partes"): self.t[(p[0], p[1])] = p[2]; return 1
        if sql.startswith("DELETE FROM evidencia_partes"):
            for k in [k for k in self.t if k[0] in p]: del self.t[k]
            return 1
        raise AssertionError(sql)


@pytest.fixture
def fp(monkeypatch):
    f = FakeParts()
    monkeypatch.setattr(ep, "execute_read", f.read)
    monkeypatch.setattr(ep, "execute_write", f.write)
    return f


DATA = bytes(range(256)) * (11 * MB // 256)       # 11 MB: justo el caso del error 8025


def test_partes_roundtrip_y_rangos(fp):
    n = ep.guardar_partes(7, DATA)
    assert n == 3 and all(len(c) <= 4 * MB for c in fp.t.values())     # cada fila cabe en el límite de 6 MB
    assert ep.tamano_total(7) == len(DATA) and ep.leer_partes(7) == DATA
    ini, fin = 4 * MB - 10, 8 * MB + 25                                  # cruza dos fronteras de trozo
    assert b"".join(ep.iterar_rango(7, ini, fin)) == DATA[ini:fin + 1]
    assert ep.leer_partes(999) is None and ep.tamano_total(999) == 0


def test_video_grande_con_onedrive_caido_se_guarda(fp, monkeypatch):
    borradas = []
    monkeypatch.setattr(er, "execute_write_with_id", lambda sql, p=None: 42)
    monkeypatch.setattr(er, "execute_write", lambda sql, p=None: borradas.append(sql) or 1)
    r = asyncio.run(er._guardar_grande_en_partes("52971.mp4", DATA, "U1", "TEST", 5, "video", "video/mp4", None))
    assert r["ok"] and ep.leer_partes(42) == DATA


def test_si_fallan_las_partes_no_queda_fila_vacia(fp, monkeypatch):
    borradas = []
    monkeypatch.setattr(er, "execute_write_with_id", lambda sql, p=None: 43)
    monkeypatch.setattr(er, "execute_write", lambda sql, p=None: borradas.append(sql) or 1)
    monkeypatch.setattr(ep, "guardar_partes", lambda *a: (_ for _ in ()).throw(RuntimeError("DB caída")))
    r = asyncio.run(er._guardar_grande_en_partes("x.mp4", DATA, "U1", "TEST", 5, "video", "video/mp4", None))
    assert not r["ok"] and any("DELETE FROM evidencias" in s for s in borradas)


def test_servir_video_en_partes_con_range(fp, monkeypatch):
    ep.guardar_partes(9, DATA)
    monkeypatch.setattr(er, "execute_read", lambda sql, p=None: [
        {"nombre_archivo": "a.mp4", "contenido": None, "mime_type": "video/mp4", "tipo": "video", "onedrive_item_id": None}])
    app = FastAPI(); app.include_router(er.router)
    app.dependency_overrides[er.require_admin_or_visor] = lambda: {"username": "a", "role": "admin"}
    c = TestClient(app)
    r = c.get("/api/evidencias/foto/9")
    assert r.status_code == 200 and r.content == DATA
    r = c.get("/api/evidencias/foto/9", headers={"Range": "bytes=4194000-4195000"})
    assert r.status_code == 206 and r.content == DATA[4194000:4195001]
    assert r.headers["content-range"] == f"bytes 4194000-4195000/{len(DATA)}"


def test_verificar_videos_no_marca_perdido_si_esta_en_partes():
    base = {"tipo": "video", "u_unit": "U1", "u_oculto": 0, "asignacion_id": 5, "a_id": 5,
            "unit_number": "U1", "a_unidad": "U1", "en_db": 0, "onedrive_item_id": None}
    assert er._evaluar_video({**base, "n_partes": 3})["ubicacion"] == "base_de_datos"
    assert er._evaluar_video({**base, "n_partes": 0})["ubicacion"] == "PERDIDO"
