from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

# ------------------------------------------------------------
# ESTILOS GLOBALES PREMIUM
# ------------------------------------------------------------
BASE_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --carrier-blue: #002B5B;
        --carrier-accent: #0057A8;
        --carrier-light: #E8F0FB;
        --carrier-success: #16a34a;
        --carrier-warn: #d97706;
        --carrier-danger: #dc2626;
    }
    * { box-sizing: border-box; font-family: 'Inter', sans-serif; }
    body {
        background: linear-gradient(135deg, #EEF2F9 0%, #F5F7FB 60%, #EAF0FB 100%);
        margin: 0; padding: 0;
    }
    /* ... (mantengo todos tus estilos originales) ... */
    .sidebar { background: linear-gradient(180deg, var(--carrier-blue) 0%, #01418a 60%, #0056b3 100%); color: white; width: 21rem; height: 100vh; position: fixed; top: 0; left: 0; padding: 1.5rem 1rem; box-shadow: 4px 0 20px rgba(0,0,0,0.1); z-index: 100; overflow-y: auto; display: flex; flex-direction: column; }
    .main-content { margin-left: 21rem; padding: 2rem; min-height: 100vh; }
    /* ... resto de tus estilos ... (para no hacer el mensaje eterno, asumo que los mantienes tal cual) */
</style>
"""

# ------------------------------------------------------------
# FUNCIÓN pagina_con_menu (mantengo la tuya original)
# ------------------------------------------------------------
def pagina_con_menu(titulo: str, contenido: str, pagina_activa: str = "", extra_scripts: str = "") -> str:
    # ... tu función original completa ...
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titulo} – Carrier Transicold</title>
        {BASE_STYLE}
        <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
        <script>
            window.token = localStorage.getItem('access_token');
            window.role = localStorage.getItem('role');
            window.username = localStorage.getItem('username');
            if (!window.token) {{
                window.location.href = '/app';
            }}
            window.fetchAuth = async (url, options) => {{
                options = options || {{}};
                const headers = options.headers || {{}};
                headers['Authorization'] = 'Bearer ' + window.token;
                const res = await fetch(url, {{ ...options, headers }});
                if (res.status === 401) {{
                    localStorage.clear();
                    window.location.href = '/app';
                }}
                return res;
            }};
        </script>
    </head>
    <body>
        <!-- ... todo tu HTML de sidebar y menú (mantengo tu código original) ... -->
        <div class="main-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; flex-wrap:wrap; gap:12px;">
                <h1 class="main-header">{titulo}</h1>
                <div id="liveClock" class="time-badge"></div>
            </div>
            {contenido}
        </div>
        <!-- scripts globales -->
        {extra_scripts}
    </body>
    </html>
    """

# ... (todas tus otras rutas: login, dashboard, asignaciones, tickets, inventario, unidades, usuarios, admin, mis-tareas, etc. se mantienen igual) ...

# ============================================================
# ASISTENCIA ADMIN - VERSIÓN CORREGIDA
# ============================================================
@router.get("/app/asistencia", response_class=HTMLResponse)
async def asistencia_admin():
    contenido = """
    <script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>
    <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
    <style>
        .tab-btn { background:white; border:1.5px solid #e5e7eb; border-radius:10px; padding:10px 24px; font-weight:600; font-size:.9rem; color:#6b7280; cursor:pointer; transition:.2s; }
        .tab-btn.active { background:#002B5B; color:white; border-color:#002B5B; }
        .tab-panel { display:none; }
        .tab-panel.active { display:block; }
        .horario-tbl { width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,43,91,0.08); font-size:.85rem; }
        .horario-tbl th { background:#002B5B; color:white; padding:10px 12px; text-align:center; white-space:nowrap; }
        .horario-tbl th:first-child { text-align:left; }
        .horario-tbl td { padding:8px 12px; border-bottom:1px solid #f0f2f5; text-align:center; }
        .horario-tbl td:first-child { font-weight:600; text-align:left; }
        .horario-tbl input[type=time] { border:1px solid #d1d5db; border-radius:6px; padding:4px 8px; font-size:.82rem; width:90px; margin-bottom:0; }
        .est-completo  { background:#dcfce7; color:#16a34a; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-retardo   { background:#fef3c7; color:#d97706; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-ausente   { background:#fee2e2; color:#dc2626; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-libre     { background:#f3f4f6; color:#9ca3af; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-sin_salida { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
    </style>

    <div style="display:flex; gap:10px; margin-bottom:28px; flex-wrap:wrap;">
        <button class="tab-btn active" onclick="switchTab('tab-qr',this)">📲 QR de Asistencia</button>
        <button class="tab-btn" onclick="switchTab('tab-horarios',this)">📅 Horario Semanal</button>
        <button class="tab-btn" onclick="switchTab('tab-registros',this)">📋 Registros del Día</button>
    </div>

    <!-- TAB QR -->
    <div id="tab-qr" class="tab-panel active">
        <div class="evidencia-info" style="margin-bottom:20px;">
            <b>📍 Geoposición del punto de asistencia</b><br>
            <span style="font-size:.85rem;">Define las coordenadas del lugar de trabajo. El técnico deberá estar dentro del radio al escanear.</span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:20px;">
            <div><label>Latitud</label><input type="number" id="latFija" step="0.000001" value="32.5027"></div>
            <div><label>Longitud</label><input type="number" id="lonFija" step="0.000001" value="-117.0037"></div>
            <div><label>Radio (metros)</label><input type="number" id="radioMetros" value="200" min="10" max="5000"></div>
        </div>
        <div style="display:flex; gap:12px; margin-bottom:28px;">
            <button class="btn-primary" onclick="generarQR()">🔄 Generar QR</button>
            <button class="btn-warning" onclick="usarUbicacionActual()">📡 Usar mi ubicación</button>
        </div>
        <div id="qrSection" style="display:none;">
            <div class="section-title">📲 QR Generado</div>
            <div style="display:flex; gap:32px; align-items:flex-start; flex-wrap:wrap;">
                <div style="background:white; padding:24px; border-radius:16px; box-shadow:0 4px 20px rgba(0,43,91,0.1); text-align:center;">
                    <div id="qrCanvas"></div>
                    <p>Expira en <b id="qrTimer">05:00</b></p>
                    <button class="btn-primary" onclick="generarQR()">🔁 Regenerar</button>
                </div>
                <div>
                    <p><b>Lat:</b> <span id="qrLatLabel"></span></p>
                    <p><b>Lon:</b> <span id="qrLonLabel"></span></p>
                    <p><b>Radio:</b> <span id="qrRadioLabel"></span> m</p>
                    <div id="mapaLink"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB HORARIOS Y REGISTROS (mantengo tu estructura) -->
    <div id="tab-horarios" class="tab-panel"> ... (tu código de horarios) ... </div>
    <div id="tab-registros" class="tab-panel"> ... (tu código de registros) ... </div>

    <script>
        console.log('✅ Script de Asistencia cargado');

        function switchTab(id, btn) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            btn.classList.add('active');
            if (id === 'tab-registros') cargarRegistros();
        }

        function fechaLocalHoy() {
            const d = new Date();
            return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
        }

        document.getElementById('fechaFiltro').value = fechaLocalHoy();

        let timerInterval = null;

        function generarQR() {
            const lat = parseFloat(document.getElementById('latFija').value);
            const lon = parseFloat(document.getElementById('lonFija').value);
            const radio = parseInt(document.getElementById('radioMetros').value);
            if (isNaN(lat) || isNaN(lon)) return alert('Latitud y Longitud son obligatorias');

            const token = btoa(`asistencia:${lat}:${lon}:${radio}:${Date.now()}`);
            const url = `${window.location.origin}/app/checkin?token=${encodeURIComponent(token)}&lat=${lat}&lon=${lon}&radio=${radio}`;

            document.getElementById('qrCanvas').innerHTML = '';
            new QRCode(document.getElementById('qrCanvas'), {
                text: url,
                width: 220,
                height: 220,
                colorDark: '#002B5B',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            });

            document.getElementById('qrLatLabel').textContent = lat;
            document.getElementById('qrLonLabel').textContent = lon;
            document.getElementById('qrRadioLabel').textContent = radio;
            document.getElementById('mapaLink').innerHTML = `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank">🗺 Ver en Google Maps</a>`;

            document.getElementById('qrSection').style.display = 'block';

            if (timerInterval) clearInterval(timerInterval);
            let seg = 300;
            timerInterval = setInterval(() => {
                seg--;
                const m = String(Math.floor(seg/60)).padStart(2,'0');
                const s = String(seg%60).padStart(2,'0');
                document.getElementById('qrTimer').textContent = m + ':' + s;
            }, 1000);
        }

        function usarUbicacionActual() {
            if (!navigator.geolocation) return alert('Geolocalización no soportada');
            navigator.geolocation.getCurrentPosition(p => {
                document.getElementById('latFija').value = p.coords.latitude.toFixed(6);
                document.getElementById('lonFija').value = p.coords.longitude.toFixed(6);
            });
        }

        async function cargarRegistros() {
            const fecha = document.getElementById('fechaFiltro').value;
            try {
                const res = await fetchAuth(`/api/asistencia/registros?fecha=${fecha}`);
                const data = await res.json();
                let html = `<table><thead><tr><th>Técnico</th><th>Tipo</th><th>Hora</th><th>Distancia</th><th>Estado</th></tr></thead><tbody>`;
                data.forEach(r => {
                    const est = r.aprobado ? '✅ Dentro' : '❌ Fuera';
                    html += `<tr><td>${r.username}</td><td>${r.tipo}</td><td>${r.hora_checkin||'—'}</td><td>${r.distancia_metros||'—'}m</td><td>${est}</td></tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('tablaAsistencia').innerHTML = html || '<p>Sin registros</p>';
            } catch(e) {
                console.error(e);
                document.getElementById('tablaAsistencia').innerHTML = '<p style="color:red;">Error al cargar</p>';
            }
        }

        // Carga inicial
        setTimeout(cargarRegistros, 800);
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Control de Asistencia", contenido, "asistencia"))
