from fastapi import APIRouter
from fastapi.responses import HTMLResponse

# Importar módulos de asistencia
from asistencia.routes import router as asistencia_router
from asistencia.templates import get_checkin_template, ASISTENCIA_STYLES

router = APIRouter()

# Incluir routers de asistencia
router.include_router(asistencia_router)

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
    .hamburger { display: none; position: fixed; top: 14px; left: 14px; z-index: 300; background: var(--carrier-blue); color: white; border: none; border-radius: 10px; width: 44px; height: 44px; font-size: 1.3rem; cursor: pointer; box-shadow: 0 4px 12px rgba(0,43,91,0.35); align-items: center; justify-content: center; }
    .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.45); z-index: 99; }
    .status-table-wrapper {
        overflow-x: auto;
        border-radius: 16px;
        background: white;
        box-shadow: 0 4px 20px rgba(0,43,91,0.08);
    }
    .status-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.75rem;
        min-width: 1000px;
    }
    .status-table th {
        background: linear-gradient(135deg, #002B5B, #0057A8);
        color: white;
        padding: 12px 8px;
        text-align: center;
        font-weight: 600;
        font-size: 0.75rem;
        border-right: 1px solid rgba(255,255,255,0.15);
    }
    .status-table th:last-child { border-right: none; }
    .status-table td {
        padding: 10px 8px;
        text-align: center;
        border-bottom: 1px solid #e5e7eb;
    }
    .status-table tbody tr:hover td { background: #e8f0fb; }
    .status-table .lote-cell { font-weight: 700; color: #002B5B; background: #f8fafc; }
    .status-table .unit-cell { font-family: monospace; font-weight: 600; }
    .status-badge-complete {
        display: inline-block;
        width: 28px;
        height: 28px;
        line-height: 28px;
        background: #16a34a;
        color: white;
        border-radius: 50%;
        font-weight: bold;
        font-size: 1rem;
    }
    .status-badge-pending {
        display: inline-block;
        width: 28px;
        height: 28px;
        line-height: 28px;
        background: #f3f4f6;
        color: #9ca3af;
        border-radius: 50%;
        font-size: 0.8rem;
    }
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
# FUNCIÓN AUXILIAR CON SIDEBAR
# ------------------------------------------------------------
def pagina_con_menu(titulo: str, contenido: str, pagina_activa: str = "", extra_scripts: str = "") -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
        <meta name="theme-color" content="#002B5B">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Carrier">
        <link rel="manifest" href="/static/manifest.json">
        <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
        <title>{titulo} – Carrier Transicold</title>
        {BASE_STYLE}
        <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
        <script>
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/static/sw.js')
                    .catch(err => console.warn('SW error:', err));
            }}
        </script>
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
                    {{ href: '/app/horarios', label: '🗓 Horarios Semanales' }},
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
                    {{ href: '/app/horarios', label: '🗓 Horarios Semanales' }},
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
# DASHBOARD
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
    <div id="statusTable" style="margin-bottom:32px;"></div>
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
                        let tableHtml = `
                            <div class="status-table-wrapper">
                                <table class="status-table">
                                    <thead>
                                        <tr>
                                            <th>LOTE</th>
                                            <th>#Económico</th>
                                            ${actividades.map(a => `<th>${a}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                        `;
                        unidades.forEach((u, idx) => {
                            const bgColor = idx % 2 === 0 ? 'white' : '#fafafa';
                            tableHtml += `
                                        <tr style="background: ${bgColor};">
                                            <td class="lote-cell">${u.id_lote || '—'}</td>
                                            <td class="unit-cell">${u.unit_number}</td>
                            `;
                            actividades.forEach(act => {
                                const completada = completadasSet.has(u.unit_number + '||' + act);
                                tableHtml += `
                                            <td>
                                                ${completada 
                                                    ? '<span class="status-badge-complete">✓</span>' 
                                                    : '<span class="status-badge-pending">—</span>'}
                                            </td>
                                `;
                            });
                            tableHtml += `
                                        </tr>
                            `;
                        });
                        tableHtml += `
                                    </tbody>
                                </table>
                            </div>
                        `;
                        document.getElementById('statusTable').innerHTML = tableHtml;
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
                                        <thead><tr><th>#Económico</th>${Object.values(camposSeries).map(s => `<th>${s}</th>`).join('')}</table></thead>
                                        <tbody>${units.map(u => `<tr><td>${u.unit_number}</td>${Object.keys(camposSeries).map(k => `<td>${u[k] || '—'}</td>`).join('')}</tr>`).join('')}</tbody>
                                    </table>
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
        async function cargarSolicitudes() {
            const lista = document.getElementById('listaSolicitudes');
            lista.innerHTML = '<p>Cargando...</p>';
            try {
                const res = await fetchAuth('/api/asignaciones/?estado=solicitado');
                if (!res.ok) throw new Error('Error');
                const data = await res.json();
                let html = '';
                if (!Array.isArray(data) || data.length === 0) { html = '<p>No hay solicitudes pendientes.</p>'; }
                else { data.forEach(s => { html += `<div style="background:white;border-left:4px solid var(--carrier-warn);padding:12px 16px;margin-bottom:8px;border-radius:8px;display:flex;justify-content:space-between;align-items:center;"><div><b>${s.actividad_id}</b> — Unidad: <b>${s.unidad}</b><br><small>Técnico: ${s.tecnico}</small></div><div style="display:flex;gap:8px;"><button class="btn-success" onclick="aprobar(${s.id})">✅ Aprobar</button><button class="btn-danger" onclick="rechazar(${s.id})">❌ Rechazar</button></div></div>`; }); }
                lista.innerHTML = html;
            } catch (err) { lista.innerHTML = '<p style="color:var(--carrier-danger);">Error al cargar solicitudes.</p>'; }
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
                if (activas.length > 0 && !confirm(`Ya existe una tarea activa para esta combinación. ¿Deseas crear la orden de todos modos?`)) { msgDiv.innerHTML = ''; return; }
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
            const unidad = document.getElementById('unidad').value;
            const vin = document.getElementById('vin').value;
            const descripcion = document.getElementById('descripcion').value;
            const tecnico = document.getElementById('tecnico').value;
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
        function renderTabla() { let html = '<table class="data-table"><thead><tr><th>#</th>'; columnas.forEach(c => html += `<th>${c}</th>`); html += '<th>Acción</th></tr></thead><tbody>'; datos.forEach((fila, idx) => { html += `<tr><td style="text-align:center;">${idx+1}</td>`; columnas.forEach(c => html += `<td><input type="text" value="${fila[c] || ''}" onchange="datos[${idx}]['${c}'] = this.value" style="margin:0;"></td>`); html += `<td><button class="btn-danger" onclick="eliminarFila(${idx})">🗑</button></td>`; }); html += '</tbody></table>'; document.getElementById('inventarioTable').innerHTML = html; }
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
        async function cargarUnidades() { const res = await fetchAuth('/api/unidades/'); const unidades = await res.json(); let html = '<table class="data-table"><thead><tr><th>#Económico</th><th>Lote</th><th>VIN</th><th>Reefer Serial</th><th>Modelo</th><th>Motor</th><th>Compresor</th></tr></thead><tbody>'; if (Array.isArray(unidades)) unidades.forEach(u => html += `<tr><td>${u.unit_number}</td><td>${u.id_lote||''}</td><td style="font-family:monospace;">${u.vin_number||''}</td><td>${u.reefer_serial||''}</td><td>${u.reefer_model||''}</td><td style="font-family:monospace;">${u.engine_serial||''}</td><td>${u.compressor_serial||''}</td>`); html += '</tbody></table>'; document.getElementById('unidadesList').innerHTML = html; }
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
# GESTIÓN DE USUARIOS (admin)
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
        <select id="role" required><option value="tecnico">Técnico</option><option value="admin">Administrador</option><option value="visor">Visor (solo lectura)</option></select>
        <button onclick="crearUsuario()" class="btn-primary" style="grid-column: span 3;">👤 Crear Usuario</button>
    </div>
    <script>
        const fetchAuth = window.fetchAuth;
        async function cargarUsuarios() {
            const res = await fetchAuth('/api/usuarios/');
            const usuarios = await res.json();
            let html = '<table class="data-table"><thead><tr><th>Usuario</th><th>Rol</th><th style="text-align:center;">Acciones</th></tr></thead><tbody>';
            if (Array.isArray(usuarios)) usuarios.forEach(u => {
                const rolTexto = u.role === 'admin' ? '🛡 Administrador' : (u.role === 'tecnico' ? '🔧 Técnico' : '👁 Visor');
                const acciones = window.role === 'admin' ? `<button class="btn-warning" onclick="abrirModalPassword(${u.id}, '${u.username}')" style="padding:6px 14px;font-size:0.82rem;margin-right:6px;">🔑 Cambiar Contraseña</button><button class="btn-danger" onclick="eliminarUsuario(${u.id}, '${u.username}')" style="padding:6px 14px;font-size:0.82rem;">🗑️ Eliminar</button>` : '—';
                html += `<tr><td><b>${u.username}</b></td><td style="text-align:center;">${rolTexto}</td><td style="text-align:center;">${acciones}</td></tr>`;
            });
            html += '</tbody></table>';
            document.getElementById('usuariosList').innerHTML = html;
        }
        function abrirModalPassword(userId, username) {
            const modal = document.createElement('div');
            modal.id = 'modalPassword';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;';
            modal.innerHTML = `<div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:460px;"><h3>Cambiar Contraseña - ${username}</h3><input id="inputNuevaPwd" type="password" placeholder="Nueva contraseña"><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:20px;"><button onclick="document.getElementById('modalPassword').remove()">Cancelar</button><button onclick="guardarPassword(${userId})">Guardar</button></div></div>`;
            document.body.appendChild(modal);
        }
        async function guardarPassword(userId) {
            const pwd = document.getElementById('inputNuevaPwd').value;
            if (!pwd || pwd.length < 4) return alert('Mínimo 4 caracteres');
            await fetchAuth('/api/usuarios/' + userId + '/password', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_password: pwd }) });
            document.getElementById('modalPassword').remove();
            alert('Contraseña actualizada');
        }
        async function crearUsuario() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('newUserPassword').value;
            const role = document.getElementById('role').value;
            if (!username || !password) return alert('Completa todos los campos');
            await fetchAuth('/api/usuarios/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, role }) });
            document.getElementById('username').value = '';
            document.getElementById('newUserPassword').value = '';
            cargarUsuarios();
        }
        async function eliminarUsuario(id, nombre) {
            if (!confirm(`¿Eliminar al usuario "${nombre}"?`)) return;
            await fetchAuth('/api/usuarios/' + id, { method: 'DELETE' });
            cargarUsuarios();
        }
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
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
    .panel { padding: 1rem 0; }
    .tabs { display: flex; gap: 8px; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .tab-btn { background: var(--navy); color: white; border: none; border-radius: 8px; padding: 9px 18px; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 7px; }
    .tab-btn.active { background: #1e4fc0; outline: 2px solid #6fa3f7; }
    .section { display: none; }
    .section.active { display: block; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .data-table th { background: #002B5B; color: white; padding: 9px 10px; text-align: left; }
    .data-table td { padding: 9px 10px; border-bottom: 0.5px solid #e5e7eb; }
    .editor-panel { width: 268px; background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; display: none; margin-left: 12px; }
    .editor-panel.visible { display: block; }
    .sql-area { width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; font-family: monospace; min-height: 110px; margin-bottom: 10px; }
    </style>
    <div class="panel">
        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('actividades')"><i class="ti ti-activity"></i> Actividades</button>
            <button class="tab-btn" onclick="showTab('usuarios')"><i class="ti ti-users"></i> Usuarios</button>
            <button class="tab-btn" onclick="showTab('unidades')"><i class="ti ti-truck"></i> Unidades</button>
            <button class="tab-btn" onclick="showTab('sql')"><i class="ti ti-terminal-2"></i> SQL Directo</button>
        </div>
        <div id="sec-actividades" class="section active"><div id="actividadesContent">Cargando...</div></div>
        <div id="sec-usuarios" class="section"><div id="usuariosContent">Cargando...</div></div>
        <div id="sec-unidades" class="section"><div id="unidadesContent">Cargando...</div></div>
        <div id="sec-sql" class="section">
            <textarea class="sql-area" id="sql-input">SELECT * FROM asignaciones LIMIT 10;</textarea>
            <button class="btn-primary" onclick="ejecutarSQL()">Ejecutar</button>
            <div id="sql-result" style="margin-top:10px; padding:10px; background:#f3f4f6; border-radius:8px; font-family:monospace; white-space:pre-wrap;"></div>
        </div>
    </div>
    <script>
        const fetchAuth = window.fetchAuth;
        function showTab(t) {
            ['actividades','usuarios','unidades','sql'].forEach(s=>{
                document.getElementById('sec-'+s).classList.toggle('active',s===t);
                document.querySelector(`.tab-btn:contains(${s})`).classList.toggle('active',s===t);
            });
        }
        async function ejecutarSQL() {
            const sql = document.getElementById('sql-input').value;
            const res = await fetchAuth('/api/admin/execute-sql', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({sql}) });
            const data = await res.json();
            document.getElementById('sql-result').innerHTML = JSON.stringify(data, null, 2);
        }
        async function cargarActividades() {
            const res = await fetchAuth('/api/asignaciones/');
            const data = await res.json();
            let html = '<table class="data-table"><thead><tr><th>ID</th><th>Unidad</th><th>Actividad</th><th>Técnico</th><th>Estado</th></tr></thead><tbody>';
            data.forEach(r => html += `<tr><td>${r.id}</td><td>${r.unidad}</td><td>${r.actividad_id}</td><td>${r.tecnico}</td><td>${r.estado}</td></tr>`);
            html += '</tbody></table>';
            document.getElementById('actividadesContent').innerHTML = html;
        }
        async function cargarUsuariosAdmin() {
            const res = await fetchAuth('/api/usuarios/');
            const data = await res.json();
            let html = '<table class="data-table"><thead><tr><th>ID</th><th>Usuario</th><th>Rol</th></tr></thead><tbody>';
            data.forEach(r => html += `<tr><td>${r.id}</td><td>${r.username}</td><td>${r.role}</td></tr>`);
            html += '</tbody></table>';
            document.getElementById('usuariosContent').innerHTML = html;
        }
        async function cargarUnidadesAdmin() {
            const res = await fetchAuth('/api/unidades/');
            const data = await res.json();
            let html = '<table class="data-table"><thead><tr><th>ID</th><th>#Económico</th><th>Lote</th><th>VIN</th></tr></thead><tbody>';
            data.forEach(r => html += `<tr><td>${r.id}</td><td>${r.unit_number}</td><td>${r.id_lote}</td><td>${r.vin_number}</td></tr>`);
            html += '</tbody><tr>';
            document.getElementById('unidadesContent').innerHTML = html;
        }
        cargarActividades(); cargarUsuariosAdmin(); cargarUnidadesAdmin();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🛠 Panel de Administración", contenido, "admin"))


# ------------------------------------------------------------
# MIS TAREAS
# ------------------------------------------------------------
@router.get("/app/mis-tareas", response_class=HTMLResponse)
async def mis_tareas():
    contenido = """
    <script> if (window.role === 'visor') { window.location.href = '/app/dashboard'; } </script>
    <div id="tareasList"></div>
    <script>
        const fetchAuth = window.fetchAuth, username = window.username;
        function mostrarModal(html) { const modal = document.createElement('div'); modal.className = 'modal'; modal.style.display = 'flex'; modal.innerHTML = html; document.body.appendChild(modal); return modal; }
        function cerrarModal() { const modal = document.querySelector('.modal'); if (modal) document.body.removeChild(modal); }
        async function cargarTareas() {
            const res = await fetchAuth('/api/asignaciones/?tecnico=' + username);
            if (!res.ok) { document.getElementById('tareasList').innerHTML = '<p style="color:red;">Error al cargar tareas.</p>'; return; }
            const tareas = await res.json();
            const activas = Array.isArray(tareas) ? tareas.filter(t => t.estado === 'pendiente' || t.estado === 'en_proceso') : [];
            let html = '';
            if (activas.length === 0) { html = '<p>✅ No tienes tareas activas.</p>'; }
            else {
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
            const comentario = prompt('Comentario del trabajo realizado:');
            if (!comentario) return alert('El comentario es obligatorio');
            const res = await fetchAuth('/api/asignaciones/' + id + '/finalizar', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ comentario }) });
            if (res.ok) cargarTareas(); else alert('Error al finalizar');
        }
        async function subirEvidencia(tareaId, unidad) {
            const cntRes = await fetchAuth(`/api/evidencias/count?unit_number=${unidad}&tecnico=${username}`); const cnt = await cntRes.json();
            const totalPrev = cnt.total || 0; const restantes = 100 - totalPrev;
            if (restantes <= 0) return alert('Límite de 100 fotos alcanzado');
            const modal = mostrarModal(`<div class="modal-content"><h3>📸 Subir Evidencia – ${unidad}</h3><p>Guardadas: <b>${totalPrev}</b> · Disponibles: <b>${restantes}</b></p><input type="file" id="fotosInput" multiple accept="image/*"><div id="previewFotos" style="display:flex; flex-wrap:wrap; gap:8px; margin:12px 0;"></div><button class="btn-primary" id="btnGuardarFotos">💾 Guardar Fotos</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('fotosInput').addEventListener('change', e => { const files = Array.from(e.target.files).slice(0, restantes); const previewDiv = document.getElementById('previewFotos'); previewDiv.innerHTML = ''; files.forEach(f => { const r = new FileReader(); r.onload = ev => { const img = document.createElement('img'); img.src = ev.target.result; img.style.cssText = 'width:70px;height:70px;object-fit:cover;border-radius:8px;'; previewDiv.appendChild(img); }; r.readAsDataURL(f); }); });
            document.getElementById('btnGuardarFotos').onclick = async () => { const input = document.getElementById('fotosInput'); if (!input.files.length) return alert('Selecciona fotos'); const fd = new FormData(); fd.append('unidad', unidad); fd.append('tecnico', username); for (let f of input.files) fd.append('files', f); await fetchAuth('/api/evidencias/upload', { method: 'POST', body: fd }); alert('Fotos guardadas'); cerrarModal(); };
        }
        async function tomarValores(tareaId) {
            const camposRes = await fetchAuth('/api/toma-valores/campos'); const campos = await camposRes.json();
            let camposHTML = campos.length ? campos.map((c,i) => `<input type="text" id="campo_${i}" placeholder="${c.campo_nombre}">`).join('') : '<p>No hay campos configurados.</p>';
            const modal = mostrarModal(`<div class="modal-content"><h3>📊 Toma de Valores</h3><div id="camposValores">${camposHTML}</div><button class="btn-primary" id="btnGuardarValores">💾 Guardar Valores</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarValores').onclick = async () => { const valores = {}; campos.forEach((c,i) => valores[c.campo_nombre] = document.getElementById('campo_'+i).value); await fetchAuth('/api/toma-valores/guardar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ asignacion_id: tareaId, valores }) }); alert('Valores guardados'); cerrarModal(); };
        }
        async function tomarSeries(tareaId) {
            const camposSeries = [{ key: 'vin_number', label: 'VIN Number' },{ key: 'reefer_serial', label: 'Serie del Reefer' },{ key: 'reefer_model', label: 'Modelo del Reefer' },{ key: 'evaporator_serial_mjs11', label: 'Evaporador MJS11' },{ key: 'evaporator_serial_mjd22', label: 'Evaporador MJD22' },{ key: 'engine_serial', label: 'Motor' },{ key: 'compressor_serial', label: 'Compresor' },{ key: 'generator_serial', label: 'Generador' },{ key: 'battery_charger_serial', label: 'Cargador de Batería' }];
            let inputs = camposSeries.map((c,i) => `<input type="text" id="serie_${i}" placeholder="${c.label}"><input type="hidden" id="serie_key_${i}" value="${c.key}">`).join('');
            const modal = mostrarModal(`<div class="modal-content"><h3>🔢 Toma de Series</h3><div id="camposSeries">${inputs}</div><button class="btn-primary" id="btnGuardarSeries">💾 Guardar Series</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarSeries').onclick = async () => { const tareasRes = await fetchAuth('/api/asignaciones/?tecnico=' + username + '&estado=en_proceso'); const tareas = await tareasRes.json(); const tarea = Array.isArray(tareas) ? tareas.find(t => t.id == tareaId) : null; if (!tarea) return alert('Tarea no encontrada'); const keys = [...document.querySelectorAll('[id^="serie_key_"]')].map(el => el.value); const values = { unit_number: tarea.unidad }; keys.forEach((key,i) => values[key] = document.getElementById('serie_'+i).value); await fetchAuth('/api/unidades/series/update', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); cerrarModal(); cargarTareas(); alert('Series guardadas'); };
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
            if (activa) { msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">Ya existe una tarea activa para esta combinación (técnico: ${activa.tecnico}).</p>`; return; }
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
            if (tickets.length) tickets.forEach(t => {
                const estado = t.atendido ? (t.reporte_enviado ? '🟢 Completado' : '🟡 Atendido (sin reporte)') : '🔴 No atendido';
                const color = t.atendido ? (t.reporte_enviado ? 'var(--carrier-success)' : 'var(--carrier-warn)') : 'var(--carrier-danger)';
                let acciones = '';
                if (!t.atendido) acciones = `<button class="btn-warning" onclick="atenderTicket(${t.id})">✅ Marcar como atendido</button>`;
                else if (!t.reporte_enviado) acciones = `<button class="btn-primary" onclick="enviarReporte(${t.id})">📤 Enviar reporte final</button>`;
                html += `<div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px;"><span style="font-size:1.5rem; font-weight:800;">#${t.ticket_num}</span><span class="badge" style="background:${color}; color:white;">${estado}</span><p><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p><p><b>Descripción:</b> ${t.descripcion}</p>${acciones}</div>`;
            });
            if (!html) html = '<p>🎫 No tienes tickets.</p>';
            document.getElementById('ticketsList').innerHTML = html;
        }
        async function atenderTicket(id) { if (!confirm('¿Marcar este ticket como atendido?')) return; await fetchAuth('/api/tickets/' + id + '/atender', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ atendido: true }) }); cargarTickets(); }
        async function enviarReporte(ticketId) { const reporte = prompt('Describe el trabajo realizado:'); if (!reporte) return alert('El reporte es obligatorio'); await fetchAuth('/api/tickets/' + ticketId + '/report', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reporte }) }); cargarTickets(); }
        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Mis Tickets", contenido, "mis-tickets"))


# ------------------------------------------------------------
# PANEL DE ASIGNACIÓN POR CLUSTER
# ------------------------------------------------------------
@router.get("/app/cluster", response_class=HTMLResponse)
async def panel_cluster():
    contenido = """
    <div id="resumenCluster" style="display:none; background:#f3f4f6; border-radius:12px; padding:16px; margin-bottom:20px;"></div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px;">
        <div style="background:white; border-radius:12px; padding:16px;">
            <div style="font-weight:500; margin-bottom:12px;">🔧 Técnicos</div>
            <div id="listaTecnicos"></div>
        </div>
        <div style="background:white; border-radius:12px; padding:16px;">
            <div style="font-weight:500; margin-bottom:12px;">🎯 Actividades</div>
            <div id="listaActividades"></div>
        </div>
        <div style="background:white; border-radius:12px; padding:16px;">
            <div style="font-weight:500; margin-bottom:12px;">🚛 Unidades</div>
            <div id="listaUnidades"></div>
        </div>
    </div>
    <div style="margin-top:20px; background:white; border-radius:12px; padding:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div id="contadorResumen">Selecciona técnicos, actividades y unidades</div>
            <button id="btnAsignar" class="btn-primary" onclick="ejecutarAsignacion()" style="width:auto;">⚡ Asignar Cluster</button>
        </div>
    </div>
    <script>
        const fetchAuth = window.fetchAuth;
        let todosTecnicos = [], todasActividades = [], todasUnidades = [];
        function getSeleccionados(tipo) { return [...document.querySelectorAll(`input[data-tipo="${tipo}"]:checked`)].map(c => c.value); }
        function actualizarContador() { const t = getSeleccionados('tecnicos').length; const a = getSeleccionados('actividades').length; const u = getSeleccionados('unidades').length; const total = t * a * u; const el = document.getElementById('contadorResumen'); if (total === 0) el.innerHTML = 'Selecciona técnicos, actividades y unidades'; else el.innerHTML = `<b>${t}</b> técnico(s) × <b>${a}</b> actividad(es) × <b>${u}</b> unidad(es) = <b style="color:var(--carrier-blue);">${total} asignaciones</b>`; }
        async function cargarDatos() {
            const [resTec, resAct, resUni] = await Promise.all([fetchAuth('/api/cluster/tecnicos'), fetchAuth('/api/cluster/actividades'), fetchAuth('/api/cluster/unidades')]);
            todosTecnicos = await resTec.json(); todasActividades = await resAct.json(); todasUnidades = await resUni.json();
            document.getElementById('listaTecnicos').innerHTML = todosTecnicos.map(t => `<label><input type="checkbox" data-tipo="tecnicos" value="${t.username}" onchange="actualizarContador()"> ${t.username}</label><br>`).join('');
            document.getElementById('listaActividades').innerHTML = todasActividades.map(a => `<label><input type="checkbox" data-tipo="actividades" value="${a.nombre}" onchange="actualizarContador()"> ${a.nombre}</label><br>`).join('');
            document.getElementById('listaUnidades').innerHTML = todasUnidades.map(u => `<label><input type="checkbox" data-tipo="unidades" value="${u.unit_number}" onchange="actualizarContador()"> ${u.unit_number} (${u.id_lote})</label><br>`).join('');
        }
        async function ejecutarAsignacion() {
            const tecnicos = getSeleccionados('tecnicos'), actividades = getSeleccionados('actividades'), unidades = getSeleccionados('unidades');
            if (!tecnicos.length || !actividades.length || !unidades.length) return alert('Selecciona al menos uno de cada tipo');
            if (!confirm(`¿Crear ${tecnicos.length * actividades.length * unidades.length} asignaciones?`)) return;
            const btn = document.getElementById('btnAsignar'); btn.textContent = 'Asignando...'; btn.disabled = true;
            const res = await fetchAuth('/api/cluster/asignar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tecnicos, actividades, unidades }) });
            const data = await res.json(); btn.textContent = '⚡ Asignar Cluster'; btn.disabled = false;
            const resumen = document.getElementById('resumenCluster'); resumen.style.display = 'block'; resumen.innerHTML = res.ok ? `<div style="color:green;">✅ ${data.mensaje}</div>` : `<div style="color:red;">❌ Error: ${data.detail}</div>`;
            if (res.ok) alert(`✅ ${data.creadas} asignaciones creadas`);
        }
        cargarDatos();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("⚡ Asignación por Cluster", contenido, "cluster"))


# ------------------------------------------------------------
# ASISTENCIA – ADMIN (v2 — diseño profesional)
# ------------------------------------------------------------
@router.get("/app/asistencia", response_class=HTMLResponse)
async def asistencia_admin():
    contenido = """
    <script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
      .asis-wrap { font-family: 'DM Sans', system-ui, sans-serif; }
      .asis-grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap:14px; margin-bottom:20px; }
      .asis-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:28px; }
      .asis-card { background: white; border: 0.5px solid #e0ddd5; border-radius: 14px; padding: 1.125rem 1.25rem; }
      .asis-card-title { font-size: 10px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #aaa; margin-bottom: 14px; display: flex; align-items: center; gap: 7px; }
      .asis-card-title i { font-size: 14px; color: #004B87; }
      .asis-field label { display: block; font-size: 11px; font-weight: 600; color: #888; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em; }
      .asis-field input[type="number"], .asis-field input[type="date"] {
        width: 100%; padding: 10px 12px; border: 0.5px solid #ddd; border-radius: 9px;
        font-family: 'DM Mono', monospace; font-size: 13px; color: #111;
        background: #fafaf8; transition: border-color 0.15s;
        margin-bottom: 0;
      }
      .asis-field input:focus { outline: none; border-color: #004B87; background: white; }
      .asis-btn { display: inline-flex; align-items: center; gap: 7px; padding: 11px 18px; border-radius: 9px; font-family: 'DM Sans', system-ui, sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s; }
      .asis-btn-primary { background: #004B87; color: white; }
      .asis-btn-primary:hover { background: #003d70; }
      .asis-btn-secondary { background: white; color: #444; border: 0.5px solid #ccc; }
      .asis-btn-secondary:hover { background: #f7f6f2; }
      .asis-btn-warning { background: #FAEEDA; color: #854F0B; border: 0.5px solid #FAC775; }
      .asis-btn-warning:hover { background: #f5e4c0; }
      .asis-btn-success { background: #EAF3DE; color: #3B6D11; border: 0.5px solid #C0DD97; }
      .asis-btn-success:hover { background: #d8eccc; }
      .asis-btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }
      .asis-qr-section { display: none; }
      .asis-qr-canvas-wrap { background: white; border: 0.5px solid #e0ddd5; border-radius: 14px; padding: 1.5rem; text-align: center; }
      .asis-qr-meta { background: #F7F6F2; border-radius: 12px; padding: 1rem 1.25rem; }
      .asis-qr-meta-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 0.5px solid #e8e5dd; font-size: 13px; }
      .asis-qr-meta-row:last-child { border-bottom: none; }
      .asis-qr-meta-label { color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
      .asis-qr-meta-val { font-family: 'DM Mono', monospace; font-weight: 500; color: #111; }
      .asis-table-wrap { overflow-x: auto; border-radius: 12px; border: 0.5px solid #e0ddd5; }
      .asis-table { width: 100%; border-collapse: collapse; font-size: 13px; }
      .asis-table thead th { background: #004B87; color: white; padding: 11px 14px; text-align: left; font-weight: 600; font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; }
      .asis-table thead th:first-child { border-radius: 12px 0 0 0; }
      .asis-table thead th:last-child  { border-radius: 0 12px 0 0; }
      .asis-table tbody td { padding: 11px 14px; border-bottom: 0.5px solid #f0ede5; color: #333; }
      .asis-table tbody tr:last-child td { border-bottom: none; }
      .asis-table tbody tr:hover td { background: #fafaf7; }
      .asis-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; border: 0.5px solid; }
      .asis-badge-ok  { background: #EAF3DE; color: #3B6D11; border-color: #C0DD97; }
      .asis-badge-err { background: #FCEBEB; color: #A32D2D; border-color: #F09595; }
      .asis-empty { text-align: center; padding: 2.5rem; color: #aaa; font-size: 13px; }
      .asis-filter-row { display: flex; gap: 10px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
      .asis-filter-row input { margin-bottom: 0; }
      .asis-toast { position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); padding: 13px 24px; border-radius: 50px; font-size: 13px; font-weight: 600; z-index: 9999; display: none; }
      @media (max-width: 640px) { .asis-grid-3 { grid-template-columns: 1fr; } .asis-grid-2 { grid-template-columns: 1fr; } }
    </style>

    <div class="asis-wrap">

      <!-- KPIs de hoy -->
      <div id="asisKpis" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;"></div>

      <!-- Configuración de geocerca -->
      <div class="asis-card" style="margin-bottom:20px;">
        <div class="asis-card-title"><i class="ti ti-map-pin"></i> Configuración de geocerca</div>
        <div class="asis-grid-3">
          <div class="asis-field"><label>Latitud fija</label><input type="number" id="latFija" step="0.000001" value="32.5027"></div>
          <div class="asis-field"><label>Longitud fija</label><input type="number" id="lonFija" step="0.000001" value="-117.0037"></div>
          <div class="asis-field"><label>Radio permitido (m)</label><input type="number" id="radioMetros" value="200" min="10" max="5000"></div>
        </div>
        <div class="asis-btn-row" style="margin-bottom:0;">
          <button class="asis-btn asis-btn-primary" onclick="guardarConfiguracion()"><i class="ti ti-device-floppy"></i> Guardar</button>
          <button class="asis-btn asis-btn-primary" onclick="generarQR()"><i class="ti ti-qrcode"></i> Generar QR</button>
          <button class="asis-btn asis-btn-warning" onclick="usarUbicacionActual()"><i class="ti ti-current-location"></i> Usar mi ubicación</button>
        </div>
      </div>

      <!-- QR section -->
      <div id="qrSection" class="asis-qr-section" style="margin-bottom:24px;">
        <div class="asis-grid-2">
          <div class="asis-qr-canvas-wrap">
            <div id="qrCanvas" style="display:inline-block;margin-bottom:12px;"></div>
            <p style="font-size:12px;color:#3B6D11;font-weight:600;margin-bottom:4px;"><i class="ti ti-circle-check" style="font-size:14px;vertical-align:-2px;"></i> QR permanente — sin expiración</p>
            <p style="font-size:11px;color:#aaa;">Se regenera solo al cambiar configuración</p>
            <button class="asis-btn asis-btn-secondary" onclick="generarQR()" style="margin-top:12px;"><i class="ti ti-refresh"></i> Regenerar</button>
          </div>
          <div>
            <div class="asis-qr-meta" style="margin-bottom:12px;">
              <div class="asis-qr-meta-row"><span class="asis-qr-meta-label">Latitud</span><span class="asis-qr-meta-val" id="qrLatLabel">—</span></div>
              <div class="asis-qr-meta-row"><span class="asis-qr-meta-label">Longitud</span><span class="asis-qr-meta-val" id="qrLonLabel">—</span></div>
              <div class="asis-qr-meta-row"><span class="asis-qr-meta-label">Radio</span><span class="asis-qr-meta-val"><span id="qrRadioLabel">—</span> m</span></div>
            </div>
            <div id="mapaLink"></div>
          </div>
        </div>
      </div>

      <!-- Tabla de registros -->
      <div class="asis-card">
        <div class="asis-card-title"><i class="ti ti-table"></i> Registros de asistencia</div>
        <div class="asis-filter-row">
          <div class="asis-field" style="flex:0 0 auto;"><label>Fecha</label><input type="date" id="fechaFiltro" onchange="cargarRegistros()"></div>
          <button class="asis-btn asis-btn-secondary" onclick="cargarRegistros()" style="margin-top:16px;"><i class="ti ti-refresh"></i> Actualizar</button>
          <button class="asis-btn asis-btn-success" onclick="exportarCSV()" style="margin-top:16px;"><i class="ti ti-download"></i> Exportar CSV</button>
        </div>
        <div class="asis-table-wrap">
          <div id="tablaAsistencia"></div>
        </div>
      </div>

    </div>

    <div class="asis-toast" id="asisToast"></div>

    <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
    <script>
      const fetchAuth = window.fetchAuth;

      function toast(msg, tipo) {
        const el = document.getElementById('asisToast');
        el.textContent = msg;
        el.style.background = tipo === 'ok' ? '#004B87' : tipo === 'err' ? '#A32D2D' : '#854F0B';
        el.style.color = 'white';
        el.style.display = 'block';
        setTimeout(() => { el.style.display = 'none'; }, 3000);
      }

      document.getElementById('fechaFiltro').value = new Date().toLocaleDateString('sv-SE', {timeZone:'America/Tijuana'});

      async function cargarKpis() {
        try {
          const fecha = document.getElementById('fechaFiltro').value;
          const res = await fetchAuth('/api/asistencia/registros' + (fecha ? '?fecha=' + fecha : ''));
          if (!res.ok) return;
          const data = await res.json();
          const total = data.length;
          const aprobados = data.filter(r => r.aprobado).length;
          const rechazados = total - aprobados;
          const tecnicos = new Set(data.map(r => r.username)).size;
          const kpis = [
            { val: total,      lbl: 'Registros',  color: '#004B87' },
            { val: aprobados,  lbl: 'Aprobados',  color: '#3B6D11' },
            { val: rechazados, lbl: 'Rechazados', color: '#A32D2D' },
            { val: tecnicos,   lbl: 'Técnicos',   color: '#854F0B' },
          ];
          document.getElementById('asisKpis').innerHTML = kpis.map(k =>
            '<div style="background:white;border:0.5px solid #e0ddd5;border-radius:12px;padding:14px 16px;border-top:3px solid ' + k.color + ';">' +
            '<div style="font-size:26px;font-weight:600;color:' + k.color + ';font-family:DM Mono,monospace;">' + k.val + '</div>' +
            '<div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#aaa;margin-top:3px;">' + k.lbl + '</div>' +
            '</div>'
          ).join('');
        } catch(e) {}
      }

      async function cargarConfiguracion() {
        try {
          const res = await fetchAuth('/api/asistencia/configuracion');
          if (!res.ok) return;
          const data = await res.json();
          const cfg = data && data.config ? data.config : data;
          if (cfg) {
            if (cfg.lat_fija   !== undefined) document.getElementById('latFija').value    = cfg.lat_fija;
            if (cfg.lon_fija   !== undefined) document.getElementById('lonFija').value    = cfg.lon_fija;
            if (cfg.radio_metros !== undefined) document.getElementById('radioMetros').value = cfg.radio_metros;
          }
        } catch(e) {}
      }

      async function guardarConfiguracion() {
        const config = {
          lat_fija:     parseFloat(document.getElementById('latFija').value),
          lon_fija:     parseFloat(document.getElementById('lonFija').value),
          radio_metros: parseInt(document.getElementById('radioMetros').value)
        };
        const res = await fetchAuth('/api/asistencia/configuracion', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config) });
        toast(res.ok ? '✅ Configuración guardada' : '❌ Error al guardar', res.ok ? 'ok' : 'err');
      }

      function usarUbicacionActual() {
        if (!navigator.geolocation) return toast('GPS no soportado en este dispositivo', 'warn');
        navigator.geolocation.getCurrentPosition(pos => {
          document.getElementById('latFija').value = pos.coords.latitude.toFixed(6);
          document.getElementById('lonFija').value = pos.coords.longitude.toFixed(6);
          toast('📍 Coordenadas actualizadas desde tu GPS', 'ok');
        }, () => toast('No se pudo obtener la ubicación', 'err'));
      }

      async function generarQR() {
        const lat   = parseFloat(document.getElementById('latFija').value);
        const lon   = parseFloat(document.getElementById('lonFija').value);
        const radio = parseInt(document.getElementById('radioMetros').value);
        if (isNaN(lat) || isNaN(lon) || isNaN(radio)) { toast('Completa todos los campos de configuración', 'warn'); return; }
        try {
          await guardarConfiguracion();
          const res = await fetchAuth('/api/asistencia/generar-qr');
          const data = await res.json();
          const qrContainer = document.getElementById('qrCanvas');
          qrContainer.innerHTML = '';
          if (typeof QRCode === 'undefined') {
            await new Promise((resolve, reject) => {
              const s = document.createElement('script');
              s.src = 'https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js';
              s.onload = resolve; s.onerror = reject;
              document.head.appendChild(s);
            });
          }
          new QRCode(qrContainer, { text: data.qr_url, width: 200, height: 200, colorDark: '#002B5B', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.L });
          document.getElementById('qrLatLabel').textContent   = data.config.lat_fija;
          document.getElementById('qrLonLabel').textContent   = data.config.lon_fija;
          document.getElementById('qrRadioLabel').textContent = data.config.radio_metros;
          document.getElementById('mapaLink').innerHTML =
            '<a href="https://www.google.com/maps?q=' + data.config.lat_fija + ',' + data.config.lon_fija + '" target="_blank" ' +
            'style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:#004B87;font-weight:600;">' +
            '<i class="ti ti-map-2" style="font-size:15px;"></i> Ver punto en Google Maps</a>';
          document.getElementById('qrSection').style.display = 'block';
        } catch(e) { toast('Error al generar el QR: ' + (e.message || ''), 'err'); }
      }

      async function cargarRegistros() {
        const fecha = document.getElementById('fechaFiltro').value;
        const tabla = document.getElementById('tablaAsistencia');
        tabla.innerHTML = '<div class="asis-empty"><i class="ti ti-loader" style="font-size:22px;"></i><br>Cargando...</div>';
        try {
          const res = await fetchAuth('/api/asistencia/registros' + (fecha ? '?fecha=' + fecha : ''));
          if (!res.ok) { tabla.innerHTML = '<div class="asis-empty">Error al cargar registros.</div>'; return; }
          const data = await res.json();
          if (!data.length) { tabla.innerHTML = '<div class="asis-empty"><i class="ti ti-calendar-off" style="font-size:28px;display:block;margin-bottom:8px;"></i>Sin registros para esta fecha.</div>'; return; }
          let html = '<table class="asis-table"><thead><tr><th>Técnico</th><th>Fecha</th><th>Hora check-in</th><th>Tipo</th><th>Distancia</th><th>Estado</th></tr></thead><tbody>';
          data.forEach(r => {
            const ok     = r.aprobado;
            const badge  = ok
              ? '<span class="asis-badge asis-badge-ok"><i class="ti ti-circle-check"></i> Aprobado</span>'
              : '<span class="asis-badge asis-badge-err"><i class="ti ti-map-pin-off"></i> Rechazado</span>';
            const dist   = r.distancia_metros ? Math.round(r.distancia_metros).toLocaleString('es-MX') + ' m' : '—';
            const tipo   = r.tipo ? (r.tipo === 'salida' ? 'Salida' : 'Entrada') : '—';
            html += '<tr>' +
              '<td><b>' + r.username + '</b></td>' +
              '<td style="font-family:monospace;">' + r.fecha + '</td>' +
              '<td style="font-family:monospace;">' + (r.hora_checkin || r.hora || '—') + '</td>' +
              '<td>' + tipo + '</td>' +
              '<td style="font-family:monospace;">' + dist + '</td>' +
              '<td>' + badge + '</td>' +
              '</tr>';
          });
          html += '</tbody></table>';
          tabla.innerHTML = html;
          cargarKpis();
        } catch(e) { tabla.innerHTML = '<div class="asis-empty">Error de conexión.</div>'; }
      }

      function exportarCSV() {
        const fecha = document.getElementById('fechaFiltro').value;
        fetchAuth('/api/asistencia/registros' + (fecha ? '?fecha=' + fecha : '')).then(r => r.json()).then(data => {
          if (!data.length) return toast('Sin datos para exportar', 'warn');
          const headers = ['Técnico','Fecha','Hora Check-in','Tipo','Distancia (m)','Aprobado'];
          const rows = data.map(r => [r.username, r.fecha, r.hora_checkin || r.hora || '', r.tipo || '', r.distancia_metros ? Math.round(r.distancia_metros) : '', r.aprobado ? 'Sí' : 'No']);
          const csv = [headers, ...rows].map(r => r.join(',')).join('\\n');
          const blob = new Blob([csv], { type: 'text/csv' });
          const url  = URL.createObjectURL(blob);
          const a    = document.createElement('a');
          a.href = url; a.download = 'asistencia_' + (fecha || 'all') + '.csv'; a.click();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
          toast('✅ CSV exportado', 'ok');
        });
      }

      cargarConfiguracion();
      cargarRegistros();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Control de Asistencia", contenido, "asistencia"))


@router.get("/app/checkin", response_class=HTMLResponse)
async def checkin_tecnico():
    html = get_checkin_template()
    init_script = """
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
    <script>
    // window.username ya está seteado por pagina_con_menu <head>
    // El IIFE del template ya definió cargarHorario() y cargarRegistros()
    // setTimeout(50ms) garantiza que el IIFE terminó antes de llamarlos
    window.__ct_username = window.username || localStorage.getItem('username') || '';

    if (typeof window.fetchAuth === 'function') {
        window.fetchAuth('/api/asistencia/configuracion').then(r => r.json()).then(data => {
            const cfg = data && data.config ? data.config : data;
            window.__ct_radio = cfg && cfg.radio_metros ? cfg.radio_metros : 200;
        }).catch(() => { window.__ct_radio = 200; });
    }

    setTimeout(function() {
        if (typeof cargarHorario  === 'function') cargarHorario();
        if (typeof cargarRegistros === 'function') cargarRegistros();
    }, 50);

    // ── Variables de estado del modal ─────────────────────────────────────────
    var _qrTipo      = 'entrada';
    var _qrFotoB64   = null;
    var _gpsCoords   = null;
    var _gpsWatcher  = null;

    // ── GPS silencioso en segundo plano ───────────────────────────────────────
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                _gpsCoords = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy };
                var tag = document.getElementById('ct-gps-tag');
                var el  = document.getElementById('ct-gps-precision');
                if (el) el.textContent = '±' + Math.round(pos.coords.accuracy) + 'm';
                if (tag) tag.className = 'ct-tag ' + (pos.coords.accuracy <= 50 ? 'gps-ok' : pos.coords.accuracy <= 100 ? 'gps-warn' : 'gps-bad');
            },
            function() {},
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    // ── Abrir modal (paso 1: tomar foto del QR) ───────────────────────────────
    // ── Escáner QR en tiempo real ──────────────────────────────────────────────
    var _qrStream    = null;
    var _qrScanLoop  = null;

    window.abrirModalQR = function(tipo) {
        _qrTipo    = tipo || 'entrada';
        _qrFotoB64 = null;
        document.getElementById('ct-modal-overlay').classList.add('open');
        _mostrarPaso('paso1');
        _iniciarEscanerQR();
    };

    window.cerrarModalQR = function() {
        _detenerEscanerQR();
        document.getElementById('ct-modal-overlay').classList.remove('open');
        _qrFotoB64 = null;
    };

    function _mostrarPaso(paso) {
        ['paso1','paso2','paso3'].forEach(function(p) {
            var el = document.getElementById('ct-' + p);
            if (el) el.style.display = (p === paso) ? 'block' : 'none';
        });
    }

    function _iniciarEscanerQR() {
        var video = document.getElementById('ct-qr-video');
        var status = document.getElementById('ct-qr-status');
        if (!video) return;
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            if (status) status.textContent = '❌ Tu navegador no soporta cámara en tiempo real';
            return;
        }
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
        .then(function(stream) {
            _qrStream = stream;
            video.srcObject = stream;
            video.play();
            video.addEventListener('loadedmetadata', function() {
                _qrScanLoop = setInterval(_escanearFrame, 350);
            }, { once: true });
        })
        .catch(function(err) {
            if (status) status.textContent = '❌ No se pudo acceder a la cámara: ' + err.message;
        });
    }

    function _detenerEscanerQR() {
        if (_qrScanLoop) { clearInterval(_qrScanLoop); _qrScanLoop = null; }
        if (_qrStream)   { _qrStream.getTracks().forEach(function(t){ t.stop(); }); _qrStream = null; }
        var video = document.getElementById('ct-qr-video');
        if (video) { video.srcObject = null; }
    }

    function _escanearFrame() {
        var video  = document.getElementById('ct-qr-video');
        var canvas = document.getElementById('ct-qr-canvas');
        if (!video || !canvas || video.readyState < 2) return;
        canvas.width  = video.videoWidth;
        canvas.height = video.videoHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        var imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        var code = null;
        try { code = jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: 'dontInvert' }); } catch(e) {}
        if (code && (code.data.includes('checkin') || code.data.includes('carrier') || code.data.includes('cleverapps'))) {
            _detenerEscanerQR();
            var qrEl = document.getElementById('ct-qr-result');
            if (qrEl) { qrEl.textContent = '✅ QR válido detectado'; qrEl.style.display = 'block'; qrEl.style.background='#EAF3DE'; qrEl.style.color='#3B6D11'; }
            _mostrarPaso('paso2');
        }
    }

    // ── Selfie de confirmación ─────────────────────────────────────────────────
    window.ct_lanzarFotoConfirmacion = function() {
        document.getElementById('ct-input-selfie').click();
    };

    window.ct_onSelfieSeleccionada = function(input) {
        var file = input.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function(e) {
            _qrFotoB64 = e.target.result;
            var preview = document.getElementById('ct-preview-img');
            if (preview) { preview.src = _qrFotoB64; preview.style.display = 'block'; }
            var tipoEl = document.getElementById('ct-paso3-tipo');
            if (tipoEl) tipoEl.textContent = _qrTipo;
            var gpsEl = document.getElementById('ct-paso3-gps');
            if (gpsEl) gpsEl.textContent = _gpsCoords ? ('±' + Math.round(_gpsCoords.accuracy || 0) + 'm') : 'Obteniendo...';
            var btnEl = document.getElementById('ct-btn-confirmar');
            if (btnEl) btnEl.textContent = '✅ Confirmar ' + (_qrTipo === 'salida' ? 'Salida' : 'Entrada');
            _mostrarPaso('paso3');
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(pos) { _gpsCoords = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy }; },
                    function() {},
                    { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
                );
            }
        };
        reader.readAsDataURL(file);
    };

        window.ct_confirmarRegistro = async function() {
        var btn = document.getElementById('ct-btn-confirmar');
        if (btn) { btn.disabled = true; btn.textContent = 'Enviando...'; }

        if (!_gpsCoords) {
            alert('Esperando GPS. Asegúrate de haber dado permiso de ubicación.');
            if (btn) { btn.disabled = false; btn.textContent = '✅ Confirmar ' + _qrTipo; }
            return;
        }

        try {
            var res = await window.fetchAuth('/api/asistencia/registrar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tipo:        _qrTipo,
                    lat:         _gpsCoords.lat,
                    lon:         _gpsCoords.lon,
                    accuracy:    _gpsCoords.accuracy,
                    foto_base64: _qrFotoB64
                })
            });
            var data = await res.json();
            cerrarModalQR();
            if (data.aprobado) {
                alert('✅ ' + (_qrTipo === 'entrada' ? 'Entrada' : 'Salida') + ' registrada a las ' + data.hora);
            } else {
                alert('⚠️ Registrado, pero fuera del perímetro.\\n' + data.mensaje);
            }
            if (typeof cargarRegistros === 'function') cargarRegistros();
        } catch(e) {
            alert('Error al enviar: ' + e.message);
        }
        if (btn) { btn.disabled = false; }
    };
    </script>
    """

    html = html.replace('</body>', init_script + '</body>')
    return HTMLResponse(content=pagina_con_menu("📍 Registrar Asistencia", html, "checkin"))


# ------------------------------------------------------------
# HORARIOS – ADMIN
# ------------------------------------------------------------
@router.get("/app/horarios", response_class=HTMLResponse)
async def horarios_admin():
    contenido = """
    <script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>
    <script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>
    <div style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;">
        <div><label>Semana (Lunes)</label><input type="date" id="semanaInicio" onchange="cargarHorarios()"></div>
        <button class="btn-primary" onclick="guardarHorarios()">💾 Guardar</button>
        <button class="btn-warning" onclick="exportarExcel()">📥 Exportar Excel</button>
        <label class="btn-primary" style="background:#0057A8; cursor:pointer;">📤 Importar Excel <input type="file" accept=".xlsx,.csv" style="display:none;" onchange="importarExcel(this)"></label>
        <button class="btn-success" onclick="abrirModalNombres()">✏️ Editar Nombres</button>
    </div>
    <div class="evidencia-info" style="margin-bottom:16px;">📋 Configura ENTRADA y SALIDA por día. Exporta plantilla, llénala en Excel e importa.</div>
    <div style="overflow-x:auto;" id="tablaHorarios"></div>
    <div class="section-title">📊 Resumen de Asistencia de la Semana</div>
    <div id="resumenAsistencia"></div>
    <div id="modalNombres" class="modal"><div class="modal-content"><h3>✏️ Editar Nombres</h3><div id="listaNombres"></div><div style="display:flex; gap:10px; margin-top:16px;"><button class="btn-primary" onclick="guardarNombres()">💾 Guardar</button><button class="btn-danger" onclick="document.getElementById('modalNombres').style.display='none'">Cancelar</button></div></div></div>
    <script>
        const fetchAuth = window.fetchAuth;
        const DIAS = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
        let tecnicosData = [], nombresMap = {};
        const ahoraTJ = new Date(new Date().toLocaleString('en-US', {timeZone:'America/Tijuana'}));
        const diffLunes = ahoraTJ.getDay() === 0 ? -6 : 1 - ahoraTJ.getDay();
        const lunes = new Date(ahoraTJ); lunes.setDate(ahoraTJ.getDate() + diffLunes);
        document.getElementById('semanaInicio').value = lunes.toLocaleDateString('sv-SE', {timeZone:'America/Tijuana'});
        function getNombre(u) { return nombresMap[u] || u; }
        function fechasDeSemana(l) { const f = []; const b = new Date(l+'T12:00:00'); for(let i=0;i<6;i++){ const d=new Date(b); d.setDate(b.getDate()+i); f.push(d.toISOString().slice(0,10)); } return f; }
        async function cargarHorarios() {
            const semana = document.getElementById('semanaInicio').value; if(!semana) return;
            const fechas = fechasDeSemana(semana);
            let horariosGuardados = {};
            try { const res = await fetchAuth('/api/horarios/?semana='+semana); if(res.ok){ const data=await res.json(); data.forEach(h=>{ horariosGuardados[h.username+'_'+h.fecha]=h; }); } } catch(e){}
            let html = '<table class="data-table"><thead><tr><th rowspan="2">Técnico</th>';
            fechas.forEach((f,i)=>{ const [,mes,dia]=f.split('-'); html+=`<th colspan="2">${DIAS[i]}<br><span style="font-size:0.75rem;">${dia}/${mes}</span></th>`; });
            html+='</thead><tbody>';
            const usuariosRes = await fetchAuth('/api/usuarios/'); const usuarios = await usuariosRes.json();
            tecnicosData = usuarios.filter(u=>u.role==='tecnico');
            // nombresMap se mantiene en memoria de la sesión
            tecnicosData.forEach(t=>{ if(!nombresMap[t.username]) nombresMap[t.username]=t.username; });
            tecnicosData.forEach(tec=>{
                html+=`<tr><td style="background:#f8fafc;"><b>${getNombre(tec.username)}</b><br><span style="font-size:0.72rem;">${tec.username}</span></td>`;
                fechas.forEach(fecha=>{
                    const key=tec.username+'_'+fecha; const h=horariosGuardados[key]||{};
                    html+=`<td><input type="time" id="e_${tec.username}_${fecha}" value="${h.hora_entrada||''}" style="width:100px;"></td><td><input type="time" id="s_${tec.username}_${fecha}" value="${h.hora_salida||''}" style="width:100px;"></td>`;
                });
                html+='</tr>';
            });
            html+='</tbody></table>';
            document.getElementById('tablaHorarios').innerHTML = html;
            cargarResumenAsistencia(semana, fechas);
        }
        async function guardarHorarios() {
            const semana = document.getElementById('semanaInicio').value; const fechas = fechasDeSemana(semana);
            const registros = [];
            tecnicosData.forEach(tec=>{ fechas.forEach(fecha=>{ registros.push({ username: tec.username, fecha, semana, hora_entrada: document.getElementById('e_'+tec.username+'_'+fecha)?.value||'', hora_salida: document.getElementById('s_'+tec.username+'_'+fecha)?.value||'' }); }); });
            const res = await fetchAuth('/api/horarios/', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ registros }) });
            if(res.ok){ const t=document.createElement('div'); t.style.cssText='position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;'; t.textContent='✅ Horarios guardados'; document.body.appendChild(t); setTimeout(()=>t.remove(),3000); }
            else alert('Error al guardar');
        }
        function exportarExcel() {
            const semana = document.getElementById('semanaInicio').value; const fechas = fechasDeSemana(semana);
            const encabezado = ['Técnico (username)', 'Nombre Completo']; fechas.forEach((f,i)=>{ encabezado.push(DIAS[i]+' Entrada', DIAS[i]+' Salida'); });
            const filas = [encabezado];
            tecnicosData.forEach(tec=>{
                const fila = [tec.username, getNombre(tec.username)];
                fechas.forEach(fecha=>{ fila.push(document.getElementById('e_'+tec.username+'_'+fecha)?.value||'', document.getElementById('s_'+tec.username+'_'+fecha)?.value||''); });
                filas.push(fila);
            });
            const ws = XLSX.utils.aoa_to_sheet(filas); ws['!cols']=encabezado.map((h,i)=>({ wch: i<2?22:14 }));
            const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, 'Horarios');
            XLSX.writeFile(wb, 'horarios_semana_'+semana+'.xlsx');
        }
        function importarExcel(input) {
            const file = input.files[0]; if(!file) return;
            const semana = document.getElementById('semanaInicio').value; const fechas = fechasDeSemana(semana);
            const reader = new FileReader();
            reader.onload = e => {
                try {
                    const wb = XLSX.read(e.target.result, { type:'array' });
                    const ws = wb.Sheets[wb.SheetNames[0]];
                    const filas = XLSX.utils.sheet_to_json(ws, { header:1, defval:'' });
                    if(filas.length<2) return alert('Archivo vacío');
                    const headers = filas[0].map(h=>String(h).trim());
                    const idxUser = headers.findIndex(h=>h.toLowerCase().includes('username'));
                    if(idxUser===-1) return alert('No se encontró columna "Técnico (username)"');
                    let importados=0;
                    function limpiarHora(v) {
                        const s = String(v||'').trim();
                        if(!s || s.toLowerCase()==='descansa') return '';
                        if(!isNaN(s) && s.indexOf(':')===-1) {
                            const totalMin = Math.round(parseFloat(s) * 1440);
                            const hh = String(Math.floor(totalMin/60)).padStart(2,'0');
                            const mm = String(totalMin%60).padStart(2,'0');
                            return hh+':'+mm;
                        }
                        return s.length >= 5 ? s.slice(0,5) : s;
                    }
                    filas.slice(1).forEach(fila=>{
                        const username = String(fila[idxUser]||'').trim();
                        if(!username) return;
                        fechas.forEach((fecha,i)=>{
                            const idxE = headers.findIndex(h=>h.includes(DIAS[i]) && h.toLowerCase().includes('entrada'));
                            const idxS = headers.findIndex(h=>h.includes(DIAS[i]) && h.toLowerCase().includes('salida'));
                            const eEl = document.getElementById('e_'+username+'_'+fecha);
                            const sEl = document.getElementById('s_'+username+'_'+fecha);
                            if(eEl && idxE!==-1) eEl.value = limpiarHora(fila[idxE]);
                            if(sEl && idxS!==-1) sEl.value = limpiarHora(fila[idxS]);
                        });
                        importados++;
                    });
                    input.value='';
                    const t=document.createElement('div'); t.style.cssText='position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#0057A8;color:white;padding:14px 28px;border-radius:50px;'; t.textContent=`📤 ${importados} técnicos importados`; document.body.appendChild(t); setTimeout(()=>t.remove(),4000);
                } catch(err){ alert('Error: '+err.message); }
            };
            reader.readAsArrayBuffer(file);
        }
        function abrirModalNombres() {
            let html=''; tecnicosData.forEach(tec=>{ html+=`<div><span>${tec.username}</span><input type="text" id="nombre_${tec.username}" value="${getNombre(tec.username)}"></div>`; });
            document.getElementById('listaNombres').innerHTML = html;
            document.getElementById('modalNombres').style.display = 'flex';
        }
        function guardarNombres() {
            tecnicosData.forEach(tec=>{ const val = document.getElementById('nombre_'+tec.username)?.value.trim(); if(val) nombresMap[tec.username]=val; });
            cargarHorarios();
            document.getElementById('modalNombres').style.display='none';
            cargarHorarios();
        }
        async function cargarResumenAsistencia(semana, fechas) {
            try {
                const res = await fetchAuth('/api/horarios/resumen?semana='+semana);
                if(!res.ok){ document.getElementById('resumenAsistencia').innerHTML='<p>Sin datos</p>'; return; }
                const data = await res.json();
                if(!data.length){ document.getElementById('resumenAsistencia').innerHTML='<p>Sin check-ins</p>'; return; }
                let html='<table class="data-table"><thead><tr><th>Técnico</th>';
                fechas.forEach((f,i)=>{ const [,mes,dia]=f.split('-'); html+=`<th>${DIAS[i]}<br><span style="font-size:0.75rem;">${dia}/${mes}</span></th>`; });
                html+='</thead><tbody>';
                const porTecnico={}; data.forEach(r=>{ if(!porTecnico[r.username]) porTecnico[r.username]={}; porTecnico[r.username][r.fecha]=r; });
                Object.entries(porTecnico).forEach(([username, dias])=>{
                    html+=`<tr><td style="background:#f8fafc;"><b>${getNombre(username)}</b><br><span style="font-size:0.72rem;">${username}</span></td>`;
                    fechas.forEach(fecha=>{ const r=dias[fecha]; html+=`<td>${r ? (r.retardo_min>0 ? `<span class="badge" style="background:#fef3c7;">⏱ +${r.retardo_min} min</span>` : `<span class="badge" style="background:#dcfce7;">✅ ${r.hora_checkin}</span>`) : '—'}</td>`; });
                    html+='</tr>';
                });
                html+='</tbody></table>';
                document.getElementById('resumenAsistencia').innerHTML = html;
            } catch(e){ document.getElementById('resumenAsistencia').innerHTML='<p>Error</p>'; }
        }
        cargarHorarios();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🗓 Horarios Semanales", contenido, "horarios"))
