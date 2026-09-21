"""Formato F-01: recepcion de una unidad en mostrador.

Un solo endpoint hace lo que en `recepcion.html` son tres pasos: encuentra o
da de alta al cliente (por telefono), encuentra o da de alta el vehiculo (por
placas, sin duplicar si ya esta registrado) y crea la cita + la orden de
servicio ya en estatus "Recibido", porque a diferencia de una cita agendada
desde `agenda.html`, aqui la unidad ya esta fisicamente en el taller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_auth
from ..database import get_connection
from ..schemas import RecepcionIn

router = APIRouter(prefix="/api", tags=["recepcion"], dependencies=[Depends(require_auth)])

NOTA_PENDIENTE = "Cita confirmada en mostrador durante la recepción."
NOTA_RECIBIDO = "Unidad recibida en bahía; se registra kilometraje e inventario."


@router.post("/recepcion", status_code=201)
def recibir_unidad(datos: RecepcionIn):
    con = get_connection()
    try:
        # 1) Cliente: se reutiliza por telefono si ya existe expediente.
        cliente = con.execute(
            "SELECT id_cliente FROM clientes WHERE telefono = ?", (datos.cliente.telefono,)
        ).fetchone()
        if cliente:
            id_cliente = cliente["id_cliente"]
        else:
            cur = con.execute(
                """INSERT INTO clientes
                     (nombre, apellido, razon_social, rfc, telefono, telefono_oficina, correo,
                      acepta_promociones, calle, numero, colonia, municipio, estado, codigo_postal)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datos.cliente.nombre, datos.cliente.apellido, datos.cliente.razon_social,
                    datos.cliente.rfc, datos.cliente.telefono, datos.cliente.telefono_oficina,
                    datos.cliente.correo, int(datos.cliente.acepta_promociones), datos.cliente.calle,
                    datos.cliente.numero, datos.cliente.colonia, datos.cliente.municipio,
                    datos.cliente.estado, datos.cliente.codigo_postal,
                ),
            )
            id_cliente = cur.lastrowid

        # 2) Vehiculo: se reutiliza por placas (queda ligado a quien ya lo tenga
        #    registrado, para no duplicar la unidad).
        vehiculo = con.execute(
            "SELECT id_vehiculo FROM vehiculos WHERE placas = ?", (datos.vehiculo.placas,)
        ).fetchone()
        if vehiculo:
            id_vehiculo = vehiculo["id_vehiculo"]
        else:
            cur = con.execute(
                """INSERT INTO vehiculos (id_cliente, placas, marca, modelo, anio, color, transmision, motor)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (id_cliente, datos.vehiculo.placas, datos.vehiculo.marca, datos.vehiculo.modelo,
                 datos.vehiculo.anio, datos.vehiculo.color, datos.vehiculo.transmision, datos.vehiculo.motor),
            )
            id_vehiculo = cur.lastrowid

        # 3) Cita: mismo bloqueo de traslape que usa la agenda.
        v = datos.visita
        ocupado = con.execute(
            """SELECT id_cita FROM citas
                WHERE fecha = ? AND hora_inicio = ? AND estatus_cita <> 'Cancelada'""",
            (v.fecha.isoformat(), v.hora_inicio),
        ).fetchone()
        if ocupado:
            raise HTTPException(
                409, f"El bloque de las {v.hora_inicio} del {v.fecha.isoformat()} ya está comprometido."
            )

        cur = con.execute(
            """INSERT INTO citas (id_vehiculo, fecha, hora_inicio, hora_fin, motivo_ingreso, estatus_cita)
               VALUES (?, ?, ?, ?, ?, 'Atendida')""",
            (id_vehiculo, v.fecha.isoformat(), v.hora_inicio, v.hora_fin, v.motivo_ingreso),
        )
        id_cita = cur.lastrowid

        # 4) Orden de servicio: ya en "Recibido" porque la unidad esta en piso.
        anio = v.fecha.year
        n = con.execute(
            "SELECT COUNT(*) AS n FROM ordenes_servicio WHERE folio LIKE ?", (f"OS-{anio}-%",)
        ).fetchone()["n"]
        folio = f"OS-{anio}-{n + 1:04d}"
        fecha_ingreso = f"{v.fecha.isoformat()} {v.hora_entrada}:00"
        hora_prometida = f"{v.fecha.isoformat()} {v.hora_prometida}:00"

        cur = con.execute(
            """INSERT INTO ordenes_servicio
                 (id_cita, folio, fecha_ingreso, hora_prometida, kilometraje, nivel_combustible,
                  forma_pago, estatus, costo_mano_obra, costo_refacciones, costo_total)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Recibido', 0, 0, 0)""",
            (id_cita, folio, fecha_ingreso, hora_prometida, v.kilometraje, v.nivel_combustible, v.forma_pago),
        )
        id_orden = cur.lastrowid

        con.executemany(
            """INSERT INTO historial_estatus (id_orden, estatus_anterior, estatus_nuevo, nota)
               VALUES (?, ?, ?, ?)""",
            [
                (id_orden, None, "Pendiente", NOTA_PENDIENTE),
                (id_orden, "Pendiente", "Recibido", NOTA_RECIBIDO),
            ],
        )

        con.commit()
        return {
            "id_cliente": id_cliente,
            "id_vehiculo": id_vehiculo,
            "id_cita": id_cita,
            "id_orden": id_orden,
            "folio": folio,
        }
    finally:
        con.close()
