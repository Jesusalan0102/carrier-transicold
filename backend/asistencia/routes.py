// BUSCA LA FUNCIÓN QUE CARGA LA CONFIGURACIÓN Y REEMPLÁZALA POR ESTA VERSIÓN COMPLETA:
async function cargarConfiguracionGeocerca() {
    try {
        const res = await window.fetchAuth('/api/asistencia/configuracion');
        const data = await res.json();
        
        // Saneamiento definitivo: Si data es null, undefined o no trae la propiedad config
        const config = data && data.config ? data.config : { lat_fija: 32.5027, lon_fija: -117.0037, radio_metros: 200 };
        
        // Pintar de forma segura en los inputs del formulario administrativo sin colapsar
        if(document.getElementById('lat_fija')) document.getElementById('lat_fija').value = config.lat_fija ?? 32.5027;
        if(document.getElementById('lon_fija')) document.getElementById('lon_fija').value = config.lon_fija ?? -117.0037;
        if(document.getElementById('radio_metros')) document.getElementById('radio_metros').value = config.radio_metros ?? 200;
        
        // Guardar en scope global por seguridad para el generador del QR
        window.currentGeocercaConfig = config;
        
    } catch (error) {
        console.warn("La tabla de configuración está vacía o el backend no responde. Inicializando valores de Tijuana por defecto:", error);
        
        // Valores de respaldo para que la app siga operativa al 100%
        window.currentGeocercaConfig = { lat_fija: 32.5027, lon_fija: -117.0037, radio_metros: 200 };
        
        if(document.getElementById('lat_fija')) document.getElementById('lat_fija').value = 32.5027;
        if(document.getElementById('lon_fija')) document.getElementById('lon_fija').value = -117.0037;
        if(document.getElementById('radio_metros')) document.getElementById('radio_metros').value = 200;
    }
}

// MODIFICA TU BOTÓN DE GENERAR QR PARA USAR EL VALOR PROTEGIDO:
function generarQRAsistencia() {
    try {
        // En lugar de leer directo de un objeto propenso a ser undefined, usamos la variable blindada
        const lat = window.currentGeocercaConfig?.lat_fija || 32.5027;
        const lon = window.currentGeocercaConfig?.lon_fija || -117.0037;
        const radio = window.currentGeocercaConfig?.radio_metros || 200;
        
        // Tu lógica actual para armar el QR...
        const urlQR = `https://tu-dominio.com/app/checkin?lat=${lat}&lon=${lon}&radius=${radio}`;
        console.log("QR Generado de forma segura:", urlQR);
        
        // Renderizar el QR usando tu librería...
    } catch(err) {
        alert("Error al generar el QR: " + err.message);
    }
}
