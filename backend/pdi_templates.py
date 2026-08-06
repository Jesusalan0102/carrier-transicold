# backend/pdi_templates.py
"""
Definición de las plantillas de PDI (Pre-Delivery Inspection / Inspección
Pre-Entrega) de Carrier Transicold.

Existen dos formatos oficiales que maneja el taller:
  - "x4"     -> Unit Installation & Pre-Delivery Inspection, X4 7300 & 7500
                (Trailer Refrigeration Units) — motor diésel, 1 compresor.
  - "vector" -> Unit Installation & Pre-Delivery Inspection, Vector 8100,
                8500, 8600MT & 8611MT — multi-temperatura, generador propio,
                hasta 3 compartimentos/evaporadores.

Este módulo es la ÚNICA fuente de verdad de los campos: tanto el backend
(pdi_router.py) como el frontend (routers/web_router.py -> /app/pdi) leen
de aquí para armar el checklist, las lecturas y la tabla de configuración.

IMPORTANTE — auto-check:
Todas las secciones marcadas con "es_registro": False se auto-marcan como
completadas (checkbox = 1) al crear o resincronizar un PDI. La única
sección que NO se auto-marca es "Unit Registration" (es_registro=True),
que siempre requiere llenado manual porque implica datos reales de
entrega (fecha de puesta en servicio, horómetros, registro de garantía).
"""

# ──────────────────────────────────────────────────────────────────────────
# CAMPOS DE ENCABEZADO (identificación de cliente / unidad)
# ──────────────────────────────────────────────────────────────────────────
HEADER_FIELDS_COMMON = [
    {"clave": "cliente",            "label": "Cliente / Customer Name",              "auto": None},
    {"clave": "direccion",          "label": "Dirección / Address",                  "auto": None},
    {"clave": "ciudad_estado_cp",   "label": "Ciudad, Estado, C.P.",                 "auto": None},
    {"clave": "fabricante_trailer", "label": "Fabricante Trailer",                   "auto": None},
    {"clave": "modelo_trailer",     "label": "Modelo Trailer",                       "auto": None},
    {"clave": "vin_trailer",        "label": "VIN Trailer",                          "auto": "vin_number"},
    {"clave": "numero_flota",       "label": "Número de Flota",                      "auto": "unit_number"},
    {"clave": "distribuidor",       "label": "Distribuidor / Dealer",                "auto": None},
    {"clave": "modelo_unidad",      "label": "Modelo de Unidad",                     "auto": "reefer_model"},
    {"clave": "numero_serie_unidad","label": "Número de Serie de Unidad",            "auto": "reefer_serial"},
    {"clave": "numero_serie_motor", "label": "Número de Serie de Motor",             "auto": "engine_serial"},
    {"clave": "numero_serie_compresor", "label": "Número de Serie de Compresor",     "auto": "compressor_serial"},
    {"clave": "numero_serie_ees",   "label": "Número de Serie EES",                  "auto": None},
    {"clave": "tecnico_instalo",    "label": "Técnico que Instaló",                  "auto": None},
    {"clave": "fecha_instalacion",  "label": "Fecha de Instalación",                 "auto": None},
]

HEADER_FIELDS_VECTOR_EXTRA = [
    {"clave": "numero_serie_generador", "label": "Número de Serie de Generador",         "auto": "generator_serial"},
    {"clave": "modelo_2do_evap",        "label": "2do Comp. Evap. — Modelo",              "auto": "evaporator_model_1"},
    {"clave": "numero_serie_2do_evap",  "label": "2do Comp. Evap. — Número de Serie",     "auto": "evaporator_serial_mjs11"},
    {"clave": "modelo_3er_evap",        "label": "3er Comp. Evap. — Modelo",              "auto": "evaporator_model_2"},
    {"clave": "numero_serie_3er_evap",  "label": "3er Comp. Evap. — Número de Serie",     "auto": "evaporator_serial_mjd22"},
]

HEADER_FIELDS_FOOTER = [
    {"clave": "dealer_firma",            "label": "Dealer / Distribuidor"},
    {"clave": "tecnico_inspecciono",     "label": "Técnico que Inspeccionó"},
    {"clave": "comentarios",             "label": "Comentarios"},
]

# ──────────────────────────────────────────────────────────────────────────
# CHECKLIST — X4 7300 & 7500
# ──────────────────────────────────────────────────────────────────────────
CHECKLIST_X4 = [
    {
        "clave": "A", "es_registro": False,
        "titulo": "A. Revisión pre-arranque / Instalación",
        "items": [
            "Torquear los tornillos de montaje del huésped (60 ft-lbs).",
            "Revisar instalación de tanque y línea de combustible (líneas de suministro y retorno a 1 pulgada del inferior del tanque).",
            "Revisar las conexiones de combustible y aceite por fugas.",
            "Revisar apriete de conexiones de cable y tierra.",
            "Revisar que todos los arneses, cables, mangueras y líneas de combustible no presenten desgaste.",
            "Revisar conexiones de batería y su ruteo.",
            "Revisar por fugas la manguera de anticongelante del motor.",
            "Revisar nivel de aceite de motor (Añada ___ lts si se requiere).",
            "Revisar nivel de anticongelante (Añada ___ lts si se requiere).",
            "Abrir todas las válvulas de servicio del sistema de refrigeración.",
            "Revisar ajuste del interruptor de deshielo (1.40\" medidor de agua).",
            "Instalar última versión de software desde TransCentral.",
            "Registrar la versión de software instalada.",
        ],
    },
    {
        "clave": "B", "es_registro": False,
        "titulo": "B. Ajuste de APX*",
        "items": [
            "Revisar y ajustar el sistema de configuración de control (Config Settings).",
            "Revisar y ajustar los parámetros de función (Functional Parameters).",
            "Revisar y ajustar la registradora de datos (Data Recorder).",
        ],
    },
    {
        "clave": "C", "es_registro": False,
        "titulo": "C. Arranque de la Unidad",
        "items": [
            "Instalar juego de manómetros de servicio.",
            "Arrancar la unidad automáticamente. El buzzer debe sonar 5 segs antes del arranque; si no suena, reparar antes de continuar.",
            "Ingresar un setpoint de 11°F (-12°C), modo continuo (Continuous Run).",
            "Revisar si hay ruidos inusuales; revisar todas las líneas, mangueras y áreas de empaque por fugas.",
            "Revisar un flujo de aire correcto para condensador y evaporador.",
            "Después de 5 min. de operación, tomar lecturas (ver sección de lecturas).",
            "Revisar nivel de refrigerante (Añada ___ lbs si se requiere).",
            "Revisar nivel de aceite del compresor.",
        ],
    },
    {
        "clave": "D", "es_registro": False,
        "titulo": "D. Rodaje del Motor (Engine Break-In)",
        "items": [
            "Revisar nivel de tanque de combustible, añadir si se requiere.",
            "Abrir puertas del trailer. Arrancar la unidad e ingresar -22°F (-30°C) como setpoint, modo continuo (en clima extremo, 80°F/27°C). Operar mínimo 4-6 hrs.",
        ],
    },
    {
        "clave": "E", "es_registro": False,
        "titulo": "E. Prueba de Funcionamiento / Re-Chequeo",
        "items": [
            "Cerrar las puertas del trailer y realizar un pull-down de temperatura.",
            "A aprox. 0°F (-18°C) de temperatura de caja, revisar los datos de la unidad y registrar lecturas (ver sección de lecturas).",
            "Re-revisar nivel de refrigerante (Añada ___ lbs si se requiere).",
            "Colocar la unidad en modo de deshielo manual.",
            "Revisar los drenes de deshielo para un drenado adecuado.",
            "Registrar velocidades del motor (alta y baja, ver sección de lecturas).",
            "Seleccionar modo Arranque/Paro. Verificar que el motor cicla apagado y reinicia automáticamente.",
            "Iniciar y monitorear el modo Pre-Trip. Registrar resultado (Aprobado / Falló) y alarmas de pre-viaje.",
            "Apagar la unidad.",
            "Re-revisar nivel de aceite del compresor.",
            "Revisar nivel de aceite de motor (Añada ___ qts si se requiere).",
            "Revisar nivel de anticongelante del motor (Añada ___ qts si se requiere).",
            "Revisar tensión de bandas.",
            "Revisar mangueras de anticongelante, líneas de combustible/aceite y conexiones de refrigeración por fugas.",
            "Colocar las válvulas de servicio en posición Backseat, retirar manómetros y asegurar que las tapas estén instaladas.",
            "Revisar cualquier equipo opcional para una operación adecuada (EES, panel remoto, interruptores de puerta, etc.).",
            "Revisar la instalación y operación del bulkhead, lona de aire, tanque de combustible, semáforo, etc.",
            "Borrar todas las alarmas activas e inactivas del microprocesador.",
        ],
    },
    {
        "clave": "F", "es_registro": True,
        "titulo": "F. Registro de Unidad (Unit Registration)",
        "items": [
            "Llenar la tarjeta de registro de garantía (Warranty Registration Card).",
            "Registrar el EES con CARB.",
            "Estampar la fecha de puesta en servicio en la placa de la unidad.",
            "Registrar horómetro final del motor.",
            "Registrar horómetro final de Switch On.",
        ],
    },
]

# ──────────────────────────────────────────────────────────────────────────
# CHECKLIST — Vector 8100 / 8500 / 8600MT / 8611MT
# ──────────────────────────────────────────────────────────────────────────
CHECKLIST_VECTOR = [
    {
        "clave": "A", "es_registro": False,
        "titulo": "A. Revisión pre-arranque / Instalación",
        "items": [
            "Torquear los tornillos de montaje del huésped (60 ft-lbs).",
            "*Revisar instalación de tanque y línea de combustible (no aplica a 8100).",
            "*Revisar las conexiones de combustible y aceite por fugas (no aplica a 8100).",
            "Revisar apriete de conexiones de cable y tierra.",
            "Revisar que todos los arneses, cables, mangueras y líneas de combustible no presenten desgaste.",
            "Revisar conexiones de batería y su ruteo.",
            "*Revisar por fugas la manguera de anticongelante del motor.",
            "*Revisar nivel de aceite de motor (Añada ___ lts si se requiere).",
            "*Revisar nivel de anticongelante (Añada ___ lts si se requiere).",
            "Abrir todas las válvulas de servicio del sistema de refrigeración.",
            "Revisar ajuste del interruptor de deshielo (1.40\" medidor de agua).",
            "Instalar última versión de software desde TransCentral.",
            "Registrar la versión de software instalada.",
        ],
    },
    {
        "clave": "B", "es_registro": False,
        "titulo": "B. Ajuste de APX",
        "items": [
            "Revisar y ajustar el sistema de configuración de control (Config Settings).",
            "Revisar y ajustar el número de modelo correcto.",
            "Revisar y ajustar la configuración de evaporador remoto.",
            "Revisar y ajustar los parámetros de función (Functional Parameters).",
            "Revisar y ajustar la registradora de datos (Data Recorder).",
        ],
    },
    {
        "clave": "C", "es_registro": False,
        "titulo": "C. 8600MT & 8611MT — Tercer compartimento y evaporadores remotos",
        "items": [
            "Revisar torque de todos los tornillos de montaje del evaporador remoto (60 ft-lbs).",
            "Si el evaporador se instala cerca de la pared, montar con todas las cubiertas colocadas para asegurar acceso a los tornillos laterales.",
            "Revisar que todos los evaporadores remotos instalados tengan la calza correcta si solo se usa un dren de deshielo.",
            "Instalar línea de succión y línea de líquido según instrucciones de soldadura (válvulas 'front seated' al instalar).",
            "Asegurarse de utilizar oxígeno libre de nitrógeno al soldar según procedimiento adjunto.",
            "Probar por fugas de succión y de líquido.",
            "Conectar arneses de evaporadores remotos según instrucciones de instalación de la unidad.",
            "Verificar resistencia de aislamiento de cableado de alto voltaje de evaporadores remotos (procedimiento 98-50264-00).",
            "Evacuar hasta lograr un mínimo de 500 micrones.",
        ],
    },
    {
        "clave": "D", "es_registro": False,
        "titulo": "D. Arranque de la Unidad",
        "items": [
            "Instalar juego de manómetros de servicio.",
            "Arrancar la unidad automáticamente. El buzzer debe sonar 5 segs antes del arranque; si no suena, reparar antes de continuar.",
            "Ingresar un setpoint de 11°F (-12°C), modo continuo (Continuous Run).",
            "Revisar si hay ruidos inusuales; revisar todas las líneas, mangueras y áreas de empaque por fugas.",
            "Revisar un flujo de aire correcto para condensador y evaporador.",
            "Revisar rotación de ventilador(es) de evaporador de la unidad huésped.",
            "Revisar rotación de ventiladores de evaporadores remotos.",
            "Después de 5 min. de operación, tomar lecturas (ver sección de lecturas).",
        ],
    },
    {
        "clave": "E", "es_registro": False,
        "titulo": "E. Rodaje del Motor (Engine Break-In)",
        "items": [
            "*Revisar nivel de tanque de combustible, añadir si se requiere.",
            "Abrir puertas del trailer. Arrancar la unidad e ingresar -22°F (-30°C) como setpoint, modo continuo (en clima extremo, 80°F/27°C). Operar mínimo 4-6 hrs.",
        ],
    },
    {
        "clave": "F", "es_registro": False,
        "titulo": "F. Prueba de Funcionamiento / Re-Chequeo",
        "items": [
            "Cerrar las puertas del trailer y realizar un pull-down de temperatura.",
            "Ingresar un setpoint de 0°F (-18°C) en todos los compartimentos; revisar los datos de la unidad y registrar lecturas (ver sección de lecturas).",
            "Revisar nivel de carga de refrigerante (Añada ___ lbs si se requiere).",
            "Colocar la unidad en modo de deshielo manual.",
            "Revisar los drenes de deshielo para un drenado adecuado.",
            "Revisar consumo de resistencias C1 HTR1 y C1 HTR2 (amps).",
            "Revisar consumo de resistencias C2 HTR1 y C2 HTR2 (amps) — según configuración del sistema.",
            "Revisar rotación de ventiladores del condensador.",
            "Permitir que la unidad termine el deshielo automáticamente.",
            "Seleccionar modo Arranque/Paro. Verificar que el motor cicla apagado y reinicia automáticamente.",
            "Iniciar y monitorear el modo Pre-Trip. Registrar resultado (Aprobado / Falló) y alarmas de pre-viaje.",
            "Apagar la unidad.",
            "*Re-revisar nivel de aceite de motor (Añada ___ qts si se requiere).",
            "*Revisar nivel de anticongelante del motor (Añada ___ qts si se requiere).",
            "*Revisar tensión de bandas.",
            "Revisar mangueras de anticongelante, líneas de combustible/aceite y conexiones de refrigeración por fugas.",
            "Colocar las válvulas de servicio en posición Backseat, retirar manómetros y asegurar que las tapas estén instaladas.",
            "Revisar cualquier equipo opcional para una operación adecuada (EES, panel remoto, interruptores de puerta, etc.).",
            "Revisar la instalación y operación del bulkhead, lona de aire, tanque de combustible, semáforo, etc.",
            "Borrar todas las alarmas activas e inactivas del microprocesador.",
        ],
    },
    {
        "clave": "HV", "es_registro": False,
        "titulo": "Conexiones de Alto Voltaje (solo 8600MT y 8611MT)",
        "items": [
            "Asegurarse de que las conexiones a tierra estén limpias y bien apretadas.",
            "Revisar que el plug eléctrico de stand-by esté libre y limpio de acceso.",
            "Cables multiconductor de C.A. y C.D. ruteados desde la unidad huésped al evaporador remoto, cortados a la longitud correcta sin dobleces.",
            "Cables de C.A. y C.D. sujetados por separado en el canal; el cable de C.A. lo más alejado posible de la tubería de cobre del refrigerante.",
            "Abrazaderas instaladas a una distancia mínima de 12 pulgadas entre ellas.",
            "Etiqueta de alto voltaje instalada en la cubierta sobre los cables eléctricos dentro del tráiler.",
        ],
    },
    {
        "clave": "G", "es_registro": True,
        "titulo": "G. Registro de Unidad (Unit Registration)",
        "items": [
            "Llenar la tarjeta de registro de garantía (Warranty Registration Card).",
            "Registrar el EES con CARB.",
            "Estampar la fecha de puesta en servicio en la placa de la unidad.",
            "Registrar horómetro final del motor.",
            "Registrar horómetro final de Switch On.",
        ],
    },
]

# ──────────────────────────────────────────────────────────────────────────
# LECTURAS (valores numéricos del run-test) — con alias para emparejar
# automáticamente contra "toma_valores_campos.campo_nombre"
# ──────────────────────────────────────────────────────────────────────────
LECTURAS_X4 = [
    {"clave": "discharge_pressure",  "label": "Presión de Descarga",       "unidad": "PSIG", "grupo": "Arranque inicial (5 min)",
     "alias": ["presión de descarga", "presion descarga", "discharge pressure"]},
    {"clave": "suction_pressure",    "label": "Presión de Succión",        "unidad": "PSIG", "grupo": "Arranque inicial (5 min)",
     "alias": ["presión de succión", "presion succion", "suction pressure"]},
    {"clave": "ambient_temp",        "label": "Temperatura Ambiente",      "unidad": "°F",   "grupo": "Arranque inicial (5 min)",
     "alias": ["temperatura ambiente", "ambient temp", "ambient air temp"]},
    {"clave": "return_air_temp",     "label": "Temperatura de Retorno",    "unidad": "°F",   "grupo": "Arranque inicial (5 min)",
     "alias": ["temperatura de retorno", "return air temp"]},

    {"clave": "rt_suction_pressure", "label": "Presión de Succión",        "unidad": "PSIG", "grupo": "Run Test",
     "alias": ["presión succión run test", "suction pressure run test", "presión de succión"]},
    {"clave": "rt_discharge_pressure","label": "Presión de Descarga",      "unidad": "PSIG", "grupo": "Run Test",
     "alias": ["presión descarga run test", "discharge pressure run test", "presión de descarga"]},
    {"clave": "engine_coolant_temp", "label": "Temp. Anticongelante del Motor", "unidad": "°F", "grupo": "Run Test",
     "alias": ["temperatura anticongelante", "engine coolant temp"]},
    {"clave": "supply_air_temp",     "label": "Temperatura de Suministro", "unidad": "°F",   "grupo": "Run Test",
     "alias": ["temperatura de suministro", "supply air temp"]},
    {"clave": "defrost_term_temp",   "label": "Temperatura Término de Deshielo", "unidad": "°F", "grupo": "Run Test",
     "alias": ["temperatura termino deshielo", "defrost term temp"]},
    {"clave": "comp_disch_temp",     "label": "Temperatura Descarga Compresor", "unidad": "°F", "grupo": "Run Test",
     "alias": ["temperatura descarga compresor", "comp disch temp"]},
    {"clave": "battery",             "label": "Voltaje de Batería",        "unidad": "V",    "grupo": "Run Test",
     "alias": ["voltaje de batería", "voltaje bateria", "battery voltage"]},
    {"clave": "current_draw",        "label": "Consumo de Corriente",      "unidad": "A",    "grupo": "Run Test",
     "alias": ["consumo de corriente", "current draw"]},
    {"clave": "engine_rpm",          "label": "RPM del Motor",             "unidad": "RPM",  "grupo": "Run Test",
     "alias": ["rpm motor", "engine rpm"]},
    {"clave": "software_revision",   "label": "Revisión de Software",      "unidad": "",     "grupo": "Run Test",
     "alias": ["revisión de software", "software revision"]},
    {"clave": "high_speed_rpm",      "label": "Velocidad Alta del Motor",  "unidad": "RPM",  "grupo": "Run Test",
     "alias": ["velocidad alta motor", "high speed rpm"]},
    {"clave": "low_speed_rpm",       "label": "Velocidad Baja del Motor",  "unidad": "RPM",  "grupo": "Run Test",
     "alias": ["velocidad baja motor", "low speed rpm"]},
    {"clave": "pretrip_resultado",   "label": "Resultado Pre-Trip (Aprobado/Falló)", "unidad": "", "grupo": "Run Test",
     "alias": ["pretrip", "pre-trip", "pretrip pass fail"]},
    {"clave": "pretrip_alarmas",     "label": "Alarmas de Pre-Viaje",      "unidad": "",     "grupo": "Run Test",
     "alias": ["alarmas pre viaje", "pretrip alarms"]},
]

# Para Vector, las lecturas de Run Test se repiten por compartimento (C1/C2/C3).
_VECTOR_COMPARTIMENTOS = ["C1", "C2", "C3"]

LECTURAS_VECTOR_BASE = [
    {"clave": "suction_pressure",    "label": "Presión de Succión",         "unidad": "PSIG", "grupo": "Run Test (general)",
     "alias": ["presión de succión", "presion succion", "suction pressure"]},
    {"clave": "discharge_pressure",  "label": "Presión de Descarga",        "unidad": "PSIG", "grupo": "Run Test (general)",
     "alias": ["presión de descarga", "presion descarga", "discharge pressure"]},
    {"clave": "discharge_temp",      "label": "Temperatura de Descarga",    "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura de descarga", "discharge temp"]},
    {"clave": "battery_voltage",     "label": "Voltaje de Batería",         "unidad": "V",    "grupo": "Run Test (general)",
     "alias": ["voltaje de batería", "voltaje bateria", "battery voltage"]},
    {"clave": "coolant_temp",        "label": "Temp. Anticongelante",       "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura anticongelante", "coolant temp"]},
    {"clave": "ambient_air_temp",    "label": "Temperatura Ambiente",       "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura ambiente", "ambient air temp"]},
    {"clave": "evap_outlet_temp",    "label": "Temp. Salida de Evaporador", "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura salida evaporador", "evap outlet temp"]},
    {"clave": "comp_suct_temp",      "label": "Temp. Succión Compresor",    "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura succión compresor", "comp suct temp"]},
    {"clave": "comp_disch_temp",     "label": "Temp. Descarga Compresor",   "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura descarga compresor", "comp disch temp"]},
    {"clave": "defrost_term_temp",   "label": "Temp. Término de Deshielo",  "unidad": "°F",   "grupo": "Run Test (general)",
     "alias": ["temperatura termino deshielo", "defrost term temp"]},
    {"clave": "software_rev",        "label": "Revisión de Software",       "unidad": "",     "grupo": "Run Test (general)",
     "alias": ["revisión de software", "software revision"]},
    {"clave": "high_speed_rpm",      "label": "Velocidad Alta del Motor",   "unidad": "RPM",  "grupo": "Run Test (general)",
     "alias": ["velocidad alta motor", "high speed rpm"]},
    {"clave": "low_speed_rpm",       "label": "Velocidad Baja del Motor",   "unidad": "RPM",  "grupo": "Run Test (general)",
     "alias": ["velocidad baja motor", "low speed rpm"]},
    {"clave": "pretrip_resultado",   "label": "Resultado Pre-Trip (Aprobado/Falló)", "unidad": "", "grupo": "Run Test (general)",
     "alias": ["pretrip", "pre-trip", "pretrip pass fail"]},
    {"clave": "pretrip_alarmas",     "label": "Alarmas de Pre-Viaje",       "unidad": "",     "grupo": "Run Test (general)",
     "alias": ["alarmas pre viaje", "pretrip alarms"]},
]

def _lecturas_vector_compartimentos():
    campos = []
    for comp in _VECTOR_COMPARTIMENTOS:
        for sub, label_sub in (("RAT", "Return Air Temp"), ("RRAT", "Remote RAT"), ("SAT", "Supply Air Temp")):
            clave = f"{comp.lower()}_{sub.lower()}"
            campos.append({
                "clave": clave,
                "label": f"{comp} {label_sub}",
                "unidad": "°F",
                "grupo": f"Compartimento {comp}",
                "alias": [f"{comp} {sub}".lower(), f"{comp} {label_sub}".lower()],
            })
    return campos

LECTURAS_VECTOR = LECTURAS_VECTOR_BASE + _lecturas_vector_compartimentos()

# ──────────────────────────────────────────────────────────────────────────
# TABLA DE CONFIGURACIÓN (compartida — Ajuste de Fábrica / Cambio a)
# Es informativa: el "ajuste_fabrica" es el valor típico de fábrica según el
# manual; el técnico llena "cambio_a" solo si el ajuste real fue distinto.
# ──────────────────────────────────────────────────────────────────────────
CONFIG_TABLE = [
    ("Identificación de Unidad", "Modelo de Unidad", "Ver placa de serie"),
    ("Identificación de Unidad", "ID de Trailer", ""),
    ("Identificación de Unidad", "Ajuste de Fecha y Hora", ""),

    ("Setpoint(s) y Bloqueo de Rango", "Decimal", "No mostrado"),
    ("Setpoint(s) y Bloqueo de Rango", "Setpoint Mínimo", "-22.0 °F"),
    ("Setpoint(s) y Bloqueo de Rango", "Setpoint Máximo", "89.6 °F"),
    ("Setpoint(s) y Bloqueo de Rango", "Rango Bloqueo 1", "OFF"),
    ("Setpoint(s) y Bloqueo de Rango", "Rango Bloqueo 2", "OFF"),

    ("Ajustes Arranque-Paro", "Corriente en S/S Apagado", "7.0 AMPS"),
    ("Ajustes Arranque-Paro", "Voltaje para S/S Reinicio", "12.2 VOLTS"),
    ("Ajustes Arranque-Paro", "Temp. Motor para S/S Reinicio", "10.0 °F"),
    ("Ajustes Arranque-Paro", "Parámetros S/S", "TOGETHER"),

    ("Intelliset y ProductShield", "Habilitar Intelliset con tecla =", "NO"),
    ("Intelliset y ProductShield", "ProductShield Econo", "OFF"),
    ("Intelliset y ProductShield", "ProductShield High Air", "OFF"),
    ("Intelliset y ProductShield", "ProductShield Winter", "OFF"),
    ("Intelliset y ProductShield", "ProductShield Fresh", "NO"),

    ("Ajustes de Motor", "Tiempo de Precalentado / Resistencia Toma de Aire", "NO"),
    ("Ajustes de Motor", "Interruptor de Nivel de Aceite Motor", "NO"),
    ("Ajustes de Motor", "Paro por Nivel de Aceite Motor", "NO"),
    ("Ajustes de Motor", "Paro por Alta Temp. Motor", "NO"),
    ("Ajustes de Motor", "Paro por Presión de Aceite Motor", "NO"),
    ("Ajustes de Motor", "Sensor Nivel de Combustible", "NO"),
    ("Ajustes de Motor", "Combustible Bajo", "UNIT SHUTDOWN"),
    ("Ajustes de Motor", "Resistencia de Combustible", "NOT INSTALLED"),
    ("Ajustes de Motor", "Máx. Posición Throttle", "125%"),

    ("Ajustes de Alarmas", "Paro Fuera de Rango", "NO"),
    ("Ajustes de Alarmas", "Paro por Alarma RPM", "NO"),
    ("Ajustes de Alarmas", "Paro por Baja Presión", "YES"),
    ("Ajustes de Alarmas", "Retraso de Paro Baja Presión", "120 SECS"),
    ("Ajustes de Alarmas", "Paro por Alta Presión de Succión", "YES"),
    ("Ajustes de Alarmas", "Paro Sistema de Refrigeración", "YES"),
    ("Ajustes de Alarmas", "Paro por Chequeo de Alternador", "NO"),

    ("Horómetros", "Mostrar Horas Totales de Motor", "YES"),
    ("Horómetros", "Mostrar Horas Totales Switch On", "YES"),

    ("Configuración de Mantenimientos Preventivos", "PM 1", "OFF"),
    ("Configuración de Mantenimientos Preventivos", "PM 2", "OFF"),
    ("Configuración de Mantenimientos Preventivos", "PM 3", "OFF"),
    ("Configuración de Mantenimientos Preventivos", "PM 4", "OFF"),
    ("Configuración de Mantenimientos Preventivos", "PM 5", "OFF"),

    ("Sensores Remotos", "Sensor Temp. Remoto 1", "OFF"),
    ("Sensores Remotos", "Sensor Temp. Remoto 2", "ON"),
    ("Sensores Remotos", "Interruptor de Puerta", "NOT INSTALLED"),
    ("Sensores Remotos", "Interruptor Remoto 1", "NOT INSTALLED"),

    ("Otros Ajustes", "Habilitar Modo Usuario Avanzado", "NO"),
    ("Otros Ajustes", "Proteger Datos con PIN", "NO"),
    ("Otros Ajustes", "Bloqueo de Parámetros", "NO"),
    ("Otros Ajustes", "8 Horas de Datos Adicionales", "YES"),
    ("Otros Ajustes", "Retraso Alta Velocidad", "1.0 MINS"),
    ("Otros Ajustes", "Semáforo (Light Bar)", "NOT INSTALLED"),

    ("Ajustes de Tren", "Operación de Unidad", "STANDARD"),
    ("Ajustes de Aire Auto Fresh", "Aire AutoFresh", "NOT INSTALLED"),
    ("Ajuste de Sistema de Emisiones del Motor", "EES", ""),

    ("Parámetros de Función — Ajustes de Economía", "Retraso Baja Vel. S/S", "10 MINS"),
    ("Parámetros de Función — Ajustes de Economía", "Retraso Baja Vel. Continuo", "0 MINS"),
    ("Parámetros de Función — Ajustes de Economía", "Flujo de Aire", "NORMAL"),

    ("Ajustes de Temperatura", "Temporizador de Deshielo", "6 HRS"),
    ("Ajustes de Temperatura", "Fresh Protect", "C"),
    ("Ajustes de Temperatura", "Control de Temperatura", "RETURN AIR"),
    ("Ajustes de Temperatura", "Alarma Temperatura Fuera de Rango", "OFF"),

    ("Ajustes Arranque-Paro (avanzado)", "Tiempo Mínimo de Trabajo", "4 MINS"),
    ("Ajustes Arranque-Paro (avanzado)", "Tiempo Mínimo Apagado", "30 MINS"),
    ("Ajustes Arranque-Paro (avanzado)", "Temp. de Reinicio", "5.4 °F"),
    ("Ajustes Arranque-Paro (avanzado)", "Temperatura de Re-arranque (Override)", "12.0 °F"),
    ("Ajustes Arranque-Paro (avanzado)", "Máximo Tiempo Apagado", "OFF"),
    ("Ajustes Arranque-Paro (avanzado)", "Tolerancia Rango de Congelado", "0.0 °F"),
    ("Ajustes Arranque-Paro (avanzado)", "Modo Sleep", "OFF"),

    ("Preferencias de Visualización", "Mostrar Temperaturas en", "°F"),
    ("Preferencias de Visualización", "Mostrar Presiones en", "PSIG"),
    ("Preferencias de Visualización", "Formato de Fecha", "MM/DD/YYYY"),
    ("Preferencias de Visualización", "Descripción de Alarmas", "YES"),
    ("Preferencias de Visualización", "Contraste", "39"),

    ("Registradora de Datos — Sensores", "Temperatura de Retorno", "Promedio"),
    ("Registradora de Datos — Sensores", "Temperatura de Suministro", "Promedio"),
    ("Registradora de Datos — Sensores", "Temperatura Ambiente", "Promedio"),
    ("Registradora de Datos — Sensores", "Temp. Término de Deshielo 1", "Promedio"),
    ("Registradora de Datos — Sensores", "Temp. Término de Deshielo 2", "Promedio"),
    ("Registradora de Datos — Sensores", "Temp. Descarga Compresor", "Promedio"),
    ("Registradora de Datos — Sensores", "Temp. Succión Compresor", "Promedio"),
    ("Registradora de Datos — Sensores", "Temperatura Evaporador", "Promedio"),
    ("Registradora de Datos — Sensores", "Temp. Anticongelante del Motor", "Promedio"),
    ("Registradora de Datos — Sensores", "Presión Descarga Compresor", "Promedio"),
    ("Registradora de Datos — Sensores", "Presión Succión Compresor", "Promedio"),
    ("Registradora de Datos — Sensores", "Presión Evaporador", "Promedio"),
    ("Registradora de Datos — Sensores", "Voltaje de Batería", "Snapshot"),
    ("Registradora de Datos — Sensores", "Corriente DC de Batería", "Snapshot"),
    ("Registradora de Datos — Sensores", "RPM del Motor", "Snapshot"),
    ("Registradora de Datos — Sensores", "Sensor Remoto #1", "OFF"),
    ("Registradora de Datos — Sensores", "Sensor Remoto #2", "ON"),
    ("Registradora de Datos — Sensores", "Intervalo de Registro", "10 Minutos"),

    ("Eventos", "Inicio de Pre-Viaje", "On"),
    ("Eventos", "Fin de Pre-Viaje", "On"),
    ("Eventos", "ID de Trailer", "On"),
    ("Eventos", "Número de Serie de Unidad", "On"),
    ("Eventos", "Número de Modelo de Unidad", "On"),
    ("Eventos", "Modo de Unidad", "On"),
    ("Eventos", "Modo de Control", "On"),
    ("Eventos", "Puerta Abierta/Cerrada", "On"),
    ("Eventos", "Calibración de Transductor", "On"),
]

# ──────────────────────────────────────────────────────────────────────────
# API pública del módulo
# ──────────────────────────────────────────────────────────────────────────
TEMPLATES = {
    "x4": {
        "clave": "x4",
        "nombre": "X4 7300 & 7500",
        "nombre_completo": "Unit Installation & Pre-Delivery Inspection — X4 7300 & 7500 Trailer Refrigeration Units",
        "header_fields": HEADER_FIELDS_COMMON,
        "secciones": CHECKLIST_X4,
        "lecturas": LECTURAS_X4,
        "config_table": CONFIG_TABLE,
    },
    "vector": {
        "clave": "vector",
        "nombre": "Vector 8100 / 8500 / 8600MT / 8611MT",
        "nombre_completo": "Unit Installation & Pre-Delivery Inspection — Vector 8100, 8500, 8600MT & 8611MT Trailer Refrigeration Units",
        "header_fields": HEADER_FIELDS_COMMON + HEADER_FIELDS_VECTOR_EXTRA,
        "secciones": CHECKLIST_VECTOR,
        "lecturas": LECTURAS_VECTOR,
        "config_table": CONFIG_TABLE,
    },
}


def detectar_tipo_por_modelo(reefer_model: str) -> str:
    """Detecta 'x4' o 'vector' a partir del texto libre reefer_model. Devuelve '' si no se puede determinar."""
    if not reefer_model:
        return ""
    m = reefer_model.strip().lower()
    if "vector" in m:
        return "vector"
    if "x4" in m or "7300" in m or "7500" in m:
        return "x4"
    return ""


def normalizar(txt: str) -> str:
    """Normaliza texto para emparejar nombres de campos (minúsculas, sin acentos ni espacios extra)."""
    if not txt:
        return ""
    import unicodedata
    t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    return " ".join(t.lower().strip().split())


def checklist_items_planos(tipo: str):
    """Devuelve lista plana [(clave_item, texto, es_registro)] para un tipo de plantilla."""
    tpl = TEMPLATES[tipo]
    out = []
    for sec in tpl["secciones"]:
        for i, texto in enumerate(sec["items"]):
            clave_item = f"chk_{sec['clave']}_{i+1}"
            out.append((clave_item, sec["clave"], texto, sec["es_registro"]))
    return out
