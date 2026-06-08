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
    body { background: linear-gradient(135deg, #EEF2F9 0%, #F5F7FB 60%, #EAF0FB 100%); margin: 0; padding: 0; }
    .sidebar { background: linear-gradient(180deg, var(--carrier-blue) 0%, #01418a 60%, #0056b3 100%); color: white; width: 21rem; height: 100vh; position: fixed; top: 0; left: 0; padding: 1.5rem 1rem; box-shadow: 4px 0 20px rgba(0,0,0,0.1); z-index: 100; overflow-y: auto; display: flex; flex-direction: column; }
    .main-content { margin-left: 21rem; padding: 2rem; min-height: 100vh; }
    .main-header { font-size: 1.75rem; font-weight: 800; color: var(--carrier-blue); border-bottom: 3px solid var(--carrier-accent); padding-bottom: 12px; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
    .section-title { font-size: 0.92rem; font-weight: 700; color: var(--carrier-blue); border-left: 4px solid var(--carrier-accent); padding: 9px 14px; margin: 22px 0 14px 0; background: white; border-radius: 0 8px 8px 0; box-shadow: 0 2px 8px rgba(0,43,91,0.07); }
    .time-badge { background: var(--carrier-blue); color: white; padding: 6px 16px; border-radius: 24px; font-size: 0.82rem; font-weight: 600; box-shadow: 0 2px 8px rgba(0,43,91,0.25); display: inline-block; }
    .btn-primary { background: linear-gradient(135deg, var(--carrier-blue) 0%, var(--carrier-accent) 100%); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    .btn-warning { background: var(--carrier-warn); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    input, select { border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; font-size: 16px; width: 100%; margin-bottom: 12px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,43,91,0.08); }
    th { background: #f8fafc; padding: 12px; text-align: left; font-weight: 600; color: var(--carrier-blue); border-bottom: 2px solid #e5e7eb; }
    td { padding: 12px; border-bottom: 1px solid #f0f0f0; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
</style>
"""

def pagina_con_menu(titulo: str, contenido: str, pagina_activa: str = "", extra_scripts: str = "") -> str:
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
            if (!window.token) window.location.href = '/app';
            window.fetchAuth = async (url, options = {{}}) => {{
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
        <div class="main-content">
            <h1 class="main-header">{titulo}</h1>
            {contenido}
        </div>
        {extra_scripts}
    </body>
    </html>
    """

# ============================================================
# ASISTENCIA - VERSIÓN CORREGIDA (SIN ERRORES DE SINTAXIS)
# ============================================================
@router.get("/app/asistencia", response_class=HTMLResponse)
async def asistencia_admin():
    contenido = """
    <script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>
    <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>

    <style>
        .tab-btn { background:white; border:1.5px solid #e5e7eb; border-radius:10px; padding:10px 24px; font-weight:600; font-size:0.9rem; color:#6b7280; cursor:pointer; }
        .tab-btn.active { background:#002B5B; color:white; border-color:#002B5B; }
        .tab-panel { display:none; }
        .tab-panel.active { display:block; }
    </style>

    <div style="display:flex; gap:10px; margin-bottom:28px; flex-wrap:wrap;">
        <button class="tab-btn active" onclick="switchTab('tab-qr', this)">📲 QR de Asistencia</button>
        <button class="tab-btn" onclick="switchTab('tab-registros', this)">📋 Registros del Día</button>
    </div>

    <!-- TAB QR -->
    <div id="tab-qr" class="tab-panel active">
        <div style="background:#eff6ff; padding:16px; border-radius:12px; margin-bottom:20px;">
            <b>📍 Geoposición del punto de asistencia</b><br>
            Define las coordenadas del lugar de trabajo.
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:20px;">
            <div><label>Latitud</label><input type="number" id="latFija" step="0.000001" value="32.5027"></div>
            <div><label>Longitud</label><input type="number" id="lonFija" step="0.000001" value="-117.0037"></div>
            <div><label>Radio (metros)</label><input type="number" id="radioMetros" value="200"></div>
        </div>
        <button class="btn-primary" onclick="generarQR()" style="width:auto; padding:12px 32px;">🔄 Generar QR</button>
        <button class="btn-warning" onclick="usarUbicacionActual()" style="width:auto; padding:12px 32px; margin-left:12px;">📍 Usar mi ubicación</button>

        <div id="qrSection" style="display:none; margin-top:32px; text-align:center;">
            <div id="qrCanvas" style="margin:0 auto; background:white; padding:20px; border-radius:16px; display:inline-block;"></div>
            <p style="margin-top:12px;">Expira en <b id="qrTimer">05:00</b></p>
        </div>
    </div>

    <!-- TAB REGISTROS -->
    <div id="tab-registros" class="tab-panel">
        <input type="date" id="fechaFiltro" onchange="cargarRegistros()">
        <button class="btn-primary" onclick="cargarRegistros()">Actualizar</button>
        <div id="tablaAsistencia" style="margin-top:20px;"></div>
    </div>

    <script>
        console.log("✅ Script de Asistencia cargado correctamente");

        function switchTab(tabId, btn) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
            if (tabId === 'tab-registros') cargarRegistros();
        }

        function generarQR() {
            const lat = parseFloat(document.getElementById('latFija').value);
            const lon = parseFloat(document.getElementById('lonFija').value);
            const radio = parseInt(document.getElementById('radioMetros').value);

            if (isNaN(lat) || isNaN(lon)) return alert("Ingresa latitud y longitud");

            const url = `${window.location.origin}/app/checkin?lat=${lat}&lon=${lon}&radio=${radio}`;
            document.getElementById('qrCanvas').innerHTML = '';
            new QRCode(document.getElementById('qrCanvas'), {
                text: url,
                width: 256,
                height: 256,
                colorDark: "#002B5B",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
            document.getElementById('qrSection').style.display = 'block';
        }

        function usarUbicacionActual() {
            if (!navigator.geolocation) return alert("Geolocalización no soportada");
            navigator.geolocation.getCurrentPosition(pos => {
                document.getElementById('latFija').value = pos.coords.latitude.toFixed(6);
                document.getElementById('lonFija').value = pos.coords.longitude.toFixed(6);
            });
        }

        async function cargarRegistros() {
            const fecha = document.getElementById('fechaFiltro').value || new Date().toISOString().split('T')[0];
            try {
                const res = await fetchAuth(`/api/asistencia/registros?fecha=${fecha}`);
                const data = await res.json();
                let html = `<table><thead><tr><th>Técnico</th><th>Tipo</th><th>Hora</th><th>Estado</th></tr></thead><tbody>`;
                data.forEach(r => {
                    html += `<tr><td>${r.username}</td><td>${r.tipo}</td><td>${r.hora_checkin||'-'}</td><td>${r.aprobado ? '✅ Dentro' : '❌ Fuera'}</td></tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('tablaAsistencia').innerHTML = html;
            } catch(e) {
                console.error(e);
                document.getElementById('tablaAsistencia').innerHTML = '<p>Error al cargar registros</p>';
            }
        }

        // Carga inicial
        setTimeout(() => {
            document.getElementById('fechaFiltro').value = new Date().toISOString().split('T')[0];
            cargarRegistros();
        }, 500);
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Control de Asistencia", contenido, "asistencia"))
