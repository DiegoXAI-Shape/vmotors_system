"""Pruebas de las reglas de negocio del backend de VMotors.

No cubren el frontend (para eso habria que automatizar un navegador); lo que
protegen es que la API siga aplicando las mismas reglas documentadas en el
esquema original: formato de datos, traslapes de citas, avance de etapas de
una orden, y los limites de lo que se puede editar o borrar.
"""

from __future__ import annotations

from datetime import date, timedelta

MANANA = (date.today() + timedelta(days=1)).isoformat()
PASADO_MANANA = (date.today() + timedelta(days=2)).isoformat()


# ===========================================================================
# Autenticacion
# ===========================================================================

def test_endpoint_protegido_sin_sesion_regresa_401(client):
    assert client.get("/api/clientes").status_code == 401


def test_login_correcto(client):
    r = client.post("/api/auth/login", json={"usuario": "administrador", "contrasena": "vmotors2026"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_login_incorrecto_no_abre_sesion(client):
    r = client.post("/api/auth/login", json={"usuario": "administrador", "contrasena": "mala"})
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert client.get("/api/clientes").status_code == 401


def test_logout_cierra_la_sesion(auth):
    assert auth.get("/api/clientes").status_code == 200
    auth.post("/api/auth/logout")
    assert auth.get("/api/clientes").status_code == 401


def test_limite_de_intentos_de_login(client):
    for _ in range(5):
        client.post("/api/auth/login", json={"usuario": "x", "contrasena": "mala"})
    r = client.post("/api/auth/login", json={"usuario": "x", "contrasena": "mala"})
    assert r.status_code == 429
    # ni siquiera con la contraseña correcta deja pasar mientras dure el bloqueo
    r2 = client.post("/api/auth/login", json={"usuario": "administrador", "contrasena": "vmotors2026"})
    assert r2.status_code == 429


# ===========================================================================
# Clientes
# ===========================================================================

def test_crear_cliente_valido(auth):
    r = auth.post("/api/clientes", json={
        "nombre": "Luis", "apellido": "García", "telefono": "8123456789", "acepta_promociones": False,
    })
    assert r.status_code == 201
    assert "id_cliente" in r.json()


def test_crear_cliente_telefono_invalido_422(auth):
    r = auth.post("/api/clientes", json={"nombre": "Luis", "apellido": "García", "telefono": "123"})
    assert r.status_code == 422


def test_crear_cliente_rfc_invalido_422(auth):
    r = auth.post("/api/clientes", json={
        "nombre": "Luis", "apellido": "García", "telefono": "8123456789", "rfc": "NO-VALIDO",
    })
    assert r.status_code == 422


def test_editar_cliente_persiste_los_cambios(auth, cliente_id):
    r = auth.patch(f"/api/clientes/{cliente_id}", json={
        "nombre": "Ana María", "apellido": "Pérez", "telefono": "8112223344", "acepta_promociones": False,
    })
    assert r.status_code == 200

    cliente = next(c for c in auth.get("/api/clientes").json() if c["id_cliente"] == cliente_id)
    assert cliente["nombre"] == "Ana María"
    assert cliente["acepta_promociones"] is False


def test_buscar_cliente_por_telefono(auth, cliente_id):
    r = auth.get("/api/clientes/buscar", params={"telefono": "8112223344"})
    assert r.status_code == 200
    assert r.json()["id_cliente"] == cliente_id


def test_buscar_cliente_inexistente_regresa_null(auth):
    r = auth.get("/api/clientes/buscar", params={"telefono": "0000000000"})
    assert r.status_code == 200
    assert r.json() is None


# ===========================================================================
# Vehiculos
# ===========================================================================

def test_placas_duplicadas_409(auth, cliente_id, vehiculo_id):
    r = auth.post(f"/api/vehiculos?id_cliente={cliente_id}", json={
        "placas": "ABC-123-D", "marca": "Toyota", "modelo": "Corolla", "anio": 2020, "transmision": "Manual",
    })
    assert r.status_code == 409


def test_anio_fuera_de_rango_422(auth, cliente_id):
    r = auth.post(f"/api/vehiculos?id_cliente={cliente_id}", json={
        "placas": "XYZ-999-A", "marca": "Toyota", "modelo": "Corolla", "anio": 1900, "transmision": "Manual",
    })
    assert r.status_code == 422


def test_editar_vehiculo(auth, vehiculo_id):
    r = auth.patch(f"/api/vehiculos/{vehiculo_id}", json={
        "placas": "ABC-123-D", "marca": "Nissan", "modelo": "Versa Sense", "anio": 2023, "transmision": "Automático",
    })
    assert r.status_code == 200
    vehiculo = next(v for v in auth.get("/api/vehiculos").json() if v["id_vehiculo"] == vehiculo_id)
    assert vehiculo["modelo"] == "Versa Sense"


def test_eliminar_vehiculo_sin_historial_ok(auth, vehiculo_id):
    r = auth.delete(f"/api/vehiculos/{vehiculo_id}")
    assert r.status_code == 200
    assert auth.get("/api/vehiculos").json() == []


def test_eliminar_vehiculo_con_citas_bloqueado(auth, vehiculo_id):
    auth.post("/api/citas", json={
        "id_vehiculo": vehiculo_id, "fecha": MANANA, "hora_inicio": "09:00", "motivo_ingreso": "Servicio",
    })
    r = auth.delete(f"/api/vehiculos/{vehiculo_id}")
    assert r.status_code == 409


# ===========================================================================
# Citas
# ===========================================================================

def test_crear_cita(auth, vehiculo_id):
    r = auth.post("/api/citas", json={
        "id_vehiculo": vehiculo_id, "fecha": MANANA, "hora_inicio": "10:00", "motivo_ingreso": "Cambio de aceite",
    })
    assert r.status_code == 201


def test_no_se_permite_traslape(auth, cliente_id, vehiculo_id):
    otro_veh = auth.post(f"/api/vehiculos?id_cliente={cliente_id}", json={
        "placas": "OTR-111-B", "marca": "Kia", "modelo": "Rio", "anio": 2021, "transmision": "Manual",
    }).json()["id_vehiculo"]

    r1 = auth.post("/api/citas", json={
        "id_vehiculo": vehiculo_id, "fecha": MANANA, "hora_inicio": "11:00", "motivo_ingreso": "Frenos",
    })
    assert r1.status_code == 201

    r2 = auth.post("/api/citas", json={
        "id_vehiculo": otro_veh, "fecha": MANANA, "hora_inicio": "11:00", "motivo_ingreso": "Otro servicio",
    })
    assert r2.status_code == 409


def test_cancelar_cita_libera_el_bloque(auth, cliente_id, vehiculo_id):
    otro_veh = auth.post(f"/api/vehiculos?id_cliente={cliente_id}", json={
        "placas": "OTR-222-C", "marca": "Kia", "modelo": "Rio", "anio": 2021, "transmision": "Manual",
    }).json()["id_vehiculo"]

    id_cita = auth.post("/api/citas", json={
        "id_vehiculo": vehiculo_id, "fecha": MANANA, "hora_inicio": "12:00", "motivo_ingreso": "Frenos",
    }).json()["id_cita"]

    auth.patch(f"/api/citas/{id_cita}", json={"estatus_cita": "Cancelada"})

    r = auth.post("/api/citas", json={
        "id_vehiculo": otro_veh, "fecha": MANANA, "hora_inicio": "12:00", "motivo_ingreso": "Otro servicio",
    })
    assert r.status_code == 201


def test_reprogramar_cita_a_bloque_ocupado_409(auth, cliente_id, vehiculo_id):
    otro_veh = auth.post(f"/api/vehiculos?id_cliente={cliente_id}", json={
        "placas": "OTR-333-D", "marca": "Kia", "modelo": "Rio", "anio": 2021, "transmision": "Manual",
    }).json()["id_vehiculo"]

    auth.post("/api/citas", json={
        "id_vehiculo": vehiculo_id, "fecha": MANANA, "hora_inicio": "13:00", "motivo_ingreso": "Frenos",
    })
    id_cita_2 = auth.post("/api/citas", json={
        "id_vehiculo": otro_veh, "fecha": PASADO_MANANA, "hora_inicio": "09:00", "motivo_ingreso": "Afinación",
    }).json()["id_cita"]

    r = auth.patch(f"/api/citas/{id_cita_2}", json={"fecha": MANANA, "hora_inicio": "13:00"})
    assert r.status_code == 409


# ===========================================================================
# Recepcion (F-01 completo)
# ===========================================================================

def test_recepcion_crea_cliente_vehiculo_cita_y_orden(auth):
    payload = {
        "cliente": {"nombre": "Marta", "apellido": "Ibarra", "telefono": "8199990000", "acepta_promociones": True},
        "vehiculo": {"placas": "REC-001-A", "marca": "Honda", "modelo": "Civic", "anio": 2021, "transmision": "Automático"},
        "visita": {
            "fecha": date.today().isoformat(), "hora_inicio": "09:00", "hora_fin": "11:00",
            "hora_entrada": "09:05", "hora_prometida": "15:00", "kilometraje": 12000,
            "nivel_combustible": 5, "motivo_ingreso": "Ruido en frenos", "forma_pago": "Efectivo",
        },
    }
    r = auth.post("/api/recepcion", json=payload)
    assert r.status_code == 201
    datos = r.json()
    assert datos["folio"].startswith(f"OS-{date.today().year}-")

    orden = next(o for o in auth.get("/api/ordenes").json() if o["id_orden"] == datos["id_orden"])
    assert orden["estatus"] == "Recibido"
    assert len(orden["historial"]) == 2


def test_recepcion_reutiliza_cliente_y_vehiculo_existentes(auth):
    payload = {
        "cliente": {"nombre": "Marta", "apellido": "Ibarra", "telefono": "8199990001", "acepta_promociones": True},
        "vehiculo": {"placas": "REC-002-B", "marca": "Honda", "modelo": "Civic", "anio": 2021, "transmision": "Automático"},
        "visita": {
            "fecha": date.today().isoformat(), "hora_inicio": "09:00", "hora_fin": "11:00",
            "hora_entrada": "09:05", "hora_prometida": "15:00", "kilometraje": 12000,
            "motivo_ingreso": "Primera visita",
        },
    }
    primera = auth.post("/api/recepcion", json=payload).json()

    payload2 = dict(payload)
    payload2["visita"] = dict(payload["visita"], hora_inicio="14:00", hora_fin="16:00",
                               hora_entrada="14:05", motivo_ingreso="Segunda visita")
    segunda = auth.post("/api/recepcion", json=payload2).json()

    assert segunda["id_cliente"] == primera["id_cliente"]
    assert segunda["id_vehiculo"] == primera["id_vehiculo"]
    assert len(auth.get("/api/clientes").json()) == 1
    assert len(auth.get("/api/vehiculos").json()) == 1


def _crear_orden_recibida(auth, folio_sufijo="A"):
    payload = {
        "cliente": {"nombre": "Test", "apellido": f"Orden{folio_sufijo}", "telefono": f"81000000{folio_sufijo}0",
                    "acepta_promociones": False},
        "vehiculo": {"placas": f"ORD-00{folio_sufijo}-Z", "marca": "Mazda", "modelo": "3", "anio": 2020,
                     "transmision": "Manual"},
        "visita": {
            "fecha": date.today().isoformat(), "hora_inicio": "08:00", "hora_fin": "10:00",
            "hora_entrada": "08:05", "hora_prometida": "12:00", "kilometraje": 5000,
            "motivo_ingreso": "Prueba",
        },
    }
    return auth.post("/api/recepcion", json=payload).json()["id_orden"]


# ===========================================================================
# Ciclo de vida de una orden
# ===========================================================================

def test_no_se_puede_saltar_una_etapa(auth):
    id_orden = _crear_orden_recibida(auth, "1")
    r = auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": "Terminado"})
    assert r.status_code == 409


def test_no_se_puede_entregar_sin_costo(auth):
    id_orden = _crear_orden_recibida(auth, "2")
    for etapa in ["En diagnóstico", "En reparación", "Terminado"]:
        assert auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": etapa}).status_code == 200
    r = auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": "Entregado"})
    assert r.status_code == 409


def test_agregar_refaccion_recalcula_costo_total(auth):
    id_orden = _crear_orden_recibida(auth, "3")
    r = auth.post(f"/api/ordenes/{id_orden}/refacciones", json={"id_refaccion": 1, "cantidad": 2})
    assert r.status_code == 201
    assert r.json()["costo_total"] == 2500.0     # REF-0001 = 1250.00 x 2

    orden = next(o for o in auth.get("/api/ordenes").json() if o["id_orden"] == id_orden)
    detalle = orden["detalle"][0]
    r2 = auth.delete(f"/api/ordenes/{id_orden}/refacciones/{detalle['id_detalle']}")
    assert r2.status_code == 200
    assert r2.json()["costo_total"] == 0.0


def test_ciclo_completo_hasta_entregado(auth):
    id_orden = _crear_orden_recibida(auth, "4")
    for etapa in ["En diagnóstico", "En reparación"]:
        auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": etapa})
    auth.post(f"/api/ordenes/{id_orden}/refacciones", json={"id_refaccion": 2, "cantidad": 1})
    auth.patch(f"/api/ordenes/{id_orden}", json={"costo_mano_obra": 500})
    auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": "Terminado"})
    r = auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": "Entregado"})
    assert r.status_code == 200

    entregada = next(o for o in auth.get("/api/ordenes_historicas").json())
    assert entregada["estatus"] == "Entregado"
    assert entregada["costo_total"] > 0


def test_eliminar_orden_recien_creada_ok(auth):
    id_orden = _crear_orden_recibida(auth, "5")
    r = auth.delete(f"/api/ordenes/{id_orden}")
    assert r.status_code == 200
    assert auth.get("/api/ordenes").json() == []


def test_eliminar_orden_avanzada_bloqueado(auth):
    id_orden = _crear_orden_recibida(auth, "6")
    auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": "En diagnóstico"})
    r = auth.delete(f"/api/ordenes/{id_orden}")
    assert r.status_code == 409


# ===========================================================================
# Tablero / reportes
# ===========================================================================

def test_dashboard_rango_por_omision(auth):
    r = auth.get("/api/dashboard")
    assert r.status_code == 200
    datos = r.json()
    assert len(datos["ingresosMensuales"]) == 7
    assert "resumenPeriodo" in datos


def test_dashboard_rango_de_12_meses(auth):
    r = auth.get("/api/dashboard", params={"meses": 13})
    assert r.status_code == 200
    assert len(r.json()["ingresosMensuales"]) == 13


# ===========================================================================
# Reportes en PDF
# ===========================================================================

def test_reporte_diario_pdf(auth):
    r = auth.get("/api/reportes/diario.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_reporte_placa_pdf(auth, vehiculo_id):
    r = auth.get(f"/api/reportes/placa/{vehiculo_id}.pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_reporte_placa_pdf_vehiculo_inexistente_404(auth):
    r = auth.get("/api/reportes/placa/9999.pdf")
    assert r.status_code == 404


def test_reporte_mensual_pdf(auth):
    r = auth.get("/api/reportes/mensual.pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
