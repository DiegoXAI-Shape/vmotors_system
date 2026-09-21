"""
VMotors - Generador de datos ficticios (compartido)
====================================================

Contiene los catalogos, constantes y la clase `Generador` que producen un
conjunto de datos ficticios coherente con Faker. No depende de ningun motor
de base de datos: tanto `seed_database.py` (PostgreSQL) como `seed_sqlite.py`
(SQLite) importan este modulo para no duplicar la logica de generacion.
"""

from __future__ import annotations

import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal

try:
    from faker import Faker
except ImportError:  # pragma: no cover
    sys.exit("Falta la dependencia 'Faker'. Ejecute: pip install -r requirements.txt")


# ===========================================================================
# Catalogos y constantes
# ===========================================================================

#: Etapas del ciclo de vida de una orden, en el orden estricto del flujo.
ETAPAS = [
    "Pendiente",
    "Recibido",
    "En diagnóstico",
    "En reparación",
    "Terminado",
    "Entregado",
]

ESTATUS_CITA = ["Agendada", "Cancelada", "Atendida"]
FORMAS_PAGO = ["Efectivo", "Tarjeta", "Transferencia", "Cheque"]
TRANSMISIONES = ["Manual", "Automático"]

#: Bloques horarios que ofrece el taller (jornada de 08:00 a 19:00).
BLOQUES = [time(h, 0) for h in range(8, 18)]

MUNICIPIOS_NL = [
    "Monterrey", "San Nicolás de los Garza", "Guadalupe", "Apodaca",
    "General Escobedo", "Santa Catarina", "San Pedro Garza García",
    "Juárez", "García", "Cadereyta Jiménez",
]

CATALOGO_VEHICULOS = {
    "Nissan":     ["Versa", "March", "Sentra", "Frontier", "X-Trail"],
    "Chevrolet":  ["Aveo", "Onix", "Silverado", "Captiva", "Beat"],
    "Ford":       ["Ranger", "Transit", "Figo", "Escape", "F-150"],
    "Toyota":     ["Hilux", "Corolla", "Yaris", "RAV4", "Tacoma"],
    "Volkswagen": ["Jetta", "Vento", "Tiguan", "Polo", "Saveiro"],
    "Honda":      ["Civic", "City", "CR-V", "HR-V", "Fit"],
    "Mazda":      ["CX-5", "Mazda 3", "CX-30", "Mazda 2"],
    "Kia":        ["Rio", "Forte", "Sportage", "Seltos"],
    "Hyundai":    ["Creta", "Accent", "Tucson", "Grand i10"],
    "Seat":       ["Ibiza", "León", "Arona"],
    "Renault":    ["Duster", "Kwid", "Logan", "Oroch"],
    "Jeep":       ["Compass", "Renegade", "Wrangler"],
}

MOTORES = [
    "1.6L 4 cil.", "1.8L 4 cil.", "2.0L 4 cil.", "2.5L 4 cil.",
    "2.7L 4 cil.", "3.2L Diesel", "2.2L Diesel", "5.3L V8", "2.0L Turbo",
]

COLORES = ["Blanco", "Negro", "Gris", "Plata", "Rojo", "Azul", "Verde", "Café", "Arena"]

#: Catalogo fijo de refacciones (clave, descripcion, categoria, precio).
REFACCIONES = [
    ("REF-0001", "Balatas delanteras cerámicas (juego)", "Frenos", "1250.00"),
    ("REF-0002", "Balatas traseras semimetálicas (juego)", "Frenos", "980.00"),
    ("REF-0003", "Disco de freno ventilado", "Frenos", "980.00"),
    ("REF-0004", "Líquido de frenos DOT 4 (litro)", "Frenos", "195.00"),
    ("REF-0005", "Aceite sintético 5W-30 (litro)", "Lubricantes", "240.00"),
    ("REF-0006", "Aceite mineral 20W-50 (litro)", "Lubricantes", "150.00"),
    ("REF-0007", "Filtro de aceite", "Filtros", "185.00"),
    ("REF-0008", "Filtro de aire de motor", "Filtros", "320.00"),
    ("REF-0009", "Filtro de cabina", "Filtros", "290.00"),
    ("REF-0010", "Filtro de combustible", "Filtros", "410.00"),
    ("REF-0011", "Bujía de iridio", "Encendido", "265.00"),
    ("REF-0012", "Bobina de encendido", "Encendido", "1490.00"),
    ("REF-0013", "Cable de bujía (juego)", "Encendido", "680.00"),
    ("REF-0014", "Amortiguador delantero", "Suspensión", "1890.00"),
    ("REF-0015", "Amortiguador trasero", "Suspensión", "1720.00"),
    ("REF-0016", "Buje de horquilla inferior", "Suspensión", "540.00"),
    ("REF-0017", "Rótula inferior", "Suspensión", "760.00"),
    ("REF-0018", "Batería 12V 65Ah", "Eléctrico", "2890.00"),
    ("REF-0019", "Alternador reconstruido", "Eléctrico", "4350.00"),
    ("REF-0020", "Motor de arranque", "Eléctrico", "3980.00"),
    ("REF-0021", "Compresor de A/C", "Climas", "6450.00"),
    ("REF-0022", "Gas refrigerante R-134a (kg)", "Climas", "480.00"),
    ("REF-0023", "Filtro deshidratador", "Climas", "890.00"),
    ("REF-0024", "Kit de clutch completo", "Transmisión", "7300.00"),
    ("REF-0025", "Aceite de transmisión ATF (litro)", "Transmisión", "310.00"),
    ("REF-0026", "Banda de distribución", "Motor", "1650.00"),
    ("REF-0027", "Bomba de agua", "Motor", "2180.00"),
    ("REF-0028", "Termostato", "Motor", "620.00"),
    ("REF-0029", "Junta de cabeza", "Motor", "1980.00"),
    ("REF-0030", "Radiador", "Motor", "3750.00"),
]

MOTIVOS = [
    "Servicio de mantenimiento programado de {km} km.",
    "Ruido metálico al frenar; solicita revisión de balatas y discos.",
    "Testigo de motor encendido de forma intermitente.",
    "Vibración en el volante a velocidad de carretera.",
    "El aire acondicionado no enfría correctamente.",
    "Fuga de aceite visible en el estacionamiento.",
    "Dificultad para arrancar en frío.",
    "Cambio de aceite y filtros.",
    "Alineación y balanceo de las cuatro ruedas.",
    "Revisión de suspensión por golpeteo en topes.",
    "El clutch se siente bajo y patina en subidas.",
    "Sobrecalentamiento del motor en tráfico lento.",
    "Revisión general previa a viaje largo.",
    "Cambio de batería; la unidad no enciende.",
    "Consumo excesivo de combustible reportado por el cliente.",
]

DIAGNOSTICOS = [
    "Se confirma la falla reportada. Se sustituyen las piezas desgastadas y se realiza prueba dinámica sin observaciones.",
    "Componentes dentro de tolerancia; únicamente se aplica servicio de mantenimiento y limpieza del sistema.",
    "Desgaste severo por kilometraje. Se reemplazan las refacciones indicadas y se recomienda revisión en 10,000 km.",
    "Se detecta fuga en el sistema. Se sustituyen sellos y se recarga el sistema conforme a especificación del fabricante.",
    "Escaneo de módulos con código almacenado. Se corrige la causa raíz y se borran los códigos de falla.",
    "Se realiza afinación completa, limpieza de inyectores y ajuste de la marcha mínima.",
    "Pieza sustituida bajo garantía del proveedor. Se documenta el número de serie en la bitácora del taller.",
    "Se aprieta a torque especificado y se verifica geometría de la suspensión en el equipo de alineación.",
]

NOTAS_ETAPA = {
    "Pendiente": ["Cita confirmada con el cliente.", "Solicitud de servicio registrada en mostrador.", "Cita agendada por teléfono."],
    "Recibido": ["Unidad recibida en bahía; se registra kilometraje e inventario.", "Ingreso de la unidad y entrega de llaves.", "Recepción física conforme al formato F-01."],
    "En diagnóstico": ["Revisión en rampa por el jefe de cuadrilla.", "Escaneo OBD-II y prueba de ruta.", "Inspección visual y medición de componentes."],
    "En reparación": ["Trabajo autorizado por el cliente.", "Refacciones surtidas por el proveedor.", "Se inicia el desmontaje de los componentes."],
    "Terminado": ["Prueba dinámica satisfactoria; cliente notificado.", "Trabajos concluidos y unidad lavada.", "Verificación final aprobada."],
    "Entregado": ["Pago recibido y firma de conformidad.", "Unidad entregada al propietario.", "Comprobante F-02 impreso y entregado."],
}


# ===========================================================================
# Generador de datos en memoria
# ===========================================================================

class Generador:
    """Construye en memoria un conjunto coherente de registros."""

    def __init__(self, fake: Faker, rnd: random.Random, hoy: date):
        self.fake = fake
        self.rnd = rnd
        self.hoy = hoy
        self.clientes: list[tuple] = []
        self.vehiculos: list[tuple] = []
        self.citas: list[tuple] = []
        self.ordenes: list[tuple] = []
        self.detalle: list[tuple] = []
        self.historial: list[tuple] = []
        self._bloques_ocupados: set[tuple[date, time]] = set()
        self._placas_usadas: set[str] = set()
        self._telefonos: set[str] = set()
        self._rfcs: set[str] = set()
        self._correos: set[str] = set()

    # ---------------------------------------------------------------- utiles
    def _telefono(self) -> str:
        while True:
            tel = "81" + "".join(str(self.rnd.randint(0, 9)) for _ in range(8))
            if tel not in self._telefonos:
                self._telefonos.add(tel)
                return tel

    def _rfc(self) -> str:
        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        alfanum = letras + "0123456789"
        while True:
            rfc = (
                "".join(self.rnd.choice(letras) for _ in range(4))
                + f"{self.rnd.randint(70, 99):02d}"
                + f"{self.rnd.randint(1, 12):02d}"
                + f"{self.rnd.randint(1, 28):02d}"
                + "".join(self.rnd.choice(alfanum) for _ in range(3))
            )
            if rfc not in self._rfcs:
                self._rfcs.add(rfc)
                return rfc

    def _correo(self, nombre: str, apellido: str) -> str:
        base = f"{nombre.split()[0]}.{apellido.split()[0]}".lower()
        base = (base.replace("á", "a").replace("é", "e").replace("í", "i")
                    .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
        dominio = self.rnd.choice(["gmail.com", "outlook.com", "hotmail.com", "correo.mx", "yahoo.com.mx"])
        i = 0
        while True:
            correo = f"{base}{'' if i == 0 else i}@{dominio}"
            if correo not in self._correos:
                self._correos.add(correo)
                return correo
            i += 1

    def _generar_placas(self) -> str:
        letras = "ABCDEFGHJKLMNPRSTUVWXYZ"
        while True:
            p = (
                "".join(self.rnd.choice(letras) for _ in range(3))
                + "-" + f"{self.rnd.randint(100, 999)}"
                + "-" + self.rnd.choice(letras)
            )
            if p not in self._placas_usadas:
                self._placas_usadas.add(p)
                return p

    def _bloque_libre(self, fecha: date, saltos: int = 12) -> tuple[date, time] | None:
        """Busca un bloque horario disponible en la fecha dada o en los días siguientes.

        Con ``saltos=1`` la búsqueda se limita al día solicitado, que es lo que
        necesitan la agenda de hoy y las citas futuras para no desplazarse.
        """
        for salto in range(0, max(1, saltos)):
            dia = fecha + timedelta(days=salto)
            if dia.weekday() == 6:       # el taller no abre en domingo
                continue
            libres = [h for h in BLOQUES if (dia, h) not in self._bloques_ocupados]
            if libres:
                hora = self.rnd.choice(libres)
                self._bloques_ocupados.add((dia, hora))
                return dia, hora
        return None

    # ------------------------------------------------------------- generacion
    def generar_clientes(self, cuantos: int) -> None:
        for i in range(1, cuantos + 1):
            nombre = self.fake.first_name()
            apellido = f"{self.fake.last_name()} {self.fake.last_name()}"
            es_empresa = self.rnd.random() < 0.22
            tiene_rfc = es_empresa or self.rnd.random() < 0.55
            tiene_correo = self.rnd.random() < 0.85

            self.clientes.append((
                i,
                nombre,
                apellido,
                self.fake.company() if es_empresa else None,
                self._rfc() if tiene_rfc else None,
                self._telefono(),
                self._telefono() if es_empresa or self.rnd.random() < 0.25 else None,
                self._correo(nombre, apellido) if tiene_correo else None,
                tiene_correo and self.rnd.random() < 0.6,
                self.fake.street_name()[:120],
                str(self.rnd.randint(1, 4999)),
                self.fake.city()[:100],
                self.rnd.choice(MUNICIPIOS_NL),
                "Nuevo León",
                f"{self.rnd.randint(64000, 67999)}",
                self._fecha_hora_pasada(dias_max=780),
            ))

    def _fecha_hora_pasada(self, dias_max: int) -> datetime:
        dias = self.rnd.randint(1, dias_max)
        base = self.hoy - timedelta(days=dias)
        return datetime.combine(base, time(self.rnd.randint(8, 18), self.rnd.choice([0, 15, 30, 45])))

    def generar_vehiculos(self) -> None:
        id_veh = 0
        for cliente in self.clientes:
            id_cliente = cliente[0]
            alta_cliente = cliente[15]
            # Una flotilla (cliente con razon social) suele tener mas unidades
            maximo = 4 if cliente[3] else 3
            for _ in range(self.rnd.randint(1, maximo)):
                id_veh += 1
                marca = self.rnd.choice(list(CATALOGO_VEHICULOS))
                self.vehiculos.append((
                    id_veh,
                    id_cliente,
                    self._generar_placas(),
                    marca,
                    self.rnd.choice(CATALOGO_VEHICULOS[marca]),
                    self.rnd.randint(2008, self.hoy.year),
                    self.rnd.choice(COLORES),
                    self.rnd.choice(TRANSMISIONES),
                    self.rnd.choice(MOTORES),
                    alta_cliente,
                ))

    def generar_citas_y_ordenes(self) -> None:
        id_cita = 0
        id_orden = 0
        id_detalle = 0
        folio_n = 0

        # La agenda se arma en tres tramos para que la base refleje una
        # operación viva: historial cerrado, trabajo de hoy y turnos futuros.
        ids_vehiculos = [v[0] for v in self.vehiculos]
        agenda: list[tuple[int, date, int]] = []

        # (a) Historial: visitas cerradas de los últimos dos años.
        for id_vehiculo in ids_vehiculos:
            for _ in range(self.rnd.randint(1, 5)):
                dias = self.rnd.randint(-730, -7)
                agenda.append((id_vehiculo, self.hoy + timedelta(days=dias), 12))

        # (b) Hoy: unidades que están físicamente en el taller.
        for id_vehiculo in self.rnd.sample(ids_vehiculos, min(7, len(ids_vehiculos))):
            agenda.append((id_vehiculo, self.hoy, 1))

        # (c) Próximas semanas: turnos ya comprometidos en el calendario.
        futuros = min(30, len(ids_vehiculos))
        for id_vehiculo in self.rnd.sample(ids_vehiculos, futuros):
            agenda.append((id_vehiculo, self.hoy + timedelta(days=self.rnd.randint(1, 18)), 1))

        agenda.sort(key=lambda x: x[1])

        km_por_vehiculo: dict[int, int] = {}

        for id_vehiculo, fecha_deseada, saltos in agenda:
            bloque = self._bloque_libre(fecha_deseada, saltos)
            if bloque is None:
                continue
            fecha, hora_inicio = bloque
            duracion = self.rnd.choice([1, 1, 2, 2, 3])
            hora_fin = time(min(hora_inicio.hour + duracion, 19), 0)
            if hora_fin <= hora_inicio:
                continue

            id_cita += 1
            km_previo = km_por_vehiculo.get(id_vehiculo, self.rnd.randint(8000, 90000))
            km = km_previo + self.rnd.randint(1500, 12000)
            km_por_vehiculo[id_vehiculo] = km
            motivo = self.rnd.choice(MOTIVOS).format(km=f"{(km // 10000) * 10000:,}")

            # ---- estatus de la cita segun su posicion en el tiempo ----
            if fecha > self.hoy:
                estatus_cita = "Cancelada" if self.rnd.random() < 0.06 else "Agendada"
            elif fecha == self.hoy:
                estatus_cita = "Atendida"
            else:
                estatus_cita = "Cancelada" if self.rnd.random() < 0.05 else "Atendida"

            if estatus_cita == "Cancelada":
                # Una cita cancelada libera su bloque horario
                self._bloques_ocupados.discard((fecha, hora_inicio))

            self.citas.append((
                id_cita, id_vehiculo, fecha, hora_inicio, hora_fin, motivo, estatus_cita,
                datetime.combine(fecha - timedelta(days=self.rnd.randint(1, 12)),
                                 time(self.rnd.randint(8, 18), 0)),
            ))

            # ---- ¿la cita deriva en una orden de servicio? ----
            if estatus_cita == "Cancelada":
                continue
            # Sólo las citas próximas tienen ya una orden abierta en estatus
            # "Pendiente"; el resto del calendario aún no genera expediente.
            if estatus_cita == "Agendada" and not (
                fecha <= self.hoy + timedelta(days=4) and self.rnd.random() < 0.6
            ):
                continue

            if fecha < self.hoy - timedelta(days=10):
                # El historial antiguo siempre está cerrado y liquidado.
                estatus = "Entregado"
            elif fecha < self.hoy:
                # Los últimos días pueden conservar unidades ya terminadas
                # que el cliente todavía no recoge.
                estatus = "Entregado" if self.rnd.random() < 0.8 else "Terminado"
            elif fecha == self.hoy:
                estatus = self.rnd.choice(["Recibido", "En diagnóstico", "En reparación",
                                           "En reparación", "Terminado"])
            else:
                estatus = "Pendiente"

            id_orden += 1
            folio_n += 1
            ingreso = datetime.combine(fecha, hora_inicio) + timedelta(minutes=self.rnd.randint(0, 25))
            prometida = datetime.combine(fecha, hora_fin) + timedelta(hours=self.rnd.choice([0, 0, 2, 5, 24]))

            avance = ETAPAS.index(estatus)
            con_refacciones = avance >= ETAPAS.index("En reparación")

            # ---- desglose de refacciones ----
            mano_obra = Decimal("0.00")
            refacciones_orden: list[tuple[int, int, Decimal]] = []
            if con_refacciones:
                elegidas = self.rnd.sample(range(1, len(REFACCIONES) + 1),
                                           self.rnd.randint(1, 4))
                for id_refaccion in elegidas:
                    precio = Decimal(REFACCIONES[id_refaccion - 1][3])
                    cantidad = self.rnd.choice([1, 1, 1, 2, 2, 4, 6])
                    refacciones_orden.append((id_refaccion, cantidad, precio))
                mano_obra = Decimal(self.rnd.randrange(35000, 480000, 500)) / 100

            costo_refacciones = sum((c * p for _, c, p in refacciones_orden), Decimal("0.00"))
            costo_total = (mano_obra + costo_refacciones).quantize(Decimal("0.01"))

            entrega = None
            if estatus == "Entregado":
                entrega = prometida + timedelta(minutes=self.rnd.randint(-90, 240))
                if entrega < ingreso:
                    entrega = ingreso + timedelta(hours=2)
                if costo_total <= 0:   # la restriccion exige importe mayor a cero
                    mano_obra = Decimal(self.rnd.randrange(45000, 150000, 500)) / 100
                    costo_total = (mano_obra + costo_refacciones).quantize(Decimal("0.01"))

            diagnostico = self.rnd.choice(DIAGNOSTICOS) if avance >= ETAPAS.index("En diagnóstico") else None

            self.ordenes.append((
                id_orden,
                id_cita,
                f"OS-{fecha.year}-{folio_n:04d}",
                ingreso,
                prometida,
                entrega,
                km,
                self.rnd.randint(0, 8),
                self.rnd.choice(FORMAS_PAGO),
                diagnostico,
                estatus,
                mano_obra.quantize(Decimal("0.01")),
                costo_refacciones.quantize(Decimal("0.01")),
                costo_total,
            ))

            for id_refaccion, cantidad, precio in refacciones_orden:
                id_detalle += 1
                self.detalle.append((id_detalle, id_orden, id_refaccion, cantidad, precio))

            # ---- bitacora de transiciones ----
            momento = ingreso - timedelta(days=self.rnd.randint(1, 6))
            anterior = None
            for etapa in ETAPAS[: avance + 1]:
                self.historial.append((
                    id_orden, anterior, etapa, momento,
                    "administrador", self.rnd.choice(NOTAS_ETAPA[etapa]),
                ))
                anterior = etapa
                momento = momento + timedelta(minutes=self.rnd.randint(45, 600))
                if entrega and momento > entrega:
                    momento = entrega
