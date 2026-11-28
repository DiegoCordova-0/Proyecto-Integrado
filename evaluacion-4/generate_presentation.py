from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


OUT = "presentacion-evaluacion-4.pptx"

NAVY = RGBColor(18, 28, 63)
BLUE = RGBColor(38, 99, 235)
CYAN = RGBColor(35, 184, 196)
TEAL = RGBColor(20, 184, 166)
WHITE = RGBColor(255, 255, 255)
INK = RGBColor(30, 41, 59)
MUTED = RGBColor(100, 116, 139)
LIGHT = RGBColor(243, 246, 252)
GREEN = RGBColor(22, 163, 74)
RED = RGBColor(220, 38, 38)
GOLD = RGBColor(245, 158, 11)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def textbox(slide, text, x, y, w, h, size=20, color=INK, bold=False,
            align=PP_ALIGN.LEFT, font="Aptos", valign=MSO_ANCHOR.TOP):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    shape.text_frame.clear()
    shape.text_frame.word_wrap = True
    shape.text_frame.vertical_anchor = valign
    p = shape.text_frame.paragraphs[0]
    p.text = text
    p.alignment = align
    run = p.runs[0]
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def rect(slide, x, y, w, h, fill, radius=True, line=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    return shape


def title(slide, text, subtitle=None):
    textbox(slide, text, 0.7, 0.45, 11.9, 0.55, 30, NAVY, True)
    rect(slide, 0.7, 1.12, 0.8, 0.06, CYAN, radius=False)
    if subtitle:
        textbox(slide, subtitle, 0.7, 1.25, 11.9, 0.42, 13, MUTED)


def footer(slide, number):
    textbox(slide, "NUAM  |  Proyecto Integrado TI  |  INACAP", 0.7, 7.08, 8.5, 0.22, 9, MUTED)
    textbox(slide, f"{number:02d}", 12.05, 7.04, 0.55, 0.25, 9, MUTED, True, PP_ALIGN.RIGHT)


def add_bullets(slide, items, x, y, w, h, size=18, color=INK, bullet_color=CYAN):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(11)
        p.text = "●  " + item
    return box


# 1 - Portada
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, NAVY, radius=False)
rect(slide, 9.85, 0, 3.483, 7.5, BLUE, radius=False)
rect(slide, 10.35, 1.15, 2.45, 2.45, CYAN, radius=True)
textbox(slide, "NUAM", 10.35, 1.72, 2.45, 0.55, 36, WHITE, True, PP_ALIGN.CENTER)
textbox(slide, "CALIFICACIONES", 10.35, 2.35, 2.45, 0.35, 13, NAVY, True, PP_ALIGN.CENTER)
textbox(slide, "Mantenedor de Calificaciones\nTributarias", 0.85, 1.35, 8.45, 1.45, 38, WHITE, True)
textbox(slide, "Automatización confiable para un proceso tributario complejo", 0.88, 3.12, 7.8, 0.55, 20, RGBColor(196, 212, 255))
textbox(slide, "Diego Ignacio Córdova López\nEduardo Ignacio Sánchez Palacios", 0.88, 5.55, 6.2, 0.75, 15, WHITE)
textbox(slide, "Evaluación 4  ·  Presentación final", 0.88, 6.55, 6.2, 0.35, 12, RGBColor(196, 212, 255))

# 2 - Pregunta ancla
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "La problemática", "El desafío no es solo registrar datos: es mantener precisión y trazabilidad.")
rect(slide, 0.75, 1.85, 11.85, 1.45, LIGHT)
textbox(slide, "¿Qué pasa cuando los factores tributarios se calculan de forma manual,\nse documentan en hojas dispersas y no queda registro claro de quién aprobó qué?",
         1.15, 2.12, 11.05, 0.92, 24, NAVY, True, PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
textbox(slide, "Mantenedores manuales generan riesgo operativo", 0.9, 4.05, 3.6, 0.5, 17, RED, True, PP_ALIGN.CENTER)
textbox(slide, "Los datos tributarios exigen precisión", 4.86, 4.05, 3.6, 0.5, 17, GOLD, True, PP_ALIGN.CENTER)
textbox(slide, "Cada operación necesita trazabilidad", 8.82, 4.05, 3.6, 0.5, 17, BLUE, True, PP_ALIGN.CENTER)
for x, text in [(0.9, "Cálculos inconsistentes\nRetrabajo y demoras"), (4.86, "30 factores\nReglas de suma estrictas"), (8.82, "Responsable\nResultado\nFecha")]:
    rect(slide, x, 4.72, 3.6, 1.05, WHITE)
    textbox(slide, text, x + 0.15, 4.93, 3.30, 0.58, 16, INK, True, PP_ALIGN.CENTER)
footer(slide, 2)

# 3 - Impacto
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Impacto del problema", "Consecuencias de un proceso tributario poco controlado.")
cards = [
    ("1", "Operación", "Más tiempo revisando registros y corrigiendo cálculos."),
    ("2", "Control", "Difícil verificar cambios, responsables y estados."),
    ("3", "Confianza", "Mayor exposición a errores, inconsistencias y reprocesos."),
]
for i, (n, head, body) in enumerate(cards):
    x = 0.75 + i * 4.18
    rect(slide, x, 1.85, 3.75, 3.65, LIGHT)
    rect(slide, x + 0.28, 2.15, 0.68, 0.68, [RED, GOLD, BLUE][i], True)
    textbox(slide, n, x + 0.28, 2.29, 0.68, 0.30, 19, WHITE, True, PP_ALIGN.CENTER)
    textbox(slide, head, x + 0.28, 3.05, 3.15, 0.45, 21, NAVY, True)
    textbox(slide, body, x + 0.28, 3.65, 3.12, 1.15, 15, INK)
rect(slide, 0.75, 5.88, 11.85, 0.72, NAVY)
textbox(slide, "La solución debe reducir el margen de error sin perder el control humano.", 0.95, 6.08, 11.45, 0.35, 17, WHITE, True, PP_ALIGN.CENTER)
footer(slide, 3)

# 4 - Equipo
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Equipo de desarrollo", "Responsabilidades complementarias sobre una solución integral.")
rect(slide, 0.75, 1.75, 5.55, 4.65, LIGHT)
rect(slide, 6.78, 1.75, 5.55, 4.65, LIGHT)
rect(slide, 1.55, 2.15, 1.15, 1.15, BLUE, True)
textbox(slide, "DC", 1.55, 2.44, 1.15, 0.50, 30, WHITE, True, PP_ALIGN.CENTER)
textbox(slide, "Diego Ignacio\nCórdova López", 3.02, 2.15, 2.75, 0.80, 20, NAVY, True)
textbox(slide, "Backend y reglas de negocio\nArquitectura de datos\nSeguridad y control de roles", 1.15, 3.55, 4.75, 1.55, 16, INK)

rect(slide, 7.58, 2.15, 1.15, 1.15, CYAN, True)
textbox(slide, "ES", 7.58, 2.44, 1.15, 0.50, 30, WHITE, True, PP_ALIGN.CENTER)
textbox(slide, "Eduardo Ignacio\nSánchez Palacios", 9.05, 2.15, 2.75, 0.80, 20, NAVY, True)
textbox(slide, "Frontend React\nExperiencia de usuario\nPruebas y documentación", 8.18, 3.55, 3.72, 1.55, 16, INK)
footer(slide, 4)

# 5 - Solución
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Nuestra solución", "NUAM convierte, valida y controla el ciclo completo de las calificaciones.")
layers = [
    ("1", "React + Vite", "Interfaz por roles"),
    ("2", "FastAPI", "Cálculo, CRUD y seguridad"),
    ("3", "PostgreSQL", "Calificaciones y integridad"),
    ("4", "MongoDB", "Auditoría y respaldos"),
]
for i, (n, name, detail) in enumerate(layers):
    x = 0.75 + i * 3.08
    rect(slide, x, 1.95, 2.72, 2.0, [LIGHT, LIGHT, LIGHT, LIGHT][i])
    rect(slide, x + 0.95, 1.65, 0.82, 0.82, [BLUE, TEAL, NAVY, GOLD][i], True)
    textbox(slide, n, x + 0.95, 1.88, 0.82, 0.30, 17, WHITE, True, PP_ALIGN.CENTER)
    textbox(slide, name, x + 0.18, 2.74, 2.36, 0.42, 18, NAVY, True, PP_ALIGN.CENTER)
    textbox(slide, detail, x + 0.18, 3.25, 2.36, 0.42, 13, MUTED, False, PP_ALIGN.CENTER)
rect(slide, 0.75, 4.55, 11.85, 1.45, NAVY)
textbox(slide, "30 factores  ·  cálculos a 8 decimales  ·  RBAC  ·  JWT  ·  cargas CSV  ·  auditoría",
         1.05, 4.98, 11.25, 0.55, 19, WHITE, True, PP_ALIGN.CENTER)
textbox(slide, "La solución no sustituye la revisión profesional: aporta precisión, control y trazabilidad.",
         1.35, 6.28, 10.65, 0.35, 14, MUTED, False, PP_ALIGN.CENTER)
footer(slide, 5)

# 6 - Beneficios
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Beneficios del valor agregado", "Una experiencia diseñada para prevenir errores y facilitar decisiones.")
benefits = [
    ("Cálculo asistido", "Convierte montos a 30 factores con truncamiento a 8 decimales."),
    ("Validación inmediata", "Bloquea el grabado si la suma F8-F19 supera 1.00000000."),
    ("Carga masiva", "Procesa CSV por factores o montos con upsert fila por fila."),
    ("Control por roles", "Analista, aprobador y auditor tienen vistas y permisos separados."),
]
for i, (head, body) in enumerate(benefits):
    x = 0.75 + (i % 2) * 6.08
    y = 1.72 + (i // 2) * 2.20
    rect(slide, x, y, 5.62, 1.78, LIGHT)
    rect(slide, x + 0.28, y + 0.32, 0.16, 1.12, [BLUE, TEAL, GOLD, CYAN][i], radius=False)
    textbox(slide, head, x + 0.68, y + 0.32, 4.58, 0.38, 19, NAVY, True)
    textbox(slide, body, x + 0.68, y + 0.82, 4.50, 0.62, 14, INK)
rect(slide, 0.75, 6.25, 11.85, 0.48, WHITE)
textbox(slide, "Resultado: menos retrabajo, mayor control y una decisión verificable.", 0.95, 6.33, 11.45, 0.28, 16, GREEN, True, PP_ALIGN.CENTER)
footer(slide, 6)

# 7 - Arquitectura y flujo
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Flujo funcional", "De un dato fuente a una decisión aprobada y auditable.")
steps = [
    ("1", "Ingresar", "Manual o CSV"),
    ("2", "Calcular", "Montos → factores"),
    ("3", "Validar", "Suma F8-F19"),
    ("4", "Aprobar", "Bandeja del rol"),
    ("5", "Auditar", "Eventos y detalle"),
]
for i, (n, head, detail) in enumerate(steps):
    x = 0.55 + i * 2.55
    rect(slide, x, 2.05, 2.15, 2.45, LIGHT)
    rect(slide, x + 0.65, 1.72, 0.85, 0.85, [BLUE, CYAN, GOLD, TEAL, NAVY][i], True)
    textbox(slide, n, x + 0.65, 1.96, 0.85, 0.30, 17, WHITE, True, PP_ALIGN.CENTER)
    textbox(slide, head, x + 0.18, 3.00, 1.79, 0.38, 18, NAVY, True, PP_ALIGN.CENTER)
    textbox(slide, detail, x + 0.18, 3.55, 1.79, 0.55, 13, MUTED, False, PP_ALIGN.CENTER)
    if i < 4:
        textbox(slide, "→", x + 2.16, 2.95, 0.38, 0.45, 22, BLUE, True, PP_ALIGN.CENTER)
rect(slide, 0.75, 5.15, 11.85, 1.15, NAVY)
textbox(slide, "Tecnología segura", 1.05, 5.40, 2.20, 0.35, 16, CYAN, True)
textbox(slide, "JWT + RBAC  ·  consultas parametrizadas  ·  restricciones PostgreSQL  ·  registros de auditoría MongoDB",
         3.15, 5.39, 9.15, 0.42, 15, WHITE, True)
footer(slide, 7)

# 8 - Demostración
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Demostración funcional", "Ruta recomendada para una prueba clara y fluida.")
demo = [
    ("01", "Analista", "Filtrar por mercado y revisar la tabla."),
    ("02", "Calcular", "Ingresar montos y aplicar “Calcular factores”."),
    ("03", "Validar", "Mostrar la suma F8-F19 y guardar."),
    ("04", "Aprobador", "Abrir la bandeja, ver detalle y aprobar."),
    ("05", "Auditor", "Filtrar la bitácora y abrir un evento."),
]
for i, (n, head, body) in enumerate(demo):
    y = 1.55 + i * 0.98
    rect(slide, 0.75, y, 11.85, 0.78, LIGHT)
    rect(slide, 0.95, y + 0.17, 0.58, 0.44, [BLUE, CYAN, GOLD, TEAL, NAVY][i], True)
    textbox(slide, n, 0.95, y + 0.23, 0.58, 0.25, 12, WHITE, True, PP_ALIGN.CENTER)
    textbox(slide, head, 1.82, y + 0.17, 2.15, 0.36, 17, NAVY, True)
    textbox(slide, body, 4.05, y + 0.17, 8.05, 0.42, 15, INK)
textbox(slide, "Previamente: iniciar backend y frontend, configurar datos de prueba y abrir dos pestañas.", 1.05, 6.62, 11.25, 0.30, 12, MUTED, False, PP_ALIGN.CENTER)
footer(slide, 8)

# 9 - Resultados y calidad
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Resultados y calidad", "La implementación cuenta con validaciones automatizadas y controles registrados.")
metrics = [
    ("20", "pruebas backend"),
    ("11", "subcasos QA"),
    ("30", "factores F8-F37"),
]
for i, (n, label) in enumerate(metrics):
    x = 0.75 + i * 4.08
    rect(slide, x, 1.75, 3.65, 1.55, NAVY)
    textbox(slide, n, x, 1.98, 3.65, 0.55, 32, WHITE, True, PP_ALIGN.CENTER)
    textbox(slide, label, x, 2.62, 3.65, 0.35, 13, RGBColor(196, 212, 255), True, PP_ALIGN.CENTER)
textbox(slide, "Cobertura principal", 0.75, 3.85, 3.2, 0.40, 18, NAVY, True)
add_bullets(slide, [
    "Conversión y truncamiento decimal.",
    "Restricción de suma F8-F19.",
    "Upsert, estados y registros SISTEMA.",
    "Auditoría, filtros y cargas CSV.",
], 0.75, 4.38, 5.30, 1.90, 15)
textbox(slide, "Validación registrada", 7.12, 3.85, 3.2, 0.40, 18, NAVY, True)
add_bullets(slide, [
    "Resultado QA global: PASS.",
    "Reporte disponible en backend/qa_report.md.",
    "Build y lint incluidos en el proceso de calidad.",
], 7.12, 4.38, 5.15, 1.90, 15)
footer(slide, 9)

# 10 - Mantención e invitación
slide = prs.slides.add_slide(prs.slide_layouts[6])
title(slide, "Mantención y siguiente paso", "Sostenibilidad para evolucionar sin perder seguridad ni trazabilidad.")
rect(slide, 0.75, 1.70, 7.55, 4.65, LIGHT)
phases = [
    ("Diario", "Revisión de errores y disponibilidad."),
    ("Mensual", "Actualizaciones, respaldos y auditorías."),
    ("Trimestral", "Optimización, seguridad y pruebas."),
    ("Continuo", "Monitoreo de logs y resolución de incidencias."),
]
for i, (head, body) in enumerate(phases):
    y = 2.05 + i * 0.98
    textbox(slide, head, 1.05, y, 1.45, 0.35, 16, BLUE, True)
    textbox(slide, body, 2.58, y, 5.15, 0.42, 14, INK)
rect(slide, 8.68, 1.70, 3.92, 4.65, NAVY)
textbox(slide, "Experimente el valor", 9.10, 2.20, 3.08, 0.45, 22, WHITE, True, PP_ALIGN.CENTER)
textbox(slide, "Pruebe el cálculo,\nla carga masiva,\nla aprobación y\nla trazabilidad.",
         9.10, 3.05, 3.08, 1.45, 18, RGBColor(196, 212, 255), True, PP_ALIGN.CENTER)
textbox(slide, "Conoce NUAM", 9.10, 5.20, 3.08, 0.48, 20, CYAN, True, PP_ALIGN.CENTER)
textbox(slide, "¿Qué calificación desea revisar primero?", 1.05, 6.65, 7.05, 0.32, 16, NAVY, True)
footer(slide, 10)

prs.save(OUT)
print(OUT)
