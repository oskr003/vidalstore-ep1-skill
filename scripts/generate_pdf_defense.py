import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.pdfgen import canvas

PDF_PATH = "/Users/oscar/Downloads/DUOC/CloudNative/Evaluacion 1/Guia_Defensa_VidalStore_EP1_D6.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "DSY1107 · Desarrollo Cloud Native I | Caso VidalStore EP1 · Preparación D6")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "DUOC UC · Escuela de Informática | Defensa de Arquitectura EP1")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    c_primary = colors.HexColor("#1B365D")   # Navy
    c_secondary = colors.HexColor("#2E6B9E") # Steel Blue
    c_dark = colors.HexColor("#222222")
    c_alert = colors.HexColor("#C0392B")
    c_success = colors.HexColor("#27AE60")
    
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        alignment=1, # Center
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        alignment=1,
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_dark,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=c_dark,
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=c_dark,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=2
    )

    q_label_style = ParagraphStyle(
        'QLabel',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1A5276")
    )

    q_text_style = ParagraphStyle(
        'QText',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=c_dark
    )

    w_label_style = ParagraphStyle(
        'WLabel',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_alert
    )

    w_text_style = ParagraphStyle(
        'WText',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark
    )

    a_label_style = ParagraphStyle(
        'ALabel',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=c_success
    )

    a_step_style = ParagraphStyle(
        'AStep',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark,
        spaceAfter=2
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=c_dark
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("GUÍA MAESTRA DE DEFENSA TÉCNICA · EP1", title_style))
    story.append(Paragraph("Caso VidalStore · DSY1107 Desarrollo Cloud Native I · DUOC UC (2026-02)<br/>Basado en la Clase Magistral D6, Pulso.pdf y Resoluciones del Profesor Cristian Calderón", subtitle_style))

    # Box Metadata
    meta_text = (
        "<b>Equipo:</b> Oscar Garrido, David, Iván | <b>Asignatura:</b> DSY1107 Desarrollo Cloud Native I<br/>"
        "<b>Fecha Entrega AVA:</b> Lunes 21 de Septiembre 23:59 hrs | <b>Defensas:</b> Martes 22 y Jueves 24<br/>"
        "<b>Duración Turno:</b> 15 minutos cronometrados | <b>Ponderación:</b> 40% Código Grupal / 60% Presentación Individual"
    )
    tbl_meta = Table([[Paragraph(meta_text, body_style)]], colWidths=[504])
    tbl_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(tbl_meta)
    story.append(Spacer(1, 10))

    # 1. Estructura y Ponderación
    story.append(Paragraph("1. Estructura y Ponderación Real de la EP1 (Clase D6 Slide 3)", h1_style))
    story.append(Paragraph("La Evaluación Parcial N°1 pondera un 40% de la nota final del ramo y se desglosa en dos instancias claramente diferenciadas:", body_style))
    story.append(Paragraph("• <b>El Código Grupal (40% de la EP1):</b> Se congela hoy a las 23:59 hrs en el commit de la rama main declarado en el documento de entrega en AVA, y se califica posteriormente.", bullet_style))
    story.append(Paragraph("• <b>La Presentación / Defensa Técnica (60% de la EP1):</b> Es estrictamente <b>INDIVIDUAL</b>. Cada alumno defiende por separado frente al computador. Vale más que todo el código junto: un grupo con el sistema funcionando al 100% puede reprobar si el estudiante no sabe defender por qué lo hizo así ni justificar las decisiones de arquitectura.", bullet_style))

    # 2. Higiene de Git
    story.append(Paragraph("2. Higiene de Git y Requisitos de Entrega (D6 Slides 4–11)", h1_style))
    story.append(Paragraph("• <b>Commits Propios Obligatorios:</b> El historial de Git es la evidencia formal de autoría. Se exige que todos los integrantes tengan commits propios. Un grupo donde todos los commits son de una sola persona tiene un problema de admisibilidad previo a defender.", bullet_style))
    story.append(Paragraph("• <b>Mensajes con Sentido:</b> Deben explicar qué cambió y por qué (ej: 'Valida el client_id del token en el guard del BFF'; prohibido 'cambios', 'asdf', 'arreglos').", bullet_style))
    story.append(Paragraph("• <b>Estrategia de Ramas para Grupo Chico:</b> Rama main siempre funcional (es la que clona el docente) ← rama dev ← ramas cortas de feature ('feat/guard-jwt', 2 a 3 días) con Pull Request obligatorio para que el compañero lea y conozca el código.", bullet_style))
    story.append(Paragraph("• <b>Lo Molesto (Generado) vs Lo Grave (Secretos):</b><br/>"
                           "  - <i>Molesto:</i> node_modules/, dist/, .angular/, *.log. Se soluciona con .gitignore, 'git rm -r --cached' y commit.<br/>"
                           "  - <i>Grave:</i> .env, *.pem, credentials.json, clientSecret. Si se sube a Git, queda comprometido para siempre en clones y caché; la única solución real es <b>ROTAR la credencial en AWS</b> donde se emitió.<br/>"
                           "  - <i>SPA sin secret:</i> Angular jamás debe tener client_secret (error clásico). userPoolId y clientId son públicos.", bullet_style))
    story.append(Paragraph("• <b>Checklist de Última Hora antes de las 23:59:</b> git status limpio, .gitignore completo, dev mezclado a main, docente (cr.calderons / Umbingelelo) invitado como colaborador en todos los repositorios y hash del último commit de main declarado en AVA.", bullet_style))

    # 3. Arquitectura de 4 Capas
    story.append(Paragraph("3. Arquitectura de 4 Capas y Flujo Secuencial (D6 Slide 23)", h1_style))
    
    capas_data = [
        [Paragraph("Capa", table_header_style), Paragraph("Puerto", table_header_style), Paragraph("Tecnología", table_header_style), Paragraph("Responsabilidad Principal", table_header_style)],
        [Paragraph("1. Frontend", table_cell_style), Paragraph("4200", table_cell_style), Paragraph("Angular + Amplify", table_cell_style), Paragraph("Navegación SPA, token en sessionStorage, lista blanca hacia :8080 exclusivamente.", table_cell_style)],
        [Paragraph("2. API Gateway", table_cell_style), Paragraph("8080", table_cell_style), Paragraph("NestJS", table_cell_style), Paragraph("AUTENTICA: Valida JWT contra JWKS, vigencia, iss, client_id. CORS solo para :4200.", table_cell_style)],
        [Paragraph("3. BFF", table_cell_style), Paragraph("3001", table_cell_style), Paragraph("NestJS", table_cell_style), Paragraph("AUTORIZA: Valida rol (cognito:groups). Orquesta agregación concurrente con Promise.all.", table_cell_style)],
        [Paragraph("4. Microservicios", table_cell_style), Paragraph("3002..3005", table_cell_style), Paragraph("Node.js", table_cell_style), Paragraph("Persistencia (Catálogo, Compras, Biblioteca, Auditoría). data/seed.ts con API externa.", table_cell_style)]
    ]
    tbl_capas = Table(capas_data, colWidths=[80, 45, 105, 274])
    tbl_capas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FBFD")]),
    ]))
    story.append(tbl_capas)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Delimitación Cloud vs Local (D6 Slide 21):</b> En la nube de AWS reside <b>exclusivamente el User Pool de Cognito</b> (usuarios, grupos, scopes, App Clients y endpoint público JWKS). Todo el resto del sistema (Frontend, Gateway, BFF y Microservicios) corre 100% en la máquina local.", body_style))
    story.append(Paragraph("<b>Flujo de Arriba a Abajo:</b> 1. Amplify obtiene token con PKCE → 2. Interceptor adjunta Authorization: Bearer → 3. Gateway verifica firma contra JWKS (401 si falla) → 4. Gateway reenvía token intacto a BFF → 5. JwtGuard del BFF revalida token (req.user) → 6. RolesGuard del BFF verifica cognito:groups (403 si no alcanza) → 7. BFF llama con Promise.all a microservicios → 8. Microservicio filtra por sub del token.", body_style))

    # 4. El Reloj de 15 Minutos
    story.append(Paragraph("4. El Reloj de los 15 Minutos y las 5 Ventanas Abiertas (D6 Slide 14 y 19)", h1_style))
    
    reloj_data = [
        [Paragraph("Minutos", table_header_style), Paragraph("Etapa Oficial", table_header_style), Paragraph("Dinámica en la Sala de Examen", table_header_style)],
        [Paragraph("0 a 1", table_cell_style), Paragraph("Procesos y Puertos", table_cell_style), Paragraph("Todos los integrantes declaran qué procesos corren y en qué puerto.", table_cell_style)],
        [Paragraph("1 a 7", table_cell_style), Paragraph("Flujos A y B", table_cell_style), Paragraph("Un integrante conduce el Flujo A (Identidad); otro el Flujo B (Lo Propio). Nadie conduce 2 seguidos.", table_cell_style)],
        [Paragraph("7 a 12", table_cell_style), Paragraph("Flujos C, D y E", table_cell_style), Paragraph("Conducción de Flujos C (Rol insuficiente) y D (Por detrás / CORS), más 30 seg del Flujo E (seed).", table_cell_style)],
        [Paragraph("12 a 14", table_cell_style), Paragraph("Modificación Señalada", table_cell_style), Paragraph("Una por integrante sobre código que no construyó él (ubicar cursor, explicar cambio y efecto).", table_cell_style)],
        [Paragraph("14 a 15", table_cell_style), Paragraph("Pregunta Botón COMPRAR", table_cell_style), Paragraph("Evaluación de fundamentación técnica de UX vs Seguridad e idempotencia en backend.", table_cell_style)]
    ]
    tbl_reloj = Table(reloj_data, colWidths=[55, 115, 334])
    tbl_reloj.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FBFD")]),
    ]))
    story.append(tbl_reloj)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Las 5 Ventanas Obligatorias Abiertas al Iniciar:</b><br/>"
                           "1. <i>Terminal:</i> Procesos y puertos corriendo (Angular 4200, Gateway 8080, BFF 3001, Microservicios 3002..3005).<br/>"
                           "2. <i>Navegador:</i> App con sesión recién iniciada (token dura 1 hora), pestaña Red limpia y Application con sessionStorage.<br/>"
                           "3. <i>Cliente REST / curl:</i> Dos tokens listos (jugador y admin) para probar 403 vs 200, y llamada directa sin token para 401.<br/>"
                           "4. <i>Editor (VS Code):</i> Pestañas del interceptor HTTP de Angular y de los guards de NestJS ya abiertas.<br/>"
                           "5. <i>Consola AWS Cognito:</i> User Pool con grupos, usuarios y los dos App Clients.", body_style))

    # 5. Framework de Respuesta en 4 Pasos
    story.append(Paragraph("5. El Framework de Respuesta en 4 Pasos de D6 (Slide 16)", h1_style))
    story.append(Paragraph("Para responder cualquier pregunta de arquitectura en 1 minuto sin caer en teoría genérica:", body_style))
    story.append(Paragraph("• <b>1. Qué hice:</b> Nombrar el componente, clase o línea exacta de tu código y abrirla en el editor.", bullet_style))
    story.append(Paragraph("• <b>2. Qué problema resuelve:</b> Describir la necesidad técnica de seguridad, rendimiento, concurrencia o arquitectura.", bullet_style))
    story.append(Paragraph("• <b>3. Qué descarté:</b> Nombrar la alternativa técnica rechazada y por qué no servía. Demuestra análisis y descarta copia ciega (el paso que más nota otorga).", bullet_style))
    story.append(Paragraph("• <b>4. Cómo lo compruebo:</b> Demostrarlo empíricamente en vivo en la pantalla (pestaña Red, dos tokens en curl, terminal).", bullet_style))

    story.append(PageBreak())

    # 6. Guion Oficial Parada por Parada
    story.append(Paragraph("6. Guion Oficial de la Defensa · Parada por Parada (D6)", h1_style))

    def add_pdf_dialogue(parada_title, question, alarm, steps):
        content = []
        content.append(Paragraph(f"<b>{parada_title}</b>", h2_style))
        
        # Q box
        q_p = [Paragraph("<b>Pregunta del Docente (Cristian Calderón):</b>", q_label_style),
               Paragraph(f'«{question}»', q_text_style)]
        tbl_q = Table([[q_p]], colWidths=[504])
        tbl_q.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF5FB")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#2980B9")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        content.append(tbl_q)
        content.append(Spacer(1, 3))

        if alarm:
            w_p = [Paragraph("<b>⚠ SEÑAL DE ALARMA DE D6 (Lo que NUNCA debes responder):</b>", w_label_style),
                   Paragraph(alarm, w_text_style)]
            tbl_w = Table([[w_p]], colWidths=[504])
            tbl_w.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDEDEC")),
                ('BOX', (0,0), (-1,-1), 0.5, c_alert),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            content.append(tbl_w)
            content.append(Spacer(1, 3))

        # A box
        a_p = [Paragraph("<b>Respuesta Técnica Modelo (Framework de 4 Pasos):</b>", a_label_style)]
        for s_num, s_title, s_desc in steps:
            a_p.append(Paragraph(f"<b>{s_num}. {s_title}:</b> {s_desc}", a_step_style))
        tbl_a = Table([[a_p]], colWidths=[504])
        tbl_a.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBF9")),
            ('BOX', (0,0), (-1,-1), 0.5, c_success),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        content.append(tbl_a)
        content.append(Spacer(1, 8))
        return [KeepTogether(content)]

    # Parada A1
    story.extend(add_pdf_dialogue(
        "Parada A1 · Auto-registro y la Trampa de Cognito",
        "Registra un usuario nuevo en la Hosted UI en vivo. Dime: ¿en qué grupo quedó esta cuenta recién creada y quién se lo asignó?",
        "«Yo se lo asigno después a mano en la consola de AWS» (demuestra que el sistema no está automatizado).",
        [
            ("1", "Qué hice", "Quedó asignada automáticamente en el grupo 'jugadores' mediante el fallback seguro en el guard de NestJS (group.guard.ts)."),
            ("2", "Qué problema resuelve", "Resuelve la trampa de Cognito: al auto-registrarse por Hosted UI, Cognito deja cognito:groups vacío. Sin este control, el usuario no tendría rol y recibiría 403 en todas partes."),
            ("3", "Qué descarté", "Descarté asignarlo a mano en la consola de AWS y descarté otorgarle permisos elevados por omisión (principio de menor privilegio)."),
            ("4", "Cómo lo compruebo", "El usuario entra a /catalogo y /biblioteca de inmediato con 200 OK, pero al intentar entrar a /admin/licencias es bloqueado con 403.")
        ]
    ))

    # Parada A2
    story.extend(add_pdf_dialogue(
        "Parada A2 · Claims del Token (Identidad vs Autorización)",
        "Abre el token JWT decodificado en pantalla. ¿Qué claim dice quién eres y cuál dice qué puedes hacer?",
        "Confundir scope con rol de usuario, o creer que el rol está contenido en el claim sub.",
        [
            ("1", "Qué hice", "Utilizo el claim 'sub' para la identidad del sujeto, y 'cognito:groups' junto a 'scope' para la autorización."),
            ("2", "Qué problema resuelve", "Separa la identidad inmutable del permiso concedido: 'sub' es el UUID inmutable que dice quién es la persona; 'cognito:groups' define el rol humano (jugadores, editores, admin); y 'scope' define qué operaciones tiene permitidas la SPA ante la API."),
            ("3", "Qué descarté", "Descarté usar client_id o scopes para autorizar acciones humanas. El client_id solo identifica al software frontend, no a la persona."),
            ("4", "Cómo lo compruebo", "En el payload vemos sub con el UUID, cognito:groups con ['jugadores'] y scope con los 3 scopes asignados al App Client.")
        ]
    ))

    # Parada B1
    story.extend(add_pdf_dialogue(
        "Parada B1 · Una Sola Dirección en Red",
        "Abre la vista /biblioteca en Angular y la pestaña Red. ¿A qué direcciones le habló el navegador para cargar esta pantalla?",
        "Aparecen dos o tres direcciones distintas en la pestaña Red (ej: el frontend habla directo a microservicios).",
        [
            ("1", "Qué hice", "Le habló a UNA SOLA dirección: http://localhost:8080 (nuestro API Gateway)."),
            ("2", "Qué problema resuelve", "Desacopla al frontend de la topología interna. Angular no conoce puertos de microservicios ni su existencia, y emite una sola llamada HTTP (GET /v1/biblioteca) reduciendo drásticamente la latencia."),
            ("3", "Qué descarté", "Descarté que Angular invoque directamente al BFF o a los microservicios. En token.interceptor.ts la lista blanca tiene una sola entrada (http://localhost:8080)."),
            ("4", "Cómo lo compruebo", "La pestaña Red muestra una única llamada a http://localhost:8080/v1/biblioteca. Es el BFF en el backend quien realiza las llamadas internas.")
        ]
    ))

    # Parada B3
    story.extend(add_pdf_dialogue(
        "Parada B3 · Resolución por 'sub' (La Parada Más Discriminante)",
        "Muestra la consulta de biblioteca. ¿De dónde sale el usuario cuyas licencias devuelves? ¿Por qué no lo recibes por parámetro?",
        "Recibir el usuario por query, body o parámetro de ruta («pero igual está protegido porque pide token»).",
        [
            ("1", "Qué hice", "Sale estrictamente del claim 'sub' del JWT verificado criptográficamente en req.user.sub en bff-biblioteca.controller.ts."),
            ("2", "Qué problema resuelve", "Previene la vulnerabilidad crítica BOLA / IDOR. Si la ruta aceptara usuarioId por URL o body, cualquier usuario con token válido podría cambiar el número y espiar o robar juegos ajenos."),
            ("3", "Qué descarté", "Descarté recibir usuarioId en URL (/v1/biblioteca/:usuarioId), query o body. Al inicio lo teníamos por URL para probar en Postman, pero con dos cuentas vimos que se podían cruzar datos y eliminamos el parámetro para siempre."),
            ("4", "Cómo lo compruebo", "En terminal ejecuto GET /v1/biblioteca con el token del Usuario A y devuelve 3 juegos; ejecuto la misma URL con el token del Usuario B y devuelve 2 juegos. La URL es idéntica; solo cambió el token.")
        ]
    ))

    # Parada C
    story.extend(add_pdf_dialogue(
        "Parada C · Rol Insuficiente y Control en Servidor",
        "Con el token de un jugador, demuéstrame que el control de acceso reside en el servidor y no en la interfaz visual.",
        "Responder 401 en vez de 403, o responder 200 y decir «es que en la pantalla el botón no aparece».",
        [
            ("1", "Qué hice", "Protegí la ruta de revocar licencias con @RequireGroups('administradores') y BffGroupsGuard en bff-licencias.controller.ts."),
            ("2", "Qué problema resuelve", "Garantiza que la seguridad no dependa del cliente. Ocultar o deshabilitar un botón en Angular es solo cosmético; cualquier usuario puede enviar un DELETE con curl."),
            ("3", "Qué descarté", "Descarté responder 401. Como el token del jugador es legítimo, responder 401 causaría un bucle infinito de login. La respuesta correcta ante falta de privilegios es estrictamente 403 Forbidden."),
            ("4", "Cómo lo compruebo", "Ejecuto con curl: curl -i -X DELETE -H 'Authorization: Bearer $T_JUGADOR' http://localhost:8080/v1/licencias/lic-001. El backend responde inmediatamente HTTP/1.1 403 Forbidden.")
        ]
    ))

    # Parada D1
    story.extend(add_pdf_dialogue(
        "Parada D1 · Por Detrás / Zero Trust",
        "Llama al BFF y al microservicio directo en su puerto interno, sin pasar por el Gateway. ¿Qué responden y por qué?",
        "Responder 200 OK (demuestra que las capas internas están totalmente abiertas sin autenticación).",
        [
            ("1", "Qué hice", "Configuré BffAuthGuard sobre el controlador del BFF, aplicando el principio de Defensa en Profundidad y Zero Trust."),
            ("2", "Qué problema resuelve", "Evita asumir que la red interna es segura. Si un contenedor vecino está comprometido o alguien se salta el gateway llamando directo a :3001, el BFF no confía ciegamente y exige su propio token."),
            ("3", "Qué descarté", "Descarté la arquitectura de 'castillo y muralla' donde solo el borde valida y los servicios internos quedan desprotegidos respondiendo 200 OK a cualquiera."),
            ("4", "Cómo lo compruebo", "Hago curl -i http://localhost:3001/v1/biblioteca sin cabecera Authorization: responde HTTP/1.1 401 Unauthorized. El BFF se protege solo.")
        ]
    ))

    # Parada D2
    story.extend(add_pdf_dialogue(
        "Parada D2 · Token Alterado y Emisor del 401",
        "Cambia un carácter al medio del token JWT y envíalo. ¿Qué responde el sistema y quién emite ese error?",
        "No saber qué capa lo rechazó ni contra qué se verificó la firma criptográfica.",
        [
            ("1", "Qué hice", "Implementé la verificación de firma criptográfica con jwt.verify en auth.service.ts del API Gateway."),
            ("2", "Qué problema resuelve", "Detecta y bloquea cualquier intento de falsificación o manipulación de datos en el payload del token."),
            ("3", "Qué descarté", "Descarté claves simétricas compartidas (HMAC). El Gateway descarga las claves públicas RSA asimétricas del endpoint JWKS de Cognito (/.well-known/jwks.json)."),
            ("4", "Cómo lo compruebo", "Envío el token alterado al Gateway con curl: responde HTTP/1.1 401 Unauthorized. Lo emite el Gateway en el perímetro exterior al fallar la firma RSA contra el JWKS; la petición ni tocó al BFF.")
        ]
    ))

    # Parada D3
    story.extend(add_pdf_dialogue(
        "Parada D3 · Configuración de CORS",
        "¿Qué origen acepta tu configuración de CORS y qué pasa si te llaman desde otro dominio?",
        "Configurar origin: '*' o creer que el CORS es el mecanismo de control de acceso a la API.",
        [
            ("1", "Qué hice", "Habilité app.enableCors() exclusivamente en el API Gateway, restringido a origin: 'http://localhost:4200'."),
            ("2", "Qué problema resuelve", "Cumple la política de seguridad del navegador para evitar peticiones maliciosas cruzadas desde sitios de terceros."),
            ("3", "Qué descarté", "Descarté origin: '*' ('para que no diera problemas') y descarté configurar CORS en el BFF o microservicios (CORS es exclusivo de navegadores; entre servidores Node no aplica)."),
            ("4", "Cómo lo compruebo", "Si un navegador llama desde otro origen, el navegador bloquea la respuesta. Si se llama con curl, la petición pasa porque curl no aplica políticas de navegador (el control real es el token).")
        ]
    ))

    # Parada E
    story.extend(add_pdf_dialogue(
        "Parada E · Origen y Trazabilidad del Catálogo",
        "¿De dónde salieron los juegos del catálogo? ¿Qué pasa si borro catalogo.json y clono en una máquina limpia?",
        "«Los escribí a mano», o tener el archivo catalogo.json pero no tener el script seed que lo generó.",
        [
            ("1", "Qué hice", "Creé el script data/seed.ts que consume la API externa real de FreeToGame y guarda los registros normalizados en data/catalogo.json."),
            ("2", "Qué problema resuelve", "Garantiza la trazabilidad institucional: prohibido tener datos inventados a mano en arreglos de memoria o datos ficticios no reproducibles."),
            ("3", "Qué descarté", "Descarté escribir el JSON a mano o depender de una base de datos local que no se pueda versionar en el repositorio."),
            ("4", "Cómo lo compruebo", "Si borro data/catalogo.json y ejecuto npm run seed, el script consume la API externa de FreeToGame, filtra campos y regenera el archivo catalogo.json de forma 100% idéntica.")
        ]
    ))

    # 7. Reglas de Negocio, Licencias e Identificadores
    story.append(Paragraph("7. Reglas de Negocio, Gestión de Licencias e Identificadores", h1_style))
    story.append(Paragraph("El docente Cristian Calderón profundiza en el modelo de datos y las decisiones de diseño de software digital:", body_style))

    story.extend(add_pdf_dialogue(
        "N1 · Modelado y Gestión de Licencias (Single Source of Truth)",
        "Muestra el modelo de licencias. ¿Cómo se gestionan, quién es el dueño de esos datos, cómo nacen y cómo se relacionan con los juegos y usuarios?",
        "Decir que las licencias se guardan dentro de Cognito o que el Catálogo administra quién compró los juegos.",
        [
            ("1", "Qué hice", "Modelé la entidad Licencia (vidalstore-backend/src/models/licencia.model.ts) con id (UUID v4), juegoId, usuarioSub (claim sub), fechaAdquisicion, plataforma, tienda, region, codigoCanje (VS-XXXXXXXXXXXXXXXX), estadoPago y precioPagado. Biblioteca (biblioteca.service.ts) es el único dueño (Single Source of Truth), respaldado en MemoryStorageService y persistido en data/licencias.json."),
            ("2", "Qué problema resuelve", "Modela la relación N:M entre usuarios y juegos desacoplando la transacción comercial de la titularidad digital. Compras simula el pago y delega por HTTP interno a Biblioteca la creación de la licencia."),
            ("3", "Qué descarté", "Descarté guardar licencias embebidas en el usuario (los usuarios viven en AWS Cognito) y descarté que Catálogo guarde tenencia privada."),
            ("4", "Cómo lo compruebo", "En biblioteca.service.ts vemos crearLicencia(). Al consultar GET /v1/biblioteca, el BFF obtiene las licencias de ese usuarioSub, las enriquece con el catálogo y devuelve el inventario propio.")
        ]
    ))

    story.append(PageBreak())

    story.extend(add_pdf_dialogue(
        "N2 · Identificador de Usuario (Por qué 'sub' UUID y NO email/username)",
        "¿Por qué en las licencias guardas 'usuarioSub' en lugar del correo electrónico (email) o username? ¿Qué ganaron con esa decisión?",
        "Creer que usar email es mejor 'porque es más legible', ignorando la mutabilidad del correo y la fuga de datos personales (PII).",
        [
            ("1", "Qué hice", "Utilicé como clave foránea única de usuario el claim sub (Subject) de Cognito (UUID v4 inmutable de 36 caracteres), extraído de req.user.sub tras verificar la firma RSA."),
            ("2", "Qué problema resuelve", "1) Inmutabilidad: El email puede cambiar en Cognito; el sub nunca cambia (evita perder compras). 2) Privacidad por Diseño (Zero PII Leakage / GDPR): El sub es un UUID opaco sin datos personales. 3) Desacoplamiento del IdP: La base de datos solo conoce UUIDs RFC 4122; si cambiamos Cognito por Keycloak, el modelo no cambia."),
            ("3", "Qué descarté", "Descarté usar email o username como claves primarias, y descarté inventar un ID numérico de usuario local que requeriría tablas de sincronización."),
            ("4", "Cómo lo compruebo", "Decodificando el JWT en jwt.io: sub contiene el UUID inmutable que coincide exactamente con los registros de licencias.json.")
        ]
    ))

    story.extend(add_pdf_dialogue(
        "N3 · Identificador de Licencia (Por qué UUID v4 y NO un autoincremental)",
        "¿Por qué el ID de la licencia es un UUID (randomUUID()) y no un número secuencial simple como 1, 2, 3...?",
        "«Es que NestJS me lo dio así», sin entender el impacto en sistemas distribuidos ni la seguridad contra enumeración de URLs.",
        [
            ("1", "Qué hice", "En biblioteca.service.ts y memory-storage.service.ts, cada nueva licencia recibe id: randomUUID(), generado con el módulo nativo criptográfico node:crypto."),
            ("2", "Qué problema resuelve", "1) Sistemas Distribuidos sin Cuello de Botella: En microservicios, los IDs autoincrementales exigen base de datos centralizada con bloqueos. UUID v4 se genera descentralizado en cualquier nodo con colisión despreciable (2^122). 2) Anti-Scraping y Confidencialidad: Si fueran 101, 102, un competidor deduciría el volumen diario de ventas y atacantes enumerarían URLs (/licencias/103)."),
            ("3", "Qué descarté", "Descarté secuencias numéricas (id: ++contador) y bibliotecas externas pesadas; usamos el generador criptográfico nativo de Node.js."),
            ("4", "Cómo lo compruebo", "Al generar dos compras vía /v1/compras, los IDs en licencias.json son hashes UUID v4 independientes de 36 caracteres.")
        ]
    ))

    story.append(PageBreak())

    story.extend(add_pdf_dialogue(
        "N4 · Convivencia de IDs (Catálogo FreeToGame '452' vs Licencias UUID)",
        "Veo que en el catálogo los IDs son números como '452', pero las licencias son UUIDs. ¿Por qué esa diferencia y cómo conviven ambos?",
        "No saber de dónde provienen los IDs de los juegos ni por qué se almacenan como cadenas en TypeScript.",
        [
            ("1", "Qué hice", "En catálogo tipamos id: string en TypeScript, con valores numéricos seriales provenientes del script seed.ts (FreeToGame API). En la licencia almacenamos juegoId: string como clave foránea que referencia ese ID de catálogo."),
            ("2", "Qué problema resuelve", "Separa datos del proveedor externo y transacciones internas: Catálogo refleja una API externa manteniendo su ID original para trazabilidad y resincronización. Licencia es un bien transaccional propio que requiere identificadores únicos globales (UUID v4). Tipar ambos como string desacopla esquemas y previene problemas de coerción de tipos."),
            ("3", "Qué descarté", "Descarté sobreescribir los IDs de FreeToGame con nuevos UUIDs en el seed, porque habríamos destruido el identificador oficial del juego."),
            ("4", "Cómo lo compruebo", "En catalogo.json vemos { 'id': '452', 'titulo': 'Warzone' } y en licencias.json vemos { 'id': 'uuid-v4...', 'juegoId': '452', 'usuarioSub': 'uuid-sub...' }.")
        ]
    ))

    story.extend(add_pdf_dialogue(
        "N5 · Unicidad e Idempotencia (HTTP 409 Conflict en Compras)",
        "¿Qué regla de negocio impide que un usuario compre dos veces el mismo juego y cómo está implementada en el código?",
        "Decir que con ocultar el botón en Angular basta, delegando la regla de negocio y la seguridad al cliente.",
        [
            ("1", "Qué hice", "En biblioteca.service.ts, crearLicencia() ejecuta primero buscarLicenciaPorUsuarioYJuego(usuarioSub, juegoId). Si existe, arroja ConflictException (HTTP 409 Conflict): 'El usuario ya posee una licencia activa para el juego con ID ...'."),
            ("2", "Qué problema resuelve", "Aplica la regla de comercialización digital: en software la posesión es unívoca (no compras 2 unidades). Previene cobros duplicados por doble clic, reintentos automáticos o llamadas directas maliciosas con curl."),
            ("3", "Qué descarté", "Descarté delegar la comprobación al frontend (en F12 cualquiera habilita el botón) y descarté responder 200 OK cobrando de nuevo o sobreescribiendo la fecha de compra original."),
            ("4", "Cómo lo compruebo", "Envío 2 peticiones POST /v1/compras con el mismo juegoId: la primera responde 201 Created y la segunda responde 409 Conflict.")
        ]
    ))

    story.append(PageBreak())

    story.extend(add_pdf_dialogue(
        "N6 · Código de Canje (CD-Key con Criptografía Segura)",
        "¿Para qué sirve el campo 'codigoCanje' en la licencia y con qué criterio se genera?",
        "No saber para qué existe el código de canje o creer que es un simple adorno estético sin valor comercial.",
        [
            ("1", "Qué hice", "En biblioteca.service.ts, al crear la licencia se genera: codigoCanje: `VS-${randomUUID().replaceAll('-', '').slice(0, 16).toUpperCase()}`."),
            ("2", "Qué problema resuelve", "Separa la titularidad legal de la entrega digital de la credencial: la Licencia es el derecho en VidalStore; el Código de Canje (CD-Key) es la credencial alfanumérica única de 16 caracteres hexadecimales para canjear en Steam o Epic Games."),
            ("3", "Qué descarté", "Descarté generar códigos con Math.random() (pseudo-aleatorio predecible). randomUUID() garantiza entropía criptográfica segura de CSPRNG."),
            ("4", "Cómo lo compruebo", "Al inspeccionar una licencia devuelta en /v1/biblioteca, incluye el código de canje formateado con prefijo institucional: VS-E4A83C90D1F5B2E7.")
        ]
    ))

    story.append(Spacer(1, 10))

    # 8. Modificación Señalada
    story.append(Paragraph("8. La Modificación Señalada (Minutos 12 a 14)", h1_style))
    story.append(Paragraph("El docente pide una modificación puntual sobre código que NO construyó el estudiante. No se programa en vivo: se abre el archivo, se ubica la línea con el cursor y se explica qué se escribiría y qué pasaría:", body_style))
    story.append(Paragraph("• <b>Caso 1: ¿Dónde y cómo agregarías una ruta que solo consulten administradores?</b><br/>"
                           "«Voy a bff-licencias.controller.ts en el BFF. Agrego el método con @RequireGroups('administradores') y @UseGuards(BffAuthGuard, BffGroupsGuard). Luego voy a gateway.controller.ts en el Gateway y creo la ruta proxy correspondiente con @RequireGroups('administradores') reenviando el encabezado Authorization.»", bullet_style))
    story.append(Paragraph("• <b>Caso 2: ¿Qué se rompe si borro la línea que inyecta 'Authorization: Bearer' en Angular?</b><br/>"
                           "«En src/app/auth/token.interceptor.ts comento setHeaders['Authorization'] = 'Bearer ...'. Angular sigue compilando, pero al cargar catálogo o biblioteca, las peticiones HTTP saldrán sin token. El Gateway cortará inmediatamente con 401 Unauthorized y la pantalla quedará en blanco.»", bullet_style))
    story.append(Paragraph("• <b>Caso 3: ¿Qué error da si configuro en el Gateway el client_id del otro App Client?</b><br/>"
                           "«En el .env del Gateway cambio COGNITO_CLIENT_ID por el del App Client 2. Al hacer peticiones desde Angular, el Gateway validará la firma contra el JWKS (pasará), pero en auth.service.ts comparará payload.client_id con la variable: no coincidirán y responderá 401 Unauthorized ('Token de cliente no autorizado'). Ningún usuario podrá entrar.»", bullet_style))
    story.append(Paragraph("• <b>Caso 4: ¿Qué pasa si quitas un microservicio del Promise.all en el BFF?</b><br/>"
                           "«En bff-licencias.service.ts, si quito la consulta a catálogo del Promise.all, la biblioteca devuelve licencias pero sin título, portada ni metadatos para enriquecerlas. El mapper fallará al buscar en el Map o devolverá datos incompletos. Se rompe el principio de agregación del BFF.»", bullet_style))

    # 9. Pregunta Botón COMPRAR
    story.append(Paragraph("9. La Pregunta del Botón COMPRAR (Minutos 14 a 15)", h1_style))
    story.append(Paragraph("<b>Pregunta del Docente:</b> <i>«Si el usuario ya posee la licencia de un juego, ¿qué debe hacer el botón COMPRAR en la interfaz? ¿Ocultarse, deshabilitarse, o permitir el clic y que el servidor responda con error?»</i>", body_style))
    story.append(Paragraph("<b>Argumentación Técnica de Ingeniería:</b><br/>"
                           "1. <b>En la Interfaz (UX):</b> Deshabilitar el botón o cambiarlo a 'Ya adquirido' / 'Jugar' mejora la experiencia de usuario, evita frustración y ahorra tráfico de red innecesario.<br/>"
                           "2. <b>En el Backend (Mandatorio):</b> La seguridad y las reglas de negocio NUNCA se delegan al cliente. Cualquier usuario puede manipular el DOM en F12 o enviar un curl POST /v1/compras directo. Por eso el microservicio de biblioteca es estrictamente IDEMPOTENTE: en biblioteca.service.ts comprueba si existe la tupla (usuarioSub, juegoId) y responde ConflictException (HTTP 409 Conflict), evitando duplicar licencias o cobros.<br/>"
                           "<b>Conclusión de Oro:</b> <i>«En la UI lo deshabilito por experiencia de usuario, pero el backend siempre valida la idempotencia y responde 409 Conflict si la llamada llega.»</i>", body_style))

    story.append(PageBreak())

    # 10. Preguntas Transversales y Pulso
    story.append(Paragraph("10. Preguntas Transversales y Resumen de Pulso.pdf (§12.2)", h1_style))
    story.append(Paragraph("• <b>Si entra un quinto microservicio, ¿qué se toca?:</b> Solo se tocan dos capas del backend: en el BFF se agrega la llamada interna y se mapea en el Promise.all; y en el Gateway se crea la ruta proxy si se requiere exponer un endpoint público /v1/... En Angular NO se toca ninguna URL: el frontend solo conoce http://localhost:8080.", bullet_style))
    story.append(Paragraph("• <b>¿Qué pasa si un microservicio interno se cae?:</b> El BFF captura el error de conexión y responde 503 Service Unavailable indicando qué servicio falló. Cuando el microservicio se restablece, el sistema vuelve a responder 200 OK inmediatamente sin necesidad de reiniciar el Gateway ni el BFF.", bullet_style))
    story.append(Paragraph("• <b>¿Qué gana el frontend con el BFF? (Números medidos):</b> Gana una sola llamada de red en lugar de múltiples peticiones; concurrencia en servidor mediante Promise.all (con 300 ms de latencia por servicio, en serie serían 600 ms y en paralelo son ~300 ms); cruce de datos en memoria O(N) con Map por ID; y cero fuga de datos internos confidenciales hacia el inspector F12.", bullet_style))

    # 11. Bitácora de Errores
    story.append(Paragraph("11. Bitácora de Errores Reales del Proyecto (D6 \"Qué Descarté\")", h1_style))
    story.append(Paragraph("Tener presentes 5 errores reales que ocurrieron durante el desarrollo demuestra autoría técnica indiscutible:", body_style))
    story.append(Paragraph("1. <b>Error de Secreto en SPA:</b> Al crear el App Client en Cognito le pusimos client_secret para Angular. Amplify no podía autenticar porque las SPAs públicas no pueden almacenar secretos. Tuvimos que recrear el App Client sin secreto.", bullet_style))
    story.append(Paragraph("2. <b>Error de Token Expirado:</b> Estábamos probando un endpoint con curl y de repente dio 401. El token de Cognito había cumplido sus 60 minutos de vigencia (exp). Tuvimos que volver a iniciar sesión.", bullet_style))
    story.append(Paragraph("3. <b>Error de la Trampa de Cognito:</b> Al registrarnos con un usuario nuevo en la Hosted UI, no podíamos ver el catálogo (403). Cognito no asigna grupos por omisión; lo resolvimos con el fallback seguro a 'jugadores' en el guard.", bullet_style))
    story.append(Paragraph("4. <b>Error de CORS en Backend:</b> Intentamos poner CORS en el BFF. Nos dimos cuenta de que CORS es exclusivo de navegadores web y que las llamadas internas entre Node.js son backend-to-backend, por lo que CORS solo debe vivir en el Gateway.", bullet_style))
    story.append(Paragraph("5. <b>Error de Whitelist en Interceptor:</b> En Angular interceptábamos todas las URLs. Al cargar fuentes de Google se enviaba el Bearer token a Google. Lo corregimos con la whitelist estricta: solo inyectar token si la URL inicia con http://localhost:8080.", bullet_style))

    story.append(Spacer(1, 10))

    # Checklist Final Table
    chk_title = Paragraph("<b>Checklist de los 60 Segundos Finales Antes de Entrar a la Sala</b>", h2_style)
    chk_items = [
        [chk_title, ""],
        [Paragraph("<b>1. Procesos y Puertos:</b>", q_label_style), Paragraph("Angular (4200), Gateway (8080), BFF (3001), Catálogo (3002), Biblioteca (3003), Compras (3004), Logs (3005) corriendo en terminales limpios.", body_style)],
        [Paragraph("<b>2. Navegador:</b>", q_label_style), Paragraph("http://localhost:4200 con sesión iniciada, pestaña Red limpia en Fetch/XHR lista para inspeccionar una sola llamada a 8080.", body_style)],
        [Paragraph("<b>3. Terminal / curl:</b>", q_label_style), Paragraph("Dos tokens listos en variables de entorno o bloc de notas (jugador y admin) para probar 403 vs 200 al instante.", body_style)],
        [Paragraph("<b>4. Editor VS Code:</b>", q_label_style), Paragraph("Archivos abiertos: token.interceptor.ts, gateway.controller.ts, bff-licencias.service.ts, seed.ts, biblioteca.service.ts.", body_style)],
        [Paragraph("<b>5. Consola AWS Cognito:</b>", q_label_style), Paragraph("User Pool abierto mostrando usuarios, grupos (jugadores, administradores) y los 2 App Clients (con y sin secreto).", body_style)],
    ]
    tbl_chk = Table(chk_items, colWidths=[120, 384])
    tbl_chk.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#EAEDED")),
        ('BACKGROUND', (0, 1), (1, -1), colors.HexColor("#F9FBFD")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1B365D")),
        ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl_chk)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()

