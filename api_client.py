"""
Cliente para la API de vacantes docentes del portal ABC.
"""
import logging
import ssl
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

import config


# Adapter para manejar servidores con SSL/TLS antiguo
class TLSAdapter(HTTPAdapter):
    """Adapter que permite conexiones con servidores TLS legacy."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Permitir protocolos más antiguos
        ctx.options &= ~ssl.OP_NO_SSLv3
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

logger = logging.getLogger(__name__)


@dataclass
class Vacante:
    """Representa una vacante docente."""
    id: str
    cargo: str
    descripcion_cargo: str
    area_incumbencia: str
    nivel_modalidad: str
    distrito: str
    escuela: str
    domicilio: str
    turno: str
    jornada: str
    fecha_inicio: Optional[str]
    fecha_fin_oferta: Optional[str]
    horarios: dict
    docente_reemplazado: Optional[str]
    motivo_reemplazo: Optional[str]

    @classmethod
    def from_api_response(cls, data: dict) -> "Vacante":
        """Crea una Vacante desde la respuesta de la API."""
        return cls(
            id=data.get("id", ""),
            cargo=data.get("cargo", ""),
            descripcion_cargo=data.get("descripcioncargo", ""),
            area_incumbencia=data.get("areaincumbencia", "").upper().strip(),
            nivel_modalidad=data.get("descnivelmodalidad", ""),
            distrito=data.get("descdistrito", ""),
            escuela=data.get("escuela", ""),
            domicilio=data.get("domiciliodesempeno", ""),
            turno=data.get("turno", ""),
            jornada=data.get("jornada", ""),
            fecha_inicio=data.get("tomaposesion"),
            fecha_fin_oferta=data.get("finoferta"),
            horarios={
                "lunes": data.get("lunes", ""),
                "martes": data.get("martes", ""),
                "miercoles": data.get("miercoles", ""),
                "jueves": data.get("jueves", ""),
                "viernes": data.get("viernes", ""),
                "sabado": data.get("sabado", ""),
            },
            docente_reemplazado=data.get("reemp_apeynom"),
            motivo_reemplazo=data.get("reemp_motivo"),
        )


class APIClient:
    """Cliente para consultar la API de vacantes ABC."""

    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "VacantesMonitor/1.0"
        })
        # Montar adapter TLS para el servidor del gobierno
        self.session.mount("https://", TLSAdapter())

    def buscar_vacantes(
        self,
        distrito: str = None,
        niveles: list[str] = None,
        max_resultados: int = 500
    ) -> list[Vacante]:
        """
        Busca vacantes publicadas con los filtros especificados.

        Args:
            distrito: Nombre del distrito (ej: "patagones")
            niveles: Lista de niveles educativos (ej: ["primaria", "secundaria"])
            max_resultados: Máximo de resultados a retornar

        Returns:
            Lista de objetos Vacante
        """
        distrito = distrito or config.DISTRITO
        niveles = niveles or config.NIVELES

        # Construir filtros Solr
        fq_params = [
            "estado:Publicada",
            f"descdistrito:{distrito.lower()}",
        ]

        # Agregar filtro de niveles (OR entre ellos)
        if niveles:
            niveles_filter = " OR ".join([f'descnivelmodalidad:"{n.lower()}"' for n in niveles])
            fq_params.append(f"({niveles_filter})")

        params = {
            "q": "*:*",
            "wt": "json",
            "rows": max_resultados,
            "sort": "finoferta asc",  # Ordenar por fecha de cierre
        }

        # Agregar cada filtro como parámetro fq separado
        for fq in fq_params:
            if "fq" not in params:
                params["fq"] = []
            if isinstance(params["fq"], list):
                params["fq"].append(fq)
            else:
                params["fq"] = [params["fq"], fq]

        try:
            logger.info(f"Consultando API: distrito={distrito}, niveles={niveles}")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            docs = data.get("response", {}).get("docs", [])

            vacantes = [Vacante.from_api_response(doc) for doc in docs]
            logger.info(f"Se encontraron {len(vacantes)} vacantes")

            return vacantes

        except requests.RequestException as e:
            logger.error(f"Error al consultar API: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Error al parsear respuesta: {e}")
            raise


def filtrar_por_codigos(vacantes: list[Vacante], codigos_habilitados: set[str]) -> list[Vacante]:
    """
    Filtra vacantes que coincidan con los códigos de área habilitados.

    Args:
        vacantes: Lista de vacantes a filtrar
        codigos_habilitados: Set de códigos de área/incumbencia de la oblea

    Returns:
        Lista de vacantes que coinciden con algún código habilitado
    """
    if not codigos_habilitados:
        logger.warning("No hay códigos de oblea para filtrar, retornando todas las vacantes")
        return vacantes

    # Normalizar códigos (mayúsculas, sin espacios)
    codigos_norm = {c.upper().strip() for c in codigos_habilitados}

    filtradas = []
    for v in vacantes:
        area = v.area_incumbencia.upper().strip()
        # Comparar área de la vacante con códigos habilitados
        if area in codigos_norm:
            filtradas.append(v)
            logger.debug(f"Vacante {v.id} coincide con código {area}")

    logger.info(f"Filtradas {len(filtradas)} vacantes de {len(vacantes)} por códigos de oblea")
    return filtradas


if __name__ == "__main__":
    # Test rápido
    logging.basicConfig(level=logging.INFO)
    client = APIClient()
    vacantes = client.buscar_vacantes()

    print(f"\nEncontradas {len(vacantes)} vacantes en {config.DISTRITO}:")
    for v in vacantes[:5]:
        print(f"  - {v.cargo} ({v.area_incumbencia}) - {v.nivel_modalidad}")
