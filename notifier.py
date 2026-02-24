"""
Notificador por email para vacantes docentes.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import config
from api_client import Vacante

logger = logging.getLogger(__name__)


def generar_html_vacante(vacante: Vacante) -> str:
    """Genera el HTML para mostrar una vacante."""
    horarios = []
    for dia, horas in vacante.horarios.items():
        if horas:
            horarios.append(f"<li><strong>{dia.capitalize()}:</strong> {horas}</li>")

    horarios_html = "<ul>" + "".join(horarios) + "</ul>" if horarios else "No especificado"

    return f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background: #f9f9f9;">
        <h3 style="color: #2c5282; margin-top: 0;">{vacante.cargo}</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold; width: 150px;">Nivel:</td>
                <td style="padding: 5px 0;">{vacante.nivel_modalidad.upper()}</td>
            </tr>
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold;">Área/Código:</td>
                <td style="padding: 5px 0;">{vacante.area_incumbencia}</td>
            </tr>
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold;">Escuela:</td>
                <td style="padding: 5px 0;">{vacante.escuela}</td>
            </tr>
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold;">Domicilio:</td>
                <td style="padding: 5px 0;">{vacante.domicilio}</td>
            </tr>
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold;">Turno:</td>
                <td style="padding: 5px 0;">{vacante.turno} - {vacante.jornada}</td>
            </tr>
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold;">Toma posesión:</td>
                <td style="padding: 5px 0;">{vacante.fecha_inicio or 'No especificado'}</td>
            </tr>
            <tr>
                <td style="padding: 5px 10px 5px 0; font-weight: bold;">Cierre oferta:</td>
                <td style="padding: 5px 0; color: #c53030;">{vacante.fecha_fin_oferta or 'No especificado'}</td>
            </tr>
        </table>
        <div style="margin-top: 10px;">
            <strong>Horarios:</strong>
            {horarios_html}
        </div>
        {f'<p style="color: #666; font-size: 0.9em;">Reemplazo de: {vacante.docente_reemplazado} ({vacante.motivo_reemplazo})</p>' if vacante.docente_reemplazado else ''}
    </div>
    """


def generar_email_html(vacantes: list[Vacante]) -> str:
    """Genera el contenido HTML del email con todas las vacantes."""
    vacantes_html = "\n".join(generar_html_vacante(v) for v in vacantes)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c5282; border-bottom: 2px solid #2c5282; padding-bottom: 10px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <h1>Nuevas Vacantes Docentes en Patagones</h1>
        <p>Se encontraron <strong>{len(vacantes)}</strong> nuevas vacantes que coinciden con tu perfil:</p>

        {vacantes_html}

        <div class="footer">
            <p>
                <a href="https://servicios.abc.gob.ar/servaddo/">Ver todas las ofertas en el portal ABC</a>
            </p>
            <p>
                Consulta realizada: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </p>
        </div>
    </body>
    </html>
    """


def enviar_email(vacantes: list[Vacante]) -> bool:
    """
    Envía un email con las vacantes encontradas.

    Args:
        vacantes: Lista de vacantes a notificar

    Returns:
        True si el envío fue exitoso, False en caso contrario
    """
    if not vacantes:
        logger.info("No hay vacantes para notificar")
        return True

    if not config.EMAIL_FROM or not config.EMAIL_PASSWORD or not config.EMAIL_TO:
        logger.error("Credenciales de email no configuradas")
        return False

    try:
        # Crear mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ABC] {len(vacantes)} nuevas vacantes en Patagones"
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO

        # Contenido HTML
        html_content = generar_email_html(vacantes)
        msg.attach(MIMEText(html_content, "html"))

        # Enviar
        logger.info(f"Conectando a {config.SMTP_SERVER}:{config.SMTP_PORT}")
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email enviado exitosamente a {config.EMAIL_TO}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación SMTP. Verifica EMAIL_FROM y EMAIL_PASSWORD")
        logger.error("Para Gmail, necesitas crear una 'App Password' en tu cuenta")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Error al enviar email: {e}")
        return False


def enviar_test():
    """Envía un email de prueba."""
    from api_client import Vacante

    vacante_test = Vacante(
        id="TEST-001",
        cargo="PROFESOR/A DE EDUCACION PRIMARIA (TEST)",
        descripcion_cargo="Cargo de prueba",
        area_incumbencia="MAT",
        nivel_modalidad="primaria",
        distrito="PATAGONES",
        escuela="E.P. N° 1 - TEST",
        domicilio="Calle Falsa 123, Carmen de Patagones",
        turno="M",
        jornada="JS",
        fecha_inicio="2026-03-01",
        fecha_fin_oferta="2026-02-28",
        horarios={
            "lunes": "08:00-12:00",
            "martes": "08:00-12:00",
            "miercoles": "08:00-12:00",
            "jueves": "08:00-12:00",
            "viernes": "08:00-12:00",
            "sabado": "",
        },
        docente_reemplazado="García, María",
        motivo_reemplazo="Licencia médica",
    )

    print("Enviando email de prueba...")
    if enviar_email([vacante_test]):
        print("Email enviado correctamente!")
    else:
        print("Error al enviar email. Revisa la configuración.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    enviar_test()
