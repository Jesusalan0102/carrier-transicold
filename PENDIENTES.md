# Pendientes — Carrier Transicold / JASS Solutions

Actualizado: 2026-11-12.

## Ya hecho
- Secciones por lote (Reefer/Evaporador/Blower/Tanque) en Inspección y Evidencia, y tarea "Video de liberación" (`cea191f`).
- Firma "DESIGNED BY JASS SOLUTIONS" con el logo en el login (`3ee8209`).
- Licencias por serial key (`cda6d75`).

## Por decidir
- [ ] Nombre de la app (opciones propuestas: JASS Fleet, JASS Cold, JASS Ops, FríoOps, Cadena Fría, Reefer360, Tempra, Núcleo, Órbita). Evitar "Carrier" en el nombre.
- [ ] Aplicar el branding completo con el nombre elegido: títulos, ícono y manifest, pantalla de arranque, página de inicio; acento con el azul del logo (~`#6BA3D0`).

## Por verificar tras el despliegue
- [ ] Lotes: marcar secciones con el botón "Secciones".
- [ ] Celular: chips de sección en la cámara, galería y aviso de secciones sin evidencia al finalizar.
- [ ] Ocultar un lote con respaldo y revisar `Backups_Lotes` (carpetas `Inspección/Reefer`, etc.).
- [ ] Migración en TiDB: columnas `seccion` y `secciones_evidencia` creadas.

## Seguridad y venta
- [ ] Rotar credenciales expuestas: TiDB, `SECRET_KEY` (poner una aleatoria), VAPID, secreto y refresh token de Microsoft, tokens de GitHub.
- [ ] Licencias: definir `LICENSE_REQUIRED` y `LICENSE_PUBLIC_KEY` en cada instalación de cliente.
- [ ] Antes de vender: titularidad del código, licencia de PyMuPDF (AGPL) y uso de la marca Carrier.

## Técnico menor
- [ ] Prueba `test_todos_los_routers_quedaron_registrados` falla por la versión de FastAPI de mi entorno (ya fallaba antes de los cambios).
