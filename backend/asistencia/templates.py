# asistencia/templates.py
ASISTENCIA_STYLES = """
<style>
    .asistencia-container { max-width: 600px; margin: 0 auto; }
    .gps-status { position: fixed; top: 10px; right: 10px; background: #f0fdf4; padding: 8px 16px; border-radius: 50px; font-size: 0.75rem; font-weight: 600; z-index: 1000; }
    .gps-status.warning { background: #fef3c7; color: #92400e; }
    .gps-status.error { background: #fee2e2; color: #991b1b; }
    .selfie-preview { width: 120px; height: 120px; border-radius: 60px; object-fit: cover; margin: 10px auto; border: 3px solid #0057A8; cursor: pointer; }
    .camera-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 2000; display: none; flex-direction: column; justify-content: center; align-items: center; }
    .camera-modal video { max-width: 90%; border-radius: 12px; }
</style>
"""

def get_checkin_template() -> str:
    return """
    <script>if (window.role !== 'tecnico') { window.location.href = '/app/dashboard'; }</script>
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
    <div class="asistencia-container">
        <div id="gpsStatus" class="gps-status">📍 Obteniendo ubicación...</div>
        <div id="estadoInicial">
            <div class="evidencia-info" style="margin-bottom:20px; text-align:center;">
                <div style="font-size:3rem;">📍</div>
                <b>Registro de Asistencia</b><br>
                <span>Escanea el código QR de la oficina</span>
            </div>
            <div style="background:white; border-radius:16px; padding:20px;">
                <div class="section-title">📷 Escanear QR</div>
                <video id="qrVideo" style="width:100%; border-radius:10px; max-height:280px; background:#000;" autoplay playsinline></video>
                <canvas id="qrCanvasHidden" style="display:none;"></canvas>
                <p id="scanStatus">Iniciando cámara...</p>
                <button class="btn-primary" onclick="iniciarCamara()">🔄 Activar Cámara</button>
            </div>
        </div>
        <div id="estadoSelfie" style="display:none; text-align:center; background:white; border-radius:16px; padding:20px; margin-top:16px;">
            <div style="font-size:2.5rem;">📸</div>
            <h3>Toma una Selfie</h3>
            <p>Necesitamos una foto tuya para validar tu identidad.</p>
            <div id="selfiePreview"><img id="selfieImg" class="selfie-preview" style="display:none;"><div id="noSelfieMsg"><button class="btn-primary" onclick="abrirCamaraSelfie()">📸 Tomar Selfie</button></div></div>
            <button id="btnContinuar" class="btn-success" style="display:none;" onclick="procesarCheckinCompleto()">✅ Confirmar</button>
        </div>
        <div id="estadoProcesando" style="display:none; text-align:center; padding:40px;"><div style="font-size:3rem;">⏳</div><p>Registrando...</p></div>
        <div id="estadoResultado" style="display:none; text-align:center;"></div>
    </div>
    <div id="cameraModal" class="camera-modal">
        <video id="selfieVideo" autoplay playsinline></video>
        <div style="margin-top:20px;"><button class="btn-primary" onclick="tomarSelfie()">📸 Tomar Foto</button><button class="btn-danger" onclick="cerrarCamaraSelfie()">Cancelar</button></div>
    </div>
    <script>
        let streamQR = null, streamSelfie = null, scanLoop = null, qrData = null, ubicacionActual = null, gpsPrecision = null, selfieBase64 = null;
        const fetchAuth = window.fetchAuth;
        
        function obtenerUbicacion() {
            const status = document.getElementById('gpsStatus');
            if (!navigator.geolocation) { status.textContent = '❌ GPS no soportado'; status.className = 'gps-status error'; return; }
            navigator.geolocation.getCurrentPosition(
                pos => {
                    ubicacionActual = { lat: pos.coords.latitude, lon: pos.coords.longitude };
                    gpsPrecision = pos.coords.accuracy;
                    if (gpsPrecision <= 50) status.innerHTML = `📍 GPS preciso (${gpsPrecision.toFixed(1)}m)`;
                    else { status.innerHTML = `⚠️ GPS poco preciso (${gpsPrecision.toFixed(1)}m) - Acércate a una ventana`; status.className = 'gps-status warning'; }
                },
                err => { status.innerHTML = '❌ No se pudo obtener ubicación'; status.className = 'gps-status error'; },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }
        
        function iniciarCamara() {
            if (streamQR) streamQR.getTracks().forEach(t => t.stop());
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    streamQR = stream;
                    const video = document.getElementById('qrVideo');
                    video.srcObject = stream;
                    video.play();
                    if (scanLoop) clearInterval(scanLoop);
                    scanLoop = setInterval(() => {
                        const video = document.getElementById('qrVideo');
                        const canvas = document.getElementById('qrCanvasHidden');
                        if (video.readyState !== video.HAVE_ENOUGH_DATA) return;
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        const code = jsQR(ctx.getImageData(0, 0, canvas.width, canvas.height).data, canvas.width, canvas.height);
                        if (code) {
                            clearInterval(scanLoop);
                            if (streamQR) streamQR.getTracks().forEach(t => t.stop());
                            try {
                                const url = new URL(code.data);
                                const token = url.searchParams.get('token');
                                if (!token) throw new Error();
                                qrData = { token };
                                document.getElementById('scanStatus').textContent = '✅ QR válido';
                                document.getElementById('estadoInicial').style.display = 'none';
                                document.getElementById('estadoSelfie').style.display = 'block';
                            } catch(e) { document.getElementById('scanStatus').textContent = '❌ QR inválido'; iniciarCamara(); }
                        }
                    }, 400);
                })
                .catch(() => document.getElementById('scanStatus').textContent = '⚠️ No se pudo acceder a la cámara');
        }
        
        function abrirCamaraSelfie() {
            const modal = document.getElementById('cameraModal');
            const video = document.getElementById('selfieVideo');
            modal.style.display = 'flex';
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
                .then(stream => { streamSelfie = stream; video.srcObject = stream; video.play(); });
        }
        
        function cerrarCamaraSelfie() {
            document.getElementById('cameraModal').style.display = 'none';
            if (streamSelfie) streamSelfie.getTracks().forEach(t => t.stop());
        }
        
        function tomarSelfie() {
            const video = document.getElementById('selfieVideo');
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            selfieBase64 = canvas.toDataURL('image/jpeg', 0.8);
            document.getElementById('selfieImg').src = selfieBase64;
            document.getElementById('selfieImg').style.display = 'block';
            document.getElementById('noSelfieMsg').style.display = 'none';
            document.getElementById('btnContinuar').style.display = 'block';
            cerrarCamaraSelfie();
        }
        
        async function procesarCheckinCompleto() {
            if (!ubicacionActual) return alert('Esperando ubicación GPS...');
            if (!selfieBase64) return alert('Debes tomarte una selfie');
            if (!qrData) return alert('QR inválido. Escanea nuevamente.');
            
            document.getElementById('estadoSelfie').style.display = 'none';
            document.getElementById('estadoProcesando').style.display = 'block';
            
            try {
                const res = await fetchAuth('/api/asistencia/registrar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        token: qrData.token,
                        lat_tecnico: ubicacionActual.lat,
                        lon_tecnico: ubicacionActual.lon,
                        selfie_base64: selfieBase64,
                        gps_accuracy: gpsPrecision
                    })
                });
                const data = await res.json();
                mostrarResultado(res.ok, data.mensaje);
            } catch(err) { mostrarResultado(false, err.message); }
        }
        
        function mostrarResultado(exito, mensaje) {
            document.getElementById('estadoProcesando').style.display = 'none';
            const el = document.getElementById('estadoResultado');
            el.style.display = 'block';
            el.innerHTML = `<div style="background:${exito ? '#dcfce7' : '#fee2e2'}; border-radius:20px; padding:32px;"><div style="font-size:4rem;">${exito ? '✅' : '❌'}</div><h2>${exito ? '¡Asistencia Registrada!' : 'Error'}</h2><p>${mensaje}</p><button class="btn-primary" onclick="window.location.href='/app/mis-tareas'">Ir a Mis Tareas</button></div>`;
        }
        
        obtenerUbicacion();
        iniciarCamara();
        setInterval(obtenerUbicacion, 10000);
    </script>
    """
