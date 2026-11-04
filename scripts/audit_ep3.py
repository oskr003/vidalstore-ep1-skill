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
    print(f"\n{C_BOLD}[3/4] Verificando configuración KRaft en Docker Compose...{C_RESET}")
    compose_path = os.path.join(root_dir, "compose.yml")
    if not os.path.isfile(compose_path):
        compose_path = os.path.join(root_dir, "docker-compose.yml")

    if not os.path.isfile(compose_path):
        log_warn("compose.yml no encontrado en la raíz.")
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
        log_warn("No se detectaron controllers KRaft en compose.yml aún (preparado para hito E1).")

    if len(encontrados_b) == 3:
        log_pass("Los 3 brokers KRaft están declarados en Compose.")
    elif len(encontrados_b) > 0:
        log_warn(f"Solo {len(encontrados_b)} de 3 brokers declarados en Compose ({encontrados_b}).")
    else:
        log_warn("No se detectaron brokers KRaft en compose.yml aún (preparado para hito E1).")

    # Verificar CLUSTER_ID
    if "VmlkYWxTdG9yZS1LYWZrYQ" in compose_text:
        log_pass("CLUSTER_ID oficial de VidalStore configurado (VmlkYWxTdG9yZS1LYWZrYQ).")
    else:
        log_warn("CLUSTER_ID de VidalStore (VmlkYWxTdG9yZS1LYWZrYQ) no detectado en Compose.")


def audit_topics_script(root_dir):
    print(f"\n{C_BOLD}[4/4] Verificando script de topología y topics de VidalStore...{C_RESET}")
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
