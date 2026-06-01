"""
backend/asistencia/templates.py
Plantilla moderna, limpia y profesional para Registro de Asistencia
Adaptada 100% a la paleta de colores corporativa y datos reales de Carrier Transicold
"""

ASISTENCIA_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
    body {
        font-family: 'Inter', sans-serif;
    }
</style>
"""

ASISTENCIA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registrar Asistencia - Carrier Transicold</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body class="bg-slate-100 text-slate-800 min-h-screen flex flex-col justify-start py-6 px-4">

<div class="w-full max-w-md mx-auto bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">

  <div class="bg-slate-50 p-3 grid grid-cols-3 gap-2 border-b border-slate-200 text-center text-[11px] text-slate-500 font-medium">
    <div class="bg-white px-1 py-2 rounded-lg border border-slate-300 shadow-sm cursor-pointer hover:bg-slate-100 transition-colors">Vista: Pendiente entrada</div>
    <div class="bg-rose-50 px-1 py-2 rounded-lg border border-rose-200 text-rose-700 font-semibold shadow-sm cursor-pointer">Vista: Rechazado</div>
    <div class="bg-white px-1 py-2 rounded-lg border border-slate-300 shadow-sm cursor-pointer hover:bg-slate-100 transition-colors">Vista: Modal QR</div>
  </div>

  <div class="bg-blue-800 px-6 py-5 text-white flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-11 h-11 bg-blue-700/60 rounded-full flex items-center justify-center text-xl border border-blue-600 shadow-inner">
        <i class="fa-solid fa-clock-rotate-left"></i>
      </div>
      <div>
        <h1 class="text-lg font-bold tracking-wide">Registrar asistencia</h1>
        <p class="text-xs text-blue-200 font-medium">Carrier Transicold • {{ fecha_hoy }}</p>
      </div>
    </div>
    <span class="relative flex h-2.5 w-2.5">
      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
      <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
    </span>
  </div>

  <div class="grid grid-cols-2 gap-3 px-6 py-4 bg-slate-50 border-b border-slate-200 text-xs font-semibold">
    <div class="flex items-center gap-2 bg-white px-3 py-2.5 rounded-xl border border-slate-200 text-slate-700 shadow-sm">
      <span class="text-slate-400"><i class="fa-solid fa-location-dot"></i></span>
      <span>Tijuana <span id="hora-gps" class="text-slate-500 font-normal">08:48</span></span>
    </div>
    <div class="flex items-center justify-center gap-1.5 bg-emerald-50 px-3 py-2.5 rounded-xl border border-emerald-200 text-emerald-700 shadow-sm">
      <span class="text-[10px] animate-pulse">🟢</span>
      <span>GPS &plusmn;90m</span>
    </div>
  </div>

  <div class="p-6 space-y-5">
    <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-sm space-y-4">
      <h3 class="uppercase text-[11px] tracking-widest text-slate-400 font-bold">TU HORARIO DE HOY</h3>
      
      <div class="grid grid-cols-2 gap-4 text-center">
        <div class="bg-slate-50/80 py-3 rounded-xl border border-slate-100">
          <div class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">ENTRADA</div>
          <div class="text-2xl font-black text-slate-800 mt-0.5">07:00</div>
        </div>
        <div class="bg-slate-50/80 py-3 rounded-xl border border-slate-100">
          <div class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">SALIDA</div>
          <div class="text-2xl font-black text-slate-800 mt-0.5">09:00</div>
        </div>
      </div>

      <div class="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl px-4 py-3 text-xs font-medium flex items-center gap-2">
        <span>⚠️</span>
        <span>Llegas con <span id="retardo" class="font-bold">107 min</span> de retardo</span>
      </div>

      <div class="bg-slate-50/80 border border-dashed border-slate-300 rounded-xl p-3.5 flex items-center gap-3">
        <div class="w-2.5 h-2.5 bg-amber-500 rounded-full animate-pulse"></div>
        <div class="text-xs">
          <p class="font-bold text-slate-700">Entrada pendiente</p>
          <p class="text-slate-500 mt-0.5">Hora actual: <span id="hora-actual" class="font-semibold text-slate-600">08:48</span></p>
        </div>
      </div>
    </div>

    <button onclick="registrarAsistencia()" 
            id="btn-registrar"
            class="w-full py-4 bg-blue-700 hover:bg-blue-800 active:scale-[0.98] transition-all text-white font-bold text-sm rounded-xl shadow-lg shadow-blue-700/20 flex items-center justify-center gap-2 tracking-wide">
      <i class="fas fa-qrcode text-base"></i>
      Escanear QR y registrar entrada
    </button>
  </div>

  <div class="bg-slate-50 px-6 pt-3 pb-6 border-t border-slate-200">
    <h3 class="uppercase text-[11px] tracking-widest text-slate-400 font-bold mb-3">REGISTROS DE HOY</h3>
    
    <div id="registros" class="space-y-3">
      </div>
  </div>

</div>

<script>
const CONFIG = {
  username: "{{ username }}",
  fecha: new Date().toISOString().split('T')[0]
};

async function cargarHistorial() {
  const contenedor = document.getElementById('registros');
  try {
    const response = await fetch(`/api/asistencia/registros/${CONFIG.username}/${CONFIG.fecha}`);
    const data = await response.json();
    
    if (!data.registros || data.registros.length === 0) {
      contenedor.innerHTML = `<p class="text-xs text-slate-400 text-center py-4 font-medium">No hay registros guardados el día de hoy.</p>`;
      return;
    }
    
    contenedor.innerHTML = data.registros.map(reg => {
      const esAprobado = reg.aprobado === 1 || reg.aprobado === true;
      return `
        <div class="flex items-center justify-between p-3.5 ${esAprobado ? 'bg-emerald-50/60 border-emerald-200' : 'bg-rose-50 border-rose-200'} rounded-xl border shadow-sm transition-all">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl ${esAprobado ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'} flex items-center justify-center text-xs font-bold">
              <i class="${esAprobado ? 'fa-solid fa-check' : 'fa-solid fa-xmark'} text-sm"></i>
            </div>
            <div>
              <p class="text-xs font-bold text-slate-800 capitalize">${reg.tipo}</p>
              <p class="text-[11px] ${esAprobado ? 'text-emerald-600' : 'text-rose-600'} font-medium mt-0.5 flex items-center gap-1">
                <span>📍</span> ${esAprobado ? 'Dentro de zona de trabajo' : (reg.motivo_rechazo || 'Fuera de rango')}
              </p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-xs font-bold text-slate-700">${reg.hora_checkin}</p>
            <span class="inline-block text-[10px] ${esAprobado ? 'bg-emerald-200 text-emerald-800 border-emerald-300' : 'bg-rose-200 text-rose-800 border-rose-300'} font-bold px-2 py-0.5 rounded-md mt-1 border">
              ${esAprobado ? 'Aprobado' : 'Rechazado'}
            </span>
          </div>
        </div>
      `;
    }).join('');
  } catch (error) {
    contenedor.innerHTML = `<p class="text-xs text-rose-500 text-center py-2">Error al sincronizar el historial.</p>`;
  }
}

async function registrarAsistencia() {
  const btn = document.getElementById('btn-registrar');
  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Procesando ubicación...`;

  try {
    const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, {
      enableHighAccuracy: true,
      timeout: 10000
    }));

    const payload = {
      username: CONFIG.username,
      tipo: "entrada",
      fecha: CONFIG.fecha,
      lat: pos.coords.latitude,
      lon: pos.coords.longitude,
      precision_gps: pos.coords.accuracy
    };

    const response = await fetch('/api/asistencia/checkin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (data.aprobado) {
      alert(`✅ Entrada registrada correctamente a las ${data.hora_registro}`);
    } else {
      alert(`❌ Rechazado: ${data.motivo_rechazo || 'Fuera de rango'}`);
    }
    cargarHistorial();
  } catch (e) {
    alert("Error al obtener coordenadas GPS. Verifica los permisos de ubicación en tu dispositivo.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fas fa-qrcode"></i> Escanear QR y registrar entrada`;
  }
}

function inicializarModulo() {
  const opciones = { hour: '2-digit', minute: '2-digit', hour12: false };
  const horaActualStr = new Date().toLocaleTimeString('es-MX', opciones);
  if(document.getElementById('hora-actual')) document.getElementById('hora-actual').textContent = horaActualStr;
  if(document.getElementById('hora-gps')) document.getElementById('hora-gps').textContent = horaActualStr;
  cargarHistorial();
}

// Llamada corregida sin tildes/acentos extraños
inicializarModulo();
</script>
</body>
</html>
"""

def get_checkin_template(username="usuario", fecha_hoy="lunes 1 jun 2026"):
    """Función exportable requerida explícitamente por web_router.py"""
    html = ASISTENCIA_HTML.replace("{{ username }}", username)
    html = html.replace("{{ fecha_hoy }}", fecha_hoy)
    return ASISTENCIA_STYLES + html
