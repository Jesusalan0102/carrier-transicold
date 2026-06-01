"""
backend/asistencia/templates.py
Plantilla moderna y profesional para Registro de Asistencia
Adaptada a las imágenes que me compartiste
"""

ASISTENCIA_STYLES = """
<style>
    .card { border-radius: 20px; box-shadow: 0 10px 30px rgba(0,43,91,0.1); }
    .tab { background: white; color: black; padding: 10px 16px; border-radius: 9999px; font-size: 13px; font-weight: 600; }
</style>
"""

ASISTENCIA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registrar Asistencia</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body class="bg-zinc-950 text-white min-h-screen">

<div class="max-w-md mx-auto p-4">

  <!-- Tabs (como en tu imagen) -->
  <div class="flex gap-2 mb-6">
    <div class="tab">Vista: Pendiente entrada</div>
    <div class="tab">Vista: Rechazado</div>
    <div class="tab">Vista: Modal QR</div>
  </div>

  <!-- Header -->
  <div class="flex items-center gap-3 mb-6">
    <div class="w-11 h-11 bg-blue-600 rounded-full flex items-center justify-center text-3xl">📍</div>
    <div>
      <h1 class="text-2xl font-bold">Registrar asistencia</h1>
      <p class="text-zinc-400">Carrier Transicold • {{ fecha_hoy }}</p>
    </div>
  </div>

  <!-- GPS Status -->
  <div class="flex gap-3 mb-6">
    <div class="flex-1 bg-zinc-900 border border-zinc-700 rounded-3xl p-4 flex items-center gap-3">
      <input type="checkbox" checked class="w-5 h-5 accent-emerald-500">
      <div>Tijuana <span id="hora-gps" class="font-mono text-emerald-400"></span></div>
    </div>
    <div class="bg-emerald-900/30 border border-emerald-500 text-emerald-400 rounded-3xl px-5 py-4 flex items-center text-sm font-medium">
      GPS ±90m
    </div>
  </div>

  <!-- Horario Card -->
  <div class="card bg-white text-black p-6 mb-6">
    <h3 class="uppercase text-xs tracking-widest text-zinc-500 font-semibold mb-4">TU HORARIO DE HOY</h3>
    <div class="grid grid-cols-2 gap-6 text-center">
      <div>
        <div class="text-xs text-zinc-500">ENTRADA</div>
        <div class="text-5xl font-bold text-blue-900">07:00</div>
      </div>
      <div>
        <div class="text-xs text-zinc-500">SALIDA</div>
        <div class="text-5xl font-bold text-blue-900">09:00</div>
      </div>
    </div>

    <div class="mt-6 bg-amber-100 border border-amber-300 text-amber-700 rounded-3xl p-4 text-center font-medium">
      Llegas con <span id="retardo">107</span> min de retardo
    </div>

    <div class="mt-4 bg-emerald-50 border border-emerald-200 rounded-3xl p-4 flex items-center gap-3">
      <div class="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
      <div>
        <p class="font-semibold">Entrada pendiente</p>
        <p class="text-sm text-zinc-600">Hora actual: <span id="hora-actual">08:48</span></p>
      </div>
    </div>

    <button onclick="registrarAsistencia()" 
            id="btn-registrar"
            class="mt-8 w-full py-6 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold text-lg rounded-3xl flex items-center justify-center gap-3 active:scale-95">
      <i class="fas fa-qrcode"></i>
      Escanear QR y registrar entrada
    </button>
  </div>

  <!-- Registros de Hoy -->
  <div class="card bg-white text-black p-6">
    <h3 class="uppercase text-xs tracking-widest text-zinc-500 font-semibold mb-4">REGISTROS DE HOY</h3>
    <div id="registros" class="space-y-4 text-sm"></div>
  </div>

</div>

<script>
async function registrarAsistencia() {
  const btn = document.getElementById('btn-registrar');
  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Procesando...`;

  try {
    const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, {enableHighAccuracy: true}));

    const payload = {
      username: "{{ username }}",
      tipo: "entrada",
      fecha: new Date().toISOString().split('T')[0],
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
      alert(`❌ Rechazado: ${data.motivo_rechazo || 'Error desconocido'}`);
    }
    location.reload();
  } catch (e) {
    alert("Error de GPS o conexión. Inténtalo nuevamente.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fas fa-qrcode"></i> Escanear QR y registrar entrada`;
  }
}

// Inicializar horas
document.getElementById('hora-actual').textContent = new Date().toLocaleTimeString('es-MX', {hour:'2-digit', minute:'2-digit'});
document.getElementById('hora-gps').textContent = new Date().toLocaleTimeString('es-MX', {hour:'2-digit', minute:'2-digit'});
</script>
</body>
</html>
"""

def get_checkin_template(username="usuario", fecha_hoy="lunes 1 jun 2026"):
    """Esta función es requerida por web_router.py"""
    html = ASISTENCIA_HTML.replace("{{ username }}", username)
    html = html.replace("{{ fecha_hoy }}", fecha_hoy)
    return ASISTENCIA_STYLES + html
