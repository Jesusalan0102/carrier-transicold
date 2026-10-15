"""Admin: arrastrar / pegar / elegir archivos en la evidencia de una tarea (JS real ejecutado con node)."""
import asyncio, shutil, subprocess
import pytest
from routers import web_router as wr


def _bloque():
    h = asyncio.run(wr.admin()).body.decode("utf-8")
    a, b = h.index("let teTarea = null;"), h.index("window.addEventListener('load', teIniciarSubida);")
    return h[a:b]


@pytest.mark.skipif(not shutil.which("node"), reason="node no disponible")
def test_cola_de_evidencia_del_admin(tmp_path):
    js = """
const window = { role: 'admin', username: 'admin', addEventListener(){}, subirVideoResumible: null };
const els = { 'te-modal': {style: {display: 'flex'}} };
const document = { getElementById: id => els[id] || null, createElement: () => ({style:{}, appendChild(){}}) };
let subidas = [], refrescos = [], llamadasVideo = [], respuesta = {ok: true, status: 200, json: async () => ({guardadas: 1})};
const fetchAuth = async (url, init) => { subidas.push({url, tecnico: init.body.get('tecnico'), tarea: init.body.get('asignacion_id'),
                                                       unidad: init.body.get('unidad'), nombre: init.body.get('files').name}); return respuesta; };
const verEvidenciaTarea = (id, o) => refrescos.push([id, o]);
""" + _bloque() + """
const esperar = async () => { for (let i = 0; i < 50 && (teTrabajando || teCola.some(x => x.estado === 'espera')); i++) await new Promise(r => setTimeout(r, 5)); await new Promise(r => setTimeout(r, 5)); };
const mk = (n, t, size = 10, lm = 1) => { const f = new File([new Uint8Array(size)], n, {type: t}); Object.defineProperty(f, 'lastModified', {value: lm}); return f; };
(async () => {
  teTarea = { id: 7, unidad: 'CW1', tecnico: 'maria' };
  // 1) foto + video + PDF (rechazado) + foto repetida
  window.subirVideoResumible = async (f, o) => { llamadasVideo.push(o); o.onProgress(1); return {evidenciaId: 1}; };
  const foto = mk('a.png', 'image/png');
  teAgregar([foto, mk('v.mp4', 'video/mp4', 50), mk('doc.pdf', 'application/pdf'), foto]);
  await esperar();
  if (teCola.length !== 2) throw new Error('debían quedar 2 en cola (pdf y repetida fuera): ' + teCola.length);
  if (subidas.length !== 1 || subidas[0].tecnico !== 'maria' || subidas[0].tarea !== '7' || subidas[0].unidad !== 'CW1' || subidas[0].url !== '/api/evidencias/upload')
      throw new Error('la foto debe subirse a nombre del técnico de la tarea: ' + JSON.stringify(subidas));
  if (llamadasVideo.length !== 1 || llamadasVideo[0].tecnico !== 'maria' || llamadasVideo[0].asignacionId !== 7 || !llamadasVideo[0].clientId.startsWith('a_7_'))
      throw new Error('el video debe ir por partes, a nombre del técnico');
  if (!teCola.every(x => x.estado === 'ok')) throw new Error('todo debía quedar ok');
  if (refrescos.length !== 1 || !refrescos[0][1].silencioso) throw new Error('debe refrescar la galería UNA vez, sin reabrir el video');
  // 2) error del servidor: se muestra el motivo y no se refresca
  respuesta = {ok: false, status: 400, json: async () => ({detail: 'Ya alcanzaste el límite de 100 fotos para esta actividad'})};
  teAgregar([mk('b.jpg', 'image/jpeg', 11)]); await esperar();
  const ult = teCola[teCola.length - 1];
  if (ult.estado !== 'error' || !ult.texto.includes('límite de 100')) throw new Error('debía mostrar el error del servidor: ' + ult.texto);
  // 3) servidor sin subida por partes -> el video se manda por el método clásico
  respuesta = {ok: true, status: 200, json: async () => ({guardadas: 1})};
  window.subirVideoResumible = async () => { const e = new Error('x'); e.fallback = true; throw e; };
  const antes = subidas.length;
  teAgregar([mk('w.mov', 'video/quicktime', 60)]); await esperar();
  if (subidas.length !== antes + 1 || teCola[teCola.length - 1].estado !== 'ok') throw new Error('el respaldo clásico no funcionó');
  // 4) nombres de capturas pegadas: únicos
  const n1 = teNombrePegado({type: 'image/png'}), n2 = teNombrePegado({type: 'image/png'});
  if (n1 === n2 || !n1.startsWith('pegado_') || !n1.endsWith('.png')) throw new Error('nombres pegados: ' + n1 + ' ' + n2);
  console.log('OK');
})().catch(e => { console.error(e.message); process.exit(1); });
"""
    f = tmp_path / "t.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True)
    assert r.returncode == 0 and "OK" in r.stdout, r.stderr
