/* ==========================================================================
   VMotors - Datos de ejemplo (mockup)
   --------------------------------------------------------------------------
   ESTE ARCHIVO NO CONSULTA NINGUNA BASE DE DATOS.
   Es un conjunto de registros hardcodeados cuya forma imita exactamente el
   esquema definido en Fase III / Fase IV (clientes, vehiculos, citas,
   ordenes_servicio, refacciones, orden_refacciones, historial_estatus), de
   modo que mas adelante baste con sustituir estos arreglos por la respuesta
   de un backend real.
   ========================================================================== */

const VM = {};

/* Fecha y hora "de ahora" del prototipo. Todas las vistas se calculan respecto a ellas. */
VM.HOY   = "2026-09-10";
VM.AHORA = "2026-09-10 14:30";

/* -------------------------------------------------------------------------
   Catalogos
   ------------------------------------------------------------------------- */
VM.ESTATUS_ORDEN = [
  { key: "Pendiente",     label: "Pendiente",      color: "var(--st-pendiente)",   cls: "st-pendiente"   },
  { key: "Recibido",      label: "Recibido",       color: "var(--st-recibido)",    cls: "st-recibido"    },
  { key: "En diagnóstico",label: "En diagnóstico", color: "var(--st-diagnostico)", cls: "st-diagnostico" },
  { key: "En reparación", label: "En reparación",  color: "var(--st-reparacion)",  cls: "st-reparacion"  },
  { key: "Terminado",     label: "Terminado",      color: "var(--st-terminado)",   cls: "st-terminado"   },
  { key: "Entregado",     label: "Entregado",      color: "var(--st-entregado)",   cls: "st-entregado"   }
];

VM.ESTATUS_CITA = {
  "Agendada":  { cls: "st-agendada",  label: "Agendada"  },
  "Atendida":  { cls: "st-atendida",  label: "Atendida"  },
  "Cancelada": { cls: "st-cancelada", label: "Cancelada" }
};

VM.BLOQUES_HORARIOS = ["08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"];

VM.FORMAS_PAGO = ["Efectivo", "Tarjeta", "Transferencia", "Cheque"];

/* -------------------------------------------------------------------------
   Tabla: clientes
   ------------------------------------------------------------------------- */
VM.clientes = [
  { id_cliente: 1,  nombre: "Alejandra", apellido: "Treviño Salinas",   razon_social: "Distribuidora Treviño S.A. de C.V.", rfc: "DTR980412H21", telefono: "8112045577", telefono_oficina: "8183456601", correo: "alejandra.trevino@correo.mx", acepta_promociones: true,  calle: "Av. Miguel Alemán", numero: "1450", colonia: "Del Prado", municipio: "San Nicolás de los Garza", estado: "Nuevo León", codigo_postal: "66450", fecha_registro: "2024-02-18 10:12" },
  { id_cliente: 2,  nombre: "Ricardo",   apellido: "Ontiveros Lara",    razon_social: null, rfc: "OOLR900311KJ2", telefono: "8119887744", telefono_oficina: null, correo: "r.ontiveros@gmail.com", acepta_promociones: true,  calle: "Calle Zaragoza", numero: "218", colonia: "Centro", municipio: "Monterrey", estado: "Nuevo León", codigo_postal: "64000", fecha_registro: "2024-05-03 16:40" },
  { id_cliente: 3,  nombre: "María Fernanda", apellido: "Cantú Robles", razon_social: null, rfc: null, telefono: "8123310098", telefono_oficina: null, correo: "mfcantu@outlook.com", acepta_promociones: false, calle: "Paseo de los Leones", numero: "3320", colonia: "Cumbres 2do Sector", municipio: "Monterrey", estado: "Nuevo León", codigo_postal: "64610", fecha_registro: "2024-07-21 09:05" },
  { id_cliente: 4,  nombre: "Jorge",     apellido: "Guerrero Peña",     razon_social: "Logística Guerrero", rfc: "GUPJ870225TR8", telefono: "8114472299", telefono_oficina: "8183991245", correo: "jguerrero@logisticagp.mx", acepta_promociones: true,  calle: "Carr. Miguel Alemán km 12", numero: "S/N", colonia: "Parque Industrial", municipio: "Apodaca", estado: "Nuevo León", codigo_postal: "66600", fecha_registro: "2024-09-14 12:33" },
  { id_cliente: 5,  nombre: "Diana",     apellido: "Villarreal Cruz",   razon_social: null, rfc: "VICD950718PL4", telefono: "8188120043", telefono_oficina: null, correo: "diana.villarreal@correo.mx", acepta_promociones: false, calle: "Río Nazas", numero: "745", colonia: "Roma", municipio: "Guadalupe", estado: "Nuevo León", codigo_postal: "67130", fecha_registro: "2024-11-02 18:20" },
  { id_cliente: 6,  nombre: "Luis Ángel", apellido: "Márquez Díaz",     razon_social: null, rfc: null, telefono: "8117760011", telefono_oficina: null, correo: null, acepta_promociones: false, calle: "Av. Chapultepec", numero: "902", colonia: "Buenos Aires", municipio: "Monterrey", estado: "Nuevo León", codigo_postal: "64800", fecha_registro: "2025-01-27 11:48" },
  { id_cliente: 7,  nombre: "Patricia",  apellido: "Zamora Hinojosa",   razon_social: "Refrigeración Zamora", rfc: "RZA010930MN6", telefono: "8125540877", telefono_oficina: "8181117744", correo: "contacto@refrizamora.com", acepta_promociones: true,  calle: "Ruiz Cortines", numero: "5510", colonia: "Valle de Santa Lucía", municipio: "Escobedo", estado: "Nuevo León", codigo_postal: "66050", fecha_registro: "2025-02-11 08:55" },
  { id_cliente: 8,  nombre: "Emiliano",  apellido: "Rangel Fuentes",    razon_social: null, rfc: "RAFE920106QW1", telefono: "8113398820", telefono_oficina: null, correo: "emiliano.rangel@correo.mx", acepta_promociones: true,  calle: "Priv. Los Encinos", numero: "112", colonia: "Contry", municipio: "Monterrey", estado: "Nuevo León", codigo_postal: "64860", fecha_registro: "2025-03-30 15:10" },
  { id_cliente: 9,  nombre: "Sofía",     apellido: "Elizondo Mora",     razon_social: null, rfc: null, telefono: "8190042215", telefono_oficina: null, correo: "sofia.elizondo@correo.mx", acepta_promociones: false, calle: "Hidalgo", numero: "88", colonia: "Centro", municipio: "Santa Catarina", estado: "Nuevo León", codigo_postal: "66350", fecha_registro: "2025-04-22 13:02" },
  { id_cliente: 10, nombre: "Héctor",    apellido: "Salazar Núñez",     razon_social: "Transportes HSN", rfc: "THS110615FG3", telefono: "8116673311", telefono_oficina: "8182203399", correo: "hector@transporteshsn.mx", acepta_promociones: true,  calle: "Av. Las Torres", numero: "2201", colonia: "Industrial", municipio: "Guadalupe", estado: "Nuevo León", codigo_postal: "67100", fecha_registro: "2025-05-19 17:37" },
  { id_cliente: 11, nombre: "Gabriela",  apellido: "Ibarra Montes",     razon_social: null, rfc: "IAMG880504ZX9", telefono: "8114409987", telefono_oficina: null, correo: "gaby.ibarra@correo.mx", acepta_promociones: true,  calle: "Lázaro Cárdenas", numero: "1810", colonia: "Residencial San Agustín", municipio: "San Pedro Garza García", estado: "Nuevo León", codigo_postal: "66260", fecha_registro: "2025-06-08 10:44" },
  { id_cliente: 12, nombre: "Andrés",    apellido: "Perales Vega",      razon_social: null, rfc: null, telefono: "8128871190", telefono_oficina: null, correo: "andres.perales@correo.mx", acepta_promociones: false, calle: "Julián Villagrán", numero: "430", colonia: "Mitras Centro", municipio: "Monterrey", estado: "Nuevo León", codigo_postal: "64460", fecha_registro: "2025-07-15 09:28" },
  { id_cliente: 13, nombre: "Norma",     apellido: "Escobedo Ruiz",     razon_social: null, rfc: "EORN930822BH5", telefono: "8111203366", telefono_oficina: null, correo: "norma.escobedo@correo.mx", acepta_promociones: true,  calle: "Av. Universidad", numero: "615", colonia: "Anáhuac", municipio: "San Nicolás de los Garza", estado: "Nuevo León", codigo_postal: "66450", fecha_registro: "2025-08-26 14:19" },
  { id_cliente: 14, nombre: "Iván",      apellido: "Solís Bermúdez",    razon_social: null, rfc: null, telefono: "8199330077", telefono_oficina: null, correo: null, acepta_promociones: false, calle: "Camino Real", numero: "77", colonia: "La Fe", municipio: "San Nicolás de los Garza", estado: "Nuevo León", codigo_postal: "66477", fecha_registro: "2026-01-09 16:03" }
];

/* -------------------------------------------------------------------------
   Tabla: vehiculos
   ------------------------------------------------------------------------- */
VM.vehiculos = [
  { id_vehiculo: 1,  id_cliente: 1,  placas: "SXK-472-A", marca: "Nissan",     modelo: "Versa",      anio: 2019, color: "Blanco",   transmision: "Automático", motor: "1.6L 4 cil." },
  { id_vehiculo: 2,  id_cliente: 1,  placas: "TRB-118-C", marca: "Toyota",     modelo: "Hilux",      anio: 2022, color: "Gris",     transmision: "Manual",     motor: "2.7L 4 cil." },
  { id_vehiculo: 3,  id_cliente: 2,  placas: "PMD-903-B", marca: "Chevrolet",  modelo: "Aveo",       anio: 2016, color: "Rojo",     transmision: "Manual",     motor: "1.6L 4 cil." },
  { id_vehiculo: 4,  id_cliente: 3,  placas: "LKW-556-D", marca: "Mazda",      modelo: "CX-5",       anio: 2021, color: "Azul",     transmision: "Automático", motor: "2.5L 4 cil." },
  { id_vehiculo: 5,  id_cliente: 4,  placas: "GHT-201-F", marca: "Ford",       modelo: "Ranger",     anio: 2020, color: "Negro",    transmision: "Automático", motor: "3.2L Diesel" },
  { id_vehiculo: 6,  id_cliente: 4,  placas: "GHT-202-F", marca: "Ford",       modelo: "Transit",    anio: 2018, color: "Blanco",   transmision: "Manual",     motor: "2.2L Diesel" },
  { id_vehiculo: 7,  id_cliente: 5,  placas: "NBV-774-H", marca: "Volkswagen", modelo: "Jetta",      anio: 2017, color: "Plata",    transmision: "Automático", motor: "2.0L 4 cil." },
  { id_vehiculo: 8,  id_cliente: 6,  placas: "QAZ-330-J", marca: "Honda",      modelo: "Civic",      anio: 2015, color: "Gris",     transmision: "Manual",     motor: "1.8L 4 cil." },
  { id_vehiculo: 9,  id_cliente: 7,  placas: "WSX-641-K", marca: "Chevrolet",  modelo: "Silverado",  anio: 2023, color: "Blanco",   transmision: "Automático", motor: "5.3L V8" },
  { id_vehiculo: 10, id_cliente: 8,  placas: "EDC-092-L", marca: "Kia",        modelo: "Rio",        anio: 2020, color: "Rojo",     transmision: "Manual",     motor: "1.6L 4 cil." },
  { id_vehiculo: 11, id_cliente: 9,  placas: "RFV-885-M", marca: "Nissan",     modelo: "March",      anio: 2014, color: "Verde",    transmision: "Manual",     motor: "1.6L 4 cil." },
  { id_vehiculo: 12, id_cliente: 10, placas: "TGB-317-N", marca: "Freightliner", modelo: "M2 106",   anio: 2019, color: "Blanco",   transmision: "Manual",     motor: "6.7L Diesel" },
  { id_vehiculo: 13, id_cliente: 10, placas: "TGB-318-N", marca: "Isuzu",      modelo: "ELF 600",    anio: 2021, color: "Blanco",   transmision: "Manual",     motor: "5.2L Diesel" },
  { id_vehiculo: 14, id_cliente: 11, placas: "YHN-450-P", marca: "Audi",       modelo: "A3",         anio: 2022, color: "Negro",    transmision: "Automático", motor: "2.0L Turbo" },
  { id_vehiculo: 15, id_cliente: 12, placas: "UJM-726-Q", marca: "Seat",       modelo: "Ibiza",      anio: 2018, color: "Azul",     transmision: "Manual",     motor: "1.6L 4 cil." },
  { id_vehiculo: 16, id_cliente: 13, placas: "IKO-238-R", marca: "Hyundai",    modelo: "Creta",      anio: 2021, color: "Plata",    transmision: "Automático", motor: "1.8L 4 cil." },
  { id_vehiculo: 17, id_cliente: 14, placas: "OLP-961-S", marca: "Renault",    modelo: "Duster",     anio: 2019, color: "Café",     transmision: "Manual",     motor: "2.0L 4 cil." },
  { id_vehiculo: 18, id_cliente: 3,  placas: "ZAQ-514-T", marca: "Jeep",       modelo: "Compass",    anio: 2023, color: "Blanco",   transmision: "Automático", motor: "2.4L 4 cil." }
];

/* -------------------------------------------------------------------------
   Tabla: citas
   ------------------------------------------------------------------------- */
VM.citas = [
  { id_cita: 101, id_vehiculo: 5,  fecha: "2026-09-10", hora_inicio: "08:00", hora_fin: "10:00", motivo_ingreso: "Servicio mayor de 60,000 km y revisión de suspensión delantera.", estatus_cita: "Atendida" },
  { id_cita: 102, id_vehiculo: 4,  fecha: "2026-09-10", hora_inicio: "09:00", hora_fin: "11:00", motivo_ingreso: "Ruido metálico al frenar, revisión de balatas y discos.", estatus_cita: "Atendida" },
  { id_cita: 103, id_vehiculo: 9,  fecha: "2026-09-10", hora_inicio: "10:00", hora_fin: "13:00", motivo_ingreso: "Falla intermitente de encendido, testigo de motor encendido.", estatus_cita: "Atendida" },
  { id_cita: 104, id_vehiculo: 1,  fecha: "2026-09-10", hora_inicio: "11:00", hora_fin: "12:00", motivo_ingreso: "Cambio de aceite y filtros, afinación menor.", estatus_cita: "Atendida" },
  { id_cita: 105, id_vehiculo: 14, fecha: "2026-09-10", hora_inicio: "13:00", hora_fin: "15:00", motivo_ingreso: "Revisión de aire acondicionado, no enfría.", estatus_cita: "Atendida" },
  { id_cita: 106, id_vehiculo: 12, fecha: "2026-09-10", hora_inicio: "15:00", hora_fin: "17:00", motivo_ingreso: "Mantenimiento preventivo de frenos de aire.", estatus_cita: "Agendada" },
  { id_cita: 107, id_vehiculo: 7,  fecha: "2026-09-11", hora_inicio: "08:00", hora_fin: "09:00", motivo_ingreso: "Cambio de batería y revisión de alternador.", estatus_cita: "Agendada" },
  { id_cita: 108, id_vehiculo: 10, fecha: "2026-09-11", hora_inicio: "10:00", hora_fin: "12:00", motivo_ingreso: "Vibración en volante a más de 90 km/h.", estatus_cita: "Agendada" },
  { id_cita: 109, id_vehiculo: 16, fecha: "2026-09-11", hora_inicio: "13:00", hora_fin: "14:00", motivo_ingreso: "Alineación y balanceo.", estatus_cita: "Agendada" },
  { id_cita: 110, id_vehiculo: 3,  fecha: "2026-09-11", hora_inicio: "15:00", hora_fin: "17:00", motivo_ingreso: "Fuga de refrigerante, revisión de radiador.", estatus_cita: "Cancelada" },
  { id_cita: 111, id_vehiculo: 18, fecha: "2026-09-12", hora_inicio: "09:00", hora_fin: "11:00", motivo_ingreso: "Servicio de 20,000 km.", estatus_cita: "Agendada" },
  { id_cita: 112, id_vehiculo: 2,  fecha: "2026-09-12", hora_inicio: "11:00", hora_fin: "13:00", motivo_ingreso: "Cambio de clutch, pedal muy suave.", estatus_cita: "Agendada" },
  { id_cita: 113, id_vehiculo: 13, fecha: "2026-09-12", hora_inicio: "14:00", hora_fin: "16:00", motivo_ingreso: "Revisión de sistema eléctrico, luces intermitentes.", estatus_cita: "Agendada" },
  { id_cita: 114, id_vehiculo: 8,  fecha: "2026-09-14", hora_inicio: "08:00", hora_fin: "10:00", motivo_ingreso: "Cambio de bomba de agua y termostato.", estatus_cita: "Agendada" },
  { id_cita: 115, id_vehiculo: 15, fecha: "2026-09-14", hora_inicio: "10:00", hora_fin: "11:00", motivo_ingreso: "Diagnóstico por consumo excesivo de gasolina.", estatus_cita: "Agendada" },
  { id_cita: 116, id_vehiculo: 17, fecha: "2026-09-15", hora_inicio: "09:00", hora_fin: "12:00", motivo_ingreso: "Reparación de transmisión, cuesta entrar segunda velocidad.", estatus_cita: "Agendada" },
  { id_cita: 117, id_vehiculo: 11, fecha: "2026-09-15", hora_inicio: "13:00", hora_fin: "14:00", motivo_ingreso: "Cambio de aceite.", estatus_cita: "Agendada" },
  { id_cita: 118, id_vehiculo: 6,  fecha: "2026-09-09", hora_inicio: "08:00", hora_fin: "11:00", motivo_ingreso: "Servicio de frenos y cambio de amortiguadores traseros.", estatus_cita: "Atendida" },
  { id_cita: 119, id_vehiculo: 16, fecha: "2026-09-08", hora_inicio: "09:00", hora_fin: "10:00", motivo_ingreso: "Cambio de balatas delanteras.", estatus_cita: "Atendida" },
  { id_cita: 120, id_vehiculo: 1,  fecha: "2026-03-04", hora_inicio: "10:00", hora_fin: "12:00", motivo_ingreso: "Afinación mayor y cambio de bujías.", estatus_cita: "Atendida" },
  { id_cita: 121, id_vehiculo: 8,  fecha: "2026-02-17", hora_inicio: "11:00", hora_fin: "13:00", motivo_ingreso: "Reemplazo de embrague.", estatus_cita: "Atendida" },
  { id_cita: 122, id_vehiculo: 11, fecha: "2026-01-23", hora_inicio: "08:00", hora_fin: "09:00", motivo_ingreso: "Cambio de aceite y filtro.", estatus_cita: "Atendida" },
  { id_cita: 123, id_vehiculo: 15, fecha: "2026-02-05", hora_inicio: "14:00", hora_fin: "16:00", motivo_ingreso: "Revisión de suspensión trasera.", estatus_cita: "Atendida" },
  { id_cita: 124, id_vehiculo: 3,  fecha: "2026-01-14", hora_inicio: "09:00", hora_fin: "11:00", motivo_ingreso: "Cambio de banda de distribución.", estatus_cita: "Atendida" },
  { id_cita: 125, id_vehiculo: 17, fecha: "2026-03-19", hora_inicio: "13:00", hora_fin: "15:00", motivo_ingreso: "Servicio de 40,000 km.", estatus_cita: "Atendida" }
];

/* -------------------------------------------------------------------------
   Tabla: refacciones (catalogo)
   ------------------------------------------------------------------------- */
VM.refacciones = [
  { id_refaccion: 1,  clave: "REF-0001", descripcion: "Balatas delanteras cerámicas (juego)", categoria: "Frenos",      precio_unitario: 1250.00 },
  { id_refaccion: 2,  clave: "REF-0002", descripcion: "Disco de freno ventilado",             categoria: "Frenos",      precio_unitario: 980.00  },
  { id_refaccion: 3,  clave: "REF-0003", descripcion: "Aceite sintético 5W-30 (litro)",       categoria: "Lubricantes", precio_unitario: 240.00  },
  { id_refaccion: 4,  clave: "REF-0004", descripcion: "Filtro de aceite",                     categoria: "Filtros",     precio_unitario: 185.00  },
  { id_refaccion: 5,  clave: "REF-0005", descripcion: "Filtro de aire de motor",              categoria: "Filtros",     precio_unitario: 320.00  },
  { id_refaccion: 6,  clave: "REF-0006", descripcion: "Bujía de iridio",                      categoria: "Encendido",   precio_unitario: 265.00  },
  { id_refaccion: 7,  clave: "REF-0007", descripcion: "Bobina de encendido",                  categoria: "Encendido",   precio_unitario: 1490.00 },
  { id_refaccion: 8,  clave: "REF-0008", descripcion: "Amortiguador trasero",                 categoria: "Suspensión",  precio_unitario: 1720.00 },
  { id_refaccion: 9,  clave: "REF-0009", descripcion: "Batería 12V 65Ah",                     categoria: "Eléctrico",   precio_unitario: 2890.00 },
  { id_refaccion: 10, clave: "REF-0010", descripcion: "Compresor de A/C",                     categoria: "Climas",      precio_unitario: 6450.00 },
  { id_refaccion: 11, clave: "REF-0011", descripcion: "Gas refrigerante R-134a (kg)",         categoria: "Climas",      precio_unitario: 480.00  },
  { id_refaccion: 12, clave: "REF-0012", descripcion: "Kit de clutch completo",               categoria: "Transmisión", precio_unitario: 7300.00 }
];

/* -------------------------------------------------------------------------
   Tabla: ordenes_servicio  (+ detalle de refacciones e historial)
   ------------------------------------------------------------------------- */
VM.ordenes = [
  {
    id_orden: 5001, folio: "OS-2026-0501", id_cita: 101,
    fecha_ingreso: "2026-09-10 08:05", hora_prometida: "2026-09-10 14:00", fecha_entrega: null,
    kilometraje: 61240, nivel_combustible: 5, forma_pago: "Transferencia",
    estatus: "En reparación",
    diagnostico: "Se detecta desgaste severo en bujes de horquilla inferior derecha y fuga leve en amortiguador delantero izquierdo. Se autoriza reemplazo de ambos elementos junto con el servicio mayor programado.",
    costo_mano_obra: 2400.00, costo_refacciones: 3665.00, costo_total: 6065.00,
    detalle: [ { id_refaccion: 3, cantidad: 6, precio_unitario: 240.00 }, { id_refaccion: 4, cantidad: 1, precio_unitario: 185.00 }, { id_refaccion: 5, cantidad: 1, precio_unitario: 320.00 }, { id_refaccion: 8, cantidad: 1, precio_unitario: 1720.00 } ],
    historial: [
      { estatus: "Pendiente",      fecha: "2026-09-09 17:20", nota: "Cita confirmada por teléfono." },
      { estatus: "Recibido",       fecha: "2026-09-10 08:05", nota: "Unidad recibida, 5/8 de combustible, sin pertenencias declaradas." },
      { estatus: "En diagnóstico", fecha: "2026-09-10 08:40", nota: "Revisión en rampa por jefe de cuadrilla." },
      { estatus: "En reparación",  fecha: "2026-09-10 10:15", nota: "Cliente autoriza refacciones vía WhatsApp." }
    ]
  },
  {
    id_orden: 5002, folio: "OS-2026-0502", id_cita: 102,
    fecha_ingreso: "2026-09-10 09:12", hora_prometida: "2026-09-10 13:00", fecha_entrega: null,
    kilometraje: 38900, nivel_combustible: 3, forma_pago: "Tarjeta",
    estatus: "En diagnóstico",
    diagnostico: "Balatas delanteras al límite de espesor. Pendiente rectificar o sustituir discos según medición con micrómetro.",
    costo_mano_obra: 0.00, costo_refacciones: 0.00, costo_total: 0.00,
    detalle: [],
    historial: [
      { estatus: "Pendiente",      fecha: "2026-09-08 12:00", nota: "Cita agendada en mostrador." },
      { estatus: "Recibido",       fecha: "2026-09-10 09:12", nota: "Unidad recibida en bahía 2." },
      { estatus: "En diagnóstico", fecha: "2026-09-10 09:35", nota: "Desmontaje de rines para inspección." }
    ]
  },
  {
    id_orden: 5003, folio: "OS-2026-0503", id_cita: 103,
    fecha_ingreso: "2026-09-10 10:03", hora_prometida: "2026-09-11 12:00", fecha_entrega: null,
    kilometraje: 24150, nivel_combustible: 6, forma_pago: "Efectivo",
    estatus: "En reparación",
    diagnostico: "Código P0303 (falla de encendido cilindro 3). Bobina con resistencia fuera de rango y bujías con depósitos de carbón. Se sustituye bobina y juego completo de bujías.",
    costo_mano_obra: 1600.00, costo_refacciones: 3610.00, costo_total: 5210.00,
    detalle: [ { id_refaccion: 7, cantidad: 1, precio_unitario: 1490.00 }, { id_refaccion: 6, cantidad: 8, precio_unitario: 265.00 } ],
    historial: [
      { estatus: "Pendiente",      fecha: "2026-09-07 09:00", nota: "Solicitud de servicio registrada." },
      { estatus: "Recibido",       fecha: "2026-09-10 10:03", nota: "Ingreso de unidad." },
      { estatus: "En diagnóstico", fecha: "2026-09-10 10:25", nota: "Escaneo OBD-II." },
      { estatus: "En reparación",  fecha: "2026-09-10 11:40", nota: "Refacción surtida por proveedor local." }
    ]
  },
  {
    id_orden: 5004, folio: "OS-2026-0504", id_cita: 104,
    fecha_ingreso: "2026-09-10 11:02", hora_prometida: "2026-09-10 12:30", fecha_entrega: null,
    kilometraje: 92800, nivel_combustible: 2, forma_pago: "Efectivo",
    estatus: "Terminado",
    diagnostico: "Servicio de mantenimiento realizado sin observaciones adicionales. Se recomienda revisión de amortiguadores en el próximo servicio.",
    costo_mano_obra: 650.00, costo_refacciones: 1705.00, costo_total: 2355.00,
    detalle: [ { id_refaccion: 3, cantidad: 5, precio_unitario: 240.00 }, { id_refaccion: 4, cantidad: 1, precio_unitario: 185.00 }, { id_refaccion: 5, cantidad: 1, precio_unitario: 320.00 } ],
    historial: [
      { estatus: "Pendiente",      fecha: "2026-09-06 10:10", nota: "Cita agendada en línea." },
      { estatus: "Recibido",       fecha: "2026-09-10 11:02", nota: "Ingreso de unidad." },
      { estatus: "En diagnóstico", fecha: "2026-09-10 11:15", nota: "Inspección de niveles." },
      { estatus: "En reparación",  fecha: "2026-09-10 11:30", nota: "Cambio de aceite y filtros." },
      { estatus: "Terminado",      fecha: "2026-09-10 12:20", nota: "Prueba dinámica satisfactoria. Cliente notificado." }
    ]
  },
  {
    id_orden: 5005, folio: "OS-2026-0505", id_cita: 105,
    fecha_ingreso: "2026-09-10 13:08", hora_prometida: "2026-09-11 17:00", fecha_entrega: null,
    kilometraje: 15420, nivel_combustible: 7, forma_pago: "Tarjeta",
    estatus: "Recibido",
    diagnostico: null,
    costo_mano_obra: 0.00, costo_refacciones: 0.00, costo_total: 0.00,
    detalle: [],
    historial: [
      { estatus: "Pendiente", fecha: "2026-09-05 15:30", nota: "Cita agendada." },
      { estatus: "Recibido",  fecha: "2026-09-10 13:08", nota: "Unidad en espera de bahía de diagnóstico." }
    ]
  },
  {
    id_orden: 5006, folio: "OS-2026-0506", id_cita: 118,
    fecha_ingreso: "2026-09-09 08:10", hora_prometida: "2026-09-09 16:00", fecha_entrega: "2026-09-09 15:40",
    kilometraje: 118300, nivel_combustible: 4, forma_pago: "Transferencia",
    estatus: "Entregado",
    diagnostico: "Se sustituyen balatas delanteras y amortiguadores traseros. Se realiza purga del sistema de frenos y prueba de carretera sin observaciones.",
    costo_mano_obra: 2100.00, costo_refacciones: 4690.00, costo_total: 6790.00,
    detalle: [ { id_refaccion: 1, cantidad: 1, precio_unitario: 1250.00 }, { id_refaccion: 8, cantidad: 2, precio_unitario: 1720.00 } ],
    historial: [
      { estatus: "Pendiente",      fecha: "2026-09-04 11:00", nota: "Cita agendada." },
      { estatus: "Recibido",       fecha: "2026-09-09 08:10", nota: "Ingreso de unidad." },
      { estatus: "En diagnóstico", fecha: "2026-09-09 08:45", nota: "Inspección de tren delantero." },
      { estatus: "En reparación",  fecha: "2026-09-09 10:00", nota: "Trabajo autorizado por el cliente." },
      { estatus: "Terminado",      fecha: "2026-09-09 14:50", nota: "Prueba de frenado aprobada." },
      { estatus: "Entregado",      fecha: "2026-09-09 15:40", nota: "Pago recibido por transferencia. Firma de conformidad." }
    ]
  },
  {
    id_orden: 5007, folio: "OS-2026-0507", id_cita: 119,
    fecha_ingreso: "2026-09-08 09:05", hora_prometida: "2026-09-08 12:00", fecha_entrega: "2026-09-08 11:30",
    kilometraje: 47200, nivel_combustible: 5, forma_pago: "Efectivo",
    estatus: "Entregado",
    diagnostico: "Sustitución de balatas delanteras. Discos dentro de tolerancia, no requieren rectificado.",
    costo_mano_obra: 700.00, costo_refacciones: 1250.00, costo_total: 1950.00,
    detalle: [ { id_refaccion: 1, cantidad: 1, precio_unitario: 1250.00 } ],
    historial: [
      { estatus: "Pendiente",      fecha: "2026-09-03 16:20", nota: "Cita agendada." },
      { estatus: "Recibido",       fecha: "2026-09-08 09:05", nota: "Ingreso de unidad." },
      { estatus: "En diagnóstico", fecha: "2026-09-08 09:20", nota: "Medición de espesor de balata." },
      { estatus: "En reparación",  fecha: "2026-09-08 09:50", nota: "Reemplazo de balatas." },
      { estatus: "Terminado",      fecha: "2026-09-08 11:05", nota: "Prueba dinámica." },
      { estatus: "Entregado",      fecha: "2026-09-08 11:30", nota: "Entrega al cliente." }
    ]
  },
  {
    id_orden: 5008, folio: "OS-2026-0508", id_cita: 106,
    fecha_ingreso: "2026-09-10 15:00", hora_prometida: "2026-09-12 13:00", fecha_entrega: null,
    kilometraje: 240100, nivel_combustible: 4, forma_pago: "Transferencia",
    estatus: "Pendiente",
    diagnostico: null,
    costo_mano_obra: 0.00, costo_refacciones: 0.00, costo_total: 0.00,
    detalle: [],
    historial: [ { estatus: "Pendiente", fecha: "2026-09-02 09:40", nota: "Cita confirmada con flotilla." } ]
  }
];

/* Ordenes historicas (cerradas) usadas por reportes e historial por placa */
VM.ordenes_historicas = [
  { folio: "OS-2026-0188", id_vehiculo: 1,  fecha_entrega: "2026-03-04 16:10", estatus: "Entregado", diagnostico: "Afinación mayor, cambio de bujías y limpieza de cuerpo de aceleración.", kilometraje: 84300, costo_total: 3450.00 },
  { folio: "OS-2026-0151", id_vehiculo: 8,  fecha_entrega: "2026-02-17 18:00", estatus: "Entregado", diagnostico: "Reemplazo de kit de embrague completo.", kilometraje: 165900, costo_total: 11200.00 },
  { folio: "OS-2026-0119", id_vehiculo: 11, fecha_entrega: "2026-01-23 11:20", estatus: "Entregado", diagnostico: "Cambio de aceite y filtro, revisión general de niveles.", kilometraje: 132400, costo_total: 1180.00 },
  { folio: "OS-2026-0142", id_vehiculo: 15, fecha_entrega: "2026-02-05 17:35", estatus: "Entregado", diagnostico: "Sustitución de bujes de barra estabilizadora trasera.", kilometraje: 98700, costo_total: 2640.00 },
  { folio: "OS-2026-0107", id_vehiculo: 3,  fecha_entrega: "2026-01-14 15:05", estatus: "Entregado", diagnostico: "Cambio de banda de distribución, bomba de agua y tensor.", kilometraje: 152300, costo_total: 8950.00 },
  { folio: "OS-2026-0203", id_vehiculo: 17, fecha_entrega: "2026-03-19 16:45", estatus: "Entregado", diagnostico: "Servicio de 40,000 km conforme a manual del fabricante.", kilometraje: 41200, costo_total: 2890.00 }
];

/* -------------------------------------------------------------------------
   Series para los graficos del tablero
   ------------------------------------------------------------------------- */
VM.ingresosMensuales = [
  { mes: "Mar", valor: 148300 }, { mes: "Abr", valor: 131900 }, { mes: "May", valor: 162400 },
  { mes: "Jun", valor: 155800 }, { mes: "Jul", valor: 178600 }, { mes: "Ago", valor: 192150 },
  { mes: "Sep", valor: 74200 }
];

VM.serviciosPorSemana = [
  { sem: "S31", valor: 18 }, { sem: "S32", valor: 22 }, { sem: "S33", valor: 19 },
  { sem: "S34", valor: 26 }, { sem: "S35", valor: 24 }, { sem: "S36", valor: 29 }, { sem: "S37", valor: 12 }
];

VM.tiposServicio = [
  { nombre: "Frenos",            valor: 34 },
  { nombre: "Mantenimiento",     valor: 28 },
  { nombre: "Motor / eléctrico", valor: 21 },
  { nombre: "Suspensión",        valor: 14 },
  { nombre: "Transmisión",       valor: 9  },
  { nombre: "Aire acondicionado",valor: 6  }
];

/* -------------------------------------------------------------------------
   Alertas de mantenimiento preventivo (ciclo semestral - Fase IV)
   ------------------------------------------------------------------------- */
VM.alertas = [
  { id_vehiculo: 3,  ultima_visita: "2026-01-14", meses: 7.9, servicio_sugerido: "Afinación y revisión de frenos", prioridad: "alta"  },
  { id_vehiculo: 11, ultima_visita: "2026-01-23", meses: 7.6, servicio_sugerido: "Cambio de aceite y filtros",     prioridad: "alta"  },
  { id_vehiculo: 15, ultima_visita: "2026-02-05", meses: 7.2, servicio_sugerido: "Revisión de suspensión",         prioridad: "alta"  },
  { id_vehiculo: 8,  ultima_visita: "2026-02-17", meses: 6.8, servicio_sugerido: "Servicio de 170,000 km",         prioridad: "media" },
  { id_vehiculo: 1,  ultima_visita: "2026-03-04", meses: 6.2, servicio_sugerido: "Afinación menor",                prioridad: "media" },
  { id_vehiculo: 17, ultima_visita: "2026-03-19", meses: 5.8, servicio_sugerido: "Servicio de 50,000 km",          prioridad: "baja"  }
];

/* -------------------------------------------------------------------------
   Helpers de consulta (equivalen a los JOIN del modelo relacional)
   ------------------------------------------------------------------------- */
VM.cliente     = (id) => VM.clientes.find(c => c.id_cliente === id);
VM.vehiculo    = (id) => VM.vehiculos.find(v => v.id_vehiculo === id);
VM.cita        = (id) => VM.citas.find(c => c.id_cita === id);
VM.refaccion   = (id) => VM.refacciones.find(r => r.id_refaccion === id);
VM.orden       = (id) => VM.ordenes.find(o => o.id_orden === id);

VM.nombreCliente = (c) => c ? `${c.nombre} ${c.apellido}` : "-";

/* Devuelve la orden con cita, vehiculo y cliente resueltos en un solo objeto */
VM.ordenExpandida = (orden) => {
  const cita = VM.cita(orden.id_cita);
  const veh  = cita ? VM.vehiculo(cita.id_vehiculo) : null;
  const cli  = veh  ? VM.cliente(veh.id_cliente)    : null;
  return { ...orden, cita, vehiculo: veh, cliente: cli };
};

VM.ordenesExpandidas = () => VM.ordenes.map(VM.ordenExpandida);

VM.vehiculosDeCliente = (id) => VM.vehiculos.filter(v => v.id_cliente === id);

VM.citasDeVehiculo = (id) => VM.citas.filter(c => c.id_vehiculo === id);

VM.ordenDeCita = (idCita) => VM.ordenes.find(o => o.id_cita === idCita);
