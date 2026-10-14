"""Monitor de salud, validación de evidencia en el servidor y subida automática de galería."""
import shutil, subprocess, asyncio
import pytest
from fastapi import HTTPException
import salud_evidencias as sv
from routers import asignaciones_router as ar
from routers import web_router as wr


# ── monitor de salud ─────────────────────────────────────────────────────────
OK = {"ok": True, "libre_gb": 100, "total_gb": 1000}
CAIDO = {"ok": False, "paso": "token", "error": "invalid_grant"}
AUD0 = {"tareas_sin_evidencia": [], "videos_sin_archivo": 0, "subidas_incompletas": [], "videos_solo_en_db": 0, "mb_videos_solo_en_db": 0}


def test_problemas_describe_lo_que_falla():
    aud = {**AUD0, "tareas_sin_evidencia": [{"id": 1}] * 3, "videos_sin_archivo": 2}
    p = sv.problemas(CAIDO, aud)
    assert len(p) == 3 and "OneDrive no funciona" in p[0] and "3 tarea(s)" in p[1] and "2 video(s)" in p[2]
    assert sv.problemas(OK, AUD0) == []


def test_aviso_solo_cuando_cambia_o_onedrive_sigue_caido():
    prob = ["OneDrive no funciona (token): x"]
    firma = "|".join(sorted(prob))
    assert sv._debe_avisar(prob, False, None, 1000)                                   # primera vez
    assert not sv._debe_avisar(prob, False, {"firma": firma, "ts": 1000}, 1000 + 3600)   # misma firma, 1 h
    assert sv._debe_avisar(prob, False, {"firma": firma, "ts": 1000}, 1000 + 25 * 3600)  # recordatorio diario
    assert not sv._debe_avisar(["3 tarea(s) sin evidencia"], True, {"firma": "3 tarea(s) sin evidencia", "ts": 0}, 10 ** 7)
    assert sv._debe_avisar(["4 tarea(s) sin evidencia"], True, {"firma": "3 tarea(s) sin evidencia", "ts": 0}, 10)  # empeoró
    assert not sv._debe_avisar([], True, None, 1)


@pytest.fixture
def ciclo_env(monkeypatch):
    mem, avisos, copias = {}, [], []
    monkeypatch.setattr(sv, "guardar_estado", lambda k, v: mem.__setitem__(k, v))
    monkeypatch.setattr(sv, "leer_estado", lambda k: mem.get(k))
    monkeypatch.setattr(sv, "_avisar_admins", lambda t, c: avisos.append((t, c)))
    import routers.evidencias_router as er
    monkeypatch.setattr(er, "copiar_videos_a_onedrive",
                        lambda **kw: copias.append(kw) or {"migrados": [1, 2], "errores": [], "pendientes_restantes": 5})
    return mem, avisos, copias


def test_ciclo_copia_solo_si_onedrive_sano_y_avisa_una_vez(ciclo_env, monkeypatch):
    mem, avisos, copias = ciclo_env
    estado = {"onedrive": OK, "auditoria": {**AUD0, "videos_solo_en_db": 88}, "problemas": []}
    monkeypatch.setattr(sv, "evaluar", lambda: dict(estado))
    r = sv.ciclo()
    assert len(copias) == 1 and copias[0]["limite"] == sv.COPIAR_POR_CICLO and r["copia_a_onedrive"]["migrados"] == 2
    assert avisos == []                                                          # todo bien: no molesta

    estado.update(onedrive=CAIDO, problemas=sv.problemas(CAIDO, AUD0))
    copias.clear(); sv.ciclo()
    assert copias == [] and len(avisos) == 1                                     # caído: no copia y avisa
    sv.ciclo()
    assert len(avisos) == 1                                                      # mismo problema: no repite


# ── validación en el servidor ────────────────────────────────────────────────
@pytest.fixture
def fin_env(monkeypatch):
    estado = {"evidencias": 0, "escrituras": []}
    def read(sql, p=None):
        if "COUNT(*) AS n FROM evidencias" in sql: return [{"n": estado["evidencias"]}]
        if "FROM asignaciones" in sql: return [{"unidad": "U1", "actividad_id": "Evidencia"}]
        return []
    monkeypatch.setattr(ar, "execute_read", read)
    monkeypatch.setattr(ar, "execute_write", lambda sql, p=None: estado["escrituras"].append(sql) or 1)
    monkeypatch.setattr(ar, "_notify", lambda *a, **k: None)
    return estado


def test_tecnico_no_puede_cerrar_tarea_sin_evidencia(fin_env):
    with pytest.raises(HTTPException) as e:
        ar.finalizar(5, {"comentario": "listo"}, {"username": "juan", "role": "tecnico"})
    assert e.value.status_code == 409 and not any("completada" in s for s in fin_env["escrituras"])


def test_con_evidencia_si_cierra_y_admin_puede_forzar(fin_env):
    fin_env["evidencias"] = 2
    assert ar.finalizar(5, {"comentario": "ok"}, {"username": "juan", "role": "tecnico"})["mensaje"]
    fin_env["evidencias"] = 0
    assert ar.finalizar(5, {"comentario": "ok", "forzar": True}, {"username": "root", "role": "admin"})["mensaje"]
    with pytest.raises(HTTPException):                      # 'forzar' no sirve a un técnico
        ar.finalizar(5, {"comentario": "ok", "forzar": True}, {"username": "juan", "role": "tecnico"})


# ── subida automática de videos de galería (JS real ejecutado con node) ──────────
@pytest.mark.skipif(not shutil.which("node"), reason="node no disponible")
def test_procesador_de_video_de_galeria(tmp_path):
    h = asyncio.run(wr.completar_tarea_html()) if hasattr(wr, "completar_tarea_html") else None
    src = open(wr.__file__, encoding="utf-8").read()
    a, b = src.index("window._galeriaVideos = window._galeriaVideos || {};"), src.index("function _equipoSeleccionado")
    js = """
const window = {}; const fetchAuth = async () => ({ok:true,json:async()=>({})}); const document = {getElementById:()=>null};
let comprimidos = 0, subidas = [], fallar = 0;
window.comprimirVideoGaleria = async (f, o) => { comprimidos++; o.onProgress(1); return { file: {size: 1000, name: f.name}, comprimido: true }; };
window.subirVideoResumible = async (file, o) => { subidas.push(o.clientId); if (fallar-- > 0) throw new Error('sin señal'); o.onProgress(1); return {evidenciaId: 9}; };
""" + src[a:b] + """
(async () => {
  const f = {name: 'v.mp4', size: 5e6, lastModified: 1}, ctx = {id: 7, unidad: 'U1', equipo: () => ''};
  const p1 = procesarVideoGaleria(f, ctx), p2 = procesarVideoGaleria(f, ctx);
  if (p1 !== p2) throw new Error('debe reutilizar la misma promesa (no subir dos veces)');
  await p1;
  if (comprimidos !== 1 || subidas.length !== 1) throw new Error('comprimió/subió más de una vez');
  await procesarVideoGaleria(f, ctx);
  if (subidas.length !== 1) throw new Error('un video ya subido no debe volver a subirse');
  // falla de red -> estado error -> se puede reintentar con el MISMO clientId (el servidor reanuda)
  const g = {name: 'w.mp4', size: 6e6, lastModified: 2}; fallar = 1;
  try { await procesarVideoGaleria(g, ctx); throw new Error('debía fallar'); } catch (e) { if (e.message === 'debía fallar') throw e; }
  await procesarVideoGaleria(g, ctx);
  if (subidas[1] !== subidas[2]) throw new Error('el reintento debe usar el mismo clientId');
  // servidor sin subida por partes -> método clásico
  window.subirVideoResumible = async () => { const e = new Error('x'); e.fallback = true; throw e; };
  const r = await procesarVideoGaleria({name: 'z.mp4', size: 7e6, lastModified: 3}, ctx);
  if (!r.fallback) throw new Error('debía pedir el método clásico');
  console.log('OK');
})().catch(e => { console.error(e.message); process.exit(1); });
"""
    f = tmp_path / "t.js"; f.write_text(js)
    r = subprocess.run(["node", str(f)], capture_output=True, text=True)
    assert r.returncode == 0 and "OK" in r.stdout, r.stderr


# ── el JavaScript YA RENDERIZADO de las páginas que tocamos debe ser válido ───────
@pytest.mark.skipif(not shutil.which("node"), reason="node no disponible")
def test_js_renderizado_de_admin_y_verificar_videos(tmp_path):
    import re
    htmls = {"admin": asyncio.run(wr.admin()).body.decode("utf-8"),
             "verificar": asyncio.run(wr.verificar_videos_page()).body.decode("utf-8"),
             "mis_tareas": asyncio.run(wr.mis_tareas()).body.decode("utf-8")}
    for nombre, h in htmls.items():
        for i, bloque in enumerate(re.findall(r"<script>(.*?)</script>", h, flags=re.S)):
            if len(bloque) < 2000:
                continue
            f = tmp_path / f"{nombre}_{i}.js"; f.write_text(bloque, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            assert r.returncode == 0, f"{nombre} script {i}: {r.stderr[:400]}"
