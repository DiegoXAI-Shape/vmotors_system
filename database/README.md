# VMotors · Base de datos PostgreSQL

Script independiente que crea el esquema relacional del taller y lo llena con
datos ficticios generados con **Faker**. No tiene relación con el prototipo web
de `frontend/`: esa interfaz es estática y no se conecta a ninguna base de datos.

---

## 1. Requisitos

| Componente | Versión mínima | Nota |
|---|---|---|
| PostgreSQL | 12 | Se usa una columna calculada `GENERATED ALWAYS AS ... STORED` |
| Python | 3.9 | |

---

## 2. Instalación

```bash
cd database

# (opcional pero recomendable) entorno virtual
python -m venv .venv
source .venv/bin/activate        # en Windows:  .venv\Scripts\activate

pip install -r requirements.txt
```

## 3. Credenciales

Las credenciales **nunca** se escriben dentro del script: se leen de variables
de entorno, normalmente desde un archivo `.env`.

```bash
cp .env.example .env
```

Edite `.env` y coloque la contraseña de su servidor:

```
PGHOST=localhost
PGPORT=5432
PGDATABASE=vmotors
PGUSER=postgres
PGPASSWORD=su_contraseña
```

Si `PGPASSWORD` queda vacío y el script se ejecuta en una terminal interactiva,
la contraseña se solicita por teclado sin mostrarse en pantalla.

Antes de la primera ejecución, la base debe existir:

```bash
createdb vmotors
# o desde psql:  CREATE DATABASE vmotors;
```

## 4. Ejecución

```bash
# Primera vez (crea estructura + datos)
python seed_database.py

# Volver a generar todo desde cero, sin confirmación
python seed_database.py --reset --yes

# Un volumen mayor de datos, reproducible con una semilla fija
python seed_database.py --reset --yes --clientes 200 --seed 7

# Sólo la estructura, sin registros de prueba
python seed_database.py --reset --yes --schema-only

# Exportar el DDL a un archivo (no se conecta a la base)
python seed_database.py --dump-schema > schema.sql
```

### Opciones

| Opción | Descripción |
|---|---|
| `--clientes N` | Cantidad de clientes a generar (por omisión 60). El resto de las tablas crece en proporción. |
| `--seed N` | Semilla aleatoria; con el mismo valor se obtiene exactamente el mismo conjunto de datos. |
| `--schema` | Esquema de PostgreSQL a utilizar (por omisión `vmotors`). |
| `--reset` | Elimina las tablas y vistas existentes y las vuelve a crear. |
| `--yes` / `-y` | No pide confirmación al usar `--reset`. Obligatorio en ejecuciones no interactivas. |
| `--schema-only` | Crea únicamente la estructura. |
| `--dump-schema` | Imprime el DDL y termina, sin conectarse. |

**Re-ejecución controlada.** Si el esquema ya contiene tablas y no se indica
`--reset`, el script se detiene con un aviso en lugar de duplicar información.
Con `--reset` se eliminan las estructuras en orden inverso de dependencias
(`DROP ... CASCADE`) y se reconstruye todo dentro de una sola transacción: si
algo falla, no queda una base a medias.

---

## 5. Modelo de datos

Siete tablas en tercera forma normal. Las cuatro primeras corresponden al
diccionario de datos de la Fase III; las tres restantes dan soporte al desglose
de refacciones y a la trazabilidad de estatus descritos en la Fase IV.

```
clientes ──1:N──> vehiculos ──1:N──> citas ──1:1──> ordenes_servicio
                                                          │
                                        ┌─────────────────┴─────────────────┐
                                        │                                   │
                                  orden_refacciones ──N:1──> refacciones    historial_estatus
```

| Tabla | Contenido | Llave primaria |
|---|---|---|
| `clientes` | Datos fiscales, contacto y domicilio del propietario | `id_cliente` |
| `vehiculos` | Padrón de unidades, una por matrícula | `id_vehiculo` |
| `citas` | Agenda de bloques horarios | `id_cita` |
| `refacciones` | Catálogo de piezas con precio de lista | `id_refaccion` |
| `ordenes_servicio` | Ciclo técnico, diagnóstico y costos | `id_orden` |
| `orden_refacciones` | Piezas instaladas en cada orden | `id_detalle` |
| `historial_estatus` | Bitácora de transiciones de estatus | `id_historial` |

### Reglas de negocio implementadas en la propia base

| Regla | Implementación |
|---|---|
| Un vehículo pertenece a un único cliente | `FOREIGN KEY vehiculos.id_cliente` |
| Cada cita corresponde a una sola unidad | `FOREIGN KEY citas.id_vehiculo` |
| Una cita deriva en exactamente una orden | `UNIQUE (ordenes_servicio.id_cita)` |
| No puede haber dos citas activas en el mismo bloque | Índice único parcial `ux_citas_bloque_activo (fecha, hora_inicio) WHERE estatus_cita <> 'Cancelada'` |
| El horario debe caer dentro de la jornada | `CHECK hora_inicio >= '08:00' AND hora_fin <= '19:00'` |
| La hora de fin es posterior a la de inicio | `CHECK hora_fin > hora_inicio` |
| No se entrega una unidad sin costo ni fecha de salida | `CHECK estatus <> 'Entregado' OR (fecha_entrega IS NOT NULL AND costo_total > 0)` |
| El total es la suma de sus componentes | `CHECK costo_total = costo_mano_obra + costo_refacciones` |
| El teléfono contiene sólo dígitos | `CHECK telefono ~ '^[0-9]{10,15}$'` |
| La matrícula se almacena en mayúsculas y es única | `CHECK placas = upper(placas)` + `UNIQUE` |
| El año del modelo es razonable | `CHECK anio BETWEEN 1980 AND 2100` |

> El límite superior del año es una constante porque PostgreSQL no admite
> funciones volátiles como `CURRENT_DATE` dentro de una restricción `CHECK`.
> La validación contra el año en curso se hace en la capa de aplicación.

### Vistas incluidas

| Vista | Salida del sistema que atiende |
|---|---|
| `v_ordenes_detalle` | Cruce Cliente + Vehículo + Cita + Orden para el tablero y el listado de órdenes |
| `v_vehiculos_en_taller` | Monitor Kanban: unidades físicamente en piso |
| `v_agenda` | Agenda diaria y semanal con el estatus de cada bloque |
| `v_alertas_mantenimiento` | Motor de alertas: unidades con seis meses o más sin visita |
| `v_historial_por_placa` | Reporte de historial acumulado por matrícula |

---

## 6. Volumen aproximado de datos

Con los valores por omisión (`--clientes 60`):

| Tabla | Registros aproximados |
|---|---|
| `clientes` | 60 |
| `vehiculos` | 120 – 130 |
| `citas` | 380 – 400 |
| `ordenes_servicio` | 340 – 360 |
| `orden_refacciones` | 850 – 900 |
| `historial_estatus` | 2,000 – 2,100 |
| `refacciones` | 30 (catálogo fijo) |

La agenda se construye en tres tramos para que la base refleje una operación
viva: historial cerrado de los últimos dos años, siete unidades en el taller el
día de hoy y alrededor de veinticinco turnos comprometidos en las próximas
semanas.

---

## 7. Consultas de comprobación

```sql
SET search_path TO vmotors, public;

-- Unidades que están hoy en el taller
SELECT folio, placas, marca, modelo, cliente, estatus
  FROM v_vehiculos_en_taller
 ORDER BY fecha_ingreso;

-- Agenda del día
SELECT hora_inicio, hora_fin, unidad, placas, cliente, estatus_cita
  FROM v_agenda
 WHERE fecha = CURRENT_DATE
 ORDER BY hora_inicio;

-- Alertas de mantenimiento preventivo (ciclo semestral)
SELECT placas, cliente, telefono, ultima_visita, meses_sin_visita
  FROM v_alertas_mantenimiento
 ORDER BY meses_sin_visita DESC
 LIMIT 20;

-- Facturación por mes
SELECT date_trunc('month', fecha_entrega)::date AS mes,
       COUNT(*)          AS ordenes,
       SUM(costo_total)  AS facturado
  FROM ordenes_servicio
 WHERE estatus = 'Entregado'
 GROUP BY 1
 ORDER BY 1 DESC;

-- Comprobación de que el empalme es imposible: esta consulta debe fallar
INSERT INTO citas (id_vehiculo, fecha, hora_inicio, hora_fin, motivo_ingreso)
SELECT id_vehiculo, fecha, hora_inicio, hora_fin, 'Prueba de empalme'
  FROM citas WHERE estatus_cita <> 'Cancelada' LIMIT 1;
-- ERROR: duplicate key value violates unique constraint "ux_citas_bloque_activo"
```

---

## 8. Problemas frecuentes

| Mensaje | Causa y solución |
|---|---|
| `No fue posible conectar con PostgreSQL` | El servicio no está arriba o los datos de `.env` no coinciden. Verifique con `psql -h localhost -U postgres -d vmotors`. |
| `database "vmotors" does not exist` | Cree la base antes: `createdb vmotors`. |
| `El esquema 'vmotors' ya contiene tablas` | Vuelva a ejecutar con `--reset`. |
| `Se requiere --yes para ejecutar --reset de forma no interactiva` | Agregue `--yes` cuando el script no corra en una terminal. |
| `permission denied to create schema` | El usuario configurado no puede crear esquemas; use uno con privilegios o cambie `--schema`. |
