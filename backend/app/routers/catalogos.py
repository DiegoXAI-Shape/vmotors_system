"""Endpoints de solo lectura para clientes, vehiculos, citas y refacciones.

Cada consulta devuelve los registros con la misma forma de campos que usaba
`frontend/assets/js/data.js`, para que las paginas existentes no requieran
cambios: solo cambia de donde viene el arreglo (antes hardcodeado, ahora esta
API respaldada por SQLite).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_auth
from ..database import get_connection, query_all, query_one
from ..schemas import CitaIn, ClienteIn, VehiculoIn

router = APIRouter(prefix="/api", tags=["catalogos"], dependencies=[Depends(require_auth)])


@router.get("/clientes")
def listar_clientes():
    filas = query_all(
        """SELECT id_cliente, nombre, apellido, razon_social, rfc, telefono,
                  telefono_oficina, correo, acepta_promociones, calle, numero,
                  colonia, municipio, estado, codigo_postal, fecha_registro
             FROM clientes
            ORDER BY id_cliente"""
    )
    for f in filas:
        f["acepta_promociones"] = bool(f["acepta_promociones"])
    return filas


@router.get("/vehiculos")
def listar_vehiculos():
    return query_all(
        """SELECT id_vehiculo, id_cliente, placas, marca, modelo, anio, color,
                  transmision, motor, fecha_registro
             FROM vehiculos
            ORDER BY id_vehiculo"""
    )


@router.get("/citas")
def listar_citas():
    return query_all(
        """SELECT id_cita, id_vehiculo, fecha,
                  substr(hora_inicio, 1, 5) AS hora_inicio,
                  substr(hora_fin, 1, 5)    AS hora_fin,
                  motivo_ingreso, estatus_cita
             FROM citas
            ORDER BY fecha, hora_inicio"""
    )


@router.get("/refacciones")
def listar_refacciones():
    return query_all(
        """SELECT id_refaccion, clave, descripcion, categoria, precio_unitario
             FROM refacciones
            ORDER BY id_refaccion"""
    )


# ---------------------------------------------------------------------------
# Busqueda de expedientes existentes (cliente recurrente / placa registrada)
# ---------------------------------------------------------------------------

@router.get("/clientes/buscar")
def buscar_cliente(telefono: str | None = None, rfc: str | None = None):
    if telefono:
        return query_one("SELECT * FROM clientes WHERE telefono = ?", (telefono,))
    if rfc:
        return query_one("SELECT * FROM clientes WHERE rfc = ?", (rfc.upper(),))
    return None


@router.get("/vehiculos/buscar")
def buscar_vehiculo(placas: str):
    return query_one("SELECT * FROM vehiculos WHERE placas = ?", (placas.strip().upper(),))


# ---------------------------------------------------------------------------
# Altas
# ---------------------------------------------------------------------------

@router.post("/clientes", status_code=201)
def crear_cliente(datos: ClienteIn):
    con = get_connection()
    try:
        if datos.rfc and con.execute("SELECT 1 FROM clientes WHERE rfc = ?", (datos.rfc,)).fetchone():
            raise HTTPException(409, f"Ya existe un cliente con el RFC {datos.rfc}.")
        cur = con.execute(
            """INSERT INTO clientes
                 (nombre, apellido, razon_social, rfc, telefono, telefono_oficina, correo,
                  acepta_promociones, calle, numero, colonia, municipio, estado, codigo_postal)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datos.nombre, datos.apellido, datos.razon_social, datos.rfc, datos.telefono,
                datos.telefono_oficina, datos.correo, int(datos.acepta_promociones), datos.calle,
                datos.numero, datos.colonia, datos.municipio, datos.estado, datos.codigo_postal,
            ),
        )
        con.commit()
        return {"id_cliente": cur.lastrowid}
    finally:
        con.close()


@router.post("/vehiculos", status_code=201)
def crear_vehiculo(id_cliente: int, datos: VehiculoIn):
    con = get_connection()
    try:
        if not con.execute("SELECT 1 FROM clientes WHERE id_cliente = ?", (id_cliente,)).fetchone():
            raise HTTPException(404, "El cliente indicado no existe.")
        if con.execute("SELECT 1 FROM vehiculos WHERE placas = ?", (datos.placas,)).fetchone():
            raise HTTPException(409, f"Ya existe un vehículo registrado con las placas {datos.placas}.")
        cur = con.execute(
            """INSERT INTO vehiculos (id_cliente, placas, marca, modelo, anio, color, transmision, motor)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (id_cliente, datos.placas, datos.marca, datos.modelo, datos.anio, datos.color,
             datos.transmision, datos.motor),
        )
        con.commit()
        return {"id_vehiculo": cur.lastrowid}
    finally:
        con.close()


@router.post("/citas", status_code=201)
def crear_cita(datos: CitaIn):
    con = get_connection()
    try:
        if not con.execute(
            "SELECT 1 FROM vehiculos WHERE id_vehiculo = ?", (datos.id_vehiculo,)
        ).fetchone():
            raise HTTPException(404, "El vehículo indicado no existe.")

        ocupado = con.execute(
            """SELECT c.id_cita, v.marca, v.modelo, v.placas
                 FROM citas c JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
                WHERE c.fecha = ? AND c.hora_inicio = ? AND c.estatus_cita <> 'Cancelada'""",
            (datos.fecha.isoformat(), datos.hora_inicio),
        ).fetchone()
        if ocupado:
            raise HTTPException(
                409,
                f"El bloque de las {datos.hora_inicio} del {datos.fecha.isoformat()} ya está "
                f"comprometido con {ocupado['marca']} {ocupado['modelo']} ({ocupado['placas']}).",
            )

        hora_h = int(datos.hora_inicio.split(":")[0])
        hora_fin = f"{min(hora_h + 1, 19):02d}:00"
        cur = con.execute(
            """INSERT INTO citas (id_vehiculo, fecha, hora_inicio, hora_fin, motivo_ingreso, estatus_cita)
               VALUES (?, ?, ?, ?, ?, 'Agendada')""",
            (datos.id_vehiculo, datos.fecha.isoformat(), datos.hora_inicio, hora_fin, datos.motivo_ingreso),
        )
        con.commit()
        return {"id_cita": cur.lastrowid}
    finally:
        con.close()
