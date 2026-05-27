from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

# ------------------------------------------------------------
# ESTILOS GLOBALES PREMIUM (botones grandes y modales con scroll)
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
    .sidebar {
        background: linear-gradient(180deg, var(--carrier-blue) 0%, #01418a 60%, #0056b3 100%);
        color: white; width: 21rem; height: 100vh; position: fixed;
        top: 0; left: 0; padding: 1.5rem 1rem; box-shadow: 4px 0 20px rgba(0,0,0,0.1);
        z-index: 100; overflow-y: auto; display: flex; flex-direction: column;
    }
    .main-content { margin-left: 21rem; padding: 2rem; min-height: 100vh; }
    .main-header {
        font-size: 1.75rem; font-weight: 800; color: var(--carrier-blue);
        border-bottom: 3px solid var(--carrier-accent); padding-bottom: 12px; margin-bottom: 24px;
        display: flex; align-items: center; gap: 12px;
    }
    .section-title {
        font-size: 0.92rem; font-weight: 700; color: var(--carrier-blue);
        border-left: 4px solid var(--carrier-accent); padding: 9px 14px;
        margin: 22px 0 14px 0; background: white; border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 8px rgba(0,43,91,0.07);
    }
    .time-badge {
        background: var(--carrier-blue); color: white; padding: 6px 16px;
        border-radius: 24px; font-size: 0.82rem; font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,43,91,0.25); display: inline-block;
    }
    .kpi-wrap { background: white; border-radius: 16px; padding: 20px 22px 18px; text-align: center; box-shadow: 0 4px 20px rgba(0,43,91,0.08); border-top: 5px solid var(--carrier-accent); transition: transform 0.2s; position: relative; overflow: hidden; }
    .kpi-wrap::after { content: ''; position: absolute; top: 0; right: 0; width: 60px; height: 60px; background: rgba(0,87,168,0.04); border-radius: 0 0 0 60px; }
    .kpi-wrap:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,43,91,0.14); }
    .kpi-wrap.green  { border-top-color: var(--carrier-success); }
    .kpi-wrap.amber  { border-top-color: var(--carrier-warn); }
    .kpi-wrap.red    { border-top-color: var(--carrier-danger); }
    .kpi-wrap.purple { border-top-color: #7c3aed; }
    .kpi-num { font-size: 2.4rem; font-weight: 800; line-height: 1.1; }
    .kpi-wrap.green  .kpi-num { color: var(--carrier-success); }
    .kpi-wrap.amber  .kpi-num { color: var(--carrier-warn); }
    .kpi-wrap.red    .kpi-num { color: var(--carrier-danger); }
    .kpi-wrap.purple .kpi-num { color: #7c3aed; }
    .kpi-lbl { font-size: 0.73rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; margin-top: 6px; }
    .nav-item { display: block; padding: 12px 16px; border-radius: 8px; color: #e0eaff; font-weight: 600; margin-bottom: 6px; text-decoration: none; transition: background 0.2s; }
    .nav-item:hover, .nav-item.active { background: rgba(255,255,255,0.15); color: white; }
    .btn-primary { background: linear-gradient(135deg, var(--carrier-blue) 0%, var(--carrier-accent) 100%); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; width: 100%; text-align: center; }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,43,91,0.3); }
    .btn-danger { background: var(--carrier-danger); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    .btn-success { background: var(--carrier-success); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    .btn-warning { background: var(--carrier-warn); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    input, textarea, select { border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; font-size: 16px; transition: border-color 0.2s; width: 100%; margin-bottom: 12px; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: var(--carrier-accent); box-shadow: 0 0 0 3px rgba(0,87,168,0.1); }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,43,91,0.08); }
    th { background: #f8fafc; padding: 12px; text-align: left; font-weight: 600; color: var(--carrier-blue); border-bottom: 2px solid #e5e7eb; }
    td { padding: 12px; border-bottom: 1px solid #f0f0f0; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .bloqueo-card { background: #fef2f2; border: 1.5px solid #fca5a5; border-left: 5px solid var(--carrier-danger); border-radius: 10px; padding: 14px 18px; margin: 8px 0; }
    .evidencia-info { background: #eff6ff; border: 1px solid #bfdbfe; border-left: 5px solid #3b82f6; border-radius: 10px; padding: 12px 18px; margin-bottom: 14px; }
    .inv-info-bar { background: linear-gradient(90deg, var(--carrier-blue) 0%, var(--carrier-accent) 100%); color: white; padding: 14px 20px; border-radius: 12px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
    .tv-field-badge { background: var(--carrier-light); border: 1px solid #c3d4f0; border-radius: 8px; padding: 6px 12px; font-size: 0.82rem; color: var(--carrier-blue); font-weight: 600; display: inline-block; margin-bottom: 8px; }
    /* Visor: ocultar botones de acción */
    body.visor-mode .btn-primary,
    body.visor-mode .btn-danger,
    body.visor-mode .btn-success,
    body.visor-mode .btn-warning,
    body.visor-mode button:not(.logout-btn):not(.hamburger) { display: none !important; }
    body.visor-mode input, body.visor-mode select, body.visor-mode textarea { pointer-events: none; background: #f9fafb; }
    body.visor-mode .admin-only { display: none !important; }
    .visor-banner { background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 8px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; text-align: center; margin-bottom: 16px; }
    .login-card { background: white; padding: 36px 40px; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,43,91,0.18); border: 1px solid #e2e8f2; }
    .user-chip { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22); border-radius: 50px; padding: 6px 14px; color: white; font-size: 0.82rem; font-weight: 500; display: inline-block; margin-top: 4px; }
    .logout-btn { background: rgba(220,38,38,0.25); border: 1px solid rgba(220,38,38,0.5); padding: 14px 20px; border-radius: 10px; color: white; font-weight: 600; font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; transition: background 0.2s; flex-shrink: 0; }
    .logout-btn:hover { background: rgba(220,38,38,0.45); }
    .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; justify-content: center; align-items: center; z-index: 200; }
    .modal-content { background: white; padding: 24px; border-radius: 16px; width: 90%; max-width: 500px; max-height: 80vh; overflow-y: auto; box-shadow: 0 12px 40px rgba(0,0,0,0.2); }
    .modal-content input { margin-bottom: 10px; }
    .modal-content .btn-primary, .modal-content .btn-danger, .modal-content .btn-success { margin-top: 8px; }
    .hamburger {
        display: none; position: fixed; top: 14px; left: 14px; z-index: 300;
        background: var(--carrier-blue); color: white; border: none; border-radius: 10px;
        width: 44px; height: 44px; font-size: 1.3rem; cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,43,91,0.35); align-items: center; justify-content: center;
    }
    .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.45); z-index: 99; }
    @media (max-width: 768px) {
        .main-header { font-size: 1.2rem; }
        .kpi-num { font-size: 1.6rem; }
        .sidebar { width: 80vw; max-width: 300px; transform: translateX(-100%); transition: transform 0.3s ease; }
        .sidebar.open { transform: translateX(0); }
        .main-content { margin-left: 0; padding: 1rem; padding-top: 4rem; }
        .hamburger { display: flex; }
        .overlay.open { display: block; }
    }
</style>
"""

# ------------------------------------------------------------
# FUNCIÓN AUXILIAR CON SIDEBAR, MENÚ Y CIERRE DE SESIÓN SIEMPRE VISIBLE
# ------------------------------------------------------------
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
        <button class="hamburger" id="hambBtn" onclick="toggleSidebar()">☰</button>
        <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div style="text-align:center; margin-bottom:24px;">
                <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg" style="width:150px; border-radius:8px;">
                <p style="color:#c3d4f0; font-size:0.8rem; margin-top:4px;">Sistema Operativo</p>
            </div>
            <div style="margin-bottom:20px;">
                <p style="font-weight:700;" id="sidebarUser"></p>
                <span id="sidebarRole" class="user-chip"></span>
            </div>
            <hr style="border-color:rgba(255,255,255,0.2);">
            <nav style="margin-top:12px; flex:1;" id="navMenu"></nav>
            <div style="margin-top:auto; padding-top:16px; border-top:1px solid rgba(255,255,255,0.2);">
                <button onclick="logout()" class="logout-btn">🚪 Cerrar Sesión</button>
            </div>
        </div>

        <div class="main-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; flex-wrap:wrap; gap:12px;">
                <h1 class="main-header">{titulo}</h1>
                <div id="liveClock" class="time-badge"></div>
            </div>
            <div id="visorBanner" style="display:none" class="visor-banner">👁 Modo solo lectura — No tienes permisos para editar</div>
            <script>if(window.role==='visor') document.getElementById('visorBanner').style.display='block';</script>
            {contenido}
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                if (window.role === 'visor') {{ document.body.classList.add('visor-mode'); }}
                document.getElementById('sidebarUser').textContent = '👤 ' + window.username;
                const roleLabels = {{ admin: '🛡 Administrador', tecnico: '🔧 Técnico', visor: '👁 Visor' }};
                document.getElementById('sidebarRole').textContent = roleLabels[window.role] || window.role;

                const adminMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/inventario', label: '📦 Inventarios' }},
                    {{ href: '/app/unidades', label: '📸 Registro de Unidades' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                    {{ href: '/app/cluster', label: '⚡ Asignación por Cluster' }},
                    {{ href: '/app/asistencia', label: '📍 Control de Asistencia' }},
                    {{ href: '/app/admin', label: '🛠 Panel de Administración' }},
                ];
                const visorMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/inventario', label: '📦 Inventarios' }},
                    {{ href: '/app/unidades', label: '📸 Registro de Unidades' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                    {{ href: '/app/asistencia', label: '📍 Control de Asistencia' }},
                ];
                const techMenu = [
                    {{ href: '/app/mis-tareas', label: '🎯 Mis Tareas' }},
                    {{ href: '/app/solicitud', label: '🔔 Nueva Solicitud' }},
                    {{ href: '/app/mis-tickets', label: '🎫 Mis Tickets' }},
                    {{ href: '/app/checkin', label: '📍 Registrar Asistencia' }},
                ];
                const menu = window.role === 'admin' ? adminMenu : (window.role === 'visor' ? visorMenu : techMenu);
                let navHtml = '';
                menu.forEach(item => {{
                    const active = item.href === '/app/{pagina_activa}' ? ' active' : '';
                    navHtml += `<a href="${{item.href}}" class="nav-item${{active}}" onclick="if(window.innerWidth<=768)toggleSidebar()">${{item.label}}</a>`;
                }});
                document.getElementById('navMenu').innerHTML = navHtml;
            }});

            function toggleSidebar() {{
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('overlay');
                sidebar.classList.toggle('open');
                overlay.classList.toggle('open');
            }}

            function logout() {{
                localStorage.clear();
                window.location.href = '/app';
            }}

            function actualizarReloj() {{
                const ahora = new Date();
                const opciones = {{ timeZone: 'America/Tijuana', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }};
                document.getElementById('liveClock').textContent = '🕒 Tijuana ' + ahora.toLocaleTimeString('es-MX', opciones);
            }}
            actualizarReloj();
            setInterval(actualizarReloj, 1000);

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
            ws.onmessage = (event) => {{}};
        </script>
        {extra_scripts}
    </body>
    </html>
    """

# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
@router.get("/app", response_class=HTMLResponse)
async def login():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carrier Transicold – Login</title>
        <style>
            * { box-sizing: border-box; font-family: 'Inter', system-ui, sans-serif; }
            body { background: linear-gradient(135deg, #EEF2F9 0%, #F5F7FB 60%, #EAF0FB 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; padding: 20px; }
            .login-card { background: white; padding: 40px 32px; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,43,91,0.18); max-width: 400px; width: 100%; text-align: center; }
            .login-card img { width: 280px; max-width: 100%; border-radius: 12px; margin-bottom: 20px; }
            .login-card h2 { color: #002B5B; font-weight: 800; font-size: 1.5rem; margin-bottom: 4px; }
            .login-card p { color: #6b7280; font-size: 0.9rem; margin-bottom: 24px; }
            input { border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; width: 100%; margin-bottom: 16px; font-size: 16px; transition: border-color 0.2s; }
            input:focus { outline: none; border-color: #0057A8; box-shadow: 0 0 0 3px rgba(0,87,168,0.1); }
            .btn-primary { background: linear-gradient(135deg, #002B5B 0%, #0057A8 100%); color: white; border: none; border-radius: 10px; padding: 14px; width: 100%; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
            .btn-primary:hover { transform: translateY(-2px); }
            #errorMsg { color: #dc2626; font-size: 0.85rem; min-height: 20px; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg">
            <h2>Sistema Operativo</h2>
            <p>Panel de Acceso</p>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Usuario" required autocomplete="off">
                <input type="password" id="password" placeholder="Contraseña" required>
                <p id="errorMsg"></p>
                <button type="submit" class="btn-primary">Ingresar al Sistema</button>
            </form>
            <p style="text-align:center; font-size:0.75rem; color:#9ca3af; margin-top:16px;">© 2026 Carrier Transicold</p>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value.trim();
                const password = document.getElementById('password').value.trim();
                const errorEl = document.getElementById('errorMsg');
                errorEl.textContent = '';
                try {
                    const res = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
                    if (!res.ok) throw new Error('Credenciales incorrectas');
                    const data = await res.json();
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('role', data.role);
                    localStorage.setItem('username', data.username);
                    window.location.href = data.role === 'tecnico' ? '/app/mis-tareas' : '/app/dashboard';
                } catch (err) { errorEl.textContent = err.message; }
            });
        </script>
    </body>
    </html>
    """

# ------------------------------------------------------------
# DASHBOARD (solo admin/visor) - TABLA DE ESTADÍSTICAS MEJORADA
# ------------------------------------------------------------
@router.get("/app/dashboard", response_class=HTMLResponse)
async def dashboard():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div id="kpiContainer" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:16px; margin-bottom:32px;"></div>
    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:24px; margin-bottom:32px;">
        <div id="barChart" style="background:white; border-radius:16px; padding:20px; box-shadow:0 4px 12px rgba(0,43,91,0.08); min-height:420px;"></div>
        <div id="pieChart" style="background:white; border-radius:16px; padding:20px; box-shadow:0 4px 12px rgba(0,43,91,0.08); min-height:420px;"></div>
    </div>
    <div class="section-title">📋 Estatus de Proceso por Unidad</div>
    <div id="statusTable" style="overflow-x:auto; margin-bottom:32px;"></div>
    <div class="section-title">📦 Lotes y Series por Unidad</div>
    <div id="lotesContainer" style="margin-bottom:32px;"></div>
    <div class="section-title admin-only">📂 Descarga de Evidencias por Unidad</div>
    <div class="admin-only" style="display:flex; gap:16px; align-items:center; margin-bottom:16px;">
        <select id="unidadEv" style="width:auto; flex:1;"><option value="">Selecciona unidad</option></select>
        <button class="btn-primary" onclick="descargarEvidencias()">📥 Descargar ZIP</button>
    </div>
    <div class="section-title admin-only">📥 Reportes y Descargas</div>
    <button class="btn-primary admin-only" onclick="descargarReporte()">📊 Descargar Reporte Maestro Excel</button>
    <script>
        if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }
        const fetchAuth = window.fetchAuth;
        const actividades = ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series'];
        const camposSeries = {"vin_number":"VIN Number","reefer_serial":"Serie del Reefer","reefer_model":"Modelo del Reefer","evaporator_serial_mjs11":"Evaporador MJS11","evaporator_serial_mjd22":"Evaporador MJD22","engine_serial":"Motor","compressor_serial":"Compresor","generator_serial":"Generador","battery_charger_serial":"Cargador de Batería"};
        async function cargarDashboard() {
            try {
                const kpisRes = await fetchAuth('/api/dashboard/kpis');
                const kpis = await kpisRes.json();
                const kpiData = [ { value: kpis.total_unidades, label: 'Total Unidades', cls: '' }, { value: kpis.completadas, label: 'Completadas', cls: 'green' }, { value: kpis.en_proceso, label: 'En Proceso', cls: 'amber' }, { value: kpis.pendientes, label: 'Pendientes', cls: 'red' }, { value: kpis.avance + '%', label: 'Avance Global', cls: 'purple' } ];
                document.getElementById('kpiContainer').innerHTML = kpiData.map(kpi => `<div class="kpi-wrap ${kpi.cls}"><div class="kpi-num">${kpi.value !== undefined ? kpi.value : '—'}</div><div class="kpi-lbl">${kpi.label}</div></div>`).join('');
                const [statsRes, usuariosRes] = await Promise.all([fetchAuth('/api/dashboard/stats_tecnicos'), fetchAuth('/api/usuarios/')]);
                const statsRaw = await statsRes.json(); const usuariosAll = await usuariosRes.json();
                const tecnicosSet = new Set(usuariosAll.filter(u => u.role === 'tecnico').map(u => u.username));
                const stats = statsRaw.filter(s => tecnicosSet.has(s.tecnico));
                if (stats.length > 0) {
                    const barData = [{x: stats.map(s => s.tecnico), y: stats.map(s => s.completadas), type: 'bar', name: 'Completadas', marker: { color: '#16a34a' }},{x: stats.map(s => s.tecnico), y: stats.map(s => s.en_curso), type: 'bar', name: 'En Curso', marker: { color: '#d97706' }},{x: stats.map(s => s.tecnico), y: stats.map(s => s.pendientes), type: 'bar', name: 'Pendientes', marker: { color: '#dc2626' }}];
                    Plotly.newPlot('barChart', barData, { title: 'Carga de Trabajo por Técnico', barmode: 'group', paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { family: 'Inter, sans-serif' } });
                }
                const asigRes = await fetchAuth('/api/asignaciones/'); const asignaciones = await asigRes.json();
                if (asignaciones.length) {
                    const conteos = { completada: 0, en_proceso: 0, pendiente: 0 }; asignaciones.forEach(a => conteos[a.estado] = (conteos[a.estado] || 0) + 1);
                    Plotly.newPlot('pieChart', [{ values: [conteos.completada, conteos.en_proceso, conteos.pendiente], labels: ['Completadas', 'En Proceso', 'Pendientes'], marker: { colors: ['#16a34a', '#d97706', '#dc2626'] }, hole: 0.55, type: 'pie' }], { title: 'Distribución Global', paper_bgcolor: 'transparent', font: { family: 'Inter, sans-serif' } });
                    const unidadesRes = await fetchAuth('/api/unidades/'); const unidades = await unidadesRes.json();
                    if (unidades.length) {
                        // Tabla de estatus con formato de tabla
                        const completadasSet = new Set(asignaciones.filter(a => a.estado === 'completada').map(a => a.unidad + '||' + a.actividad_id));
                        let headers = '</table><th>LOTE</th><th>#Económico</th>';
                        actividades.forEach(a => headers += `<th>${a}</th>`);
                        headers += '</tr>';
                        let body = '';
                        unidades.forEach(u => {
                            body += `<tr><td>${u.id_lote || ''}</td><td>${u.unit_number}</td>`;
                            actividades.forEach(act => {
                                const completada = completadasSet.has(u.unit_number + '||' + act);
                                body += `<td style="text-align:center; font-weight:bold;">${completada ? '✔' : '—'}</td>`;
                            });
                            body += '</tr>';
                        });
                        document.getElementById('statusTable').innerHTML = `<table class="data-table" style="width:100%; border-collapse:collapse;">${headers}<tbody>${body}</tbody></table>`;
                        // Lotes y series
                        const lotesMap = {};
                        unidades.forEach(u => {
                            const lote = u.id_lote || 'Sin lote';
                            if (!lotesMap[lote]) lotesMap[lote] = [];
                            lotesMap[lote].push(u);
                        });
                        let lotesHtml = '';
                        for (const [lote, units] of Object.entries(lotesMap)) {
                            lotesHtml += `<div style="margin-bottom:16px; border:1px solid #e0e0e0; border-radius:12px; overflow:hidden;">
                                <div class="inv-info-bar" style="margin-bottom:0; cursor:pointer;" onclick="var d=this.nextElementSibling;d.style.display=d.style.display==='none'?'block':'none';">📦 Lote: ${lote} (${units.length} unidades) <span style="margin-left:auto;">▼</span></div>
                                <div style="display:none; padding:16px; background:white; overflow-x:auto;">
                                    <table class="data-table" style="width:100%;">
                                        <thead><tr><th>#Económico</th>${Object.values(camposSeries).map(s => `<th>${s}</th>`).join('')}</tr></thead>
                                        <tbody>${units.map(u => `<tr><td>${u.unit_number}</td>${Object.keys(camposSeries).map(k => `<td>${u[k] || '—'}</td>`).join('')}</tr>`).join('')}</tbody>
                                    ~
                                </div>
                            </div>`;
                        }
                        document.getElementById('lotesContainer').innerHTML = lotesHtml;
                        const unidadEvEl = document.getElementById('unidadEv');
                        if (unidadEvEl) unidadEvEl.innerHTML = '<option value="">Selecciona unidad</option>' + unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} – ${u.id_lote || ''}</option>`).join('');
                    }
                }
            } catch (err) { console.error('Error al cargar dashboard:', err); document.getElementById('kpiContainer').innerHTML = '<p style="color:red;">Error al conectar con el servidor.</p>'; }
        }
        async function descargarEvidencias() { const unit = document.getElementById('unidadEv').value; if (!unit) return alert('Selecciona unidad'); const res = await fetchAuth(`/api/evidencias/download/${unit}`); if (!res.ok) return alert('Error al descargar'); const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `evidencias_${unit}.zip`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
        async function descargarReporte() { const res = await fetchAuth('/api/dashboard/reporte-excel'); if (!res.ok) return alert('Error al generar reporte'); const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'reporte_maestro.xlsx'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
        cargarDashboard();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📊 Panel de Rendimiento Operativo", contenido, "dashboard"))

# ------------------------------------------------------------
# ASIGNACIONES (admin)
# ------------------------------------------------------------
@router.get("/app/asignaciones", response_class=HTMLResponse)
async def asignaciones():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div id="solicitudesPendientes">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="section-title" style="margin:0;">🔔 Solicitudes Pendientes</div>
            <button class="btn-primary" onclick="cargarSolicitudes()" style="margin-bottom:16px; width:auto;">🔄 Recargar</button>
        </div>
        <div id="listaSolicitudes" style="margin-top:16px;"></div>
    </div>
    <div class="section-title admin-only">➕ Asignación Directa</div>
    <form id="asignacionForm" class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px;">
        <select id="unidad" required><option value="">Unidad</option></select>
        <select id="tecnico" required><option value="">Técnico</option></select>
        <select id="actividad" required><option value="">Actividad</option></select>
        <button type="submit" class="btn-primary" style="grid-column: span 3;">📋 Crear Orden</button>
        <div id="msgAsignacion" style="grid-column: span 3; font-size:0.85rem;"></div>
    </form>
    <script>
        const fetchAuth = window.fetchAuth;
        const actividades = ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series'];
        document.getElementById('unidad').addEventListener('change', () => document.getElementById('msgAsignacion').innerHTML = '');
        document.getElementById('tecnico').addEventListener('change', () => document.getElementById('msgAsignacion').innerHTML = '');
        document.getElementById('actividad').addEventListener('change', () => document.getElementById('msgAsignacion').innerHTML = '');

        async function cargarSolicitudes() {
            const lista = document.getElementById('listaSolicitudes');
            lista.innerHTML = '<p style="color:var(--carrier-warn);">Cargando solicitudes...</p>';
            try {
                const res = await fetchAuth('/api/asignaciones/?estado=solicitado');
                if (!res.ok) throw new Error('Error ' + res.status);
                const solicitudes = await res.json();
                let html = '';
                if (!Array.isArray(solicitudes) || solicitudes.length === 0) {
                    html = '<p>✅ Sin solicitudes pendientes.</p>';
                } else {
                    solicitudes.forEach(s => {
                        html += `<div style="background:white; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); display:flex; justify-content:space-between; align-items:center;">
                            <div><b>${s.tecnico}</b> solicita <b>${s.actividad_id}</b> — Unidad: <b>${s.unidad}</b></div>
                            <div>
                                <button class="btn-success" onclick="aprobar(${s.id})">✅ Aprobar</button>
                                <button class="btn-danger" onclick="rechazar(${s.id})">❌ Rechazar</button>
                            </div>
                        </div>`;
                    });
                }
                lista.innerHTML = html;
            } catch (err) {
                console.error(err);
                lista.innerHTML = '<p style="color:var(--carrier-danger);">Error al cargar solicitudes. Intenta recargar.</p>';
            }

            const [unidadesRes, tecnicosRes] = await Promise.all([fetchAuth('/api/unidades/'), fetchAuth('/api/usuarios/')]);
            const unidades = await unidadesRes.json(); const tecnicos = await tecnicosRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.id_lote} - ${u.unit_number}</option>`).join('') : '');
            document.getElementById('tecnico').innerHTML = '<option value="">Técnico</option>' + (Array.isArray(tecnicos) ? tecnicos.filter(u => u.role === 'tecnico').map(u => `<option value="${u.username}">${u.username}</option>`).join('') : '');
            document.getElementById('actividad').innerHTML = '<option value="">Actividad</option>' + actividades.map(a => `<option value="${a}">${a}</option>`).join('');
        }

        async function aprobar(id) { await fetchAuth('/api/asignaciones/' + id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ estado: 'pendiente' }) }); cargarSolicitudes(); }
        async function rechazar(id) { if (confirm('¿Eliminar solicitud?')) { await fetchAuth('/api/asignaciones/' + id, { method: 'DELETE' }); cargarSolicitudes(); } }

        document.getElementById('asignacionForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const unidad = document.getElementById('unidad').value, tecnico = document.getElementById('tecnico').value, actividad = document.getElementById('actividad').value;
            const msgDiv = document.getElementById('msgAsignacion');
            if (!unidad || !tecnico || !actividad) return alert('Completa los campos');
            msgDiv.innerHTML = '<p style="color:var(--carrier-warn);">Verificando...</p>';
            try {
                const res = await fetchAuth('/api/asignaciones/');
                if (!res.ok) throw new Error('Error al verificar');
                const todas = await res.json();
                const activas = todas.filter(a => a.unidad === unidad && a.actividad_id === actividad && a.estado !== 'completada' && a.estado !== 'rechazada');
                const completadas = todas.filter(a => a.unidad === unidad && a.actividad_id === actividad && a.estado === 'completada');
                if (activas.length > 0) {
                    if (!confirm(`Ya existe una tarea activa (${activas.map(a => a.tecnico).join(', ')}) para esta combinación. ¿Deseas crear la orden de todos modos?`)) {
                        msgDiv.innerHTML = '';
                        return;
                    }
                }
                if (completadas.length > 0 && !confirm('Esta actividad ya fue completada anteriormente. ¿Deseas crear una nueva orden?')) { msgDiv.innerHTML = ''; return; }
                await fetchAuth('/api/asignaciones/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ unidad, tecnico, actividad_id: actividad, estado: 'pendiente' }) });
                msgDiv.innerHTML = '<p style="color:var(--carrier-success);">✅ Orden creada correctamente.</p>';
                cargarSolicitudes();
            } catch (err) { msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">Error: ${err.message}</p>`; }
        });
        cargarSolicitudes();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎯 Control de Asignaciones", contenido, "asignaciones"))

# ------------------------------------------------------------
# TICKETS (admin)
# ------------------------------------------------------------
@router.get("/app/tickets", response_class=HTMLResponse)
async def tickets():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div id="ticketsList"></div>
    <div class="section-title admin-only">➕ Nuevo Ticket</div>
    <form id="ticketForm" class="admin-only">
        <select id="unidad" required><option value="">Unidad</option></select>
        <input type="text" id="vin" placeholder="VIN (opcional)">
        <textarea id="descripcion" placeholder="Descripción del problema" rows="3" required></textarea>
        <select id="tecnico" required><option value="">Asignar a técnico</option></select>
        <button type="submit" class="btn-primary">🎫 Crear Ticket</button>
    </form>
    <script>
        const fetchAuth = window.fetchAuth;
        async function cargarTickets() {
            const res = await fetchAuth('/api/tickets/'); const tickets = await res.json();
            let html = '';
            if (tickets.length) tickets.forEach(t => {
                const estado = t.atendido ? (t.reporte_enviado ? '🟢 Completado' : '🟡 Atendido (sin reporte)') : '🔴 No atendido';
                const color = t.atendido ? (t.reporte_enviado ? 'var(--carrier-success)' : 'var(--carrier-warn)') : 'var(--carrier-danger)';
                html += `<div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px; border-radius:0 12px 12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05);"><span style="font-size:1.5rem; font-weight:800; color:var(--carrier-blue);">#${t.ticket_num}</span><span class="badge" style="background:${color}; color:white;">${estado}</span><p><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p><p><b>Descripción:</b> ${t.descripcion}</p><small>Creado por: ${t.creado_por} · ${t.fecha_creacion}</small>${!t.atendido ? `<button class="btn-danger" onclick="eliminarTicket(${t.id})">🗑️</button>` : ''}${t.atendido && !t.reporte_enviado ? `<button class="btn-primary" onclick="marcarReporte(${t.id})">📤 Marcar reporte enviado</button>` : ''}</div>`;
            });
            if (!html) html = '<p>📋 No hay tickets.</p>'; document.getElementById('ticketsList').innerHTML = html;
            const [unidadesRes, tecnicosRes] = await Promise.all([fetchAuth('/api/unidades/'), fetchAuth('/api/usuarios/')]);
            const unidades = await unidadesRes.json(); const tecnicos = await tecnicosRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} (${u.id_lote})</option>`).join('') : '');
            document.getElementById('tecnico').innerHTML = '<option value="">Asignar a técnico</option>' + (Array.isArray(tecnicos) ? tecnicos.filter(u => u.role === 'tecnico').map(u => `<option value="${u.username}">${u.username}</option>`).join('') : '');
        }
        async function eliminarTicket(id) { if (confirm('¿Eliminar ticket?')) { await fetchAuth('/api/tickets/' + id, { method: 'DELETE' }); cargarTickets(); } }
        async function marcarReporte(id) { await fetchAuth('/api/tickets/' + id + '/report', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reporte: 'Reporte enviado' }) }); cargarTickets(); }
        document.getElementById('ticketForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const unidad      = document.getElementById('unidad').value;
            const vin         = document.getElementById('vin').value;
            const descripcion = document.getElementById('descripcion').value;
            const tecnico     = document.getElementById('tecnico').value;
            if (!unidad || !descripcion || !tecnico) return alert('Completa los campos obligatorios');
            await fetchAuth('/api/tickets/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ unit_number: unidad, vin_number: vin, descripcion, tecnico }) });
            alert('Ticket creado'); cargarTickets();
        });
        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Gestión de Tickets", contenido, "tickets"))

# ------------------------------------------------------------
# INVENTARIO (admin)
# ------------------------------------------------------------
@router.get("/app/inventario", response_class=HTMLResponse)
async def inventario():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div class="inv-info-bar" id="infoBar"></div>
    <div style="display:flex; gap:12px; margin-bottom:16px;">
        <button class="btn-primary" onclick="agregarFila()">➕ Agregar Fila</button>
        <button class="btn-warning" onclick="guardarInventario()">💾 Guardar Cambios</button>
        <button class="btn-primary" onclick="mostrarConfigColumnas()">⚙️ Configurar Columnas</button>
    </div>
    <div id="inventarioTable" style="overflow-x:auto;"></div>
    <div id="modalColumnas" class="modal" style="display:none;">
        <div class="modal-content"><h3>⚙️ Configurar Columnas</h3><input type="text" id="nuevaColumna" placeholder="Nuevo nombre de columna"><button class="btn-primary" onclick="agregarColumna()">➕ Agregar</button><div id="columnasList" style="margin-top:12px;"></div><button class="btn-danger" onclick="cerrarModal()">Cerrar</button></div>
    </div>
    <script>
        const fetchAuth = window.fetchAuth; let columnas = [], datos = [];
        async function cargarInventario() {
            const colRes = await fetchAuth('/api/inventario/columnas'); columnas = await colRes.json();
            if (!Array.isArray(columnas) || columnas.length === 0) { columnas = ["Código","Descripción","Cantidad","Unidad","Ubicación","Estado"]; await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); }
            const datRes = await fetchAuth('/api/inventario/datos'); datos = await datRes.json();
            if (!Array.isArray(datos) || datos.length === 0) datos = [Object.fromEntries(columnas.map(c => [c, '']))];
            document.getElementById('infoBar').innerHTML = `🗄 Inventario Principal &nbsp;·&nbsp; ${datos.length} registros &nbsp;·&nbsp; ${columnas.length} columnas`;
            renderTabla();
        }
        function renderTabla() { let html = '<table><thead><tr><th>#</th>'; columnas.forEach(c => html += `<th>${c}</th>`); html += '<th>Acción</th></tr></thead><tbody>'; datos.forEach((fila, idx) => { html += `<tr><td style="text-align:center;">${idx+1}</td>`; columnas.forEach(c => html += `<td><input type="text" value="${fila[c] || ''}" onchange="datos[${idx}]['${c}'] = this.value" style="margin:0;"></td>`); html += `<td><button class="btn-danger" onclick="eliminarFila(${idx})">🗑</button></td>`; }); html += '</tbody></table>'; document.getElementById('inventarioTable').innerHTML = html; }
        function agregarFila() { datos.push(Object.fromEntries(columnas.map(c => [c, '']))); renderTabla(); }
        function eliminarFila(idx) { if (confirm('¿Eliminar fila?')) { datos.splice(idx,1); renderTabla(); } }
        async function guardarInventario() { await fetchAuth('/api/inventario/datos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(datos) }); alert('Inventario guardado'); }
        async function agregarColumna() { const nombre = document.getElementById('nuevaColumna').value.trim(); if (!nombre) return; if (!columnas.includes(nombre)) { columnas.push(nombre); await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); datos = datos.map(fila => { fila[nombre] = ''; return fila; }); renderTabla(); } }
        function mostrarConfigColumnas() { document.getElementById('modalColumnas').style.display = 'flex'; renderColumnasList(); }
        function cerrarModal() { document.getElementById('modalColumnas').style.display = 'none'; }
        function renderColumnasList() { let html = ''; columnas.forEach((c, i) => { html += `<div style="display:flex; justify-content:space-between; margin-bottom:4px;"><input type="text" value="${c}" onchange="renombrarColumna(${i}, this.value)"><button class="btn-danger" onclick="eliminarColumna(${i})">🗑</button></div>`; }); document.getElementById('columnasList').innerHTML = html; }
        async function renombrarColumna(idx, nuevoNombre) { columnas[idx] = nuevoNombre; await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); renderTabla(); }
        async function eliminarColumna(idx) { columnas.splice(idx, 1); await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); datos = datos.map(fila => { const newFila = {}; columnas.forEach(c => newFila[c] = fila[c] || ''); return newFila; }); renderTabla(); }
        cargarInventario();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📦 Gestión de Inventarios", contenido, "inventario"))

# ------------------------------------------------------------
# REGISTRO DE UNIDADES (admin)
# ------------------------------------------------------------
@router.get("/app/unidades", response_class=HTMLResponse)
async def unidades():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <form id="unidadForm" class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
        <input type="text" id="unit_number" placeholder="Número Económico" required><input type="text" id="id_lote" placeholder="Número de Lote">
        <input type="text" id="vin_number" placeholder="VIN Number"><input type="text" id="reefer_serial" placeholder="Serie del Reefer">
        <input type="text" id="reefer_model" placeholder="Modelo del Reefer"><input type="text" id="evaporator_serial_mjs11" placeholder="Evaporador MJS11">
        <input type="text" id="evaporator_serial_mjd22" placeholder="Evaporador MJD22"><input type="text" id="engine_serial" placeholder="Motor">
        <input type="text" id="compressor_serial" placeholder="Compresor"><input type="text" id="generator_serial" placeholder="Generador">
        <input type="text" id="battery_charger_serial" placeholder="Cargador de Batería">
        <button type="submit" class="btn-primary" style="grid-column: span 2;">💾 Guardar Registro</button>
    </form>
    <div class="section-title">📸 Unidades Registradas</div>
    <div id="unidadesList"></div>
    <script>
        const fetchAuth = window.fetchAuth;
        async function cargarUnidades() { const res = await fetchAuth('/api/unidades/'); const unidades = await res.json(); let html = '<table><thead><tr><th>#Económico</th><th>Lote</th><th>VIN</th><th>Reefer Serial</th><th>Modelo</th><th>Motor</th><th>Compresor</th></tr></thead><tbody>'; if (Array.isArray(unidades)) unidades.forEach(u => html += `<tr><td>${u.unit_number}</td><td>${u.id_lote||''}</td><td style="font-family:monospace;">${u.vin_number||''}</td><td>${u.reefer_serial||''}</td><td>${u.reefer_model||''}</td><td style="font-family:monospace;">${u.engine_serial||''}</td><td>${u.compressor_serial||''}</td>`); html += '</tbody></table>'; document.getElementById('unidadesList').innerHTML = html; }
        document.getElementById('unidadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                unit_number: document.getElementById('unit_number').value,
                id_lote: document.getElementById('id_lote').value,
                vin_number: document.getElementById('vin_number').value,
                reefer_serial: document.getElementById('reefer_serial').value,
                reefer_model: document.getElementById('reefer_model').value,
                evaporator_serial_mjs11: document.getElementById('evaporator_serial_mjs11').value,
                evaporator_serial_mjd22: document.getElementById('evaporator_serial_mjd22').value,
                engine_serial: document.getElementById('engine_serial').value,
                compressor_serial: document.getElementById('compressor_serial').value,
                generator_serial: document.getElementById('generator_serial').value,
                battery_charger_serial: document.getElementById('battery_charger_serial').value
            };
            if (!data.unit_number) return alert('El Número Económico es obligatorio');
            await fetchAuth('/api/unidades/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            alert('Unidad registrada'); cargarUnidades();
        });
        cargarUnidades();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📸 Registro de Unidades", contenido, "unidades"))

# ------------------------------------------------------------
# GESTIÓN DE USUARIOS (admin) - se añadió opción "visor"
# ------------------------------------------------------------
@router.get("/app/usuarios", response_class=HTMLResponse)
async def usuarios():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>

    <div class="section-title">👥 Usuarios Registrados</div>
    <div id="usuariosList"></div>

    <div class="section-title admin-only" style="margin-top:28px;">➕ Crear Nuevo Usuario</div>
    <div class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px;">
        <input type="text" id="username" placeholder="Nombre de usuario" required>
        <input type="password" id="newUserPassword" placeholder="Contraseña" required>
        <select id="role" required>
            <option value="tecnico">Técnico</option>
            <option value="admin">Administrador</option>
            <option value="visor">Visor (solo lectura)</option>
        </select>
        <button onclick="crearUsuario()" class="btn-primary" style="grid-column: span 3;">👤 Crear Usuario</button>
    </div>

    <script>
        const fetchAuth = window.fetchAuth;

        async function cargarUsuarios() {
            try {
                const res = await fetchAuth('/api/usuarios/');
                const usuarios = await res.json();
                let html = '<table><thead><tr><th>Usuario</th><th>Rol</th><th style="text-align:center;">Acciones</th></tr></thead><tbody>';
                if (Array.isArray(usuarios)) {
                    usuarios.forEach(u => {
                        const rolTexto = u.role === 'admin' ? '🛡 Administrador' : (u.role === 'tecnico' ? '🔧 Técnico' : '👁 Visor');
                        const acciones = window.role === 'admin' ? `
                            <button class="btn-warning" onclick="abrirModalPassword(${u.id}, '${u.username}')" style="padding:6px 14px;font-size:0.82rem;margin-right:6px;">🔑 Cambiar Contraseña</button>
                            <button class="btn-danger" onclick="eliminarUsuario(${u.id}, '${u.username}')" style="padding:6px 14px;font-size:0.82rem;">🗑️ Eliminar</button>
                        ` : '—';
                        html += `<tr><td><b>${u.username}</b></td><td>${rolTexto}</td><td style="text-align:center;">${acciones}</td></tr>`;
                    });
                }
                html += '</tbody></table>';
                document.getElementById('usuariosList').innerHTML = html;
            } catch (err) {
                document.getElementById('usuariosList').innerHTML = '<p style="color:red;">Error al cargar usuarios</p>';
            }
        }

        function abrirModalPassword(userId, username) {
            const prev = document.getElementById('modalPassword');
            if (prev) prev.remove();
            const modal = document.createElement('div');
            modal.id = 'modalPassword';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;';
            modal.innerHTML = `
                <div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:460px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeInP 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:#fef3c7;border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🔑</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.1rem;font-weight:800;">Cambiar Contraseña</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:#6b7280;">Usuario: <b>${username}</b></p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">Nueva contraseña</label>
                    <div style="position:relative;">
                        <input id="inputNuevaPwd" type="password" placeholder="Escribe la nueva contraseña" style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:12px 44px 12px 12px;font-size:0.95rem;font-family:inherit;">
                        <span onclick="togglePwd()" style="position:absolute;right:14px;top:50%;transform:translateY(-50%);cursor:pointer;font-size:1.1rem;" title="Mostrar/ocultar">👁</span>
                    </div>
                    <p id="pwdError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button onclick="document.getElementById('modalPassword').remove()" style="background:#f1f5f9;color:#374151;border:none;border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnGuardarPwd" onclick="guardarPassword(${userId})" style="background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent));color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">💾 Guardar</button>
                    </div>
                </div>
                <style>@keyframes fadeInP{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            setTimeout(() => document.getElementById('inputNuevaPwd').focus(), 100);
        }

        function togglePwd() {
            const input = document.getElementById('inputNuevaPwd');
            input.type = input.type === 'password' ? 'text' : 'password';
        }

        async function guardarPassword(userId) {
            const pwd = document.getElementById('inputNuevaPwd').value.trim();
            const errorEl = document.getElementById('pwdError');
            if (!pwd || pwd.length < 4) { errorEl.textContent = 'Mínimo 4 caracteres.'; return; }
            const btn = document.getElementById('btnGuardarPwd');
            btn.textContent = 'Guardando...'; btn.disabled = true;
            const res = await fetchAuth('/api/usuarios/' + userId + '/password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_password: pwd })
            });
            if (res.ok) {
                document.getElementById('modalPassword').remove();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#1F4E79;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Contraseña actualizada correctamente.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
            } else {
                const err = await res.json();
                errorEl.textContent = err.detail || 'Error al guardar.';
                btn.textContent = '💾 Guardar'; btn.disabled = false;
            }
        }

        async function crearUsuario() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('newUserPassword').value;
            const role     = document.getElementById('role').value;
            if (!username || !password) return alert('Completa todos los campos');
            const res = await fetchAuth('/api/usuarios/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role })
            });
            if (res.ok) {
                document.getElementById('username').value = '';
                document.getElementById('newUserPassword').value = '';
                cargarUsuarios();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Usuario creado exitosamente.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
            } else {
                const err = await res.json();
                alert('Error: ' + (err.detail || 'No se pudo crear el usuario'));
            }
        }

        async function eliminarUsuario(id, nombre) {
            if (!confirm(`¿Eliminar al usuario "${nombre}"? Esta acción no se puede deshacer.`)) return;
            const res = await fetchAuth('/api/usuarios/' + id, { method: 'DELETE' });
            if (res.ok) cargarUsuarios();
            else alert('Error al eliminar usuario');
        }

        cargarUsuarios();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("👥 Gestión de Usuarios", contenido, "usuarios"))

# ------------------------------------------------------------
# PANEL DE ADMINISTRACIÓN (admin) — CRUD interactivo
# ------------------------------------------------------------
@router.get("/app/admin", response_class=HTMLResponse)
async def admin():
    contenido = """
    <script> if (window.role !== 'admin') { window.location.href = '/app/mis-tareas'; } </script>

    <!-- Tabler Icons CDN -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --navy: #0f2d6b;
      --navy-mid: #1a3f8f;
      --navy-btn: #1e4fc0;
      --navy-light: #2e63d4;
      --danger: #c0392b;
      --danger-hover: #a93226;
      --success: #1a7a4a;
      --warn: #b7640a;
      --text-on-navy: #e8f0ff;
      --row-hover: #edf2fb;
      --selected-bg: #d6e4fc;
      --border: rgba(30,79,192,0.18);
      --color-background-primary: #ffffff;
      --color-background-secondary: #f4f6fb;
      --color-text-primary: #1a2340;
      --color-text-secondary: #6b7280;
      --color-border-secondary: #d1d5db;
      --color-border-tertiary: #e5e7eb;
      --border-radius-md: 8px;
      --border-radius-lg: 12px;
      --font-sans: 'Inter', sans-serif;
      --font-mono: 'Courier New', monospace;
    }
    .panel { padding: 1rem 0; }
    .tabs { display: flex; gap: 8px; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .tab-btn {
      background: var(--navy);
      color: var(--text-on-navy);
      border: none;
      border-radius: var(--border-radius-md);
      padding: 9px 18px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex; align-items: center; gap: 7px;
      transition: background 0.15s;
    }
    .tab-btn:hover { background: var(--navy-light); }
    .tab-btn.active { background: var(--navy-btn); outline: 2px solid #6fa3f7; outline-offset: 1px; }
    .tab-btn i { font-size: 15px; }
    .section { display: none; }
    .section.active { display: block; }
    .toolbar {
      display: flex; align-items: center; gap: 10px;
      margin-bottom: 10px; flex-wrap: wrap;
    }
    .toolbar input[type=text] {
      flex: 1; min-width: 160px; max-width: 280px;
      border: 0.5px solid var(--border);
      border-radius: var(--border-radius-md);
      padding: 7px 12px; font-size: 13px;
      background: var(--color-background-primary);
      color: var(--color-text-primary);
      margin-bottom: 0;
    }
    .toolbar select {
      border: 0.5px solid var(--border);
      border-radius: var(--border-radius-md);
      padding: 7px 10px; font-size: 13px;
      background: var(--color-background-primary);
      color: var(--color-text-primary);
      margin-bottom: 0;
    }
    .btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 14px; border-radius: var(--border-radius-md);
      font-size: 13px; font-weight: 500; cursor: pointer; border: none;
      transition: background 0.15s, transform 0.1s;
    }
    .btn:active { transform: scale(0.97); }
    .btn-navy { background: var(--navy-btn); color: #fff; }
    .btn-navy:hover { background: var(--navy-light); }
    .btn-danger-sm { background: var(--danger); color: #fff; }
    .btn-danger-sm:hover { background: var(--danger-hover); }
    .btn-ghost {
      background: transparent; color: var(--color-text-secondary);
      border: 0.5px solid var(--color-border-secondary);
    }
    .btn-ghost:hover { background: var(--color-background-secondary); }
    .btn i { font-size: 14px; }
    .bulk-bar {
      display: none; align-items: center; gap: 10px;
      background: #fff3cd; border: 0.5px solid #f5a623;
      border-radius: var(--border-radius-md); padding: 8px 14px;
      margin-bottom: 10px; font-size: 13px; color: #7a4e00;
    }
    .bulk-bar.visible { display: flex; }
    .main-layout { display: flex; gap: 12px; align-items: flex-start; }
    .table-wrap { flex: 1; min-width: 0; overflow: hidden; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .data-table th {
      background: var(--navy);
      color: var(--text-on-navy);
      padding: 9px 10px; text-align: left;
      font-weight: 500; font-size: 12px; letter-spacing: 0.02em;
      white-space: nowrap;
    }
    .data-table th:first-child { border-radius: var(--border-radius-md) 0 0 0; width: 32px; }
    .data-table th:last-child { border-radius: 0 var(--border-radius-md) 0 0; }
    .data-table td { padding: 9px 10px; border-bottom: 0.5px solid var(--color-border-tertiary); color: var(--color-text-primary); vertical-align: middle; }
    .data-table tr:hover td { background: var(--row-hover); }
    .data-table tr.selected td { background: var(--selected-bg); }
    .data-table tr.editing td { background: #edf6ff; }
    .admin-badge {
      display: inline-block; padding: 2px 9px; border-radius: 999px;
      font-size: 11px; font-weight: 500;
    }
    .badge-pending { background: #fff3cd; color: #7a4e00; }
    .badge-done { background: #d4edda; color: #155724; }
    .badge-req { background: #d1ecf1; color: #0c5460; }
    .badge-cancel { background: #f8d7da; color: #721c24; }
    .row-actions { display: flex; gap: 5px; }
    .icon-btn {
      background: none; border: none; cursor: pointer;
      padding: 4px; border-radius: 5px; color: var(--color-text-secondary);
      font-size: 15px; display: flex; align-items: center; justify-content: center;
      transition: background 0.12s, color 0.12s;
    }
    .icon-btn:hover.edit { background: #dbeafe; color: var(--navy-btn); }
    .icon-btn:hover.del { background: #fde8e8; color: var(--danger); }
    .editor-panel {
      width: 268px; min-width: 268px;
      background: var(--color-background-primary);
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-lg);
      padding: 1rem; font-size: 13px;
      display: none;
    }
    .editor-panel.visible { display: block; }
    .editor-panel h3 {
      font-size: 14px; font-weight: 500;
      color: var(--navy);
      margin-bottom: 14px;
      display: flex; align-items: center; gap: 7px; justify-content: space-between;
    }
    .editor-panel h3 span { display: flex; align-items: center; gap: 7px; }
    .close-editor { background: none; border: none; cursor: pointer; color: var(--color-text-secondary); font-size: 16px; padding: 2px; border-radius: 4px; }
    .close-editor:hover { background: var(--color-background-secondary); }
    .field-group { margin-bottom: 11px; }
    .field-group label { display: block; font-size: 11px; color: var(--color-text-secondary); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
    .field-group input, .field-group select, .field-group textarea {
      width: 100%;
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      padding: 7px 10px; font-size: 13px;
      background: var(--color-background-primary);
      color: var(--color-text-primary);
      margin-bottom: 0;
    }
    .field-group textarea { resize: vertical; min-height: 60px; }
    .editor-actions { display: flex; gap: 8px; margin-top: 14px; }
    .editor-actions .btn { flex: 1; justify-content: center; }
    .admin-divider { height: 0.5px; background: var(--color-border-tertiary); margin: 14px 0; }
    .id-badge { font-size: 11px; background: var(--color-background-secondary); color: var(--color-text-secondary); padding: 2px 8px; border-radius: var(--border-radius-md); }
    .sql-area {
      width: 100%;
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      padding: 12px; font-size: 13px;
      font-family: var(--font-mono);
      background: var(--color-background-secondary);
      color: var(--color-text-primary);
      min-height: 110px; resize: vertical;
      margin-bottom: 10px;
    }
    .sql-result {
      font-size: 12px; font-family: var(--font-mono);
      background: var(--color-background-secondary);
      border: 0.5px solid var(--color-border-tertiary);
      border-radius: var(--border-radius-md);
      padding: 10px 12px; max-height: 180px; overflow-y: auto;
      color: var(--color-text-primary); white-space: pre-wrap;
      display: none; margin-top: 10px;
    }
    .sql-result.visible { display: block; }
    .sql-presets { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .sql-presets button {
      font-size: 11px; padding: 4px 10px;
      background: var(--color-background-secondary);
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      cursor: pointer; color: var(--color-text-secondary);
      margin-bottom: 0;
    }
    .sql-presets button:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
    .admin-notice { font-size: 12px; color: var(--color-text-secondary); padding: 6px 10px; background: var(--color-background-secondary); border-radius: var(--border-radius-md); border-left: 3px solid var(--navy-light); margin-bottom: 10px; }
    .pagination { display: flex; align-items: center; gap: 8px; margin-top: 10px; font-size: 12px; color: var(--color-text-secondary); }
    .pagination button {
      background: var(--color-background-secondary);
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      padding: 4px 10px; font-size: 12px; cursor: pointer;
      margin-bottom: 0;
    }
    .pagination button:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
    .pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
    </style>

    <div class="panel">
      <div class="tabs">
        <button class="tab-btn active" onclick="showTab('actividades')" id="tab-actividades">
          <i class="ti ti-activity"></i> Actividades
        </button>
        <button class="tab-btn" onclick="showTab('usuarios')" id="tab-usuarios">
          <i class="ti ti-users"></i> Usuarios
        </button>
        <button class="tab-btn" onclick="showTab('unidades')" id="tab-unidades">
          <i class="ti ti-truck"></i> Unidades
        </button>
        <button class="tab-btn" onclick="showTab('sql')" id="tab-sql">
          <i class="ti ti-terminal-2"></i> SQL Directo
        </button>
      </div>

      <!-- ── ACTIVIDADES ── -->
      <div id="sec-actividades" class="section active">
        <div class="toolbar">
          <input type="text" id="search-act" placeholder="Buscar por ID, vehículo, técnico…" oninput="filterTable('act')" />
          <select id="filter-estado" onchange="filterTable('act')">
            <option value="">Todos los estados</option>
            <option value="pendiente">Pendiente</option>
            <option value="en_proceso">En Proceso</option>
            <option value="completada">Completada</option>
            <option value="solicitado">Solicitado</option>
            <option value="cancelado">Cancelado</option>
          </select>
          <button class="btn btn-navy" onclick="recargarActividades()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
        </div>
        <div class="bulk-bar" id="bulk-act">
          <i class="ti ti-checkbox"></i>
          <span id="bulk-count-act">0</span> seleccionados
          <button class="btn btn-danger-sm" style="margin-left:auto" onclick="eliminarSeleccionados('act')">
            <i class="ti ti-trash"></i> Eliminar seleccionados
          </button>
        </div>
        <div class="main-layout">
          <div class="table-wrap">
            <table class="data-table" id="table-act">
              <thead>
                <tr>
                  <th><input type="checkbox" id="check-all-act" onchange="toggleAll('act')" /></th>
                  <th>ID</th><th>Unidad</th><th>Actividad</th><th>Técnico</th><th>Estado</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody id="tbody-act"></tbody>
            </table>
            <div class="pagination" id="pag-act"></div>
          </div>
          <div class="editor-panel" id="editor-act">
            <h3>
              <span><i class="ti ti-edit"></i> Editar registro</span>
              <button class="close-editor" onclick="cerrarEditor('act')"><i class="ti ti-x"></i></button>
            </h3>
            <div id="editor-id-act" class="id-badge" style="margin-bottom:12px"></div>
            <div class="field-group"><label>Unidad</label><input type="text" id="ef-vehiculo" /></div>
            <div class="field-group"><label>Técnico</label><input type="text" id="ef-tecnico" /></div>
            <div class="field-group"><label>Estado</label>
              <select id="ef-estado">
                <option value="pendiente">Pendiente</option>
                <option value="en_proceso">En Proceso</option>
                <option value="solicitado">Solicitado</option>
                <option value="completada">Completada</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>
            <div class="admin-divider"></div>
            <div class="editor-actions">
              <button class="btn btn-navy" onclick="guardarEditor('act')"><i class="ti ti-device-floppy"></i> Guardar</button>
              <button class="btn btn-ghost" onclick="cerrarEditor('act')">Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── USUARIOS ── -->
      <div id="sec-usuarios" class="section">
        <div class="toolbar">
          <input type="text" id="search-usr" placeholder="Buscar usuario…" oninput="filterTable('usr')" />
          <select id="filter-rol" onchange="filterTable('usr')">
            <option value="">Todos los roles</option>
            <option value="admin">Administrador</option>
            <option value="tecnico">Técnico</option>
            <option value="visor">Visor</option>
          </select>
          <button class="btn btn-navy" onclick="recargarUsuarios()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
          <button class="btn btn-navy" onclick="nuevoUsuario()">
            <i class="ti ti-plus"></i> Nuevo
          </button>
        </div>
        <div class="bulk-bar" id="bulk-usr">
          <i class="ti ti-checkbox"></i>
          <span id="bulk-count-usr">0</span> seleccionados
          <button class="btn btn-danger-sm" style="margin-left:auto" onclick="eliminarSeleccionados('usr')">
            <i class="ti ti-trash"></i> Eliminar seleccionados
          </button>
        </div>
        <div class="main-layout">
          <div class="table-wrap">
            <table class="data-table" id="table-usr">
              <thead>
                <tr>
                  <th><input type="checkbox" id="check-all-usr" onchange="toggleAll('usr')" /></th>
                  <th>ID</th><th>Usuario</th><th>Rol</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody id="tbody-usr"></tbody>
            </table>
            <div class="pagination" id="pag-usr"></div>
          </div>
          <div class="editor-panel" id="editor-usr">
            <h3>
              <span><i class="ti ti-user-edit"></i> Editar usuario</span>
              <button class="close-editor" onclick="cerrarEditor('usr')"><i class="ti ti-x"></i></button>
            </h3>
            <div id="editor-id-usr" class="id-badge" style="margin-bottom:12px"></div>
            <div class="field-group"><label>Usuario</label><input type="text" id="uf-nombre" /></div>
            <div class="field-group"><label>Rol</label>
              <select id="uf-rol">
                <option value="admin">Administrador</option>
                <option value="tecnico">Técnico</option>
                <option value="visor">Visor (solo lectura)</option>
              </select>
            </div>
            <div class="field-group"><label>Contraseña nueva</label><input type="password" id="uf-pass" placeholder="Dejar en blanco = sin cambios" /></div>
            <div class="admin-divider"></div>
            <div class="editor-actions">
              <button class="btn btn-navy" onclick="guardarEditor('usr')"><i class="ti ti-device-floppy"></i> Guardar</button>
              <button class="btn btn-ghost" onclick="cerrarEditor('usr')">Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── UNIDADES ── -->
      <div id="sec-unidades" class="section">
        <div class="toolbar">
          <input type="text" id="search-uni" placeholder="Buscar unidad…" oninput="filterTable('uni')" />
          <button class="btn btn-navy" onclick="recargarUnidades()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
        </div>
        <div class="bulk-bar" id="bulk-uni">
          <i class="ti ti-checkbox"></i>
          <span id="bulk-count-uni">0</span> seleccionados
          <button class="btn btn-danger-sm" style="margin-left:auto" onclick="eliminarSeleccionados('uni')">
            <i class="ti ti-trash"></i> Eliminar seleccionados
          </button>
        </div>
        <div class="main-layout">
          <div class="table-wrap">
            <table class="data-table" id="table-uni">
              <thead>
                <tr>
                  <th><input type="checkbox" id="check-all-uni" onchange="toggleAll('uni')" /></th>
                  <th>ID</th><th>#Económico</th><th>Lote</th><th>VIN</th><th>Modelo</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody id="tbody-uni"></tbody>
            </table>
            <div class="pagination" id="pag-uni"></div>
          </div>
          <div class="editor-panel" id="editor-uni">
            <h3>
              <span><i class="ti ti-truck"></i> Editar unidad</span>
              <button class="close-editor" onclick="cerrarEditor('uni')"><i class="ti ti-x"></i></button>
            </h3>
            <div id="editor-id-uni" class="id-badge" style="margin-bottom:12px"></div>
            <div class="field-group"><label>#Económico</label><input type="text" id="nf-placa" /></div>
            <div class="field-group"><label>Lote</label><input type="text" id="nf-lote" /></div>
            <div class="field-group"><label>VIN</label><input type="text" id="nf-vin" /></div>
            <div class="field-group"><label>Modelo Reefer</label><input type="text" id="nf-modelo" /></div>
            <div class="admin-divider"></div>
            <div class="editor-actions">
              <button class="btn btn-navy" onclick="guardarEditor('uni')"><i class="ti ti-device-floppy"></i> Guardar</button>
              <button class="btn btn-ghost" onclick="cerrarEditor('uni')">Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── SQL ── -->
      <div id="sec-sql" class="section">
        <div class="admin-notice"><i class="ti ti-info-circle"></i> Ejecuta consultas directas. Los cambios son permanentes.</div>
        <div class="sql-presets">
          <button onclick="setSQL('SELECT * FROM asignaciones;')">asignaciones</button>
          <button onclick="setSQL('SELECT * FROM usuarios;')">usuarios</button>
          <button onclick="setSQL('SELECT * FROM unidades;')">unidades</button>
          <button onclick="setSQL('SELECT * FROM tickets;')">tickets</button>
          <button onclick="setSQL('SELECT * FROM inventarios;')">inventarios</button>
          <button onclick="setSQL(&quot;DELETE FROM asignaciones WHERE estado = 'cancelado';&quot;)">limpiar cancelados</button>
        </div>
        <textarea class="sql-area" id="sql-input" spellcheck="false">SELECT * FROM asignaciones;</textarea>
        <div style="display:flex; gap:8px; align-items:center;">
          <button class="btn btn-navy" onclick="ejecutarSQL()"><i class="ti ti-player-play"></i> Ejecutar</button>
          <button class="btn btn-ghost" onclick="document.getElementById('sql-input').value=''"><i class="ti ti-eraser"></i> Limpiar</button>
        </div>
        <div class="sql-result" id="sql-result"></div>
      </div>
    </div>

    <script>
    const fetchAuth = window.fetchAuth;
    const PER_PAGE = 8;
    const DATA   = { act: [], usr: [], uni: [] };
    const filtered = { act: [], usr: [], uni: [] };
    const pages  = { act: 1, usr: 1, uni: 1 };
    const editing = { act: null, usr: null, uni: null };
    const selected = { act: new Set(), usr: new Set(), uni: new Set() };

    // ── Carga desde API ──────────────────────────────────────
    async function recargarActividades() {
        const estado = document.getElementById('filter-estado').value;
        const url = estado ? `/api/asignaciones/?estado=${estado}` : '/api/asignaciones/';
        const res = await fetchAuth(url);
        DATA.act = await res.json();
        filterTable('act');
    }

    async function recargarUsuarios() {
        const res = await fetchAuth('/api/usuarios/');
        DATA.usr = await res.json();
        filterTable('usr');
    }

    async function recargarUnidades() {
        const res = await fetchAuth('/api/unidades/');
        DATA.uni = await res.json();
        filterTable('uni');
    }

    // ── Badges ──────────────────────────────────────────────
    function badgeEstado(e) {
        const m = {
            pendiente:'badge-pending', en_proceso:'badge-req',
            completada:'badge-done', solicitado:'badge-req',
            cancelado:'badge-cancel', activo:'badge-done',
            inactivo:'badge-cancel', mantenimiento:'badge-pending',
            admin:'badge-req', tecnico:'badge-pending', visor:'badge-done'
        };
        return `<span class="admin-badge ${m[e]||''}">${e}</span>`;
    }

    // ── Render tablas ────────────────────────────────────────
    function renderAct() {
        const pg = pages.act; const rows = filtered.act;
        const slice = rows.slice((pg-1)*PER_PAGE, pg*PER_PAGE);
        document.getElementById('tbody-act').innerHTML = slice.map(r => `
            <tr id="row-act-${r.id}" class="${editing.act===r.id?'editing':''} ${selected.act.has(r.id)?'selected':''}">
              <td><input type="checkbox" onchange="toggleRow('act',${r.id},this)" ${selected.act.has(r.id)?'checked':''}></td>
              <td><span style="font-family:monospace;font-size:12px;color:#6b7280">${r.id}</span></td>
              <td style="font-weight:500">${r.unidad||''}</td>
              <td>${r.actividad_id||''}</td>
              <td>${r.tecnico||''}</td>
              <td>${badgeEstado(r.estado||'')}</td>
              <td><div class="row-actions">
                <button class="icon-btn edit" onclick="editarFilaAct(${r.id})" title="Editar"><i class="ti ti-edit"></i></button>
                <button class="icon-btn del" onclick="eliminarFilaAct(${r.id})" title="Eliminar"><i class="ti ti-trash"></i></button>
              </div></td>
            </tr>`).join('');
        renderPag('act', rows.length);
    }

    function renderUsr() {
        const pg = pages.usr; const rows = filtered.usr;
        const slice = rows.slice((pg-1)*PER_PAGE, pg*PER_PAGE);
        document.getElementById('tbody-usr').innerHTML = slice.map(r => `
            <tr id="row-usr-${r.id}" class="${editing.usr===r.id?'editing':''} ${selected.usr.has(r.id)?'selected':''}">
              <td><input type="checkbox" onchange="toggleRow('usr',${r.id},this)" ${selected.usr.has(r.id)?'checked':''}></td>
              <td style="font-family:monospace;font-size:12px;color:#6b7280">${r.id}</td>
              <td style="font-weight:500">${r.username||''}</td>
              <td>${badgeEstado(r.role||'')}</td>
              <td><div class="row-actions">
                <button class="icon-btn edit" onclick="editarFilaUsr(${r.id})" title="Editar"><i class="ti ti-edit"></i></button>
                <button class="icon-btn del" onclick="eliminarFilaUsr(${r.id})" title="Eliminar"><i class="ti ti-trash"></i></button>
              </div></td>
            </tr>`).join('');
        renderPag('usr', rows.length);
    }

    function renderUni() {
        const pg = pages.uni; const rows = filtered.uni;
        const slice = rows.slice((pg-1)*PER_PAGE, pg*PER_PAGE);
        document.getElementById('tbody-uni').innerHTML = slice.map(r => `
            <tr id="row-uni-${r.id}" class="${editing.uni===r.id?'editing':''} ${selected.uni.has(r.id)?'selected':''}">
              <td><input type="checkbox" onchange="toggleRow('uni',${r.id},this)" ${selected.uni.has(r.id)?'checked':''}></td>
              <td style="font-family:monospace;font-size:12px;color:#6b7280">${r.id}</td>
              <td style="font-weight:500;font-family:monospace">${r.unit_number||''}</td>
              <td>${r.id_lote||''}</td>
              <td style="font-size:12px;color:#6b7280">${r.vin_number||'—'}</td>
              <td>${r.reefer_model||'—'}</td>
              <td><div class="row-actions">
                <button class="icon-btn edit" onclick="editarFilaUni(${r.id})" title="Editar"><i class="ti ti-edit"></i></button>
                <button class="icon-btn del" onclick="eliminarFilaUni(${r.id})" title="Eliminar"><i class="ti ti-trash"></i></button>
              </div></td>
            </tr>`).join('');
        renderPag('uni', rows.length);
    }

    function renderPag(t, total) {
        const pg = pages[t]; const tot = Math.ceil(total/PER_PAGE)||1;
        document.getElementById('pag-'+t).innerHTML = `
            <button onclick="changePage('${t}',-1)" ${pg<=1?'disabled':''}>&#8249;</button>
            <span>Pág ${pg} de ${tot} &nbsp;·&nbsp; ${total} registros</span>
            <button onclick="changePage('${t}',1)" ${pg>=tot?'disabled':''}>&#8250;</button>`;
    }

    function changePage(t,d){ pages[t]+=d; render(t); }
    function render(t){ if(t==='act')renderAct(); else if(t==='usr')renderUsr(); else renderUni(); }

    // ── Filtros ──────────────────────────────────────────────
    function filterTable(t) {
        if(t==='act'){
            const q=(document.getElementById('search-act').value||'').toLowerCase();
            const es=document.getElementById('filter-estado').value;
            filtered.act=DATA.act.filter(r=>{
                const match=!q||((r.unidad||'')+(r.tecnico||'')+(r.actividad_id||'')+String(r.id)).toLowerCase().includes(q);
                return match&&(!es||r.estado===es);
            }); pages.act=1; renderAct();
        } else if(t==='usr'){
            const q=(document.getElementById('search-usr').value||'').toLowerCase();
            const rl=document.getElementById('filter-rol').value;
            filtered.usr=DATA.usr.filter(r=>{
                const match=!q||(r.username||'').toLowerCase().includes(q);
                return match&&(!rl||r.role===rl);
            }); pages.usr=1; renderUsr();
        } else {
            const q=(document.getElementById('search-uni').value||'').toLowerCase();
            filtered.uni=DATA.uni.filter(r=>!q||((r.unit_number||'')+(r.id_lote||'')).toLowerCase().includes(q));
            pages.uni=1; renderUni();
        }
    }

    // ── Pestañas ─────────────────────────────────────────────
    function showTab(t) {
        ['actividades','usuarios','unidades','sql'].forEach(s=>{
            document.getElementById('sec-'+s).classList.toggle('active',s===t);
            document.getElementById('tab-'+s).classList.toggle('active',s===t);
        });
    }

    // ── Editar Actividades ───────────────────────────────────
    function editarFilaAct(id) {
        editing.act=id;
        const r=DATA.act.find(x=>x.id===id); if(!r) return;
        document.getElementById('editor-act').classList.add('visible');
        document.getElementById('editor-id-act').textContent='ID: '+id;
        document.getElementById('ef-vehiculo').value=r.unidad||'';
        document.getElementById('ef-tecnico').value=r.tecnico||'';
        document.getElementById('ef-estado').value=r.estado||'pendiente';
        renderAct();
    }

    async function guardarEditor(t) {
        if(t==='act'){
            const id=editing.act;
            const estado=document.getElementById('ef-estado').value;
            await fetchAuth('/api/asignaciones/'+id, {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({estado})
            });
            cerrarEditor('act'); recargarActividades();
        } else if(t==='usr'){
            const id=editing.usr;
            const username=document.getElementById('uf-nombre').value;
            const role=document.getElementById('uf-rol').value;
            const pass=document.getElementById('uf-pass').value;
            await fetchAuth('/api/usuarios/'+id, {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({username, role})
            });
            if(pass) await fetchAuth('/api/usuarios/'+id+'/password', {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({new_password:pass})
            });
            cerrarEditor('usr'); recargarUsuarios();
        } else {
            const id=editing.uni;
            const unit_number=document.getElementById('nf-placa').value;
            const id_lote=document.getElementById('nf-lote').value;
            const vin_number=document.getElementById('nf-vin').value;
            const reefer_model=document.getElementById('nf-modelo').value;
            await fetchAuth('/api/unidades/'+id, {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({unit_number, id_lote, vin_number, reefer_model})
            });
            cerrarEditor('uni'); recargarUnidades();
        }
    }

    function cerrarEditor(t){
        editing[t]=null;
        document.getElementById('editor-'+t).classList.remove('visible');
        render(t);
    }

    // ── Editar Usuarios ──────────────────────────────────────
    function editarFilaUsr(id) {
        editing.usr=id;
        const r=DATA.usr.find(x=>x.id===id); if(!r) return;
        document.getElementById('editor-usr').classList.add('visible');
        document.getElementById('editor-id-usr').textContent='ID: '+id;
        document.getElementById('uf-nombre').value=r.username||'';
        document.getElementById('uf-rol').value=r.role||'tecnico';
        document.getElementById('uf-pass').value='';
        renderUsr();
    }

    async function nuevoUsuario() {
        const username=prompt('Nombre de usuario:'); if(!username) return;
        const password=prompt('Contraseña:'); if(!password) return;
        const role=prompt('Rol (admin/tecnico/visor):','tecnico'); if(!role) return;
        const res=await fetchAuth('/api/usuarios/', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({username, password, role})
        });
        if(res.ok){ recargarUsuarios(); } else { alert('Error al crear usuario'); }
    }

    async function eliminarFilaUsr(id) {
        const r=DATA.usr.find(x=>x.id===id);
        if(!confirm('¿Eliminar usuario "'+( r?.username||id)+'"?')) return;
        await fetchAuth('/api/usuarios/'+id, {method:'DELETE'});
        recargarUsuarios();
    }

    // ── Editar Unidades ──────────────────────────────────────
    function editarFilaUni(id) {
        editing.uni=id;
        const r=DATA.uni.find(x=>x.id===id); if(!r) return;
        document.getElementById('editor-uni').classList.add('visible');
        document.getElementById('editor-id-uni').textContent='#: '+r.unit_number;
        document.getElementById('nf-placa').value=r.unit_number||'';
        document.getElementById('nf-lote').value=r.id_lote||'';
        document.getElementById('nf-vin').value=r.vin_number||'';
        document.getElementById('nf-modelo').value=r.reefer_model||'';
        renderUni();
    }

    async function eliminarFilaUni(id) {
        const r=DATA.uni.find(x=>x.id===id);
        if(!confirm('¿Eliminar unidad "'+(r?.unit_number||id)+'"?')) return;
        await fetchAuth('/api/unidades/'+id, {method:'DELETE'});
        recargarUnidades();
    }

    // ── Eliminar Actividades ─────────────────────────────────
    async function eliminarFilaAct(id) {
        if(!confirm('¿Eliminar actividad '+id+'?')) return;
        await fetchAuth('/api/asignaciones/'+id, {method:'DELETE'});
        recargarActividades();
    }

    // ── Selección múltiple ───────────────────────────────────
    function toggleRow(t,id,cb){
        if(cb.checked) selected[t].add(id); else selected[t].delete(id);
        updateBulk(t); render(t);
    }

    function toggleAll(t){
        const cb=document.getElementById('check-all-'+t);
        filtered[t].forEach(r=>{ if(cb.checked) selected[t].add(r.id); else selected[t].delete(r.id); });
        updateBulk(t); render(t);
    }

    function updateBulk(t){
        const bar=document.getElementById('bulk-'+t);
        const n=selected[t].size;
        bar.classList.toggle('visible',n>0);
        document.getElementById('bulk-count-'+t).textContent=n;
    }

    async function eliminarSeleccionados(t) {
        const n=selected[t].size;
        if(!confirm('¿Eliminar '+n+' registros seleccionados?')) return;
        const endpoint = t==='act' ? '/api/asignaciones/' : t==='usr' ? '/api/usuarios/' : '/api/unidades/';
        for(const id of selected[t]) await fetchAuth(endpoint+id, {method:'DELETE'});
        selected[t].clear();
        if(t==='act') recargarActividades();
        else if(t==='usr') recargarUsuarios();
        else recargarUnidades();
        updateBulk(t);
    }

    // ── SQL ──────────────────────────────────────────────────
    function setSQL(q){ document.getElementById('sql-input').value=q; }
    async function ejecutarSQL(){
        const sql=document.getElementById('sql-input').value.trim();
        const res=document.getElementById('sql-result');
        res.classList.add('visible');
        if(!sql){ res.textContent='Error: consulta vacía.'; return; }
        res.textContent='Ejecutando…';
        try {
            const r=await fetchAuth('/api/admin/execute-sql', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({sql})
            });
            const data=await r.json();
            if(data.error){ res.textContent='Error: '+data.error; return; }
            if(Array.isArray(data)&&data.length){
                const keys=Object.keys(data[0]);
                res.textContent=[keys.join(' | '),'-'.repeat(60),...data.map(row=>keys.map(k=>String(row[k]??'')).join(' | '))].join('\\n');
            } else { res.textContent='Consulta ejecutada. '+JSON.stringify(data); }
        } catch(e){ res.textContent='Error: '+e.message; }
    }

    // ── Init ─────────────────────────────────────────────────
    recargarActividades();
    recargarUsuarios();
    recargarUnidades();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🛠 Panel de Administración", contenido, "admin"))

# ------------------------------------------------------------
# MIS TAREAS (modales con botones grandes y scroll)
# ------------------------------------------------------------
@router.get("/app/mis-tareas", response_class=HTMLResponse)
async def mis_tareas():
    contenido = """
    <script> if (window.role === 'visor') { window.location.href = '/app/dashboard'; } </script>
    <div id="tareasList"></div>
    <script>
        const fetchAuth = window.fetchAuth, username = window.username;

        function mostrarModal(html) {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.style.display = 'flex';
            modal.innerHTML = html;
            document.body.appendChild(modal);
            return modal;
        }
        function cerrarModal() {
            const modal = document.querySelector('.modal');
            if (modal) document.body.removeChild(modal);
        }

        async function cargarTareas() {
            const res = await fetchAuth('/api/asignaciones/?tecnico=' + username);
            if (!res.ok) { document.getElementById('tareasList').innerHTML = '<p style="color:red;">Error al cargar tareas.</p>'; return; }
            const tareas = await res.json();
            const activas = Array.isArray(tareas) ? tareas.filter(t => t.estado === 'pendiente' || t.estado === 'en_proceso') : [];
            let html = '';
            if (activas.length === 0) {
                html = '<p>✅ No tienes tareas activas.</p>';
            } else {
                activas.forEach(t => {
                    let btn = '';
                    if (t.estado === 'pendiente') btn = `<button class="btn-primary" onclick="iniciarTarea(${t.id})">▶️ Iniciar Actividad</button>`;
                    else if (t.estado === 'en_proceso') {
                        btn = `<button class="btn-success" onclick="completarTarea(${t.id})">✅ Finalizar</button>`;
                        if (t.actividad_id === 'Evidencia') btn += `<button class="btn-primary" onclick="subirEvidencia(${t.id}, '${t.unidad}')">📸 Subir Fotos</button>`;
                        if (t.actividad_id === 'Toma de Valores') btn += `<button class="btn-primary" onclick="tomarValores(${t.id})">📊 Ingresar Valores</button>`;
                        if (t.actividad_id === 'Toma de Series') btn += `<button class="btn-primary" onclick="tomarSeries(${t.id})">🔢 Ingresar Series</button>`;
                    }
                    html += `<div style="background:white; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); display:flex; justify-content:space-between; align-items:center;"><div><b>${t.actividad_id}</b> — Unidad: <b>${t.unidad}</b><br><span class="badge" style="background:${t.estado === 'pendiente' ? 'var(--carrier-warn)' : 'var(--carrier-success)'}; color:white;">${t.estado}</span></div><div>${btn}</div></div>`;
                });
            }
            document.getElementById('tareasList').innerHTML = html;
        }

        async function iniciarTarea(id) { const res = await fetchAuth('/api/asignaciones/' + id + '/iniciar', { method: 'PATCH' }); if (res.ok) cargarTareas(); else alert('Error al iniciar la tarea'); }
        async function completarTarea(id) {
            const prev = document.getElementById('modalFinalizar');
            if (prev) prev.remove();

            const modal = document.createElement('div');
            modal.id = 'modalFinalizar';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;';
            modal.innerHTML = `
                <div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:520px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeInM 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:#f0fdf4;border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">✅</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.2rem;font-weight:800;">Finalizar Actividad</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:#6b7280;">Agrega un comentario antes de cerrar esta tarea.</p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">📝 Comentario del técnico</label>
                    <textarea id="comentarioTexto" rows="4" placeholder="Describe brevemente el trabajo realizado, observaciones, etc." style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:12px;font-size:0.95rem;resize:vertical;font-family:inherit;transition:border-color 0.2s;"></textarea>
                    <p id="comentarioError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button onclick="document.getElementById('modalFinalizar').remove()" style="background:#f1f5f9;color:#374151;border:none;border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnConfirmarFinalizar" onclick="confirmarFinalizar(${id})" style="background:linear-gradient(135deg,#16a34a,#15803d);color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">✅ Confirmar y Finalizar</button>
                    </div>
                </div>
                <style>@keyframes fadeInM{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            setTimeout(() => document.getElementById('comentarioTexto').focus(), 100);
        }

        async function confirmarFinalizar(id) {
            const comentario = document.getElementById('comentarioTexto').value.trim();
            const errorEl   = document.getElementById('comentarioError');
            if (!comentario) { errorEl.textContent = 'El comentario no puede estar vacío.'; return; }
            const btn = document.getElementById('btnConfirmarFinalizar');
            btn.textContent = 'Guardando...'; btn.disabled = true;
            const res = await fetchAuth('/api/asignaciones/' + id + '/finalizar', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ comentario }) });
            if (res.ok) {
                document.getElementById('modalFinalizar').remove();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Actividad finalizada correctamente.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                cargarTareas();
            } else {
                const err = await res.json();
                errorEl.textContent = err.detail || 'No se pudo finalizar. Intenta de nuevo.';
                btn.textContent = '✅ Confirmar y Finalizar'; btn.disabled = false;
            }
        }

        // ────────── EVIDENCIA ──────────
        async function subirEvidencia(tareaId, unidad) {
            const cntRes = await fetchAuth(`/api/evidencias/count?unit_number=${unidad}&tecnico=${username}`); const cnt = await cntRes.json();
            const totalPrev = cnt.total || 0; const restantes = 100 - totalPrev;
            if (restantes <= 0) return alert('Límite de 100 fotos alcanzado');
            const modal = mostrarModal(`<div class="modal-content"><h3>📸 Subir Evidencia – ${unidad}</h3><p>Guardadas: <b>${totalPrev}</b> · Disponibles: <b>${restantes}</b></p><input type="file" id="fotosInput" multiple accept="image/*"><div id="previewFotos" style="display:flex; flex-wrap:wrap; gap:8px; margin:12px 0;"></div><button class="btn-primary" id="btnGuardarFotos">💾 Guardar Fotos</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('fotosInput').addEventListener('change', e => {
                const files = Array.from(e.target.files).slice(0, restantes), previewDiv = document.getElementById('previewFotos'); previewDiv.innerHTML = '';
                files.forEach(f => { const r = new FileReader(); r.onload = ev => { const img = document.createElement('img'); img.src = ev.target.result; img.style.cssText = 'width:70px;height:70px;object-fit:cover;border-radius:8px;'; previewDiv.appendChild(img); }; r.readAsDataURL(f); });
            });
            document.getElementById('btnGuardarFotos').onclick = async () => {
                const input = document.getElementById('fotosInput'); if (!input.files.length) return alert('Selecciona fotos');
                const fd = new FormData(); fd.append('unidad', unidad); fd.append('tecnico', username); for (let f of input.files) fd.append('files', f);
                await fetchAuth('/api/evidencias/upload', { method: 'POST', body: fd }); alert('Fotos guardadas'); cerrarModal();
            };
        }

        // ────────── VALORES ──────────
        async function tomarValores(tareaId) {
            const camposRes = await fetchAuth('/api/toma-valores/campos'); const campos = await camposRes.json();
            let camposHTML = campos.length ? campos.map((c,i) => `<input type="text" id="campo_${i}" placeholder="${c.campo_nombre}">`).join('') : '<p>No hay campos configurados.</p>';
            const modal = mostrarModal(`<div class="modal-content"><h3>📊 Toma de Valores</h3><div id="camposValores">${camposHTML}</div><button class="btn-primary" id="btnGuardarValores">💾 Guardar Valores</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarValores').onclick = async () => {
                const valores = {}; campos.forEach((c,i) => valores[c.campo_nombre] = document.getElementById('campo_'+i).value);
                await fetchAuth('/api/toma-valores/guardar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ asignacion_id: tareaId, valores }) }); alert('Valores guardados'); cerrarModal();
            };
        }

        // ────────── SERIES ──────────
        async function tomarSeries(tareaId) {
            const camposSeries = [
                { key: 'vin_number', label: 'VIN Number' },{ key: 'reefer_serial', label: 'Serie del Reefer' },{ key: 'reefer_model', label: 'Modelo del Reefer' },
                { key: 'evaporator_serial_mjs11', label: 'Evaporador MJS11' },{ key: 'evaporator_serial_mjd22', label: 'Evaporador MJD22' },
                { key: 'engine_serial', label: 'Motor' },{ key: 'compressor_serial', label: 'Compresor' },{ key: 'generator_serial', label: 'Generador' },
                { key: 'battery_charger_serial', label: 'Cargador de Batería' }
            ];
            let inputs = camposSeries.map((c,i) => `<input type="text" id="serie_${i}" placeholder="${c.label}"><input type="hidden" id="serie_key_${i}" value="${c.key}">`).join('');
            const modal = mostrarModal(`<div class="modal-content"><h3>🔢 Toma de Series</h3><div id="camposSeries">${inputs}</div><button class="btn-primary" id="btnGuardarSeries">💾 Guardar Series</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarSeries').onclick = async () => {
                const tareasRes = await fetchAuth('/api/asignaciones/?tecnico=' + username + '&estado=en_proceso'); const tareas = await tareasRes.json();
                const tarea = Array.isArray(tareas) ? tareas.find(t => t.id == tareaId) : null; if (!tarea) return alert('Tarea no encontrada');
                const keys = [...document.querySelectorAll('[id^="serie_key_"]')].map(el => el.value); const values = { unit_number: tarea.unidad };
                keys.forEach((key,i) => values[key] = document.getElementById('serie_'+i).value);
                const resSeries = await fetchAuth('/api/unidades/series/update', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); if (resSeries.ok) { cerrarModal(); cargarTareas(); const t = document.createElement('div'); t.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;z-index:600;'; t.textContent = '✅ Series guardadas correctamente.'; document.body.appendChild(t); setTimeout(() => t.remove(), 3000); } else { alert('Error al guardar las series.'); }
            };
        }

        cargarTareas();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎯 Mis Tareas", contenido, "mis-tareas"))

# ------------------------------------------------------------
# NUEVA SOLICITUD
# ------------------------------------------------------------
@router.get("/app/solicitud", response_class=HTMLResponse)
async def solicitud():
    contenido = """
    <form id="solicitudForm">
        <select id="unidad" required><option value="">Unidad</option></select>
        <select id="actividad" required><option value="">Actividad</option></select>
        <button type="submit" class="btn-primary">📤 Enviar Solicitud</button>
        <div id="msgSolicitud" style="font-size:0.85rem;"></div>
    </form>
    <div class="section-title">📋 Mis Solicitudes Recientes</div>
    <div id="historialSolicitudes" style="margin-top:16px;"></div>
    <script>
        const fetchAuth = window.fetchAuth, username = window.username;
        document.getElementById('unidad').addEventListener('change', () => document.getElementById('msgSolicitud').innerHTML = '');
        document.getElementById('actividad').addEventListener('change', () => document.getElementById('msgSolicitud').innerHTML = '');
        async function cargarOpciones() {
            const unidadesRes = await fetchAuth('/api/unidades/'); const unidades = await unidadesRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} (${u.id_lote})</option>`).join('') : '');
            document.getElementById('actividad').innerHTML = '<option value="">Actividad</option>' + ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series'].map(a => `<option value="${a}">${a}</option>`).join('');
            const histRes = await fetchAuth('/api/asignaciones/?tecnico=' + username + '&limit=20'); const historial = await histRes.json();
            let hHtml = '';
            if (Array.isArray(historial)) historial.forEach(h => { const color = h.estado === 'solicitado' ? '#fef9c3' : h.estado === 'pendiente' ? '#fff7ed' : h.estado === 'en_proceso' ? '#eff6ff' : '#f0fdf4'; const borderColor = h.estado === 'solicitado' ? '#854d0e' : h.estado === 'pendiente' ? '#9a3412' : h.estado === 'en_proceso' ? '#1e40af' : '#166534'; hHtml += `<div style="background:${color};border-left:4px solid ${borderColor};padding:10px 16px;margin-bottom:6px;border-radius:8px;"><b>${h.actividad_id}</b> — Unidad: ${h.unidad} · ${h.estado}</div>`; });
            document.getElementById('historialSolicitudes').innerHTML = hHtml || '<p>Sin solicitudes recientes.</p>';
        }
        document.getElementById('solicitudForm').addEventListener('submit', async (e) => {
            e.preventDefault(); const unidad = document.getElementById('unidad').value, actividad = document.getElementById('actividad').value;
            if (!unidad || !actividad) return alert('Selecciona unidad y actividad');
            const msgDiv = document.getElementById('msgSolicitud'); msgDiv.innerHTML = '<p style="color:var(--carrier-warn);">Verificando...</p>';
            const res = await fetchAuth('/api/asignaciones/?estado=solicitado,pendiente,en_proceso');
            if (!res.ok) { msgDiv.innerHTML = '<p style="color:var(--carrier-danger);">Error al verificar.</p>'; return; }
            const todas = await res.json(); const activa = todas.find(a => a.unidad === unidad && a.actividad_id === actividad);
            if (activa) { msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">Ya existe una tarea activa para esta combinación (técnico: ${activa.tecnico}). Solo un administrador puede autorizarla.</p>`; return; }
            const crearRes = await fetchAuth('/api/asignaciones/solicitar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ unidad, actividad_id: actividad, tecnico: username }) });
            if (!crearRes.ok) { const err = await crearRes.json(); msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">${err.detail || 'Error al enviar solicitud'}</p>`; return; }
            msgDiv.innerHTML = '<p style="color:var(--carrier-success);">Solicitud enviada correctamente.</p>'; cargarOpciones();
        });
        cargarOpciones();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🔔 Nueva Solicitud", contenido, "solicitud"))

# ------------------------------------------------------------
# MIS TICKETS
# ------------------------------------------------------------
@router.get("/app/mis-tickets", response_class=HTMLResponse)
async def mis_tickets():
    contenido = """
    <div id="ticketsList"></div>
    <script>
        const fetchAuth = window.fetchAuth;

        async function cargarTickets() {
            const res = await fetchAuth('/api/tickets/');
            const tickets = await res.json();
            let html = '';
            if (tickets.length) {
                tickets.forEach(t => {
                    const estado = t.atendido
                        ? (t.reporte_enviado ? '🟢 Completado' : '🟡 Atendido (sin reporte)')
                        : '🔴 No atendido';
                    const color = t.atendido
                        ? (t.reporte_enviado ? 'var(--carrier-success)' : 'var(--carrier-warn)')
                        : 'var(--carrier-danger)';

                    let acciones = '';
                    if (!t.atendido) {
                        acciones = `<button class="btn-warning" onclick="atenderTicket(${t.id})" style="margin-top:10px; width:auto; padding:10px 18px;">✅ Marcar como atendido</button>`;
                    } else if (!t.reporte_enviado) {
                        acciones = `<button class="btn-primary" onclick="enviarReporte(${t.id})" style="margin-top:10px; width:auto; padding:10px 18px;">📤 Enviar reporte final</button>`;
                    }

                    html += `
                        <div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px; border-radius:0 12px 12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                                <div>
                                    <span style="font-size:1.5rem; font-weight:800; color:var(--carrier-blue);">#${t.ticket_num}</span>
                                    <span class="badge" style="background:${color}; color:white; margin-left:8px;">${estado}</span>
                                    <p style="margin:8px 0 4px;"><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p>
                                    <p style="margin:4px 0;"><b>Descripción:</b> ${t.descripcion}</p>
                                    <small style="color:#6b7280;">Creado: ${t.fecha_creacion}</small>
                                </div>
                                <div style="display:flex; align-items:center;">${acciones}</div>
                            </div>
                        </div>`;
                });
            }
            if (!html) html = '<p>🎫 No tienes tickets.</p>';
            document.getElementById('ticketsList').innerHTML = html;
        }

        async function atenderTicket(id) {
            if (!confirm('¿Marcar este ticket como atendido?')) return;
            const res = await fetchAuth('/api/tickets/' + id + '/atender', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ atendido: true }) });
            if (res.ok) { cargarTickets(); }
            else { alert('Error al actualizar el ticket'); }
        }

        async function enviarReporte(ticketId) {
            const prev = document.getElementById('modalReporte');
            if (prev) prev.remove();

            const modal = document.createElement('div');
            modal.id = 'modalReporte';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;';
            modal.innerHTML = `
                <div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:520px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeIn 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:var(--carrier-light);border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">📋</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.2rem;font-weight:800;">Reporte Final del Ticket</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:#6b7280;">Este reporte quedará registrado y cerrará el ticket en verde.</p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">📝 Descripción del trabajo realizado</label>
                    <textarea id="reporteTexto" rows="5" placeholder="Describe detalladamente las acciones realizadas, piezas cambiadas, diagnóstico, etc." style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:12px;font-size:0.95rem;resize:vertical;font-family:inherit;transition:border-color 0.2s;"></textarea>
                    <p id="reporteError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:4px;">
                        <button onclick="document.getElementById('modalReporte').remove()" style="background:#f1f5f9;color:#374151;border:none;border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnEnviarReporte" onclick="confirmarReporte(${ticketId})" style="background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent));color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">📤 Enviar y Cerrar Ticket</button>
                    </div>
                </div>
                <style>@keyframes fadeIn{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            setTimeout(() => document.getElementById('reporteTexto').focus(), 100);
        }

        async function confirmarReporte(id) {
            const reporte = document.getElementById('reporteTexto').value.trim();
            const errorEl = document.getElementById('reporteError');
            if (!reporte) { errorEl.textContent = 'El reporte no puede estar vacío.'; return; }
            const btn = document.getElementById('btnEnviarReporte');
            btn.textContent = 'Enviando...'; btn.disabled = true;
            const res = await fetchAuth('/api/tickets/' + id + '/report', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reporte }) });
            if (res.ok) {
                document.getElementById('modalReporte').remove();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Reporte enviado. Ticket completado.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                cargarTickets();
            } else {
                errorEl.textContent = 'Error al enviar el reporte. Intenta de nuevo.';
                btn.textContent = '📤 Enviar y Cerrar Ticket'; btn.disabled = false;
            }
        }

        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Mis Tickets", contenido, "mis-tickets"))

# ------------------------------------------------------------
# PANEL DE ASIGNACIÓN POR CLUSTER (CORREGIDO, SIN DEPENDENCIAS)
# ------------------------------------------------------------
@router.get("/app/cluster", response_class=HTMLResponse)
async def panel_cluster():
    contenido = """
    <div id="resumenCluster" style="display:none; background:var(--color-background-secondary); border-radius:var(--border-radius-lg); padding:16px; margin-bottom:20px;"></div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; align-items:start;">
        <div style="background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:16px;">
            <div style="font-weight:500; margin-bottom:12px; color:var(--color-text-primary);">🔧 Técnicos</div>
            <div style="margin-bottom:8px; display:flex; gap:6px;">
                <button onclick="seleccionarTodos('tecnicos')" style="font-size:11px;padding:4px 10px;">Todos</button>
                <button onclick="limpiarTodos('tecnicos')" style="font-size:11px;padding:4px 10px;">Ninguno</button>
            </div>
            <div id="listaTecnicos" style="max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;"></div>
        </div>
        <div style="background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:16px;">
            <div style="font-weight:500; margin-bottom:12px; color:var(--color-text-primary);">🎯 Actividades</div>
            <div style="margin-bottom:8px; display:flex; gap:6px;">
                <button onclick="seleccionarTodos('actividades')" style="font-size:11px;padding:4px 10px;">Todas</button>
                <button onclick="limpiarTodos('actividades')" style="font-size:11px;padding:4px 10px;">Ninguna</button>
            </div>
            <div id="listaActividades" style="max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;"></div>
        </div>
        <div style="background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:16px;">
            <div style="font-weight:500; margin-bottom:12px; color:var(--color-text-primary);">🚛 Unidades</div>
            <div style="margin-bottom:8px; display:flex; gap:6px;">
                <button onclick="seleccionarTodos('unidades')" style="font-size:11px;padding:4px 10px;">Todas</button>
                <button onclick="limpiarTodos('unidades')" style="font-size:11px;padding:4px 10px;">Ninguna</button>
            </div>
            <div id="filtroLote" style="margin-bottom:8px;"></div>
            <div id="listaUnidades" style="max-height:280px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;"></div>
        </div>
    </div>
    <div style="margin-top:20px; background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div id="contadorResumen" style="font-size:13px; color:var(--color-text-secondary);">Selecciona técnicos, actividades y unidades</div>
            <button id="btnAsignar" onclick="ejecutarAsignacion()" style="padding:12px 32px; font-size:0.95rem; font-weight:600; background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent)); color:white; border:none; border-radius:10px; cursor:pointer;">⚡ Asignar Cluster</button>
        </div>
    </div>
    <script>
        const fetchAuth = window.fetchAuth;
        let todosTecnicos = [], todasActividades = [], todasUnidades = [];
        let lotes = [];

        function checkItem(tipo, valor) {
            return `<label style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;cursor:pointer;border:0.5px solid var(--color-border-tertiary);font-size:13px;color:var(--color-text-primary);transition:background 0.15s;" onmouseover="this.style.background='var(--color-background-secondary)'" onmouseout="this.style.background='transparent'">
                <input type="checkbox" data-tipo="${tipo}" data-valor="${encodeURIComponent(valor)}" onchange="actualizarContador()" style="width:15px;height:15px;cursor:pointer;">
                ${valor}
            </label>`;
        }

        function seleccionarTodos(tipo) {
            document.querySelectorAll(`input[data-tipo="${tipo}"]`).forEach(c => c.checked = true);
            actualizarContador();
        }
        function limpiarTodos(tipo) {
            document.querySelectorAll(`input[data-tipo="${tipo}"]`).forEach(c => c.checked = false);
            actualizarContador();
        }

        function getSeleccionados(tipo) {
            return [...document.querySelectorAll(`input[data-tipo="${tipo}"]:checked`)].map(c => decodeURIComponent(c.dataset.valor));
        }

        function actualizarContador() {
            const t = getSeleccionados('tecnicos').length;
            const a = getSeleccionados('actividades').length;
            const u = getSeleccionados('unidades').length;
            const total = t * a * u;
            const el = document.getElementById('contadorResumen');
            if (total === 0) {
                el.innerHTML = 'Selecciona técnicos, actividades y unidades';
                el.style.color = 'var(--color-text-secondary)';
            } else {
                el.innerHTML = `<b>${t}</b> técnico(s) × <b>${a}</b> actividad(es) × <b>${u}</b> unidad(es) = <b style="color:var(--carrier-blue);">${total} asignaciones</b>`;
                el.style.color = 'var(--color-text-primary)';
            }
        }

        function filtrarPorLote(lote) {
            const items = document.querySelectorAll('[data-lote]');
            items.forEach(i => {
                i.style.display = (!lote || i.dataset.lote === lote) ? 'flex' : 'none';
            });
        }

        async function cargarDatos() {
            const [resTec, resAct, resUni] = await Promise.all([
                fetchAuth('/api/cluster/tecnicos'),
                fetchAuth('/api/cluster/actividades'),
                fetchAuth('/api/cluster/unidades')
            ]);
            todosTecnicos  = await resTec.json();
            todasActividades = await resAct.json();
            todasUnidades  = await resUni.json();

            document.getElementById('listaTecnicos').innerHTML = todosTecnicos.map(t => checkItem('tecnicos', t.username)).join('');
            document.getElementById('listaActividades').innerHTML = todasActividades.map(a => checkItem('actividades', a.nombre)).join('');

            lotes = [...new Set(todasUnidades.map(u => u.id_lote).filter(Boolean))].sort();
            let filtroHtml = '<select onchange="filtrarPorLote(this.value)" style="width:100%;margin-bottom:6px;font-size:12px;padding:5px;"><option value="">— Todos los lotes —</option>';
            lotes.forEach(l => filtroHtml += `<option value="${l}">${l}</option>`);
            filtroHtml += '</select>';
            document.getElementById('filtroLote').innerHTML = filtroHtml;

            document.getElementById('listaUnidades').innerHTML = todasUnidades.map(u =>
                `<label data-lote="${u.id_lote || ''}" style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;cursor:pointer;border:0.5px solid var(--color-border-tertiary);font-size:13px;color:var(--color-text-primary);transition:background 0.15s;" onmouseover="this.style.background='var(--color-background-secondary)'" onmouseout="this.style.background='transparent'">
                    <input type="checkbox" data-tipo="unidades" data-valor="${encodeURIComponent(u.unit_number)}" onchange="actualizarContador()" style="width:15px;height:15px;cursor:pointer;">
                    <span>${u.unit_number}</span><span style="font-size:11px;color:var(--color-text-secondary);margin-left:auto;">${u.id_lote || ''}</span>
                </label>`
            ).join('');
        }

        async function ejecutarAsignacion() {
            const tecnicos   = getSeleccionados('tecnicos');
            const actividades = getSeleccionados('actividades');
            const unidades   = getSeleccionados('unidades');
            if (!tecnicos.length || !actividades.length || !unidades.length) {
                return alert('Selecciona al menos un técnico, una actividad y una unidad.');
            }
            const total = tecnicos.length * actividades.length * unidades.length;
            if (!confirm(`¿Crear ${total} asignaciones? Esta acción no se puede deshacer.`)) return;

            const btn = document.getElementById('btnAsignar');
            btn.textContent = 'Asignando...'; btn.disabled = true;

            const res = await fetchAuth('/api/cluster/asignar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tecnicos, actividades, unidades })
            });
            const data = await res.json();

            btn.textContent = '⚡ Asignar Cluster'; btn.disabled = false;

            const resumen = document.getElementById('resumenCluster');
            resumen.style.display = 'block';
            resumen.innerHTML = res.ok
                ? `<div style="color:var(--color-text-success);font-weight:500;">✅ ${data.mensaje}</div>`
                : `<div style="color:var(--color-text-danger);font-weight:500;">❌ Error: ${data.detail || 'No se pudo completar'}</div>`;

            if (res.ok) {
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = `✅ ${data.creadas} asignaciones creadas correctamente.`;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 4000);
                limpiarTodos('tecnicos'); limpiarTodos('actividades'); limpiarTodos('unidades');
                actualizarContador();
            }
        }

        cargarDatos();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("⚡ Asignación por Cluster", contenido, "cluster"))


# ------------------------------------------------------------
# ASISTENCIA – PANEL ADMIN: genera QR con geocoordenadas fijas
# ------------------------------------------------------------
@router.get("/app/asistencia", response_class=HTMLResponse)
async def asistencia_admin():
    contenido = """
    <script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>
    <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>

    <!-- Configuración de geoposición fija -->
    <div class="evidencia-info" style="margin-bottom:20px;">
        <b>📍 Geoposición fija del QR</b><br>
        <span style="font-size:0.85rem;">Define las coordenadas del lugar de trabajo. El técnico deberá estar dentro del radio permitido al escanear.</span>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:20px;">
        <div>
            <label style="font-size:0.82rem; font-weight:600; color:#374151;">Latitud fija</label>
            <input type="number" id="latFija" step="0.000001" value="32.5027" placeholder="Ej: 32.5027">
        </div>
        <div>
            <label style="font-size:0.82rem; font-weight:600; color:#374151;">Longitud fija</label>
            <input type="number" id="lonFija" step="0.000001" value="-117.0037" placeholder="Ej: -117.0037">
        </div>
        <div>
            <label style="font-size:0.82rem; font-weight:600; color:#374151;">Radio permitido (metros)</label>
            <input type="number" id="radioMetros" value="200" min="10" max="5000">
        </div>
    </div>

    <div style="display:flex; gap:12px; margin-bottom:28px; flex-wrap:wrap;">
        <button class="btn-primary" style="width:auto; padding:12px 24px;" onclick="generarQR()">🔄 Generar QR de Asistencia</button>
        <button class="btn-warning" style="width:auto; padding:12px 24px;" onclick="usarUbicacionActual()">📡 Usar mi ubicación actual</button>
    </div>

    <!-- QR generado -->
    <div id="qrSection" style="display:none; margin-bottom:32px;">
        <div class="section-title">📲 QR para Escanear</div>
        <div style="display:flex; gap:32px; align-items:flex-start; flex-wrap:wrap;">
            <div style="background:white; padding:24px; border-radius:16px; box-shadow:0 4px 20px rgba(0,43,91,0.1); text-align:center;">
                <div id="qrCanvas"></div>
                <p style="font-size:0.78rem; color:#6b7280; margin-top:12px;">Válido por <b id="qrTimer">05:00</b></p>
                <button class="btn-primary" style="width:auto; padding:10px 20px; font-size:0.85rem; margin-top:8px;" onclick="generarQR()">🔁 Regenerar</button>
            </div>
            <div style="flex:1; min-width:220px;">
                <div class="inv-info-bar" style="margin-bottom:12px;">📍 Punto de asistencia configurado</div>
                <p style="font-size:0.9rem;"><b>Lat:</b> <span id="qrLatLabel"></span></p>
                <p style="font-size:0.9rem;"><b>Lon:</b> <span id="qrLonLabel"></span></p>
                <p style="font-size:0.9rem;"><b>Radio:</b> <span id="qrRadioLabel"></span> m</p>
                <div id="mapaLink" style="margin-top:8px;"></div>
            </div>
        </div>
    </div>

    <!-- Historial de registros de asistencia -->
    <div class="section-title">📋 Registros de Asistencia del Día</div>
    <div style="display:flex; gap:12px; margin-bottom:12px; flex-wrap:wrap; align-items:center;">
        <input type="date" id="fechaFiltro" style="width:auto; margin-bottom:0;" onchange="cargarRegistros()">
        <button class="btn-primary" style="width:auto; padding:10px 20px; font-size:0.85rem;" onclick="cargarRegistros()">🔄 Actualizar</button>
        <button class="btn-success" style="width:auto; padding:10px 20px; font-size:0.85rem;" onclick="exportarCSV()">📥 Exportar CSV</button>
    </div>
    <div id="tablaAsistencia" style="overflow-x:auto;"></div>

    <script>
        let qrInterval = null;
        let timerInterval = null;
        let segundosRestantes = 0;

        // Poner fecha de hoy por defecto
        document.getElementById('fechaFiltro').value = new Date().toISOString().slice(0, 10);
        cargarRegistros();

        function usarUbicacionActual() {
            if (!navigator.geolocation) return alert('Tu navegador no soporta geolocalización.');
            navigator.geolocation.getCurrentPosition(pos => {
                document.getElementById('latFija').value = pos.coords.latitude.toFixed(6);
                document.getElementById('lonFija').value = pos.coords.longitude.toFixed(6);
                alert('✅ Coordenadas actualizadas con tu posición actual.');
            }, () => alert('No se pudo obtener la ubicación.'));
        }

        function generarQR() {
            const lat = parseFloat(document.getElementById('latFija').value);
            const lon = parseFloat(document.getElementById('lonFija').value);
            const radio = parseInt(document.getElementById('radioMetros').value);
            if (isNaN(lat) || isNaN(lon) || isNaN(radio)) return alert('Completa todos los campos de configuración.');

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
            document.getElementById('mapaLink').innerHTML = `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" style="color:#0057A8; font-size:0.85rem;">🗺 Ver en Google Maps</a>`;
            document.getElementById('qrSection').style.display = 'block';

            // Timer de 5 minutos
            if (timerInterval) clearInterval(timerInterval);
            segundosRestantes = 300;
            actualizarTimer();
            timerInterval = setInterval(() => {
                segundosRestantes--;
                actualizarTimer();
                if (segundosRestantes <= 0) {
                    clearInterval(timerInterval);
                    document.getElementById('qrCanvas').innerHTML = '<p style="color:#dc2626; font-weight:600;">⏱ QR expirado. Regenera.</p>';
                }
            }, 1000);
        }

        function actualizarTimer() {
            const m = String(Math.floor(segundosRestantes / 60)).padStart(2, '0');
            const s = String(segundosRestantes % 60).padStart(2, '0');
            const el = document.getElementById('qrTimer');
            if (el) el.textContent = m + ':' + s;
        }

        async function cargarRegistros() {
            const fecha = document.getElementById('fechaFiltro').value;
            try {
                const res = await fetchAuth(`/api/asistencia/registros?fecha=${fecha}`);
                if (!res.ok) { document.getElementById('tablaAsistencia').innerHTML = '<p style="color:#6b7280;">Sin registros para esta fecha.</p>'; return; }
                const data = await res.json();
                if (!data.length) { document.getElementById('tablaAsistencia').innerHTML = '<p style="color:#6b7280; padding:12px;">No hay registros para esta fecha.</p>'; return; }
                let html = `<table><thead><tr>
                    <th>#</th><th>Técnico</th><th>Hora Entrada</th><th>Latitud</th><th>Longitud</th><th>Distancia</th><th>Estado</th>
                </tr></thead><tbody>`;
                data.forEach((r, i) => {
                    const estadoBadge = r.dentro_radio
                        ? '<span class="badge" style="background:#dcfce7; color:#16a34a;">✅ Dentro</span>'
                        : '<span class="badge" style="background:#fee2e2; color:#dc2626;">❌ Fuera</span>';
                    html += `<tr>
                        <td>${i+1}</td>
                        <td><b>${r.username}</b></td>
                        <td>${r.hora}</td>
                        <td>${r.lat_tecnico}</td>
                        <td>${r.lon_tecnico}</td>
                        <td>${r.distancia_m} m</td>
                        <td>${estadoBadge}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('tablaAsistencia').innerHTML = html;
            } catch (e) {
                document.getElementById('tablaAsistencia').innerHTML = '<p style="color:#dc2626;">Error al cargar registros.</p>';
            }
        }

        function exportarCSV() {
            const tabla = document.querySelector('#tablaAsistencia table');
            if (!tabla) return alert('No hay datos para exportar.');
            let csv = '';
            tabla.querySelectorAll('tr').forEach(row => {
                const cols = [...row.querySelectorAll('th, td')].map(c => '"' + c.innerText.replace(/"/g, '""') + '"');
                csv += cols.join(',') + '\\n';
            });
            const blob = new Blob([csv], { type: 'text/csv' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `asistencia_${document.getElementById('fechaFiltro').value}.csv`;
            a.click();
        }
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Control de Asistencia", contenido, "asistencia"))


# ------------------------------------------------------------
# CHECKIN – PÁGINA DEL TÉCNICO: escanea QR y registra ubicación
# ------------------------------------------------------------
@router.get("/app/checkin", response_class=HTMLResponse)
async def checkin_tecnico():
    contenido = """
    <script>if (window.role !== 'tecnico') { window.location.href = '/app/dashboard'; }</script>

    <div style="max-width:480px; margin:0 auto;">

        <!-- Estado inicial -->
        <div id="estadoInicial">
            <div class="evidencia-info" style="margin-bottom:20px; text-align:center;">
                <div style="font-size:3rem; margin-bottom:8px;">📍</div>
                <b style="font-size:1.1rem;">Registro de Asistencia</b><br>
                <span style="font-size:0.88rem;">Escanea el código QR para registrar tu entrada.</span>
            </div>

            <!-- Cámara para escanear QR -->
            <div style="background:white; border-radius:16px; padding:20px; box-shadow:0 4px 16px rgba(0,43,91,0.1); margin-bottom:20px; text-align:center;">
                <div class="section-title" style="margin-top:0;">📷 Escanear QR</div>
                <video id="qrVideo" style="width:100%; border-radius:10px; max-height:280px; background:#000;" autoplay playsinline></video>
                <canvas id="qrCanvasHidden" style="display:none;"></canvas>
                <p id="scanStatus" style="font-size:0.85rem; color:#6b7280; margin-top:8px;">Iniciando cámara...</p>
                <button class="btn-primary" style="margin-top:10px;" onclick="iniciarCamara()">🔄 Activar Cámara</button>
            </div>

            <!-- O bien, si ya viene con token en URL -->
            <div id="tokenUrlSection" style="display:none; background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px; padding:16px; margin-bottom:20px; text-align:center;">
                <p style="font-size:0.9rem; margin-bottom:12px;">✅ QR detectado desde enlace</p>
                <button class="btn-primary" onclick="procesarDesdeURL()">📍 Registrar mi Asistencia</button>
            </div>
        </div>

        <!-- Estado de procesamiento -->
        <div id="estadoProcesando" style="display:none; text-align:center; padding:40px 20px;">
            <div style="font-size:3rem; margin-bottom:12px;">⏳</div>
            <p style="font-weight:600; color:#374151;">Obteniendo tu ubicación...</p>
            <p style="font-size:0.85rem; color:#6b7280;">Asegúrate de tener el GPS activado.</p>
        </div>

        <!-- Resultado -->
        <div id="estadoResultado" style="display:none; text-align:center; padding:20px;">
        </div>

    </div>

    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
    <script>
        let streamCamera = null;
        let scanLoop = null;
        let qrParams = null;

        // Revisar si ya vienen parámetros en la URL
        window.addEventListener('DOMContentLoaded', () => {
            const params = new URLSearchParams(window.location.search);
            if (params.has('lat') && params.has('lon') && params.has('radio')) {
                qrParams = {
                    lat: parseFloat(params.get('lat')),
                    lon: parseFloat(params.get('lon')),
                    radio: parseInt(params.get('radio'))
                };
                document.getElementById('tokenUrlSection').style.display = 'block';
            } else {
                iniciarCamara();
            }
        });

        function iniciarCamara() {
            document.getElementById('scanStatus').textContent = 'Solicitando acceso a la cámara...';
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    streamCamera = stream;
                    const video = document.getElementById('qrVideo');
                    video.srcObject = stream;
                    video.play();
                    document.getElementById('scanStatus').textContent = '🔍 Apunta al código QR...';
                    scanLoop = setInterval(() => escanearFrame(), 400);
                })
                .catch(() => {
                    document.getElementById('scanStatus').textContent = '⚠️ No se pudo acceder a la cámara. Usa el enlace directo del QR.';
                });
        }

        function escanearFrame() {
            const video = document.getElementById('qrVideo');
            const canvas = document.getElementById('qrCanvasHidden');
            if (video.readyState !== video.HAVE_ENOUGH_DATA) return;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            if (code) {
                clearInterval(scanLoop);
                if (streamCamera) streamCamera.getTracks().forEach(t => t.stop());
                try {
                    const url = new URL(code.data);
                    const p = url.searchParams;
                    qrParams = {
                        lat: parseFloat(p.get('lat')),
                        lon: parseFloat(p.get('lon')),
                        radio: parseInt(p.get('radio'))
                    };
                    if (isNaN(qrParams.lat) || isNaN(qrParams.lon)) throw new Error('QR inválido');
                    document.getElementById('scanStatus').textContent = '✅ QR leído correctamente';
                    procesarCheckin();
                } catch {
                    document.getElementById('scanStatus').textContent = '❌ QR no reconocido. Intenta de nuevo.';
                    scanLoop = setInterval(() => escanearFrame(), 400);
                }
            }
        }

        function procesarDesdeURL() {
            if (!qrParams) return alert('No se detectaron parámetros del QR.');
            procesarCheckin();
        }

        function procesarCheckin() {
            document.getElementById('estadoInicial').style.display = 'none';
            document.getElementById('estadoProcesando').style.display = 'block';

            if (!navigator.geolocation) {
                mostrarResultado(false, 'Tu navegador no soporta geolocalización.');
                return;
            }

            navigator.geolocation.getCurrentPosition(
                pos => {
                    const latTec = pos.coords.latitude;
                    const lonTec = pos.coords.longitude;
                    const distancia = calcularDistancia(latTec, lonTec, qrParams.lat, qrParams.lon);
                    const dentroRadio = distancia <= qrParams.radio;
                    enviarRegistro(latTec, lonTec, distancia, dentroRadio);
                },
                err => {
                    mostrarResultado(false, 'No se pudo obtener tu ubicación GPS. Activa la localización e intenta de nuevo.');
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }

        async function enviarRegistro(latTec, lonTec, distancia, dentroRadio) {
            try {
                const res = await fetchAuth('/api/asistencia/registrar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        lat_fija: qrParams.lat,
                        lon_fija: qrParams.lon,
                        radio: qrParams.radio,
                        lat_tecnico: latTec,
                        lon_tecnico: lonTec,
                        distancia_m: Math.round(distancia),
                        dentro_radio: dentroRadio
                    })
                });
                const data = await res.json();
                mostrarResultado(dentroRadio, data.mensaje || (dentroRadio ? 'Asistencia registrada.' : 'Estás fuera del área permitida.'), latTec, lonTec, Math.round(distancia));
            } catch {
                mostrarResultado(false, 'Error al conectar con el servidor. Verifica tu conexión.');
            }
        }

        function mostrarResultado(exito, mensaje, lat, lon, distancia) {
            document.getElementById('estadoProcesando').style.display = 'none';
            const el = document.getElementById('estadoResultado');
            el.style.display = 'block';
            const ahora = new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
            const iconoGrande = exito ? '✅' : '❌';
            const color = exito ? '#16a34a' : '#dc2626';
            const bg = exito ? '#dcfce7' : '#fee2e2';
            const border = exito ? '#86efac' : '#fca5a5';
            el.innerHTML = `
                <div style="background:${bg}; border:2px solid ${border}; border-radius:20px; padding:32px 24px;">
                    <div style="font-size:4rem; margin-bottom:12px;">${iconoGrande}</div>
                    <h2 style="color:${color}; font-size:1.4rem; margin-bottom:8px;">${exito ? '¡Asistencia Registrada!' : 'No se pudo registrar'}</h2>
                    <p style="color:#374151; font-size:0.95rem; margin-bottom:16px;">${mensaje}</p>
                    ${lat ? `<div style="background:white; border-radius:12px; padding:12px; font-size:0.85rem; color:#374151; margin-bottom:16px; text-align:left;">
                        <p>🕐 <b>Hora:</b> ${ahora}</p>
                        <p>👤 <b>Técnico:</b> ${window.username}</p>
                        <p>📍 <b>Tu ubicación:</b> ${lat.toFixed(5)}, ${lon.toFixed(5)}</p>
                        <p>📏 <b>Distancia al punto:</b> ${distancia} m</p>
                    </div>` : ''}
                    <button class="btn-primary" onclick="window.location.href='/app/mis-tareas'">🏠 Ir a Mis Tareas</button>
                </div>`;
        }

        // Haversine: distancia en metros entre dos coordenadas
        function calcularDistancia(lat1, lon1, lat2, lon2) {
            const R = 6371000;
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLon/2) * Math.sin(dLon/2);
            return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        }
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Registrar Asistencia", contenido, "checkin"))
