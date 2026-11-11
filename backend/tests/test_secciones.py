"""Secciones de evidencia (Reefer / Evaporador / Blower / Tanque) por lote."""
import os
import zipfile
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import db
import secciones as sec
from auth import verify_token
from routers import evidencias_router as er
from routers import unidades_router as ur


# ── módulo secciones ───────────────────────────────────────────────────────────────────────────
def test_normalizar_ordena_quita_repetidas_y_acepta_texto():
    assert sec.normalizar(["tanque", "reefer", "Reefer", " blower "]) == ["reefer", "blower", "tanque"]
    assert sec.normalizar("tanque,reefer") == ["reefer", "tanque"]
    assert sec.normalizar(None) == [] and sec.normalizar([]) == []
    assert sec.a_texto(["tanque", "reefer"]) == "reefer,tanque"
    assert sec.a_texto([]) is None


def test_invalidas_y_etiquetas():
    assert sec.invalidas(["reefer", "motor", "X"]) == ["motor", "x"]
    assert sec.etiqueta("evaporador") == "Evaporador" and sec.etiqueta("nada") is None
    assert sec.aplica_a_actividad("Inspección") and sec.aplica_a_actividad("Evidencia")
    assert not sec.aplica_a_actividad("PDI") and not sec.aplica_a_actividad("Video de liberación")


def _fake_info(monkeypatch, actividad="Inspección", secciones="reefer,tanque", tecnico="juan"):
    def leer(sql, params=None):
        if "FROM asignaciones" in sql:
            return [{"actividad": actividad, "tecnico": tecnico, "id_lote": "L1"}]
        if "FROM lotes_config" in sql:
            return [{"secciones_evidencia": secciones}]
        if "GROUP BY seccion" in sql:
            return [{"seccion": "reefer", "n": 3}]
        raise AssertionError(sql)
    monkeypatch.setattr(db, "execute_read", leer)
    monkeypatch.setattr(er, "execute_read", leer)


def test_seccion_para_guardar_reglas(monkeypatch):
    _fake_info(monkeypatch)
    assert sec.seccion_para_guardar(5, None) is None
    assert sec.seccion_para_guardar(5, "") is None
    assert sec.seccion_para_guardar(5, "Reefer") == "reefer"
    with pytest.raises(ValueError):
        sec.seccion_para_guardar(5, "motor")
    # no se pierde una foto si el admin quitó la sección entretanto
    _fake_info(monkeypatch, secciones=None)
    assert sec.seccion_para_guardar(5, "tanque") == "tanque"
    # tarea que no es Inspección/Evidencia: la sección se ignora
    _fake_info(monkeypatch, actividad="PDI")
    assert sec.seccion_para_guardar(5, "tanque") is None


# ── endpoint de la tarea ───────────────────────────────────────────────────────────────────────
def _cliente(rol="tecnico", usuario="juan"):
    app = FastAPI()
    app.include_router(er.router)
    app.dependency_overrides[verify_token] = lambda: {"username": usuario, "role": rol}
    return TestClient(app)


def test_endpoint_secciones_de_tarea(monkeypatch):
    _fake_info(monkeypatch)
    d = _cliente().get("/api/evidencias/secciones/5").json()
    assert d["aplica"] is True
    assert [(s["clave"], s["etiqueta"], s["total"]) for s in d["secciones"]] == [("reefer", "Reefer", 3), ("tanque", "Tanque", 0)]
    assert _cliente("tecnico", "otro").get("/api/evidencias/secciones/5").status_code == 403
    assert _cliente("admin", "root").get("/api/evidencias/secciones/5").status_code == 200
    _fake_info(monkeypatch, secciones=None)
    d = _cliente().get("/api/evidencias/secciones/5").json()
    assert d["aplica"] is False and d["secciones"] == []


def test_endpoint_tarea_inexistente(monkeypatch):
    monkeypatch.setattr(db, "execute_read", lambda *a, **k: [])
    assert _cliente().get("/api/evidencias/secciones/99").status_code == 404


# ── endpoints del lote (administrador) ─────────────────────────────────────────────────────────
def _cliente_lotes(rol):
    app = FastAPI()
    app.include_router(ur.router)
    app.dependency_overrides[verify_token] = lambda: {"username": "root", "role": rol}
    return TestClient(app)


def test_guardar_secciones_del_lote(monkeypatch):
    guardado = {}
    monkeypatch.setattr(ur, "execute_read", lambda sql, p=None: [{"id": 1}, {"id": 2}] if "FROM unidades" in sql else [])
    monkeypatch.setattr(sec, "guardar_secciones_lote",
                        lambda lote, s, u: guardado.update(lote=lote, s=sec.normalizar(s)) or sec.normalizar(s))
    c = _cliente_lotes("admin")
    r = c.post("/api/unidades/lotes/secciones", json={"id_lote": "L1", "secciones": ["tanque", "reefer"]})
    assert r.status_code == 200 and r.json()["secciones"] == ["reefer", "tanque"] and r.json()["unidades_afectadas"] == 2
    assert guardado == {"lote": "L1", "s": ["reefer", "tanque"]}
    assert c.post("/api/unidades/lotes/secciones", json={"id_lote": "L1", "secciones": ["motor"]}).status_code == 400
    assert _cliente_lotes("visor").post("/api/unidades/lotes/secciones", json={"id_lote": "L1", "secciones": []}).status_code == 403
    monkeypatch.setattr(ur, "execute_read", lambda *a, **k: [])
    assert c.post("/api/unidades/lotes/secciones", json={"id_lote": "NO", "secciones": []}).status_code == 404


# ── ZIP de exportación: carpetas por sección ───────────────────────────────────────────────────
def _fila(i, nombre, act, seccion):
    return {"id": i, "unit_number": "U1", "nombre_archivo": nombre, "tecnico": "juan", "equipo": "",
            "asignacion_id": 5, "tipo": "foto", "onedrive_item_id": None, "en_db": 1, "bytes_db": 3,
            "fecha_hora": datetime(2026, 6, 1, 10, 0, i), "actividad": act, "seccion": seccion}


FILAS = [_fila(1, "a.jpg", "Inspección", "reefer"), _fila(2, "b.jpg", "Inspección", "reefer"),
         _fila(3, "c.jpg", "Inspección", "tanque"), _fila(4, "d.jpg", "Evidencia", "blower"),
         _fila(5, "e.jpg", "PDI", None), _fila(6, "f.mp4", "Video de liberación", None),
         _fila(7, "g.jpg", "Inspección", None)]            # foto vieja, sin sección


class _Cur:
    def __init__(self): self._r = None
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params=None):
        if "FROM unidades WHERE id_lote" in sql:
            self._r = [{"unit_number": "U1", "vin_number": "VIN1"}]
        elif "FROM evidencias e" in sql:
            assert "e.seccion" in sql
            self._r = list(FILAS)
        elif sql.startswith("SELECT contenido FROM evidencias WHERE id="):
            self._r = {"contenido": b"abc"}
        elif "SUBSTRING(contenido" in sql:
            self._r = {"t": b"abc"}
        else:
            self._r = []
    def fetchall(self): return self._r
    def fetchone(self): return self._r


class _Conn:
    def cursor(self, *a, **k): return _Cur()
    def close(self): pass


@pytest.fixture
def zip_lote(monkeypatch):
    monkeypatch.setattr(db, "get_db_connection", lambda: _Conn())
    monkeypatch.setattr(ur, "ONEDRIVE_ENABLED", False)

    def abrir(builder, *args):
        ruta = builder(*args)
        try:
            with zipfile.ZipFile(ruta) as z:
                return z.testzip(), sorted(z.namelist()), {n: z.read(n) for n in z.namelist() if n.endswith(".csv")}
        finally:
            os.remove(ruta)
    return abrir


@pytest.mark.parametrize("builder,args", [(lambda: ur._generar_zip_evidencias_por_lotes, (["L1"],)),
                                          (lambda: ur._generar_zip_backup_lote_disco, ("L1",))])
def test_zip_separa_por_seccion(zip_lote, builder, args):
    malo, nombres, csvs = zip_lote(builder(), *args)
    assert malo is None
    archivos = [n for n in nombres if not n.endswith("/") and not n.endswith(".csv")]
    rutas = archivos
    texto = "\n".join(rutas)
    assert "Inspección/Reefer/" in texto and "Inspección/Tanque/" in texto and "Evidencia/Blower/" in texto
    # sin secciones: la carpeta de la tarea queda como siempre (sin subcarpeta)
    assert "PDI/Reefer" not in texto and "Video de liberación/" in texto
    reefer = [n for n in archivos if "Inspección/Reefer/" in n]
    assert len(reefer) == 2 and all("_Reefer_" in n for n in reefer)
    # la foto vieja sin sección sigue en la carpeta de Inspección, sin subcarpeta
    sueltas = [n for n in archivos if "/Inspección/" in n and not any(f"/{s}/" in n for s in ("Reefer", "Tanque"))]
    assert len(sueltas) == 1
    # informacion.csv dentro de cada carpeta de sección, con columna Seccion
    csv_reefer = [v for k, v in csvs.items() if "Inspección/Reefer/" in k]
    assert csv_reefer and b"Seccion" in csv_reefer[0]
