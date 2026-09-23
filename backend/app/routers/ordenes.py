"""Ordenes de servicio, con su desglose de refacciones e historial de estatus
anidados exactamente como los esperaba `VM.ordenes` en el prototipo estatico.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_auth
from ..database import get_connection, query_all
from ..schemas import ETAPAS, OrdenPatchIn, RefaccionOrdenIn

router = APIRouter(prefix="/api", tags=["ordenes"], dependencies=[Depends(require_auth)])


@router.get("/ordenes")
def listar_ordenes():
    """Ordenes operativamente vigentes: todo lo que no esta entregado, mas lo
    entregado en los ultimos 30 dias. Esto alimenta el tablero, el kanban del
    taller y la bitacora de ordenes con una carga de trabajo realista, sin
    volcar ahi los dos anios completos de historial cerrado (eso vive en
    /api/ordenes_historicas)."""
    con = get_connection()
    try:
        ordenes = [
            dict(r)
            for r in con.execute(
                """SELECT id_orden, id_cita, folio, fecha_ingreso, hora_prometida,
                          fecha_entrega, kilometraje, nivel_combustible, forma_pago,
                          diagnostico, estatus, costo_mano_obra, costo_refacciones,
                          costo_total
                     FROM ordenes_servicio
                    WHERE estatus <> 'Entregado'
                       OR fecha_entrega >= datetime('now', '-30 days')
                    ORDER BY fecha_ingreso DESC"""
            ).fetchall()
        ]
        if not ordenes:
            return []

        ids = [o["id_orden"] for o in ordenes]
        marcadores = ",".join("?" * len(ids))

        detalle_por_orden: dict[int, list[dict]] = {i: [] for i in ids}
        for r in con.execute(
            f"""SELECT id_detalle, id_orden, id_refaccion, cantidad, precio_unitario
                  FROM orden_refacciones
                 WHERE id_orden IN ({marcadores})
                 ORDER BY id_detalle""",
            ids,
        ).fetchall():
            detalle_por_orden[r["id_orden"]].append(
                {
                    "id_detalle": r["id_detalle"],
                    "id_refaccion": r["id_refaccion"],
                    "cantidad": r["cantidad"],
                    "precio_unitario": r["precio_unitario"],
                }
            )

        historial_por_orden: dict[int, list[dict]] = {i: [] for i in ids}
        for r in con.execute(
            f"""SELECT id_orden, estatus_nuevo, fecha_cambio, nota
                  FROM historial_estatus
                 WHERE id_orden IN ({marcadores})
                 ORDER BY fecha_cambio, id_historial""",
            ids,
        ).fetchall():
            historial_por_orden[r["id_orden"]].append(
                {"estatus": r["estatus_nuevo"], "fecha": r["fecha_cambio"], "nota": r["nota"]}
            )

        for o in ordenes:
            o["detalle"] = detalle_por_orden[o["id_orden"]]
            o["historial"] = historial_por_orden[o["id_orden"]]

        return ordenes
    finally:
        con.close()


@router.get("/ordenes_historicas")
def listar_ordenes_historicas():
    """Ledger completo de ordenes ya entregadas, usado por reportes y por el
    historial por placa en la ficha del vehiculo."""
    return query_all(
        """SELECT o.folio, c.id_vehiculo, o.fecha_entrega, o.estatus,
                  o.diagnostico, o.kilometraje, o.costo_total
             FROM ordenes_servicio o
             JOIN citas c ON c.id_cita = o.id_cita
            WHERE o.estatus = 'Entregado'
            ORDER BY o.fecha_entrega DESC"""
    )


def _orden_o_404(con, id_orden: int) -> dict:
    row = con.execute(
        "SELECT * FROM ordenes_servicio WHERE id_orden = ?", (id_orden,)
    ).fetchone()
    if not row:
        raise HTTPException(404, "La orden indicada no existe.")
    return dict(row)


@router.patch("/ordenes/{id_orden}")
def actualizar_orden(id_orden: int, cambios: OrdenPatchIn):
    """Guarda diagnostico/mano de obra y, si viene, aplica un cambio de
    estatus validando que el flujo avance una sola etapa a la vez (misma
    regla que ya vivia solo en el cliente en `orden-detalle.html`)."""
    con = get_connection()
    try:
        actual = _orden_o_404(con, id_orden)

        nueva_mano_obra = cambios.costo_mano_obra if cambios.costo_mano_obra is not None else actual["costo_mano_obra"]
        costo_refacciones = actual["costo_refacciones"]
        nuevo_total = round(nueva_mano_obra + costo_refacciones, 2)

        nuevo_estatus = actual["estatus"]
        fecha_entrega = actual["fecha_entrega"]

        if cambios.estatus and cambios.estatus != actual["estatus"]:
            i_actual = ETAPAS.index(actual["estatus"])
            i_destino = ETAPAS.index(cambios.estatus)
            if i_destino > i_actual + 1:
                raise HTTPException(
                    409,
                    f"No es posible saltar de '{actual['estatus']}' a '{cambios.estatus}'. "
                    "El flujo debe avanzar etapa por etapa.",
                )
            if cambios.estatus == "Entregado":
                if nuevo_total <= 0:
                    raise HTTPException(
                        409, "No se puede marcar como Entregado mientras el costo total sea cero."
                    )
                fecha_entrega = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nuevo_estatus = cambios.estatus

        con.execute(
            """UPDATE ordenes_servicio
                  SET diagnostico = COALESCE(?, diagnostico),
                      costo_mano_obra = ?,
                      costo_total = ?,
                      estatus = ?,
                      fecha_entrega = ?
                WHERE id_orden = ?""",
            (cambios.diagnostico, nueva_mano_obra, nuevo_total, nuevo_estatus, fecha_entrega, id_orden),
        )

        if nuevo_estatus != actual["estatus"]:
            con.execute(
                """INSERT INTO historial_estatus (id_orden, estatus_anterior, estatus_nuevo, nota)
                   VALUES (?, ?, ?, ?)""",
                (id_orden, actual["estatus"], nuevo_estatus, f"Estatus actualizado a '{nuevo_estatus}'."),
            )

        con.commit()
        return {"ok": True, "estatus": nuevo_estatus, "costo_total": nuevo_total}
    finally:
        con.close()


def _recalcular_costos(con, id_orden: int) -> float:
    total_refacciones = con.execute(
        "SELECT COALESCE(SUM(importe), 0) AS t FROM orden_refacciones WHERE id_orden = ?", (id_orden,)
    ).fetchone()["t"]
    mano_obra = con.execute(
        "SELECT costo_mano_obra FROM ordenes_servicio WHERE id_orden = ?", (id_orden,)
    ).fetchone()["costo_mano_obra"]
    nuevo_total = round(mano_obra + total_refacciones, 2)
    con.execute(
        "UPDATE ordenes_servicio SET costo_refacciones = ?, costo_total = ? WHERE id_orden = ?",
        (total_refacciones, nuevo_total, id_orden),
    )
    return nuevo_total


@router.post("/ordenes/{id_orden}/refacciones", status_code=201)
def agregar_refaccion(id_orden: int, datos: RefaccionOrdenIn):
    con = get_connection()
    try:
        _orden_o_404(con, id_orden)
        refaccion = con.execute(
            "SELECT precio_unitario FROM refacciones WHERE id_refaccion = ?", (datos.id_refaccion,)
        ).fetchone()
        if not refaccion:
            raise HTTPException(404, "La refacción indicada no existe en el catálogo.")

        existente = con.execute(
            "SELECT id_detalle, cantidad FROM orden_refacciones WHERE id_orden = ? AND id_refaccion = ?",
            (id_orden, datos.id_refaccion),
        ).fetchone()
        if existente:
            con.execute(
                "UPDATE orden_refacciones SET cantidad = ? WHERE id_detalle = ?",
                (existente["cantidad"] + datos.cantidad, existente["id_detalle"]),
            )
        else:
            con.execute(
                """INSERT INTO orden_refacciones (id_orden, id_refaccion, cantidad, precio_unitario)
                   VALUES (?, ?, ?, ?)""",
                (id_orden, datos.id_refaccion, datos.cantidad, refaccion["precio_unitario"]),
            )

        nuevo_total = _recalcular_costos(con, id_orden)
        con.commit()
        return {"ok": True, "costo_total": nuevo_total}
    finally:
        con.close()


@router.delete("/ordenes/{id_orden}/refacciones/{id_detalle}")
def quitar_refaccion(id_orden: int, id_detalle: int):
    con = get_connection()
    try:
        _orden_o_404(con, id_orden)
        borrado = con.execute(
            "DELETE FROM orden_refacciones WHERE id_detalle = ? AND id_orden = ?", (id_detalle, id_orden)
        )
        if borrado.rowcount == 0:
            raise HTTPException(404, "El renglón de refacción indicado no existe en esta orden.")

        nuevo_total = _recalcular_costos(con, id_orden)
        con.commit()
        return {"ok": True, "costo_total": nuevo_total}
    finally:
        con.close()


ETAPAS_ELIMINABLES = ("Pendiente", "Recibido")


@router.delete("/ordenes/{id_orden}")
def eliminar_orden(id_orden: int):
    """Solo permite borrar una orden recien creada por error (todavia sin
    diagnostico ni trabajo registrado). Mas alla de esas dos primeras etapas
    la orden es un registro real del taller y se corrige, no se borra. La
    cita que la origino se cancela para liberar su bloque en la agenda."""
    con = get_connection()
    try:
        actual = _orden_o_404(con, id_orden)
        if actual["estatus"] not in ETAPAS_ELIMINABLES:
            raise HTTPException(
                409,
                f"No se puede eliminar una orden en etapa '{actual['estatus']}'. Solo se permite "
                f"en {' o '.join(ETAPAS_ELIMINABLES)}, antes de registrar diagnóstico o trabajo; "
                "para etapas posteriores corrija los datos desde la orden en vez de borrarla.",
            )
        con.execute("DELETE FROM historial_estatus WHERE id_orden = ?", (id_orden,))
        con.execute("DELETE FROM orden_refacciones WHERE id_orden = ?", (id_orden,))
        con.execute("UPDATE citas SET estatus_cita = 'Cancelada' WHERE id_cita = ?", (actual["id_cita"],))
        con.execute("DELETE FROM ordenes_servicio WHERE id_orden = ?", (id_orden,))
        con.commit()
        return {"ok": True}
    finally:
        con.close()
