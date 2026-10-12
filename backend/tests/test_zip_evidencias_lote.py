"""ZIP de evidencias por lote: se arma archivo por archivo, por trozos, sin juntar
todos los videos del lote en RAM (eso tumbaba el servidor con 502/503)."""
import glob
import os
import tempfile
import zipfile
from datetime import datetime

import pytest

import db
from routers import unidades_router as ur

BLOBS = {1: b"FOTO1", 2: b"V" * 25, 3: b"W" * 7}          # contenido que vive en la DB
OD = {"OD1": [b"AAAA", b"BBBB", b"CC"], "OD_MALO": None}   # contenido que vive en OneDrive


def _fila(i, nombre, tipo, en_db, bytes_db, item=None, act="PDI"):
    return {"id": i, "unit_number": "U1", "nombre_archivo": nombre, "tecnico": "juan", "equipo": "",
            "asignacion_id": 5, "tipo": tipo, "onedrive_item_id": item, "en_db": en_db,
            "bytes_db": bytes_db, "fecha_hora": datetime(2026, 6, 1, 10, 0, i), "actividad": act}


META = [
    _fila(1, "f.jpg", "foto", 1, 5),                    # foto chica en la DB
    _fila(2, "v.mp4", "video", 1, 25),                  # video "grande" en la DB -> por trozos
    _fila(3, "c.mp4", "video", 1, 7),                   # video chico en la DB
    _fila(4, "od.mp4", "video", 0, None, item="OD1"),   # video solo en OneDrive
    _fila(5, "malo.mp4", "video", 0, None, item="OD_MALO"),   # OneDrive falla -> se omite
    _fila(6, "vacio.mp4", "video", 0, None),            # fila sin archivo en ningún lado -> se omite
]


class FakeCursor:
    def __init__(self, log):
        self.log, self._res = log, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append(sql)
        if "FROM unidades WHERE id_lote" in sql:
            self._res = [{"unit_number": "U1", "vin_number": "VIN1"}]
        elif "FROM evidencias e" in sql:
            self._res = list(META)
        elif "SUBSTRING(contenido" in sql:
            pos, largo, ident = params
            self._res = {"t": BLOBS[ident][pos - 1: pos - 1 + largo]}
            self.log.append(("trozo", len(self._res["t"])))
        elif sql.startswith("SELECT contenido FROM evidencias WHERE id="):
            self._res = {"contenido": BLOBS[params[0]]}
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchall(self):
        return self._res

    def fetchone(self):
        return self._res


class FakeConn:
    def __init__(self):
        self.log = []

    def cursor(self, *a, **k):
        return FakeCursor(self.log)

    def close(self):
        pass


@pytest.fixture
def entorno(monkeypatch):
    conn = FakeConn()
    monkeypatch.setattr(db, "get_db_connection", lambda: conn)
    monkeypatch.setattr(ur, "ZIP_TROZO_BYTES", 10)           # fuerza leer el blob de 25 bytes en 3 trozos
    monkeypatch.setattr(ur, "ONEDRIVE_ENABLED", True)

    def iter_od(item_id):
        if OD[item_id] is None:
            raise RuntimeError("OneDrive caído")
        yield from OD[item_id]

    monkeypatch.setattr(ur, "_od_iter_item_bytes", iter_od)
    return conn


def _generar():
    antes = set(glob.glob(os.path.join(tempfile.gettempdir(), "evid_od_*")))
    ruta = ur._generar_zip_evidencias_por_lotes(["LOTE1"])
    despues = set(glob.glob(os.path.join(tempfile.gettempdir(), "evid_od_*")))
    return ruta, despues - antes


def test_zip_contiene_todo_y_omite_lo_que_no_se_puede(entorno):
    ruta, temporales = _generar()
    try:
        with zipfile.ZipFile(ruta) as z:
            assert z.testzip() is None
            archivos = {i.filename.rsplit("/", 1)[-1]: i for i in z.infolist() if not i.filename.endswith("/")}
            datos = {n: z.read(i) for n, i in archivos.items()}
            nombres = sorted(n for n in datos if n != "informacion.csv")
            assert len(nombres) == 4, nombres                    # foto + 2 videos de DB + 1 de OneDrive
            por_contenido = {v: n for n, v in datos.items()}
            for esperado in (BLOBS[1], BLOBS[2], BLOBS[3], b"AAAABBBBCC"):
                assert esperado in por_contenido                 # bytes íntegros, también el de 3 trozos
            csv = datos["informacion.csv"].decode()
            assert csv.count("\n") == 4                          # encabezado + 4 filas (sin los omitidos)
            # consecutivos sin huecos (01..04), porque los omitidos no consumen número
            assert [n[:2] for n in nombres] == ["01", "02", "03", "04"]
            # videos sin comprimir, foto comprimida
            for n, i in archivos.items():
                if n.endswith(".mp4"):
                    assert i.compress_type == zipfile.ZIP_STORED
                elif n.endswith(".jpg"):
                    assert i.compress_type == zipfile.ZIP_DEFLATED
    finally:
        os.remove(ruta)
    assert temporales == set()                                   # no quedan temporales de OneDrive


def test_nunca_se_trae_mas_de_un_trozo_a_la_vez(entorno):
    ruta, _ = _generar()
    os.remove(ruta)
    trozos = [x[1] for x in entorno.log if isinstance(x, tuple)]
    assert trozos == [10, 10, 5]                                 # 25 bytes en 3 lecturas, nunca el blob entero
    # ya no existe la carga masiva de blobs del lote entero
    assert not any(isinstance(x, str) and "contenido FROM evidencias WHERE id IN" in x for x in entorno.log)


def test_si_falla_a_medias_no_deja_zip_ni_temporales(entorno, monkeypatch):
    def explota(*a, **k):
        raise RuntimeError("se cayó la DB")

    monkeypatch.setattr(ur, "_leer_blob_por_trozos", explota)
    antes = set(glob.glob(os.path.join(tempfile.gettempdir(), "evid_lotes_*")))
    with pytest.raises(RuntimeError):
        ur._generar_zip_evidencias_por_lotes(["LOTE1"])
    assert set(glob.glob(os.path.join(tempfile.gettempdir(), "evid_lotes_*"))) == antes
