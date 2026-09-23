/* ==========================================================================
   VMotors - Carga de datos reales
   --------------------------------------------------------------------------
   Este archivo ya NO contiene datos hardcodeados: al cargar la pagina pide
   los arreglos (clientes, vehiculos, citas, ordenes...) a la API del backend
   (FastAPI + SQLite) y llena el objeto VM con exactamente la misma forma que
   antes tenia el mockup, para que el resto del codigo de cada pantalla
   (app.js y los scripts de cada *.html) no tuviera que cambiar.
   ========================================================================== */

const VM = {};

/* -------------------------------------------------------------------------
   Catalogos estaticos (no dependen de la base de datos)
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

/* Fecha y hora "de ahora": se calculan del reloj real del navegador, en el
   mismo formato "YYYY-MM-DD" / "YYYY-MM-DD HH:MM:SS" que usa la base. */
function _pad(n) { return String(n).padStart(2, "0"); }
(function fijarReloj() {
  const d = new Date();
  VM.HOY = `${d.getFullYear()}-${_pad(d.getMonth() + 1)}-${_pad(d.getDate())}`;
  VM.AHORA = `${VM.HOY} ${_pad(d.getHours())}:${_pad(d.getMinutes())}:${_pad(d.getSeconds())}`;
})();

/* -------------------------------------------------------------------------
   Arreglos que llena la API (vacios hasta que resuelva vmCargarDatos)
   ------------------------------------------------------------------------- */
VM.clientes = [];
VM.vehiculos = [];
VM.citas = [];
VM.refacciones = [];
VM.ordenes = [];
VM.ordenes_historicas = [];
VM.ingresosMensuales = [];
VM.serviciosPorSemana = [];
VM.tiposServicio = [];
VM.resumenPeriodo = { facturacion: 0, ordenesCerradas: 0, ticketPromedio: 0, diasPromedioTaller: 0 };
VM.alertas = [];

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
  if (!orden) return null;
  const cita = VM.cita(orden.id_cita);
  const veh  = cita ? VM.vehiculo(cita.id_vehiculo) : null;
  const cli  = veh  ? VM.cliente(veh.id_cliente)    : null;
  return { ...orden, cita, vehiculo: veh, cliente: cli };
};

VM.ordenesExpandidas = () => VM.ordenes.map(VM.ordenExpandida);

VM.vehiculosDeCliente = (id) => VM.vehiculos.filter(v => v.id_cliente === id);

VM.citasDeVehiculo = (id) => VM.citas.filter(c => c.id_vehiculo === id);

VM.ordenDeCita = (idCita) => VM.ordenes.find(o => o.id_cita === idCita);

/* -------------------------------------------------------------------------
   Carga desde la API
   ------------------------------------------------------------------------- */
async function _fetchJSON(url) {
  const r = await fetch(url, { credentials: "same-origin" });
  if (r.status === 401) throw new Error("401");
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

async function vmCargarDatos() {
  const [clientes, vehiculos, citas, refacciones, ordenes, historicas, alertas, tablero] =
    await Promise.all([
      _fetchJSON("/api/clientes"),
      _fetchJSON("/api/vehiculos"),
      _fetchJSON("/api/citas"),
      _fetchJSON("/api/refacciones"),
      _fetchJSON("/api/ordenes"),
      _fetchJSON("/api/ordenes_historicas"),
      _fetchJSON("/api/alertas"),
      _fetchJSON("/api/dashboard"),
    ]);

  VM.clientes = clientes;
  VM.vehiculos = vehiculos;
  VM.citas = citas;
  VM.refacciones = refacciones;
  VM.ordenes = ordenes;
  VM.ordenes_historicas = historicas;
  VM.alertas = alertas;
  VM.ingresosMensuales = tablero.ingresosMensuales;
  VM.serviciosPorSemana = tablero.serviciosPorSemana;
  VM.tiposServicio = tablero.tiposServicio;
  VM.resumenPeriodo = tablero.resumenPeriodo;
}

/* Vuelve a pedir solo el tablero, con un rango de meses distinto al que
   trajo vmCargarDatos() al inicio (usado por el selector 6/12 meses). */
async function vmCargarDashboard(meses) {
  const tablero = await _fetchJSON(`/api/dashboard?meses=${meses}`);
  VM.ingresosMensuales = tablero.ingresosMensuales;
  VM.serviciosPorSemana = tablero.serviciosPorSemana;
  VM.tiposServicio = tablero.tiposServicio;
  VM.resumenPeriodo = tablero.resumenPeriodo;
}

/* VM.listo: promesa que el resto de la app espera antes de pintar nada.
   Las paginas sin data-page (por ahora, solo login.html) no piden datos. */
VM.listo = (async () => {
  const pagina = document.body && document.body.dataset ? document.body.dataset.page : null;
  if (!pagina) return;
  try {
    await vmCargarDatos();
  } catch (err) {
    if (err.message === "401") {
      window.location.href = "login.html";
      return new Promise(() => {}); // no seguir pintando esta pagina
    }
    console.error("No se pudieron cargar los datos de VMotors:", err);
    document.body.innerHTML =
      '<div style="padding:40px;font:14px/1.6 system-ui">' +
      '<h2>No fue posible conectar con el servidor de VMotors</h2>' +
      '<p>Verifique que el backend esté corriendo y vuelva a intentar.</p></div>';
    return new Promise(() => {});
  }
})();
