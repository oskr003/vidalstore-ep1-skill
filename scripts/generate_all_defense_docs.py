import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.pdfgen import canvas

DOCX_PATH = "/Users/oscar/Downloads/DUOC/CloudNative/Evaluacion 1/Guia_Defensa_VidalStore_EP1_D6.docx"
PDF_PATH = "/Users/oscar/Downloads/DUOC/CloudNative/Evaluacion 1/Guia_Defensa_VidalStore_EP1_D6.pdf"

# -------------------------------------------------------------
# DATA DICTIONARY OF DEFENSE DIALOGUES
# -------------------------------------------------------------
DIALOGUES = [
    {
        "id": "A1",
        "section": "Flujo A · Identidad y Tokens",
        "title": "A1 · Auto-registro y la Trampa de Cognito",
        "question": "Registra un usuario nuevo en la Hosted UI en vivo. Dime: ¿en qué grupo quedó esta cuenta recién creada y quién se lo asignó?",
        "alarm": "«Yo se lo asigno después a mano en la consola de AWS» (demuestra que el sistema no está automatizado ni preparado para producción).",
        "steps": [
            ("1", "Qué hice", "Quedó asignada automáticamente en el grupo 'jugadores' mediante el fallback seguro en el guard de NestJS (groups.guard.ts)."),
            ("2", "Qué problema resuelve", "Resuelve la trampa de Cognito: al auto-registrarse por Hosted UI, Cognito deja cognito:groups vacío. Sin este control, el usuario no tendría rol y recibiría 403 Forbidden en todas las rutas."),
            ("3", "Qué descarté", "Descarté asignarlo a mano en AWS (autoservicio no depende de administración manual) y descarté otorgarle permisos elevados por omisión (principio de menor privilegio)."),
            ("4", "Cómo lo compruebo", "El usuario entra a /catalogo y /biblioteca con 200 OK, pero al intentar entrar a /licencias o /auditoria es bloqueado inmediatamente con 403 Forbidden.")
        ],
        "code": "// vidalstore-gateway/src/auth/groups.guard.ts:L35-L39\nconst rawGroups: string[] = Array.isArray(user['cognito:groups']) ? user['cognito:groups'] : [];\nconst userGroups: string[] = rawGroups.length > 0 ? rawGroups : ['jugadores'];",
        "cmd": None
    },
    {
        "id": "A2",
        "section": "Flujo A · Identidad y Tokens",
        "title": "A2 · Claims del Token (Identidad vs Autorización)",
        "question": "Abre el token JWT decodificado en pantalla. ¿Qué claim dice quién eres y cuál dice qué puedes hacer?",
        "alarm": "Confundir el scope con el rol de usuario, o creer que el rol humano está contenido en el claim sub.",
        "steps": [
            ("1", "Qué hice", "Utilizo el claim sub para la identidad del sujeto, y cognito:groups junto a scope para la autorización."),
            ("2", "Qué problema resuelve", "Separa técnicamente la identidad inmutable del permiso: sub es el UUID inmutable que dice quién es la persona; cognito:groups define el rol humano (jugadores, administradores); y scope define qué operaciones tiene permitidas la SPA ante el Resource Server."),
            ("3", "Qué descarté", "Descarté usar el client_id o los scopes para autorizar acciones humanas. El client_id solo identifica al software frontend, no a la persona."),
            ("4", "Cómo lo compruebo", "En el payload decodificado vemos sub con el UUID del usuario, cognito:groups con ['jugadores'] y scope con los scopes autorizados.")
        ],
        "code": "// Payload del JWT emitido por Cognito User Pool:\n{\n  \"sub\": \"c4f82a91-4d3e-4fa2-9856-123456789abc\", // Identidad inmutable\n  \"cognito:groups\": [\"jugadores\"],                // Rol humano\n  \"scope\": \"openid email vidalstore/catalogo.leer\" // Permisos del cliente SPA\n}",
        "cmd": None
    },
    {
        "id": "B1",
        "section": "Flujo B · Lo Propio y Agregación",
        "title": "B1 · Una Sola Dirección en Red (El Perímetro)",
        "question": "Abre la vista /biblioteca en Angular y la pestaña Red. ¿A qué direcciones le habló el navegador para cargar esta pantalla?",
        "alarm": "Que aparezcan llamadas directas a localhost:3001 (BFF) o 3002..3005 (Microservicios) en la pestaña Red de Angular.",
        "steps": [
            ("1", "Qué hice", "Le habló a UNA SOLA dirección: http://localhost:8080 (nuestro API Gateway)."),
            ("2", "Qué problema resuelve", "Asegura el desacoplamiento total y oculta la topología interna: Angular no sabe qué microservicios existen ni en qué puertos corren. Centraliza CORS, TLS y validación de tokens en el perímetro."),
            ("3", "Qué descarté", "Descarté que Angular llame directo al BFF (3001) o a los microservicios (3002..3005), lo que expondría la arquitectura interna y violaría el principio de frontera perimetral."),
            ("4", "Cómo lo compruebo", "En la pestaña Red (Fetch/XHR) al recargar /biblioteca se observa una única petición HTTP hacia http://localhost:8080/v1/biblioteca con respuesta 200 OK.")
        ],
        "code": "// vidalstore-frontend/src/app/auth/token.interceptor.ts:L5-L9\nconst PERMITIDOS = ['http://localhost:8080'];\nconst esPermitido = PERMITIDOS.some((base) => req.url.startsWith(base)) || req.url.startsWith('/v1');\nif (!esPermitido) return next(req);",
        "cmd": None
    },
    {
        "id": "B2",
        "section": "Flujo B · Lo Propio y Agregación",
        "title": "B2 · Inspección en Vivo de Peticiones y Puertos",
        "question": "Muestra en tu terminal los procesos corriendo y cómo se comunican.",
        "alarm": "Tener microservicios apagados o creer que el Gateway y el BFF son el mismo proceso.",
        "steps": [
            ("1", "Qué hice", "Mantenemos procesos Node.js independientes: Gateway (8080), BFF (3001) y Microservicios (3002 Catálogo, 3003 Biblioteca, 3004 Compras, 3005 Logs)."),
            ("2", "Qué problema resuelve", "Garantiza aislamiento de fallos: si el microservicio de logs se cae, el catálogo y las compras siguen operando sin interrupción."),
            ("3", "Qué descarté", "Descarté un monolito modular donde todo corre en el mismo puerto y memoria."),
            ("4", "Cómo lo compruebo", "Ejecutando lsof en la terminal: se aprecian los puertos escuchando de forma simultánea y autónoma.")
        ],
        "code": "// vidalstore-gateway/src/main.ts:L17-L19\nconst port = process.env.PORT ?? 8080;\nawait app.listen(port, '0.0.0.0');\nconsole.log(`Gateway corriendo en http://localhost:${port}`);",
        "cmd": "lsof -iTCP:4200,8080,3001,3002,3003,3004,3005 -sTCP:LISTEN -n -P"
    },
    {
        "id": "B3",
        "section": "Flujo B · Lo Propio y Agregación",
        "title": "B3 · Resolución por 'sub' (La Parada Más Discriminante)",
        "question": "Muestra la consulta de biblioteca. ¿De dónde sale el usuario cuyas licencias devuelves? ¿Por qué no lo recibes por URL?",
        "alarm": "Recibir el usuario por query (?usuarioId=...) o body en GET («pero igual está protegido con token»). Revela vulnerabilidad BOLA / IDOR.",
        "steps": [
            ("1", "Qué hice", "El usuario se obtiene estrictamente de req.user.sub, extraído del token JWT verificado por el JwtGuard. No existe ningún parámetro de usuario en la ruta /v1/biblioteca."),
            ("2", "Qué problema resuelve", "Elimina de raíz la vulnerabilidad OWASP API #1: BOLA / IDOR. Si recibiera el ID por parámetro, cualquier usuario autenticado podría espiar juegos ajenos cambiando un valor."),
            ("3", "Qué descarté", "Descarté rutas estilo /v1/biblioteca/:usuarioId (que usé al principio en pruebas locales con Postman y luego corregí)."),
            ("4", "Cómo lo compruebo", "Mismo endpoint /v1/biblioteca llamado con Token de Usuario A devuelve sus juegos; con Token de Usuario B devuelve los juegos de B. Cero parámetros en la URL.")
        ],
        "code": "// vidalstore-backend/src/bff/biblioteca/bff-biblioteca.controller.ts:L22-L30\n@Get()\n@UseGuards(BffAuthGuard)\nasync obtenerBiblioteca(@CurrentUser('sub') usuarioSub: string) {\n  if (!usuarioSub) throw new UnauthorizedException('sub no resuelto');\n  return this.bffHttpService.request(this.bffHttpService.bibliotecaUrl, 'GET', '/v1/biblioteca');\n}",
        "cmd": "curl -s -H \"Authorization: Bearer $TOKEN_USUARIO_A\" http://localhost:8080/v1/biblioteca | jq '.[].juego.titulo'\ncurl -s -H \"Authorization: Bearer $TOKEN_USUARIO_B\" http://localhost:8080/v1/biblioteca | jq '.[].juego.titulo'"
    },
    {
        "id": "B4",
        "section": "Flujo B · Lo Propio y Agregación",
        "title": "B4 · Agregación en Memoria con Promise.all y Map",
        "question": "Muestra el código del BFF donde combinas los datos de biblioteca y catálogo. ¿Por qué se hace así?",
        "alarm": "Hacer las llamadas en serie con await secuencial (duplica latencia) o cruzar arreglos con un find O(N²) anidado dentro de un map.",
        "steps": [
            ("1", "Qué hice", "Ejecuto Promise.all para consultar en paralelo al microservicio de biblioteca y al de catálogo; luego indexo el catálogo en un Map por ID para resolver en tiempo O(1)."),
            ("2", "Qué problema resuelve", "Reduce la latencia total al máximo entre ambas llamadas (max(T1, T2) ≈ 300 ms en lugar de T1 + T2 = 600 ms) y optimiza el cruce a O(N) computacional."),
            ("3", "Qué descarté", "Descarté llamadas secuenciales await biblioteca; await catalogo; y descarté que Angular haga el cruce en el cliente (fugaría datos confidenciales)."),
            ("4", "Cómo lo compruebo", "En bff-biblioteca.controller.ts vemos Promise.all([request(biblioteca), request(catalogo)]) y new Map(catalogo.map(j => [j.id, j])).")
        ],
        "code": "// vidalstore-backend/src/bff/biblioteca/bff-biblioteca.controller.ts:L35-L56\nconst [licencias, catalogo] = await Promise.all([\n  this.bffHttpService.request<Licencia[]>(this.bffHttpService.bibliotecaUrl, 'GET', '/v1/biblioteca', authHeader),\n  this.bffHttpService.request<Juego[]>(this.bffHttpService.catalogoUrl, 'GET', '/v1/catalogo', authHeader).catch(() => []),\n]);\nconst juegoMap = new Map<string, Juego>(catalogo.map((j) => [j.id, j]));",
        "cmd": None
    },
    {
        "id": "C1",
        "section": "Flujo C · Rol Insuficiente",
        "title": "C1 · Rol Insuficiente y Rechazo en Capa Exterior",
        "question": "Con el token del jugador, intenta ejecutar una operación administrativa (revocar licencia). ¿Qué responde el sistema y quién lo rechaza?",
        "alarm": "Responder 401 en lugar de 403, o responder 200 diciendo «es que en Angular el botón está deshabilitado / oculto».",
        "steps": [
            ("1", "Qué hice", "El Gateway aplica GroupsGuard con @RequireGroups('administradores') sobre la ruta DELETE /v1/licencias/:id."),
            ("2", "Qué problema resuelve", "Aplica el principio de corte perimetral: si el token es válido pero el rol es insuficiente, el Gateway rechaza inmediatamente con 403 Forbidden sin tocar al BFF ni a los microservicios."),
            ("3", "Qué descarté", "Descarté delegar la seguridad al frontend (ocultar botones) y descarté responder 401 (el token sí es válido y sabemos quién es el usuario)."),
            ("4", "Cómo lo compruebo", "Llamando a DELETE /v1/licencias/xyz con token de jugador: responde HTTP/1.1 403 Forbidden; con token de administrador: responde 200 OK.")
        ],
        "code": "// vidalstore-gateway/src/gateway.controller.ts:L83-L86\n@Delete('licencias/:licenciaId')\n@UseGuards(AuthGuard, GroupsGuard)\n@RequireGroups('administradores')\nasync revocarLicencia(@Param('licenciaId') licenciaId: string, @Request() req: ExpressRequest) {\n  return this.gatewayService.forward('DELETE', `/v1/licencias/${licenciaId}`, req);\n}",
        "cmd": "curl -i -X DELETE -H \"Authorization: Bearer $TOKEN_JUGADOR\" http://localhost:8080/v1/licencias/test-id  # 403 Forbidden\ncurl -i -X DELETE -H \"Authorization: Bearer $TOKEN_ADMIN\" http://localhost:8080/v1/licencias/test-id    # 200 OK"
    },
    {
        "id": "D1",
        "section": "Flujo D · Por Detrás y CORS",
        "title": "D1 · Por Detrás / Zero Trust",
        "question": "Llama directamente al BFF (puerto 3001) sin token. ¿Qué responde y por qué?",
        "alarm": "Que el BFF responda 200 OK asumiendo que «como es interno, la red es de confianza».",
        "steps": [
            ("1", "Qué hice", "El BFF implementa su propio BffAuthGuard que exige y valida el token Bearer en cada petición."),
            ("2", "Qué problema resuelve", "Aplica Defensa en Profundidad y Zero Trust: nunca asumir confianza en la red interna ni dar por sentado que el tráfico viene exclusivamente del Gateway."),
            ("3", "Qué descarté", "Descarté dejar los microservicios internos sin autenticación basándome solo en seguridad perimetral."),
            ("4", "Cómo lo compruebo", "curl -i http://localhost:3001/v1/biblioteca responde inmediatamente HTTP/1.1 401 Unauthorized.")
        ],
        "code": "// vidalstore-backend/src/auth/guards/auth.guard.ts:L19-L26\nif (!authHeader || typeof authHeader !== 'string' || !authHeader.startsWith('Bearer ')) {\n  throw new UnauthorizedException('Cabecera Authorization ausente (debe iniciar con Bearer <token>)');\n}",
        "cmd": "curl -i http://localhost:3001/v1/biblioteca  # HTTP/1.1 401 Unauthorized emitido por el BFF"
    },
    {
        "id": "D2",
        "section": "Flujo D · Por Detrás y CORS",
        "title": "D2 · Token Alterado y Emisor del 401",
        "question": "Cambia un carácter al medio del token JWT y envíalo. ¿Qué responde el sistema y quién emite ese error?",
        "alarm": "No saber qué capa emite el error ni contra qué se verifica la firma criptográfica (creer que se valida contra una base de datos local).",
        "steps": [
            ("1", "Qué hice", "El Gateway verifica la firma criptográfica RSA del JWT contra las claves públicas del endpoint JWKS de AWS Cognito."),
            ("2", "Qué problema resuelve", "Garantiza la integridad estricta del token: cualquier manipulación de claims o firma invalida el token al instante sin requerir llamadas de red bloqueantes."),
            ("3", "Qué descarté", "Descarté claves simétricas compartidas (HMAC) o validación en base de datos local."),
            ("4", "Cómo lo compruebo", "Envío el token alterado al Gateway con curl: responde HTTP/1.1 401 Unauthorized en el perímetro exterior; la petición ni tocó al BFF.")
        ],
        "code": "// vidalstore-backend/src/auth/auth.service.ts:L44-L46\nconst { payload } = await jwtVerify(token, this.jwks, { issuer }); // Valida firma RSA contra endpoint JWKS",
        "cmd": "TOKEN_ALTERADO=\"${TOKEN_JUGADOR:0:20}X${TOKEN_JUGADOR:21}\"\ncurl -i -H \"Authorization: Bearer $TOKEN_ALTERADO\" http://localhost:8080/v1/catalogo  # 401 Unauthorized"
    },
    {
        "id": "D3",
        "section": "Flujo D · Por Detrás y CORS",
        "title": "D3 · Origen de CORS",
        "question": "¿Qué origen acepta tu configuración de CORS y qué pasa si te llaman desde otro dominio?",
        "alarm": "Configurar origin: '*' («para que no diera problemas») o creer que CORS es un firewall de seguridad para llamadas de backend o curl.",
        "steps": [
            ("1", "Qué hice", "Habilité app.enableCors() exclusivamente en el API Gateway, restringido a origin: 'http://localhost:4200'."),
            ("2", "Qué problema resuelve", "Cumple la política de seguridad del navegador para evitar peticiones cruzadas no autorizadas desde otros sitios web."),
            ("3", "Qué descarté", "Descarté origin: '*' y descarté configurar CORS en el BFF o microservicios (entre procesos Node.js no aplica CORS)."),
            ("4", "Cómo lo compruebo", "Llamada con navegador desde otro origen es bloqueada. Llamada con curl pasa porque curl no aplica políticas de navegador (el control real es el token JWT).")
        ],
        "code": "// vidalstore-gateway/src/main.ts:L12-L16\napp.enableCors({\n  origin: 'http://localhost:4200',\n  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],\n  allowedHeaders: ['Content-Type', 'Authorization', 'ngrok-skip-browser-warning'],\n});",
        "cmd": None
    },
    {
        "id": "E1",
        "section": "Flujo E · Origen y Trazabilidad",
        "title": "E1 · Origen y Trazabilidad del Catálogo",
        "question": "¿De dónde salieron los juegos del catálogo? ¿Qué pasa si borro catalogo.json y clono en una máquina limpia?",
        "alarm": "«Los escribí a mano», o tener el archivo catalogo.json pero no tener el script seed que lo generó de forma reproducible.",
        "steps": [
            ("1", "Qué hice", "Creé el script data/seed.ts que consume la API externa real de FreeToGame y guarda los registros normalizados en data/catalogo.json."),
            ("2", "Qué problema resuelve", "Garantiza la trazabilidad institucional: prohibido tener datos ficticios inventados a mano que no sean reproducibles."),
            ("3", "Qué descarté", "Descarté escribir el JSON a mano o depender de una base de datos local que no se pueda versionar en el repositorio."),
            ("4", "Cómo lo compruebo", "Borro data/catalogo.json y ejecuto npm run seed: el script consume FreeToGame y regenera el archivo de forma 100% determinista.")
        ],
        "code": "// vidalstore-backend/data/seed.ts:L22-L35\nconst res = await fetch('https://www.freetogame.com/api/games');\nconst data = await res.json();\nconst catalogo = data.slice(0, 50).map(j => ({ id: String(j.id), titulo: j.title, precio: 29.99 }));\nfs.writeFileSync('data/catalogo.json', JSON.stringify(catalogo, null, 2));",
        "cmd": "rm -f data/catalogo.json && npm run seed && head -n 12 data/catalogo.json"
    },
    {
        "id": "N1",
        "section": "Reglas de Negocio, Licencias e IDs",
        "title": "N1 · Modelado y Gestión de Licencias (Single Source of Truth)",
        "question": "Muestra el modelo de licencias. ¿Cómo se gestionan, quién es el dueño de esos datos, cómo nacen y cómo se relacionan con los juegos y usuarios?",
        "alarm": "Decir que las licencias se guardan dentro de Cognito o que el Catálogo administra quién compró los juegos.",
        "steps": [
            ("1", "Qué hice", "Modelé la entidad Licencia (licencia.model.ts) con id (UUID v4), juegoId, usuarioSub (claim sub), fechaAdquisicion, plataforma, tienda, region, codigoCanje (VS-XXXXXXXXXXXXXXXX), estadoPago y precioPagado. Biblioteca es el único dueño (Single Source of Truth), respaldado en MemoryStorageService y persistido en data/licencias.json."),
            ("2", "Qué problema resuelve", "Modela la relación N:M entre usuarios y juegos desacoplando la transacción comercial de la titularidad digital. Compras simula el pago y delega por HTTP interno a Biblioteca la creación de la licencia."),
            ("3", "Qué descarté", "Descarté guardar licencias embebidas en el usuario (los usuarios viven en AWS Cognito) y descarté que Catálogo guarde tenencia privada."),
            ("4", "Cómo lo compruebo", "En biblioteca.service.ts vemos crearLicencia(). Al consultar GET /v1/biblioteca, el BFF obtiene las licencias de ese usuarioSub, las enriquece con el catálogo y devuelve el inventario propio.")
        ],
        "code": "// vidalstore-backend/src/models/licencia.model.ts:L1-L13\nexport interface Licencia {\n  id: string;          // UUID v4 único\n  juegoId: string;     // ID foráneo del catálogo\n  usuarioSub: string;  // Claim sub inmutable de Cognito\n  fechaAdquisicion: string; // ISO 8601\n  codigoCanje?: string;     // Formato VS-XXXXXXXXXXXXXXXX\n  estadoPago?: 'aprobado' | 'rechazado';\n  precioPagado?: number;\n}",
        "cmd": None
    },
    {
        "id": "N2",
        "section": "Reglas de Negocio, Licencias e IDs",
        "title": "N2 · Identificador de Usuario (Por qué 'sub' UUID y NO email/username)",
        "question": "¿Por qué en las licencias guardas 'usuarioSub' en lugar del correo electrónico (email) o username? ¿Qué ganaron con esa decisión?",
        "alarm": "Creer que usar email es mejor 'porque es más legible', ignorando la mutabilidad del correo y la fuga de datos personales (PII).",
        "steps": [
            ("1", "Qué hice", "Utilicé como clave foránea única de usuario el claim sub (Subject) de Cognito (UUID v4 inmutable de 36 caracteres), extraído de req.user.sub tras verificar la firma RSA."),
            ("2", "Qué problema resuelve", "1) Inmutabilidad: El email puede cambiar en Cognito; el sub nunca cambia (evita perder compras). 2) Privacidad por Diseño (Zero PII Leakage / GDPR): El sub es un UUID opaco sin datos personales. 3) Desacoplamiento del IdP: La base de datos solo conoce UUIDs RFC 4122; si cambiamos Cognito por Keycloak, el modelo no cambia."),
            ("3", "Qué descarté", "Descarté usar email o username como claves primarias, y descarté inventar un ID numérico de usuario local que requeriría tablas de sincronización."),
            ("4", "Cómo lo compruebo", "Decodificando el JWT en jwt.io: sub contiene el UUID inmutable que coincide exactamente con los registros de licencias.json.")
        ],
        "code": "// vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L64-L66\nbuscarLicenciasPorUsuario(usuarioSub: string): Licencia[] {\n  return this.storageService.buscarLicenciasPorUsuarioSub(usuarioSub);\n}",
        "cmd": None
    },
    {
        "id": "N3",
        "section": "Reglas de Negocio, Licencias e IDs",
        "title": "N3 · Identificador de Licencia (Por qué UUID v4 y NO un autoincremental)",
        "question": "¿Por qué el ID de la licencia es un UUID (randomUUID()) y no un número secuencial simple como 1, 2, 3...?",
        "alarm": "«Es que NestJS me lo dio así», sin entender el impacto en sistemas distribuidos ni la seguridad contra enumeración de URLs.",
        "steps": [
            ("1", "Qué hice", "En biblioteca.service.ts y memory-storage.service.ts, cada nueva licencia recibe id: randomUUID(), generado con el módulo nativo criptográfico node:crypto."),
            ("2", "Qué problema resuelve", "1) Sistemas Distribuidos sin Cuello de Botella: En microservicios, los IDs autoincrementales exigen base de datos centralizada con bloqueos. UUID v4 se genera descentralizado en cualquier nodo con colisión despreciable (2^122). 2) Anti-Scraping y Confidencialidad: Si fueran 101, 102, un competidor deduciría el volumen diario de ventas y atacantes enumerarían URLs (/licencias/103)."),
            ("3", "Qué descarté", "Descarté secuencias numéricas (id: ++contador) y bibliotecas externas pesadas; usamos el generador criptográfico nativo de Node.js."),
            ("4", "Cómo lo compruebo", "Al generar dos compras vía /v1/compras, los IDs en licencias.json son hashes UUID v4 independientes de 36 caracteres.")
        ],
        "code": "// vidalstore-backend/src/storage/memory-storage.service.ts:L202-L206\nconst nuevaLicencia: Licencia = {\n  id: randomUUID(), // UUID v4 RFC 4122 (128 bits, sin colisión distribuida)\n  juegoId: datos.juegoId,\n  usuarioSub: datos.usuarioSub,\n  fechaAdquisicion: new Date().toISOString(),\n};",
        "cmd": None
    },
    {
        "id": "N4",
        "section": "Reglas de Negocio, Licencias e IDs",
        "title": "N4 · Convivencia de IDs (Catálogo FreeToGame '452' vs Licencias UUID)",
        "question": "Veo que en el catálogo los IDs son números como '452', pero las licencias son UUIDs. ¿Por qué esa diferencia y cómo conviven ambos?",
        "alarm": "No saber de dónde provienen los IDs de los juegos ni por qué se almacenan como cadenas en TypeScript.",
        "steps": [
            ("1", "Qué hice", "En catálogo tipamos id: string en TypeScript, con valores numéricos seriales provenientes del script seed.ts (FreeToGame API). En la licencia almacenamos juegoId: string como clave foránea que referencia ese ID de catálogo."),
            ("2", "Qué problema resuelve", "Separa datos del proveedor externo y transacciones internas: Catálogo refleja una API externa manteniendo su ID original para trazabilidad y resincronización. Licencia es un bien transaccional propio que requiere identificadores únicos globales (UUID v4). Tipar ambos como string desacopla esquemas y previene problemas de coerción de tipos."),
            ("3", "Qué descarté", "Descarté sobreescribir los IDs de FreeToGame con nuevos UUIDs en el seed, porque habríamos destruido el identificador oficial del juego."),
            ("4", "Cómo lo compruebo", "En catalogo.json vemos { 'id': '452', 'titulo': 'Warzone' } y en licencias.json vemos { 'id': 'uuid-v4...', 'juegoId': '452', 'usuarioSub': 'uuid-sub...' }.")
        ],
        "code": "// data/seed.ts vs models/licencia.model.ts:\nid: String(juegoExterno.id), // '452' (origen FreeToGame)\njuegoId: string,              // clave foránea tipada en Licencia",
        "cmd": None
    },
    {
        "id": "N5",
        "section": "Reglas de Negocio, Licencias e IDs",
        "title": "N5 · Unicidad e Idempotencia (HTTP 409 Conflict en Compras)",
        "question": "¿Qué regla de negocio impide que un usuario compre dos veces el mismo juego y cómo está implementada en el código?",
        "alarm": "Decir que con ocultar el botón en Angular basta, delegando la regla de negocio y la seguridad al cliente.",
        "steps": [
            ("1", "Qué hice", "En biblioteca.service.ts, crearLicencia() ejecuta primero buscarLicenciaPorUsuarioYJuego(usuarioSub, juegoId). Si existe, arroja ConflictException (HTTP 409 Conflict): 'El usuario ya posee una licencia activa para el juego con ID ...'."),
            ("2", "Qué problema resuelve", "Aplica la regla de comercialización digital: en software la posesión es unívoca (no compras 2 unidades). Previene cobros duplicados por doble clic, reintentos automáticos o llamadas directas maliciosas con curl."),
            ("3", "Qué descarté", "Descarté delegar la comprobación al frontend (en F12 cualquiera habilita el botón) y descarté responder 200 OK cobrando de nuevo o sobreescribiendo la fecha de compra original."),
            ("4", "Cómo lo compruebo", "Envío 2 peticiones POST /v1/compras con el mismo juegoId: la primera responde 201 Created y la segunda responde 409 Conflict.")
        ],
        "code": "// vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L49-L54\nconst licenciaExistente = this.buscarLicenciaPorUsuarioYJuego(usuarioSub, licenciaDatos.juegoId);\nif (licenciaExistente) {\n  throw new ConflictException(`El usuario ya posee una licencia activa para el juego con ID '${licenciaDatos.juegoId}'.`);\n}",
        "cmd": "curl -i -X POST http://localhost:8080/v1/compras -H \"Authorization: Bearer $TOKEN\" -H \"Content-Type: application/json\" -d '{\"juegoId\":\"1\"}' # 201 Created\ncurl -i -X POST http://localhost:8080/v1/compras -H \"Authorization: Bearer $TOKEN\" -H \"Content-Type: application/json\" -d '{\"juegoId\":\"1\"}' # 409 Conflict"
    },
    {
        "id": "N6",
        "section": "Reglas de Negocio, Licencias e IDs",
        "title": "N6 · Código de Canje (CD-Key con Criptografía Segura)",
        "question": "¿Para qué sirve el campo 'codigoCanje' en la licencia y con qué criterio se genera?",
        "alarm": "No saber para qué existe el código de canje o creer que es un simple adorno estético sin valor comercial.",
        "steps": [
            ("1", "Qué hice", "En biblioteca.service.ts, al crear la licencia se genera: codigoCanje: `VS-${randomUUID().replaceAll('-', '').slice(0, 16).toUpperCase()}`."),
            ("2", "Qué problema resuelve", "Separa la titularidad legal de la entrega digital de la credencial: la Licencia es el derecho en VidalStore; el Código de Canje (CD-Key) es la credencial alfanumérica única de 16 caracteres hexadecimales para canjear en Steam o Epic Games."),
            ("3", "Qué descarté", "Descarté generar códigos con Math.random() (pseudo-aleatorio predecible). randomUUID() garantiza entropía criptográfica segura de CSPRNG."),
            ("4", "Cómo lo compruebo", "Al inspeccionar una licencia devuelta en /v1/biblioteca, incluye el código de canje formateado con prefijo institucional: VS-E4A83C90D1F5B2E7.")
        ],
        "code": "// vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L59\ncodigoCanje: `VS-${randomUUID().replaceAll('-', '').slice(0, 16).toUpperCase()}`",
        "cmd": None
    }
]

# -------------------------------------------------------------
# BUILD WORD DOCUMENT
# -------------------------------------------------------------
def build_docx():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    COLOR_PRIMARY = RGBColor(27, 54, 93)     # Navy #1B365D
    COLOR_SECONDARY = RGBColor(46, 107, 158) # Steel Blue #2E6B9E
    COLOR_DARK = RGBColor(34, 34, 34)        # Charcoal
    COLOR_ALERT = RGBColor(192, 57, 43)      # Crimson #C0392B
    COLOR_SUCCESS = RGBColor(39, 174, 96)    # Emerald #27AE60

    def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m_name, m_val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{m_name}')
            node.set(qn('w:w'), str(m_val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    def set_cell_background(cell, hex_color):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.bold = True
        run.font.size = Pt(22)
        run.font.color.rgb = COLOR_PRIMARY

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(14)
        run = p.add_run(text)
        run.font.italic = True
        run.font.size = Pt(11)
        run.font.color.rgb = COLOR_SECONDARY

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = COLOR_PRIMARY

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.bold = True
        run.font.size = Pt(11.5)
        run.font.color.rgb = COLOR_SECONDARY

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_DARK

    def add_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.bold = True
            r_pre.font.size = Pt(9.5)
            r_pre.font.color.rgb = COLOR_DARK
        run = p.add_run(text)
        run.font.size = Pt(9.5)
        run.font.color.rgb = COLOR_DARK
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.bold = True
            r_pre.font.size = Pt(9.5)
            r_pre.font.color.rgb = COLOR_DARK
        run = p.add_run(text)
        run.font.size = Pt(9.5)
        run.font.color.rgb = COLOR_DARK

    def add_dialogue_docx(item):
        add_heading_3(f"Parada de Defensa: {item['title']}")
        
        # Question box
        tbl_q = doc.add_table(rows=1, cols=1)
        tbl_q.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell_q = tbl_q.cell(0, 0)
        set_cell_margins(cell_q, top=100, bottom=100, left=160, right=160)
        set_cell_background(cell_q, "EBF5FB")
        b_q = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:left w:val="single" w:sz="24" w:space="0" w:color="2980B9"/></w:tcBorders>')
        cell_q._tc.get_or_add_tcPr().append(b_q)
        pq = cell_q.paragraphs[0]
        rq_label = pq.add_run("Pregunta Oficial del Docente (Cristian Calderón):\n")
        rq_label.font.bold = True
        rq_label.font.size = Pt(9.5)
        rq_label.font.color.rgb = RGBColor(41, 128, 185)
        rq = pq.add_run(f'«{item["question"]}»')
        rq.font.italic = True
        rq.font.size = Pt(10)
        rq.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

        # Alarm box
        if item.get("alarm"):
            tbl_w = doc.add_table(rows=1, cols=1)
            tbl_w.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell_w = tbl_w.cell(0, 0)
            set_cell_margins(cell_w, top=80, bottom=80, left=140, right=140)
            set_cell_background(cell_w, "FDEDEC")
            b_w = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:left w:val="single" w:sz="24" w:space="0" w:color="C0392B"/></w:tcBorders>')
            cell_w._tc.get_or_add_tcPr().append(b_w)
            pw = cell_w.paragraphs[0]
            rw_label = pw.add_run("⚠ SEÑAL DE ALARMA DE D6 (Lo que NUNCA debes decir):\n")
            rw_label.font.bold = True
            rw_label.font.size = Pt(9)
            rw_label.font.color.rgb = COLOR_ALERT
            rw = pw.add_run(item["alarm"])
            rw.font.size = Pt(9)
            rw.font.color.rgb = COLOR_DARK
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

        # Answer 4 steps box
        tbl_a = doc.add_table(rows=1, cols=1)
        tbl_a.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell_a = tbl_a.cell(0, 0)
        set_cell_margins(cell_a, top=100, bottom=100, left=160, right=160)
        set_cell_background(cell_a, "F9FBF9")
        b_a = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:left w:val="single" w:sz="24" w:space="0" w:color="27AE60"/></w:tcBorders>')
        cell_a._tc.get_or_add_tcPr().append(b_a)
        pa = cell_a.paragraphs[0]
        ra_label = pa.add_run("Respuesta Técnica Modelo (Framework de 4 Pasos de D6):\n")
        ra_label.font.bold = True
        ra_label.font.size = Pt(9.5)
        ra_label.font.color.rgb = COLOR_SUCCESS

        for step_num, step_title, step_content in item["steps"]:
            r_step = pa.add_run(f"\n{step_num}. {step_title}: ")
            r_step.font.bold = True
            r_step.font.size = Pt(9.5)
            r_step.font.color.rgb = COLOR_PRIMARY
            r_c = pa.add_run(step_content)
            r_c.font.size = Pt(9.5)
            r_c.font.color.rgb = COLOR_DARK

        if item.get("code"):
            r_c_lbl = pa.add_run("\n\nExtracto de Código Clave:\n")
            r_c_lbl.font.bold = True
            r_c_lbl.font.size = Pt(9)
            r_c_lbl.font.color.rgb = RGBColor(41, 128, 185)
            r_code = pa.add_run(item["code"] + "\n")
            r_code.font.name = "Courier New"
            r_code.font.size = Pt(8.5)
            r_code.font.color.rgb = RGBColor(44, 62, 80)

        if item.get("cmd"):
            r_cmd_lbl = pa.add_run("\nComando de Prueba en Vivo (Terminal):\n")
            r_cmd_lbl.font.bold = True
            r_cmd_lbl.font.size = Pt(9)
            r_cmd_lbl.font.color.rgb = RGBColor(211, 84, 0)
            r_cmd = pa.add_run(f"$ {item['cmd']}\n")
            r_cmd.font.name = "Courier New"
            r_cmd.font.size = Pt(8.5)
            r_cmd.font.color.rgb = RGBColor(34, 34, 34)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Document Header
    add_title("GUÍA MAESTRA DE DEFENSA TÉCNICA · EP1")
    add_subtitle("Caso VidalStore · DSY1107 Desarrollo Cloud Native I · DUOC UC (2026-02)\nBasado en Clase D6, Pulso.pdf y Resoluciones del Profesor Cristian Calderón")

    # Section 1
    add_heading_1("1. Reglas de Oro y Contexto D6")
    add_bullet("La nota es personal: el repositorio grupal vale 40% y la defensa oral individual vale 60%. Puedes reprobar con código perfecto si no defiendes tu arquitectura.", "Ponderación Real: ")
    add_bullet("El docente no busca que memorices código; busca que demuestres autoría real, criterio de ingeniería y dominio absoluto de los flujos de red.", "Objetivo Docente: ")
    add_bullet("El docente corta a los 60 segundos si te vas por las ramas o recitas definiciones teóricas abstractas. Debes abrir el archivo en pantalla e ir al grano.", "Regla del Reloj: ")

    # Section 2
    add_heading_1("2. El Tablero de Control: 5 Ventanas Listas")
    add_bullet("Angular (4200), Gateway (8080), BFF (3001), Catálogo (3002), Biblioteca (3003), Compras (3004), Logs (3005).", "1. Terminal con Procesos: ")
    add_bullet("http://localhost:4200 con sesión iniciada y pestaña Red limpia en Fetch/XHR.", "2. Navegador Web: ")
    add_bullet("Variables $TOKEN_JUGADOR y $TOKEN_ADMIN listas para curl.", "3. Cliente REST / Terminal: ")
    add_bullet("Archivos token.interceptor.ts, gateway.controller.ts, bff-biblioteca.controller.ts, seed.ts ya abiertos.", "4. Editor VS Code: ")
    add_bullet("User Pool abierto con usuarios, grupos y los 2 App Clients (lo único en la nube).", "5. Consola AWS Cognito: ")

    # Section 3
    add_heading_1("3. Arquitectura de 4 Capas y Delimitación Cloud vs Local")
    add_p("Flujo de arriba a abajo: Navegador (Angular 4200) → API Gateway (8080) → BFF (3001) → Microservicios (3002..3005).")
    add_p("Delimitación Cloud vs Local: En AWS reside EXCLUSIVAMENTE el User Pool de Cognito (usuarios, grupos, scopes, JWKS). Todo el resto del software corre 100% en la máquina local.")

    # Section 4
    add_heading_1("4. El Reloj de los 15 Minutos y Metodología")
    add_bullet("0 a 1 min: Declaración de procesos y puertos corriendo.", "Minuto 0..1: ")
    add_bullet("1 a 7 min: Flujo A (Identidad) y Flujo B (Lo Propio) alternando integrantes.", "Minuto 1..7: ")
    add_bullet("7 a 12 min: Flujos C (Rol insuficiente), D (Por detrás / CORS) y E (Seed).", "Minuto 7..12: ")
    add_bullet("12 a 14 min: Modificación Señalada sobre código de otro integrante.", "Minuto 12..14: ")
    add_bullet("14 a 15 min: Pregunta técnica sobre el botón COMPRAR.", "Minuto 14..15: ")

    # Section 5
    add_heading_1("5. El Framework de Respuesta en 4 Pasos de D6")
    add_bullet("Nombrar el componente, clase o función exacta en el código y abrir el archivo.", "1. Qué hice → ")
    add_bullet("Explicar la necesidad concreta de seguridad, rendimiento, concurrencia o arquitectura.", "2. Qué problema resuelve → ")
    add_bullet("Nombrar explícitamente la alternativa técnica rechazada y por qué no servía (es el paso que más nota otorga).", "3. Qué descarté → ")
    add_bullet("Demostrarlo empíricamente en vivo en la pantalla (pestaña Red, curl, terminal).", "4. Cómo lo compruebo → ")

    # Section 6: Official Dialogues
    add_heading_1("6. Guion Oficial de la Defensa · Parada por Parada (D6)")
    for item in DIALOGUES[:10]:
        add_dialogue_docx(item)

    # Section 7: Business Rules & IDs
    add_heading_1("7. Reglas de Negocio, Gestión de Licencias e Identificadores (UUID vs Sub vs Integer)")
    add_p("El docente Cristian Calderón evalúa el dominio del modelo de datos y las reglas comerciales que sustentan la arquitectura:")
    for item in DIALOGUES[10:]:
        add_dialogue_docx(item)

    # Section 8: Modificación Señalada
    add_heading_1("8. La Modificación Señalada (Minutos 12 a 14)")
    add_p("El docente pide una modificación puntual sobre código ajeno. No se programa en vivo: se ubica la línea y se explica el impacto:")
    add_bullet("En bff-licencias.controller.ts agregar @RequireGroups('administradores') y en gateway.controller.ts mapear la ruta proxy. Comprobación: curl con token de jugador da 403.", "Caso 1: Ruta exclusiva para administradores → ")
    add_bullet("En src/app/auth/token.interceptor.ts comentar setHeaders['Authorization']. Comprobación: Angular compila bien pero las llamadas salen limpias y el Gateway corta con 401 Unauthorized.", "Caso 2: Borrar cabecera Authorization en Angular → ")
    add_bullet("En vidalstore-gateway/.env cambiar COGNITO_CLIENT_ID por el del App Client 2. Comprobación: Las llamadas de la SPA validan la firma pero fallan en payload.client_id !== expected con 401.", "Caso 3: Configurar client_id equivocado en Gateway → ")
    add_bullet("En bff-biblioteca.controller.ts quitar la llamada a catálogo del Promise.all. Comprobación: La biblioteca responde licencias pero juego: null; la vista queda sin portadas ni nombres.", "Caso 4: Quitar microservicio del Promise.all en BFF → ")

    # Section 9: Pregunta Botón COMPRAR
    add_heading_1("9. La Pregunta del Botón COMPRAR (Minutos 14 a 15)")
    add_p("Pregunta del Docente: «Si el usuario ya posee la licencia de un juego, ¿qué debe hacer el botón COMPRAR en la interfaz? ¿Ocultarse, deshabilitarse, o permitir el clic y que el servidor responda con error?»")
    add_bullet("Deshabilitar el botón o cambiarlo a 'Ya adquirido' / 'Jugar'. Mejora la experiencia y ahorra tráfico.", "1. En la Interfaz (UX): ")
    add_bullet("La seguridad y las reglas de negocio NUNCA se delegan al cliente (F12 o curl pueden enviar peticiones). El microservicio de biblioteca es estrictamente IDEMPOTENTE: en biblioteca.service.ts comprueba la tupla (usuarioSub, juegoId) y responde ConflictException (HTTP 409 Conflict).", "2. En el Backend (Mandatorio): ")
    add_bullet("«En la UI lo deshabilito por experiencia de usuario, pero el backend siempre valida idempotencia y responde 409 Conflict si la llamada llega.»", "Conclusión de Oro: ")

    # Section 10: Pulso & Extensibilidad
    add_heading_1("10. Preguntas Transversales y Resumen de Pulso.pdf (§12.2)")
    add_bullet("Solo se tocan dos capas del backend: en el BFF se agrega la llamada interna y se mapea en el Promise.all; y en el Gateway se crea la ruta proxy si se requiere exponer un endpoint público /v1/... En Angular NO se toca ninguna URL: el frontend solo conoce http://localhost:8080.", "Si entra un 5to microservicio, ¿qué se toca? → ")
    add_bullet("El BFF captura el error de conexión y responde 503 Service Unavailable indicando qué servicio falló. Cuando el microservicio se restablece, el sistema vuelve a responder 200 OK inmediatamente sin reiniciar Gateway ni BFF.", "¿Qué pasa si un microservicio interno se cae? → ")
    add_bullet("Una sola llamada HTTP en lugar de múltiples peticiones; concurrencia en servidor mediante Promise.all (con 300 ms de latencia por servicio, en serie serían 600 ms y en paralelo son ~300 ms); cruce de datos en memoria O(N) con Map por ID; y cero fuga de datos internos hacia F12.", "¿Qué gana el frontend con el BFF? (Números medidos) → ")

    # Section 11: Bitácora de Errores
    add_heading_1("11. Bitácora de Errores Reales del Proyecto (D6 \"Qué Descarté\")")
    add_bullet("Al crear el App Client en Cognito le pusimos client_secret para Angular. Amplify no podía autenticar porque las SPAs públicas no pueden almacenar secretos. Tuvimos que recrear el App Client sin secreto.", "1. Error de Secreto en SPA: ")
    add_bullet("Estábamos probando un endpoint con curl y de repente dio 401. El token de Cognito había cumplido sus 60 minutos de vigencia (exp). Tuvimos que volver a iniciar sesión.", "2. Error de Token Expirado: ")
    add_bullet("Al registrarnos con un usuario nuevo en la Hosted UI, no podíamos ver el catálogo (403). Cognito no asigna grupos por omisión; lo resolvimos con el fallback seguro a 'jugadores' en el guard.", "3. Error de la Trampa de Cognito: ")
    add_bullet("Intentamos poner CORS en el BFF. Nos dimos cuenta de que CORS es exclusivo de navegadores web y que las llamadas internas entre Node.js son backend-to-backend, por lo que CORS solo debe vivir en el Gateway.", "4. Error de CORS en Backend: ")
    add_bullet("En Angular interceptábamos todas las URLs sin filtro, enviando el token Bearer a Google Fonts y CDNs externos. Lo solucionamos con la whitelist estricta que solo inyecta el token si la URL comienza con environment.apiUrl (http://localhost:8080).", "5. Error de Whitelist en Interceptor: ")

    doc.save(DOCX_PATH)
    print(f"Word document saved at: {DOCX_PATH}")


# -------------------------------------------------------------
# BUILD PDF DOCUMENT
# -------------------------------------------------------------
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
        
        if self._pageNumber > 1:
            self.drawString(54, 750, "DSY1107 · Desarrollo Cloud Native I | Caso VidalStore EP1 · Preparación D6")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

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
    c_primary = colors.HexColor("#1B365D")
    c_secondary = colors.HexColor("#2E6B9E")
    c_dark = colors.HexColor("#222222")
    c_alert = colors.HexColor("#C0392B")
    c_success = colors.HexColor("#27AE60")

    title_style = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=c_primary, alignment=1, spaceAfter=3)
    subtitle_style = ParagraphStyle('DocSubTitle', fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=c_secondary, alignment=1, spaceAfter=10)
    h1_style = ParagraphStyle('Heading1_Custom', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=c_primary, spaceBefore=8, spaceAfter=3, keepWithNext=True)
    h2_style = ParagraphStyle('Heading2_Custom', fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=c_secondary, spaceBefore=6, spaceAfter=2, keepWithNext=True)
    body_style = ParagraphStyle('Body_Custom', fontName='Helvetica', fontSize=8.5, leading=11.5, textColor=c_dark, spaceAfter=2)
    bullet_style = ParagraphStyle('Bullet_Custom', fontName='Helvetica', fontSize=8.5, leading=11.5, textColor=c_dark, leftIndent=12, firstLineIndent=-8, spaceAfter=2)
    q_label_style = ParagraphStyle('QLabel', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor("#1A5276"))
    q_text_style = ParagraphStyle('QText', fontName='Helvetica-Oblique', fontSize=8.5, leading=11.5, textColor=c_dark)
    w_label_style = ParagraphStyle('WLabel', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_alert)
    w_text_style = ParagraphStyle('WText', fontName='Helvetica', fontSize=8, leading=10.5, textColor=colors.HexColor("#78281F"))
    a_label_style = ParagraphStyle('ALabel', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_success)
    a_step_style = ParagraphStyle('AStep', fontName='Helvetica', fontSize=8, leading=11, textColor=c_dark, leftIndent=8, firstLineIndent=-6, spaceAfter=1)
    code_lbl_style = ParagraphStyle('CodeLbl', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor("#1A5276"))
    cmd_lbl_style = ParagraphStyle('CmdLbl', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor("#B9770E"))

    def add_pdf_dialogue(item):
        content = []
        content.append(Paragraph(f"<b>{item['title']}</b>", h2_style))
        
        # Question box
        q_p = [Paragraph("<b>Pregunta del Docente (Cristian Calderón):</b>", q_label_style),
               Paragraph(f'«{item["question"]}»', q_text_style)]
        tbl_q = Table([[q_p]], colWidths=[504])
        tbl_q.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF5FB")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#2980B9")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        content.append(tbl_q)
        content.append(Spacer(1, 2))

        # Alarm box
        if item.get("alarm"):
            w_p = [Paragraph("<b>⚠ SEÑAL DE ALARMA DE D6 (Lo que NUNCA debes responder):</b>", w_label_style),
                   Paragraph(item["alarm"], w_text_style)]
            tbl_w = Table([[w_p]], colWidths=[504])
            tbl_w.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDEDEC")),
                ('BOX', (0,0), (-1,-1), 0.5, c_alert),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            content.append(tbl_w)
            content.append(Spacer(1, 2))

        # Answer 4 steps box
        a_p = [Paragraph("<b>Respuesta Técnica Modelo (Framework de 4 Pasos):</b>", a_label_style)]
        for s_num, s_title, s_desc in item["steps"]:
            a_p.append(Paragraph(f"<b>{s_num}. {s_title}:</b> {s_desc}", a_step_style))

        # Code snippet block
        if item.get("code"):
            a_p.append(Spacer(1, 3))
            a_p.append(Paragraph("<b>Extracto de Código Clave:</b>", code_lbl_style))
            clean_code = item["code"].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>&nbsp;&nbsp;')
            code_p = Paragraph(f"<font name='Courier' size=7 color='#1C2833'>{clean_code}</font>", body_style)
            tbl_code = Table([[code_p]], colWidths=[488])
            tbl_code.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EAEDED")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ]))
            a_p.append(tbl_code)

        # Test command block
        if item.get("cmd"):
            a_p.append(Spacer(1, 2))
            a_p.append(Paragraph("<b>Comando de Prueba en Vivo (Terminal):</b>", cmd_lbl_style))
            clean_cmd = item["cmd"].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>&nbsp;&nbsp;')
            cmd_p = Paragraph(f"<font name='Courier-Bold' size=7 color='#784212'>$ {clean_cmd}</font>", body_style)
            tbl_cmd = Table([[cmd_p]], colWidths=[488])
            tbl_cmd.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF5E7")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#EDBB99")),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ]))
            a_p.append(tbl_cmd)

        tbl_a = Table([[a_p]], colWidths=[504])
        tbl_a.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBF9")),
            ('BOX', (0,0), (-1,-1), 0.5, c_success),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        content.append(tbl_a)
        content.append(Spacer(1, 6))
        return [KeepTogether(content)]

    story = []

    # PAGE 1: Portada, Reglas, Reloj, 5 Ventanas
    story.append(Paragraph("GUÍA MAESTRA DE DEFENSA TÉCNICA · EP1", title_style))
    story.append(Paragraph("Caso VidalStore · DSY1107 Desarrollo Cloud Native I · DUOC UC (2026-02)<br/>Basado en Clase Magistral D6, Pulso.pdf y Resoluciones del Profesor Cristian Calderón", subtitle_style))

    story.append(Paragraph("1. Reglas de Oro y Contexto D6", h1_style))
    story.append(Paragraph("• <b>Ponderación Real:</b> El código grupal en el repositorio vale el 40% y la defensa individual oral vale el 60%. Un estudiante puede reprobar con código perfecto si no demuestra dominio técnico.", bullet_style))
    story.append(Paragraph("• <b>Objetivo de Evaluación:</b> El docente no evalúa memorizar sintaxis; busca comprobar autoría técnica, criterio de diseño y dominio de los flujos de punta a punta.", bullet_style))
    story.append(Paragraph("• <b>La Regla del Reloj:</b> El docente corta a los 60 segundos si la respuesta es abstracta. Abre el archivo en el editor y responde con el framework de 4 pasos.", bullet_style))

    story.append(Paragraph("2. El Tablero de Control: 5 Ventanas Listas", h1_style))
    data_ventanas = [
        [Paragraph("<b>Ventana Obligatoria</b>", q_label_style), Paragraph("<b>Estado Esperado y Puertos Activos</b>", q_label_style)],
        [Paragraph("<b>1. Terminal:</b>", body_style), Paragraph("Procesos activos: Angular (4200), Gateway (8080), BFF (3001), Catálogo (3002), Biblioteca (3003), Compras (3004), Logs (3005).", body_style)],
        [Paragraph("<b>2. Navegador:</b>", body_style), Paragraph("http://localhost:4200 con sesión iniciada, pestaña Red limpia en Fetch/XHR lista para inspeccionar una sola llamada a 8080.", body_style)],
        [Paragraph("<b>3. Cliente REST / Terminal:</b>", body_style), Paragraph("Dos tokens listos en variables ($TOKEN_JUGADOR y $TOKEN_ADMIN) para probar 403 vs 200 al instante.", body_style)],
        [Paragraph("<b>4. Editor VS Code:</b>", body_style), Paragraph("Pestañas abiertas: token.interceptor.ts, gateway.controller.ts, bff-biblioteca.controller.ts, seed.ts, biblioteca.service.ts.", body_style)],
        [Paragraph("<b>5. Consola AWS Cognito:</b>", body_style), Paragraph("User Pool abierto mostrando usuarios, grupos (jugadores, administradores) y los 2 App Clients (con y sin secreto).", body_style)],
    ]
    tbl_v = Table(data_ventanas, colWidths=[130, 374])
    tbl_v.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1B365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7E9")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tbl_v)

    story.append(PageBreak())

    # PAGE 2: Arquitectura, Extensibilidad, 4 Pasos
    story.append(Paragraph("3. Arquitectura de 4 Capas y Flujo Secuencial", h1_style))
    story.append(Paragraph("<b>Flujo Top-to-Bottom:</b> 1) Navegador (Angular :4200) → 2) API Gateway (:8080) → 3) BFF (:3001) → 4) Microservicios internos (:3002..:3005).", body_style))
    story.append(Paragraph("<b>Delimitación Cloud vs Local:</b> En AWS reside EXCLUSIVAMENTE el User Pool de Cognito (usuarios, grupos, scopes, JWKS). Todo el resto del sistema corre 100% en la máquina local.", body_style))

    story.append(Paragraph("4. Principio de Extensibilidad (El 5to Microservicio)", h1_style))
    story.append(Paragraph("• <b>¿Qué se toca?:</b> Solo se tocan dos capas del backend: en el BFF se agrega la llamada interna y se mapea en el Promise.all; y en el Gateway se crea la ruta proxy si se requiere exponer un endpoint público /v1/... En Angular NO se toca ninguna URL: el frontend solo conoce http://localhost:8080.", bullet_style))

    story.append(Paragraph("5. El Framework de Respuesta en 4 Pasos de D6", h1_style))
    story.append(Paragraph("• <b>1. Qué hice:</b> Nombrar el componente, clase o línea exacta de tu código y abrirla en el editor.", bullet_style))
    story.append(Paragraph("• <b>2. Qué problema resuelve:</b> Describir la necesidad técnica de seguridad, rendimiento, concurrencia o arquitectura.", bullet_style))
    story.append(Paragraph("• <b>3. Qué descarté:</b> Nombrar la alternativa técnica rechazada y por qué no servía (el paso que más nota otorga).", bullet_style))
    story.append(Paragraph("• <b>4. Cómo lo compruebo:</b> Demostrarlo empíricamente en vivo en la pantalla (pestaña Red, curl, terminal).", bullet_style))

    story.append(PageBreak())

    # SECTION 6: DIALOGUES A1 & A2 (PAGE 3)
    story.append(Paragraph("6. Guion Oficial de la Defensa · Parada por Parada (D6)", h1_style))
    story.extend(add_pdf_dialogue(DIALOGUES[0])) # A1
    story.extend(add_pdf_dialogue(DIALOGUES[1])) # A2

    story.append(PageBreak())

    # DIALOGUES B1 & B2 (PAGE 4)
    story.extend(add_pdf_dialogue(DIALOGUES[2])) # B1
    story.extend(add_pdf_dialogue(DIALOGUES[3])) # B2

    story.append(PageBreak())

    # DIALOGUES B3 & B4 (PAGE 5)
    story.extend(add_pdf_dialogue(DIALOGUES[4])) # B3
    story.extend(add_pdf_dialogue(DIALOGUES[5])) # B4

    story.append(PageBreak())

    # DIALOGUES C1 & D1 (PAGE 6)
    story.extend(add_pdf_dialogue(DIALOGUES[6])) # C1
    story.extend(add_pdf_dialogue(DIALOGUES[7])) # D1

    story.append(PageBreak())

    # DIALOGUES D2 & D3 (PAGE 7)
    story.extend(add_pdf_dialogue(DIALOGUES[8])) # D2
    story.extend(add_pdf_dialogue(DIALOGUES[9])) # D3

    story.append(PageBreak())

    # DIALOGUES E1 & SECTION 7: N1 (PAGE 8)
    story.extend(add_pdf_dialogue(DIALOGUES[10])) # E1
    story.append(Paragraph("7. Reglas de Negocio, Gestión de Licencias e Identificadores", h1_style))
    story.append(Paragraph("El docente Cristian Calderón evalúa el modelo de datos y las reglas comerciales que sustentan la arquitectura:", body_style))
    story.extend(add_pdf_dialogue(DIALOGUES[11])) # N1

    story.append(PageBreak())

    # DIALOGUES N2 & N3 (PAGE 9)
    story.extend(add_pdf_dialogue(DIALOGUES[12])) # N2
    story.extend(add_pdf_dialogue(DIALOGUES[13])) # N3

    story.append(PageBreak())

    # DIALOGUES N4 & N5 (PAGE 10)
    story.extend(add_pdf_dialogue(DIALOGUES[14])) # N4
    story.extend(add_pdf_dialogue(DIALOGUES[15])) # N5

    story.append(PageBreak())

    # DIALOGUES N6 & SECTIONS 8 & 9 (PAGE 11)
    story.extend(add_pdf_dialogue(DIALOGUES[16])) # N6
    story.append(Paragraph("8. La Modificación Señalada (Minutos 12 a 14)", h1_style))
    story.append(Paragraph("• <b>Caso 1 (Ruta Admin):</b> En bff-licencias.controller.ts agregar @RequireGroups('administradores'). En Gateway mapear ruta proxy. curl con jugador da 403.", bullet_style))
    story.append(Paragraph("• <b>Caso 2 (Borrar Token en Angular):</b> En token.interceptor.ts comentar setHeaders['Authorization']. Las peticiones salen limpias y Gateway corta con 401.", bullet_style))
    story.append(Paragraph("• <b>Caso 3 (Client ID Equivocado):</b> En Gateway cambiar COGNITO_CLIENT_ID por el del App Client 2. Valida firma pero falla en client_id !== expected con 401.", bullet_style))
    story.append(Paragraph("• <b>Caso 4 (Quitar Microservicio en BFF):</b> En bff-biblioteca.controller.ts quitar llamada a catálogo del Promise.all. Devuelve licencias pero juego: null.", bullet_style))

    story.append(Paragraph("9. La Pregunta del Botón COMPRAR (Minutos 14 a 15)", h1_style))
    story.append(Paragraph("• <b>Conclusión de Oro:</b> <i>«En la UI lo deshabilito por experiencia de usuario, pero el backend siempre valida la idempotencia en biblioteca.service.ts y responde 409 Conflict si la llamada llega.»</i>", body_style))

    story.append(PageBreak())

    # PAGE 12: Section 10, Section 11 & Final Checklist
    story.append(Paragraph("10. Preguntas Transversales y Resumen de Pulso.pdf (§12.2)", h1_style))
    story.append(Paragraph("• <b>Si entra un 5to microservicio:</b> Solo se tocan BFF y Gateway; en Angular NO se toca ninguna URL.", bullet_style))
    story.append(Paragraph("• <b>Si un microservicio se cae:</b> El BFF responde 503; cuando se restablece vuelve a 200 sin reiniciar Gateway ni BFF.", bullet_style))
    story.append(Paragraph("• <b>Métricas del BFF:</b> 1 sola llamada; concurrencia Promise.all (~300 ms vs 600 ms en serie); cruce O(N) con Map; cero fuga de datos hacia F12.", bullet_style))

    story.append(Paragraph("11. Bitácora de Errores Reales del Proyecto (D6 \"Qué Descarté\")", h1_style))
    story.append(Paragraph("1. <b>Error de Secreto en SPA:</b> App Client con secreto en Angular → Amplify fallaba → recreado sin secreto.", bullet_style))
    story.append(Paragraph("2. <b>Error de Token Expirado:</b> Token cumplió sus 60 min de vigencia (exp) → 401 Unauthorized en curl.", bullet_style))
    story.append(Paragraph("3. <b>Error de Trampa de Cognito:</b> Auto-registro deja grupos vacío → fallback seguro a 'jugadores' en el guard.", bullet_style))
    story.append(Paragraph("4. <b>Error de CORS en Backend:</b> Intentar poner CORS en BFF → CORS solo aplica a navegadores en el Gateway.", bullet_style))
    story.append(Paragraph("5. <b>Error de Whitelist en Interceptor:</b> Token enviado a Google Fonts → whitelist estricta req.url.startsWith(8080).", bullet_style))

    story.append(Spacer(1, 4))
    chk_title = Paragraph("<b>Checklist de los 60 Segundos Finales Antes de Entrar a la Sala</b>", h2_style)
    chk_items = [
        [chk_title, ""],
        [Paragraph("<b>1. Procesos y Puertos:</b>", q_label_style), Paragraph("Angular (4200), Gateway (8080), BFF (3001), Catálogo (3002), Biblioteca (3003), Compras (3004), Logs (3005) corriendo.", body_style)],
        [Paragraph("<b>2. Navegador:</b>", q_label_style), Paragraph("http://localhost:4200 con sesión iniciada, pestaña Red limpia en Fetch/XHR lista para inspeccionar una sola llamada a 8080.", body_style)],
        [Paragraph("<b>3. Terminal / curl:</b>", q_label_style), Paragraph("Dos tokens listos en variables de entorno ($TOKEN_JUGADOR y $TOKEN_ADMIN) para probar 403 vs 200 al instante.", body_style)],
        [Paragraph("<b>4. Editor VS Code:</b>", q_label_style), Paragraph("Pestañas abiertas: token.interceptor.ts, gateway.controller.ts, bff-biblioteca.controller.ts, seed.ts, biblioteca.service.ts.", body_style)],
        [Paragraph("<b>5. Consola AWS Cognito:</b>", q_label_style), Paragraph("User Pool abierto mostrando usuarios, grupos (jugadores, administradores) y los 2 App Clients (con y sin secreto).", body_style)],
    ]
    tbl_chk = Table(chk_items, colWidths=[110, 394])
    tbl_chk.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#EAEDED")),
        ('BACKGROUND', (0, 1), (1, -1), colors.HexColor("#F9FBFD")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1B365D")),
        ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl_chk)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {PDF_PATH}")

if __name__ == "__main__":
    print("Building Word document...")
    build_docx()
    print("Building PDF document...")
    build_pdf()
    print("Building Interactive HTML document...")
    try:
        from build_html import generate_html
        generate_html()
    except Exception as e:
        print(f"Error generating HTML: {e}")

