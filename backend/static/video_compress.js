/*
 * video_compress.js — Compresión automática de videos elegidos desde la galería.
 *
 * Se ejecuta en el celular (WebCodecs, con el codificador por hardware del equipo)
 * ANTES de subir el archivo, así nunca viaja el video original pesado.
 *
 * Uso:
 *   const r = await window.comprimirVideoGaleria(file, { onProgress: p => ... });
 *   // r = { file, comprimido, motivo, bytesAntes, bytesDespues, duracion }
 *   //   r.file         -> File listo para subir (el original si no se pudo comprimir)
 *   //   r.comprimido   -> true si se re-codificó
 *   //   r.motivo       -> 'ok' | 'ya-liviano' | 'sin-webcodecs' | 'sin-libreria' |
 *   //                     'sin-video' | 'sin-codec' | 'no-mejora' | 'error' | 'timeout'
 *
 * Nunca lanza excepción: si algo falla devuelve el archivo original y el motivo.
 * La librería (mediabunny, MPL-2.0) va incluida en /static/vendor/ para no
 * depender de ningún CDN.
 */
(function () {
    'use strict';

    var MB = 1024 * 1024;

    var CFG = {
        maxBytes: 70 * MB,          // objetivo de salida: por debajo del tope de 80 MB del servidor
        umbralBytes: 12 * MB,       // videos más chicos que esto se suben tal cual
        maxLado: 1280,              // lado más largo en px (720p)
        maxFps: 30,
        bitrateMax: 2500000,        // 2.5 Mbps  -> ~19 MB por minuto
        bitrateMin: 350000,         // piso para videos muy largos
        audioBitrate: 96000,
        margen: 0.92,               // deja 8% de holgura por contenedor/audio
        stallMs: 60000,             // si no hay progreso en 60 s, se cancela y se sube el original
        libUrl: '/static/vendor/mediabunny.min.mjs?v=1.61.0'
    };

    var _libPromise = null;

    function soportado() {
        return typeof VideoEncoder !== 'undefined' &&
               typeof VideoDecoder !== 'undefined' &&
               typeof VideoFrame !== 'undefined';
    }

    function cargarLib() {
        if (!_libPromise) {
            _libPromise = import(CFG.libUrl).catch(function (e) {
                _libPromise = null;   // permite reintentar
                throw e;
            });
        }
        return _libPromise;
    }

    function par(n) {            // los codificadores de video piden dimensiones pares
        n = Math.max(2, Math.round(n));
        return n % 2 === 0 ? n : n - 1;
    }

    function nombreSalida(nombreOriginal, ext) {
        var base = (nombreOriginal || 'video').replace(/\.[^.]+$/, '');
        return base + '_comp.' + ext;
    }

    async function pedirWakeLock() {
        try {
            if (navigator.wakeLock && navigator.wakeLock.request) {
                return await navigator.wakeLock.request('screen');
            }
        } catch (e) { /* no crítico */ }
        return null;
    }

    async function comprimirVideoGaleria(file, opts) {
        opts = opts || {};
        var onProgress = typeof opts.onProgress === 'function' ? opts.onProgress : function () {};
        var maxBytes = opts.maxBytes || CFG.maxBytes;
        var umbral = opts.umbralBytes != null ? opts.umbralBytes : CFG.umbralBytes;

        function res(f, comprimido, motivo, extra) {
            var r = { file: f, comprimido: comprimido, motivo: motivo, bytesAntes: file.size, bytesDespues: f.size };
            if (extra) { for (var k in extra) { r[k] = extra[k]; } }
            return r;
        }

        if (file.size <= umbral) return res(file, false, 'ya-liviano');
        if (!soportado()) return res(file, false, 'sin-webcodecs');

        var mb;
        try { mb = await cargarLib(); }
        catch (e) { console.warn('[video] no se pudo cargar la librería de compresión:', e); return res(file, false, 'sin-libreria'); }

        var input = null, conversion = null, wake = null, watchdog = null, cancelado = false;
        try {
            input = new mb.Input({ source: new mb.BlobSource(file), formats: mb.ALL_FORMATS });

            var track = await input.getPrimaryVideoTrack();
            if (!track) return res(file, false, 'sin-video');

            var duracion = await input.computeDuration();
            if (!isFinite(duracion) || duracion <= 0) duracion = 60;

            // ── Dimensiones de salida (máx. 720p en el lado largo, sin agrandar) ──
            var w = track.displayWidth, h = track.displayHeight;
            var escala = Math.min(1, CFG.maxLado / Math.max(w, h));
            var outW = par(w * escala), outH = par(h * escala);

            // ── FPS: solo se reduce si el original supera 30 ──
            var fpsOut;
            var bitrateOriginal = 0;
            try {
                var stats = await track.computePacketStats(120);
                if (stats && stats.averagePacketRate > CFG.maxFps + 1) fpsOut = CFG.maxFps;
                if (stats && stats.averageBitrate) bitrateOriginal = stats.averageBitrate;
            } catch (e) { /* sin estadísticas: se usan valores por defecto */ }

            // ── Bitrate para que el resultado quepa en maxBytes ──
            var presupuestoBps = (maxBytes * 8 * CFG.margen) / duracion;
            var videoBps = Math.floor(presupuestoBps - CFG.audioBitrate);
            videoBps = Math.min(videoBps, CFG.bitrateMax);
            if (bitrateOriginal) videoBps = Math.min(videoBps, Math.floor(bitrateOriginal * 0.7));
            videoBps = Math.max(videoBps, CFG.bitrateMin);

            // ── Códec: H.264/MP4 (se reproduce en todos lados); VP9/VP8 en WebM como respaldo ──
            var codec = await mb.getFirstEncodableVideoCodec(['avc', 'vp9', 'vp8'], {
                width: outW, height: outH, quality: new mb.Quality({ bitrate: videoBps })
            });
            if (!codec) return res(file, false, 'sin-codec');
            var esMp4 = (codec === 'avc');

            var output = new mb.Output({
                format: esMp4 ? new mb.Mp4OutputFormat() : new mb.WebMOutputFormat(),
                target: new mb.BufferTarget()
            });

            var videoOpts = {
                width: outW,
                height: outH,
                fit: 'fill',                       // ya calculamos dimensiones con la misma proporción
                codec: codec,
                quality: new mb.Quality({ bitrate: videoBps }),
                keyFrameInterval: 2,
                forceTranscode: true
            };
            if (fpsOut) videoOpts.frameRate = fpsOut;

            conversion = await mb.Conversion.init({
                input: input,
                output: output,
                video: videoOpts,
                audio: { quality: new mb.Quality({ bitrate: CFG.audioBitrate }) },
                showWarnings: false
            });

            if (!conversion.isValid) {
                console.warn('[video] conversión inválida:', conversion.discardedTracks);
                return res(file, false, 'error');
            }

            // ── Progreso + vigilante de bloqueo ──
            var ultimoProgreso = Date.now();
            conversion.onProgress = function (p) {
                ultimoProgreso = Date.now();
                try { onProgress(Math.max(0, Math.min(1, p))); } catch (e) {}
            };
            watchdog = setInterval(function () {
                if (Date.now() - ultimoProgreso > CFG.stallMs) {
                    cancelado = true;
                    try { conversion.cancel(); } catch (e) {}
                }
            }, 5000);

            wake = await pedirWakeLock();
            await conversion.execute();

            var buffer = output.target.buffer;
            if (!buffer || !buffer.byteLength) return res(file, false, 'error');

            var tipo = esMp4 ? 'video/mp4' : 'video/webm';
            var comprimidoFile = new File([buffer], nombreSalida(file.name, esMp4 ? 'mp4' : 'webm'),
                                          { type: tipo, lastModified: Date.now() });

            // Si por alguna razón quedó igual o más pesado, se conserva el original.
            if (comprimidoFile.size >= file.size) {
                return res(file, false, 'no-mejora', { duracion: duracion });
            }
            onProgress(1);
            return res(comprimidoFile, true, 'ok', { duracion: duracion, codec: codec, videoBps: videoBps });

        } catch (e) {
            console.warn('[video] falló la compresión, se usará el original:', e);
            return res(file, false, cancelado ? 'timeout' : 'error');
        } finally {
            if (watchdog) clearInterval(watchdog);
            try { if (wake && wake.release) await wake.release(); } catch (e) {}
            try { if (input) input.dispose(); } catch (e) {}
        }
    }

    window.videoCompressSoportado = soportado;
    window.comprimirVideoGaleria = comprimirVideoGaleria;
    window.VIDEO_COMPRESS_CFG = CFG;
})();
