#!/usr/bin/env python3
"""
VMotors - Generador de la base de datos PostgreSQL
===================================================

Script independiente que:

  1. Crea la estructura relacional completa (tablas, llaves, restricciones,
     indices y vistas) descrita en las fases III y IV del proyecto.
  2. Genera datos ficticios realistas con Faker (locale es_MX).
  3. Inserta los registros respetando el orden de dependencias y todas las
     restricciones de integridad.
  4. Puede volver a ejecutarse de forma controlada mediante --reset.

No forma parte del prototipo web: la interfaz de `frontend/` es estatica y no
se conecta a esta base de datos. Este script prepara el esquema para que mas
adelante un backend pueda consumirlo.

Uso rapido
----------
    cp .env.example .env          # y editar las credenciales
    pip install -r requirements.txt
    python seed_database.py --reset --yes

Consulte el README.md de esta carpeta para el detalle de las opciones.
"""

from __future__ import annotations

import argparse
import os
import sys
import random
from datetime import date
from getpass import getpass

try:
    import psycopg
    from psycopg import sql
except ImportError:  # pragma: no cover
    sys.exit("Falta la dependencia 'psycopg'. Ejecute: pip install -r requirements.txt")

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):
        return False

try:
    from faker import Faker
except ImportError:  # pragma: no cover
    sys.exit("Falta la dependencia 'Faker'. Ejecute: pip install -r requirements.txt")

from generador import (
    ETAPAS,
    ESTATUS_CITA,
    FORMAS_PAGO,
    TRANSMISIONES,
    REFACCIONES,
    Generador,
)


# ===========================================================================
# 1. Configuracion
# ===========================================================================

APP_NAME = "VMotors"
DEFAULT_SCHEMA = "vmotors"


# ===========================================================================
# 2. DDL - estructura de la base de datos
# ===========================================================================

def construir_ddl(schema: str) -> str:
    """Devuelve el guion completo de creacion de estructuras."""
    etapas = ", ".join(f"'{e}'" for e in ETAPAS)
    estatus_cita = ", ".join(f"'{e}'" for e in ESTATUS_CITA)
    pagos = ", ".join(f"'{p}'" for p in FORMAS_PAGO)
    trans = ", ".join(f"'{t}'" for t in TRANSMISIONES)

    return f"""
-- ==========================================================================
-- {APP_NAME} · Estructura relacional (Tercera Forma Normal)
-- Generada por seed_database.py
-- ==========================================================================

CREATE SCHEMA IF NOT EXISTS {schema};
SET search_path TO {schema}, public;

-- --------------------------------------------------------------------------
-- Tabla 1: CLIENTES · propietarios de las unidades
-- --------------------------------------------------------------------------
CREATE TABLE clientes (
    id_cliente          SERIAL        PRIMARY KEY,
    nombre              VARCHAR(60)   NOT NULL,
    apellido            VARCHAR(60)   NOT NULL,
    razon_social        VARCHAR(120),
    rfc                 VARCHAR(13),
    telefono            VARCHAR(15)   NOT NULL,
    telefono_oficina    VARCHAR(15),
    correo              VARCHAR(100),
    acepta_promociones  BOOLEAN       NOT NULL DEFAULT FALSE,
    calle               VARCHAR(120),
    numero              VARCHAR(10),
    colonia             VARCHAR(100),
    municipio           VARCHAR(100),
    estado              VARCHAR(60),
    codigo_postal       CHAR(5),
    fecha_registro      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_clientes_nombre   CHECK (char_length(btrim(nombre))   >= 2),
    CONSTRAINT ck_clientes_apellido CHECK (char_length(btrim(apellido)) >= 2),
    CONSTRAINT ck_clientes_telefono CHECK (telefono ~ '^[0-9]{{10,15}}$'),
    CONSTRAINT ck_clientes_tel_ofi  CHECK (telefono_oficina IS NULL
                                           OR telefono_oficina ~ '^[0-9]{{10,15}}$'),
    CONSTRAINT ck_clientes_correo   CHECK (correo IS NULL
                                           OR correo ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+[.][A-Z]{{2,}}$'),
    CONSTRAINT ck_clientes_cp       CHECK (codigo_postal IS NULL OR codigo_postal ~ '^[0-9]{{5}}$'),
    CONSTRAINT ck_clientes_rfc      CHECK (rfc IS NULL OR rfc ~ '^[A-ZÑ&]{{3,4}}[0-9]{{6}}[A-Z0-9]{{3}}$')
);

CREATE UNIQUE INDEX ux_clientes_rfc      ON clientes (rfc)            WHERE rfc    IS NOT NULL;
CREATE UNIQUE INDEX ux_clientes_correo   ON clientes (lower(correo))  WHERE correo IS NOT NULL;
CREATE        INDEX ix_clientes_telefono ON clientes (telefono);
CREATE        INDEX ix_clientes_apellido ON clientes (lower(apellido), lower(nombre));

COMMENT ON TABLE  clientes                    IS 'Expediente único por propietario; base del padrón del taller.';
COMMENT ON COLUMN clientes.acepta_promociones IS 'Autorización para enviar recordatorios de mantenimiento por correo.';

-- --------------------------------------------------------------------------
-- Tabla 2: VEHICULOS · parque vehicular atendido (1 cliente : N vehículos)
-- --------------------------------------------------------------------------
CREATE TABLE vehiculos (
    id_vehiculo     SERIAL       PRIMARY KEY,
    id_cliente      INTEGER      NOT NULL,
    placas          VARCHAR(10)  NOT NULL,
    marca           VARCHAR(50)  NOT NULL,
    modelo          VARCHAR(50)  NOT NULL,
    anio            SMALLINT     NOT NULL,
    color           VARCHAR(30),
    transmision     VARCHAR(12)  NOT NULL DEFAULT 'Manual',
    motor           VARCHAR(40),
    fecha_registro  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_vehiculos_cliente FOREIGN KEY (id_cliente)
        REFERENCES clientes (id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ux_vehiculos_placas   UNIQUE (placas),
    CONSTRAINT ck_vehiculos_placas   CHECK (placas = upper(placas) AND placas ~ '^[A-Z0-9-]{{5,10}}$'),
    -- El limite superior es una constante porque PostgreSQL no admite
    -- funciones volatiles (CURRENT_DATE) dentro de un CHECK.
    CONSTRAINT ck_vehiculos_anio     CHECK (anio BETWEEN 1980 AND 2100),
    CONSTRAINT ck_vehiculos_trans    CHECK (transmision IN ({trans}))
);

CREATE INDEX ix_vehiculos_cliente ON vehiculos (id_cliente);
CREATE INDEX ix_vehiculos_marca   ON vehiculos (marca, modelo);

COMMENT ON TABLE  vehiculos        IS 'Padrón de unidades; la matrícula es la llave natural del historial mecánico.';
COMMENT ON COLUMN vehiculos.placas IS 'Matrícula en mayúsculas, única en todo el sistema.';

-- --------------------------------------------------------------------------
-- Tabla 3: CITAS · agenda del taller (1 vehículo : N citas)
-- --------------------------------------------------------------------------
CREATE TABLE citas (
    id_cita         SERIAL       PRIMARY KEY,
    id_vehiculo     INTEGER      NOT NULL,
    fecha           DATE         NOT NULL,
    hora_inicio     TIME         NOT NULL,
    hora_fin        TIME         NOT NULL,
    motivo_ingreso  TEXT         NOT NULL,
    estatus_cita    VARCHAR(20)  NOT NULL DEFAULT 'Agendada',
    fecha_registro  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_citas_vehiculo FOREIGN KEY (id_vehiculo)
        REFERENCES vehiculos (id_vehiculo) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_citas_horas    CHECK (hora_fin > hora_inicio),
    CONSTRAINT ck_citas_jornada  CHECK (hora_inicio >= TIME '08:00' AND hora_fin <= TIME '19:00'),
    CONSTRAINT ck_citas_motivo   CHECK (char_length(btrim(motivo_ingreso)) > 0),
    CONSTRAINT ck_citas_estatus  CHECK (estatus_cita IN ({estatus_cita}))
);

-- Regla del Proceso 2.0: no puede existir mas de una cita ACTIVA en el mismo
-- par (fecha, hora_inicio). Las citas canceladas quedan fuera del indice.
CREATE UNIQUE INDEX ux_citas_bloque_activo
    ON citas (fecha, hora_inicio)
    WHERE estatus_cita <> 'Cancelada';

CREATE INDEX ix_citas_fecha    ON citas (fecha, hora_inicio);
CREATE INDEX ix_citas_vehiculo ON citas (id_vehiculo);

COMMENT ON TABLE citas IS 'Calendario de reservaciones; evita el empalme de bloques horarios.';

-- --------------------------------------------------------------------------
-- Tabla 4: REFACCIONES · catálogo de piezas
-- --------------------------------------------------------------------------
CREATE TABLE refacciones (
    id_refaccion     SERIAL        PRIMARY KEY,
    clave            VARCHAR(20)   NOT NULL UNIQUE,
    descripcion      VARCHAR(120)  NOT NULL,
    categoria        VARCHAR(40)   NOT NULL,
    precio_unitario  NUMERIC(10,2) NOT NULL,

    CONSTRAINT ck_refacciones_precio CHECK (precio_unitario >= 0)
);

CREATE INDEX ix_refacciones_categoria ON refacciones (categoria);

COMMENT ON TABLE refacciones IS 'Catálogo de piezas con precio de lista.';

-- --------------------------------------------------------------------------
-- Tabla 5: ORDENES_SERVICIO · bitácora técnica (1 cita : 1 orden)
-- --------------------------------------------------------------------------
CREATE TABLE ordenes_servicio (
    id_orden           SERIAL        PRIMARY KEY,
    id_cita            INTEGER       NOT NULL,
    folio              VARCHAR(15)   NOT NULL,
    fecha_ingreso      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hora_prometida     TIMESTAMP,
    fecha_entrega      TIMESTAMP,
    kilometraje        INTEGER,
    nivel_combustible  SMALLINT,
    forma_pago         VARCHAR(20),
    diagnostico        TEXT,
    estatus            VARCHAR(25)   NOT NULL DEFAULT 'Pendiente',
    costo_mano_obra    NUMERIC(10,2) NOT NULL DEFAULT 0,
    costo_refacciones  NUMERIC(10,2) NOT NULL DEFAULT 0,
    costo_total        NUMERIC(10,2) NOT NULL DEFAULT 0,

    CONSTRAINT fk_ordenes_cita FOREIGN KEY (id_cita)
        REFERENCES citas (id_cita) ON UPDATE CASCADE ON DELETE CASCADE,
    -- Cardinalidad 1:1 entre cita y orden de servicio
    CONSTRAINT ux_ordenes_cita   UNIQUE (id_cita),
    CONSTRAINT ux_ordenes_folio  UNIQUE (folio),

    CONSTRAINT ck_ordenes_estatus CHECK (estatus IN ({etapas})),
    CONSTRAINT ck_ordenes_pago    CHECK (forma_pago IS NULL OR forma_pago IN ({pagos})),
    CONSTRAINT ck_ordenes_km      CHECK (kilometraje IS NULL OR kilometraje >= 0),
    CONSTRAINT ck_ordenes_comb    CHECK (nivel_combustible IS NULL
                                         OR nivel_combustible BETWEEN 0 AND 8),
    CONSTRAINT ck_ordenes_costos  CHECK (costo_mano_obra   >= 0
                                         AND costo_refacciones >= 0
                                         AND costo_total       >= 0),
    CONSTRAINT ck_ordenes_suma    CHECK (costo_total = costo_mano_obra + costo_refacciones),
    CONSTRAINT ck_ordenes_fechas  CHECK (fecha_entrega IS NULL OR fecha_entrega >= fecha_ingreso),
    -- Regla del formulario E-02: no se entrega sin costo capturado ni fecha de salida
    CONSTRAINT ck_ordenes_cierre  CHECK (estatus <> 'Entregado'
                                         OR (fecha_entrega IS NOT NULL AND costo_total > 0))
);

CREATE INDEX ix_ordenes_estatus ON ordenes_servicio (estatus);
CREATE INDEX ix_ordenes_ingreso ON ordenes_servicio (fecha_ingreso DESC);
CREATE INDEX ix_ordenes_entrega ON ordenes_servicio (fecha_entrega DESC) WHERE fecha_entrega IS NOT NULL;

COMMENT ON TABLE  ordenes_servicio         IS 'Ciclo de vida técnico del vehículo dentro del taller.';
COMMENT ON COLUMN ordenes_servicio.estatus IS 'Etapa del flujo: Pendiente → Recibido → En diagnóstico → En reparación → Terminado → Entregado.';

-- --------------------------------------------------------------------------
-- Tabla 6: ORDEN_REFACCIONES · desglose de piezas por orden (N:M resuelta)
-- --------------------------------------------------------------------------
CREATE TABLE orden_refacciones (
    id_detalle       SERIAL         PRIMARY KEY,
    id_orden         INTEGER        NOT NULL,
    id_refaccion     INTEGER        NOT NULL,
    cantidad         SMALLINT       NOT NULL,
    precio_unitario  NUMERIC(10,2)  NOT NULL,
    importe          NUMERIC(12,2)  GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,

    CONSTRAINT fk_detalle_orden FOREIGN KEY (id_orden)
        REFERENCES ordenes_servicio (id_orden) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_detalle_refaccion FOREIGN KEY (id_refaccion)
        REFERENCES refacciones (id_refaccion) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ux_detalle_orden_refaccion UNIQUE (id_orden, id_refaccion),
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_precio   CHECK (precio_unitario >= 0)
);

CREATE INDEX ix_detalle_orden ON orden_refacciones (id_orden);

COMMENT ON TABLE  orden_refacciones         IS 'Piezas instaladas en cada orden; alimenta el comprobante F-02.';
COMMENT ON COLUMN orden_refacciones.importe IS 'Columna calculada: cantidad × precio_unitario.';

-- --------------------------------------------------------------------------
-- Tabla 7: HISTORIAL_ESTATUS · trazabilidad de la máquina de estados
-- --------------------------------------------------------------------------
CREATE TABLE historial_estatus (
    id_historial      SERIAL       PRIMARY KEY,
    id_orden          INTEGER      NOT NULL,
    estatus_anterior  VARCHAR(25),
    estatus_nuevo     VARCHAR(25)  NOT NULL,
    fecha_cambio      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario           VARCHAR(60)  NOT NULL DEFAULT 'administrador',
    nota              TEXT,

    CONSTRAINT fk_historial_orden FOREIGN KEY (id_orden)
        REFERENCES ordenes_servicio (id_orden) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT ck_historial_nuevo    CHECK (estatus_nuevo    IN ({etapas})),
    CONSTRAINT ck_historial_anterior CHECK (estatus_anterior IS NULL
                                            OR estatus_anterior IN ({etapas}))
);

CREATE INDEX ix_historial_orden ON historial_estatus (id_orden, fecha_cambio);

COMMENT ON TABLE historial_estatus IS 'Bitácora de transiciones de estatus por orden de servicio.';

-- ==========================================================================
-- Vistas de consulta (salidas del sistema)
-- ==========================================================================

-- Cruce Cliente + Vehículo + Cita + Orden usado por el tablero y las órdenes.
CREATE VIEW v_ordenes_detalle AS
SELECT o.id_orden,
       o.folio,
       o.estatus,
       o.fecha_ingreso,
       o.hora_prometida,
       o.fecha_entrega,
       o.kilometraje,
       o.costo_mano_obra,
       o.costo_refacciones,
       o.costo_total,
       o.diagnostico,
       c.id_cita,
       c.fecha        AS fecha_cita,
       c.hora_inicio,
       c.hora_fin,
       c.motivo_ingreso,
       v.id_vehiculo,
       v.placas,
       v.marca,
       v.modelo,
       v.anio,
       v.color,
       v.transmision,
       cl.id_cliente,
       cl.nombre || ' ' || cl.apellido AS cliente,
       cl.telefono,
       cl.correo
  FROM ordenes_servicio o
  JOIN citas     c  ON c.id_cita     = o.id_cita
  JOIN vehiculos v  ON v.id_vehiculo = c.id_vehiculo
  JOIN clientes  cl ON cl.id_cliente = v.id_cliente;

-- Unidades que físicamente están en el taller (monitor Kanban).
CREATE VIEW v_vehiculos_en_taller AS
SELECT *
  FROM v_ordenes_detalle
 WHERE estatus IN ('Recibido', 'En diagnóstico', 'En reparación', 'Terminado');

-- Agenda del día con el estatus operativo de cada bloque.
CREATE VIEW v_agenda AS
SELECT c.id_cita,
       c.fecha,
       c.hora_inicio,
       c.hora_fin,
       c.motivo_ingreso,
       c.estatus_cita,
       v.placas,
       v.marca || ' ' || v.modelo      AS unidad,
       cl.nombre || ' ' || cl.apellido AS cliente,
       cl.telefono,
       o.folio,
       o.estatus                       AS estatus_orden
  FROM citas c
  JOIN vehiculos v  ON v.id_vehiculo = c.id_vehiculo
  JOIN clientes  cl ON cl.id_cliente = v.id_cliente
  LEFT JOIN ordenes_servicio o ON o.id_cita = c.id_cita;

-- Motor de alertas: unidades con seis meses o más desde su última entrega.
CREATE VIEW v_alertas_mantenimiento AS
SELECT v.id_vehiculo,
       v.placas,
       v.marca,
       v.modelo,
       v.anio,
       cl.id_cliente,
       cl.nombre || ' ' || cl.apellido AS cliente,
       cl.telefono,
       cl.correo,
       cl.acepta_promociones,
       MAX(o.fecha_entrega)                                           AS ultima_visita,
       ROUND(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(o.fecha_entrega)))
             / 2629800.0, 1)                                          AS meses_sin_visita
  FROM vehiculos v
  JOIN clientes  cl ON cl.id_cliente = v.id_cliente
  JOIN citas     c  ON c.id_vehiculo = v.id_vehiculo
  JOIN ordenes_servicio o ON o.id_cita = c.id_cita
 WHERE o.fecha_entrega IS NOT NULL
 GROUP BY v.id_vehiculo, v.placas, v.marca, v.modelo, v.anio,
          cl.id_cliente, cl.nombre, cl.apellido, cl.telefono, cl.correo, cl.acepta_promociones
HAVING MAX(o.fecha_entrega) < CURRENT_TIMESTAMP - INTERVAL '6 months';

-- Historial acumulado por matrícula (reporte "historial clínico").
CREATE VIEW v_historial_por_placa AS
SELECT v.placas,
       o.folio,
       c.fecha        AS fecha_cita,
       o.fecha_entrega,
       o.kilometraje,
       c.motivo_ingreso,
       o.diagnostico,
       o.costo_total
  FROM vehiculos v
  JOIN citas c            ON c.id_vehiculo = v.id_vehiculo
  JOIN ordenes_servicio o ON o.id_cita     = c.id_cita
 ORDER BY v.placas, c.fecha DESC;
"""


DROP_SQL_TABLAS = """
DROP VIEW IF EXISTS v_historial_por_placa   CASCADE;
DROP VIEW IF EXISTS v_alertas_mantenimiento CASCADE;
DROP VIEW IF EXISTS v_agenda                CASCADE;
DROP VIEW IF EXISTS v_vehiculos_en_taller   CASCADE;
DROP VIEW IF EXISTS v_ordenes_detalle       CASCADE;
DROP TABLE IF EXISTS historial_estatus  CASCADE;
DROP TABLE IF EXISTS orden_refacciones  CASCADE;
DROP TABLE IF EXISTS ordenes_servicio   CASCADE;
DROP TABLE IF EXISTS refacciones        CASCADE;
DROP TABLE IF EXISTS citas              CASCADE;
DROP TABLE IF EXISTS vehiculos          CASCADE;
DROP TABLE IF EXISTS clientes           CASCADE;
"""


# ===========================================================================
# 4. Acceso a PostgreSQL
# ===========================================================================

def cadena_conexion() -> str:
    """Arma la cadena de conexion a partir de variables de entorno."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    base = os.getenv("PGDATABASE", "vmotors")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD")

    if not password:
        if sys.stdin.isatty():
            password = getpass(f"Contraseña de PostgreSQL para {user}@{host}: ")
        else:
            sys.exit(
                "No se encontró la contraseña. Defina PGPASSWORD o DATABASE_URL "
                "en el archivo .env o en el entorno."
            )
    return f"host={host} port={port} dbname={base} user={user} password={password}"


def hay_estructura(cur, schema: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = %s AND table_type = 'BASE TABLE'",
        (schema,),
    )
    return cur.fetchone()[0] > 0


def crear_estructura(cur, schema: str, reset: bool) -> None:
    if reset:
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
        cur.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema)))
        cur.execute(DROP_SQL_TABLAS)
    cur.execute(construir_ddl(schema))


def insertar_datos(cur, gen: Generador) -> None:
    cur.executemany(
        """INSERT INTO refacciones (id_refaccion, clave, descripcion, categoria, precio_unitario)
           VALUES (%s, %s, %s, %s, %s)""",
        [(i, *r) for i, r in enumerate(REFACCIONES, start=1)],
    )

    cur.executemany(
        """INSERT INTO clientes
             (id_cliente, nombre, apellido, razon_social, rfc, telefono, telefono_oficina,
              correo, acepta_promociones, calle, numero, colonia, municipio, estado,
              codigo_postal, fecha_registro)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        gen.clientes,
    )

    cur.executemany(
        """INSERT INTO vehiculos
             (id_vehiculo, id_cliente, placas, marca, modelo, anio, color,
              transmision, motor, fecha_registro)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        gen.vehiculos,
    )

    cur.executemany(
        """INSERT INTO citas
             (id_cita, id_vehiculo, fecha, hora_inicio, hora_fin, motivo_ingreso,
              estatus_cita, fecha_registro)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        gen.citas,
    )

    cur.executemany(
        """INSERT INTO ordenes_servicio
             (id_orden, id_cita, folio, fecha_ingreso, hora_prometida, fecha_entrega,
              kilometraje, nivel_combustible, forma_pago, diagnostico, estatus,
              costo_mano_obra, costo_refacciones, costo_total)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        gen.ordenes,
    )

    cur.executemany(
        """INSERT INTO orden_refacciones
             (id_detalle, id_orden, id_refaccion, cantidad, precio_unitario)
           VALUES (%s, %s, %s, %s, %s)""",
        gen.detalle,
    )

    cur.executemany(
        """INSERT INTO historial_estatus
             (id_orden, estatus_anterior, estatus_nuevo, fecha_cambio, usuario, nota)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        gen.historial,
    )

    # Los identificadores se insertaron de forma explícita: hay que reposicionar
    # las secuencias para que las altas posteriores no choquen con las llaves.
    for tabla, columna in [
        ("clientes", "id_cliente"), ("vehiculos", "id_vehiculo"),
        ("citas", "id_cita"), ("refacciones", "id_refaccion"),
        ("ordenes_servicio", "id_orden"), ("orden_refacciones", "id_detalle"),
        ("historial_estatus", "id_historial"),
    ]:
        cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{tabla}', '{columna}'), "
            f"COALESCE((SELECT MAX({columna}) FROM {tabla}), 0) + 1, false)"
        )


def resumen(cur, schema: str) -> None:
    print("\n" + "=" * 62)
    print(f"  Base de datos {APP_NAME} lista · esquema '{schema}'")
    print("=" * 62)
    for tabla in ["clientes", "vehiculos", "citas", "refacciones",
                  "ordenes_servicio", "orden_refacciones", "historial_estatus"]:
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        print(f"  {tabla:<20} {cur.fetchone()[0]:>7} registros")

    print("-" * 62)
    cur.execute("SELECT estatus, COUNT(*) FROM ordenes_servicio GROUP BY estatus ORDER BY 1")
    for estatus, total in cur.fetchall():
        print(f"  órdenes · {estatus:<18} {total:>7}")

    print("-" * 62)
    cur.execute("SELECT COALESCE(SUM(costo_total), 0) FROM ordenes_servicio WHERE estatus = 'Entregado'")
    print(f"  facturación acumulada        ${cur.fetchone()[0]:,.2f}")
    cur.execute("SELECT COUNT(*) FROM v_vehiculos_en_taller")
    print(f"  unidades actualmente en piso  {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM v_alertas_mantenimiento")
    print(f"  alertas de mantenimiento      {cur.fetchone()[0]}")
    print("=" * 62 + "\n")


# ===========================================================================
# 5. Punto de entrada
# ===========================================================================

def parsear_argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=f"Crea y puebla la base de datos PostgreSQL de {APP_NAME}.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python seed_database.py --reset --yes\n"
            "  python seed_database.py --reset --clientes 200 --seed 7\n"
            "  python seed_database.py --dump-schema > schema.sql\n"
        ),
    )
    p.add_argument("--clientes", type=int, default=60,
                   help="cantidad de clientes a generar (por omisión 60)")
    p.add_argument("--seed", type=int, default=2026,
                   help="semilla aleatoria para obtener resultados reproducibles")
    p.add_argument("--schema", default=os.getenv("VMOTORS_SCHEMA", DEFAULT_SCHEMA),
                   help=f"esquema de PostgreSQL a utilizar (por omisión '{DEFAULT_SCHEMA}')")
    p.add_argument("--reset", action="store_true",
                   help="elimina y vuelve a crear las tablas antes de insertar")
    p.add_argument("--yes", "-y", action="store_true",
                   help="no pedir confirmación al usar --reset")
    p.add_argument("--schema-only", action="store_true",
                   help="crear únicamente la estructura, sin datos de prueba")
    p.add_argument("--dump-schema", action="store_true",
                   help="imprimir el DDL en pantalla y salir (no se conecta a la base)")
    return p.parse_args()


def main() -> int:
    args = parsear_argumentos()
    load_dotenv()

    if args.dump_schema:
        print(construir_ddl(args.schema))
        return 0

    if args.clientes < 1:
        sys.exit("--clientes debe ser un número mayor o igual a 1.")

    conninfo = cadena_conexion()

    try:
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), version()")
                base, version = cur.fetchone()
                print(f"Conectado a '{base}' · {version.split(',')[0]}")

                existe = hay_estructura(cur, args.schema)
                if existe and not args.reset:
                    sys.exit(
                        f"\nEl esquema '{args.schema}' ya contiene tablas.\n"
                        "Vuelva a ejecutar con --reset para eliminarlas y recrearlas."
                    )
                if existe and args.reset and not args.yes:
                    if not sys.stdin.isatty():
                        sys.exit("Se requiere --yes para ejecutar --reset de forma no interactiva.")
                    print(f"\nSe eliminarán TODAS las tablas del esquema '{args.schema}'.")
                    if input("Escriba 'si' para continuar: ").strip().lower() not in ("si", "sí"):
                        print("Operación cancelada.")
                        return 1

                print(f"Creando estructura en el esquema '{args.schema}'...")
                crear_estructura(cur, args.schema, reset=args.reset or not existe)

                if args.schema_only:
                    conn.commit()
                    print("Estructura creada. No se insertaron datos (--schema-only).")
                    return 0

                print(f"Generando datos ficticios (semilla {args.seed})...")
                fake = Faker("es_MX")
                Faker.seed(args.seed)
                rnd = random.Random(args.seed)

                gen = Generador(fake, rnd, date.today())
                gen.generar_clientes(args.clientes)
                gen.generar_vehiculos()
                gen.generar_citas_y_ordenes()

                print("Insertando registros...")
                cur.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(args.schema)))
                insertar_datos(cur, gen)
                conn.commit()

                resumen(cur, args.schema)

    except psycopg.OperationalError as exc:
        sys.exit(f"\nNo fue posible conectar con PostgreSQL:\n  {exc}")
    except psycopg.Error as exc:
        sys.exit(f"\nError de base de datos:\n  {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
