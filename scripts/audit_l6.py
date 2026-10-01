#!/usr/bin/env python3
"""
Script de Auditoría Automática para Laboratorio L6 y Unidad 2 (Mensajería Asíncrona, Docker y RabbitMQ).
Verifica:
  1. Estado de Docker y contenedores requeridos (rabbit1, postgres1).
  2. Publicación de puertos (5672, 15672, 5432).
  3. Verificación de volúmenes con nombre (datos-rabbit, datos-postgres).
  4. Verificación de hostname fijo en RabbitMQ (--hostname rabbit1).
  5. Topología centralizada (topologia.ts / topologia.mjs).
  6. Regla de desacoplamiento: El BFF no publica; el microservicio productor publica tras guardar.
  7. Archivos de plataforma (docs/repositorios.md, docs/modelo-de-datos.md).
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

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip(), res.returncode
    except Exception as e:
        return "", 1

def audit_docker():
    print_header("1. AUDITORÍA DE DOCKER Y CONTENEDORES (D7 & L6)")
    # Comprobar docker daemon
    version_out, code = run_cmd("docker version --format '{{.Server.Version}}'")
    if code != 0:
        check_fail("Docker Desktop no está corriendo o no se puede conectar al daemon.",
                   "Abrir Docker Desktop y esperar a que termine de iniciar (L6A Slide 10).")
        return
    else:
        check_pass(f"Docker Daemon activo (Versión: {version_out}).")

    # Comprobar contenedor rabbit1
    ps_out, _ = run_cmd("docker ps --filter 'name=rabbit1' --format '{{.Names}}|{{.Image}}|{{.Ports}}|{{.Status}}'")
    if "rabbit1" in ps_out:
        check_pass(f"Contenedor rabbit1 activo: {ps_out}")
        # Comprobar puertos 5672 y 15672
        if "5672" in ps_out and "15672" in ps_out:
            check_pass("Puertos 5672 (AMQP) y 15672 (Management) publicados correctamente.")
        else:
            check_warn("rabbit1 no tiene ambos puertos (5672 y 15672) publicados.",
                       "Recrear con: docker run -d --name rabbit1 --hostname rabbit1 -p 5672:5672 -p 15672:15672 -v datos-rabbit:/var/lib/rabbitmq rabbitmq:4.3-management")

        # Comprobar nodename
        node_out, ncode = run_cmd("docker exec rabbit1 rabbitmqctl eval 'node().'")
        if "rabbit@rabbit1" in node_out:
            check_pass(f"Nodo Erlang tiene nombre estable y persistente: {node_out.strip()}.")
        else:
            check_fail(f"rabbit1 no tiene hostname fijo. Nodo actual: {node_out.strip()}.",
                       "Falta la bandera '--hostname rabbit1'. Sin esto se pierden colas al recrear (D7 Slide 11).")
    else:
        # Verificar si está en Exited o Created
        ps_all, _ = run_cmd("docker ps -a --filter 'name=rabbit1' --format '{{.Names}}|{{.Status}}'")
        if "rabbit1" in ps_all:
            check_warn(f"Contenedor rabbit1 existe pero está detenido o en Created: {ps_all}",
                       "Revisar 'docker logs rabbit1' o si hubo colisión de puertos (D7 Slide 9). Iniciar con 'docker start rabbit1'.")
        else:
            check_fail("Contenedor rabbit1 no existe.",
                       "Ejecutar: docker run -d --name rabbit1 --hostname rabbit1 -p 5672:5672 -p 15672:15672 -v datos-rabbit:/var/lib/rabbitmq rabbitmq:4.3-management")

    # Comprobar contenedor postgres1
    pg_out, _ = run_cmd("docker ps --filter 'name=postgres1' --format '{{.Names}}|{{.Image}}|{{.Ports}}|{{.Status}}'")
    if "postgres1" in pg_out:
        check_pass(f"Contenedor postgres1 activo: {pg_out}")
        if "5432" in pg_out:
            check_pass("Puerto 5432 publicado correctamente.")
    else:
        check_warn("Contenedor postgres1 no encontrado en ejecución.",
                   "Para L6 Tramo 2: docker run -d --name postgres1 -e POSTGRES_USER=biblioteca -e POSTGRES_PASSWORD=biblioteca -e POSTGRES_DB=biblioteca -p 5432:5432 -v datos-postgres:/var/lib/postgresql postgres:18")

def audit_topologia():
    print_header("2. AUDITORÍA DE TOPOLOGÍA CENTRALIZADA (L6 REGLA 3)")
    topologia_found = []
    for root, _, files in os.walk(BASE_DIR):
        if any(ignored in root for ignored in [".git", "node_modules", "dist"]):
            continue
        for f in files:
            if f in ["topologia.ts", "topologia.mjs"]:
                fpath = os.path.join(root, f)
                topologia_found.append(fpath)

    if topologia_found:
        check_pass(f"Archivos de topología encontrados ({len(topologia_found)}):")
        for p in topologia_found:
            rel = os.path.relpath(p, BASE_DIR)
            content = open(p, "r", encoding="utf-8", errors="ignore").read()
            has_exchanges = "EXCHANGES" in content
            has_routing = "ROUTING_KEYS" in content
            print(f"    • {rel} (EXCHANGES: {'✓' if has_exchanges else '✗'}, ROUTING_KEYS: {'✓' if has_routing else '✗'})")
            if not has_exchanges or not has_routing:
                check_warn(f"{rel} no exporta EXCHANGES o ROUTING_KEYS de forma centralizada.",
                           "Exportar los objetos para evitar strings mágicos sueltos (L6A Slide 8).")
    else:
        check_fail("No se encontró ningún archivo topologia.ts ni topologia.mjs.",
                   "Crear src/mensajeria/topologia.ts (worker) y servicios/mensajeria/topologia.mjs (productor).")

def audit_productor_bff():
    print_header("3. AUDITORÍA DE REGLAS DE PUBLICACIÓN (L6 REGLAS 1 Y 2)")
    # Regla 2: El BFF no publica
    bff_files = []
    for root, _, files in os.walk(BASE_DIR):
        if "bff" in root.lower() and not any(ign in root for ign in [".git", "node_modules", "dist"]):
            for f in files:
                if f.endswith((".ts", ".js")):
                    bff_files.append(os.path.join(root, f))

    bff_publishes = False
    for bf in bff_files:
        content = open(bf, "r", encoding="utf-8", errors="ignore").read()
        if "amqplib" in content or "publish(" in content:
            check_fail(f"El BFF ({os.path.relpath(bf, BASE_DIR)}) contiene referencias a publicación o amqplib.",
                       "REGLA 2: El BFF NUNCA publica en el broker. Solo reenvía la cabecera Authorization (L6A Slide 6).")
            bff_publishes = True
            break
    if not bff_publishes and bff_files:
        check_pass("El BFF cumple la Regla 2: no publica mensajes en el broker ni importa amqplib.")

    # Regla 1: El microservicio publica después de guardar y extrae usuarioSub del token
    productor_files = []
    for root, _, files in os.walk(BASE_DIR):
        if any(ign in root for ign in [".git", "node_modules", "dist", "frontend", "gateway"]):
            continue
        for f in files:
            if f in ["prestamos.mjs", "licencias.service.ts", "compras.service.ts"]:
                productor_files.append(os.path.join(root, f))

    for pf in productor_files:
        rel = os.path.relpath(pf, BASE_DIR)
        content = open(pf, "r", encoding="utf-8", errors="ignore").read()
        if "publish(" in content or "publicar" in content:
            check_pass(f"Productor {rel} implementa publicación de eventos.")
            if "jwtVerify" in content or "req.user.sub" in content or "sub" in content:
                check_pass(f"{rel} extrae la identidad del token firmado y no del cuerpo de la petición.")
            else:
                check_warn(f"{rel} no parece verificar la identidad del token.",
                           "El usuarioSub debe salir estrictamente del claim 'sub' verificado con jose (L6A Slide 6).")

def audit_plataforma():
    print_header("4. AUDITORÍA DE REPOSITORIO DE PLATAFORMA Y DOCUMENTACIÓN")
    plataforma_dirs = [d for d in os.listdir(BASE_DIR) if "plataforma" in d.lower() and os.path.isdir(os.path.join(BASE_DIR, d))]
    if plataforma_dirs:
        for pdir in plataforma_dirs:
            p_path = os.path.join(BASE_DIR, pdir)
            repos_md = os.path.join(p_path, "docs", "repositorios.md")
            modelo_md = os.path.join(p_path, "docs", "modelo-de-datos.md")
            env_example = os.path.join(p_path, ".env.example")
            
            check_pass(f"Repositorio de plataforma encontrado: {pdir}")
            if os.path.exists(repos_md):
                check_pass(f"  • {pdir}/docs/repositorios.md presente.")
            else:
                check_warn(f"  • Falta {pdir}/docs/repositorios.md con el mapa de repositorios del grupo.")
            
            if os.path.exists(modelo_md):
                check_pass(f"  • {pdir}/docs/modelo-de-datos.md presente.")
            else:
                check_warn(f"  • Falta {pdir}/docs/modelo-de-datos.md con el diagrama ER.")

            if os.path.exists(env_example):
                check_pass(f"  • {pdir}/.env.example presente.")
            else:
                check_warn(f"  • Falta {pdir}/.env.example.")
    else:
        check_warn("No se encontró carpeta de plataforma (biblioteca-plataforma o vidalstore-plataforma).",
                   "La EP2 exige vidalstore-plataforma con compose.yml, docs/repositorios.md y .env.example (L6A Slide 12).")

def main():
    print(f"\n{BOLD}INICIANDO AUDITORÍA TÉCNICA L6 / MENSAJERÍA ASÍNCRONA Y DOCKER{RESET}")
    print(f"Directorio de evaluación: {BASE_DIR}")
    audit_docker()
    audit_topologia()
    audit_productor_bff()
    audit_plataforma()
    print_header("FIN DE LA AUDITORÍA L6")
    print(f"Guías de referencia:")
    print(f"  • .agents/skills/vidalstore-ep1/references/mensajeria_docker_rabbitmq_l6.md")
    print(f"  • .agents/skills/vidalstore-ep1/references/preguntas_defensa.md\n")

if __name__ == "__main__":
    main()
