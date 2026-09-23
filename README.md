# VMotors · Sistema de gestión para taller automotriz

Proyecto Integrador 1 — FIME, UANL · Grupo 002 · Equipo #10

El sistema tiene tres partes:

| Carpeta | Qué es |
|---|---|
| `frontend/` | Interfaz: pantallas HTML/CSS/JS (sin frameworks) |
| `backend/` | API en FastAPI que lee/escribe la base de datos y sirve la interfaz |
| `database/` | Script de Python que crea el esquema (SQLite) y lo llena con datos ficticios (Faker) |

El backend sirve la carpeta `frontend/` directamente, así que **todo corre
en un solo proceso y un solo puerto**: no hace falta levantar dos servidores
por separado.

## Arranque rápido (un solo comando)

```powershell
.\scripts\iniciar.ps1
```

Este script:

1. Crea un entorno virtual (`.venv`) e instala las dependencias si hace falta.
2. Genera `database/vmotors.db` con datos ficticios la primera vez que corre.
3. Levanta el backend en `http://127.0.0.1:8000`.
4. Abre un túnel público con `cloudflared` (se instala con
   `winget install --id Cloudflare.cloudflared -e` si no lo tiene) e imprime
   una URL `https://xxxxx.trycloudflare.com` que puede compartir con el
   equipo para que revisen el sistema sin instalar nada en su máquina.

Cerrar la ventana (o `Ctrl+C`) apaga el túnel y el backend. Usuario de acceso
por omisión: **administrador / vmotors2026** (cámbielo en `backend/.env`
antes de compartir el enlace si le preocupa la seguridad — ver
`backend/.env.example`).

---

## 1. Interfaz (`frontend/`)

Ya no es un prototipo aislado: cada pantalla pide sus datos al backend
(`/api/...`) y requiere haber iniciado sesión en `login.html`. Ábrala a
través del backend (`.\scripts\iniciar.ps1`, o `uvicorn app.main:app` desde
`backend/` y luego `http://127.0.0.1:8000`) — abrir los `.html` con doble
clic ya no funciona, porque las páginas necesitan el servidor para traer la
información.

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
    ├── js/data.js            Carga los datos reales desde /api/* y llena VM
    ├── js/app.js             Marco de la aplicación, formateadores y gráficas SVG
    └── img/favicon.svg
```

* **Sin dependencias**: no usa frameworks ni librerías de gráficas. Las gráficas
  del tablero son SVG generado a mano en `app.js`.
* **Datos reales**: `data.js` ya no trae arreglos hardcodeados; al cargar la
  página pide `/api/clientes`, `/api/vehiculos`, `/api/ordenes`, etc. y llena
  el objeto `VM` con la respuesta, con la misma forma que antes tenía el
  mockup. El resto del código de cada pantalla no tuvo que cambiar.
* **Lectura y escritura reales**: recepción de una unidad (alta de cliente,
  vehículo, cita y orden en un solo paso, reutilizando el expediente si el
  teléfono o la placa ya existen), agendar una cita con validación de
  traslapes, mover una tarjeta del Kanban, avanzar el estatus de una orden,
  capturar diagnóstico/mano de obra y agregar o quitar refacciones — todo
  queda guardado en `vmotors.db`. Lo que sigue siendo demostración es lo que
  no tiene un concepto real detrás en el modelo de datos: exportar CSV,
  imprimir, enviar correo, guardar un borrador o registrar una llamada.
* **Validación de datos**: el backend valida formato de teléfono, RFC, CP,
  placas, año del vehículo y coherencia de horarios (las mismas reglas que
  antes vivían como `CHECK` en el esquema de PostgreSQL) y regresa mensajes
  claros que el formulario muestra al usuario.

---

## 2. Backend (`backend/`)

API en FastAPI que lee `database/vmotors.db` y sirve el `frontend/`. Sesión
de un solo usuario administrador (sin roles ni tabla de usuarios, acorde al
alcance actual del proyecto).

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # usuario/contraseña y clave de sesión
uvicorn app.main:app --reload
```

Con eso el sistema completo queda en `http://127.0.0.1:8000`. El script
`scripts/iniciar.ps1` en la raíz hace estos pasos automáticamente y además
levanta el túnel de `cloudflared` para compartirlo por internet.

**Pruebas** (`backend/tests/`): cubren las reglas de negocio de la API —
login y límite de intentos, validación de datos, traslapes de citas,
reutilización de expediente en recepción, avance de etapas de una orden,
recálculo de costos y los límites de qué se puede editar o borrar. Corren
contra una base de datos temporal, nunca contra `vmotors.db`.

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

| Endpoint | Qué hace |
|---|---|
| `POST /api/auth/login`, `/logout`, `GET /me` | Sesión del administrador (con límite de 5 intentos fallidos cada 15 min) |
| `GET /api/clientes`, `/vehiculos`, `/citas`, `/refacciones` | Catálogos completos |
| `GET /api/clientes/buscar`, `/vehiculos/buscar` | Localiza un cliente por teléfono/RFC o un vehículo por placas (cliente recurrente) |
| `POST /api/clientes`, `/vehiculos`, `/citas` | Altas sueltas, con validación de formato y de traslapes |
| `PATCH /api/clientes/{id}`, `/vehiculos/{id}` | Edición de un expediente ya existente |
| `DELETE /api/vehiculos/{id}` | Baja de una unidad (rechazada si tiene citas/órdenes en su historial) |
| `PATCH /api/citas/{id}` | Cancelar o reprogramar una cita (revalida traslapes si cambia fecha/hora) |
| `POST /api/recepcion` | Formato F-01 completo: cliente + vehículo + cita + orden en una sola operación |
| `GET /api/ordenes` | Órdenes vigentes (abiertas + entregadas en los últimos 30 días), con su desglose de refacciones e historial de estatus anidado |
| `PATCH /api/ordenes/{id}` | Diagnóstico, mano de obra y cambio de estatus (valida que el flujo avance una sola etapa y que haya costo antes de "Entregado") |
| `DELETE /api/ordenes/{id}` | Borra una orden creada por error (solo en etapa Pendiente/Recibido; más allá de eso se corrige, no se borra) |
| `POST/DELETE /api/ordenes/{id}/refacciones/...` | Agregar o quitar refacciones de una orden, recalculando costos |
| `GET /api/ordenes_historicas` | Ledger completo de órdenes ya entregadas (para reportes e historial por placa) |
| `GET /api/alertas` | Unidades con 6+ meses sin visita |
| `GET /api/dashboard` | Series para las gráficas del tablero y reportes |

**Seguridad de la sesión**: cookie firmada con `SameSite=Lax` (un sitio
externo no puede reenviarla en un POST/PATCH/DELETE de otro origen — esa es
la defensa contra CSRF), sin CORS habilitado, límite de intentos de login, y
un aviso en el arranque si `SECRET_KEY` sigue en su valor por omisión.

---

## 3. Base de datos (`database/`)

Dos generadores comparten la misma lógica de datos ficticios
(`generador.py`, con Faker en `es_MX`) y solo difieren en el motor:

```bash
cd database
pip install -r requirements.txt

# SQLite (lo que usa el backend actual: un solo archivo, sin servidor)
python seed_sqlite.py --reset --yes

# PostgreSQL (variante para un futuro despliegue con servidor de base de datos)
cp .env.example .env          # coloque aquí las credenciales de PostgreSQL
createdb vmotors
python seed_database.py --reset --yes
```

Crea siete tablas en tercera forma normal y alrededor de 3,300 registros
ficticios coherentes entre sí (clientes, vehículos, citas, órdenes,
refacciones y su historial de estatus). El detalle completo del modelo, las
opciones del script y las consultas de comprobación están en
[`database/README.md`](database/README.md) (escrito para la variante
PostgreSQL; el esquema de SQLite es el mismo modelo, adaptado en
`seed_sqlite.py`).

---

## 4. Estado del proyecto

Sistema funcional de un solo nivel de usuario: interfaz + backend + base de
datos, con sesión real, datos en vivo en las 12 pantallas, las operaciones
del día a día (recepción, agenda, Kanban, cierre de orden) escribiendo de
verdad en la base de datos, edición/cancelación de lo ya creado (cliente,
vehículo, cita, y una orden recién creada por error), paginación real en las
tablas largas (clientes, vehículos, órdenes, alertas), exportación a CSV
donde tenía sentido, los indicadores de "Resumen mensual" calculados sobre
datos reales (ya no hay números fijos en ninguna pantalla), y una suite de
pruebas automatizadas (`backend/tests/`) que cubre las reglas de negocio.

Deliberadamente fuera de alcance, porque no tienen un concepto de negocio
real detrás en el modelo de datos actual: enviar el comprobante por correo,
imprimir a PDF desde el servidor, programar el envío de un reporte o
guardar un borrador de recepción. Y, como siguiente etapa mayor: cuando el
taller lo requiera, sumar roles adicionales (mecánicos) sobre la misma
base — hoy es deliberadamente un solo nivel de acceso.
3. Si el sistema deja de vivir en una laptop + túnel, mover el despliegue a
   un servidor propio (el backend ya es un proceso WSGI/ASGI estándar, no
   depende de `cloudflared` para funcionar).
