"""
Configuración del monitor de vacantes docentes ABC.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === API ABC ===
API_BASE_URL = "https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select"

# Filtros de búsqueda
DISTRITO = "patagones"
DISTRITO_ID = 78
NIVELES = ["primaria", "secundaria", "artistica"]

# === Email ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")  # App Password de Gmail
EMAIL_TO = os.getenv("EMAIL_TO", "")

# === Scheduler ===
CHECK_INTERVAL_HOURS = 6

# === Archivos ===
OBLEA_PDF_PATH = os.getenv("OBLEA_PDF_PATH", "oblea.pdf")
DATABASE_PATH = "vacantes.db"

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
