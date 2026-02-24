"""
Monitor de Vacantes Docentes ABC - Patagones

Consulta periódicamente la API del portal ABC buscando vacantes docentes
que coincidan con los códigos de habilitación de la oblea.
"""
import logging
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config
from api_client import APIClient, filtrar_por_codigos
from oblea_parser import obtener_codigos_habilitados
from storage import (
    inicializar_db,
    filtrar_nuevas,
    marcar_como_notificada,
    registrar_consulta,
    obtener_estadisticas,
    limpiar_antiguas,
)
from notifier import enviar_email

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def verificar_vacantes():
    """
    Tarea principal: busca vacantes, filtra y notifica.
    """
    logger.info("=" * 50)
    logger.info("Iniciando verificación de vacantes...")
    logger.info(f"Distrito: {config.DISTRITO}")
    logger.info(f"Niveles: {config.NIVELES}")

    try:
        # 1. Obtener códigos de la oblea
        codigos = obtener_codigos_habilitados()
        if codigos:
            logger.info(f"Códigos de oblea: {codigos}")
        else:
            logger.warning("No se encontraron códigos de oblea, se mostrarán todas las vacantes")

        # 2. Consultar API
        client = APIClient()
        vacantes = client.buscar_vacantes()

        if not vacantes:
            logger.info("No se encontraron vacantes publicadas")
            registrar_consulta(0, 0, "OK - Sin vacantes")
            return

        # 3. Filtrar por códigos de oblea (si hay)
        if codigos:
            vacantes_filtradas = filtrar_por_codigos(vacantes, codigos)
        else:
            vacantes_filtradas = vacantes

        if not vacantes_filtradas:
            logger.info("No hay vacantes que coincidan con tus códigos de oblea")
            registrar_consulta(len(vacantes), 0, "OK - Sin coincidencias")
            return

        # 4. Filtrar solo las nuevas (no notificadas)
        nuevas = filtrar_nuevas(vacantes_filtradas)

        if not nuevas:
            logger.info("No hay vacantes nuevas desde la última consulta")
            registrar_consulta(len(vacantes), 0, "OK - Sin nuevas")
            return

        # 5. Notificar por email
        logger.info(f"Encontradas {len(nuevas)} vacantes nuevas!")
        if enviar_email(nuevas):
            # Marcar como notificadas solo si el email se envió
            for v in nuevas:
                marcar_como_notificada(v.id, v.cargo, v.area_incumbencia, v.nivel_modalidad)
            registrar_consulta(len(vacantes), len(nuevas), "OK")
        else:
            registrar_consulta(len(vacantes), len(nuevas), "ERROR - Email no enviado")

    except Exception as e:
        logger.error(f"Error en verificación: {e}", exc_info=True)
        registrar_consulta(0, 0, f"ERROR - {str(e)[:100]}")


def ejecutar_una_vez():
    """Ejecuta una verificación única (sin scheduler)."""
    inicializar_db()
    verificar_vacantes()


def iniciar_scheduler():
    """Inicia el scheduler para ejecución periódica."""
    logger.info("Iniciando Monitor de Vacantes Docentes ABC")
    logger.info(f"Intervalo de verificación: cada {config.CHECK_INTERVAL_HOURS} horas")

    # Inicializar base de datos
    inicializar_db()

    # Limpiar registros antiguos (más de 30 días)
    limpiar_antiguas(30)

    # Mostrar estadísticas
    stats = obtener_estadisticas()
    logger.info(f"Estadísticas: {stats}")

    # Ejecutar una vez al inicio
    verificar_vacantes()

    # Configurar scheduler
    scheduler = BlockingScheduler()
    scheduler.add_job(
        verificar_vacantes,
        trigger=IntervalTrigger(hours=config.CHECK_INTERVAL_HOURS),
        id="verificar_vacantes",
        name="Verificar vacantes docentes",
        replace_existing=True,
    )

    # Limpiar registros antiguos una vez al día
    scheduler.add_job(
        lambda: limpiar_antiguas(30),
        trigger=IntervalTrigger(days=1),
        id="limpiar_antiguos",
        name="Limpiar registros antiguos",
    )

    logger.info("Scheduler iniciado. Presiona Ctrl+C para detener.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Deteniendo scheduler...")
        scheduler.shutdown()


def mostrar_ayuda():
    """Muestra ayuda de uso."""
    print("""
Monitor de Vacantes Docentes ABC - Patagones
=============================================

Uso:
    python main.py              Inicia el monitor con scheduler (cada 6 horas)
    python main.py --once       Ejecuta una verificación única y termina
    python main.py --test       Envía un email de prueba
    python main.py --stats      Muestra estadísticas del sistema

Configuración:
    1. Copia .env.example a .env y completa las variables
    2. Coloca tu oblea.pdf en el directorio o crea codigos.txt con tus códigos

Más info:
    - EMAIL_FROM: Tu email de Gmail
    - EMAIL_PASSWORD: App Password de Gmail (no tu contraseña normal)
    - EMAIL_TO: Email donde recibir notificaciones
    """)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ["--help", "-h"]:
            mostrar_ayuda()

        elif arg == "--once":
            ejecutar_una_vez()

        elif arg == "--test":
            from notifier import enviar_test
            enviar_test()

        elif arg == "--stats":
            inicializar_db()
            stats = obtener_estadisticas()
            print("\nEstadísticas del Monitor:")
            print("-" * 30)
            for k, v in stats.items():
                print(f"  {k}: {v}")

        else:
            print(f"Argumento desconocido: {arg}")
            mostrar_ayuda()
    else:
        iniciar_scheduler()
