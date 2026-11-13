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
    print(f"\n{C_BOLD}[1/8] Verificando .gitattributes e higiene EOL en repositorios...{C_RESET}")
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
    print(f"\n{C_BOLD}[2/8] Verificando dependencias de Kafka en repositorios Node.js...{C_RESET}")
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
    print(f"\n{C_BOLD}[3/8] Verificando configuración KRaft en Docker Compose...{C_RESET}")
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
    print(f"\n{C_BOLD}[5/8] Verificando correcciones específicas de la Retroalimentación E1...{C_RESET}")
    
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
            # Buscar el bloque de la clase CompraRealizadaEventoDto
            match = re.search(r"class CompraRealizadaEventoDto\b.*?(?=export class|\Z)", dto_compra_code, re.DOTALL)
            if match and "juegoId" in match.group(0):
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
    print(f"\n{C_BOLD}[6/8] Verificando evidencias de Nube y Red (E2 preventivo)...{C_RESET}")
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
    print(f"\n{C_BOLD}[4/8] Verificando script de topología y topics de VidalStore...{C_RESET}")
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

    if "min.insync.replicas=2" in text:
        log_pass("min.insync.replicas=2 configurado en topics.sh (D13 / L10).")
    else:
        log_warn("No se detectó min.insync.replicas=2 en topics.sh (requerido con replication-factor=3 y acks=all).")


def audit_e2_streaming_y_panel(root_dir):
    print(f"\n{C_BOLD}[7/8] Verificando arquitectura de Consumer Groups, Idempotencia y Panel en Vivo (L10 E2)...{C_RESET}")
    streaming_dir = os.path.join(root_dir, "vidalstore-eventos", "src", "streaming")
    if os.path.isdir(streaming_dir):
        negocio_files = []
        for r, _, files in os.walk(streaming_dir):
            for f in files:
                if f.endswith(".negocio.ts"):
                    negocio_files.append(os.path.join(r, f))
        if negocio_files:
            violaciones_kafka = []
            for nf in negocio_files:
                with open(nf, "r", encoding="utf-8", errors="ignore") as fh:
                    code = fh.read()
                if "@platformatic/kafka" in code:
                    violaciones_kafka.append(os.path.relpath(nf, root_dir))
                if re.search(r"UPDATE\s+\w+.*RETURNING", code, re.IGNORECASE | re.DOTALL) and "WITH " not in code.upper():
                    log_warn(f"[{os.path.relpath(nf, root_dir)}] Usa UPDATE ... RETURNING sin CTE 'WITH ... SELECT' (trampa de TypeORM L10 §1.7).")
            if violaciones_kafka:
                log_fail(f"Clases *.negocio.ts importan @platformatic/kafka (viola separación IE5): {violaciones_kafka}")
            else:
                log_pass(f"Las {len(negocio_files)} clases *.negocio.ts están desacopladas de Kafka (IE5).")
        else:
            log_warn("[vidalstore-eventos] Aún no se detectan archivos *.negocio.ts en src/streaming/.")
    else:
        log_warn("[vidalstore-eventos] Directorio src/streaming/ aún no creado para E2.")

    # Verificar que BFF no importe pg ni typeorm (Regla L10 Tramo 2)
    bff_pkg = os.path.join(root_dir, "vidalstore-bff", "package.json")
    if os.path.isfile(bff_pkg):
        try:
            with open(bff_pkg, "r", encoding="utf-8") as fh:
                pkg = json.load(fh)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "pg" in deps or "typeorm" in deps or "@nestjs/typeorm" in deps:
                log_fail("[vidalstore-bff] El BFF incluye dependencias de Postgres (pg/typeorm); debe consultar a vidalstore-eventos por HTTP.")
            else:
                log_pass("[vidalstore-bff] El BFF no tiene dependencias de Postgres (cumple arquitectura de Panel en Vivo L10).")
        except Exception:
            pass

    # Verificar docs/topics.md, docs/consumer-groups.md y docs/despliegue.md
    for doc_name in ["topics.md", "consumer-groups.md", "despliegue.md"]:
        doc_path = os.path.join(root_dir, "vidalstore-plataforma", "docs", doc_name)
        if os.path.isfile(doc_path):
            log_pass(f"[vidalstore-plataforma/docs/{doc_name}] Documento obligatorio de E2 presente.")
            if doc_name == "despliegue.md":
                with open(doc_path, "r", encoding="utf-8", errors="ignore") as dfh:
                    dcontent = dfh.read()
                # Verificar presencia de los 8 comandos requeridos por EP3 Entrega 2 pág. 9
                cmds_despliegue = [
                    ("describe-instances", "Comando #1 AWS (IPs privadas)"),
                    ("describe-security-groups", "Comando #2 AWS (filtro puerto 22)"),
                    ("kafka-metadata-quorum.sh", "Comando #3 AWS (quórum controllers 1, 2 y 3)"),
                    ("vidalstore.compras", "Comando #4 AWS (3 particiones con ISR 3)"),
                    ("vidalstore.actividad", "Comando #5 AWS (offsets 1751, 520 y 768)"),
                    ("api.ipify.org", "Comando #6 Azure (IP de salida por gw-azure)"),
                    ("route-table route list", "Comando #7 Azure (tabla de rutas privada a gw-azure)"),
                    ("powerState", "Comando #8 Azure (máquinas en estado deallocated)"),
                ]
                for token, label in cmds_despliegue:
                    if token in dcontent:
                        log_pass(f"[docs/despliegue.md] Incluye evidencia de: {label}.")
                    else:
                        log_warn(f"[docs/despliegue.md] Falta evidencia de: {label} (EP3 Entrega 2 pág. 9).")
        else:
            log_warn(f"[vidalstore-plataforma/docs/{doc_name}] Aún no existe (obligatorio para E2).")

    # Verificar repositorios.md (formato inalterable para script docente)
    repomd_path = os.path.join(root_dir, "vidalstore-plataforma", "docs", "repositorios.md")
    if os.path.isfile(repomd_path):
        with open(repomd_path, "r", encoding="utf-8", errors="ignore") as rfh:
            rcontent = rfh.read()
        if "SHA de main al entregar" in rcontent and "Comando: `bash levantar.sh`" in rcontent:
            log_pass("[vidalstore-plataforma/docs/repositorios.md] Formato normativo de E2 cumplido (script de corrección docente).")
        else:
            log_warn("[vidalstore-plataforma/docs/repositorios.md] Verificar cabeceras y tabla | Repositorio | URL | SHA de main al entregar | (EP3 E2 pág. 12).")


def audit_e2_ghcr_y_nube_l10(root_dir):
    print(f"\n{C_BOLD}[8/8] Verificando Dockerfiles Multi-Stage, Workflows GHCR y Reglas Cloud L10...{C_RESET}")
    servicios_con_imagen = [r for r in REPOS if r != "vidalstore-plataforma"]
    for repo in servicios_con_imagen:
        repo_dir = os.path.join(root_dir, repo)
        if not os.path.isdir(repo_dir):
            continue
        dockerfile = os.path.join(repo_dir, "Dockerfile")
        if os.path.isfile(dockerfile):
            with open(dockerfile, "r", encoding="utf-8", errors="ignore") as fh:
                df_text = fh.read()
            if "AS build" in df_text and ("USER node" in df_text or "nginx:" in df_text):
                log_pass(f"[{repo}] Dockerfile multi-stage válido (AS build + USER node / nginx).")
            else:
                log_warn(f"[{repo}] Dockerfile presente pero verificar multi-stage 'AS build' y 'USER node'.")

        wf_path = os.path.join(repo_dir, ".github", "workflows", "imagen.yml")
        if os.path.isfile(wf_path):
            with open(wf_path, "r", encoding="utf-8", errors="ignore") as fh:
                wf_text = fh.read()
            if ":latest" in wf_text:
                log_fail(f"[{repo}] imagen.yml publica con tag ':latest' (prohibido en E2; usar ${{GITHUB_SHA}}).")
            elif "GITHUB_SHA" in wf_text or "github.sha" in wf_text:
                log_pass(f"[{repo}] Workflow .github/workflows/imagen.yml etiqueta con SHA del commit.")

    # Verificar ASCII puro en cloud-init de Azure (trampa silenciosa L10 §6.3)
    azure_dir = os.path.join(root_dir, "vidalstore-plataforma", "deploy", "azure")
    if os.path.isdir(azure_dir):
        for fname in os.listdir(azure_dir):
            if fname.startswith("cloud-init") and fname.endswith(".yaml"):
                fpath = os.path.join(azure_dir, fname)
                with open(fpath, "rb") as fh:
                    raw = fh.read()
                non_ascii = [b for b in raw if b > 127]
                if non_ascii:
                    log_fail(f"[deploy/azure/{fname}] Contiene caracteres no ASCII (tildes/ñ). cloud-init en Azure descartará el archivo en silencio.")
                else:
                    log_pass(f"[deploy/azure/{fname}] 100% ASCII puro (seguro para cloud-init en Azure).")
                if fname == "cloud-init-gw-azure.yaml":
                    txt = raw.decode("utf-8", errors="ignore")
                    if "DOCKER-USER" in txt:
                        log_pass("[deploy/azure/cloud-init-gw-azure.yaml] Incluye regla iptables DOCKER-USER para permitir NAT con Docker.")
                    else:
                        log_warn("[deploy/azure/cloud-init-gw-azure.yaml] Falta regla iptables DOCKER-USER (Docker bloqueará el tráfico NAT de bff).")


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
    audit_e2_streaming_y_panel(root_dir)
    audit_e2_ghcr_y_nube_l10(root_dir)

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
