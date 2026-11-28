# Guion de presentación - Evaluación 4

## Elevator pitch

**Duración objetivo: 2 minutos**

**Pregunta ancla (0:00-0:20)**  
"¿Qué pasa cuando los factores tributarios se calculan manualmente, los datos quedan en hojas dispersas y no existe una trazabilidad clara de cada operación?"

**Impacto (0:20-0:35)**  
"Esto genera retrasos, retrabajo y riesgo de inconsistencias en un proceso donde la precisión y el control son fundamentales."

**Equipo (0:35-0:55)**  
"Somos Diego Córdova y Eduardo Sánchez, equipo de desarrollo del Proyecto Integrado TI. Diego participa en backend, arquitectura de datos y seguridad; Eduardo, en frontend, experiencia de usuario y calidad."

**Solución (0:55-1:20)**  
"NUAM es un mantenedor web de calificaciones tributarias para ACN, CFI y FFMM. Automatiza la conversión de montos a los factores F8-F37 con precisión de ocho decimales, valida la suma F8-F19 y permite ingresar datos manualmente o mediante CSV."

**Beneficios (1:20-1:45)**  
"La solución separa los roles de analista, aprobador y auditor, protege los registros maestros, registra cada operación y permite revisar la trazabilidad completa sin depender de cálculos manuales."

**Invitación (1:45-2:00)**  
"Los invitamos a experimentar NUAM: ingresaremos una calificación, calcularemos sus factores, verificaremos la aprobación y revisaremos el evento generado en la bitácora."

## Demostración funcional

1. Mostrar inicio de sesión y explicar los tres roles.
2. Como Analista, aplicar filtros y abrir el mantenedor.
3. Seleccionar "Ingresar", ingresar datos de una calificación de prueba y cambiar a "Montos".
4. Pulsar "Calcular factores" y mostrar que se completan los 30 factores.
5. Mostrar la suma F8-F19 y guardar la calificación.
6. Como Aprobador, buscar pendientes, abrir el detalle y aprobar o rechazar.
7. Como Auditor, mostrar la bitácora, aplicar filtros y abrir el JSON del evento.
8. Cerrar con carga masiva o exportación si el tiempo lo permite.

## Datos verificables para responder

- Backend: Python, FastAPI y Uvicorn.
- Frontend: React y Vite.
- Bases de datos: PostgreSQL/Supabase y MongoDB Atlas.
- Seguridad: JWT, refresh tokens, RBAC y consultas SQL parametrizadas.
- Cálculo: 30 factores, F8-F37.
- Precisión: `Decimal` y `ROUND_DOWN` a ocho decimales.
- Suma regulada: F8-F19 debe ser menor o igual a 1.00000000.
- Llave de upsert: corredor, ejercicio, mercado, instrumento, secuencia y fecha de pago.
- QA registrado: 20 pruebas backend y 11 subcasos aprobados.

## Respuestas técnicas probables

**¿Por qué PostgreSQL y MongoDB?**  
PostgreSQL mantiene la integridad de las calificaciones y reglas únicas; MongoDB conserva eventos de auditoría y respaldos de cargas.

**¿Cómo se evita el redondeo incorrecto?**  
Los cálculos usan `Decimal` y `ROUND_DOWN`, evitando aritméticas binarias y truncando a ocho decimales.

**¿Cómo protege el sistema los datos?**  
JWT identifica al usuario, RBAC limita las operaciones por rol y PostgreSQL aplica restricciones y transacciones.

**¿Qué pasa si el CSV contiene una fila inválida?**  
El sistema procesa por fila y devuelve insertados, actualizados y rechazados. Las filas válidas confirmadas no se revierten por el rechazo posterior de otra fila.

**¿Qué no implica la solución?**  
Es una herramienta de apoyo que mejora precisión y trazabilidad; no reemplaza la revisión profesional ni constituye certificación legal.

**Plan de mantención:**  
Monitoreo diario de errores y disponibilidad, respaldos y actualizaciones mensuales, revisiones trimestrales de seguridad y rendimiento, y resolución continua de incidencias.
