# backend/db.py
import os
import pymysql
from dbutils.pooled_db import PooledDB  # ← Importante: dbutils en minúsculas

pool = None

def _run_migrations():
    """Aplica migraciones de columnas nuevas sin romper si ya existen."""
    conn = pool.connection()
    try:
        with conn.cursor() as cur:
            # ── retardo_min en registros_asistencia ───────────────────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'registros_asistencia'
                  AND COLUMN_NAME  = 'retardo_min'
            """)
            row = cur.fetchone()
            count = row[0] if isinstance(row, tuple) else list(row.values())[0]
            if count == 0:
                cur.execute(
                    "ALTER TABLE registros_asistencia ADD COLUMN retardo_min INT NOT NULL DEFAULT 0"
                )
                conn.commit()
                print("✅ Migración: columna retardo_min añadida a registros_asistencia")

            # ── fecha_registro en unidades ────────────────────────────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'unidades'
                  AND COLUMN_NAME  = 'fecha_registro'
            """)
            row2 = cur.fetchone()
            count2 = row2[0] if isinstance(row2, tuple) else list(row2.values())[0]
            if count2 == 0:
                cur.execute(
                    "ALTER TABLE unidades ADD COLUMN fecha_registro DATETIME DEFAULT NULL"
                )
                conn.commit()
                print("✅ Migración: columna fecha_registro añadida a unidades")
            # ── created_at en evidencias ──────────────────────────────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'evidencias'
                  AND COLUMN_NAME  = 'created_at'
            """)
            row3 = cur.fetchone()
            count3 = row3[0] if isinstance(row3, tuple) else list(row3.values())[0]
            if count3 == 0:
                cur.execute(
                    "ALTER TABLE evidencias ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                )
                conn.commit()
                print("✅ Migración: columna created_at añadida a evidencias")

            # ── oculto en unidades (ocultar lote del dashboard) ───────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'unidades'
                  AND COLUMN_NAME  = 'oculto'
            """)
            row4 = cur.fetchone()
            count4 = row4[0] if isinstance(row4, tuple) else list(row4.values())[0]
            if count4 == 0:
                cur.execute(
                    "ALTER TABLE unidades ADD COLUMN oculto TINYINT(1) NOT NULL DEFAULT 0"
                )
                conn.commit()
                print("✅ Migración: columna oculto añadida a unidades")
            # ── foto_url en users (MEDIUMTEXT para base64 de imagen) ─────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'users'
                  AND COLUMN_NAME  = 'foto_url'
            """)
            row_f = cur.fetchone()
            count_f = row_f[0] if isinstance(row_f, tuple) else list(row_f.values())[0]
            if count_f == 0:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN foto_url MEDIUMTEXT DEFAULT NULL"
                )
                conn.commit()
                print("✅ Migración: columna foto_url añadida a users")
            else:
                cur.execute("""
                    SELECT DATA_TYPE FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'users'
                      AND COLUMN_NAME  = 'foto_url'
                """)
                row_dt = cur.fetchone()
                dtype = (row_dt[0] if isinstance(row_dt, tuple) else list(row_dt.values())[0] or "").lower()
                if dtype == "varchar":
                    cur.execute(
                        "ALTER TABLE users MODIFY COLUMN foto_url MEDIUMTEXT DEFAULT NULL"
                    )
                    conn.commit()
                    print("✅ Migración: foto_url ampliada a MEDIUMTEXT")

            # ── puesto en users ───────────────────────────────────────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'users'
                  AND COLUMN_NAME  = 'puesto'
            """)
            row_p = cur.fetchone()
            count_p = row_p[0] if isinstance(row_p, tuple) else list(row_p.values())[0]
            if count_p == 0:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN puesto VARCHAR(100) DEFAULT NULL"
                )
                conn.commit()
                print("✅ Migración: columna puesto añadida a users")

            # ── alarmas_reefer (Alarm Troubleshooting Vector 8600MT) ──────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'alarmas_reefer'
            """)
            row5 = cur.fetchone()
            count5 = row5[0] if isinstance(row5, tuple) else list(row5.values())[0]
            if count5 == 0:
                cur.execute("""
                    CREATE TABLE alarmas_reefer (
                        codigo              VARCHAR(10)  NOT NULL PRIMARY KEY,
                        titulo              VARCHAR(255) NOT NULL,
                        activacion          TEXT,
                        control_unidad      TEXT,
                        condicion_reset     TEXT,
                        notas               TEXT,
                        acciones_correctivas JSON,
                        referencia_alarma   JSON,
                        alarmas_relacionadas JSON
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tabla alarmas_reefer creada")

            # ── figuras en alarmas_reefer (diagramas referenciados, ej. Figura 2.6) ──
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'alarmas_reefer'
                  AND COLUMN_NAME  = 'figuras'
            """)
            row7 = cur.fetchone()
            count7 = row7[0] if isinstance(row7, tuple) else list(row7.values())[0]
            if count7 == 0:
                cur.execute(
                    "ALTER TABLE alarmas_reefer ADD COLUMN figuras JSON DEFAULT NULL"
                )
                conn.commit()
                print("✅ Migración: columna figuras añadida a alarmas_reefer")

            # ── Auto-seed: cargar alarmas.json si la tabla está vacía ─────────
            cur.execute("SELECT COUNT(*) FROM alarmas_reefer")
            row6 = cur.fetchone()
            count6 = row6[0] if isinstance(row6, tuple) else list(row6.values())[0]
            if count6 == 0:
                import json as _json, pathlib as _pl
                _json_path = _pl.Path(__file__).parent / "alarmas.json"
                if _json_path.exists():
                    alarmas = _json.loads(_json_path.read_text(encoding="utf-8"))
                    for a in alarmas:
                        cur.execute(
                            """
                            INSERT INTO alarmas_reefer
                                (codigo, titulo, activacion, control_unidad,
                                 condicion_reset, notas, acciones_correctivas,
                                 referencia_alarma, alarmas_relacionadas, figuras)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON DUPLICATE KEY UPDATE titulo=VALUES(titulo)
                            """,
                            (
                                a["codigo"],
                                a["titulo"],
                                a.get("activacion"),
                                a.get("control_unidad"),
                                a.get("condicion_reset"),
                                a.get("notas"),
                                _json.dumps(a.get("acciones_correctivas") or [], ensure_ascii=False),
                                _json.dumps(a.get("referencia_alarma"), ensure_ascii=False),
                                _json.dumps(a.get("alarmas_relacionadas") or [], ensure_ascii=False),
                                _json.dumps(a.get("figuras") or [], ensure_ascii=False),
                            ),
                        )
                    conn.commit()
                    print(f"✅ Auto-seed: {len(alarmas)} alarmas cargadas en alarmas_reefer")
                else:
                    print("⚠️  alarmas.json no encontrado — ejecuta cargar_alarmas.py manualmente")
            else:
                # Tabla ya tiene datos: sincronizar SOLO el campo figuras si está vacío/NULL
                # en algún registro que sí tiene figuras en el JSON (no pisa ediciones manuales).
                import json as _json, pathlib as _pl
                _json_path = _pl.Path(__file__).parent / "alarmas.json"
                if _json_path.exists():
                    alarmas = _json.loads(_json_path.read_text(encoding="utf-8"))
                    con_figuras = [a for a in alarmas if a.get("figuras")]
                    actualizadas = 0
                    for a in con_figuras:
                        cur.execute(
                            """
                            UPDATE alarmas_reefer
                            SET figuras = %s
                            WHERE codigo = %s
                              AND (figuras IS NULL OR JSON_LENGTH(figuras) = 0)
                            """,
                            (
                                _json.dumps(a.get("figuras") or [], ensure_ascii=False),
                                a["codigo"],
                            ),
                        )
                        actualizadas += cur.rowcount
                    if actualizadas:
                        conn.commit()
                        print(f"✅ Sync: figuras añadidas a {actualizadas} alarmas existentes")

            # ── schedule_produccion (DRY & Reefer VT Production Daily Schedule) ──
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'schedule_produccion'
            """)
            row9 = cur.fetchone()
            count9 = row9[0] if isinstance(row9, tuple) else list(row9.values())[0]
            if count9 == 0:
                cur.execute("""
                    CREATE TABLE schedule_produccion (
                        id            INT AUTO_INCREMENT PRIMARY KEY,
                        mes_anio      VARCHAR(7)   NOT NULL,
                        orden         INT          NOT NULL DEFAULT 0,
                        linea         VARCHAR(50)  DEFAULT '',
                        owner         VARCHAR(150) DEFAULT '',
                        size          VARCHAR(20)  DEFAULT '',
                        tipo          VARCHAR(50)  DEFAULT '',
                        reefer_brand  VARCHAR(150) DEFAULT '',
                        notas_evaps   VARCHAR(255) DEFAULT '',
                        qty           INT          DEFAULT 0,
                        model_no      VARCHAR(50)  DEFAULT '',
                        dias          JSON         DEFAULT NULL,
                        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_mes (mes_anio)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tabla schedule_produccion creada")

            # ── lote (editable) en schedule_produccion ────────────────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'schedule_produccion'
                  AND COLUMN_NAME  = 'lote'
            """)
            row10 = cur.fetchone()
            count10 = row10[0] if isinstance(row10, tuple) else list(row10.values())[0]
            if count10 == 0:
                cur.execute(
                    "ALTER TABLE schedule_produccion ADD COLUMN lote VARCHAR(50) DEFAULT '' AFTER model_no"
                )
                conn.commit()
                print("✅ Migración: columna lote añadida a schedule_produccion")

            # ── comentarios_asistencia (comentarios semanales por técnico) ────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'comentarios_asistencia'
            """)
            row8 = cur.fetchone()
            count8 = row8[0] if isinstance(row8, tuple) else list(row8.values())[0]
            if count8 == 0:
                cur.execute("""
                    CREATE TABLE comentarios_asistencia (
                        id          INT AUTO_INCREMENT PRIMARY KEY,
                        username    VARCHAR(100) NOT NULL,
                        semana      DATE         NOT NULL,
                        comentario  TEXT,
                        updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY uniq_user_semana (username, semana)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tabla comentarios_asistencia creada")

            # ── evaporator_model_1 / evaporator_model_2 en unidades ───────────
            for col in ("evaporator_model_1", "evaporator_model_2"):
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'unidades'
                      AND COLUMN_NAME  = %s
                """, (col,))
                row_ev = cur.fetchone()
                count_ev = row_ev[0] if isinstance(row_ev, tuple) else list(row_ev.values())[0]
                if count_ev == 0:
                    cur.execute(
                        f"ALTER TABLE unidades ADD COLUMN {col} VARCHAR(20) DEFAULT NULL"
                    )
                    conn.commit()
                    print(f"✅ Migración: columna {col} añadida a unidades")

            # ── nombre_completo en users ───────────────────────────────────────
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'users'
                  AND COLUMN_NAME  = 'nombre_completo'
            """)
            row_nc = cur.fetchone()
            count_nc = row_nc[0] if isinstance(row_nc, tuple) else list(row_nc.values())[0]
            if count_nc == 0:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN nombre_completo VARCHAR(120) DEFAULT NULL"
                )
                conn.commit()
                print("✅ Migración: columna nombre_completo añadida a users")

            # ── alerta_6h_enviada en asignaciones (contador de horas 'Corriendo') ──
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'asignaciones'
                  AND COLUMN_NAME  = 'alerta_6h_enviada'
            """)
            row_a6 = cur.fetchone()
            count_a6 = row_a6[0] if isinstance(row_a6, tuple) else list(row_a6.values())[0]
            if count_a6 == 0:
                cur.execute(
                    "ALTER TABLE asignaciones ADD COLUMN alerta_6h_enviada TINYINT(1) NOT NULL DEFAULT 0"
                )
                conn.commit()
                print("✅ Migración: columna alerta_6h_enviada añadida a asignaciones")

            # ── corriendo_tracking (contador acumulado de horas 'Corriendo') ──
            # Vive independiente de la tabla `asignaciones` para poder acumular
            # tiempo a través de pausas/reinicios hasta llegar a las 6 horas.
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'corriendo_tracking'
            """)
            row_ct = cur.fetchone()
            count_ct = row_ct[0] if isinstance(row_ct, tuple) else list(row_ct.values())[0]
            if count_ct == 0:
                cur.execute("""
                    CREATE TABLE corriendo_tracking (
                        unidad               VARCHAR(50) PRIMARY KEY,
                        segundos_acumulados  INT NOT NULL DEFAULT 0,
                        corriendo_desde      DATETIME DEFAULT NULL,
                        alerta_6h_enviada    TINYINT(1) NOT NULL DEFAULT 0,
                        actualizado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tabla corriendo_tracking creada")

            # ── evidencias: columna contenido con tamaño suficiente ───────────
            # Si la columna es un BLOB normal (límite 64KB), las fotos comprimidas
            # (hasta ~800KB antes de comprimir) se truncan/corrompen en silencio,
            # causando que "no aparezcan" algunas imágenes. La ampliamos a LONGBLOB.
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'evidencias'
            """)
            row_ev_ex = cur.fetchone()
            count_ev_ex = row_ev_ex[0] if isinstance(row_ev_ex, tuple) else list(row_ev_ex.values())[0]
            if count_ev_ex > 0:
                cur.execute("""
                    SELECT DATA_TYPE FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'evidencias'
                      AND COLUMN_NAME  = 'contenido'
                """)
                row_ec = cur.fetchone()
                if row_ec:
                    dtype_ec = (row_ec[0] if isinstance(row_ec, tuple) else list(row_ec.values())[0] or "").lower()
                    if dtype_ec in ("blob", "tinyblob"):
                        cur.execute(
                            "ALTER TABLE evidencias MODIFY COLUMN contenido LONGBLOB"
                        )
                        conn.commit()
                        print(f"✅ Migración: evidencias.contenido ampliada de {dtype_ec} a LONGBLOB")

                # ── evidencias: asignacion_id (vincula la foto a la actividad exacta) ─
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'evidencias'
                      AND COLUMN_NAME  = 'asignacion_id'
                """)
                row_eai = cur.fetchone()
                count_eai = row_eai[0] if isinstance(row_eai, tuple) else list(row_eai.values())[0]
                if count_eai == 0:
                    cur.execute(
                        "ALTER TABLE evidencias ADD COLUMN asignacion_id INT DEFAULT NULL, "
                        "ADD INDEX idx_asignacion_id (asignacion_id)"
                    )
                    conn.commit()
                    print("✅ Migración: columna asignacion_id añadida a evidencias")

                # ── evidencias: tipo (foto/video) + mime_type + OneDrive ──────────
                # Todo este bloque va en su propio try/except: si algo aquí falla,
                # NO debe tumbar las migraciones que vienen después (comentario en
                # unidades, tablas de PDI, etc.) — antes todo el archivo compartía
                # un único try/except y un error a la mitad silenciaba todo el resto.
                try:
                    # Permite que los técnicos suban también video como evidencia.
                    # tipo se infiere del nombre de archivo al subir; mime_type se
                    # guarda para servir el Content-Type correcto (antes se adivinaba
                    # solo por extensión, lo cual no cubre .mov, .webm, etc.).
                    cur.execute("""
                        SELECT COLUMN_NAME FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME   = 'evidencias'
                          AND COLUMN_NAME IN ('tipo', 'mime_type')
                    """)
                    cols_existentes = {
                        (r[0] if isinstance(r, tuple) else list(r.values())[0])
                        for r in (cur.fetchall() or [])
                    }
                    if "tipo" not in cols_existentes:
                        cur.execute(
                            "ALTER TABLE evidencias ADD COLUMN tipo VARCHAR(10) NOT NULL DEFAULT 'foto'"
                        )
                        conn.commit()
                        print("✅ Migración: columna tipo añadida a evidencias (foto/video)")
                    if "mime_type" not in cols_existentes:
                        cur.execute(
                            "ALTER TABLE evidencias ADD COLUMN mime_type VARCHAR(60) DEFAULT NULL"
                        )
                        conn.commit()
                        print("✅ Migración: columna mime_type añadida a evidencias")

                    # Índice de tipo por separado (algunas versiones de TiDB no
                    # aceptan combinar ADD COLUMN + ADD INDEX del mismo campo en
                    # un solo ALTER cuando el campo se acaba de crear)
                    cur.execute("""
                        SELECT COUNT(*) FROM information_schema.STATISTICS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME   = 'evidencias'
                          AND INDEX_NAME   = 'idx_tipo'
                    """)
                    row_idx = cur.fetchone()
                    count_idx = row_idx[0] if isinstance(row_idx, tuple) else list(row_idx.values())[0]
                    if count_idx == 0:
                        cur.execute("ALTER TABLE evidencias ADD INDEX idx_tipo (tipo)")
                        conn.commit()
                        print("✅ Migración: índice idx_tipo añadido a evidencias")

                    # ── onedrive_item_id + onedrive_url ────────────────────────
                    # Para video, el archivo se sube a OneDrive y NO se guarda el
                    # blob completo en la base de datos (para no saturarla); se
                    # guarda solo la referencia al archivo en OneDrive.
                    cur.execute("""
                        SELECT COLUMN_NAME FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME   = 'evidencias'
                          AND COLUMN_NAME IN ('onedrive_item_id', 'onedrive_url')
                    """)
                    cols_od = {
                        (r[0] if isinstance(r, tuple) else list(r.values())[0])
                        for r in (cur.fetchall() or [])
                    }
                    if "onedrive_item_id" not in cols_od:
                        cur.execute(
                            "ALTER TABLE evidencias ADD COLUMN onedrive_item_id VARCHAR(150) DEFAULT NULL"
                        )
                        conn.commit()
                        print("✅ Migración: columna onedrive_item_id añadida a evidencias")
                    if "onedrive_url" not in cols_od:
                        cur.execute(
                            "ALTER TABLE evidencias ADD COLUMN onedrive_url VARCHAR(500) DEFAULT NULL"
                        )
                        conn.commit()
                        print("✅ Migración: columna onedrive_url añadida a evidencias")
                    # contenido debe poder ser NULL para videos que solo viven en OneDrive
                    cur.execute("""
                        SELECT IS_NULLABLE FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME   = 'evidencias'
                          AND COLUMN_NAME  = 'contenido'
                    """)
                    row_null = cur.fetchone()
                    if row_null:
                        is_nullable = (row_null[0] if isinstance(row_null, tuple) else list(row_null.values())[0])
                        if is_nullable == "NO":
                            cur.execute("ALTER TABLE evidencias MODIFY COLUMN contenido LONGBLOB NULL")
                            conn.commit()
                            print("✅ Migración: evidencias.contenido ahora permite NULL (video en OneDrive)")
                except Exception as e_video:
                    print(f"⚠️  Migración de video/OneDrive en evidencias omitida: {e_video}")
                    conn.rollback()

                # ── comentario en unidades (nota libre del admin en el dashboard) ─
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'unidades'
                      AND COLUMN_NAME  = 'comentario'
                """)
                row_com = cur.fetchone()
                count_com = row_com[0] if isinstance(row_com, tuple) else list(row_com.values())[0]
                if count_com == 0:
                    cur.execute(
                        "ALTER TABLE unidades ADD COLUMN comentario TEXT DEFAULT NULL"
                    )
                    conn.commit()
                    print("✅ Migración: columna comentario añadida a unidades")

                # ── actividades_ocultas (columnas del dashboard ocultables por admin) ─
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS actividades_ocultas (
                        actividad VARCHAR(50) NOT NULL PRIMARY KEY,
                        fecha_ocultada DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

                # ── juegos_puntajes (marcadores de la sección de Juegos) ──────────
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS juegos_puntajes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(80) NOT NULL,
                        juego VARCHAR(30) NOT NULL,
                        puntaje INT NOT NULL,
                        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_juego_puntaje (juego, puntaje)
                    )
                """)
                conn.commit()

                # ── toma_valores_campos / toma_valores_datos (red de seguridad;  ──
                # ── ya existían en producción pero no estaban en migraciones)    ──
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS toma_valores_campos (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        campo_nombre VARCHAR(150) NOT NULL UNIQUE,
                        campo_orden INT NOT NULL DEFAULT 0
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS toma_valores_datos (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        asignacion_id INT NOT NULL,
                        campo_nombre VARCHAR(150) NOT NULL,
                        valor TEXT,
                        INDEX idx_asignacion (asignacion_id),
                        INDEX idx_campo (campo_nombre)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()

                # ── lotes_config (tipo de reefer asignado a cada lote: x4/vector) ─
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS lotes_config (
                        id_lote      VARCHAR(50) NOT NULL PRIMARY KEY,
                        tipo_reefer  VARCHAR(20) DEFAULT NULL,
                        updated_by   VARCHAR(100) DEFAULT NULL,
                        updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()

                # ── pdi_inspecciones (encabezado de cada PDI, 1 por unidad) ───────
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pdi_inspecciones (
                        id                    INT AUTO_INCREMENT PRIMARY KEY,
                        id_lote               VARCHAR(50)  DEFAULT NULL,
                        unit_number           VARCHAR(50)  NOT NULL,
                        tipo                  VARCHAR(20)  NOT NULL,
                        cliente               VARCHAR(150) DEFAULT '',
                        direccion             VARCHAR(255) DEFAULT '',
                        ciudad_estado_cp      VARCHAR(150) DEFAULT '',
                        fabricante_trailer    VARCHAR(100) DEFAULT '',
                        modelo_trailer        VARCHAR(100) DEFAULT '',
                        vin_trailer           VARCHAR(50)  DEFAULT '',
                        numero_flota          VARCHAR(50)  DEFAULT '',
                        distribuidor          VARCHAR(150) DEFAULT '',
                        modelo_unidad         VARCHAR(100) DEFAULT '',
                        numero_serie_unidad   VARCHAR(100) DEFAULT '',
                        numero_serie_motor    VARCHAR(100) DEFAULT '',
                        numero_serie_compresor VARCHAR(100) DEFAULT '',
                        numero_serie_ees      VARCHAR(100) DEFAULT '',
                        numero_serie_generador VARCHAR(100) DEFAULT '',
                        modelo_2do_evap       VARCHAR(100) DEFAULT '',
                        numero_serie_2do_evap VARCHAR(100) DEFAULT '',
                        modelo_3er_evap       VARCHAR(100) DEFAULT '',
                        numero_serie_3er_evap VARCHAR(100) DEFAULT '',
                        tecnico_instalo       VARCHAR(150) DEFAULT '',
                        fecha_instalacion     VARCHAR(50)  DEFAULT '',
                        dealer_firma          VARCHAR(150) DEFAULT '',
                        tecnico_inspecciono   VARCHAR(150) DEFAULT '',
                        comentarios           TEXT,
                        estado                VARCHAR(20)  NOT NULL DEFAULT 'borrador',
                        created_by            VARCHAR(100) DEFAULT '',
                        created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_unit (unit_number),
                        INDEX idx_lote (id_lote)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()

                # ── pdi_datos (EAV: checklist + lecturas + tabla de config) ───────
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pdi_datos (
                        id             INT AUTO_INCREMENT PRIMARY KEY,
                        inspeccion_id  INT NOT NULL,
                        campo_clave    VARCHAR(150) NOT NULL,
                        valor          TEXT,
                        origen         VARCHAR(20) DEFAULT 'manual',
                        UNIQUE KEY uniq_insp_campo (inspeccion_id, campo_clave),
                        INDEX idx_inspeccion (inspeccion_id)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tablas de PDI (lotes_config, pdi_inspecciones, pdi_datos) verificadas")

            # ── system_settings: pares clave/valor de configuración interna ───
            # Uso actual: recordar en qué semana ISO (ej. "2026-W35") se mandó
            # el último reporte semanal automático, para no duplicarlo si
            # Clever Cloud reinicia el proceso el mismo día.
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_settings (
                        clave      VARCHAR(100) PRIMARY KEY,
                        valor      VARCHAR(255) DEFAULT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tabla system_settings verificada")
            except Exception as e_ss:
                print(f"⚠️  Migración (system_settings) omitida: {e_ss}")

            # ── kpis_custom_metricas / kpis_custom_valores ─────────────────────
            # Permite que un admin defina SUS PROPIAS métricas (ej. "Satisfacción
            # de cliente", "Unidades PDI completadas") además de las que ya
            # calculamos automáticamente (tickets, asistencia). El valor se
            # captura a mano por técnico y por periodo (ej. "2026-08").
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS kpis_custom_metricas (
                        id            INT AUTO_INCREMENT PRIMARY KEY,
                        nombre        VARCHAR(120) NOT NULL,
                        unidad        VARCHAR(30)  DEFAULT '',
                        descripcion   VARCHAR(255) DEFAULT '',
                        activo        TINYINT(1)   NOT NULL DEFAULT 1,
                        creado_por    VARCHAR(80)  DEFAULT NULL,
                        created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS kpis_custom_valores (
                        id            INT AUTO_INCREMENT PRIMARY KEY,
                        metrica_id    INT NOT NULL,
                        tecnico       VARCHAR(80) NOT NULL,
                        periodo       VARCHAR(20) NOT NULL,
                        valor         DECIMAL(12,2) DEFAULT NULL,
                        registrado_por VARCHAR(80) DEFAULT NULL,
                        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY uniq_metrica_tecnico_periodo (metrica_id, tecnico, periodo),
                        INDEX idx_periodo (periodo),
                        CONSTRAINT fk_kpicustom_metrica FOREIGN KEY (metrica_id)
                            REFERENCES kpis_custom_metricas(id) ON DELETE CASCADE
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tablas kpis_custom_metricas / kpis_custom_valores verificadas")
            except Exception as e_kpi:
                print(f"⚠️  Migración (kpis_custom) omitida: {e_kpi}")

            # ── actividades_catalogo: tiempo estimado por tipo de actividad ────
            # Antes ACTIVIDADES_CARRIER era una lista fija en Python (sin tiempo
            # objetivo). Se vuelve tabla para que el admin le ponga a cada
            # actividad cuánto debería tardar en completarse — insumo para
            # medir SLA en los KPIs por técnico.
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS actividades_catalogo (
                        id                    INT AUTO_INCREMENT PRIMARY KEY,
                        nombre                VARCHAR(80) NOT NULL UNIQUE,
                        tiempo_estimado_horas DECIMAL(6,2) DEFAULT NULL,
                        activo                TINYINT(1) NOT NULL DEFAULT 1,
                        created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                actividades_default = [
                    "Cableado", "Programación", "Soldadura", "Check de fugas",
                    "Vacío", "Cerrado", "Pre-viaje", "Horas Corridas",
                    "Standby", "GPS", "Corriendo", "Inspección",
                    "Accesorios", "Toma de Valores", "Evidencia", "Toma de Series",
                    "Extra Eléctrico", "Extra Soldador",
                ]
                for nombre in actividades_default:
                    cur.execute(
                        "INSERT IGNORE INTO actividades_catalogo (nombre) VALUES (%s)", (nombre,)
                    )
                conn.commit()
                print("✅ Migración: tabla actividades_catalogo verificada/poblada")
            except Exception as e_act:
                print(f"⚠️  Migración (actividades_catalogo) omitida: {e_act}")

            # ── asignaciones.tiempo_estimado_horas ──────────────────────────────
            # Snapshot del tiempo objetivo (tomado de actividades_catalogo al
            # momento de crear la asignación) — se guarda copiado, no como
            # referencia viva, para que si luego cambias el objetivo de una
            # actividad no se reescriba retroactivamente el SLA de asignaciones
            # que ya estaban en curso o cerradas.
            try:
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'asignaciones'
                      AND COLUMN_NAME  = 'tiempo_estimado_horas'
                """)
                row = cur.fetchone()
                count = row[0] if isinstance(row, tuple) else list(row.values())[0]
                if count == 0:
                    cur.execute(
                        "ALTER TABLE asignaciones ADD COLUMN tiempo_estimado_horas DECIMAL(6,2) DEFAULT NULL"
                    )
                    conn.commit()
                    print("✅ Migración: columna tiempo_estimado_horas añadida a asignaciones")
            except Exception as e_te:
                print(f"⚠️  Migración (asignaciones.tiempo_estimado_horas) omitida: {e_te}")

            # ── kpis_custom_metricas: ponderación (motor de KPI final 0-100) ───
            # Agrega lo necesario para convertir cada métrica (automática o
            # manual) en una nota de 0-100 y ponderarla:
            #   tipo_evaluacion:
            #     - 'automatica_tiempo_sla'  → tiempo real vs. tiempo_estimado_horas
            #       de asignaciones (calculado en vivo, sin valor guardado)
            #     - 'automatica_reporte'     → % tickets cerrados con reporte
            #     - 'automatica_asistencia'  → 100 - % de tardanza
            #     - 'manual_directo'         → el valor capturado YA es 0-100
            #     - 'manual_rango'           → (valor-min)/(max-min)*100, más=mejor
            #     - 'manual_rango_invertido' → igual pero menos=mejor
            #   valor_min / valor_max solo aplican a los tipos 'manual_rango*'
            #   peso: % que aporta esta métrica al KPI final (deben sumar 100
            #   entre las métricas activas — se valida en el endpoint, no aquí)
            try:
                columnas_nuevas = [
                    ("tipo_evaluacion", "VARCHAR(30) NOT NULL DEFAULT 'manual_directo'"),
                    ("valor_min",       "DECIMAL(10,2) DEFAULT 0"),
                    ("valor_max",       "DECIMAL(10,2) DEFAULT 100"),
                    ("peso",            "DECIMAL(5,2) NOT NULL DEFAULT 0"),
                    ("es_automatica",   "TINYINT(1) NOT NULL DEFAULT 0"),
                    ("clave_automatica","VARCHAR(30) DEFAULT NULL"),
                ]
                for col, ddl in columnas_nuevas:
                    cur.execute("""
                        SELECT COUNT(*) FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME   = 'kpis_custom_metricas'
                          AND COLUMN_NAME  = %s
                    """, (col,))
                    row = cur.fetchone()
                    count = row[0] if isinstance(row, tuple) else list(row.values())[0]
                    if count == 0:
                        cur.execute(f"ALTER TABLE kpis_custom_metricas ADD COLUMN {col} {ddl}")
                        conn.commit()
                        print(f"✅ Migración: columna {col} añadida a kpis_custom_metricas")

                # Siembra las 3 métricas automáticas una sola vez (peso=0 por
                # defecto — no afectan nada hasta que un admin les asigne peso).
                metricas_automaticas = [
                    ("Tiempo de resolución (SLA)", "hrs", "automatica_tiempo_sla",
                     "Compara el tiempo real de cada actividad completada contra su tiempo estimado."),
                    ("Tickets con reporte adjunto", "%", "automatica_reporte",
                     "% de tickets cerrados que traen reporte adjunto."),
                    ("Puntualidad / asistencia", "%", "automatica_asistencia",
                     "100 menos el % de check-ins con tardanza."),
                ]
                for nombre, unidad, clave, descripcion in metricas_automaticas:
                    cur.execute(
                        "SELECT id FROM kpis_custom_metricas WHERE clave_automatica = %s", (clave,)
                    )
                    if not cur.fetchone():
                        cur.execute(
                            "INSERT INTO kpis_custom_metricas "
                            "(nombre, unidad, descripcion, tipo_evaluacion, peso, es_automatica, clave_automatica) "
                            "VALUES (%s, %s, %s, %s, 0, 1, %s)",
                            (nombre, unidad, descripcion, clave, clave)
                        )
                conn.commit()
                print("✅ Migración: columnas de ponderación + métricas automáticas verificadas")
            except Exception as e_pond:
                print(f"⚠️  Migración (ponderación kpis_custom_metricas) omitida: {e_pond}")

            # ── tickets: archivo de reporte (Word/PDF) subido por el técnico ──
            # Bloque aislado en su propio try/except (ver nota arriba) para que
            # un fallo aquí no tumbe migraciones futuras.
            try:
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'tickets'
                      AND COLUMN_NAME  = 'reporte_archivo_url'
                """)
                row_tra = cur.fetchone()
                count_tra = row_tra[0] if isinstance(row_tra, tuple) else list(row_tra.values())[0]
                if count_tra == 0:
                    cur.execute(
                        "ALTER TABLE tickets "
                        "ADD COLUMN reporte_archivo_nombre VARCHAR(255) DEFAULT NULL, "
                        "ADD COLUMN reporte_archivo_url VARCHAR(500) DEFAULT NULL, "
                        "ADD COLUMN reporte_archivo_item_id VARCHAR(150) DEFAULT NULL"
                    )
                    conn.commit()
                    print("✅ Migración: columnas de archivo de reporte añadidas a tickets")
            except Exception as e_tra:
                print(f"⚠️  Migración (tickets.reporte_archivo_*) omitida: {e_tra}")

            # ── reportes_unidad / reportes_lote_envios: bitácora de trabajo/  ──
            # ── problemas por unidad que los líderes capturan agrupada por    ──
            # ── lote, y que se envía como reporte al administrador.          ──
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reportes_unidad (
                        id              INT AUTO_INCREMENT PRIMARY KEY,
                        id_lote         VARCHAR(50)  NOT NULL,
                        unit_number     VARCHAR(50)  NOT NULL,
                        username_lider  VARCHAR(80)  NOT NULL,
                        tipo            ENUM('trabajo','problema') NOT NULL DEFAULT 'trabajo',
                        detalle         TEXT NOT NULL,
                        fecha           DATE NOT NULL,
                        enviado         TINYINT(1) NOT NULL DEFAULT 0,
                        envio_id        INT DEFAULT NULL,
                        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_lote_fecha (id_lote, fecha),
                        INDEX idx_envio (envio_id)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reportes_lote_envios (
                        id              INT AUTO_INCREMENT PRIMARY KEY,
                        id_lote         VARCHAR(50)  NOT NULL,
                        username_lider  VARCHAR(80)  NOT NULL,
                        fecha           DATE NOT NULL,
                        total_unidades  INT NOT NULL DEFAULT 0,
                        total_problemas INT NOT NULL DEFAULT 0,
                        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_fecha (fecha)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                conn.commit()
                print("✅ Migración: tablas reportes_unidad / reportes_lote_envios verificadas")
            except Exception as e_ru:
                print(f"⚠️  Migración (reportes_unidad) omitida: {e_ru}")

    except Exception as e:
        print(f"⚠️  Migración omitida: {e}")
    finally:
        conn.close()


def init_db():
    global pool
    if pool is not None:
        return
    
    pool = PooledDB(
        creator=pymysql,
        maxconnections=15,
        mincached=2,
        maxcached=5,
        blocking=True,
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4',
        # ssl={"ca": "/etc/ssl/certs/ca-certificates.crt"}  # Descomenta si CleverCloud requiere SSL
    )
    print("✅ Pool de conexiones DB inicializado correctamente")

    # ── Migraciones automáticas (idempotentes) ────────────────────────────────
    _run_migrations()


def execute_read(sql: str, params=None):
    """Ejecuta consultas SELECT"""
    conn = pool.connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute_write(sql: str, params=None):
    """Ejecuta INSERT, UPDATE, DELETE"""
    conn = pool.connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params or ())
            conn.commit()
            return affected
    finally:
        conn.close()


def execute_write_with_id(sql: str, params=None):
    """Ejecuta INSERT y devuelve el lastrowid del registro creado."""
    conn = pool.connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def get_db_connection():
    """
    Devuelve una conexión directa del pool.
    El llamador es responsable de llamar connection.close() en un bloque finally.
    Usado por asistencia/routes.py y reporte_router.py que manejan
    el cursor y commit manualmente.
    """
    if pool is None:
        print("❌ get_db_connection: el pool no está inicializado")
        return None
    try:
        return pool.connection()
    except Exception as e:
        print(f"❌ Error obteniendo conexión del pool: {e}")
        return None
