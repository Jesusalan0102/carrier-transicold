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
