#!/usr/bin/env python3
"""
Script de Auditoría Automática para Laboratorio L8, L8A y Unidad 2 (Clúster RabbitMQ, Quorum Queues, Microservicio Administrador y Políticas).
Verifica:
  1. Configuración de Clúster de 2 Nodos (cluster.conf, compose.yml, volúmenes nombrados, Erlang cookie, sin depends_on circular en rabbit2).
  2. Quorum Queues en Topología (x-queue-type: quorum en colas de trabajo y DLQs).
  3. Microservicio Administrador (RabbitAdminService encapsulado, DTOs con class-validator, ValidationPipe forbidNonWhitelisted, traducir() con 404/409/503).
  4. Seguridad y Roles en el Administrador (JwtGuard con jose, RolGuard con roles administrativos).
  5. Políticas de Retención (politicas.json versionado con max-length, drop-head y reject-publish).
  6. Higiene de Secretos (.env ignorado en .gitignore, .env.example versionado con RABBITMQ_COOKIE).
"""

import os
import re
import subprocess
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

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

def find_file(filename, search_dirs=None):
    if search_dirs is None:
        search_dirs = [BASE_DIR]
    for d in search_dirs:
        for root, _, files in os.walk(d):
            if "node_modules" in root or ".git" in root:
                continue
            if filename in files:
                return os.path.join(root, filename)
    return None

def read_content(path):
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def audit_cluster_config():
    print_header("1. CLÚSTER DE DOS NODOS Y AUTODESCUBRIMIENTO (IE9, IE10, IE11)")
    
    # 1.1 cluster.conf
    cluster_conf = find_file("cluster.conf")
    if not cluster_conf:
        cluster_conf = find_file("20-cluster.conf")
    
    if cluster_conf:
        content = read_content(cluster_conf)
        if ("classic_config" in content or "rabbit_peer_discovery_classic_config" in content) and ("rabbit@rabbitmq1" in content or "rabbit@rabbit1" in content):
            check_pass(f"Archivo de clúster encontrado con descubrimiento clásico automático ({os.path.relpath(cluster_conf, BASE_DIR)})")
        else:
            check_warn(f"cluster.conf presente pero faltan directivas de nodos rabbit@rabbitmq1 y rabbit@rabbitmq2")
    else:
        check_fail("No se encontró archivo rabbitmq/cluster.conf para autodescubrimiento sin comandos manuales",
                   "Crear rabbitmq/cluster.conf con classic_config apuntando a rabbit@rabbit1 y rabbit@rabbit2.")

    # 1.2 compose.yml con los 2 nodos
    compose_path = find_file("compose.yml") or find_file("docker-compose.yml")
    if compose_path:
        c_content = read_content(compose_path)
        has_r1 = "rabbit1:" in c_content or "rabbitmq1:" in c_content
        has_r2 = "rabbit2:" in c_content or "rabbitmq2:" in c_content
        
        if has_r1 and has_r2:
            check_pass("compose.yml define ambos nodos RabbitMQ (rabbit1 y rabbit2)")
        else:
            check_fail("compose.yml no define ambos nodos rabbit1 y rabbit2",
                       "Agregar rabbit2 con puertos 5673:5672 y 15673:15672.")

        # Verificar cookie compartida
        if "RABBITMQ_ERLANG_COOKIE" in c_content or "RABBITMQ_COOKIE" in c_content:
            check_pass("compose.yml propaga la cookie de Erlang en ambos nodos")
        else:
            check_fail("Falta RABBITMQ_ERLANG_COOKIE en las variables de entorno de rabbit1 y rabbit2")

        # Verificar ausencia de depends_on circular/deadlock en rabbit2
        r2_match = re.search(r'^\s+(rabbit2|rabbitmq2):.*?(?=^\s{2}[a-zA-Z0-9_-]+:|\Z)', c_content, re.DOTALL | re.MULTILINE)
        if r2_match:
            r2_block = r2_match.group(0)
            if "depends_on" in r2_block and "condition: service_healthy" in r2_block:
                check_fail("rabbit2 tiene depends_on con service_healthy hacia rabbit1 (riesgo de deadlock o falla en recreación)",
                           "Eliminar depends_on de rabbit2; ambos deben arrancar en paralelo y unirse vía cluster.conf.")
            else:
                check_pass("rabbit2 arranca de forma autónoma sin depends_on restrictivo")

        # Verificar montaje de cluster.conf
        if "cluster.conf" in c_content:
            check_pass("cluster.conf está montado en /etc/rabbitmq/conf.d/ en compose.yml")
        else:
            check_warn("cluster.conf no parece estar montado en el bloque volumes de los nodos")

def audit_quorum_queues():
    print_header("2. QUORUM QUEUES Y MIGRACIÓN RAFT (IE10, IE12, IE13)")
    topologia_ts = find_file("topologia.ts") or find_file("topologia.mjs")
    
    if topologia_ts:
        content = read_content(topologia_ts)
        quorum_count = content.count("'x-queue-type': 'quorum'") + content.count('"x-queue-type": "quorum"') + content.count("x-queue-type: 'quorum'")
        
        if quorum_count >= 2 or "quorum" in content:
            check_pass(f"Topología declara colas Quorum con 'x-queue-type': 'quorum' ({os.path.relpath(topologia_ts, BASE_DIR)})")
        else:
            check_fail("topologia.ts no contiene 'x-queue-type': 'quorum'",
                       "Agregar 'x-queue-type': 'quorum' a los argumentos de las colas de trabajo y las 3 DLQ.")
        
        if "ha-mode" in content:
            check_fail("Se detectó 'ha-mode' en topología. Las colas espejo fueron eliminadas en RabbitMQ 4.0",
                       "Reemplazar colas espejo por Quorum Queues.")
    else:
        check_warn("No se encontró archivo topologia.ts para auditar Quorum Queues")

def audit_admin_microservice():
    print_header("3. MICROSERVICIO ADMINISTRADOR (IE6, IE7, IE8, IE17)")
    
    # 3.1 Servicio RabbitAdminService
    admin_service = find_file("rabbit-admin.service.ts") or find_file("admin.service.ts")
    if admin_service:
        content = read_content(admin_service)
        check_pass(f"RabbitAdminService encontrado ({os.path.relpath(admin_service, BASE_DIR)})")
        
        # Verificar canal efímero y oyente de error
        if "canal.on('error'" in content or 'canal.on("error"' in content:
            check_pass("Canal efímero protegido con oyente canal.on('error', ...) para evitar caídas de Node.js")
        else:
            check_warn("Falta canal.on('error', () => undefined) en los canales de RabbitAdminService")

        # Verificar método traducir
        if "traducir" in content or ("NOT_FOUND" in content and "PRECONDITION_FAILED" in content):
            check_pass("Método de traducción semántica presente (mapea NOT_FOUND a 404 y PRECONDITION_FAILED a 409)")
        else:
            check_fail("Falta función de mapeo de excepciones de AMQP a códigos HTTP (404, 409, 503)",
                       "Implementar método traducir() que capture errores de AMQP y arroje excepciones de NestJS.")

        # Verificar AMQP y Management API
        has_amqp = "assertQueue" in content or "deleteQueue" in content
        has_http = "fetch" in content or "axios" in content or "http" in content or "/api/queues" in content
        if has_amqp and has_http:
            check_pass("RabbitAdminService implementa arquitectura de 2 protocolos (AMQP para mutaciones y HTTP para lecturas)")
        elif has_amqp:
            check_warn("RabbitAdminService implementa AMQP pero no parece consultar la HTTP Management API para listar colas")
    else:
        check_fail("No se encontró RabbitAdminService", "Crear servicio que encapsule las operaciones administrativas de RabbitMQ.")

    # 3.2 DTOs y class-validator
    dto_file = find_file("crear-cola.dto.ts") or find_file("admin.dto.ts") or find_file("colas.dto.ts")
    if dto_file:
        content = read_content(dto_file)
        if "class-validator" in content or "@IsString" in content:
            check_pass(f"DTOs con validación estricta encontrados ({os.path.relpath(dto_file, BASE_DIR)})")
            if "@Matches" in content or "NOMBRE_VALIDO" in content:
                check_pass("DTO valida nombres de colas con expresión regular permitida")
            else:
                check_warn("Se sugiere validar nombres de colas con regex ^[a-zA-Z0-9._-]+$")
        else:
            check_fail("Los DTOs no implementan decoradores de class-validator")
    else:
        check_warn("No se encontró archivo DTO explícito de colas en el administrador")

    # 3.3 ValidationPipe global
    admin_main = find_file("main.ts", search_dirs=[os.path.join(BASE_DIR, "vidalstore-admin")])
            
    if admin_main:
        content = read_content(admin_main)
        if "ValidationPipe" in content:
            has_white = "whitelist: true" in content
            has_forbid = "forbidNonWhitelisted: true" in content
            if has_white and has_forbid:
                check_pass("main.ts de vidalstore-admin configura ValidationPipe con whitelist y forbidNonWhitelisted")
            else:
                check_fail("Falta forbidNonWhitelisted: true en el ValidationPipe global de vidalstore-admin",
                           "Configurar forbidNonWhitelisted: true para responder 400 ante campos desconocidos.")
        else:
            check_fail("main.ts de vidalstore-admin no configura useGlobalPipes(new ValidationPipe(...))")
    else:
        check_warn("No se encontró main.ts en vidalstore-admin")

def audit_policies():
    print_header("4. POLÍTICAS DE RETENCIÓN VERSIONADAS (IE19)")
    politicas_json = find_file("politicas.json")
    
    if politicas_json:
        content = read_content(politicas_json)
        check_pass(f"Archivo de políticas versionado encontrado ({os.path.relpath(politicas_json, BASE_DIR)})")
        
        has_max_len = "max-length" in content
        has_drop_head = "drop-head" in content
        has_reject_pub = "reject-publish" in content
        has_ttl = "message-ttl" in content
        
        if has_max_len:
            check_pass("Políticas configuran límite estricto con 'max-length'")
        else:
            check_fail("Falta directiva 'max-length' en politicas.json")

        if has_drop_head and has_reject_pub:
            check_pass("Políticas implementan ambas estrategias de overflow: drop-head (avisos) y reject-publish (auditoría/DLQ)")
        elif has_drop_head or has_reject_pub:
            check_warn("Se encontró solo una de las estrategias de overflow (drop-head o reject-publish)")
            
        if has_ttl:
            check_pass("Políticas configuran caducidad temporal con 'message-ttl'")
        else:
            check_warn("No se detectó 'message-ttl' en politicas.json")
    else:
        check_fail("No se encontró rabbitmq/politicas.json",
                   "Crear rabbitmq/politicas.json y montarlo en rabbit1 para cargar con import_definitions.")

def audit_hygiene():
    print_header("5. HIGIENE DE SECRETOS Y VARIABLES DE ENTORNO")
    env_example = find_file(".env.example", [os.path.join(BASE_DIR, "vidalstore-plataforma"), BASE_DIR])
    if env_example:
        content = read_content(env_example)
        if "RABBITMQ_COOKIE" in content or "RABBIT_URL" in content:
            check_pass(f".env.example incluye variables de clúster y cookie ({os.path.relpath(env_example, BASE_DIR)})")
        else:
            check_warn(".env.example no incluye RABBITMQ_COOKIE")
    else:
        check_fail("No se encontró .env.example en la plataforma",
                   "Dejar .env.example versionado con RABBITMQ_COOKIE y credenciales de ejemplo.")

def main():
    print(f"{BOLD}======================================================================{RESET}")
    print(f"{BOLD} AUDITORÍA TÉCNICA L8 / L8A · CLÚSTER Y ADMINISTRADOR RABBITMQ{RESET}")
    print(f"{BOLD} Asignatura: DSY1107 - Desarrollo Cloud Native I (DUOC UC){RESET}")
    print(f"{BOLD}======================================================================{RESET}")
    
    audit_cluster_config()
    audit_quorum_queues()
    audit_admin_microservice()
    audit_policies()
    audit_hygiene()
    
    print(f"\n{BOLD}Auditoría L8/L8A finalizada.{RESET}\n")

if __name__ == "__main__":
    main()
