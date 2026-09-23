/* ==========================================================================
   VMotors - Capa de presentacion del prototipo
   --------------------------------------------------------------------------
   Aqui vive UNICAMENTE logica de interfaz: pintar el marco de la aplicacion,
   formatear valores, dibujar graficos en SVG y animar componentes (stepper,
   kanban, modales). No hay peticiones de red ni acceso a datos reales.
   ========================================================================== */

/* -------------------------------------------------------------------------
   1. Iconos (trazos tipo outline, 24x24)
   ------------------------------------------------------------------------- */
const ICONS = {
  tablero:   '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  recepcion: '<path d="M9 3h6a1 1 0 0 1 1 1v2H8V4a1 1 0 0 1 1-1Z"/><path d="M16 5h2a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2"/><path d="M9 12h6M9 16h4"/>',
  agenda:    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  taller:    '<rect x="3" y="4" width="5" height="16" rx="1.5"/><rect x="9.5" y="4" width="5" height="10" rx="1.5"/><rect x="16" y="4" width="5" height="13" rx="1.5"/>',
  clientes:  '<path d="M16 20v-1.5a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4V20"/><circle cx="9" cy="7" r="3.2"/><path d="M17 4.2a3.2 3.2 0 0 1 0 6.2M22 20v-1.5a4 4 0 0 0-3-3.8"/>',
  vehiculos: '<path d="M5 17h14M6.5 17v1.6a1 1 0 0 1-1 1H4.6a1 1 0 0 1-1-1V17M20.4 17v1.6a1 1 0 0 1-1 1h-.9a1 1 0 0 1-1-1V17"/><path d="M3.5 17v-4l2-5.2A2 2 0 0 1 7.4 6.5h9.2a2 2 0 0 1 1.9 1.3l2 5.2v4Z"/><path d="M6.5 13.5h2M15.5 13.5h2M5.6 11.2h12.8"/>',
  ordenes:   '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
  alertas:   '<path d="M18 8.5a6 6 0 1 0-12 0c0 6-2.2 7.5-2.2 7.5h16.4S18 14.5 18 8.5"/><path d="M13.7 20a2 2 0 0 1-3.4 0"/>',
  reportes:  '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  buscar:    '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/>',
  mas:       '<path d="M12 5v14M5 12h14"/>',
  chevron:   '<path d="m9 6 6 6-6 6"/>',
  reloj:     '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.2l3.2 2"/>',
  check:     '<path d="M20 6 9 17l-5-5"/>',
  alerta:    '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4.5M12 17.2h.01"/>',
  info:      '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4.5M12 8h.01"/>',
  imprimir:  '<path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="7" rx="1"/>',
  descargar: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  salir:     '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  telefono:  '<path d="M21.5 16.9v2.6a2 2 0 0 1-2.2 2 19.4 19.4 0 0 1-8.5-3 19.1 19.1 0 0 1-5.9-5.9 19.4 19.4 0 0 1-3-8.6A2 2 0 0 1 3.9 2h2.6a2 2 0 0 1 2 1.7c.1 1 .3 1.9.7 2.8a2 2 0 0 1-.5 2.1L7.6 9.8a15.5 15.5 0 0 0 5.9 5.9l1.2-1.1a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.9 2.1Z"/>',
  correo:    '<rect x="2.5" y="4.5" width="19" height="15" rx="2"/><path d="m3 6.5 9 6 9-6"/>',
  mapa:      '<path d="M20 10.2c0 5.4-8 11.8-8 11.8s-8-6.4-8-11.8a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.7"/>',
  llave:     '<path d="M14.5 9.5a4.5 4.5 0 1 0-4.2 4.5L9 15.3l1.4 1.4-1 1 1.4 1.4-1 1 1.4 1.4 2-2v-5.2a4.5 4.5 0 0 0 1.3-4.8Z" transform="rotate(180 12 12)"/><circle cx="15.5" cy="8.5" r="1.4"/>',
  editar:    '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  ojo:       '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  filtro:    '<path d="M3 5h18l-7 8v6l-4 2v-8Z"/>',
  cerrar:    '<path d="M18 6 6 18M6 6l12 12"/>',
  arriba:    '<path d="M12 19V5M5 12l7-7 7 7"/>',
  abajo:     '<path d="M12 5v14M19 12l-7 7-7-7"/>',
  usuario:   '<circle cx="12" cy="8" r="3.5"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
  menu:      '<path d="M4 6h16M4 12h16M4 18h16"/>',
  candado:   '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  llaveInv:  '<circle cx="8" cy="12" r="3.5"/><path d="M11.5 12H21l-1.5 2M17 12v3"/>',
  refaccion: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 3 14.1H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 7a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 9.9 3H10a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1.3Z"/>'
};

function icon(name, cls) {
  const body = ICONS[name] || "";
  return `<svg class="${cls || ""}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
}

/* -------------------------------------------------------------------------
   2. Formateadores
   ------------------------------------------------------------------------- */
const MESES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
const DIAS  = ["dom","lun","mar","mié","jue","vie","sáb"];
const DIAS_LARGO = ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"];
const MESES_LARGO = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];

/* "Jueves 17 de septiembre, 2026" a partir de una fecha ISO "YYYY-MM-DD" */
function fechaLarga(iso) {
  const [y, m, d] = iso.slice(0, 10).split("-");
  const dia = new Date(iso + "T12:00:00").getDay();
  return `${DIAS_LARGO[dia]} ${Number(d)} de ${MESES_LARGO[Number(m) - 1]}, ${y}`;
}

const fmt = {
  money(n, decimales = 2) {
    if (n === null || n === undefined) return "-";
    return "$" + Number(n).toLocaleString("es-MX", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
  },
  moneyShort(n) {
    if (n >= 1000) return "$" + (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k";
    return "$" + n;
  },
  int(n) { return Number(n).toLocaleString("es-MX"); },
  fecha(iso) {
    if (!iso) return "-";
    const [y, m, d] = iso.slice(0, 10).split("-");
    return `${Number(d)} ${MESES[Number(m) - 1]} ${y}`;
  },
  fechaCorta(iso) {
    if (!iso) return "-";
    const [y, m, d] = iso.slice(0, 10).split("-");
    return `${d}/${m}/${y.slice(2)}`;
  },
  fechaHora(iso) {
    if (!iso) return "-";
    const hora = iso.length > 10 ? iso.slice(11, 16) : "";
    return fmt.fecha(iso) + (hora ? ` · ${hora}` : "");
  },
  hora(iso) { return iso && iso.length > 10 ? iso.slice(11, 16) : "-"; },
  diaSemana(iso) {
    const d = new Date(iso + "T12:00:00");
    return DIAS[d.getDay()];
  },
  combustible(octavos) {
    if (octavos === null || octavos === undefined) return "-";
    return `${octavos}/8`;
  }
};

/* Pastilla de estatus reutilizable */
function pill(texto, cls) {
  return `<span class="pill ${cls}"><span class="dot"></span>${texto}</span>`;
}
function pillOrden(estatus) {
  const e = VM.ESTATUS_ORDEN.find(x => x.key === estatus);
  return pill(e ? e.label : estatus, e ? e.cls : "st-neutral");
}
function pillCita(estatus) {
  const e = VM.ESTATUS_CITA[estatus];
  return pill(e ? e.label : estatus, e ? e.cls : "st-neutral");
}
function iniciales(nombre) {
  return nombre.split(/\s+/).slice(0, 2).map(p => p[0]).join("").toUpperCase();
}

/* -------------------------------------------------------------------------
   3. Marco de la aplicacion (sidebar + topbar)
   ------------------------------------------------------------------------- */
const NAV = [
  {
    grupo: "Operación diaria",
    items: [
      { key: "tablero",   label: "Tablero",     href: "index.html",     icon: "tablero"   },
      { key: "recepcion", label: "Recepción",   href: "recepcion.html", icon: "recepcion" },
      { key: "agenda",    label: "Agenda",      href: "agenda.html",    icon: "agenda", badge: () => VM.citas.filter(c => c.fecha === VM.HOY).length },
      { key: "taller",    label: "Taller",      href: "taller.html",    icon: "taller",  badge: () => VM.ordenes.filter(o => o.estatus !== "Entregado" && o.estatus !== "Pendiente").length }
    ]
  },
  {
    grupo: "Expedientes",
    items: [
      { key: "clientes",  label: "Clientes",    href: "clientes.html",  icon: "clientes"  },
      { key: "vehiculos", label: "Vehículos",   href: "vehiculos.html", icon: "vehiculos" },
      { key: "ordenes",   label: "Órdenes de servicio", href: "ordenes.html", icon: "ordenes" }
    ]
  },
  {
    grupo: "Análisis",
    items: [
      { key: "alertas",   label: "Alertas preventivas", href: "alertas.html", icon: "alertas", badge: () => VM.alertas.length, alerta: true },
      { key: "reportes",  label: "Reportes",    href: "reportes.html",  icon: "reportes"  }
    ]
  }
];

function renderShell() {
  const page = document.body.dataset.page;
  const aside = document.getElementById("sidebar");
  const top   = document.getElementById("topbar");
  if (!aside || !top) return;

  aside.className = "sidebar";
  aside.innerHTML = `
    <div class="brand">
      <div class="brand-mark">VM</div>
      <div class="brand-text">
        <span class="brand-name">VMOTORS</span>
        <span class="brand-sub">Taller automotriz</span>
      </div>
    </div>
    <nav class="nav">
      ${NAV.map(g => `
        <div class="nav-group">
          <div class="nav-label">${g.grupo}</div>
          ${g.items.map(i => `
            <a class="nav-item ${i.key === page ? "is-active" : ""}" href="${i.href}">
              ${icon(i.icon)}
              <span>${i.label}</span>
              ${i.badge ? `<span class="nav-badge ${i.alerta ? "is-alert" : ""}">${typeof i.badge === "function" ? i.badge() : i.badge}</span>` : ""}
            </a>`).join("")}
        </div>`).join("")}
    </nav>
    <div class="sidebar-foot">
      <span>Versión 0.9 · Prototipo</span>
      <a href="login.html" data-logout title="Cerrar sesión">${icon("salir")}</a>
    </div>`;

  const titulo = document.body.dataset.title || "";
  const crumb  = document.body.dataset.crumb || "VMotors";
  top.className = "topbar";
  top.innerHTML = `
    <button class="nav-toggle" id="btn-nav-toggle" aria-label="Abrir menú">${icon("menu")}</button>
    <div class="topbar-titles">
      <div class="crumb">${crumb}</div>
      <h1>${titulo}</h1>
    </div>
    <div class="topbar-spacer"></div>
    <div class="search">
      ${icon("buscar")}
      <input type="search" placeholder="Buscar placa, cliente o folio" aria-label="Buscar">
    </div>
    <div class="topbar-chip">${icon("reloj")} ${fechaLarga(VM.HOY)}</div>
    <div class="user-chip">
      <div class="avatar">AD</div>
      <div>
        <div class="u-name">Administrador</div>
        <div class="u-role">Taller VMotors</div>
      </div>
    </div>`;

  initMenuMovil(aside);
}

/* Cajon de navegacion en pantallas angostas: la barra lateral (oculta por
   CSS bajo los 900px) se abre como panel deslizante sobre un fondo oscuro. */
function initMenuMovil(aside) {
  let fondo = document.querySelector(".sidebar-backdrop");
  if (!fondo) {
    fondo = document.createElement("div");
    fondo.className = "sidebar-backdrop";
    document.body.appendChild(fondo);
  }
  const cerrar = () => { aside.classList.remove("is-open"); fondo.classList.remove("is-open"); };
  const abrir  = () => { aside.classList.add("is-open"); fondo.classList.add("is-open"); };

  document.getElementById("btn-nav-toggle").addEventListener("click", abrir);
  fondo.addEventListener("click", cerrar);
  aside.querySelectorAll(".nav-item").forEach(a => a.addEventListener("click", cerrar));
}

/* -------------------------------------------------------------------------
   4. Avisos de prototipo (toast)
   ------------------------------------------------------------------------- */
function toast(mensaje, tipo = "info") {
  let cont = document.querySelector(".toast-stack");
  if (!cont) {
    cont = document.createElement("div");
    cont.className = "toast-stack";
    document.body.appendChild(cont);
  }
  const iconos = { ok: "check", danger: "alerta", warn: "alerta", info: "info" };
  const el = document.createElement("div");
  el.className = `toast toast-${tipo}`;
  el.innerHTML = `${icon(iconos[tipo] || "info")}<span>${mensaje}</span>`;
  cont.appendChild(el);
  requestAnimationFrame(() => el.classList.add("is-on"));
  setTimeout(() => {
    el.classList.remove("is-on");
    setTimeout(() => el.remove(), 250);
  }, 3000);
}

/* Sustituye <span data-icon="nombre"></span> por el SVG correspondiente */
function initIcons(raiz = document) {
  raiz.querySelectorAll("[data-icon]").forEach(el => {
    const tmp = document.createElement("div");
    tmp.innerHTML = icon(el.dataset.icon, el.className || "");
    const svg = tmp.firstElementChild;
    if (el.getAttribute("style")) svg.setAttribute("style", el.getAttribute("style"));
    el.replaceWith(svg);
  });
}

/* Cualquier control marcado con data-demo muestra el aviso de prototipo */
function initDemoActions() {
  document.addEventListener("click", (ev) => {
    const el = ev.target.closest("[data-demo]");
    if (!el) return;
    ev.preventDefault();
    toast(el.dataset.demo || "Acción de demostración: el prototipo no guarda información.");
  });
}

/* -------------------------------------------------------------------------
   Exportar a CSV (columnas: [{clave, titulo}], filas: arreglo de objetos)
   ------------------------------------------------------------------------- */
function exportarCSV(nombreArchivo, columnas, filas) {
  const escapar = (v) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const encabezado = columnas.map(c => escapar(c.titulo)).join(",");
  const cuerpo = filas.map(f => columnas.map(c => escapar(f[c.clave])).join(",")).join("\n");
  const csv = "﻿" + encabezado + "\n" + cuerpo;   // BOM para que Excel respete acentos

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombreArchivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/* -------------------------------------------------------------------------
   Paginacion de tablas en el cliente
   ------------------------------------------------------------------------- */
/**
 * Gobierna la paginacion de una lista ya renderizada en HTML.
 * @param {Object} opts
 * @param {HTMLElement} opts.contenedor   elemento .pagination donde se dibujan los controles
 * @param {Function} opts.onCambio        (paginaActual) => void, pinta la pagina indicada
 * @param {number} opts.porPagina
 * @returns {{ actualizar(totalItems): void, pagina: number }}
 */
function crearPaginador({ contenedor, onCambio, porPagina }) {
  const estado = { pagina: 1, total: 0 };

  function totalPaginas() { return Math.max(1, Math.ceil(estado.total / porPagina)); }

  function pintarControles() {
    const tp = totalPaginas();
    const p = estado.pagina;
    const botones = [];
    botones.push(`<button data-p="${p - 1}" ${p <= 1 ? "disabled" : ""}>‹</button>`);
    for (let i = 1; i <= tp; i++) {
      if (tp > 7 && i !== 1 && i !== tp && Math.abs(i - p) > 1) {
        if (i === 2 || i === tp - 1) botones.push(`<button disabled>…</button>`);
        continue;
      }
      botones.push(`<button data-p="${i}" class="${i === p ? "is-active" : ""}">${i}</button>`);
    }
    botones.push(`<button data-p="${p + 1}" ${p >= tp ? "disabled" : ""}>›</button>`);
    contenedor.innerHTML = botones.join("");
    contenedor.querySelectorAll("[data-p]").forEach(b => {
      b.addEventListener("click", () => irA(Number(b.dataset.p)));
    });
  }

  function irA(p) {
    const tp = totalPaginas();
    estado.pagina = Math.min(Math.max(1, p), tp);
    pintarControles();
    onCambio(estado.pagina);
  }

  function actualizar(totalItems) {
    estado.total = totalItems;
    if (estado.pagina > totalPaginas()) estado.pagina = 1;
    pintarControles();
    onCambio(estado.pagina);
  }

  return { actualizar, get pagina() { return estado.pagina; } };
}

/* -------------------------------------------------------------------------
   Llamadas de escritura a la API (POST/PATCH/DELETE)
   ------------------------------------------------------------------------- */

/* FastAPI devuelve detail como string (errores de negocio, 404/409) o como
   arreglo de {loc, msg, type} (errores de validación de Pydantic, 422). */
function _mensajeError(data) {
  if (!data) return "Ocurrió un error inesperado.";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) return data.detail.map(e => e.msg).join(" · ");
  return "Ocurrió un error inesperado.";
}

async function vmApi(method, url, body) {
  let r;
  try {
    r = await fetch(url, {
      method,
      credentials: "same-origin",
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("No fue posible conectar con el servidor.");
  }
  if (r.status === 401) { window.location.href = "login.html"; throw new Error("Sesión expirada."); }
  let data = null;
  try { data = await r.json(); } catch { /* respuesta sin cuerpo */ }
  if (!r.ok) throw new Error(_mensajeError(data));
  return data;
}

/* Cierre de sesión real: avisa al backend antes de volver al login */
function initLogout() {
  document.addEventListener("click", (ev) => {
    const el = ev.target.closest("[data-logout]");
    if (!el) return;
    ev.preventDefault();
    fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" })
      .catch(() => {})
      .finally(() => { window.location.href = "login.html"; });
  });
}

/* -------------------------------------------------------------------------
   5. Graficos en SVG (sin librerias)
   ------------------------------------------------------------------------- */
const SVG_NS = "http://www.w3.org/2000/svg";

function ejeValores(max, pasos = 4) {
  const bruto = max / pasos;
  const magnitud = Math.pow(10, Math.floor(Math.log10(bruto)));
  const norm = bruto / magnitud;
  const paso = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10) * magnitud;
  const techo = Math.ceil(max / paso) * paso;
  const ticks = [];
  for (let v = 0; v <= techo + paso / 1000; v += paso) ticks.push(v);
  return { techo, ticks };
}

function pathBarraSuperiorRedondeada(x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h);
  return `M${x},${y + h} L${x},${y + rr} Q${x},${y} ${x + rr},${y} L${x + w - rr},${y} Q${x + w},${y} ${x + w},${y + rr} L${x + w},${y + h} Z`;
}

/**
 * Grafico de barras verticales, una sola serie (magnitud en el tiempo).
 * @param {HTMLElement} host  contenedor con clase .chart-holder
 * @param {Array} datos       [{ etiqueta, valor }]
 * @param {Object} opts       { alto, formato, resaltarUltima }
 */
function barChart(host, datos, opts = {}) {
  const alto = opts.alto || 210;
  const ancho = host.clientWidth || 620;
  const m = { t: 16, r: 8, b: 26, l: 46 };
  const iw = ancho - m.l - m.r;
  const ih = alto - m.t - m.b;
  const max = Math.max(...datos.map(d => d.valor));
  const { techo, ticks } = ejeValores(max);
  const fmtV = opts.formato || (v => fmt.int(v));
  const bw = Math.min(46, (iw / datos.length) * 0.56);

  const y = v => m.t + ih - (v / techo) * ih;

  let svg = `<svg class="chart" viewBox="0 0 ${ancho} ${alto}" role="img" aria-label="${opts.aria || "Gráfico de barras"}">`;
  ticks.forEach(t => {
    svg += `<line class="grid-line" x1="${m.l}" x2="${ancho - m.r}" y1="${y(t)}" y2="${y(t)}"/>`;
    svg += `<text class="axis-text" x="${m.l - 9}" y="${y(t) + 3.5}" text-anchor="end">${opts.formatoEje ? opts.formatoEje(t) : fmtV(t)}</text>`;
  });
  datos.forEach((d, i) => {
    const cx = m.l + (iw / datos.length) * (i + 0.5);
    const h = Math.max(2, ih - (y(d.valor) - m.t));
    const ultima = opts.resaltarUltima && i === datos.length - 1;
    svg += `<g class="bar-g" data-i="${i}">
      <path class="bar" d="${pathBarraSuperiorRedondeada(cx - bw / 2, y(d.valor), bw, h, 4)}"
            ${ultima ? 'style="fill:var(--series-1-weak)"' : ""}/>
      <rect class="chart-hit" x="${cx - iw / datos.length / 2}" y="${m.t}" width="${iw / datos.length}" height="${ih}"/>
      <text class="axis-text" x="${cx}" y="${alto - 8}" text-anchor="middle">${d.etiqueta}</text>
    </g>`;
  });
  svg += `</svg><div class="chart-tip"></div>`;
  host.innerHTML = svg;

  const tip = host.querySelector(".chart-tip");
  host.querySelectorAll(".bar-g").forEach(g => {
    g.addEventListener("mousemove", (ev) => {
      const d = datos[+g.dataset.i];
      const r = host.getBoundingClientRect();
      tip.innerHTML = `<span class="t-k">${d.etiqueta}</span> · <span class="t-v">${fmtV(d.valor)}</span>${d.nota ? `<br><span class="t-k">${d.nota}</span>` : ""}`;
      tip.style.left = (ev.clientX - r.left) + "px";
      tip.style.top  = (ev.clientY - r.top) + "px";
      tip.classList.add("is-on");
    });
    g.addEventListener("mouseleave", () => tip.classList.remove("is-on"));
  });
}

/**
 * Grafico de linea con area, una sola serie (cambio en el tiempo).
 */
function lineChart(host, datos, opts = {}) {
  const alto = opts.alto || 200;
  const ancho = host.clientWidth || 620;
  const m = { t: 18, r: 12, b: 26, l: 38 };
  const iw = ancho - m.l - m.r;
  const ih = alto - m.t - m.b;
  const max = Math.max(...datos.map(d => d.valor));
  const { techo, ticks } = ejeValores(max);
  const fmtV = opts.formato || (v => fmt.int(v));

  const x = i => m.l + (iw / Math.max(1, datos.length - 1)) * i;
  const y = v => m.t + ih - (v / techo) * ih;

  const linea = datos.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.valor).toFixed(1)}`).join(" ");
  const area  = `${linea} L${x(datos.length - 1).toFixed(1)},${m.t + ih} L${x(0).toFixed(1)},${m.t + ih} Z`;

  let svg = `<svg class="chart" viewBox="0 0 ${ancho} ${alto}" role="img" aria-label="${opts.aria || "Gráfico de línea"}">
    <defs><linearGradient id="areaFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--series-1)" stop-opacity=".18"/>
      <stop offset="100%" stop-color="var(--series-1)" stop-opacity="0"/>
    </linearGradient></defs>`;
  ticks.forEach(t => {
    svg += `<line class="grid-line" x1="${m.l}" x2="${ancho - m.r}" y1="${y(t)}" y2="${y(t)}"/>`;
    svg += `<text class="axis-text" x="${m.l - 9}" y="${y(t) + 3.5}" text-anchor="end">${fmtV(t)}</text>`;
  });
  svg += `<path class="area" d="${area}"/><path class="line" d="${linea}"/>`;
  datos.forEach((d, i) => {
    svg += `<circle class="marker" cx="${x(i)}" cy="${y(d.valor)}" r="4.5"/>`;
    svg += `<text class="axis-text" x="${x(i)}" y="${alto - 8}" text-anchor="middle">${d.etiqueta}</text>`;
    svg += `<rect class="chart-hit" data-i="${i}" x="${x(i) - iw / datos.length / 2}" y="${m.t}" width="${iw / datos.length}" height="${ih}"/>`;
  });
  svg += `<line class="grid-line cross" style="stroke:var(--border-strong);display:none" y1="${m.t}" y2="${m.t + ih}"/>`;
  svg += `</svg><div class="chart-tip"></div>`;
  host.innerHTML = svg;

  const tip = host.querySelector(".chart-tip");
  const cross = host.querySelector(".cross");
  host.querySelectorAll(".chart-hit").forEach(r => {
    r.addEventListener("mousemove", (ev) => {
      const i = +r.dataset.i, d = datos[i];
      const rect = host.getBoundingClientRect();
      cross.style.display = "block";
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i));
      tip.innerHTML = `<span class="t-k">${d.etiqueta}</span> · <span class="t-v">${fmtV(d.valor)}</span>`;
      tip.style.left = (ev.clientX - rect.left) + "px";
      tip.style.top  = (ev.clientY - rect.top) + "px";
      tip.classList.add("is-on");
    });
    r.addEventListener("mouseleave", () => { tip.classList.remove("is-on"); cross.style.display = "none"; });
  });
}

/** Barras horizontales en HTML (ranking por categoria). */
function hbars(host, datos, opts = {}) {
  const max = Math.max(...datos.map(d => d.valor));
  const sufijo = opts.sufijo || "";
  host.innerHTML = `<div class="hbar">${datos.map(d => `
    <div class="hbar-row">
      <div class="hbar-name">${d.color ? `<span class="kb-swatch" style="background:${d.color}"></span>` : ""}${d.nombre}</div>
      <div class="hbar-track"><div class="hbar-fill" style="width:${(d.valor / max * 100).toFixed(1)}%${d.color ? `;background:${d.color}` : ""}"></div></div>
      <div class="hbar-val">${fmt.int(d.valor)}${sufijo}</div>
    </div>`).join("")}</div>`;
}

/* Redibuja los graficos al cambiar el tamaño de la ventana */
const _charts = [];
function registrarChart(fn) { _charts.push(fn); fn(); }
let _rt;
window.addEventListener("resize", () => {
  clearTimeout(_rt);
  _rt = setTimeout(() => _charts.forEach(f => f()), 180);
});

/* -------------------------------------------------------------------------
   6. Componentes interactivos
   ------------------------------------------------------------------------- */

/* Stepper: navegacion entre pasos de un formulario */
function initStepper() {
  const wrap = document.querySelector("[data-stepper]");
  if (!wrap) return;
  const pasos   = [...wrap.querySelectorAll(".step")];
  const paneles = [...document.querySelectorAll(".step-panel")];
  let actual = 0;

  const pintar = () => {
    pasos.forEach((p, i) => {
      p.classList.toggle("is-active", i === actual);
      p.classList.toggle("is-done", i < actual);
      const dot = p.querySelector(".step-dot");
      dot.innerHTML = i < actual ? icon("check") : (i + 1);
    });
    paneles.forEach((p, i) => p.classList.toggle("is-current", i === actual));
    document.querySelectorAll("[data-step-prev]").forEach(b => b.classList.toggle("is-disabled", actual === 0));
    const ultimo = actual === paneles.length - 1;
    document.querySelectorAll("[data-step-next]").forEach(b => b.hidden = ultimo);
    document.querySelectorAll("[data-step-finish]").forEach(b => b.hidden = !ultimo);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  document.addEventListener("click", (ev) => {
    if (ev.target.closest("[data-step-next]")) { actual = Math.min(actual + 1, paneles.length - 1); pintar(); }
    if (ev.target.closest("[data-step-prev]")) { actual = Math.max(actual - 1, 0); pintar(); }
    const salto = ev.target.closest(".step");
    if (salto && pasos.includes(salto)) { actual = pasos.indexOf(salto); pintar(); }
  });
  pintar();
}

/* Kanban: arrastrar tarjetas entre columnas. Todos los listeners van en el
   contenedor `.kanban` (delegados), para seguir funcionando aunque la pagina
   vuelva a pintar el HTML interno (por ejemplo, al revertir un movimiento
   que el backend rechazó). */
function initKanban() {
  const board = document.querySelector(".kanban");
  if (!board) return;
  let arrastrada = null;

  const actualizarConteos = () => {
    board.querySelectorAll(".kb-col").forEach(col => {
      const n = col.querySelectorAll(".kb-card").length;
      const countEl = col.querySelector(".kb-count");
      if (countEl) countEl.textContent = n;
      const body = col.querySelector(".kb-body");
      if (body && n === 0 && !body.querySelector(".kb-empty")) {
        body.insertAdjacentHTML("beforeend", '<div class="kb-empty">Sin unidades</div>');
      }
    });
  };

  board.addEventListener("dragstart", (e) => {
    const card = e.target.closest(".kb-card");
    if (!card) return;
    arrastrada = card;
    card.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  board.addEventListener("dragend", () => {
    if (arrastrada) arrastrada.classList.remove("dragging");
    board.querySelectorAll(".drop-target").forEach(c => c.classList.remove("drop-target"));
    arrastrada = null;
    actualizarConteos();
  });
  board.addEventListener("dragover", (e) => {
    const col = e.target.closest(".kb-col");
    if (!col) return;
    e.preventDefault();
    board.querySelectorAll(".drop-target").forEach(c => { if (c !== col) c.classList.remove("drop-target"); });
    col.classList.add("drop-target");
  });
  board.addEventListener("dragleave", (e) => {
    const col = e.target.closest(".kb-col");
    if (col && !col.contains(e.relatedTarget)) col.classList.remove("drop-target");
  });
  board.addEventListener("drop", (e) => {
    const col = e.target.closest(".kb-col");
    if (!col) return;
    e.preventDefault();
    col.classList.remove("drop-target");
    if (!arrastrada) return;
    const colOrigen = arrastrada.closest(".kb-col");
    if (colOrigen === col) return;
    const destino = col.querySelector(".kb-body");
    const vacio = destino.querySelector(".kb-empty");
    if (vacio) vacio.remove();
    destino.appendChild(arrastrada);
    arrastrada.style.setProperty("--kb-accent", col.dataset.color);
    /* La pagina decide que hacer con el cambio (persistirlo o revertirlo);
       aqui solo se mueve la tarjeta en pantalla. */
    board.dispatchEvent(new CustomEvent("vm-kanban-drop", {
      detail: { card: arrastrada, colOrigen, colDestino: col },
    }));
  });
}

/* Modales */
function initModals() {
  document.addEventListener("click", (e) => {
    const abrir = e.target.closest("[data-modal-open]");
    if (abrir) {
      e.preventDefault();
      const m = document.getElementById(abrir.dataset.modalOpen);
      if (m) m.classList.add("is-open");
    }
    const cerrar = e.target.closest("[data-modal-close]");
    if (cerrar) { cerrar.closest(".modal-backdrop").classList.remove("is-open"); }
    if (e.target.classList.contains("modal-backdrop")) e.target.classList.remove("is-open");
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") document.querySelectorAll(".modal-backdrop.is-open").forEach(m => m.classList.remove("is-open"));
  });
}

/* Grupos segmentados y filtros de tabla (filtrado en cliente sobre el DOM) */
function initSegmentos() {
  document.querySelectorAll(".seg").forEach(seg => {
    seg.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      seg.querySelectorAll("button").forEach(x => x.classList.remove("is-active"));
      b.classList.add("is-active");
      const destino = seg.dataset.filterTarget;
      if (!destino) return;
      const valor = b.dataset.value;
      document.querySelectorAll(`${destino} [data-estatus]`).forEach(fila => {
        fila.hidden = !(valor === "todos" || fila.dataset.estatus === valor);
      });
    });
  });
}

/* Busqueda en vivo sobre una tabla ya renderizada */
function initBusquedaTabla() {
  document.querySelectorAll("[data-search-target]").forEach(input => {
    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      document.querySelectorAll(`${input.dataset.searchTarget} tbody tr`).forEach(tr => {
        tr.hidden = q !== "" && !tr.textContent.toLowerCase().includes(q);
      });
    });
  });
}

/* Tarjetas de radio (transmisión, forma de pago...) */
function initRadioCards() {
  document.querySelectorAll(".radio-cards").forEach(grupo => {
    const sync = () => grupo.querySelectorAll(".radio-card").forEach(c => {
      c.classList.toggle("is-selected", c.querySelector("input").checked);
    });
    grupo.addEventListener("change", sync);
    sync();
  });
}

/* -------------------------------------------------------------------------
   7. Arranque
   ------------------------------------------------------------------------- */
/* Overlay de carga mientras VM.listo resuelve: evita la pantalla en blanco
   que se veia antes de que llegara la primera respuesta de la API. */
function mostrarCargando() {
  if (!document.body.dataset.page) return null;
  const el = document.createElement("div");
  el.className = "vm-loading";
  el.innerHTML = `<div class="vm-spinner"></div><span>Cargando VMotors…</span>`;
  document.body.appendChild(el);
  return el;
}

document.addEventListener("DOMContentLoaded", () => {
  const overlay = mostrarCargando();
  Promise.resolve(VM.listo).then(() => {
    renderShell();
    /* La pagina pinta su contenido primero; despues se enlazan los componentes */
    if (typeof initPagina === "function") initPagina();
    initIcons();
    initDemoActions();
    initLogout();
    initStepper();
    initKanban();
    initModals();
    initSegmentos();
    initBusquedaTabla();
    initRadioCards();
  }).finally(() => { if (overlay) overlay.remove(); });
});
