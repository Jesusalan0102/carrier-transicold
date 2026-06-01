"""
templates.py — Diseño profesional adaptado a tu imagen
"""
ASISTENCIA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registrar Asistencia</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    .card { border-radius: 20px; box-shadow: 0 10px 30px rgba(0,43,91,0.1); }
  </style>
</head>
<body class="bg-zinc-950 text-white min-h-screen">

<div class="max-w-md mx-auto p-4">

  <!-- Header como en tu imagen -->
  <div class="flex gap-2 mb-6">
    <div class="bg-white text-black px-4 py-2 rounded-2xl text-sm font-medium">Vista: Pendiente entrada</div>
    <div class="bg-white text-black px-4 py-2 rounded-2xl text-sm font-medium">Vista: Rechazado</div>
    <div class="bg-white text-black px-4 py-2 rounded-2xl text-sm font-medium">Vista: Modal QR</div>
  </div>

  <div class="flex items-center gap-3 mb-6">
    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-xl">📍</div>
    <div>
      <h1 class="text-xl font-bold">Registrar asistencia</h1>
      <p class="text-zinc-400">Carrier Transicold • lunes 1 jun 2026</p>
    </div>
  </div>

  <!-- GPS Bar -->
  <div class="flex gap-3 mb-6">
    <div onclick="getGPS()" class="flex-1 bg-zinc-900 border border-zinc-700 rounded-2xl p-4 flex items-center gap-3 cursor-pointer hover:border-blue-500 transition">
      <input type="checkbox" id="gps-check" class="w-5 h-5 accent-green-500">
      <div>
        <div class="text-sm">Tijuana <span id="hora-gps" class="font-mono"></span></div>
      </div>
    </div>
    <div class="bg-emerald-900/30 border border-emerald-500 text-emerald-400 rounded-2xl px-5 py-4 flex items-center gap-2 text-sm font-medium">
      <span>GPS ±90m</span>
    </div>
  </div>

  <!-- Horario Card -->
  <div class="card bg-white text-black p-6 mb-6">
    <h3 class="uppercase text-xs tracking-widest text-zinc-500 font-semibold mb-4">TU HORARIO DE HOY</h3>
    <div class="grid grid-cols-2 gap-6">
      <div class="text-center">
        <div class="text-xs text-zinc-500">ENTRADA</div>
        <div id="hora-entrada" class="text-5xl font-bold text-blue-900">07:00</div>
      </div>
      <div class="text-center">
        <div class="text-xs text-zinc-500">SALIDA</div>
        <div id="hora-salida" class="text-5xl font-bold text-blue-900">09:00</div>
      </div>
    </div>

    <div id="retardo-alert" class="mt-6 bg-amber-100 border border-amber-300 text-amber-700 rounded-2xl p-4 text-center font-medium">
      Llegas con <span id="min-retardo" class="font-bold">107</span> min de retardo
    </div>

    <div id="status-entrada" class="mt-4 bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center gap-3">
      <div class="w-3 h-3 bg-emerald-500 rounded-full"></div>
      <div class="flex-1">
        <p class="font-semibold">Entrada pendiente</p>
        <p class="text-sm text-zinc-600">Hora actual: <span id="hora-actual">08:48</span></p>
      </div>
    </div>

    <button onclick="registrarAsistencia('entrada')" 
            id="btn-entrada"
            class="mt-6 w-full py-5 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold text-lg rounded-2xl flex items-center justify-center gap-3 active:scale-95 transition">
      <i class="fas fa-qrcode"></i>
      Escanear QR y registrar entrada
    </button>
  </div>

  <!-- Registros de Hoy -->
  <div class="card bg-white text-black p-6">
    <h3 class="uppercase text-xs tracking-widest text-zinc-500 font-semibold mb-4">REGISTROS DE HOY</h3>
    <div id="lista-registros" class="space-y-4"></div>
  </div>

</div>

<script>
// Configuración
const username = "tu_usuario_aqui"; // ← Se reemplaza dinámicamente

async function getGPS() {
  if (!navigator.geolocation) return alert("GPS no soportado");
  navigator.geolocation.getCurrentPosition(pos => {
    document.getElementById('hora-gps').textContent = new Date().toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit'});
  }, () => {}, {enableHighAccuracy: true});
}

async function registrarAsistencia(tipo) {
  const btn = document.getElementById('btn-entrada');
  btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Procesando...`;
  btn.disabled = true;

  try {
    const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, {enableHighAccuracy:true}));
    
    const payload = {
      username: username,
      tipo: tipo,
      fecha: new Date().toISOString().split('T')[0],
      lat: pos.coords.latitude,
      lon: pos.coords.longitude,
      precision_gps: pos.coords.accuracy
    };

    const res = await fetch('/api/asistencia/checkin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.aprobado) {
      alert(`✅ ${tipo.toUpperCase()} registrada correctamente`);
    } else {
      alert(`❌ Rechazado: ${data.motivo_rechazo}`);
    }
    location.reload();
  } catch(e) {
    alert("Error de GPS o conexión");
  } finally {
    btn.innerHTML = `<i class="fas fa-qrcode"></i> Escanear QR y registrar entrada`;
    btn.disabled = false;
  }
}

// Cargar hora actual
document.getElementById('hora-actual').textContent = new Date().toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit'});
</script>
</body>
</html>
"""

# Función para servir
def get_asistencia_html():
    return ASISTENCIA_HTML
