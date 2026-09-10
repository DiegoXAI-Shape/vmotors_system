# VMotors · Sistema de gestión para taller automotriz

Proyecto Integrador 1 — FIME, UANL · Grupo 002 · Equipo #10

Este repositorio contiene **dos entregables independientes** construidos a
partir de los requerimientos de las fases III (Diseño del sistema) y IV
(Proceso del sistema):

| Carpeta | Qué es | Qué **no** es |
|---|---|---|
| `frontend/` | Prototipo visual: pantallas HTML/CSS/JS estáticas con datos de ejemplo | No tiene backend, autenticación ni conexión a base de datos |
| `database/` | Script de Python que crea el esquema PostgreSQL y lo llena con Faker | No sirve a la interfaz; prepara el terreno para un backend futuro |

Los dos entregables están deliberadamente separados: la interfaz muestra cómo
se vería el sistema y el script define cómo estarán organizados los datos
cuando exista un backend que los una.

---

## 1. Prototipo de interfaz (`frontend/`)

No requiere instalación ni servidor. Abra `frontend/login.html` (o directamente
`frontend/index.html`) con doble clic en cualquier navegador moderno.

> Si prefiere servirlo por HTTP:
> `cd frontend && python -m http.server 8000` y visite <http://localhost:8000>.

### Pantallas

| Archivo | Pantalla | Origen en la documentación |
|---|---|---|
| `login.html` | Acceso del administrador | Arquitectura de un solo nivel de usuario |
| `index.html` | Tablero operativo con indicadores y gráficas | Salida **S-01** |
| `recepcion.html` | Captura escalonada en 3 pasos: cliente, vehículo y visita | Formato **F-01** / stepper de la Fase IV |
| `agenda.html` | Calendario semanal y alta de citas con detección de traslapes | Formulario **E-01** / Proceso 2.0 |
| `taller.html` | Monitor Kanban de las unidades en piso | Tablero central de estatus |
| `clientes.html` | Padrón de clientes y ficha del expediente | Módulo 1.0 |
| `vehiculos.html` | Padrón vehicular e historial por unidad | Módulo 1.0 |
| `ordenes.html` | Listado de órdenes de servicio | Módulo 3.0 |
| `orden-detalle.html` | Control de estatus, diagnóstico y desglose de costos | Formulario **E-02** |
| `comprobante.html` | Hoja de entrega imprimible | Salida **S-02** / Formato **F-02** |
| `alertas.html` | Motor de alertas de mantenimiento semestral | Reporte preventivo de la Fase IV |
| `reportes.html` | Reporte diario, historial por placa y resumen mensual | Reportes automatizados |

### Cómo está hecho

```
frontend/
├── *.html                    Una pantalla por archivo
└── assets/
    ├── css/styles.css        Sistema de diseño completo (tokens, componentes)
    ├── js/data.js            Datos de ejemplo con la forma exacta del esquema
    ├── js/app.js             Marco de la aplicación, formateadores y gráficas SVG
    └── img/favicon.svg
```

* **Sin dependencias**: no usa frameworks ni librerías de gráficas. Las gráficas
  del tablero son SVG generado a mano en `app.js`.
* **Datos de ejemplo**: `data.js` expone arreglos (`VM.clientes`, `VM.vehiculos`,
  `VM.citas`, `VM.ordenes`…) cuyos campos coinciden con las columnas reales de
  la base de datos, de modo que cambiar a un backend consista en sustituir esos
  arreglos por la respuesta de una API.
* **Acciones simuladas**: los botones que representarían una escritura muestran
  un aviso de demostración. Sí funcionan de forma local, porque son
  comportamiento de interfaz, el paso a paso del formulario de recepción, el
  arrastre de tarjetas en el Kanban, los filtros y buscadores de las tablas, la
  detección visual de traslapes en la agenda y la validación del flujo de
  estatus en la orden de servicio.

---

## 2. Base de datos (`database/`)

```bash
cd database
pip install -r requirements.txt
cp .env.example .env          # coloque aquí las credenciales de PostgreSQL
createdb vmotors
python seed_database.py --reset --yes
```

Crea siete tablas en tercera forma normal, cinco vistas de consulta y alrededor
de 3,300 registros ficticios coherentes entre sí.

Las credenciales se leen de variables de entorno; **no hay contraseñas escritas
en el código**. El detalle completo del modelo, las opciones del script y las
consultas de comprobación están en [`database/README.md`](database/README.md).

---

## 3. Estado del proyecto

Lo que existe hoy es un **prototipo visual** más un **generador de base de
datos**. Falta, para tener un sistema funcional:

1. Una capa de backend (por ejemplo Flask, FastAPI o Node) que exponga las
   operaciones de alta, consulta y cambio de estatus.
2. Autenticación real del administrador.
3. Sustituir `frontend/assets/js/data.js` por llamadas a esa API.

El diseño actual está pensado para que esos tres pasos no obliguen a rehacer ni
las pantallas ni el esquema.
