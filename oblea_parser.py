"""
Parser para extraer códigos de habilitación de la oblea docente (PDF).
"""
import logging
import re
from pathlib import Path

import pdfplumber

import config

logger = logging.getLogger(__name__)

# Patrones comunes de códigos de área/incumbencia en obleas
# Ejemplos: AE, /AL, FPG, MAT, LEN, EFI, MUS, etc.
CODIGO_PATTERN = re.compile(
    r'\b([A-Z]{2,4}|/[A-Z]{2,3})\b'
)

# Códigos conocidos de áreas docentes (se puede expandir)
CODIGOS_CONOCIDOS = {
    # Áreas generales
    "AE", "FPG", "MG", "MI",
    # Materias primaria/secundaria
    "MAT", "LEN", "NAT", "SOC", "ING", "EFI", "MUS", "PLA", "TEC",
    # Educación Física
    "/EF", "/AL",
    # Artística
    "ART", "DAN", "TEA",
    # Especial
    "ESP", "PSI",
    # Otros
    "INF", "ADM", "BIB", "PRE", "SEC",
}


def extraer_texto_pdf(pdf_path: str) -> str:
    """
    Extrae todo el texto de un archivo PDF.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Texto extraído del PDF
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")

    texto_completo = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            texto = page.extract_text()
            if texto:
                texto_completo.append(texto)
                logger.debug(f"Página {i+1}: {len(texto)} caracteres extraídos")

    return "\n".join(texto_completo)


def extraer_codigos_oblea(pdf_path: str = None) -> set[str]:
    """
    Extrae los códigos de área/incumbencia de una oblea docente.

    Args:
        pdf_path: Ruta al PDF de la oblea (usa config si no se especifica)

    Returns:
        Set de códigos de área encontrados
    """
    pdf_path = pdf_path or config.OBLEA_PDF_PATH

    try:
        texto = extraer_texto_pdf(pdf_path)
        logger.info(f"Texto extraído del PDF: {len(texto)} caracteres")

        # Buscar todos los patrones que parecen códigos
        matches = CODIGO_PATTERN.findall(texto.upper())

        # Filtrar solo los que parecen códigos válidos
        codigos = set()
        for match in matches:
            codigo = match.strip()
            # Incluir si es un código conocido o tiene formato típico
            if codigo in CODIGOS_CONOCIDOS or (
                len(codigo) >= 2 and
                len(codigo) <= 4 and
                codigo.replace("/", "").isalpha()
            ):
                codigos.add(codigo)

        logger.info(f"Se encontraron {len(codigos)} códigos: {codigos}")
        return codigos

    except FileNotFoundError:
        logger.warning(f"No se encontró el PDF de oblea en {pdf_path}")
        return set()
    except Exception as e:
        logger.error(f"Error al procesar oblea: {e}")
        return set()


def extraer_codigos_desde_texto(texto: str) -> set[str]:
    """
    Extrae códigos de un texto plano (alternativa al PDF).
    Útil si el usuario quiere ingresar los códigos manualmente.

    Args:
        texto: Texto con códigos separados por comas, espacios o líneas

    Returns:
        Set de códigos normalizados
    """
    codigos = set()

    for linea in texto.split("\n"):
        # Ignorar comentarios y líneas vacías
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue

        # Separar por comas o espacios si hay múltiples en una línea
        partes = re.split(r'[,\s]+', linea.upper())

        for parte in partes:
            codigo = parte.strip()
            # Aceptar códigos de 2-4 caracteres, incluyendo prefijos especiales
            # Ejemplos: /PR, +3N, -7H, CCD, APV
            if codigo and len(codigo) >= 2 and len(codigo) <= 4:
                codigos.add(codigo)

    return codigos


def cargar_codigos_desde_archivo(archivo: str = "codigos.txt") -> set[str]:
    """
    Carga códigos desde un archivo de texto simple.
    Alternativa al PDF si el usuario prefiere listar manualmente.

    Args:
        archivo: Ruta al archivo de texto

    Returns:
        Set de códigos
    """
    path = Path(archivo)
    if not path.exists():
        logger.debug(f"No existe archivo de códigos: {archivo}")
        return set()

    texto = path.read_text(encoding="utf-8")
    return extraer_codigos_desde_texto(texto)


def obtener_codigos_habilitados() -> set[str]:
    """
    Obtiene los códigos habilitados de cualquier fuente disponible.
    Prioridad: archivo codigos.txt > PDF oblea

    Returns:
        Set de códigos de área habilitados
    """
    # Primero intentar desde archivo de texto (más simple)
    codigos = cargar_codigos_desde_archivo()
    if codigos:
        logger.info(f"Códigos cargados desde archivo: {codigos}")
        return codigos

    # Si no hay archivo, intentar extraer del PDF
    codigos = extraer_codigos_oblea()
    if codigos:
        return codigos

    logger.warning("No se pudieron obtener códigos de oblea")
    return set()


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.DEBUG)

    print("Buscando códigos de oblea...")
    codigos = obtener_codigos_habilitados()

    if codigos:
        print(f"\nCódigos encontrados ({len(codigos)}):")
        for c in sorted(codigos):
            print(f"  - {c}")
    else:
        print("\nNo se encontraron códigos.")
        print("Opciones:")
        print("  1. Colocar oblea.pdf en el directorio del proyecto")
        print("  2. Crear un archivo codigos.txt con los códigos separados por líneas")
