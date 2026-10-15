/**
 * video_upload.js — Subida de video por partes, reanudable e idempotente.
 *
 * window.subirVideoResumible(archivo, opciones) -> Promise<{evidenciaId}>
 *   opciones: { clientId, unidad, asignacionId, equipo, tecnico (solo admin), nombre, mime, onProgress(0..1), onEstado(texto) }
 *
 * Rechaza con un Error que puede traer:
 *   e.fallback   = true → el servidor no soporta subida por partes: usar /api/evidencias/upload
 *   e.permanente = true → error que reintentar no arregla (muy pesado, formato inválido…)
 * Cualquier otro rechazo = se agotaron los reintentos de esta ronda; el archivo NO se pierde:
 * volver a llamar con el mismo clientId continúa desde el último byte confirmado.
 */
(function () {
    var MAX_REINTENTOS_SEGUIDOS = 40;   // con espera creciente (tope 20 s) ≈ 10+ minutos sin señal
    var dormir = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };

    function esperarConexion() {
        if (navigator.onLine !== false) return Promise.resolve();
        return new Promise(function (resolve) {
            var h = function () { window.removeEventListener('online', h); resolve(); };
            window.addEventListener('online', h);
        });
    }

    function errorPermanente(msg) { var e = new Error(msg); e.permanente = true; return e; }

    async function detalle(res) {
        try { var j = await res.json(); return j.detail || ''; } catch (e) { return ''; }
    }

    window.subirVideoResumible = async function (archivo, op) {
        op = op || {};
        var total = archivo.size;
        var nombre = op.nombre || archivo.name || ('video_' + Date.now() + '.mp4');
        var uploadId = null, offset = 0, chunk = 3932160, fallos = 0;
        var estado = function (t) { if (op.onEstado) { try { op.onEstado(t); } catch (e) {} } };
        var progreso = function () { if (op.onProgress) { try { op.onProgress(total ? offset / total : 1); } catch (e) {} } };

        async function iniciar() {
            var res = await window.fetchAuth('/api/evidencias/video/iniciar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    client_id: op.clientId, unidad: op.unidad, asignacion_id: op.asignacionId != null ? Number(op.asignacionId) : null,
                    nombre: nombre, tamano: total, mime: op.mime || archivo.type || null, equipo: op.equipo || null,
                    tecnico: op.tecnico || null
                })
            });
            if (res.status === 503) { var f = new Error('Subida por partes no disponible'); f.fallback = true; throw f; }
            if (res.status === 400 || res.status === 403 || res.status === 422) {
                throw errorPermanente((await detalle(res)) || 'El servidor rechazó el video');
            }
            if (!res.ok) throw new Error('iniciar ' + res.status);
            return res.json();
        }

        while (true) {
            try {
                await esperarConexion();
                if (!uploadId) {
                    estado('Preparando subida…');
                    var ini = await iniciar();
                    if (ini.done) { offset = total; progreso(); return { evidenciaId: ini.evidencia_id }; }
                    uploadId = ini.upload_id; offset = ini.next_start || 0; chunk = ini.chunk_size || chunk;
                    progreso();
                }
                if (offset >= total) {   // todo enviado pero sin confirmación: preguntar al servidor
                    var st = await window.fetchAuth('/api/evidencias/video/' + uploadId + '/estado');
                    if (st.ok) { var sj = await st.json(); if (sj.done) { progreso(); return { evidenciaId: sj.evidencia_id }; } offset = sj.next_start; }
                    else if (st.status === 410 || st.status === 404) { uploadId = null; continue; }
                    else throw new Error('estado ' + st.status);
                }
                var fin = Math.min(offset + chunk, total);
                var res = await window.fetchAuth('/api/evidencias/video/' + uploadId + '/parte', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/octet-stream', 'X-Offset': String(offset) },
                    body: archivo.slice(offset, fin)
                });
                if (res.ok) {
                    var j = await res.json();
                    fallos = 0;
                    if (j.done) { offset = total; progreso(); return { evidenciaId: j.evidencia_id }; }
                    offset = (typeof j.next_start === 'number') ? j.next_start : fin;   // el servidor manda
                    progreso();
                    continue;
                }
                if (res.status === 410 || res.status === 404) { uploadId = null; continue; }   // sesión perdida: reabrir (mismo clientId)
                if (res.status === 400) throw errorPermanente((await detalle(res)) || 'Parte rechazada');
                throw new Error('parte ' + res.status);
            } catch (e) {
                if (e && (e.permanente || e.fallback)) throw e;
                fallos++;
                if (fallos >= MAX_REINTENTOS_SEGUIDOS) throw new Error('Sin conexión estable para subir el video');
                estado('Reintentando subida… (' + Math.round(total ? offset / total * 100 : 0) + '%)');
                await dormir(Math.min(1000 * Math.pow(1.6, fallos), 20000));
            }
        }
    };
})();
