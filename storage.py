"""
Almacenamiento de vacantes notificadas usando JSON (compatible con GitHub Actions).
"""
import json
import logging
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

# Archivo JSON para persistir datos
DATA_FILE = Path(__file__).parent / "data" / "vacantes_notificadas.json"


def inicializar_db():
    """Crea el archivo JSON si no existe."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({
            "vacantes_notificadas": {},
            "log_consultas": []
        }, indent=2))
        logger.info("Archivo de datos inicializado")


def _cargar_datos() -> dict:
    """Carga los datos del archivo JSON."""
    if not DATA_FILE.exists():
        return {"vacantes_notificadas": {}, "log_consultas": []}
    return json.loads(DATA_FILE.read_text())


def _guardar_datos(datos: dict):
    """Guarda los datos en el archivo JSON."""
    DATA_FILE.write_text(json.dumps(datos, indent=2, ensure_ascii=False))


def vacante_ya_notificada(vacante_id: str) -> bool:
    """Verifica si una vacante ya fue notificada."""
    datos = _cargar_datos()
    return vacante_id in datos["vacantes_notificadas"]


def marcar_como_notificada(vacante_id: str, cargo: str, area: str, nivel: str):
    """Marca una vacante como notificada."""
    datos = _cargar_datos()
    datos["vacantes_notificadas"][vacante_id] = {
        "cargo": cargo,
        "area": area,
        "nivel": nivel,
        "fecha_notificacion": datetime.now().isoformat()
    }
    _guardar_datos(datos)
    logger.debug(f"Vacante {vacante_id} marcada como notificada")


def filtrar_nuevas(vacantes: list) -> list:
    """Filtra vacantes, retornando solo las no notificadas."""
    nuevas = []
    for v in vacantes:
        if not vacante_ya_notificada(v.id):
            nuevas.append(v)

    logger.info(f"De {len(vacantes)} vacantes, {len(nuevas)} son nuevas")
    return nuevas


def registrar_consulta(total_encontradas: int, nuevas: int, estado: str = "OK"):
    """Registra una consulta en el log."""
    datos = _cargar_datos()
    datos["log_consultas"].append({
        "fecha": datetime.now().isoformat(),
        "total_encontradas": total_encontradas,
        "nuevas": nuevas,
        "estado": estado
    })
    # Mantener solo las últimas 100 consultas
    datos["log_consultas"] = datos["log_consultas"][-100:]
    _guardar_datos(datos)


def obtener_estadisticas() -> dict:
    """Obtiene estadísticas del sistema."""
    datos = _cargar_datos()
    return {
        "total_notificadas": len(datos["vacantes_notificadas"]),
        "ultima_consulta": datos["log_consultas"][-1] if datos["log_consultas"] else None,
        "total_consultas": len(datos["log_consultas"]),
    }


def limpiar_antiguas(dias: int = 30):
    """Elimina registros de vacantes más antiguas que X días."""
    from datetime import timedelta

    datos = _cargar_datos()
    ahora = datetime.now()
    limite = ahora - timedelta(days=dias)

    vacantes_actuales = {}
    eliminadas = 0

    for vid, info in datos["vacantes_notificadas"].items():
        fecha = datetime.fromisoformat(info["fecha_notificacion"])
        if fecha > limite:
            vacantes_actuales[vid] = info
        else:
            eliminadas += 1

    if eliminadas:
        datos["vacantes_notificadas"] = vacantes_actuales
        _guardar_datos(datos)
        logger.info(f"Eliminadas {eliminadas} vacantes antiguas (>{dias} días)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("Inicializando almacenamiento...")
    inicializar_db()

    print("\nEstadísticas:")
    stats = obtener_estadisticas()
    for k, v in stats.items():
        print(f"  {k}: {v}")
