"""Rescate: descargar los videos guardados en la DB, se vean o no en la app."""
import csv, io, zipfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import verify_token
import evidencia_partes as ep
from routers import evidencias_router as er

FILAS = [
    {"id": 10, "unit_number": "CW1", "nombre_archivo": "a.webm", "tecnico": "Auxiliar", "asignacion_id": 7,
     "created_at": "2026-10-09 22:01:33", "actividad": "Evidencia", "bytes_db": 5},
    {"id": 11, "unit_number": "UNIDAD OCULTA", "nombre_archivo": "b.mp4", "tecnico": "X", "asignacion_id": None,
     "created_at": "2026-10-10 10:00:00", "actividad": None, "bytes_db": 3},      # sin tarea y unidad rara
    {"id": 12, "unit_number": "CW1", "nombre_archivo": "grande.mp4", "tecnico": "Y", "asignacion_id": 7,
     "created_at": "2026-10-10 11:00:00", "actividad": "Evidencia", "bytes_db": None},   # en partes
]
BLOBS = {10: b"AAAAA", 11: b"BBB"}
PARTES = b"P" * 9_000_000


@pytest.fixture
def cli(monkeypatch):
    def read(sql, p=None):
        if sql.startswith("SELECT e.id, e.unit_number"):
            desde = p[1]; return [f for f in FILAS if f["id"] > desde][:p[-1]]
        if "COUNT(*) AS n" in sql: return [{"n": len([f for f in FILAS if f["id"] > p[-1]])}]
        if sql.startswith("SELECT contenido FROM evidencias"): return [{"contenido": BLOBS.get(p[0])}]
        raise AssertionError(sql)
    monkeypatch.setattr(er, "execute_read", read)
    monkeypatch.setattr(ep, "tamano_total", lambda i: len(PARTES) if i == 12 else 0)
    monkeypatch.setattr(ep, "iterar_rango", lambda i, a, b: iter([PARTES[:4 * 1024 * 1024], PARTES[4 * 1024 * 1024:]]))
    app = FastAPI(); app.include_router(er.router)
    app.dependency_overrides[verify_token] = lambda: {"username": "admin", "role": "admin"}
    return TestClient(app)


def test_tanda_incluye_videos_ocultos_y_en_partes(cli):
    r = cli.get("/api/evidencias/descargar-videos?limite=2")
    assert r.status_code == 200 and r.headers["x-siguiente-desde"] == "11" and r.headers["x-pendientes"] == "1"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.read("CW1/Tarea_7_Evidencia/10_a.webm") == b"AAAAA"
    assert z.read("UNIDAD_OCULTA/Sin_tarea/11_b.mp4") == b"BBB"             # visible aunque la app no lo muestre
    filas = list(csv.reader(io.StringIO(z.read("LEEME.csv").decode("utf-8-sig"))))
    assert filas[0][0] == "id" and filas[1][1] == "CW1" and filas[1][4] == "Auxiliar" and filas[1][-1] == "ok"


def test_segunda_tanda_trae_el_video_en_partes(cli):
    r = cli.get("/api/evidencias/descargar-videos?limite=2&desde_id=11")
    assert r.headers["x-pendientes"] == "0"
    assert zipfile.ZipFile(io.BytesIO(r.content)).read("CW1/Tarea_7_Evidencia/12_grande.mp4") == PARTES


def test_sin_mas_videos_da_404_y_solo_admin(cli):
    assert cli.get("/api/evidencias/descargar-videos?desde_id=99").status_code == 404
    cli.app.dependency_overrides[verify_token] = lambda: {"username": "t", "role": "tecnico"}
    assert cli.get("/api/evidencias/descargar-videos").status_code == 403
