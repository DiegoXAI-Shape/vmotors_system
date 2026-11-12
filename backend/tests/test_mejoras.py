"""Pruebas de las mejoras de la segunda entrega: envio de comprobante por
correo, portal del cliente (segundo rol), recordatorios de mantenimiento,
avisos de seguimiento y resumen mensual para el dueno."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

PLACAS = "POR-123-A"
TELEFONO = "8112345678"


def _orden(auth, *, correo="cliente@ejemplo.com", placas=PLACAS, telefono=TELEFONO, acepta=True, hora=10):
    payload = {
        "cliente": {"nombre": "Laura", "apellido": "Garza", "telefono": telefono, "correo": correo,
                    "acepta_promociones": acepta},
        "vehiculo": {"placas": placas, "marca": "Toyota", "modelo": "Corolla", "anio": 2019,
                     "transmision": "Automático"},
        "visita": {
            "fecha": date.today().isoformat(), "hora_inicio": f"{hora:02d}:00", "hora_fin": f"{hora + 1:02d}:00",
            "hora_entrada": f"{hora:02d}:05", "hora_prometida": "17:00", "kilometraje": 45000,
            "motivo_ingreso": "Servicio de frenos",
        },
    }
    r = auth.post("/api/recepcion", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _bandeja(auth):
    return auth.get("/api/correos").json()


def _entregar(auth, id_orden):
    for etapa in ["En diagnóstico", "En reparación", "Terminado"]:
        assert auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": etapa}).status_code == 200
    auth.patch(f"/api/ordenes/{id_orden}", json={"costo_mano_obra": 800, "diagnostico": "Cambio de balatas"})
    return auth.patch(f"/api/ordenes/{id_orden}", json={"estatus": "Entregado"})


# ---------------------------------------------------------------------------
# Comprobante por correo
# ---------------------------------------------------------------------------

def test_enviar_comprobante_al_correo_del_cliente(auth):
    datos = _orden(auth)
    r = auth.post(f"/api/ordenes/{datos['id_orden']}/comprobante/enviar", json={})
    assert r.status_code == 200
    assert r.json()["ok"] is True and r.json()["modo"] == "simulado"
    ultimo = _bandeja(auth)[0]
    assert ultimo["tipo"] == "comprobante" and ultimo["destinatario"] == "cliente@ejemplo.com"
    assert ultimo["adjunto"].endswith(".pdf")
    detalle = auth.get(f"/api/correos/{ultimo['id_correo']}").json()
    assert datos["folio"] in detalle["cuerpo_html"]


def test_comprobante_a_otro_destinatario(auth):
    datos = _orden(auth)
    r = auth.post(f"/api/ordenes/{datos['id_orden']}/comprobante/enviar", json={"destinatario": "yo@uanl.edu.mx"})
    assert r.json()["destinatario"] == "yo@uanl.edu.mx"


def test_comprobante_sin_correo_registrado_409(auth):
    datos = _orden(auth, correo=None)
    r = auth.post(f"/api/ordenes/{datos['id_orden']}/comprobante/enviar", json={})
    assert r.status_code == 409


def test_descargar_comprobante_pdf(auth):
    datos = _orden(auth)
    r = auth.get(f"/api/ordenes/{datos['id_orden']}/comprobante.pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Seguimiento automatico
# ---------------------------------------------------------------------------

def test_aviso_al_terminar_y_comprobante_al_entregar(auth):
    datos = _orden(auth)
    r = _entregar(auth, datos["id_orden"])
    assert r.status_code == 200
    assert r.json()["notificacion"]["ok"] is True
    tipos = [c["tipo"] for c in _bandeja(auth)]
    assert tipos[:2] == ["comprobante", "seguimiento"]


def test_sin_correo_no_hay_aviso_y_la_orden_avanza_igual(auth):
    datos = _orden(auth, correo=None)
    assert _entregar(auth, datos["id_orden"]).status_code == 200
    assert _bandeja(auth) == []


def test_avisos_automaticos_se_pueden_apagar(auth, monkeypatch):
    monkeypatch.setenv("NOTIFICACIONES_AUTOMATICAS", "0")
    datos = _orden(auth)
    _entregar(auth, datos["id_orden"])
    assert _bandeja(auth) == []


# ---------------------------------------------------------------------------
# Portal del cliente
# ---------------------------------------------------------------------------

def test_portal_login_y_estatus_del_vehiculo(client, auth):
    datos = _orden(auth)
    auth.post("/api/auth/logout")

    r = client.post("/api/portal/login", json={"placas": "por 123 a", "telefono": "(81) 1234-5678"})
    assert r.json() == {"ok": True, "nombre": "Laura"}

    info = client.get("/api/portal/mis-vehiculos").json()
    v = info["vehiculos"][0]
    assert v["placas"] == PLACAS
    assert v["orden_activa"]["folio"] == datos["folio"]
    assert v["orden_activa"]["estatus"] == "Recibido"
    assert v["orden_activa"]["etapa"] == 1


def test_portal_datos_incorrectos(client, auth):
    _orden(auth)
    auth.post("/api/auth/logout")
    r = client.post("/api/portal/login", json={"placas": PLACAS, "telefono": "8100000000"})
    assert r.json()["ok"] is False
    assert client.get("/api/portal/mis-vehiculos").status_code == 401


def test_cliente_no_puede_usar_la_api_del_administrador(client, auth):
    _orden(auth)
    auth.post("/api/auth/logout")
    client.post("/api/portal/login", json={"placas": PLACAS, "telefono": TELEFONO})
    for ruta in ("/api/clientes", "/api/ordenes", "/api/correos", "/api/reportes/mensual.pdf"):
        assert client.get(ruta).status_code == 401, ruta


def test_cliente_solo_descarga_sus_comprobantes(client, auth):
    propia = _orden(auth)
    ajena = _orden(auth, placas="AJE-999-B", telefono="8199998888", correo="otro@ejemplo.com", hora=14)
    auth.post("/api/auth/logout")
    client.post("/api/portal/login", json={"placas": PLACAS, "telefono": TELEFONO})
    assert client.get(f"/api/portal/ordenes/{propia['id_orden']}/comprobante.pdf").status_code == 200
    assert client.get(f"/api/portal/ordenes/{ajena['id_orden']}/comprobante.pdf").status_code == 404


# ---------------------------------------------------------------------------
# Recordatorios de mantenimiento
# ---------------------------------------------------------------------------

def _envejecer_visita(db_path, id_orden, meses=8):
    vieja = (datetime.now() - timedelta(days=int(meses * 30.44))).strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(db_path)
    con.execute("UPDATE ordenes_servicio SET estatus='Entregado', fecha_entrega=?, costo_total=900 "
                "WHERE id_orden=?", (vieja, id_orden))
    con.commit()
    con.close()


def test_recordatorios_a_unidades_en_alerta(auth, db_path):
    con_permiso = _orden(auth)
    sin_permiso = _orden(auth, placas="SIN-111-C", telefono="8177776666", correo="no@ejemplo.com", acepta=False, hora=14)
    _envejecer_visita(db_path, con_permiso["id_orden"])
    _envejecer_visita(db_path, sin_permiso["id_orden"])

    r = auth.post("/api/alertas/recordatorios", json={}).json()
    assert r["enviados"] == 1 and r["omitidos"] == 1

    # Un segundo envio inmediato no repite el recordatorio (limite de 30 dias)
    r2 = auth.post("/api/alertas/recordatorios", json={}).json()
    assert r2["enviados"] == 0
    assert r2["resultados"][0]["ok"] is False


def test_recordatorio_forzado_a_correo_de_prueba(auth, db_path):
    datos = _orden(auth)
    _envejecer_visita(db_path, datos["id_orden"])
    r = auth.post("/api/alertas/recordatorios", json={
        "ids_vehiculo": [datos["id_vehiculo"]], "destinatario": "prueba@uanl.edu.mx", "forzar": True}).json()
    assert r["enviados"] == 1
    assert _bandeja(auth)[0]["destinatario"] == "prueba@uanl.edu.mx"


# ---------------------------------------------------------------------------
# Resumen mensual para el dueno
# ---------------------------------------------------------------------------

def test_reporte_mensual_requiere_destinatario(auth):
    assert auth.post("/api/reportes/mensual/enviar", json={}).status_code == 409


def test_reporte_mensual_al_dueno(auth, monkeypatch):
    monkeypatch.setenv("CORREO_DUENO", "dueno@vmotors.mx")
    r = auth.post("/api/reportes/mensual/enviar", json={})
    assert r.status_code == 200 and r.json()["destinatario"] == "dueno@vmotors.mx"
    assert _bandeja(auth)[0]["tipo"] == "reporte_mensual"


def test_envio_mensual_programado_solo_una_vez(auth, monkeypatch):
    from app.reporte_mensual import revisar_envio_programado
    monkeypatch.setenv("CORREO_DUENO", "dueno@vmotors.mx")
    assert revisar_envio_programado() is not None
    assert revisar_envio_programado() is None
    assert len([c for c in _bandeja(auth) if c["tipo"] == "reporte_mensual"]) == 1


# ---------------------------------------------------------------------------
# Envio real solo a destinatarios autorizados (CORREOS_REALES)
# ---------------------------------------------------------------------------

class _SMTPFalso:
    """Sustituye a smtplib.SMTP: registra lo que se 'envia' sin red."""
    enviados: list = []

    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self, **k): pass
    def login(self, *a): pass
    def send_message(self, msg): _SMTPFalso.enviados.append(msg["To"])


def _smtp_activo(monkeypatch, reales=""):
    import app.correo as c
    _SMTPFalso.enviados = []
    monkeypatch.setattr(c.smtplib, "SMTP", _SMTPFalso)
    monkeypatch.setenv("SMTP_HOST", "smtp.ejemplo.com")
    monkeypatch.setenv("SMTP_USER", "taller@ejemplo.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("CORREOS_REALES", reales)


def test_correo_de_muestra_no_sale_aunque_haya_smtp(auth, monkeypatch):
    _smtp_activo(monkeypatch, reales="isaid@uanl.edu.mx")
    datos = _orden(auth)  # cliente@ejemplo.com, como los datos de muestra
    r = auth.post(f"/api/ordenes/{datos['id_orden']}/comprobante/enviar", json={}).json()
    assert r["ok"] is True and r["modo"] == "simulado"
    assert _SMTPFalso.enviados == []
    assert _bandeja(auth)[0]["modo"] == "simulado"


def test_correo_autorizado_sale_por_smtp(auth, monkeypatch):
    _smtp_activo(monkeypatch, reales="isaid@uanl.edu.mx")
    datos = _orden(auth)
    r = auth.post(f"/api/ordenes/{datos['id_orden']}/comprobante/enviar",
                  json={"destinatario": "Isaid@UANL.edu.mx"}).json()
    assert r["modo"] == "smtp"
    assert [d.lower() for d in _SMTPFalso.enviados] == ["isaid@uanl.edu.mx"]


def test_reglas_de_correos_reales(monkeypatch):
    import app.correo as c
    monkeypatch.setenv("SMTP_HOST", "smtp.ejemplo.com")
    monkeypatch.setenv("CORREOS_REALES", "@uanl.edu.mx; yo@gmail.com")
    monkeypatch.setenv("CORREO_DUENO", "dueno@vmotors.mx")
    assert c.envio_real_permitido("alumno@uanl.edu.mx")
    assert c.envio_real_permitido("yo@gmail.com")
    assert c.envio_real_permitido("dueno@vmotors.mx")
    assert not c.envio_real_permitido("jorge.alarcon@gmail.com")
    assert not c.envio_real_permitido("x@notuanl.edu.mx")
    monkeypatch.setenv("CORREOS_REALES", "*")
    assert c.envio_real_permitido("cualquiera@hotmail.com")
    monkeypatch.delenv("SMTP_HOST")
    assert not c.envio_real_permitido("cualquiera@hotmail.com")


def test_fallo_smtp_queda_registrado(auth, monkeypatch):
    import app.correo as c
    _smtp_activo(monkeypatch, reales="*")

    class _Caido(_SMTPFalso):
        def login(self, *a):
            raise c.smtplib.SMTPAuthenticationError(535, b"Usuario o contrasena incorrectos")

    monkeypatch.setattr(c.smtplib, "SMTP", _Caido)
    datos = _orden(auth)
    r = auth.post(f"/api/ordenes/{datos['id_orden']}/comprobante/enviar", json={}).json()
    assert r["ok"] is False and "SMTPAuthenticationError" in r["error"]
    assert _bandeja(auth)[0]["estado"] == "fallido"
