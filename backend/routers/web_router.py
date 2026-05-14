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
                    {{ href: '/app/admin', label: '🛠 Panel de Administración' }},
                ];
                const visorMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/inventario', label: '📦 Inventarios' }},
                    {{ href: '/app/unidades', label: '📸 Registro de Unidades' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                ];
                const techMenu = [
                    {{ href: '/app/mis-tareas', label: '🎯 Mis Tareas' }},
                    {{ href: '/app/solicitud', label: '🔔 Nueva Solicitud' }},
                    {{ href: '/app/mis-tickets', label: '🎫 Mis Tickets' }},
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
            /* Visor: ocultar botones de acción */
    body.visor-mode .btn-primary,
    body.visor-mode .btn-danger,
    body.visor-mode .btn-success,
    body.visor-mode .btn-warning,
    body.visor-mode button:not(.logout-btn):not(.hamburger) { display: none !important; }
    body.visor-mode input, body.visor-mode select, body.visor-mode textarea { pointer-events: none; background: #f9fafb; }
    .visor-banner { background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 8px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; text-align: center; margin-bottom: 16px; }
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
# DASHBOARD (solo admin) - TABLA DE ESTADÍSTICAS ELIMINADA
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
                        const completadasSet = new Set(asignaciones.filter(a => a.estado === 'completada').map(a => a.unidad + '||' + a.actividad_id));
                        let headers = '<table><th>LOTE</th><th>#Económico</th>'; actividades.forEach(a => headers += `<th>${a}</th>`); headers += '</tr>';
                        let body = ''; unidades.forEach(u => { body += `<tr><td>${u.id_lote || ''}</td><td>${u.unit_number}</td>`; actividades.forEach(act => body += `<td>${completadasSet.has(u.unit_number + '||' + act) ? '✔' : '–'}</td>`); body += '</tr>'; });
                        document.getElementById('statusTable').innerHTML = `<table><thead>${headers}</thead><tbody>${body}</tbody></table>`;
                        const lotesMap = {}; unidades.forEach(u => { const lote = u.id_lote || 'Sin lote'; if (!lotesMap[lote]) lotesMap[lote] = []; lotesMap[lote].push(u); });
                        let lotesHtml = ''; for (const [lote, units] of Object.entries(lotesMap)) { lotesHtml += `<div style="margin-bottom:16px; border:1px solid #e0e0e0; border-radius:12px; overflow:hidden;"><div class="inv-info-bar" style="margin-bottom:0; cursor:pointer;" onclick="var d=this.nextElementSibling;d.style.display=d.style.display==='none'?'block':'none';">📦 Lote: ${lote} (${units.length} unidades) <span style="margin-left:auto;">▼</span></div><div style="display:none; padding:16px; background:white; overflow-x:auto;"><table><thead><tr><th>#Económico</th>${Object.values(camposSeries).map(s => `<th>${s}</th>`).join('')}</tr></thead><tbody>${units.map(u => `<tr><td>${u.unit_number}</td>${Object.keys(camposSeries).map(k => `<td>${u[k] || '—'}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div>`; }
                        document.getElementById('lotesContainer').innerHTML = lotesHtml;
                        const unidadEvEl = document.getElementById('unidadEv'); if (unidadEvEl) unidadEvEl.innerHTML = '<option value="">Selecciona unidad</option>' + unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} – ${u.id_lote || ''}</option>`).join('');
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
        function renderTabla() { let html = '<table><thead><tr><th>#</th>'; columnas.forEach(c => html += `<th>${c}</th>`); html += '<th>Acción</th></tr></thead><tbody>'; datos.forEach((fila, idx) => { html += `<tr><td>${idx+1}</td>`; columnas.forEach(c => html += `<td><input type="text" value="${fila[c] || ''}" onchange="datos[${idx}]['${c}'] = this.value" style="margin:0;"></td>`); html += `<td><button class="btn-danger" onclick="eliminarFila(${idx})">🗑</button><tr></tr>`; }); html += '</tbody></table>'; document.getElementById('inventarioTable').innerHTML = html; }
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
        async function cargarUnidades() { const res = await fetchAuth('/api/unidades/'); const unidades = await res.json(); let html = '<table><thead><tr><th>#Económico</th><th>Lote</th><th>VIN</th><th>Reefer Serial</th><th>Modelo</th><th>Motor</th><th>Compresor</th></tr></thead><tbody>'; if (Array.isArray(unidades)) unidades.forEach(u => html += `<tr><td>${u.unit_number}</td><td>${u.id_lote||''}</td><td>${u.vin_number||''}</td><td>${u.reefer_serial||''}</td><td>${u.reefer_model||''}</td><td>${u.engine_serial||''}</td><td>${u.compressor_serial||''}</td></tr>`); html += '</tbody></table>'; document.getElementById('unidadesList').innerHTML = html; }
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
# GESTIÓN DE USUARIOS (admin) - CORREGIDO: se añadió opción "visor"
# ------------------------------------------------------------
@router.get("/app/usuarios", response_class=HTMLResponse)
async def usuarios():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div class="section-title">👥 Usuarios Registrados</div>
    <div id="usuariosList"></div>
    <div class="section-title admin-only">➕ Crear Nuevo Usuario</div>
    <form id="usuarioForm" class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px;">
        <input type="text" id="username" placeholder="Nombre de usuario" required>
        <input type="password" id="password" placeholder="Contraseña" required>
        <select id="role" required>
            <option value="tecnico">Técnico</option>
            <option value="admin">Administrador</option>
            <option value="visor">Visor (solo lectura)</option>
        </select>
        <button type="submit" class="btn-primary" style="grid-column: span 3;">👤 Crear Usuario</button>
    </form>
    <script>
        const fetchAuth = window.fetchAuth;
        
        async function cargarUsuarios() { 
            try {
                const res = await fetchAuth('/api/usuarios/'); 
                const usuarios = await res.json(); 
                let html = '<table><thead><tr><th>Usuario</th><th>Rol</th><th>Acción</th></tr></thead><tbody>'; 
                if (Array.isArray(usuarios)) {
                    usuarios.forEach(u => {
                        const rolTexto = u.role === 'admin' ? '🛡 Administrador' : (u.role === 'tecnico' ? '🔧 Técnico' : '👁 Visor');
                        html += `<tr><td>${u.username}</td><td>${rolTexto}</td><td><button class="btn-danger" onclick="eliminarUsuario(${u.id})">🗑️</button></td></tr>`;
                    });
                }
                html += '</tbody></table>'; 
                document.getElementById('usuariosList').innerHTML = html;
            } catch (err) {
                console.error('Error cargando usuarios:', err);
                document.getElementById('usuariosList').innerHTML = '<p style="color:red;">Error al cargar usuarios</p>';
            }
        }
        
        async function eliminarUsuario(id) { 
            if (confirm('¿Eliminar usuario?')) { 
                const res = await fetchAuth('/api/usuarios/' + id, { method: 'DELETE' }); 
                if (res.ok) cargarUsuarios();
                else alert('Error al eliminar usuario');
            } 
        }
        
        document.getElementById('usuarioForm').addEventListener('submit', async (e) => { 
            e.preventDefault(); 
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const role = document.getElementById('role').value;
            
            if (!username || !password) {
                alert('Complete todos los campos');
                return;
            }
            
            try {
                const res = await fetchAuth('/api/usuarios/', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ username, password, role }) 
                });
                
                if (res.ok) {
                    alert('Usuario creado exitosamente'); 
                    cargarUsuarios();
                    document.getElementById('usuarioForm').reset();
                } else {
                    const error = await res.json();
                    alert('Error: ' + (error.detail || 'No se pudo crear el usuario'));
                }
            } catch (err) {
                alert('Error de conexión: ' + err.message);
            }
        });
        
        cargarUsuarios();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("👥 Gestión de Usuarios", contenido, "usuarios"))
# ------------------------------------------------------------
# PANEL DE ADMINISTRACIÓN (admin)
# ------------------------------------------------------------
@router.get("/app/admin", response_class=HTMLResponse)
async def admin():
    contenido = """
    <script> if (window.role !== 'admin') { window.location.href = '/app/mis-tareas'; } </script>
    <div style="display:flex; gap:8px; margin-bottom:16px;">
        <button class="btn-primary" onclick="mostrarPestana('actividades')">🗂 Actividades</button>
        <button class="btn-primary" onclick="mostrarPestana('usuarios')">👥 Usuarios</button>
        <button class="btn-primary" onclick="mostrarPestana('unidades')">🚛 Unidades</button>
        <button class="btn-primary" onclick="mostrarPestana('sql')">🗄 SQL Directo</button>
    </div>
    <div id="panelContenido"></div>
    <script>
        const fetchAuth = window.fetchAuth;
        const pestanas = {
            actividades: async () => {
                document.getElementById('panelContenido').innerHTML = `<div class="section-title">Filtrar por estado</div><select id="filtroEstado" onchange="cargarActividades()"><option value="Todos">Todos</option><option value="solicitado">Solicitado</option><option value="pendiente">Pendiente</option><option value="en_proceso">En Proceso</option><option value="completada">Completada</option></select><div id="listaActividades"></div>`;
                window.cargarActividades = async () => { const estado = document.getElementById('filtroEstado').value; const url = estado === 'Todos' ? '/api/asignaciones/' : `/api/asignaciones/?estado=${estado}`; const [asigRes, usuariosRes] = await Promise.all([fetchAuth(url), fetchAuth('/api/usuarios/')]); const asigs = await asigRes.json(); const usuarios = await usuariosRes.json(); const tecnicosSet = new Set(usuarios.filter(u => u.role === 'tecnico').map(u => u.username)); const huerfanas = asigs.filter(a => !tecnicosSet.has(a.tecnico)); let h = ''; if (huerfanas.length) h += `<div class="bloqueo-card"><p>⚠️ Existen <b>${huerfanas.length}</b> asignaciones con usuarios no técnicos (ej: ${[...new Set(huerfanas.map(a => a.tecnico))].join(', ')}).</p></div>`; asigs.forEach(a => { const esTecnico = tecnicosSet.has(a.tecnico); const borderColor = esTecnico ? '#e5e7eb' : '#fca5a5', bg = esTecnico ? 'white' : '#fff5f5'; const warning = esTecnico ? '' : ' <span style="color:#dc2626;">⚠️ No es técnico</span>'; h += `<div style="background:${bg}; border-left:5px solid ${borderColor}; padding:10px; margin-bottom:6px; border-radius:8px;"><b>ID ${a.id}</b> · ${a.unidad} — ${a.actividad_id} (<b>${a.tecnico}</b>${warning}) [${a.estado}]<button class="btn-danger" onclick="eliminarActividad(${a.id})" style="float:right;">🗑️</button></div>`; }); document.getElementById('listaActividades').innerHTML = h || 'Sin actividades.'; };
                window.eliminarActividad = async (id) => { if (confirm('¿Eliminar actividad?')) { await fetchAuth('/api/asignaciones/' + id, { method: 'DELETE' }); cargarActividades(); } };
                cargarActividades();
            },
            usuarios: async () => { const res = await fetchAuth('/app/usuarios'); const html = await res.text(); const parser = new DOMParser(); const doc = parser.parseFromString(html, 'text/html'); document.getElementById('panelContenido').innerHTML = doc.querySelector('.main-content').innerHTML; },
            unidades: async () => { const res = await fetchAuth('/app/unidades'); const html = await res.text(); const parser = new DOMParser(); const doc = parser.parseFromString(html, 'text/html'); document.getElementById('panelContenido').innerHTML = doc.querySelector('.main-content').innerHTML; },
            sql: () => { document.getElementById('panelContenido').innerHTML = `<textarea id="sqlInput" placeholder="SELECT * FROM asignaciones;" rows="6" style="width:100%;"></textarea><button class="btn-primary" onclick="ejecutarSQL()">▶️ Ejecutar</button><div id="sqlResult" style="margin-top:16px;"></div>`; window.ejecutarSQL = async () => { const sql = document.getElementById('sqlInput').value.trim(); if (!sql) return; try { const res = await fetchAuth('/api/admin/execute-sql', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sql }) }); const data = await res.json(); if (data.error) { document.getElementById('sqlResult').innerHTML = `<p style="color:red;">${data.error}</p>`; return; } if (Array.isArray(data) && data.length) { let table = '</table><thead><tr>'; Object.keys(data[0]).forEach(k => table += `<th>${k}</th>`); table += '</tr></thead><tbody>'; data.forEach(row => { table += '<tr>'; Object.values(row).forEach(v => table += `<td>${v}</td>`); table += '</tr>'; }); table += '</tbody></tr>'; document.getElementById('sqlResult').innerHTML = table; } else document.getElementById('sqlResult').innerHTML = '<p>Consulta ejecutada sin resultados.</p>'; } catch (e) { alert('Error: ' + e.message); } }; }
        };
        function mostrarPestana(nombre) { pestanas[nombre](); }
        mostrarPestana('actividades');
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
            const comentario = prompt('Comentario obligatorio:'); if (!comentario) return;
            const res = await fetchAuth('/api/asignaciones/' + id + '/finalizar', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ comentario }) });
            if (res.ok) cargarTareas(); else { const err = await res.json(); alert('Error: ' + (err.detail || 'No se pudo finalizar')); }
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
                await fetchAuth('/api/unidades/series', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); alert('Series guardadas'); cerrarModal();
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
        async function cargarTickets() { const res = await fetchAuth('/api/tickets/'); const tickets = await res.json(); let html = ''; if (tickets.length) tickets.forEach(t => { const estado = t.atendido ? (t.reporte_enviado ? '🟢 Completado' : '🟡 Atendido (sin reporte)') : '🔴 No atendido'; const color = t.atendido ? (t.reporte_enviado ? 'var(--carrier-success)' : 'var(--carrier-warn)') : 'var(--carrier-danger)'; html += `<div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px; border-radius:0 12px 12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05);"><span style="font-size:1.5rem; font-weight:800; color:var(--carrier-blue);">#${t.ticket_num}</span><span class="badge" style="background:${color}; color:white;">${estado}</span><p><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p><p><b>Descripción:</b> ${t.descripcion}</p><small>Creado: ${t.fecha_creacion}</small></div>`; }); if (!html) html = '<p>🎫 No tienes tickets.</p>'; document.getElementById('ticketsList').innerHTML = html; }
        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Mis Tickets", contenido, "mis-tickets"))
