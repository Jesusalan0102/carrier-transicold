"""El panel y la página Verificar videos traen el visor de evidencia (y su JS es válido)."""
import asyncio, re, shutil, subprocess
import pytest
from routers import web_router as wr


def _html(resp):
    return resp.body.decode("utf-8")


def test_actividades_tiene_boton_ver_evidencia_y_modal():
    h = _html(asyncio.run(wr.admin()))
    assert "verEvidenciaTarea(${r.id})" in h and 'id="te-modal"' in h
    assert "/api/evidencias/por-actividad/" in h and "Descargar" in h
    assert 'id="ev-filtro-tipo"' in h and "evCambioUnidad()" in h


def test_verificar_videos_tiene_reproductor():
    h = _html(asyncio.run(wr.verificar_videos_page()))
    assert "vvVer(" in h and 'id="vvVideo"' in h and "Descargar video" in h


@pytest.mark.skipif(not shutil.which("node"), reason="node no disponible")
def test_js_del_visor_es_valido(tmp_path):
    h = _html(asyncio.run(wr.admin()))
    a, b = h.index("let teUrls = [];"), h.index("function evCloseLightbox")
    f = tmp_path / "te.js"
    f.write_text("(function(){const DATA={act:[]},fetchAuth=()=>{},showTab=()=>{},evCambioUnidad=()=>{};\n" + h[a:b] + "\n})();")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
