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
# FUNCIÓN AUXILIAR CON SIDEBAR (CORREGIDA Y BLINDADA)
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
                try {{
                    const res = await fetch(url, {{ ...options, headers }});
                    if (res.status === 401) {{
                        localStorage.clear();
                        window.location.href = '/app';
                    }}
                    return res;
                }} catch (err) {{
                    console.error("Fallo de red en fetchAuth:", err);
                    throw err;
                }}
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
                    {{ href: '/app/admin', label: '🛠 Panel de Administración' }}
                ];
                const visorMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/inventario', label: '📦 Inventarios' }},
                    {{ href: '/app/unidades', label: '📸 Registro de Unidades' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                    {{ href: '/app/horarios', label: '🗓 Horarios Semanales' }},
                    {{ href: '/app/asistencia', label: '📍 Control de Asistencia' }}
                ];
                const techMenu = [
                    {{ href: '/app/mis-tareas', label: '🎯 Mis Tareas' }},
                    {{ href: '/app/solicitud', label: '🔔 Nueva Solicitud' }},
                    {{ href: '/app/mis-tickets', label: '🎫 Mis Tickets' }},
                    {{ href: '/app/checkin', label: '📍 Registrar Asistencia' }}
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
# DASHBOARD (CIERRE CORREGIDO Y SCRIPT COMPLETO)
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
        
        async function descargarReporte() {
            try {
                const res = await fetchAuth('/api/unidades/reporte/excel');
                if(!res.ok) throw new Error("Fallo al generar excel");
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = `Reporte_Maestro_Carrier.xlsx`;
                document.body.appendChild(a); a.click(); a.remove();
            } catch(e) { alert("Error al descargar reporte: " + e.message); }
        }

        async function descargarEvidencias() {
            const unit = document.getElementById('unidadEv').value;
            if(!unit) return alert("Selecciona una unidad");
            try {
                const res = await fetchAuth(`/api/unidades/descargar-evidencias-zip/${unit}`);
                if(!res.ok) throw new Error("No hay evidencias o falló el empaquetado");
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = `Evidencias_${unit}.zip`;
                document.body.appendChild(a); a.click(); a.remove();
            } catch(e) { alert("Error: " + e.message); }
        }

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
                }
                
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
                                        \${actividades.map(a => `<th>\${a}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    unidades.forEach((u, idx) => {
                        const bgColor = idx % 2 === 0 ? 'white' : '#fafafa';
                        tableHtml += `
                            <tr style="background: \${bgColor};">
                                <td class="lote-cell">\${u.id_lote || '—'}</td>
                                <td class="unit-cell">\${u.unit_number}</td>
                        `;
                        actividades.forEach(act => {
                            const completada = completadasSet.has(u.unit_number + '||' + act);
                            tableHtml += `
                                <td>
                                    \${completada ? '<span class="status-badge-complete">✓</span>' : '<span class="status-badge-pending">—</span>'}
                                </td>
                            `;
                        });
                        tableHtml += `</tr>`;
                    });
                    tableHtml += `</tbody></table></div>`;
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
                            <div class="inv-info-bar" style="margin-bottom:0; cursor:pointer;" onclick="var d=this.nextElementSibling;d.style.display=d.style.display==='none'?'block':'none';">📦 Lote: \${lote} (\${units.length} unidades) <span style="margin-left:auto;">▼</span></div>
                            <div style="display:none; padding:16px; background:white; overflow-x:auto;">
                                <table class="status-table" style="width:100%; min-width:800px;">
                                    <thead><tr><th>#Económico</th>\${Object.values(camposSeries).map(s => `<th>\${s}</th>`).join('')}</tr></thead>
                                    <tbody>\${units.map(u => `<tr><td>\${u.unit_number}</td>\${Object.keys(camposSeries).map(k => `<td>\${u[k] || '—'}</td>`).join('')}</tr>`).join('')}</tbody>
                                </table>
                            </div>
                        </div>`;
                    }
                    document.getElementById('lotesContainer').innerHTML = lotesHtml;
                    
                    const unidadEvEl = document.getElementById('unidadEv');
                    if (unidadEvEl) {
                        unidadEvEl.innerHTML = '<option value="">Selecciona unidad</option>' + unidades.map(u => `<option value="\${u.unit_number}">\${u.unit_number} – \${u.id_lote || ''}</option>`).join('');
                    }
                }
            } catch(e) { console.error(e); }
        }
        document.addEventListener('DOMContentLoaded', cargarDashboard);
    </script>
    """
    return pagina_con_menu("Dashboard Ejecutivo", contenido, "dashboard")
