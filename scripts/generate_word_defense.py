import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = docx.Document()

# Page Setup - Margins (1 inch)
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Colors
COLOR_PRIMARY = RGBColor(27, 54, 93)     # Navy #1B365D
COLOR_SECONDARY = RGBColor(46, 107, 158) # Steel Blue #2E6B9E
COLOR_DARK = RGBColor(34, 34, 34)         # Charcoal
COLOR_ALERT = RGBColor(192, 57, 43)       # Dark Red #C0392B
COLOR_SUCCESS = RGBColor(39, 174, 96)     # Green

def set_cell_background(cell, fill_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY
    return p

def add_subtitle(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(14)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(12)
    run.font.italic = True
    run.font.color.rgb = COLOR_SECONDARY
    return p

def add_heading_1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY
    return p

def add_heading_2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(12.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_SECONDARY
    return p

def add_heading_3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = COLOR_DARK
    return p

def add_p(text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.font.name = 'Calibri'
        r_bold.font.size = Pt(10)
        r_bold.font.bold = True
        r_bold.font.color.rgb = COLOR_DARK
    r_text = p.add_run(text)
    r_text.font.name = 'Calibri'
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = COLOR_DARK
    return p

def add_bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.font.name = 'Calibri'
        r_bold.font.size = Pt(10)
        r_bold.font.bold = True
        r_bold.font.color.rgb = COLOR_DARK
    r_text = p.add_run(text)
    r_text.font.name = 'Calibri'
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = COLOR_DARK
    return p

def add_callout(title, body, alert_type="info"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    fill_hex = "F0F4F8"
    border_color = "1B365D"
    title_color = COLOR_PRIMARY
    if alert_type == "warning":
        fill_hex = "FFF8E7"
        border_color = "D97706"
        title_color = RGBColor(180, 83, 9)
    elif alert_type == "alert":
        fill_hex = "FDEDEC"
        border_color = "C0392B"
        title_color = COLOR_ALERT
    elif alert_type == "success":
        fill_hex = "EAFAF1"
        border_color = "27AE60"
        title_color = COLOR_SUCCESS

    set_cell_background(cell, fill_hex)
    
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    cell._tc.get_or_add_tcPr().append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    r_title = p.add_run(f"■ {title}\n")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(10.5)
    r_title.font.bold = True
    r_title.font.color.rgb = title_color
    
    r_body = p.add_run(body)
    r_body.font.name = 'Calibri'
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = COLOR_DARK
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_dialogue(parada_label, question, answer_4_steps, warning_alarm=None):
    add_heading_3(f"Parada de Defensa: {parada_label}")
    
    # Question box
    tbl_q = doc.add_table(rows=1, cols=1)
    tbl_q.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_q = tbl_q.cell(0, 0)
    set_cell_margins(cell_q, top=100, bottom=100, left=160, right=160)
    set_cell_background(cell_q, "EBF5FB")
    b_q = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="2980B9"/>
        </w:tcBorders>
    ''')
    cell_q._tc.get_or_add_tcPr().append(b_q)
    pq = cell_q.paragraphs[0]
    rq_label = pq.add_run("Pregunta Oficial del Docente (Cristian Calderón):\n")
    rq_label.font.bold = True
    rq_label.font.size = Pt(9.5)
    rq_label.font.color.rgb = RGBColor(41, 128, 185)
    rq = pq.add_run(f'«{question}»')
    rq.font.italic = True
    rq.font.size = Pt(10)
    rq.font.color.rgb = COLOR_DARK
    
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    
    if warning_alarm:
        tbl_w = doc.add_table(rows=1, cols=1)
        tbl_w.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell_w = tbl_w.cell(0, 0)
        set_cell_margins(cell_w, top=80, bottom=80, left=140, right=140)
        set_cell_background(cell_w, "FDEDEC")
        b_w = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="C0392B"/>
            </w:tcBorders>
        ''')
        cell_w._tc.get_or_add_tcPr().append(b_w)
        pw = cell_w.paragraphs[0]
        rw_label = pw.add_run("⚠ SEÑAL DE ALARMA DE D6 (Lo que NUNCA debes decir):\n")
        rw_label.font.bold = True
        rw_label.font.size = Pt(9)
        rw_label.font.color.rgb = COLOR_ALERT
        rw = pw.add_run(warning_alarm)
        rw.font.size = Pt(9)
        rw.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # Response 4 steps
    tbl_a = doc.add_table(rows=1, cols=1)
    tbl_a.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_a = tbl_a.cell(0, 0)
    set_cell_margins(cell_a, top=100, bottom=100, left=160, right=160)
    set_cell_background(cell_a, "F9FBF9")
    b_a = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="27AE60"/>
        </w:tcBorders>
    ''')
    cell_a._tc.get_or_add_tcPr().append(b_a)
    pa = cell_a.paragraphs[0]
    ra_label = pa.add_run("Respuesta Técnica Modelo (Framework de 4 Pasos de D6):\n")
    ra_label.font.bold = True
    ra_label.font.size = Pt(9.5)
    ra_label.font.color.rgb = COLOR_SUCCESS
    
    for step_num, step_title, step_content in answer_4_steps:
        r_step = pa.add_run(f"\n{step_num}. {step_title}: ")
        r_step.font.bold = True
        r_step.font.size = Pt(9.5)
        r_step.font.color.rgb = COLOR_PRIMARY
        r_c = pa.add_run(step_content)
        r_c.font.size = Pt(9.5)
        r_c.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ==================== DOCUMENT CONTENT ====================

add_title("GUÍA MAESTRA DE DEFENSA TÉCNICA Y PREPARACIÓN EP1")
add_subtitle("Caso VidalStore · DSY1107 Desarrollo Cloud Native I · DUOC UC (2026-02)\nBasado en Clase D6, Pulso.pdf y Resoluciones del Profesor Cristian Calderón (Umbingelelo)")

add_callout(
    "DATOS GENERALES DE LA EVALUACIÓN",
    "• Integrantes del Equipo: Oscar Garrido, David, Iván.\n"
    "• Fecha de Entrega de Repositorios (AVA): Lunes 21 de Septiembre de 2026, 23:59 hrs.\n"
    "• Fechas de Defensas Individuales: Martes 22 y Jueves 24 de Septiembre de 2026.\n"
    "• Duración del Turno de Defensa: 15 minutos cronometrados por grupo.\n"
    "• Ponderación Oficial: 40% Código Grupal (repositorios) | 60% Presentación Técnica Individual.",
    "info"
)

# ----------------------------------------------------
# SECCIÓN 1
# ----------------------------------------------------
add_heading_1("1. Estructura y Ponderación Real de la EP1")
add_p("La Evaluación Parcial N°1 pondera un 40% de la nota final de la asignatura y se divide en dos instancias muy claras según la Clase D6 (Slide 3):")
add_bullet("Representa el 40% de la nota de la EP1. Se entrega en el AVA a las 23:59 hrs declarando el enlace a los 3 repositorios y el hash del último commit de la rama main. El docente lo clona y califica posteriormente.", "El Código Grupal (40%): ")
add_bullet("Representa el 60% de la nota de la EP1. Es estrictamente INDIVIDUAL. Cada integrante defiende por separado frente al computador. Vale más que todo el código junto: un estudiante con el sistema perfecto reprobará si no sabe explicar sus decisiones o cómo viaja un dato de punta a punta.", "La Presentación / Defensa Individual (60%): ")

add_callout(
    "REGLA DE ORO DE EVALUACIÓN INDIVIDUAL",
    "«Puedes tener el sistema perfecto y reprobar si no puedes explicar por qué lo hiciste así. Y al revés no funciona: sin sistema no hay nada que defender. En la defensa te van a preguntar por partes que construyó tu compañero, y responder 'eso lo hizo el otro' equivale a cero.» (D6 Slide 3 y 6)",
    "warning"
)

# ----------------------------------------------------
# SECCIÓN 2
# ----------------------------------------------------
add_heading_1("2. Higiene de Git y Requisitos de Entrega (D6 Slides 4–11)")
add_p("La entrega de repositorios exige el cumplimiento riguroso de las siguientes reglas institucionales:")

add_heading_2("2.1. Commits Propios Obligatorios como Evidencia de Autoría")
add_p("El historial de Git es la evidencia formal de quién construyó el sistema. Se exige que todos los integrantes del grupo tengan commits propios en los repositorios. Un grupo donde todos los commits pertenecen a una sola persona tiene un problema de admisibilidad antes de empezar a defender.")
add_bullet("Los mensajes deben decir qué cambió y por qué (ej: 'Valida el client_id del token en el guard del BFF'). Prohibidos mensajes inútiles como 'cambios', 'asdf' o 'arreglos'.", "Mensajes con Sentido: ")
add_bullet("Entre 100 y 200 commits en total sumando frontend, gateway y backend.", "Meta de Commits: ")

add_heading_2("2.2. Estrategia de Ramas para Grupo Chico")
add_bullet("Siempre funcional. Es la rama que clona el docente y de donde se extrae el hash declarado en el documento de entrega.", "Rama main: ")
add_bullet("Rama de integración donde se consolidan las funcionalidades.", "Rama dev: ")
add_bullet("Ramas de 2 o 3 días para una tarea puntual (ej: feat/guard-jwt). Se mezclan a dev mediante Pull Request.", "Ramas cortas de feature: ")
add_bullet("Instancia obligatoria donde el compañero lee el código del otro antes de mezclarlo. Garantiza que nadie desconozca el código del proyecto en la defensa individual.", "Pull Request (PR): ")

add_heading_2("2.3. Distinción entre lo Molesto (Generado) y lo Grave (Secretos)")
add_bullet("node_modules/, dist/, .angular/, coverage/, *.log, .DS_Store. Ensucia el historial pero se soluciona agregándolo al .gitignore, corriendo 'git rm -r --cached' y haciendo commit. Diez minutos.", "Molesto (Generado): ")
add_bullet(".env, *.pem, *.jks, credentials.json, clientSecret o contraseñas. Si se sube a Git, queda comprometido PARA SIEMPRE en el historial, clones y caché de GitHub. Borrar el archivo NO alcanza: la única solución real es ROTAR la credencial en AWS donde se emitió.", "Grave (Secretos): ")
add_bullet("Una SPA pública Angular jamás debe tener client_secret (crearla con secret es el error clásico). userPoolId y clientId NO son secretos: van en el frontend y son visibles en cualquier petición de red.", "SPA sin secreto: ")

add_heading_2("2.4. Checklist de Entrega de Última Hora (Antes de las 23:59)")
add_bullet("git status limpio en los 3 repositorios (frontend, gateway, backend).", "1. ")
add_bullet("Archivos .gitignore completos (Node y Angular) ignorando .env y compilados.", "2. ")
add_bullet("Rama dev mezclada hacia main en todos los repositorios.", "3. ")
add_bullet("Docente (cr.calderons / Umbingelelo) agregado y activo como colaborador en los repositorios privados.", "4. ")
add_bullet("Hash del último commit de main de cada repositorio declarado en el PDF de entrega en AVA.", "5. ")

# ----------------------------------------------------
# SECCIÓN 3
# ----------------------------------------------------
add_heading_1("3. Arquitectura de 4 Capas y Flujo Secuencial")
add_p("El sistema VidalStore distribuye sus responsabilidades de forma desacoplada en cuatro capas:")

table_capas = doc.add_table(rows=5, cols=4)
table_capas.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Capa", "Puerto", "Tecnología", "Responsabilidad Principal"]
for i, h in enumerate(headers):
    cell = table_capas.cell(0, i)
    set_cell_background(cell, "1B365D")
    set_cell_margins(cell, 80, 80, 100, 100)
    p = cell.paragraphs[0]
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(255, 255, 255)

data_capas = [
    ("1. Frontend", "4200", "Angular + Amplify", "Navegación SPA, token en sessionStorage, lista blanca hacia :8080."),
    ("2. API Gateway", "8080", "NestJS", "AUTENTICA: Valida JWT contra JWKS, emisor, vigencia y client_id. CORS solo para :4200."),
    ("3. BFF", "3001", "NestJS", "AUTORIZA: Valida rol (cognito:groups). Orquesta agregación concurrente con Promise.all."),
    ("4. Microservicios", "3002..3005", "Node.js", "Persistencia (Catálogo, Compras, Biblioteca, Auditoría). data/seed.ts con API externa.")
]

for row_idx, row_data in enumerate(data_capas, start=1):
    for col_idx, text in enumerate(row_data):
        cell = table_capas.cell(row_idx, col_idx)
        set_cell_background(cell, "FFFFFF" if row_idx % 2 == 1 else "F9FBFD")
        set_cell_margins(cell, 60, 60, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(text)
        r.font.size = Pt(9)
        r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(8)

add_callout(
    "DELIMITACIÓN CLOUD VS LOCAL (D6 Slide 21)",
    "• EN LA NUBE (AWS): Únicamente el User Pool de Cognito (usuarios, grupos, scopes, App Clients y endpoint público JWKS).\n"
    "• EN LA MÁQUINA LOCAL: Todo el resto del sistema (Frontend en 4200, Gateway en 8080, BFF en 3001 y Microservicios).\n"
    "• Señal de Alarma: Creer que el Gateway es un servicio administrado de AWS (API Gateway de AWS).",
    "info"
)

add_heading_2("Flujo Paso a Paso de una Petición Autenticada (D6 Slide 23)")
add_p("Secuencia exacta de arriba a abajo por donde pasa una petición en VidalStore:")
add_bullet("Amplify obtiene el token del User Pool de Cognito usando Authorization Code con PKCE.", "1. ")
add_bullet("El Interceptor HTTP de Angular adjunta 'Authorization: Bearer <token>' a la llamada hacia el Gateway.", "2. ")
add_bullet("El API Gateway (NestJS :8080) verifica la firma contra el JWKS, vigencia, emisor y client_id (401 si falla).", "3. ")
add_bullet("El Gateway reenvía la petición con el encabezado Authorization intacto hacia el BFF (:3001).", "4. ")
add_bullet("El JwtGuard del BFF vuelve a validar el token (Defensa en Profundidad) y deja el payload en req.user.", "5. ")
add_bullet("El RolesGuard del BFF compara cognito:groups con el rol requerido por la ruta (@Roles) (403 si no alcanza).", "6. ")
add_bullet("El BFF realiza llamadas concurrentes internas con Promise.all hacia los microservicios.", "7. ")
add_bullet("El Microservicio de persistencia consulta o filtra si el recurso pertenece al claim sub del token.", "8. ")

# ----------------------------------------------------
# SECCIÓN 4
# ----------------------------------------------------
add_heading_1("4. El Reloj de los 15 Minutos y las 5 Ventanas")
add_p("La defensa individual dura exactamente 15 minutos cronometrados por grupo, con el orden sorteado previamente:")

table_reloj = doc.add_table(rows=6, cols=3)
table_reloj.alignment = WD_TABLE_ALIGNMENT.CENTER
r_headers = ["Minutos", "Etapa Oficial", "Dinámica en la Sala"]
for i, h in enumerate(r_headers):
    cell = table_reloj.cell(0, i)
    set_cell_background(cell, "1B365D")
    set_cell_margins(cell, 80, 80, 100, 100)
    p = cell.paragraphs[0]
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(255, 255, 255)

data_reloj = [
    ("0 a 1", "Procesos y Puertos", "Todos los integrantes declaran los procesos corriendo y sus puertos."),
    ("1 a 7", "Flujo A y Flujo B", "Un integrante conduce el Flujo A (Identidad); otro conduce el Flujo B (Lo Propio). Nadie conduce 2 seguidos."),
    ("7 a 12", "Flujos C, D y E", "Conducción de Flujos C (Rol insuficiente) y D (Por detrás / CORS), más 30 seg del Flujo E (abrir seed)."),
    ("12 a 14", "Modificación Señalada", "Una por integrante sobre un archivo que no construyó él (ubicar línea, explicar cambio y efecto)."),
    ("14 a 15", "Pregunta Botón COMPRAR", "Evaluación de fundamentación técnica de UX vs Idempotencia en backend.")
]

for row_idx, row_data in enumerate(data_reloj, start=1):
    for col_idx, text in enumerate(row_data):
        cell = table_reloj.cell(row_idx, col_idx)
        set_cell_background(cell, "FFFFFF" if row_idx % 2 == 1 else "F9FBFD")
        set_cell_margins(cell, 60, 60, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(text)
        r.font.size = Pt(9)
        r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(8)

add_heading_2("Las 5 Ventanas Obligatorias Abiertas al Entrar (D6 Slide 19)")
add_p("Llegar con estas 5 ventanas preparadas evita perder valiosos minutos del turno:")
add_bullet("Procesos activos mostrando sus puertos (Angular 4200, Gateway 8080, BFF 3001, Microservicios 3002..3005).", "1. Terminal: ")
add_bullet("Aplicación con sesión iniciada, pestaña Red limpia lista para inspeccionar y Application con sessionStorage.", "2. Navegador: ")
add_bullet("Dos tokens listos (jugador y administrador) para probar 403 vs 200, y llamada directa sin token para 401.", "3. Cliente REST o curl: ")
add_bullet("Pestañas del interceptor HTTP de Angular y de los guards de NestJS ya abiertas.", "4. Editor (VS Code): ")
add_bullet("User Pool con grupos, usuarios y los dos App Clients (lo único en la nube).", "5. Consola AWS Cognito: ")

# ----------------------------------------------------
# SECCIÓN 5
# ----------------------------------------------------
add_heading_1("5. El Framework de Respuesta en 4 Pasos de D6")
add_p("Para responder cualquier pregunta de arquitectura en 1 minuto, estructurar la respuesta en estos cuatro pasos obligatorios (D6 Slide 16):")

add_bullet("Nombrar el componente, clase o función exacta en el código y abrir el archivo en el editor.", "Paso 1: Qué hice → ")
add_bullet("Explicar la necesidad concreta de seguridad, rendimiento, arquitectura o desacoplamiento.", "Paso 2: Qué problema resuelve → ")
add_bullet("Nombrar explícitamente la alternativa técnica rechazada y por qué no servía. Demuestra análisis y descarta copia ciega. Es el paso que más califica.", "Paso 3: Qué descarté → ")
add_bullet("Validarlo empíricamente en vivo en la pantalla (pestaña Red, dos tokens en curl, terminal).", "Paso 4: Cómo lo compruebo → ")

# ----------------------------------------------------
# SECCIÓN 6
# ----------------------------------------------------
add_heading_1("6. Guion Oficial de la Defensa · Parada por Parada")

add_dialogue(
    "A1 · Auto-registro y la Trampa de Cognito",
    "Registra un usuario nuevo en la Hosted UI en vivo. Dime: ¿en qué grupo quedó esta cuenta recién creada y quién se lo asignó?",
    [
        ("1", "Qué hice", "Quedó asignada automáticamente en el grupo 'jugadores' mediante el fallback seguro que implementamos en el guard de NestJS (group.guard.ts)."),
        ("2", "Qué problema resuelve", "Resuelve la trampa de Cognito: al auto-registrarse por Hosted UI, Cognito deja cognito:groups vacío. Sin este control, el usuario no tendría rol y recibiría 403 Forbidden en todas partes."),
        ("3", "Qué descarté", "Descarté asignarlo a mano en la consola de AWS (un sistema real de autoservicio no depende de administración manual) y descarté otorgarle permisos elevados por omisión (principio de menor privilegio)."),
        ("4", "Cómo lo compruebo", "El usuario nuevo entra de inmediato a /catalogo y /biblioteca con 200 OK, pero al intentar entrar a /admin/licencias es bloqueado con 403 Forbidden.")
    ],
    "«Yo se lo asigno después a mano en la consola de AWS» (demuestra que el sistema no está automatizado)."
)

add_dialogue(
    "A2 · Claims del Token (Identidad vs Autorización)",
    "Abre el token JWT decodificado en pantalla. ¿Qué claim dice quién eres y cuál dice qué puedes hacer?",
    [
        ("1", "Qué hice", "Utilizo el claim 'sub' para la identidad del sujeto, y 'cognito:groups' junto a 'scope' para la autorización."),
        ("2", "Qué problema resuelve", "Separa técnicamente la identidad inmutable del permiso concedido: 'sub' es el UUID inmutable que dice quién es la persona; 'cognito:groups' define el rol humano (jugadores, editores, administradores); y 'scope' define qué operaciones tiene permitidas la SPA ante la API."),
        ("3", "Qué descarté", "Descarté usar el client_id o los scopes para autorizar acciones humanas de usuario. El client_id solo identifica al software frontend, no a la persona."),
        ("4", "Cómo lo compruebo", "En el payload del token decodificado vemos sub con el UUID del usuario, cognito:groups con ['jugadores'] y scope con los 3 scopes asignados al App Client.")
    ],
    "Confundir scope con rol de usuario, o creer que el rol está contenido en el claim sub."
)

add_dialogue(
    "B1 · Una Sola Dirección en Red",
    "Abre la vista /biblioteca en Angular y la pestaña Red. ¿A qué direcciones le habló el navegador para cargar esta pantalla?",
    [
        ("1", "Qué hice", "Le habló a UNA SOLA dirección: http://localhost:8080 (nuestro API Gateway)."),
        ("2", "Qué problema resuelve", "Desacopla al frontend de la topología interna. Angular no conoce puertos de microservicios ni su existencia, y emite una sola llamada HTTP (GET /v1/biblioteca) reduciendo drásticamente la latencia en redes móviles."),
        ("3", "Qué descarté", "Descarté que Angular invoque directamente al BFF o a los microservicios. En token.interceptor.ts la lista blanca tiene una sola entrada (http://localhost:8080)."),
        ("4", "Cómo lo compruebo", "La pestaña Red muestra una única llamada a http://localhost:8080/v1/biblioteca. Es el BFF en el backend quien realiza las múltiples llamadas internas hacia biblioteca y catálogo.")
    ],
    "Aparecen dos o tres direcciones distintas en la pestaña Red (ej: el frontend habla directo a microservicios)."
)

add_dialogue(
    "B3 · Resolución por 'sub' (La Parada Más Discriminante)",
    "Muestra la consulta de biblioteca. ¿De dónde sale el usuario cuyas licencias devuelves? ¿Por qué no lo recibes por parámetro?",
    [
        ("1", "Qué hice", "Sale estrictamente del claim 'sub' del JWT verificado criptográficamente en req.user.sub en bff-biblioteca.controller.ts."),
        ("2", "Qué problema resuelve", "Previene la vulnerabilidad crítica BOLA / IDOR (Broken Object Level Authorization). Si la ruta aceptara usuarioId por URL o body, cualquier usuario con token válido podría cambiar el número y espiar o robar juegos ajenos."),
        ("3", "Qué descarté", "Descarté recibir usuarioId en URL (/v1/biblioteca/:usuarioId), query o body. Al inicio lo teníamos por URL para probar en Postman, pero al probar con dos cuentas vimos que se podían cruzar datos y eliminamos el parámetro para siempre."),
        ("4", "Cómo lo compruebo", "En la terminal ejecuto GET /v1/biblioteca con el token del Usuario A y devuelve 3 juegos; ejecuto la misma URL con el token del Usuario B y devuelve 2 juegos. No cambié nada en la URL, solo el token.")
    ],
    "Recibir el usuario por query, body o parámetro de ruta («pero igual está protegido porque pide token»)."
)

add_dialogue(
    "C · Rol Insuficiente y Control en Servidor",
    "Con el token de un jugador, demuéstrame que el control de acceso reside en el servidor y no en la interfaz visual.",
    [
        ("1", "Qué hice", "Protegí la ruta de revocar licencias con @RequireGroups('administradores') y BffGroupsGuard en bff-licencias.controller.ts."),
        ("2", "Qué problema resuelve", "Garantiza que la seguridad no dependa del cliente. Ocultar o deshabilitar un botón en Angular es solo cosmético; cualquier usuario puede manipular el DOM en F12 o enviar un DELETE con curl."),
        ("3", "Qué descarté", "Descarté responder 401 Unauthorized. Como el token del jugador es legítimo, responder 401 causaría un bucle infinito de login en el navegador. La respuesta correcta es 403 Forbidden ('sé quién eres, pero tu rol no te alcanza')."),
        ("4", "Cómo lo compruebo", "Ejecuto en terminal: curl -i -X DELETE -H 'Authorization: Bearer $T_JUGADOR' http://localhost:8080/v1/licencias/lic-001. El backend responde inmediatamente HTTP/1.1 403 Forbidden.")
    ],
    "Responder 401 en vez de 403, o responder 200 y decir «es que en la pantalla el botón no aparece»."
)

add_dialogue(
    "D1 · Por Detrás / Zero Trust",
    "Llama al BFF y al microservicio directo en su puerto interno, sin pasar por el Gateway. ¿Qué responden y por qué?",
    [
        ("1", "Qué hice", "Configuré BffAuthGuard sobre el controlador del BFF, aplicando el principio de Defensa en Profundidad y Zero Trust."),
        ("2", "Qué problema resuelve", "Evita asumir que la red interna es segura. Si un contenedor vecino está comprometido o alguien se salta el gateway llamando directo a :3001, el BFF no confía ciegamente y exige su propio token."),
        ("3", "Qué descarté", "Descarté la arquitectura de 'castillo y muralla' donde solo el borde valida y los servicios internos quedan desprotegidos respondiendo 200 OK a cualquiera."),
        ("4", "Cómo lo compruebo", "Hago curl -i http://localhost:3001/v1/biblioteca sin cabecera Authorization: responde HTTP/1.1 401 Unauthorized. El BFF se protege solo.")
    ],
    "Responder 200 OK (demuestra que las capas internas están totalmente abiertas sin autenticación)."
)

add_dialogue(
    "D2 · Token Alterado y Emisor del 401",
    "Cambia un carácter al medio del token JWT y envíalo. ¿Qué responde el sistema y quién emite ese error?",
    [
        ("1", "Qué hice", "Implementé la verificación de firma criptográfica con jwt.verify en auth.service.ts del API Gateway."),
        ("2", "Qué problema resuelve", "Detecta y bloquea cualquier intento de falsificación o manipulación de datos en el payload del token."),
        ("3", "Qué descarté", "Descarté claves simétricas compartidas (HMAC). El Gateway descarga las claves públicas RSA asimétricas del endpoint JWKS de Cognito (/.well-known/jwks.json)."),
        ("4", "Cómo lo compruebo", "Envío el token alterado al Gateway con curl: responde HTTP/1.1 401 Unauthorized. Lo emite el Gateway en el perímetro exterior al fallar la firma RSA contra el JWKS; la petición ni tocó al BFF.")
    ],
    "No saber qué capa lo rechazó ni contra qué se verificó la firma criptográfica."
)

add_dialogue(
    "D3 · Origen de CORS",
    "¿Qué origen acepta tu configuración de CORS y qué pasa si te llaman desde otro dominio?",
    [
        ("1", "Qué hice", "Habilité app.enableCors() exclusivamente en el API Gateway, restringido a origin: 'http://localhost:4200'."),
        ("2", "Qué problema resuelve", "Cumple la política de seguridad del navegador para evitar peticiones maliciosas cruzadas desde sitios de terceros."),
        ("3", "Qué descarté", "Descarté origin: '*' ('para que no diera problemas') y descarté configurar CORS en el BFF o microservicios (CORS es exclusivo de navegadores; entre servidores Node no aplica)."),
        ("4", "Cómo lo compruebo", "Si un navegador llama desde otro origen, el navegador bloquea la respuesta. Si se llama con curl, la petición pasa porque curl no aplica políticas de navegador (el control real es el token).")
    ],
    "Configurar origin: '*' o creer que el CORS es el mecanismo de control de acceso a la API."
)

add_dialogue(
    "E · Origen y Trazabilidad del Catálogo",
    "¿De dónde salieron los juegos del catálogo? ¿Qué pasa si borro catalogo.json y clono en una máquina limpia?",
    [
        ("1", "Qué hice", "Creé el script data/seed.ts que consume la API externa real de FreeToGame y guarda los registros normalizados en data/catalogo.json."),
        ("2", "Qué problema resuelve", "Garantiza la trazabilidad institucional: prohibido tener datos inventados a mano en arreglos de memoria o datos ficticios no reproducibles."),
        ("3", "Qué descarté", "Descarté escribir el JSON a mano o depender de una base de datos local que no se pueda versionar en el repositorio."),
        ("4", "Cómo lo compruebo", "Si borro data/catalogo.json y ejecuto npm run seed, el script consume la API externa de FreeToGame, filtra campos y regenera el archivo catalogo.json de forma 100% idéntica.")
    ],
    "«Los escribí a mano», o tener el archivo catalogo.json pero no tener el script seed que lo generó."
)

# ----------------------------------------------------
# SECCIÓN 7: REGLAS DE NEGOCIO, LICENCIAS E IDENTIFICADORES
# ----------------------------------------------------
add_heading_1("7. Reglas de Negocio, Gestión de Licencias e Identificadores (UUID vs Sub vs Integer)")
add_p("El docente Cristian Calderón evalúa con especial énfasis el dominio del modelo de datos y las reglas de negocio de software digital que sustentan la arquitectura:")

add_dialogue(
    "N1 · Modelado y Gestión de Licencias (Single Source of Truth)",
    "Muestra el modelo de licencias. ¿Cómo se gestionan, quién es el dueño de esos datos, cómo nacen y cómo se relacionan con los juegos y usuarios?",
    [
        ("1", "Qué hice", "Modelé la entidad Licencia (vidalstore-backend/src/models/licencia.model.ts) con id (UUID v4), juegoId (string numérico), usuarioSub (claim sub de Cognito), fechaAdquisicion (ISO 8601), plataforma, tienda, region, codigoCanje (VS-XXXXXXXXXXXXXXXX), estadoPago: 'aprobado', precioPagado y referenciaPago. El microservicio de Biblioteca (biblioteca.service.ts) es el único dueño (Single Source of Truth) del agregado de licencias, respaldado en MemoryStorageService y persistido sincrónicamente en data/licencias.json."),
        ("2", "Qué problema resuelve", "Modela la relación N:M entre usuarios y juegos desacoplando la transacción comercial de la titularidad de los derechos digitales. Cuando un usuario compra en /v1/compras, el microservicio de Compras valida/simula la transacción financiera y le delega por HTTP interno a Biblioteca la creación de la licencia."),
        ("3", "Qué descarté", "Descarté almacenar las licencias embebidas en un arreglo dentro del usuario (violaría el desacoplamiento de microservicios, ya que los usuarios viven en AWS Cognito y no en nuestra base de datos local). También descarté que el microservicio de Catálogo guardara qué usuarios tienen qué juegos (mezclaría catálogo público de lectura con tenencia privada confidencial)."),
        ("4", "Cómo lo compruebo", "En biblioteca.service.ts se observa el método crearLicencia(). Al consultar GET /v1/biblioteca, el BFF llama a Biblioteca, obtiene las licencias de ese usuarioSub, las enriquece con el catálogo y devuelve el inventario digital propio.")
    ],
    "Decir que las licencias se guardan dentro de Cognito o que el Catálogo administra quién compró los juegos."
)

add_dialogue(
    "N2 · Identificador de Usuario (Por qué 'sub' UUID y NO email/username)",
    "¿Por qué en las licencias guardas 'usuarioSub' en lugar del correo electrónico (email) o el nombre de usuario (username)? ¿Qué ganaron con esa decisión?",
    [
        ("1", "Qué hice", "Utilicé como clave foránea única de usuario el claim sub (Subject) emitido por AWS Cognito, que es un UUID v4 inmutable de 36 caracteres (ej: c4f82a91-4d3e-4fa2-9856-123456789abc), extraído de req.user.sub tras verificar la firma RSA del JWT."),
        ("2", "Qué problema resuelve", "Resuelve 3 problemas críticos: 1) Inmutabilidad Absoluta: Un usuario puede cambiar su email o username en Cognito en cualquier momento. Si usáramos el email como clave foránea, cambiar de correo rompería la integridad referencial y el jugador perdería sus juegos comprados. El sub es inmutable de por vida. 2) Privacidad por Diseño (Zero PII Leakage / GDPR): El sub es un UUID opaco sin datos personales. Los microservicios y logs intercambian un UUID sin filtrar correos ni nombres. 3) Desacoplamiento del Identity Provider: La base de datos interna solo conoce UUIDs RFC 4122; si cambiamos Cognito por Keycloak, el modelo no cambia."),
        ("3", "Qué descarté", "Descarté usar el email o el username como clave primaria/foránea, y descarté inventar un ID numérico de usuario local (usuarioId: 1, 2, 3) que obligaría a mantener una tabla de sincronización mapeando Cognito con la base de datos interna."),
        ("4", "Cómo lo compruebo", "Decodifico el JWT en jwt.io: el claim sub contiene el UUID inmutable que coincide exactamente con los registros de data/licencias.json.")
    ],
    "Creer que usar email es mejor 'porque es más legible', ignorando la mutabilidad del correo y la fuga de datos personales (PII)."
)

add_dialogue(
    "N3 · Identificador de Licencia (Por qué UUID v4 y NO un autoincremental)",
    "¿Por qué el ID de la licencia es un UUID (randomUUID()) y no un número secuencial simple como 1, 2, 3...?",
    [
        ("1", "Qué hice", "En biblioteca.service.ts y memory-storage.service.ts, cada nueva licencia recibe id: randomUUID(), generado mediante el módulo nativo criptográfico node:crypto."),
        ("2", "Qué problema resuelve", "1) Sistemas Distribuidos sin Cuello de Botella: En microservicios con múltiples réplicas, los IDs autoincrementales exigen una base de datos centralizada con bloqueos transaccionales (punto único de falla). El UUID v4 se genera de forma descentralizada y autónoma en cualquier nodo con probabilidad de colisión matemáticamente despreciable (2^122). 2) Confidencialidad y Anti-Scraping: Si los IDs fueran 101, 102, un competidor sabría cuántas compras procesa VidalStore restando compras consecutivas, y un atacante intentaría adivinar licencias adyacentes (/licencias/103)."),
        ("3", "Qué descarté", "Descarté secuencias numéricas (id: ++contador) y bibliotecas externas pesadas; usamos el generador criptográfico nativo de Node.js randomUUID()."),
        ("4", "Cómo lo compruebo", "Si genero dos compras consecutivas vía /v1/compras, los IDs resultantes en licencias.json son hashes UUID v4 independientes de 36 caracteres.")
    ],
    "«Es que NestJS me lo dio así», sin entender el impacto en sistemas distribuidos ni la seguridad contra enumeración de URLs."
)

add_dialogue(
    "N4 · Convivencia de Identificadores (Catálogo FreeToGame '452' vs Licencias UUID)",
    "Veo que en el catálogo los IDs son números como '452', pero las licencias son UUIDs. ¿Por qué esa diferencia y cómo conviven ambos?",
    [
        ("1", "Qué hice", "En el catálogo tipamos id: string en TypeScript, pero sus valores son numéricos seriales provenientes del script data/seed.ts que consume la API externa de FreeToGame. En la licencia almacenamos juegoId: string como clave foránea que referencia ese ID de catálogo."),
        ("2", "Qué problema resuelve", "Respeta la separación entre datos de proveedores externos y transacciones internas: El Catálogo es un reflejo de una API externa (FreeToGame); mantener su ID original preserva la trazabilidad con la fuente externa original si se requiere resincronizar. La Licencia es un bien transaccional propio generado por VidalStore, por lo que requiere identificadores únicos globales no secuenciales (UUID v4). Tipar ambos como string desacopla esquemas y previene problemas de coerción de tipos."),
        ("3", "Qué descarté", "Descarté sobreescribir los IDs de FreeToGame con nuevos UUIDs en el seed, porque habríamos destruido el identificador oficial del juego en la API externa."),
        ("4", "Cómo lo compruebo", "En catalogo.json vemos { 'id': '452', 'titulo': 'Call of Duty: Warzone' }, y en licencias.json vemos { 'id': 'uuid-v4...', 'juegoId': '452', 'usuarioSub': 'uuid-sub...' }.")
    ],
    "No saber de dónde provienen los IDs de los juegos ni por qué se almacenan como cadenas en TypeScript."
)

add_dialogue(
    "N5 · Unicidad e Idempotencia (HTTP 409 Conflict en Compras)",
    "¿Qué regla de negocio impide que un usuario compre dos veces el mismo juego y cómo está implementada en el código?",
    [
        ("1", "Qué hice", "En biblioteca.service.ts, el método crearLicencia() ejecuta primero buscarLicenciaPorUsuarioYJuego(usuarioSub, licenciaDatos.juegoId). Si la tupla (usuarioSub, juegoId) ya existe en memoria/archivo, arroja inmediatamente una excepción ConflictException (HTTP 409 Conflict): 'El usuario ya posee una licencia activa para el juego con ID ...'."),
        ("2", "Qué problema resuelve", "Aplica la regla fundamental de comercialización de software digital: a diferencia de un e-commerce físico donde compras 3 unidades, en licencias de software digital la posesión es unívoca. Previene cobros duplicados por doble clic del usuario, reintentos de red automáticos o llamadas directas maliciosas con curl."),
        ("3", "Qué descarté", "Descarté delegar esta comprobación únicamente a la interfaz gráfica en Angular (un atacante puede habilitar el botón en F12 o disparar la API directo). Y descarté responder 200 OK cobrando de nuevo o sobreescribiendo la fecha de compra original."),
        ("4", "Cómo lo compruebo", "Envío dos peticiones consecutivas con curl -X POST http://localhost:8080/v1/compras -d '{\"juegoId\":\"452\"}': la primera responde 201 Created y la segunda responde 409 Conflict.")
    ],
    "Decir que con ocultar el botón en Angular basta, delegando la regla de negocio y la seguridad al cliente."
)

add_dialogue(
    "N6 · Código de Canje (CD-Key con Criptografía Segura)",
    "¿Para qué sirve el campo 'codigoCanje' en la licencia y con qué criterio se genera?",
    [
        ("1", "Qué hice", "En biblioteca.service.ts línea 59, al crear la licencia se genera: codigoCanje: `VS-${randomUUID().replaceAll('-', '').slice(0, 16).toUpperCase()}`."),
        ("2", "Qué problema resuelve", "Separa el derecho legal de tenencia de la entrega física/digital de la credencial: la Licencia representa la titularidad en VidalStore; el Código de Canje (CD-Key) es la credencial alfanumérica única de 16 caracteres hexadecimales que el jugador ingresa en Steam, Epic Games o el launcher para descargar el ejecutable."),
        ("3", "Qué descarté", "Descarté generar códigos con Math.random() (es un generador pseudo-aleatorio predecible y vulnerable a ataques de fuerza bruta). El uso de randomUUID() garantiza entropía criptográfica derivada del CSPRNG del sistema operativo."),
        ("4", "Cómo lo compruebo", "Al inspeccionar una licencia devuelta en /v1/biblioteca, el objeto incluye un código de canje formateado con prefijo institucional: VS-E4A83C90D1F5B2E7.")
    ],
    "No saber para qué existe el código de canje o creer que es un simple adorno estético sin valor comercial."
)

# ----------------------------------------------------
# SECCIÓN 8
# ----------------------------------------------------
add_heading_1("8. La Modificación Señalada (Minutos 12 a 14)")
add_p("En este bloque de 2 minutos, el docente pide a cada integrante una modificación puntual sobre un frente que NO programó él. No se programa en vivo: se abre el archivo, se ubica la línea con el cursor y se explica qué se escribiría y qué pasaría:")

add_heading_2("Caso 1: ¿Dónde y cómo agregarías una ruta que solo consulten administradores?")
add_p("«Voy a bff-licencias.controller.ts en el BFF. Agrego el método del endpoint con el decorador @RequireGroups('administradores') y @UseGuards(BffAuthGuard, BffGroupsGuard). Luego voy a gateway.controller.ts en el Gateway y creo la ruta proxy correspondiente con @RequireGroups('administradores') reenviando el encabezado Authorization.»")

add_heading_2("Caso 2: ¿Qué se rompe si borro la línea que inyecta 'Authorization: Bearer' en Angular?")
add_p("«En src/app/auth/token.interceptor.ts comento setHeaders['Authorization'] = 'Bearer ...'. La aplicación Angular sigue compilando sin errores, pero al intentar cargar catálogo o biblioteca, las peticiones HTTP saldrán sin token. El API Gateway recibirá la llamada, el AuthGuard detectará que no hay encabezado Authorization y cortará inmediatamente con 401 Unauthorized. La pantalla quedará en blanco.»")

add_heading_2("Caso 3: ¿Qué error da si configuro en el Gateway el client_id del otro App Client?")
add_p("«En el .env del Gateway cambio COGNITO_CLIENT_ID por el del App Client 2. Al hacer peticiones desde Angular, el Gateway validará la firma contra el JWKS (pasará), pero en el paso 5 de auth.service.ts comparará payload.client_id con la variable: no coincidirán y responderá 401 Unauthorized ('Token de cliente no autorizado'). Ningún usuario podrá entrar.»")

add_heading_2("Caso 4: ¿Qué pasa si quitas un microservicio del Promise.all en el BFF?")
add_p("«En bff-licencias.service.ts, si quito la consulta a catálogo del Promise.all, la biblioteca devuelve licencias pero sin título, portada ni metadatos para enriquecerlas. El mapper fallará al buscar en el Map o devolverá datos incompletos. Se rompe el principio de agregación del BFF.»")

# ----------------------------------------------------
# SECCIÓN 9
# ----------------------------------------------------
add_heading_1("9. La Pregunta del Botón COMPRAR (Minutos 14 a 15)")
add_p("Pregunta del Docente: «Si el usuario ya posee la licencia de un juego, ¿qué debe hacer el botón COMPRAR en la interfaz? ¿Ocultarse, deshabilitarse, o permitir el clic y que el servidor responda con error?»")

add_p("Respuesta Técnica Modelo:", bold_prefix="Argumentación de Ingeniería: ")
add_p("«La decisión técnica balancea experiencia de usuario en el cliente con seguridad estricta en el servidor:")
add_bullet("Deshabilitar el botón o cambiarlo a 'Ya adquirido' / 'Jugar'. Mejora la UX, previene frustraciones y ahorra tráfico de red innecesario.", "1. En la Interfaz (UX): ")
add_bullet("La seguridad y las reglas de negocio NUNCA se delegan al cliente. Cualquier usuario puede manipular el DOM en F12 o enviar un curl POST /v1/compras directo. Por eso el microservicio de biblioteca es estrictamente IDEMPOTENTE: en biblioteca.service.ts comprueba si existe la tupla (usuarioSub, juegoId) y responde ConflictException (HTTP 409 Conflict), evitando duplicar licencias o cobros.", "2. En el Backend (Mandatorio): ")
add_bullet("En la UI lo deshabilito por experiencia de usuario, pero el backend siempre valida la idempotencia y responde 409 Conflict si la llamada llega.", "Conclusión de Oro: ")

# ----------------------------------------------------
# SECCIÓN 10
# ----------------------------------------------------
add_heading_1("10. Preguntas Transversales y Resumen de Pulso.pdf (§12.2)")

add_heading_2("Pregunta Transversal 1: Si entra un quinto microservicio, ¿qué se toca?")
add_p("«Solo se tocan dos capas del backend: en el BFF se agrega la llamada interna y se mapea en el Promise.all; y en el Gateway se crea la ruta proxy si se requiere exponer un endpoint público /v1/... En Angular NO se toca ninguna URL: el frontend solo conoce http://localhost:8080.»")

add_heading_2("Pregunta Transversal 2: ¿Qué pasa si un microservicio interno se cae?")
add_p("«El BFF captura el error de conexión y responde 503 Service Unavailable indicando qué servicio falló. Cuando el microservicio se restablece, el sistema vuelve a responder 200 OK inmediatamente sin necesidad de reiniciar el Gateway ni el BFF.»")

add_heading_2("Pregunta Pulso 6: ¿Qué gana el frontend con el BFF? (Números medidos)")
add_p("«Gana una sola llamada de red en lugar de múltiples peticiones; concurrencia en servidor mediante Promise.all (con 300 ms de latencia por servicio, en serie serían 600 ms y en paralelo son ~300 ms); cruce de datos en memoria O(N) con Map por ID; y cero fuga de datos internos confidenciales hacia el inspector F12.»")

# ----------------------------------------------------
# SECCIÓN 11
# ----------------------------------------------------
add_heading_1("11. Bitácora de Errores Reales del Proyecto (D6 \"Qué Descarté\")")
add_p("Tener presentes 5 errores reales que ocurrieron durante el desarrollo demuestra autoría indiscutible:")
add_bullet("Al crear el App Client en Cognito le pusimos client_secret para Angular. Amplify no podía autenticar porque las SPAs públicas no pueden almacenar secretos. Tuvimos que recrear el App Client sin secreto.", "1. Error de Secreto en SPA: ")
add_bullet("Estábamos probando un endpoint con curl y de repente dio 401. El token de Cognito había cumplido sus 60 minutos de vigencia (exp). Tuvimos que volver a iniciar sesión.", "2. Error de Token Expirado: ")
add_bullet("Al registrarnos con un usuario nuevo en la Hosted UI, no podíamos ver el catálogo (403). Cognito no asigna grupos por omisión; lo resolvimos con el fallback seguro a 'jugadores' en el guard.", "3. Error de la Trampa de Cognito: ")
add_bullet("Intentamos poner CORS en el BFF. Nos dimos cuenta de que CORS es exclusivo de navegadores web y que las llamadas internas entre Node.js son backend-to-backend, por lo que CORS solo debe vivir en el Gateway.", "4. Error de CORS en Backend: ")
add_bullet("En Angular interceptábamos todas las URLs sin filtro, enviando el token Bearer a Google Fonts y CDNs externos. Lo solucionamos con la whitelist estricta que solo inyecta el token si la URL comienza con environment.apiUrl (http://localhost:8080).", "5. Error de Whitelist en Interceptor: ")

# Save Document
output_path = "/Users/oscar/Downloads/DUOC/CloudNative/Evaluacion 1/Guia_Defensa_VidalStore_EP1_D6.docx"
doc.save(output_path)
print(f"Document saved successfully at: {output_path}")

