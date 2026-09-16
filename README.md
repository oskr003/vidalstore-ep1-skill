# 🎮 VidalStore EP1 — Skill de Auditoría y Cumplimiento al 100%
### DSY1107 · Desarrollo Cloud Native I · DUOC UC (2026-02)

[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Skill-4285F4?logo=google&logoColor=white)](https://github.com)
[![Evaluation](https://img.shields.io/badge/Evaluaci%C3%B3n-EP1%20VidalStore-blueviolet)](#)
[![Profesor](https://img.shields.io/badge/Docente-Cristian%20Calder%C3%B3n%20%28Umbingelelo%29-orange)](#)
[![Rúbrica](https://img.shields.io/badge/R%C3%BAbrica-IE1%20a%20IE10%20(100%25)-success)](#)

Esta skill es una **suite de auditoría técnica, control de calidad y preparación para la defensa individual** de la Evaluación Parcial N°1 (**Caso VidalStore**).

Fue diseñada para garantizar el **cumplimiento estricto al pie de la letra** de todas las fuentes oficiales de evaluación:
1. 📄 **`EP1-aclaraciones.pdf`**: Documento normativo oficial que rige sobre el enunciado.
2. 📄 **`EP1-Caso-VidalStore.pdf`**: Enunciado de negocio, arquitectura y rúbrica oficial (Indicadores IE1 a IE10).
3. 💬 **Foro oficial de GitHub (`Umbingelelo/DSY1107-Foro-2026-02`)**: Respuestas y aclaraciones directas del profesor Cristian Calderón.
4. 📋 **Plan de Trabajo del Proyecto**: Flujos de ramas, responsabilidades y ruta de auditoría para grupos de 3 personas.

---

## 🎯 ¿Qué hace esta Skill?

Cuando integras esta skill en tu agente (o ejecutas sus herramientas en tu terminal), la skill:

1. **Audita el Código Automáticamente**: Verifica si el frontend, gateway y microservicios cumplen con los estándares de la rúbrica y detecta fallas críticas antes de la entrega.
2. **Garantiza la Seguridad y Tokens**: Valida que el token de Cognito se guarde en `sessionStorage`, que el login use Hosted UI con PKCE (`signInWithRedirect`) y que el Gateway verifique la firma contra el JWKS.
3. **Controla las 4 Capas Arquitectónicas**: Comprueba la separación estricta entre Angular, API Gateway (puerto 8080 con CORS), BFF y Microservicios.
4. **Verifica las Rutas y Permisos**: Audita los 7 endpoints del punto 4.3 (y el 8vo de auditoría), asegurando la distinción entre Scopes (aplicación) y Grupos (roles).
5. **Entrena para la Defensa Individual (60% de la nota)**: Provee un banco de 10 preguntas y respuestas modelo fundamentadas sobre las decisiones arquitectónicas del encargo.

---

## 📂 Contenido del Repositorio

```text
vidalstore-ep1-skill/
├── SKILL.md                          # Directiva principal para agentes de IA (Antigravity, etc.)
├── README.md                         # Esta documentación para humanos
├── scripts/
│   └── audit_ep1.py                  # Script ejecutable de diagnóstico automático en terminal
└── references/
    ├── rubrica_completa.md           # Rúbrica desglosada (IE1 a IE10) y causas de nota mínima
    ├── arquitectura_4_capas.md       # Diagrama de las 4 capas, responsabilidades y códigos HTTP
    ├── rutas_y_permisos.md           # Matriz detallada de endpoints, métodos y claims
    ├── cognito_y_seguridad.md        # User pool, grupos, App Clients, Lambda trigger y sessionStorage
    └── preguntas_defensa.md          # 10 preguntas y respuestas modelo para la defensa técnica
```

---

## 🚀 Cómo Instalar y Usar esta Skill

### Opción A: En Google Antigravity (Recomendado)

#### 1. Instalación a nivel de Proyecto (Workspace)
Copia la carpeta de la skill dentro de tu proyecto en la ruta `.agents/skills/`:
```bash
mkdir -p .agents/skills/vidalstore-ep1
# Copia los archivos del repositorio en esa carpeta
```
Antigravity detectará automáticamente la skill en el workspace. A partir de ese momento, puedes pedirle cosas como:
* *"Audita mi proyecto con la skill de VidalStore y dime qué me falta para tener el 100%."*
* *"Revisa si mi API Gateway cumple con la validación de tokens contra el JWKS."*
* *"Hazme un simulacro de preguntas para la defensa individual de la EP1."*

#### 2. Instalación Global en tu Máquina
Si prefieres tenerla disponible en cualquier proyecto o terminal:
```bash
mkdir -p ~/.gemini/config/skills/vidalstore-ep1
# Copiar el contenido del repositorio allí
```

---

### Opción B: Ejecución del Script de Diagnóstico en Terminal

Puedes ejecutar el script de auditoría en cualquier momento sin necesidad de IA. Solo colócalo en la raíz donde conviven tus repositorios (`vidalstore-frontend`, `vidalstore-gateway`, `vidalstore-backend`):

```bash
python3 scripts/audit_ep1.py
```

El script analizará tu código y te entregará un reporte visual con semáforo:
* `[✓ LOGRADO]`: Requisitos que cumplen al 100%.
* `[⚠ ATENCIÓN]`: Elementos a revisar (como el conteo de commits).
* `[✗ NO LOGRADO]`: Errores que restan puntaje según la rúbrica oficial, con la **acción correctiva exacta** para solucionarlos.

---

### Opción C: En Claude Code, Cursor o ChatGPT

Puedes referenciar o importar el archivo `SKILL.md` como system prompt o regla de proyecto (`.cursorrules`, `CLAUDE.md`, etc.).

---

## 📌 Checklist de los 10 Mandamientos de Umbingelelo

Cualquier proyecto que aspire a nota 7.0 debe cumplir con estos 10 puntos:

- [ ] **1. Una sola dirección en el Frontend**: Angular solo conoce la URL del Gateway (`http://localhost:8080`). La lista blanca del interceptor tiene una sola entrada.
- [ ] **2. Token en `sessionStorage`**: Configurado explícitamente en `main.ts` con `cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage)`.
- [ ] **3. Hosted UI Obligatorio**: Login y registro delegado a Cognito mediante `signInWithRedirect()`. Prohibido formularios propios de contraseña.
- [ ] **4. Sin vitrina pública**: `/catalogo` y `/biblioteca` protegidos con `sessionGuard`.
- [ ] **5. Token validado en ambos saltos**: El Gateway valida contra el JWKS y reenvía el encabezado `Authorization` al Backend para que este vuelva a validar (defensa en profundidad).
- [ ] **6. Biblioteca resuelta por `sub`**: `GET /v1/biblioteca` obtiene la identidad únicamente del claim `sub` del JWT. Prohibido recibir `userId` por parámetro o body.
- [ ] **7. Idempotencia en compras**: `POST /v1/compras` retorna `409 Conflict` si el usuario ya posee una licencia para ese juego.
- [ ] **8. Carpeta `data/` con Seed Real**: Cada microservicio debe tener `data/seed.ts` (o `.js`) que consuma una API externa real y guarde los datos en un JSON versionado.
- [ ] **9. Grupo `jugadores` automático**: Trigger Lambda Post-Confirmación en Cognito que asigna el rol al registrarse.
- [ ] **10. Conteo de Commits e Invitación**: Entre 100 y 200 commits en total entre los repositorios, y el usuario `Umbingelelo` invitado como colaborador en todos los repositorios de GitHub.

---

## 🧪 Las 4 Pruebas Obligatorias del Gateway (IE10)

Antes de entregar, prueba tu Gateway en el puerto 8080 con estos comandos `curl`:

1. **Sin token (`401 Unauthorized`)**:
   ```bash
   curl -i http://localhost:8080/v1/catalogo
   ```
2. **Token alterado (`401 Unauthorized`)**:
   ```bash
   curl -i -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.tokenInvalido" http://localhost:8080/v1/catalogo
   ```
3. **Token de otra aplicación / App Client 2 (`401 Unauthorized`)**:
   ```bash
   curl -i -H "Authorization: Bearer <token_client2>" http://localhost:8080/v1/catalogo
   ```
4. **Token con rol insuficiente (`403 Forbidden`)**:
   ```bash
   curl -i -X DELETE -H "Authorization: Bearer <token_jugador>" http://localhost:8080/v1/licencias/lic-123
   ```

---

## ⚖️ Licencia

Distribuido bajo la licencia MIT. Uso libre para estudiantes de Duoc UC y la comunidad académica.
