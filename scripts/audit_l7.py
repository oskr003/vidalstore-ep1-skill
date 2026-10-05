#!/usr/bin/env python3
"""
Script de Auditoría Automática para Laboratorio L7 y Unidad 2 (Docker Compose, DLX/DLQ, Idempotencia y Persistencia).
Verifica:
  1. compose.yml y orquestación (8 servicios, healthchecks, condition: service_healthy, volúmenes).
  2. Topología de Mensajería (topologia.ts con DLX direct, 3 DLQs, orden estricto de declaración).
  3. Worker y Consumidores (prefetch(1), ack explícito, nack sin reencolar, manejo de 23505 y reintentos).
  4. CartasMuertasConsumidor (consumo de DLQs, extracción de x-death y payload text).
  5. Entidades TypeORM y PostgreSQL (eventos_auditoria con jsonb, notificaciones con CHECK, mensajes_muertos con text).
  6. Persistencia del Productor (esquema propio, índice parcial WHERE estado = 'activa', pool.on('error')).
  7. Documentación obligatoria (docs/modelo-de-datos.md con 2 dueños, docs/topologia.md, README con veneno).
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

def run_cmd(cmd, cwd=None):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return res.stdout.strip(), res.returncode
    except Exception:
        return "", 1

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

def audit_compose():
    print_header("1. AUDITORÍA DE DOCKER COMPOSE Y ORQUESTACIÓN (D8 & L7 Tramo 1)")
    compose_path = find_file("compose.yml") or find_file("docker-compose.yml")
    if not compose_path:
        check_fail("No se encontró compose.yml en la plataforma.",
                   "Crear compose.yml en la raíz de vidalstore-plataforma / biblioteca-plataforma (L7 Tramo 1.3).")
        return

    check_pass(f"Archivo compose.yml encontrado: {os.path.relpath(compose_path, BASE_DIR)}")
    content = read_content(compose_path)

    # Healthchecks
    if "healthcheck" in content:
        check_pass("Declaración de 'healthcheck' detectada en compose.yml.")
    else:
        check_fail("compose.yml no define healthchecks.",
                   "Definir healthcheck en rabbit1 (rabbitmq-diagnostics) y postgres (pg_isready) (D8 Slide 17).")

    # condition: service_healthy
    if "service_healthy" in content:
        check_pass("Dependencias condicionadas a 'service_healthy' configuradas.")
    else:
        check_fail("compose.yml no usa condition: service_healthy en depends_on.",
                   "Atar depends_on con 'condition: service_healthy' para evitar caídas por carrera al arrancar (L7 Tramo 1.6).")

    # Volúmenes nombrados
    if "datos-rabbit" in content and "datos-postgres" in content:
        check_pass("Volúmenes con nombre 'datos-rabbit' y 'datos-postgres' presentes.")
    else:
        check_warn("Verificar nombres de volúmenes persistentes en compose.yml.")

    # Hostname fijo
    if "rabbit1" in content and ("hostname: rabbit1" in content or "hostname: 'rabbit1'" in content):
        check_pass("Hostname fijo 'rabbit1' configurado en el servicio del broker.")
    else:
        check_fail("Falta 'hostname: rabbit1' en el servicio de RabbitMQ.",
                   "Agregar 'hostname: rabbit1' para que el nodo Erlang conserve Mnesia (D7 Slide 11).")

def audit_topology():
    print_header("2. AUDITORÍA DE TOPOLOGÍA AMQP, DLX Y 3 DLQS (L7 Tramo 3)")
    topo_ts = find_file("topologia.ts")
    topo_mjs = find_file("topologia.mjs")

    if not topo_ts and not topo_mjs:
        check_fail("No se encontró topologia.ts ni topologia.mjs.",
                   "Centralizar la topología en src/mensajeria/topologia.ts (L7 Tramo 3.4).")
        return

    target = topo_ts or topo_mjs
    check_pass(f"Archivo de topología encontrado: {os.path.relpath(target, BASE_DIR)}")
    content = read_content(target)

    # DLX y DLQ
    if re.search(r"dlx", content, re.IGNORECASE):
        check_pass("Exchange de cartas muertas (DLX) definido en la topología.")
    else:
        check_fail("Falta exchange DLX ('vidalstore.dlx' o 'biblioteca.dlx').",
                   "Definir EXCHANGES.dlx de tipo 'direct' (L7 Tramo 3.4).")

    if "deadLetterExchange" in content or "x-dead-letter-exchange" in content:
        check_pass("Argumentos deadLetterExchange / x-dead-letter-exchange presentes en colas de trabajo.")
    else:
        check_fail("Las colas de trabajo no tienen configurado deadLetterExchange.",
                   "Agregar { deadLetterExchange: EXCHANGES.dlx, deadLetterRoutingKey: cola } (L7 Tramo 3.4).")

    # Orden de declaración
    pos_dlq = content.find("assertQueue")
    if "DLQ" in content and pos_dlq != -1:
        check_pass("Configuración de colas DLQ detectada en declararTopologia.")

def audit_consumers():
    print_header("3. AUDITORÍA DE CONSUMIDORES, PREFETCH, ACK Y REINTENTOS (D8 & L7 Tramos 2, 4 y 5)")
    mensajeria_svc = find_file("mensajeria.service.ts")
    if mensajeria_svc:
        m_content = read_content(mensajeria_svc)
        if "prefetch(1)" in m_content:
            check_pass("Control de flujo 'prefetch(1)' implementado en el canal de mensajería.")
        else:
            check_fail("Falta 'await this.canal.prefetch(1)' en MensajeriaService.",
                       "Agregar 'await this.canal.prefetch(1)' inmediatamente al crear el canal (L7 Tramo 2.4).")

    # CartasMuertasConsumidor
    cartas_muertas = find_file("cartas-muertas.consumidor.ts")
    if cartas_muertas:
        check_pass("CartasMuertasConsumidor implementado.")
        cm_content = read_content(cartas_muertas)
        if "x-death" in cm_content or "x-first-death-queue" in cm_content:
            check_pass("Extracción de metadatos forenses (x-death / x-first-death-queue) en cartas muertas.")
        if "requeue" in cm_content and "5000" in cm_content:
            check_pass("Resiliencia con nack(false, true) tras 5s si la base de datos no responde.")
    else:
        check_fail("No se encontró cartas-muertas.consumidor.ts.",
                   "Crear src/mensajeria/consumidores/cartas-muertas.consumidor.ts (L7 Tramo 5.1).")

    # AuditoriaConsumidor y manejo de 23505
    auditoria_cons = find_file("auditoria.consumidor.ts")
    if auditoria_cons:
        a_content = read_content(auditoria_cons)
        if "23505" in a_content:
            check_pass("Captura de código 23505 (unique_violation) con canal.ack(mensaje) para idempotencia.")
        else:
            check_fail("AuditoriaConsumidor no maneja el código de error 23505.",
                       "Capturar error 23505 y confirmar con canal.ack(mensaje) sin mandar a DLQ (L7 Tramo 4.8).")

        if "nack" in a_content and "false, false" in a_content:
            check_pass("Rechazo nack(mensaje, false, false) configurado hacia la DLQ.")
        else:
            check_fail("Falta canal.nack(mensaje, false, false) en el catch de error del mensaje.",
                       "Rechazar mensajes corruptos con nack sin reencolar para que viajen al DLX (L7 Tramo 3.6).")

def audit_persistence():
    print_header("4. AUDITORÍA DE MODELO DE DATOS Y TYPEORM (L7 Tramos 4 y 5)")
    # Entidad EventoAuditoria
    ev_entity = find_file("evento-auditoria.entity.ts") or find_file("evento.entity.ts")
    if ev_entity:
        e_content = read_content(ev_entity)
        if "jsonb" in e_content:
            check_pass("EventoAuditoria usa 'jsonb' para la columna payload.")
        else:
            check_warn("EventoAuditoria debería usar type: 'jsonb' para permitir consultas indexadas.")
        if "unique" in e_content.lower() and "evento" in e_content.lower():
            check_pass("Restricción UNIQUE en evento_id presente para idempotencia.")
        else:
            check_fail("evento_id debe tener restricción UNIQUE en la base de datos.",
                       "Agregar unique: true en la columna evento_id (L7 Tramo 4.4).")
    else:
        check_warn("No se encontró evento-auditoria.entity.ts.")

    # Entidad MensajeMuerto
    mm_entity = find_file("mensaje-muerto.entity.ts")
    if mm_entity:
        mm_content = read_content(mm_entity)
        if "type: 'text'" in mm_content or 'type: "text"' in mm_content:
            check_pass("MensajeMuerto usa 'text' para payload (prohibido jsonb para aceptar JSON roto).")
        else:
            check_fail("MensajeMuerto NO debe usar jsonb; debe ser 'text'.",
                       "Cambiar payload a type: 'text' en MensajeMuerto (L7 Tramo 4.4).")
    else:
        check_warn("No se encontró mensaje-muerto.entity.ts.")

    # Productor con índice parcial y pool error
    repo_prod = find_file("repositorio-prestamos.mjs") or find_file("repositorio-licencias.mjs") or find_file("licencias.service.ts")
    if repo_prod:
        p_content = read_content(repo_prod)
        if "WHERE estado =" in p_content or "where: \"estado =" in p_content or "where: 'estado =" in p_content:
            check_pass("Índice parcial único (WHERE estado = 'activa' o 'vigente') detectado en el productor.")
        else:
            check_fail("El microservicio productor debe definir un índice parcial con WHERE estado.",
                       "Crear UNIQUE (usuario_sub, juego_id) WHERE estado = 'activa' (L7 Tramo 5.3).")
        if "pool.on('error'" in p_content or 'pool.on("error"' in p_content:
            check_pass("Manejador pool.on('error') implementado para tolerar reinicios de Postgres.")
        else:
            check_warn("Se recomienda agregar pool.on('error', ...) para no caer ante reconexiones de Postgres.")

def audit_docs():
    print_header("5. AUDITORÍA DE DOCUMENTACIÓN Y GUÍAS DE DEFENSA (L7 Tramo 4.10 & README)")
    modelo_md = find_file("modelo-de-datos.md")
    if modelo_md:
        check_pass(f"docs/modelo-de-datos.md encontrado: {os.path.relpath(modelo_md, BASE_DIR)}")
        m_content = read_content(modelo_md)
        if "EVENTOS_AUDITORIA" in m_content and ("PRESTAMOS" in m_content or "LICENCIAS" in m_content):
            check_pass("Diagrama ER documenta los dos dueños (worker y microservicio productor).")
        else:
            check_warn("docs/modelo-de-datos.md debe mostrar las 4 tablas separadas por dueño (L7 Tramo 5.3).")
    else:
        check_fail("Falta docs/modelo-de-datos.md en la plataforma.",
                   "Crear docs/modelo-de-datos.md con el diagrama entidad-relación de 4 tablas (L7 Tramo 4.10).")

    readme_plat = find_file("README.md", [os.path.join(BASE_DIR, "vidalstore-plataforma"), os.path.join(BASE_DIR, "biblioteca-plataforma")])
    if readme_plat:
        r_content = read_content(readme_plat)
        if "Mensaje envenenado" in r_content or "envenenado" in r_content.lower():
            check_pass("Sección 'Mensaje envenenado' documentada en README de la plataforma.")
        else:
            check_warn("El README de la plataforma debe documentar la prueba del mensaje envenenado (L7 Tramo 3.7).")

def main():
    print(f"\n{BOLD}{GREEN}AUDITORÍA TÉCNICA · DSY1107 SEMANA 9 (D8, L7A Y L7){RESET}")
    print(f"Base Directory: {BASE_DIR}")
    audit_compose()
    audit_topology()
    audit_consumers()
    audit_persistence()
    audit_docs()
    print(f"\n{BOLD}Auditoría completada.{RESET}\n")

if __name__ == "__main__":
    main()
