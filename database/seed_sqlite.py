#!/usr/bin/env python3
"""
VMotors - Generador de la base de datos SQLite
================================================

Version SQLite del generador de base de datos, pensada para correr en una
sola maquina sin depender de un servidor PostgreSQL: basta con Python y el
archivo `vmotors.db` que este script crea junto a si mismo. Reutiliza la
misma logica de generacion de datos ficticios (Faker) que `seed_database.py`,
importada desde `generador.py`.

Uso rapido
----------
    pip install -r requirements.txt
    python seed_sqlite.py --reset --yes

El backend (carpeta `backend/`) lee este mismo archivo `vmotors.db`.
"""

from __future__ import annotations

import argparse
import os
import random
import sqlite3
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

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

APP_NAME = "VMotors"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "vmotors.db"


# ===========================================================================
# DDL - estructura de la base de datos (SQLite)
# ===========================================================================

def construir_ddl() -> str:
    etapas = ", ".join(f"'{e}'" for e in ETAPAS)
    estatus_cita = ", ".join(f"'{e}'" for e in ESTATUS_CITA)
    pagos = ", ".join(f"'{p}'" for p in FORMAS_PAGO)
    trans = ", ".join(f"'{t}'" for t in TRANSMISIONES)

    return f"""
PRAGMA foreign_keys = ON;

CREATE TABLE clientes (
    id_cliente          INTEGER       PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT          NOT NULL,
    apellido            TEXT          NOT NULL,
    razon_social        TEXT,
    rfc                 TEXT,
    telefono            TEXT          NOT NULL,
    telefono_oficina    TEXT,
    correo              TEXT,
    acepta_promociones  INTEGER       NOT NULL DEFAULT 0,
    calle               TEXT,
    numero              TEXT,
    colonia             TEXT,
    municipio           TEXT,
    estado              TEXT,
    codigo_postal       TEXT,
    fecha_registro      TEXT          NOT NULL DEFAULT (datetime('now')),

    CHECK (length(trim(nombre))   >= 2),
    CHECK (length(trim(apellido)) >= 2)
);

CREATE UNIQUE INDEX ux_clientes_rfc      ON clientes (rfc)           WHERE rfc    IS NOT NULL;
CREATE UNIQUE INDEX ux_clientes_correo   ON clientes (lower(correo)) WHERE correo IS NOT NULL;
CREATE        INDEX ix_clientes_telefono ON clientes (telefono);
CREATE        INDEX ix_clientes_apellido ON clientes (lower(apellido), lower(nombre));

CREATE TABLE vehiculos (
    id_vehiculo     INTEGER      PRIMARY KEY AUTOINCREMENT,
    id_cliente      INTEGER      NOT NULL REFERENCES clientes (id_cliente),
    placas          TEXT         NOT NULL UNIQUE,
    marca           TEXT         NOT NULL,
    modelo          TEXT         NOT NULL,
    anio            INTEGER      NOT NULL,
    color           TEXT,
    transmision     TEXT         NOT NULL DEFAULT 'Manual',
    motor           TEXT,
    fecha_registro  TEXT         NOT NULL DEFAULT (datetime('now')),

    CHECK (placas = upper(placas)),
    CHECK (anio BETWEEN 1980 AND 2100),
    CHECK (transmision IN ({trans}))
);

CREATE INDEX ix_vehiculos_cliente ON vehiculos (id_cliente);
CREATE INDEX ix_vehiculos_marca   ON vehiculos (marca, modelo);

CREATE TABLE citas (
    id_cita         INTEGER      PRIMARY KEY AUTOINCREMENT,
    id_vehiculo     INTEGER      NOT NULL REFERENCES vehiculos (id_vehiculo),
    fecha           TEXT         NOT NULL,
    hora_inicio     TEXT         NOT NULL,
    hora_fin        TEXT         NOT NULL,
    motivo_ingreso  TEXT         NOT NULL,
    estatus_cita    TEXT         NOT NULL DEFAULT 'Agendada',
    fecha_registro  TEXT         NOT NULL DEFAULT (datetime('now')),

    CHECK (hora_fin > hora_inicio),
    CHECK (length(trim(motivo_ingreso)) > 0),
    CHECK (estatus_cita IN ({estatus_cita}))
);

-- Regla del Proceso 2.0: no puede existir mas de una cita ACTIVA en el mismo
-- par (fecha, hora_inicio). Las citas canceladas quedan fuera del indice.
CREATE UNIQUE INDEX ux_citas_bloque_activo
    ON citas (fecha, hora_inicio)
    WHERE estatus_cita <> 'Cancelada';

CREATE INDEX ix_citas_fecha    ON citas (fecha, hora_inicio);
CREATE INDEX ix_citas_vehiculo ON citas (id_vehiculo);

CREATE TABLE refacciones (
    id_refaccion     INTEGER       PRIMARY KEY AUTOINCREMENT,
    clave            TEXT          NOT NULL UNIQUE,
    descripcion      TEXT          NOT NULL,
    categoria        TEXT          NOT NULL,
    precio_unitario  REAL          NOT NULL,

    CHECK (precio_unitario >= 0)
);

CREATE INDEX ix_refacciones_categoria ON refacciones (categoria);

CREATE TABLE ordenes_servicio (
    id_orden           INTEGER       PRIMARY KEY AUTOINCREMENT,
    id_cita            INTEGER       NOT NULL UNIQUE REFERENCES citas (id_cita),
    folio              TEXT          NOT NULL UNIQUE,
    fecha_ingreso      TEXT          NOT NULL DEFAULT (datetime('now')),
    hora_prometida     TEXT,
    fecha_entrega      TEXT,
    kilometraje        INTEGER,
    nivel_combustible  INTEGER,
    forma_pago         TEXT,
    diagnostico        TEXT,
    estatus            TEXT          NOT NULL DEFAULT 'Pendiente',
    costo_mano_obra    REAL          NOT NULL DEFAULT 0,
    costo_refacciones  REAL          NOT NULL DEFAULT 0,
    costo_total        REAL          NOT NULL DEFAULT 0,

    CHECK (estatus IN ({etapas})),
    CHECK (forma_pago IS NULL OR forma_pago IN ({pagos})),
    CHECK (kilometraje IS NULL OR kilometraje >= 0),
    CHECK (nivel_combustible IS NULL OR nivel_combustible BETWEEN 0 AND 8),
    CHECK (costo_mano_obra >= 0 AND costo_refacciones >= 0 AND costo_total >= 0)
);

CREATE INDEX ix_ordenes_estatus ON ordenes_servicio (estatus);
CREATE INDEX ix_ordenes_ingreso ON ordenes_servicio (fecha_ingreso DESC);

CREATE TABLE orden_refacciones (
    id_detalle       INTEGER        PRIMARY KEY AUTOINCREMENT,
    id_orden         INTEGER        NOT NULL REFERENCES ordenes_servicio (id_orden),
    id_refaccion     INTEGER        NOT NULL REFERENCES refacciones (id_refaccion),
    cantidad         INTEGER        NOT NULL,
    precio_unitario  REAL           NOT NULL,
    importe          REAL           GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,

    UNIQUE (id_orden, id_refaccion),
    CHECK (cantidad > 0),
    CHECK (precio_unitario >= 0)
);

CREATE INDEX ix_detalle_orden ON orden_refacciones (id_orden);

CREATE TABLE historial_estatus (
    id_historial      INTEGER       PRIMARY KEY AUTOINCREMENT,
    id_orden          INTEGER       NOT NULL REFERENCES ordenes_servicio (id_orden),
    estatus_anterior  TEXT,
    estatus_nuevo     TEXT          NOT NULL,
    fecha_cambio      TEXT          NOT NULL DEFAULT (datetime('now')),
    usuario           TEXT          NOT NULL DEFAULT 'administrador',
    nota              TEXT,

    CHECK (estatus_nuevo IN ({etapas})),
    CHECK (estatus_anterior IS NULL OR estatus_anterior IN ({etapas}))
);

CREATE INDEX ix_historial_orden ON historial_estatus (id_orden, fecha_cambio);
"""


DROP_SQL = """
DROP TABLE IF EXISTS historial_estatus;
DROP TABLE IF EXISTS orden_refacciones;
DROP TABLE IF EXISTS ordenes_servicio;
DROP TABLE IF EXISTS refacciones;
DROP TABLE IF EXISTS citas;
DROP TABLE IF EXISTS vehiculos;
DROP TABLE IF EXISTS clientes;
"""


# ===========================================================================
# Insercion de datos
# ===========================================================================

def _dec(v):
    """Convierte Decimal/date/time/datetime a un tipo que sqlite3 acepte."""
    if isinstance(v, Decimal):
        return float(v)
    if hasattr(v, "isoformat"):
        return v.isoformat(sep=" ") if hasattr(v, "hour") and hasattr(v, "year") else v.isoformat()
    return v


def _fila(t: tuple) -> tuple:
    return tuple(_dec(v) for v in t)


def insertar_datos(con: sqlite3.Connection, gen: Generador) -> None:
    cur = con.cursor()

    cur.executemany(
        "INSERT INTO refacciones (id_refaccion, clave, descripcion, categoria, precio_unitario) "
        "VALUES (?, ?, ?, ?, ?)",
        [_fila((i, *r)) for i, r in enumerate(REFACCIONES, start=1)],
    )

    cur.executemany(
        """INSERT INTO clientes
             (id_cliente, nombre, apellido, razon_social, rfc, telefono, telefono_oficina,
              correo, acepta_promociones, calle, numero, colonia, municipio, estado,
              codigo_postal, fecha_registro)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [_fila(c) for c in gen.clientes],
    )

    cur.executemany(
        """INSERT INTO vehiculos
             (id_vehiculo, id_cliente, placas, marca, modelo, anio, color,
              transmision, motor, fecha_registro)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [_fila(v) for v in gen.vehiculos],
    )

    cur.executemany(
        """INSERT INTO citas
             (id_cita, id_vehiculo, fecha, hora_inicio, hora_fin, motivo_ingreso,
              estatus_cita, fecha_registro)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [_fila(c) for c in gen.citas],
    )

    cur.executemany(
        """INSERT INTO ordenes_servicio
             (id_orden, id_cita, folio, fecha_ingreso, hora_prometida, fecha_entrega,
              kilometraje, nivel_combustible, forma_pago, diagnostico, estatus,
              costo_mano_obra, costo_refacciones, costo_total)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [_fila(o) for o in gen.ordenes],
    )

    cur.executemany(
        """INSERT INTO orden_refacciones
             (id_detalle, id_orden, id_refaccion, cantidad, precio_unitario)
           VALUES (?, ?, ?, ?, ?)""",
        [_fila(d) for d in gen.detalle],
    )

    cur.executemany(
        """INSERT INTO historial_estatus
             (id_orden, estatus_anterior, estatus_nuevo, fecha_cambio, usuario, nota)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [_fila(h) for h in gen.historial],
    )

    con.commit()


def resumen(con: sqlite3.Connection, db_path: Path) -> None:
    cur = con.cursor()
    print("\n" + "=" * 62)
    print(f"  Base de datos {APP_NAME} lista · {db_path}")
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
    print("=" * 62 + "\n")


# ===========================================================================
# Punto de entrada
# ===========================================================================

def parsear_argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=f"Crea y puebla la base de datos SQLite de {APP_NAME}.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python seed_sqlite.py --reset --yes\n"
            "  python seed_sqlite.py --reset --clientes 200 --seed 7\n"
        ),
    )
    p.add_argument("--clientes", type=int, default=60,
                   help="cantidad de clientes a generar (por omisión 60)")
    p.add_argument("--seed", type=int, default=2026,
                   help="semilla aleatoria para obtener resultados reproducibles")
    p.add_argument("--db-path", default=str(DEFAULT_DB_PATH),
                   help=f"ruta del archivo SQLite (por omisión {DEFAULT_DB_PATH})")
    p.add_argument("--reset", action="store_true",
                   help="elimina y vuelve a crear las tablas antes de insertar")
    p.add_argument("--yes", "-y", action="store_true",
                   help="no pedir confirmación al usar --reset")
    return p.parse_args()


def main() -> int:
    args = parsear_argumentos()

    if args.clientes < 1:
        sys.exit("--clientes debe ser un número mayor o igual a 1.")

    db_path = Path(args.db_path)
    existe = db_path.exists()

    if existe and not args.reset:
        sys.exit(
            f"\nEl archivo '{db_path}' ya existe.\n"
            "Vuelva a ejecutar con --reset para eliminarlo y recrearlo."
        )
    if existe and args.reset and not args.yes:
        if not sys.stdin.isatty():
            sys.exit("Se requiere --yes para ejecutar --reset de forma no interactiva.")
        print(f"\nSe eliminará el archivo '{db_path}' y se recreará desde cero.")
        if input("Escriba 'si' para continuar: ").strip().lower() not in ("si", "sí"):
            print("Operación cancelada.")
            return 1

    if existe:
        os.remove(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(construir_ddl())

    print(f"Generando datos ficticios (semilla {args.seed})...")
    fake = Faker("es_MX")
    Faker.seed(args.seed)
    rnd = random.Random(args.seed)

    gen = Generador(fake, rnd, date.today())
    gen.generar_clientes(args.clientes)
    gen.generar_vehiculos()
    gen.generar_citas_y_ordenes()

    print("Insertando registros...")
    insertar_datos(con, gen)

    resumen(con, db_path)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
