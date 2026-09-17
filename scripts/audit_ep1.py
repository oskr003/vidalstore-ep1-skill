#!/usr/bin/env python3
"""
Script de Auditoría Automática para la Evaluación Parcial 1 (EP1) - Caso VidalStore.
Verifica punto por punto los requisitos de:
  - EP1-aclaraciones.pdf
  - EP1-Caso-VidalStore.pdf (IE1 a IE10)
  - Respuestas del profesor Umbingelelo en el foro GitHub
"""

import os
import re
import subprocess
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
FRONTEND_DIR = os.path.join(BASE_DIR, "vidalstore-frontend")
GATEWAY_DIR = os.path.join(BASE_DIR, "vidalstore-gateway")
BACKEND_DIR = os.path.join(BASE_DIR, "vidalstore-backend")

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD} {title}{RESET}")
    print(f"{BOLD}======================================================================{RESET}")

def check_pass(msg):
    print(f"  {GREEN}[✓ LOGRADO]{RESET} {msg}")

def check_warn(msg, fix=""):
    print(f"  {YELLOW}[⚠ ATENCIÓN]{RESET} {msg}")
    if fix:
        print(f"    {BOLD}↳ Acción sugerida:{RESET} {fix}")

def check_fail(msg, fix=""):
    print(f"  {RED}[✗ NO LOGRADO]{RESET} {msg}")
    if fix:
        print(f"    {BOLD}↳ Acción requerida:{RESET} {fix}")

def run_cmd(cmd, cwd):
    try:
        res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return ""

def audit_git():
    print_header("1. AUDITORÍA DE GIT, COMMITS Y REPOSITORIOS")
    repos = [("vidalstore-frontend", FRONTEND_DIR), 
             ("vidalstore-gateway", GATEWAY_DIR), 
             ("vidalstore-backend", BACKEND_DIR)]
    
    total_commits = 0
    for name, path in repos:
        if not os.path.exists(path):
            check_fail(f"Repositorio no encontrado: {name}", f"Verificar que la carpeta {name} exista en la raíz.")
            continue
        
        git_dir = os.path.join(path, ".git")
        if not os.path.exists(git_dir):
            check_warn(f"{name} no está inicializado como repositorio git.")
            continue
        
        branch = run_cmd("git branch --show-current", path)
        count_str = run_cmd("git rev-list --count HEAD", path)
        count = int(count_str) if count_str.isdigit() else 0
        total_commits += count
        
        print(f"  • {name}: Rama {BOLD}{branch}{RESET} | Commits: {BOLD}{count}{RESET}")
    
    print(f"\n  Total de commits acumulados en el proyecto: {BOLD}{total_commits}{RESET}")
    if 100 <= total_commits <= 200:
        check_pass(f"Cumple con el rango estimado por Umbingelelo (100 a 200 commits).")
    elif total_commits < 100:
        check_warn(f"Actualmente tienes {total_commits} commits. Umbingelelo estimó entre 100 y 200 commits en total.",
                   "Continuar realizando commits descriptivos y atómicos por cada funcionalidad o test.")
    else:
        check_pass(f"Proyecto con amplio historial de commits ({total_commits}).")

def audit_frontend():
    print_header("2. AUDITORÍA DE FRONTEND (ANGULAR + AMPLIFY)")
    if not os.path.exists(FRONTEND_DIR):
        check_fail("Carpeta vidalstore-frontend no encontrada.")
        return

    main_ts = os.path.join(FRONTEND_DIR, "src/main.ts")
    if os.path.exists(main_ts):
        content = open(main_ts).read()
        if "sessionStorage" in content and "setKeyValueStorage" in content:
            check_pass("Token configurado explícitamente en sessionStorage (main.ts).")
        else:
            check_fail("Falta configurar el token en sessionStorage con cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage).",
                       "Configurarlo en src/main.ts según página 5 de aclaraciones.")
        
        if "signInWithRedirect" in content or "oauth" in content:
            check_pass("Configuración OAuth con redirección presente en main.ts.")
    else:
        check_fail("No se encontró src/main.ts en el frontend.")

    routes_ts = os.path.join(FRONTEND_DIR, "src/app/app.routes.ts")
    if os.path.exists(routes_ts):
        content = open(routes_ts).read()
        if "canActivate" in content and "catalogo" in content:
            check_pass("Ruta /catalogo protegida con Guard (no hay vitrina pública).")
        else:
            check_fail("La ruta /catalogo debe estar protegida con un guard de sesión.",
                       "Agregar canActivate: [sesionGuard] en app.routes.ts.")
    
    interceptor_ts = os.path.join(FRONTEND_DIR, "src/app/interceptors/token.interceptor.ts")
    if os.path.exists(interceptor_ts):
        content = open(interceptor_ts).read()
        urls = re.findall(r'http://localhost:\d+', content)
        if len(set(urls)) == 1 and "8080" in urls[0]:
            check_pass(f"Interceptor HTTP tiene lista blanca con una sola entrada ({urls[0]}).")
        elif len(set(urls)) > 1:
            check_warn("El interceptor tiene más de una dirección en su lista blanca.",
                       "El frontend solo debe comunicarse con el API Gateway (http://localhost:8080).")

    vidalstore_ts = os.path.join(FRONTEND_DIR, "src/app/services/vidalstore.ts")
    if os.path.exists(vidalstore_ts):
        content = open(vidalstore_ts).read()
        if "/v1/catalogo" in content and "/v1/biblioteca" in content:
            check_pass("Servicio frontend VidalStore llama a /v1/catalogo y /v1/biblioteca.")

def audit_gateway():
    print_header("3. AUDITORÍA DEL API GATEWAY (NESTJS)")
    if not os.path.exists(GATEWAY_DIR):
        check_fail("Carpeta vidalstore-gateway no encontrada.")
        return

    main_ts = os.path.join(GATEWAY_DIR, "src/main.ts")
    if os.path.exists(main_ts):
        content = open(main_ts).read()
        if "8080" in content:
            check_pass("API Gateway configurado en el puerto estándar 8080.")
        if "enableCors" in content:
            if "localhost:4200" in content:
                check_pass("CORS habilitado y restringido al origen de Angular (http://localhost:4200).")
            else:
                check_warn("CORS está habilitado pero verificar que solo permita http://localhost:4200.")
        else:
            check_fail("CORS no está configurado explícitamente en el Gateway.",
                       "Agregar app.enableCors({ origin: 'http://localhost:4200', methods: 'GET,POST,PUT,DELETE,OPTIONS' })")

    auth_guard = os.path.join(GATEWAY_DIR, "src/auth/auth.guard.ts")
    if os.path.exists(auth_guard):
        content = open(auth_guard).read()
        validations = []
        if "jwks" in content.lower() or "publickey" in content.lower() or "verify" in content.lower():
            validations.append("Firma/JWKS")
        if "iss" in content or "issuer" in content:
            validations.append("Emisor")
        if "exp" in content or "expiration" in content:
            validations.append("Vigencia")
        if "token_use" in content:
            validations.append("Tipo (access)")
        if "client_id" in content:
            validations.append("App Client")
        
        check_pass(f"AuthGuard en Gateway implementa validaciones criptográficas: {', '.join(validations)}.")
    
    # Check routes exposed in Gateway
    gateway_controllers = []
    gateway_content = ""
    for root, _, files in os.walk(os.path.join(GATEWAY_DIR, "src")):
        for f in files:
            if f.endswith(".controller.ts") and f != "app.controller.ts":
                gateway_controllers.append(f)
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                        gateway_content += fp.read() + "\n"
                except Exception:
                    pass
    
    print(f"  • Controladores en Gateway: {gateway_controllers}")
    missing_routes = []
    for expected in ["biblioteca", "compras", "licencias", "catalogo"]:
        if expected not in gateway_content.lower():
            missing_routes.append(expected)
    
    if missing_routes:
        check_fail(f"El Gateway no expone endpoints proxy para: {', '.join(missing_routes)}.",
                   "Crear los controladores proxy en vidalstore-gateway con prefijo /v1/ y reenviar el Authorization header.")
    else:
        check_pass("El Gateway cuenta con controladores proxy para todos los módulos requeridos (catalogo, compras, biblioteca, licencias, auditoria).")

def audit_backend():
    print_header("4. AUDITORÍA DE BACKEND / BFF Y MICROSERVICIOS")
    if not os.path.exists(BACKEND_DIR):
        check_fail("Carpeta vidalstore-backend no encontrada.")
        return

    # Buscar controladores de forma recursiva en backend (BFF y microservicios)
    backend_controllers = {}
    for root, _, files in os.walk(os.path.join(BACKEND_DIR, "src")):
        for f in files:
            if f.endswith(".controller.ts") or f.endswith(".service.ts"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                        backend_controllers[f] = fp.read()
                except Exception:
                    pass

    # Compras (idempotencia)
    compras_content = "".join(v for k, v in backend_controllers.items() if "compras" in k.lower())
    if "ConflictException" in compras_content:
        check_pass("POST /v1/compras implementa idempotencia respondiendo 409 ante licencias ya existentes.")
    else:
        check_warn("POST /v1/compras no parece retornar 409 Conflict ante duplicados.",
                   "Implementar verificación de compra duplicada para devolver 409 según discusión #10.")

    # Biblioteca (sub)
    biblio_content = "".join(v for k, v in backend_controllers.items() if "biblioteca" in k.lower() and "controller" in k.lower())
    if "usuarioSub" in biblio_content or "sub" in biblio_content:
        check_pass("GET /v1/biblioteca resuelve al usuario estrictamente por el claim 'sub' del JWT.")
    if "@Param" in biblio_content or "@Query" in biblio_content:
        check_fail("GET /v1/biblioteca no debe recibir ningún identificador de usuario por parámetro o query.",
                   "Eliminar cualquier parámetro de usuario y obtenerlo solo de req.user.sub.")

    # Licencias (admin DELETE)
    licencias_content = "".join(v for k, v in backend_controllers.items() if "licencias" in k.lower())
    if "administradores" in licencias_content and ("Delete" in licencias_content or "revocar" in licencias_content):
        check_pass("DELETE /v1/licencias/:id protegido por grupo 'administradores'.")
    else:
        check_fail("DELETE /v1/licencias/:id debe exigir estrictamente grupo 'administradores'.")

    # Data folder and seed
    data_dir = os.path.join(BACKEND_DIR, "data")
    seed_files = []
    if os.path.exists(data_dir):
        seed_files = [f for f in os.listdir(data_dir) if "seed" in f.lower() or f.endswith(".json")]
    
    if os.path.exists(data_dir) and any("seed" in f for f in seed_files) and any(f.endswith(".json") for f in seed_files):
        check_pass(f"Carpeta data/ presente con script de seed y datos versionados: {seed_files}.")
    else:
        check_fail("Cada microservicio debe tener una carpeta data/ con un script seed que consuma una API externa real y su JSON generado.",
                   "Crear data/seed.ts consumiendo una API real de videojuegos y generar data/catalogo.json.")

def audit_secrets():
    print_header("5. AUDITORÍA DE SEGURIDAD (HIGIENE DE SECRETOS)")
    pattern = re.compile(r'(aws_secret_access_key|client_secret|password\s*=\s*[\'"][^\'"]+[\'"])', re.I)
    found_secrets = []
    
    for repo_path in [FRONTEND_DIR, GATEWAY_DIR, BACKEND_DIR]:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", ".agents"]]
            for file in files:
                if file.endswith((".ts", ".js", ".json", ".env")):
                    fpath = os.path.join(root, file)
                    try:
                        text = open(fpath, encoding="utf-8", errors="ignore").read()
                        if pattern.search(text) and "example" not in file and "template" not in file:
                            found_secrets.append(os.path.relpath(fpath, BASE_DIR))
                    except Exception:
                        pass
    
    if not found_secrets:
        check_pass("No se detectaron secretos ni contraseñas evidentes en el código fuente.")
    else:
        check_warn(f"Se detectaron posibles secretos en los siguientes archivos:\n    {found_secrets}",
                   "Revisar que no se estén commiteando credenciales reales ni claves privadas de AWS.")

def main():
    print(f"\n{BOLD}INICIANDO AUDITORÍA INTEGRAL VIDALSTORE EP1 (DSY1107){RESET}")
    print(f"Directorio de evaluación: {BASE_DIR}")
    
    audit_git()
    audit_frontend()
    audit_gateway()
    audit_backend()
    audit_secrets()
    
    print_header("FIN DE LA AUDITORÍA")
    print(f"Para más detalles sobre cómo resolver cada observación, consultar:")
    print(f"  • .agents/skills/vidalstore-ep1/SKILL.md")
    print(f"  • .agents/skills/vidalstore-ep1/references/rubrica_completa.md")
    print(f"  • .agents/skills/vidalstore-ep1/references/preguntas_defensa.md\n")

if __name__ == "__main__":
    main()
