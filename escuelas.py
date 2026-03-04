"""
Mapeo de códigos de escuela a nombres completos.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache del mapeo
_escuelas_cache: dict = {}


def cargar_escuelas() -> dict:
    """Carga el mapeo de escuelas desde el archivo JSON."""
    global _escuelas_cache

    if _escuelas_cache:
        return _escuelas_cache

    archivo = Path(__file__).parent / "data" / "escuelas_patagones.json"

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            _escuelas_cache = json.load(f)
            logger.debug(f"Cargadas {len(_escuelas_cache)} escuelas")
    except FileNotFoundError:
        logger.warning(f"Archivo de escuelas no encontrado: {archivo}")
        _escuelas_cache = {}
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear archivo de escuelas: {e}")
        _escuelas_cache = {}

    return _escuelas_cache


def obtener_nombre_escuela(codigo: str) -> str:
    """
    Obtiene el nombre completo de una escuela dado su código.

    Args:
        codigo: Código de la escuela (ej: "0078PP0014")

    Returns:
        Nombre completo si se encuentra, o el código original si no
    """
    escuelas = cargar_escuelas()

    if codigo in escuelas:
        return escuelas[codigo]["nombre"]

    return codigo
