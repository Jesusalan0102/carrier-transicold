# -*- coding: utf-8 -*-

# Estilos CSS de respaldo reutilizables en tu aplicación
ASISTENCIA_STYLES = """
<style>
    .brand-blue { background-color: #004B87; }
    .brand-dark { background-color: #0A2540; }
    .text-brand { color: #004B87; }
    .bg-gray-custom { background-color: #F4F4F2; }
</style>
"""

def get_checkin_template() -> str:
    """
    Retorna el diseño HTML adaptado para la interfaz profesional e 
    institucional de Carrier Transicold.
    """
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carrier Transicold - Registro de Asistencia</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .brand-blue { background-color: #004B87; }
        .brand-dark { background-color: #0A2540; }
        .text-brand { color: #004B87; }
        .bg-gray-custom { background-color: #F4F4F2; }
    </style>
</head>
<body class="bg-gray-100 font-sans antialiased text-gray-800 min-h-screen flex flex-col items-center py-6 px-4">

    <div class="w-full max-w-md bg-stone-100 border border-stone-200 rounded-xl p-2 mb-6 flex justify-between space-x-2 text-xs font-medium shadow-sm">
        <button onclick="cambiarVista('pendiente')" id="btn-v-pendiente" class="flex-1 py-2.5 px-2 text-center rounded-lg border border-stone-300 bg-white shadow-sm transition">
            Vista:<br>Pendiente entrada
        </button>
        <button onclick="cambiarVista('rechazado')" id="btn-v-rechazado" class="flex-1 py-2.5 px-2 text-center rounded-lg border border-stone-200 text-stone-600 hover:bg-white transition">
            Vista:<br>Rechazado
        </button>
        <button onclick="cambiarVista('modal')" id="btn-v-modal" class="flex-1 py-2.5 px-2 text-center rounded-lg border border-stone-200 text-stone-600 hover:bg-white transition">
            Vista:<br>Modal QR
        </button>
    </div>

    <div class="w-full max-w-md space-y-4">
        
        <div class="flex items-center justify-between border-b border-gray-200 pb-4">
            <div class="flex items-center space-x-3">
                <div class="brand-blue text-white w-12 h-12 rounded-full flex items-center justify-center shadow-sm">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <div>
                    <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Registrar asistencia</h1>
                    <p class="text-xs text-gray-500">Carrier Transicold • <span id="fecha-actual">lunes 1 jun 2026</span></p>
                </div>
            </div>
            <div class="flex items-center space-x-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
                <span>Online</span>
            </div>
        </div>

        <div class="flex items-center space-x-3 text-xs font-medium">
            <div class="bg-stone-100 border border-stone-200 text-stone-700 px-3 py-1.5 rounded-lg shadow-sm flex items-center space-x-1">
                <span>📍</span>
                <span>Tijuana 08:48</span>
            </div>
            <div class="bg-emerald-50 border border-emerald-200 text-emerald-800 px-3 py-1.5 rounded-lg shadow-sm flex items-center space-x-1">
                <span>🟢</span>
                <span>GPS &plusmn;90m</span>
            </div>
        </div>

        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-200 space-y-4">
            <h2 class="text-xs font-bold text-gray-400 tracking-wider uppercase">Tu horario de hoy</h2>
            
            <div class="grid grid-cols-2 gap-4 bg-stone-50 border border-stone-100 rounded-xl p-4 text-center">
                <div class="border-r border-stone-200">
                    <p class="text-xs font-semibold text-stone-400 uppercase tracking-tight">Entrada</p>
                    <p class="text-2xl font-bold text-stone-800 mt-1">07:00</p>
                </div>
                <div>
                    <p class="text-xs font-semibold text-stone-400 uppercase tracking-tight">Salida</p>
                    <p class="text-2xl font-bold text-stone-800 mt-1">09:00</p>
                </div>
            </div>

            <div class="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-3 text-xs font-medium flex items-center space-x-2 shadow-sm">
                <span>⚠️</span>
                <span>Llegas con <strong class="font-bold">107 min de retardo</strong></span>
            </div>

            <div id="estado-pendiente" class="bg-stone-50 border border-dashed border-stone-300 rounded-xl p-4 flex items-center space-x-3">
                <span class="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
                <div>
                    <p class="text-sm font-semibold text-stone-800">Entrada pendiente</p>
                    <p class="text-xs text-stone-500 mt-0.5">Hora actual: 08:48</p>
                </div>
            </div>

            <button onclick="abrirModalQR()" class="w-full bg-white hover:bg-stone-50 border border-gray-300 hover:border-gray-400 text-gray-800 font-semibold py-3 px-4 rounded-xl text-sm transition flex items-center justify-center space-x-2 shadow-sm">
                <span>📷</span>
                <span>Escanear QR y registrar entrada</span>
            </button>
        </div>

        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-200 space-y-4">
            <h2 class="text-xs font-bold text-gray-400 tracking-wider uppercase">Registros de hoy</h2>
            
            <div id="registro-vacio" class="hidden flex flex-col items-center justify-center py-6 text-center space-y-2">
                <span class="text-2xl text-stone-400">🕒</span>
                <p class="text-xs text-stone-500 font-medium">Sin registros por ahora</p>
            </div>

            <div id="registro-lista" class="block">
                <div class="flex items-center justify-between bg-white border border-gray-100 rounded-xl p-3 shadow-sm">
                    <div class="flex items-center space-x-3">
                        <div class="bg-stone-100 text-stone-500 w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm">
                            🕒
                        </div>
                        <div>
                            <p class="text-sm font-semibold text-gray-900">Entrada</p>
                            <p class="text-xs text-gray-500 flex items-center space-x-1 mt-0.5">
                                <span>📍</span>
                                <span>19,522 m del punto fijo</span>
                            </p>
                        </div>
                    </div>
                    <div class="text-right space-y-1">
                        <p class="text-sm font-bold text-gray-900">08:47</p>
                        <span id="badge-estatus" class="inline-block bg-red-50 text-red-700 border border-red-200 text-[11px] font-bold px-2.5 py-0.5 rounded-md shadow-sm">
                            ⚠️ Rechazado
                        </span>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div id="modal-qr" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white w-full max-w-sm rounded-2xl shadow-xl overflow-hidden transform transition-all border border-gray-200 flex flex-col items-center p-6 space-y-4">
            <div class="w-full flex justify-between items-center border-b border-gray-100 pb-2">
                <h3 class="text-md font-bold text-gray-900 flex items-center space-x-1.5">
                    <span>📷</span>
                    <span>Cámara de Validación</span>
                </h3>
                <button onclick="cerrarModalQR()" class="text-gray-400 hover:text-gray-600 font-bold text-sm bg-gray-100 hover:bg-gray-200 w-7 h-7 rounded-full flex items-center justify-center transition">✕</button>
            </div>
            
            <div class="w-full aspect-square bg-stone-900 rounded-xl relative flex flex-col items-center justify-center overflow-hidden border border-stone-800">
                <div class="absolute inset-x-0 h-0.5 bg-cyan-500 shadow-[0_0_10px_#06b6d4] top-1/2 animate-bounce w-full"></div>
                <span class="text-4xl">🔲</span>
                <p class="text-xs text-stone-400 mt-2 font-medium">Apunta al QR del Administrator</p>
            </div>
            <p class="text-xs text-center text-stone-500">Mantén el dispositivo firme dentro del perímetro establecido de la sucursal.</p>
        </div>
    </div>

    <script>
        function cambiarVista(vista) {
            const estadoPendiente = document.getElementById('estado-pendiente');
            const badgeEstatus = document.getElementById('badge-estatus');
            const registroLista = document.getElementById('registro-lista');
            const registroVacio = document.getElementById('registro-vacio');
            
            const btnPendiente = document.getElementById('btn-v-pendiente');
            const btnRechazado = document.getElementById('btn-v-rechazado');
            const btnModal = document.getElementById('btn-v-modal');

            [btnPendiente, btnRechazado, btnModal].forEach(btn => {
                btn.className = "flex-1 py-2.5 px-2 text-center rounded-lg border border-stone-200 text-stone-600 hover:bg-white transition";
            });

            if (vista === 'pendiente') {
                btnPendiente.className = "flex-1 py-2.5 px-2 text-center rounded-lg border border-stone-300 bg-white shadow-sm font-bold text-stone-900 transition";
                estadoPendiente.className = "bg-stone-50 border border-dashed border-stone-300 rounded-xl p-4 flex items-center space-x-3";
                estadoPendiente.innerHTML = `<span class="w-3 h-3 rounded-full bg-amber-500 inline-block"></span><div><p class="text-sm font-semibold text-stone-800">Entrada pendiente</p><p class="text-xs text-stone-500 mt-0.5">Hora actual: 08:48</p></div>`;
                registroLista.classList.add('hidden');
                registroVacio.classList.remove('hidden');
                cerrarModalQR();
            } 
            else if (vista === 'rechazado') {
                btnRechazado.className = "flex-1 py-2.5 px-2 text-center rounded-lg border-red-300 bg-red-50 text-red-900 shadow-sm font-bold transition";
                estadoPendiente.className = "bg-red-50 border border-dashed border-red-200 rounded-xl p-4 flex items-center space-x-3 text-red-900";
                estadoPendiente.innerHTML = `<span class="w-3 h-3 rounded-full bg-red-500 inline-block"></span><div><p class="text-sm font-bold">Entrada Rechazada por Geofencing</p><p class="text-xs text-red-600 mt-0.5">Fuera de perímetro (19,522 m de desfase)</p></div>`;
                registroLista.classList.remove('hidden');
                registroVacio.classList.add('hidden');
                badgeEstatus.className = "inline-block bg-red-50 text-red-700 border border-red-200 text-[11px] font-bold px-2.5 py-0.5 rounded-md shadow-sm";
                badgeEstatus.innerText = "⚠️ Rechazado";
                cerrarModalQR();
            } 
            else if (vista === 'modal') {
                btnModal.className = "flex-1 py-2.5 px-2 text-center rounded-lg border-stone-300 bg-white shadow-sm font-bold text-stone-900 transition";
                abrirModalQR();
            }
        }

        function abrirModalQR() {
            document.getElementById('modal-qr').classList.remove('hidden');
        }

        function cerrarModalQR() {
            document.getElementById('modal-qr').classList.add('hidden');
        }

        document.addEventListener("DOMContentLoaded", () => {
            const opciones = { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' };
            const fechaHoy = new Date().toLocaleDateString('es-MX', opciones);
            document.getElementById('fecha-actual').innerText = fechaHoy;
        });
    </script>
</body>
</html>"""
    return html_content
