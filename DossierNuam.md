# DOSSIER DE IMPLEMENTACIÓN: MANTENEDOR DE CALIFICACIONES TRIBUTARIAS (NUAM - HDU INACAP)

## 1. CONTEXTO DEL PROYECTO Y ARQUITECTURA ACTUAL
Estamos desarrollando el **Mantenedor de Calificaciones Tributarias (DJ 1949 / Cert. 70 y DJ 1922 / Cert. 44)** para **nuam**, ejecutándose en entorno local (`localhost:5173` Frontend y `127.0.0.1:8000` Backend).
- **Stack actual:** FastAPI (Python), React + Vite (CSS propio sin Bootstrap/Tailwind), PostgreSQL (Supabase), MongoDB Atlas (`pymongo`), autenticación JWT con rotación de refresh tokens, RBAC (`Analista`, `Aprobador`, `Auditor`) y suite QA (`pytest` + `qa_runner.py`).
- **Objetivo de esta iteración:** Evolucionar el sistema actual para cubrir el 100% de las Historias de Usuario (HDU) del documento funcional, incorporando:
  1. Metadatos completos del instrumento financiero y homologación oficial de los factores **Factor 8 al Factor 37**.
  2. Conversor automático de **Montos ($) a Factores (8 decimales)**.
  3. Regla de negocio exacta: la suma de los **Factores 8 al 19** debe ser $\le 1.00000000$.
  4. CRUD completo en el mantenedor (**Buscar/Limpiar filtros**, **Ingresar**, **Modificar**, **Eliminar**).
  5. Carga masiva CSV dual (**Por Factores** y **Por Montos**) con lógica **Upsert** por llave única y aislamiento local por corredor.

---

## 2. REGLAS DE NEGOCIO Y FÓRMULAS TRIBUTARIAS (OBLIGATORIAS)

1. **Rango y Nomenclatura de Factores:**
   - Utilizar columnas `factor_8` hasta `factor_37` (30 factores en total, correspondientes a las columnas 8..37 de la DJ 1949 / Cert. 70, homologadas con las columnas 13..47 de la DJ 1922 / Cert. 44).
2. **Fórmula de Conversión de Montos a Factores:**
   - Sea $S = \sum_{k=8}^{19} \text{Monto}_k$ (la suma de los montos de las columnas 8 a la 19: rentas afectas, exentas e ingresos no constitutivos de renta).
   - Si $S \le 0$, retornar error de validación (`HTTP 422`: *"La suma de los montos base (columnas 8 a 19) debe ser mayor a 0"*).
   - Para cada columna $i \in \{8, \dots, 37\}$:
     $$\text{Factor}_i = \text{Decimal}\left(\frac{\text{Monto}_i}{S}\right).\text{quantize}(\text{Decimal}('0.00000001'), \text{rounding}=\text{ROUND\_DOWN})$$
3. **Validación de Suma Máxima:**
   - La suma de los factores base **del 8 al 19** debe cumplir estrictamente:
     $$\sum_{i=8}^{19} \text{Factor}_i \le 1.00000000$$
   - Los factores **20 al 37** corresponden a créditos tributarios y tasas (TEF/TEX); se calculan con la misma fórmula y precisión de 8 decimales, pero **no** se suman dentro del límite de `1.00000000` de los factores 8..19 (cada factor individual debe estar en el rango $[0, 1]$).
4. **Llave Única y Lógica Upsert (Carga Masiva e Ingreso):**
   - Llave compuesta de negocio: `(corredor_id, ejercicio, mercado, instrumento, secuencia, fecha_pago)`.
   - Al cargar un CSV o guardar, si la llave ya existe para ese corredor, se **actualiza** (`UPDATE`) el registro dejando constancia de `fecha_modificacion` y `origen_fuente` (`CARGA_MASIVA_FACTORES`, `CARGA_MASIVA_MONTOS`, `MANUAL`). Si no existe, se **inserta** (`INSERT`).
   - **Aislamiento Local:** Las modificaciones del corredor nunca sobrescriben registros con `origen = 'SISTEMA'` (Bolsa); siempre prevalece el registro local del corredor en las consultas.

---

## 3. TAREAS DE IMPLEMENTACIÓN POR CAPA

### TAREA A: Base de Datos PostgreSQL (`schema.sql` / migración)
Actualizar o crear la tabla `calificaciones_tributarias` (manteniendo compatibilidad con `declaraciones_tributarias` si ya está referenciada) con los siguientes campos:
- `id` (SERIAL PRIMARY KEY)
- `corredor_id` (INT / VARCHAR, aislamiento por corredor)
- `ejercicio` (INT, 4 dígitos, ej. 2026)
- `mercado` (VARCHAR(10), valores: `'ACN'`, `'CFI'`, `'FFMM'`)
- `instrumento` (VARCHAR(50), ej. `'Copec'`)
- `fecha_pago` (DATE)
- `secuencia` (BIGINT, $> 10000$ para ingresos locales)
- `numero_dividendo` (INT, default `0`)
- `tipo_sociedad` (CHAR(1), `'A'` Abierta o `'C'` Cerrada)
- `valor_historico` (NUMERIC(18, 2), default `0`)
- `acogido_isfut` (BOOLEAN, default `False`)
- `factor_actualizacion` (NUMERIC(12, 8), default `0`)
- `descripcion` (TEXT)
- `origen` (VARCHAR(20): `'CORREDORA'` o `'SISTEMA'`)
- `fuente_ingreso` (VARCHAR(30): `'MANUAL'`, `'CSV_FACTORES'`, `'CSV_MONTOS'`, `'SISTEMA'`)
- `estado` (VARCHAR(20): `'Pendiente'`, `'Aprobado'`, `'Rechazado'`)
- `monto_8` a `monto_37` (NUMERIC(18, 2), nullable, para trazabilidad cuando se ingresa por montos)
- `factor_8` a `factor_37` (NUMERIC(12, 8), default `0.00000000`)
- `fecha_creacion` y `fecha_ultima_modificacion` (TIMESTAMP WITH TIME ZONE)
- Restricción `UNIQUE (corredor_id, ejercicio, mercado, instrumento, secuencia, fecha_pago)`.

### TAREA B: Backend FastAPI (`calculator.py`, `declarations.py`, `main.py`, `mongo_db.py`)
1. **Motor de Cálculo (`calculator.py`):**
   - Implementar `calcular_factores_desde_montos(montos: dict[str, Decimal]) -> dict[str, Decimal]` aplicando `ROUND_DOWN` a 8 decimales.
   - Implementar `validar_factores_8_a_19(factores: dict[str, Decimal])` verificando que $\sum_{i=8}^{19} \text{factor}_i \le \text{Decimal}('1.00000000')$.
   - Exponer endpoint `POST /api/v1/calificaciones/calcular-montos` para que el botón **Calcular** del frontend obtenga los factores exactos antes de grabar.
2. **Endpoints CRUD del Mantenedor (`declarations.py`):**
   - `GET /api/v1/calificaciones`: Filtros opcionales parametrizados por `mercado`, `origen`, `ejercicio`, `estado` e `instrumento`.
   - `POST /api/v1/calificaciones`: Crear calificación (acepta modo `MONTOS` o `FACTORES`), aplica Upsert si existe la llave del corredor y registra auditoría en MongoDB.
   - `PUT /api/v1/calificaciones/{id}`: Modificar montos y/o factores de una calificación local existente, actualizando `fecha_ultima_modificacion` y auditando en MongoDB.
   - `DELETE /api/v1/calificaciones/{id}`: Eliminar calificación local seleccionada (bloqueando eliminación de registros maestros `SISTEMA`) y auditando en MongoDB.
3. **Carga Masiva Dual CSV (`POST /api/v1/calificaciones/carga-masiva`):**
   - Soportar parámetro `tipo_carga` (`FACTORES` | `MONTOS`).
   - Columnas esperadas del CSV (UTF-8, separador `,` o `;` autodetectado): `Ejercicio,Mercado,Instrumento,Fecha,Secuencia,Numero de dividendo,Tipo sociedad,Valor Historico` + `Factor 8`..`Factor 37` (o `Monto 8`..`Monto 37`).
   - Guardar respaldo crudo en MongoDB (`raw_csv_files`), ejecutar Upsert fila por fila en transacción segura y devolver resumen detallado (`insertados`, `actualizados`, `rechazados` con detalle de fila y motivo).

### TAREA C: Frontend React + Vite (Experiencia Superior a los Mockups)
1. **Vista Principal del Mantenedor (`Analista.jsx` / `Mantenedor.jsx`):**
   - **Panel Superior de Filtros:** Selectores para `Tipo de Mercado` (Todos, Acciones `ACN`, `CFI`, Fondos Mutuos `FFMM`), `Origen de la Información` (Todos, Corredora, Sistema), `Periodo Comercial` (Año) + botones **Buscar** y **Limpiar**.
   - **Grilla Principal:** Tabla responsive con cabecera fija, selección de fila mediante radio/checkbox, badge visual para `Origen` (`Corredora` vs `Sistema`) y `Fuente` (`Manual`, `CSV Factores`, `CSV Montos`), y columnas desde `Ejercicio` hasta `Factor 37`.
   - **Barra de Acciones Inferior:** Botones **Ingresar**, **Modificar** (habilitado al seleccionar fila), **Eliminar** (con modal de confirmación) y **Carga Masiva**.
2. **Modal Wizard de Ingreso / Modificación (2 Pasos / Pestañas):**
   - **Paso 1 — Datos del Instrumento:** Mercado (pre-cargado del filtro), Instrumento, Secuencia ($>10000$), Dividendo (`0`), Fecha Pago (date picker), Valor Histórico, Año, Descripción, Checkbox `Acogido a ISFUT/ISIFT`, Factor Actualización (`0`).
   - **Paso 2 — Pestañas "Ingreso por Montos" e "Ingreso por Factores":**
     - En pestaña **Montos**: Inputs numéricos con etiquetas oficiales del SII (DJ 1949 / Cert. 70) y botón **Calcular** que invoca el cálculo y autocompleta la pestaña **Factores**.
     - En pestaña **Factores**: Grilla de los 30 factores (8 al 37) editables con **indicador reactivo en vivo** mostrando la suma de los **Factores 8 al 19** (`Suma F8-F19: 0.XXXXXX / 1.00000000`). Si supera `1.00000000`, el indicador se torna **rojo**, muestra alerta explícita y deshabilita el botón **Grabar**.
3. **Modal de Carga Masiva CSV (Previsualización Inteligente):**
   - Selector de modalidad: **Carga de Factores** o **Carga de Montos**.
   - Botón **Descargar Plantilla CSV** con el formato exacto.
   - Al seleccionar un archivo `.csv`, parsear en cliente y mostrar tabla de previsualización con validación visual por fila (válida, advertencia de suma $>1$ en F8-F19, o error de formato) antes de confirmar la subida al servidor.

### TAREA D: Suite de Pruebas QA (`test_declarations.py` y `qa_runner.py`)
Agregar y ejecutar pruebas automatizadas en `pytest` que validen:
1. Conversión exacta de montos a factores (usando caso real: `[192770580, 64161878, 0, 111812860]` $\rightarrow$ suma base `368745318`, factores `0.52277431`, `0.17400052`, `0`, `0.30322516`).
2. Bloqueo cuando $\sum_{i=8}^{19} \text{Factor}_i > 1.00000000$ y aceptación cuando $\sum_{i=8}^{19} \text{Factor}_i \le 1.00000000$ aun teniendo créditos en factores `20..37`.
3. Comportamiento **Upsert** en carga masiva CSV (primera carga inserta, segunda carga con misma llave actualiza sin duplicar).
4. Protección de registros `SISTEMA` (no modificables/eliminables directamente, prevalencia local del corredor) y registro de auditoría en MongoDB.
5. Regenerar `qa_report.md` y asegurar `0` errores de build/lint en frontend.