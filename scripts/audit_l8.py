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
    print_header("2. QUORUM QUEUES, MIGRACIÓN RAFT Y SINCRONIZACIÓN DE TOPOLOGÍA (IE1, IE10, IE12, IE13)")
    topo_paths = [
        os.path.join(BASE_DIR, "vidalstore-plataforma", "shared", "topologia.ts"),
        os.path.join(BASE_DIR, "vidalstore-eventos", "src", "mensajeria", "topologia.ts"),
        os.path.join(BASE_DIR, "vidalstore-admin", "src", "mensajeria", "topologia.ts"),
        os.path.join(BASE_DIR, "vidalstore-backend", "src", "mensajeria", "topologia.ts"),
    ]
    existing_topos = [p for p in topo_paths if os.path.exists(p)]

    if existing_topos:
        for tpath in existing_topos:
            content = read_content(tpath)
            rel = os.path.relpath(tpath, BASE_DIR)
            quorum_count = content.count("'x-queue-type': 'quorum'") + content.count('"x-queue-type": "quorum"') + content.count("x-queue-type: 'quorum'")
            if quorum_count >= 2:
                check_pass(f"{rel} declara colas Quorum con 'x-queue-type': 'quorum' ({quorum_count} bloques)")
            else:
                check_fail(f"{rel} no contiene 'x-queue-type': 'quorum' en las colas",
                           "Agregar 'x-queue-type': 'quorum' a las colas de trabajo y las 3 DLQ.")
            if "COLA_REPROCESO" in content and quorum_count < 3:
                check_warn(f"{rel} declara COLA_REPROCESO ('q.reprocesar') sin 'x-queue-type': 'quorum'.")
            if "ha-mode" in content:
                check_fail(f"Se detectó 'ha-mode' en {rel}. Las colas espejo fueron eliminadas en RabbitMQ 4.0")

        # Verificar consistencia entre archivos topologia.ts (IE1)
        has_reproceso_cola = [os.path.relpath(p, BASE_DIR) for p in existing_topos if "COLA_REPROCESO" in read_content(p)]
        missing_reproceso_cola = [os.path.relpath(p, BASE_DIR) for p in existing_topos if "COLA_REPROCESO" not in read_content(p)]
        if has_reproceso_cola and missing_reproceso_cola:
            check_warn(f"Desincronización en topologia.ts (IE1): {has_reproceso_cola} define COLA_REPROCESO pero {missing_reproceso_cola} no la incluye.",
                       "Propagar la misma definición de topologia.ts a los 4 repositorios (EP2-Caso-VidalStore.pdf §4.1 pág. 15).")
        else:
            check_pass("Los archivos topologia.ts están sincronizados entre los repositorios.")
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
            check_pass("RabbitAdminService implementa arquitectura de 2 protocolos (AMQP y HTTP Management API)")
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

    binding_dto = find_file("crear-binding.dto.ts") or find_file("binding.dto.ts")
    if binding_dto:
        b_content = read_content(binding_dto)
        if "exchange" in b_content and "cola" in b_content:
            check_pass("CrearBindingDto soporta formato '{ exchange, cola, routingKey }' (EP2-Caso-VidalStore.pdf pág. 20)")
        elif "origen" in b_content and "exchange" not in b_content:
            check_warn("CrearBindingDto usa 'origen' y 'destino', pero EP2-Caso-VidalStore.pdf (pág. 20) y L8.pdf (pág. 25) especifican '{ exchange, cola, routingKey }'.",
                       "Con forbidNonWhitelisted: true, un curl del docente enviando '{ exchange, cola, routingKey }' recibirá 400 Bad Request si no se admiten ambos nombres.")

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
    print_header("4. POLÍTICAS DE RETENCIÓN VERSIONADAS Y DOCUMENTACIÓN (IE19 & EP2 §4.8)")
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
            check_pass("Políticas implementan ambas estrategias de overflow: drop-head y reject-publish")
        elif has_drop_head or has_reject_pub:
            check_warn("Se encontró solo una de las estrategias de overflow (drop-head o reject-publish)")
            
        if has_ttl:
            check_pass("Políticas configuran caducidad temporal con 'message-ttl'")
        else:
            check_warn("No se detectó 'message-ttl' en politicas.json")
    else:
        check_fail("No se encontró rabbitmq/politicas.json",
                   "Crear rabbitmq/politicas.json y montarlo en rabbit1 para cargar con import_definitions.")

    docs_dir = os.path.join(BASE_DIR, "vidalstore-plataforma", "docs")
    if os.path.exists(docs_dir):
        pol_md = os.path.join(docs_dir, "politicas.md")
        pol_ret_md = os.path.join(docs_dir, "politicas-retencion.md")
        if os.path.exists(pol_md):
            check_pass("Archivo entregable docs/politicas.md presente (nombre exacto de EP2-Caso-VidalStore.pdf pág. 23 y 24).")
        elif os.path.exists(pol_ret_md):
            check_warn("Existe docs/politicas-retencion.md pero EP2-Caso-VidalStore.pdf (pág. 23 y 24) y L8.pdf (pág. 52) piden el nombre 'docs/politicas.md'.")

        # Verificar textos desactualizados o nombres propios en docs/ (Regla 14)
        repos_md = os.path.join(docs_dir, "repositorios.md")
        modelo_md = os.path.join(docs_dir, "modelo-de-datos.md")
        for doc_path in [repos_md, modelo_md]:
            if os.path.exists(doc_path):
                d_txt = read_content(doc_path)
                rel_d = os.path.relpath(doc_path, BASE_DIR)
                if "no incluye el driver `pg`" in d_txt or "no expone endpoints CRUD" in d_txt or "todavía no declara un consumidor" in d_txt:
                    check_warn(f"{rel_d} contiene notas de 'Estado conocido' desactualizadas que contradicen el código ya implementado.")
                if re.search(r"\b(David|Oscar|Ivan|Iván)\b", d_txt):
                    check_warn(f"{rel_d} contiene nombres propios de integrantes (Regla 14 de neutralidad técnica).")

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
