#!/usr/bin/env python3
"""
audit_ep3.py - Auditor Automatizado de Calidad y Cumplimiento EP3 (DSY1107)

Verifica automáticamente el cumplimiento de los estándares normativos de la
Unidad 3 / Evaluación Parcial N°3 para el proyecto VidalStore:
1. Higiene de saltos de línea y presencia de .gitattributes en los 8 repositorios.
2. Regla estricta de dependencias: presencia de @platformatic/kafka@2.14.0 y
   ausencia total de librerías prohibidas (kafkajs, @confluentinc/kafka-javascript).
3. Configuración de clúster KRaft en Docker Compose (3 controllers + 3 brokers + CLUSTER_ID).
4. Catálogo oficial de topics de VidalStore (retención y compactación).
"""

import os
import sys
import json
import re

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_CYAN = "\033[36m"

REPOS = [
    "vidalstore-plataforma",
    "vidalstore-bff",
    "vidalstore-catalogo",
    "vidalstore-licencias",
    "vidalstore-admin",
    "vidalstore-eventos",
    "vidalstore-gateway",
    "vidalstore-frontend",
]

TOPICS_REQUERIDOS = [
    "vidalstore.compras",
    "vidalstore.actividad",
    "vidalstore.compras.dlt",
    "vidalstore.actividad.dlt",
    "vidalstore.catalogo",
]

TOTAL_CHECKS = 0
PASSED_CHECKS = 0
WARNING_CHECKS = 0
FAILED_CHECKS = 0


def log_pass(msg):
    global TOTAL_CHECKS, PASSED_CHECKS
    TOTAL_CHECKS += 1
    PASSED_CHECKS += 1
    print(f"  {C_GREEN}✔ [PASS]{C_RESET} {msg}")


def log_warn(msg):
    global TOTAL_CHECKS, WARNING_CHECKS
    TOTAL_CHECKS += 1
    WARNING_CHECKS += 1
    print(f"  {C_YELLOW}⚠ [WARN]{C_RESET} {msg}")


def log_fail(msg):
    global TOTAL_CHECKS, FAILED_CHECKS
    TOTAL_CHECKS += 1
    FAILED_CHECKS += 1
    print(f"  {C_RED}✘ [FAIL]{C_RESET} {msg}")


def audit_gitattributes(root_dir):
    print(f"\n{C_BOLD}[1/4] Verificando .gitattributes e higiene EOL en repositorios...{C_RESET}")
    for repo in REPOS:
        repo_path = os.path.join(root_dir, repo)
        if not os.path.isdir(repo_path):
            log_warn(f"[{repo}] Directorio no encontrado localmente.")
            continue

        gitattr_path = os.path.join(repo_path, ".gitattributes")
        if os.path.isfile(gitattr_path):
            with open(gitattr_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "eol=lf" in content:
                log_pass(f"[{repo}] .gitattributes presente con regla eol=lf.")
            else:
                log_warn(f"[{repo}] .gitattributes presente pero sin regla eol=lf explícita.")
        else:
            log_warn(f"[{repo}] Falta archivo .gitattributes (obligatorio para E1).")


def audit_kafka_dependencies(root_dir):
    print(f"\n{C_BOLD}[2/4] Verificando dependencias de Kafka en repositorios Node.js...{C_RESET}")
    for repo in REPOS:
        pkg_path = os.path.join(root_dir, repo, "package.json")
        if not os.path.isfile(pkg_path):
            continue

        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
        except Exception as e:
            log_fail(f"[{repo}] Error al leer package.json: {e}")
            continue

        deps = pkg_data.get("dependencies", {})
        dev_deps = pkg_data.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}

        # Verificación de librerías prohibidas
        prohibidas = ["kafkajs", "@confluentinc/kafka-javascript"]
        for p in prohibidas:
            if p in all_deps:
                log_fail(f"[{repo}] Contiene librería prohibida por pauta: '{p}' (usar @platformatic/kafka).")

        # Verificación de cliente oficial si usa Kafka
        if "@platformatic/kafka" in all_deps:
            version = all_deps["@platformatic/kafka"]
            if version == "2.14.0":
                log_pass(f"[{repo}] @platformatic/kafka fijado exactamente en '2.14.0' (--save-exact).")
            else:
                log_warn(f"[{repo}] @platformatic/kafka en versión '{version}' (pauta sugiere fijar exactamente '2.14.0').")


def audit_kraft_compose(root_dir):
    print(f"\n{C_BOLD}[3/6] Verificando configuración KRaft en Docker Compose...{C_RESET}")
    candidatos_compose = [
        os.path.join(root_dir, "vidalstore-plataforma", "docker-compose.yml"),
        os.path.join(root_dir, "vidalstore-plataforma", "compose.yml"),
        os.path.join(root_dir, "compose.yml"),
        os.path.join(root_dir, "docker-compose.yml"),
    ]
    compose_path = None
    for c in candidatos_compose:
        if os.path.isfile(c):
            compose_path = c
            break

    if not compose_path:
        log_warn("compose.yml no encontrado en la raíz ni en vidalstore-plataforma.")
        return

    with open(compose_path, "r", encoding="utf-8", errors="ignore") as f:
        compose_text = f.read()

    # Verificar presencia de controladores y brokers KRaft
    controllers = ["controller-1", "controller-2", "controller-3"]
    brokers = ["broker-1", "broker-2", "broker-3"]

    encontrados_c = [c for c in controllers if c in compose_text]
    encontrados_b = [b for b in brokers if b in compose_text]

    if len(encontrados_c) == 3:
        log_pass("Los 3 controllers KRaft están declarados en Compose.")
    elif len(encontrados_c) > 0:
        log_warn(f"Solo {len(encontrados_c)} de 3 controllers declarados en Compose ({encontrados_c}).")
    else:
        log_warn("No se detectaron controllers KRaft en compose.yml aún.")

    if len(encontrados_b) == 3:
        log_pass("Los 3 brokers KRaft están declarados en Compose.")
    elif len(encontrados_b) > 0:
        log_warn(f"Solo {len(encontrados_b)} de 3 brokers declarados en Compose ({encontrados_b}).")
    else:
        log_warn("No se detectaron brokers KRaft en compose.yml aún.")

    # Verificar CLUSTER_ID
    if "CLUSTER_ID" in compose_text:
        log_pass("CLUSTER_ID para quórum KRaft configurado en Compose.")
    else:
        log_warn("CLUSTER_ID de VidalStore no detectado en Compose.")


def audit_retroalimentacion_e1(root_dir):
    print(f"\n{C_BOLD}[5/6] Verificando correcciones específicas de la Retroalimentación E1...{C_RESET}")
    
    # 1. KAFKA_BROKERS sin fallback hardcodeado en licencias
    lic_prod_path = os.path.join(root_dir, "vidalstore-licencias", "src", "kafka", "kafka-productor.service.ts")
    if os.path.isfile(lic_prod_path):
        with open(lic_prod_path, "r", encoding="utf-8", errors="ignore") as f:
            lic_prod_code = f.read()
        if "broker-1:19092" in lic_prod_code:
            log_warn("[vidalstore-licencias] Detectada dirección de broker hardcodeada como respaldo en kafka-productor.service.ts. Debe leerse solo de .env (IE1).")
        else:
            log_pass("[vidalstore-licencias] kafka-productor.service.ts no tiene direcciones de brokers hardcodeadas.")
    
    # 2. .env.example en licencias
    lic_env_example = os.path.join(root_dir, "vidalstore-licencias", ".env.example")
    if os.path.isfile(lic_env_example):
        with open(lic_env_example, "r", encoding="utf-8", errors="ignore") as f:
            if "KAFKA_BROKERS" in f.read():
                log_pass("[vidalstore-licencias] .env.example incluye KAFKA_BROKERS.")
            else:
                log_warn("[vidalstore-licencias] .env.example NO incluye KAFKA_BROKERS (IE1).")

    # 3. Shutdown hooks en vidalstore-eventos
    eventos_main_path = os.path.join(root_dir, "vidalstore-eventos", "src", "main.ts")
    if os.path.isfile(eventos_main_path):
        with open(eventos_main_path, "r", encoding="utf-8", errors="ignore") as f:
            eventos_main_code = f.read()
        if "enableShutdownHooks" in eventos_main_code:
            log_pass("[vidalstore-eventos] app.enableShutdownHooks() presente en main.ts.")
        else:
            log_warn("[vidalstore-eventos] Falta app.enableShutdownHooks() en main.ts (IE2).")

    # 4. Sobre de compra con juegoId en primer nivel
    dto_compra_path = os.path.join(root_dir, "vidalstore-licencias", "src", "kafka", "dto", "compra-evento.dto.ts")
    if os.path.isfile(dto_compra_path):
        with open(dto_compra_path, "r", encoding="utf-8", errors="ignore") as f:
            dto_compra_code = f.read()
        # Verificar clase CompraRealizadaEventoDto
        if "class CompraRealizadaEventoDto" in dto_compra_code:
            # Buscar si juegoId está en la clase
            match = re.search(r"class CompraRealizadaEventoDto.*?\{(.*?)\}", dto_compra_code, re.DOTALL)
            if match and "juegoId" in match.group(1):
                log_pass("[vidalstore-licencias] CompraRealizadaEventoDto incluye juegoId en el sobre de primer nivel.")
            else:
                log_warn("[vidalstore-licencias] CompraRealizadaEventoDto NO incluye juegoId en el sobre de primer nivel (IE4).")

    # 5. Higiene del script levantar.sh
    levantar_candidatos = [
        os.path.join(root_dir, "vidalstore-plataforma", "scripts", "levantar.sh"),
        os.path.join(root_dir, "vidalstore-plataforma", "levantar.sh"),
        os.path.join(root_dir, "levantar.sh"),
    ]
    for lev in levantar_candidatos:
        if os.path.isfile(lev):
            with open(lev, "r", encoding="utf-8", errors="ignore") as f:
                lev_code = f.read()
            rel = os.path.relpath(lev, root_dir)
            if "kill -9" in lev_code or "kill -15" in lev_code:
                log_warn(f"[{rel}] Contiene kill -9 o kill -15 sobre procesos del host (peligroso para equipo docente).")
            else:
                log_pass(f"[{rel}] No contiene llamadas agresivas a kill -9/kill -15.")


def audit_nube_y_red(root_dir):
    print(f"\n{C_BOLD}[6/6] Verificando evidencias de Nube y Red (E2 preventivo)...{C_RESET}")
    red_md_path = os.path.join(root_dir, "vidalstore-plataforma", "docs", "red.md")
    if os.path.isfile(red_md_path):
        with open(red_md_path, "r", encoding="utf-8", errors="ignore") as f:
            red_text = f.read()
        # buscar placeholders tipo <...>
        placeholders = re.findall(r"<[A-Za-z0-9_-]+>", red_text)
        if placeholders:
            log_warn(f"[vidalstore-plataforma/docs/red.md] Conserva placeholders de ejemplo: {set(placeholders)}")
        else:
            log_pass("[vidalstore-plataforma/docs/red.md] Sin placeholders residuales <...>.")
    
    azure_region_path = os.path.join(root_dir, "vidalstore-plataforma", "deploy", "azure", "region.txt")
    if os.path.isfile(azure_region_path):
        with open(azure_region_path, "r", encoding="utf-8", errors="ignore") as f:
            azure_text = f.read()
        if "Standard_B2ats_v2" in azure_text or "Standard_B2als_v2" in azure_text:
            log_pass("[deploy/azure/region.txt] Contiene verificación de SKUs Standard_B2ats_v2 / B2als_v2.")
        else:
            log_warn("[deploy/azure/region.txt] Falta salida de 'az vm list-skus' para verificar Standard_B2ats_v2 y Standard_B2als_v2.")



def audit_topics_script(root_dir):
    print(f"\n{C_BOLD}[4/6] Verificando script de topología y topics de VidalStore...{C_RESET}")
    rutas_script = [
        os.path.join(root_dir, "kafka", "topics.sh"),
        os.path.join(root_dir, "vidalstore-plataforma", "kafka", "topics.sh"),
        os.path.join(root_dir, "scripts", "topics.sh"),
    ]

    encontrado = None
    for r in rutas_script:
        if os.path.isfile(r):
            encontrado = r
            break

    if not encontrado:
        log_warn("Archivo topics.sh no encontrado en rutas estándar (requerido para E1).")
        return

    log_pass(f"Script de topics localizado en: {os.path.relpath(encontrado, root_dir)}")

    # Verificar fin de línea CRLF
    with open(encontrado, "rb") as f:
        bytes_data = f.read()
    if b"\r" in bytes_data:
        log_fail("El script topics.sh contiene retornos de carro CRLF (\\r). Ejecutar: sed -i 's/\\r$//' topics.sh")
    else:
        log_pass("El script topics.sh utiliza saltos de línea limpios LF.")

    # Verificar topics declarados
    text = bytes_data.decode("utf-8", errors="ignore")
    for t in TOPICS_REQUERIDOS:
        if t in text:
            log_pass(f"Topic [{t}] declarado en topics.sh.")
        else:
            log_warn(f"Topic obligatorio [{t}] no encontrado en topics.sh.")

    if "cleanup.policy=compact" in text:
        log_pass("Política de compactación (cleanup.policy=compact) configurada para vidalstore.catalogo.")
    else:
        log_warn("No se detectó configuración de compactación (cleanup.policy=compact).")


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    print(f"{C_BOLD}{C_CYAN}======================================================================{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}   VIDALSTORE - AUDITOR AUTOMATIZADO DE UNIDAD 3 / EP3 (DSY1107)      {C_RESET}")
    print(f"{C_BOLD}{C_CYAN}======================================================================{C_RESET}")
    print(f"Directorio Raíz: {root_dir}")

    audit_gitattributes(root_dir)
    audit_kafka_dependencies(root_dir)
    audit_kraft_compose(root_dir)
    audit_topics_script(root_dir)
    audit_retroalimentacion_e1(root_dir)
    audit_nube_y_red(root_dir)

    print(f"\n{C_BOLD}{C_CYAN}======================================================================{C_RESET}")
    print(f"{C_BOLD}Resumen de Auditoría EP3:{C_RESET}")
    print(f"  Total Validaciones: {TOTAL_CHECKS}")
    print(f"  {C_GREEN}Exitosas (PASS):   {PASSED_CHECKS}{C_RESET}")
    print(f"  {C_YELLOW}Advertencias (WARN): {WARNING_CHECKS}{C_RESET}")
    print(f"  {C_RED}Fallidas (FAIL):     {FAILED_CHECKS}{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}======================================================================{C_RESET}\n")

    if FAILED_CHECKS > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
