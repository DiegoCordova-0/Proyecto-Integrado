# Mantenedor de Calificaciones Tributarias — nuam (DJ 1949 / DJ 1922)

Aplicación web para ingresar, calcular, revisar y auditar calificaciones tributarias asociadas a instrumentos financieros. Automatiza la conversión de montos a factores del SII y el mantenimiento de sus registros, con acceso separado para Analista, Aprobador y Auditor.

El producto está orientado al contexto del mercado regional de Chile, Perú y Colombia y a los procesos referenciados como DJ 1949 y DJ 1922. La lógica de cálculo implementada trabaja con **30 factores, F8–F37 inclusive**. No reemplaza la revisión tributaria profesional ni constituye una certificación de cumplimiento legal.

## Arquitectura y tecnologías

```text
Navegador (React + Vite)
        │ REST / JSON + JWT
        ▼
API (Python + FastAPI + Uvicorn)
   ├── PostgreSQL (Supabase) — usuarios y calificaciones
   └── MongoDB Atlas — eventos de auditoría y respaldos CSV
```

| Componente | Tecnología y responsabilidad |
|---|---|
| Frontend | React + Vite; SPA responsiva con estilos propios e identidad visual nuam. El `package.json` actual declara React `^19.3.1` y Vite `^8.3.4` (no React 18). |
| Backend | Python, FastAPI y Uvicorn. API desacoplada del cliente web; utiliza `Decimal` y `ROUND_DOWN` para truncar los resultados a 8 decimales sin pasar por aritmética binaria de punto flotante. |
| PostgreSQL | Instancia PostgreSQL configurable, incluida Supabase. `backend/schema.sql` define usuarios, roles, calificaciones, restricciones `CHECK` y la llave única compuesta de negocio. El backend se conecta mediante `psycopg2` y usa transacciones PostgreSQL con propiedades ACID por operación. |
| MongoDB | MongoDB Atlas configurable. La aplicación inserta eventos en `nuam_audit.audit_logs` y almacena cargas originales en `raw_csv_files`. La escritura de auditoría es append-only desde la aplicación; la inmutabilidad debe reforzarse con permisos y políticas de retención en MongoDB. |

### Nota sobre los factores

El rango F8–F37 contiene **30** posiciones, no 29. El flujo de calificaciones utiliza esas 30 posiciones. El esquema también mantiene un flujo de declaraciones anterior con 29 columnas `factor_1`–`factor_29`; no confundir ambos modelos.

## Roles y control de acceso

La API valida tokens JWT y aplica permisos por rol (`RBAC`). El backend es la autoridad para las operaciones; ocultar un botón en la interfaz no sustituye la autorización del endpoint.

| Rol | Permisos principales |
|---|---|
| **Analista** | Consultar sus calificaciones; ingresar manualmente o mediante CSV por factores o montos; modificar y eliminar registros propios que no sean maestros `SISTEMA`; exportar resultados desde la interfaz. |
| **Aprobador** | Consultar la bandeja global; revisar el detalle de los 30 factores; aprobar o rechazar calificaciones pendientes que no sean registros `SISTEMA`. |
| **Auditor** | Consultar la bitácora cronológica, filtrar por rango de tiempo, mes, usuario, acción y estado, exportar el resultado filtrado y abrir el documento JSON completo del evento. |

## Reglas de negocio y seguridad

### Cálculo y persistencia

- Los montos F8–F37 se convierten en factores con precisión de 8 decimales y truncamiento `ROUND_DOWN`.
- La suma de los factores base debe cumplir:

  ```text
  F8 + F9 + ... + F19 <= 1.00000000
  ```

- F20–F37 corresponden a créditos y se validan independientemente del límite de suma de F8–F19; cada factor individual debe estar entre 0 y 1.
- La llave de upsert es `(corredor_id, ejercicio, mercado, instrumento, secuencia, fecha_pago)`. Si una calificación de esa llave ya existe, se actualiza; de lo contrario, se inserta.
- PostgreSQL aplica restricciones `UNIQUE` y `CHECK` para proteger la integridad de los datos. Las operaciones de escritura manejan `commit` y `rollback` a nivel de operación.
- **Alcance de las cargas CSV:** se procesan fila por fila y la respuesta incluye filas insertadas, actualizadas o rechazadas. No hay rollback global de todo el lote ante una fila inválida: las filas ya confirmadas no se revierten por el rechazo de otra fila.
- La carga masiva de calificaciones admite CSV de hasta 10 MB e intenta guardar una copia cruda en MongoDB. En el flujo de declaraciones, una falla al almacenar el respaldo impide continuar con esa carga.

### Controles de seguridad

- JWT de acceso de 15 minutos y refresh tokens de 7 días. La renovación revoca el refresh anterior y emite uno nuevo.
- Las contraseñas se verifican con `bcrypt`; el secreto JWT se configura fuera del código mediante `JWT_SECRET_KEY` (mínimo 32 caracteres).
- Consultas de valores SQL parametrizadas con `psycopg2`.
- Protección contra *CSV Formula Injection*: las celdas de texto de las cargas que comienzan con `=`, `+`, `-` o `@` (también después de espacios) se rechazan; las exportaciones CSV del frontend prefijan esas celdas con apóstrofe y usan BOM UTF-8.
- Los registros maestros `origen = SISTEMA` no se pueden modificar, eliminar, aprobar ni rechazar desde las operaciones del mantenedor.
- La API añade cabeceras como `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y una política CSP básica.
- Estas medidas apoyan una implementación segura y consideran las leyes chilenas 21.719 y 21.459 como referencia del proyecto; **no equivalen a una auditoría legal, certificación OWASP ni declaración formal de cumplimiento**.

## Instalación y ejecución local

### Requisitos

- Python 3.11 o superior.
- Node.js compatible con Vite 8: `^20.19.0` o `>=22.12.0` (Node.js 18 no satisface el requisito declarado por la versión instalada de Vite).
- npm.
- Instancias y credenciales de PostgreSQL/Supabase y MongoDB Atlas.

### 1. Obtener dependencias

Desde la raíz del repositorio:

```powershell
python -m pip install -r backend/requirements.txt
```

### 2. Configurar variables de entorno

Crea los archivos locales a partir de las plantillas:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

`frontend/.env.example` define `VITE_API_URL`. El `backend/.env.example` actual no contiene la configuración de base de datos ni de JWT; agrega esas variables a `backend/.env`:

```dotenv
DB_HOST=<host-postgresql>
DB_PORT=5432
DB_USER=<usuario>
DB_PASSWORD=<contraseña>
DB_NAME=postgres
DB_CONNECT_TIMEOUT=5

JWT_SECRET_KEY=<secreto-aleatorio-de-al-menos-32-caracteres>
FRONTEND_ORIGIN=http://localhost:5173
MONGO_URI=<cadena-de-conexion-de-mongodb-atlas>
```

Configura `frontend/.env` con la URL de la API local:

```dotenv
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

Genera un secreto JWT localmente; no reutilices este secreto en producción:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

No agregues archivos `.env` con credenciales reales al control de versiones.

### 3. Inicializar PostgreSQL y datos de prueba

1. Ejecuta el contenido de `backend/schema.sql` en el SQL Editor de Supabase o contra la instancia PostgreSQL configurada.
2. Con las variables de `backend/.env` configuradas, crea el usuario de prueba que soporta el script actual:

   ```powershell
   Set-Location backend
   python seed_data.py
   Set-Location ..
   ```

   El script crea o actualiza el usuario Analista y una declaración de ejemplo. No crea los usuarios Aprobador ni Auditor.
3. Configura MongoDB Atlas en `MONGO_URI`. La aplicación crea las colecciones al insertar documentos; el usuario de base de datos debe tener los permisos necesarios para escribir y consultar.

### 4. Iniciar backend y frontend

En una terminal, desde la raíz del repositorio:

```powershell
uvicorn backend.main:app --reload --port 8000
```

En otra terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Vite muestra la dirección local al iniciar (normalmente `http://localhost:5173`). La documentación interactiva de FastAPI está disponible en `http://127.0.0.1:8000/docs`.

## Credenciales de prueba

Credenciales para uso exclusivamente local/académico. Cambia las contraseñas y secretos antes de cualquier despliegue. El repositorio solo incluye la contraseña del usuario Analista que genera `backend/seed_data.py`; no se deben asumir contraseñas para los otros roles.

| Rol | Usuario | Contraseña / estado |
|---|---|---|
| Analista | `analista@nuam.com` (o RUT `12345678-9`) | `Analista123!` — creada por `backend/seed_data.py`. |
| Aprobador | `aprobador@nuam.com` | No creado por el script de datos incluido; debe provisionarse en la base de datos con una contraseña bcrypt. |
| Auditor | `auditor@nuam.com` | No creado por el script de datos incluido; debe provisionarse en la base de datos con una contraseña bcrypt. |

## Calidad y pruebas

Desde la raíz del repositorio:

```powershell
python -m pytest backend -q
python backend/qa_runner.py
```

`pytest` ejecuta la suite backend. En la validación registrada para esta entrega, el resultado fue **20 pruebas y 11 subcasos aprobados**. El runner ejecuta las pruebas individualmente y genera o reemplaza `backend/qa_report.md` con el resultado y la fecha de ejecución.

Para comprobar frontend:

```powershell
Set-Location frontend
npm run lint
npm run build
```

### Resumen de casos CP-01 a CP-10

Estos identificadores resumen escenarios funcionales y no funcionales del proyecto. `qa_runner.py` reporta los node IDs de pytest, no los códigos `CP-*`.

| Caso | Escenario |
|---|---|
| **CP-01** | Inicio de sesión, validación de credenciales y verificación de contraseñas bcrypt. |
| **CP-02** | Emisión de JWT y control de acceso por rol; rechazo de usuarios sin permisos. |
| **CP-03** | Conversión de montos a los factores F8–F37 mediante aritmética decimal. |
| **CP-04** | Truncamiento hacia abajo a ocho decimales, sin redondeo ni punto flotante binario. |
| **CP-05** | Validación de la suma F8–F19 y validación independiente de F20–F37. |
| **CP-06** | Persistencia por upsert con llave compuesta y protección de registros `SISTEMA`. |
| **CP-07** | Aprobación o rechazo únicamente de calificaciones pendientes. |
| **CP-08** | Consulta global por filtros, incluyendo “todos los estados”, con SQL parametrizado. |
| **CP-09** | Carga CSV por filas, detección de errores de formato, origen de ingreso y rechazo de celdas tipo fórmula. |
| **CP-10** | Trazabilidad en MongoDB, consulta/exportación de auditoría y validación de build/lint del frontend. |

## Autores

- Diego Ignacio Córdova López
- Eduardo Ignacio Sánchez Palacios

**INACAP — Proyecto Integrado TI**
