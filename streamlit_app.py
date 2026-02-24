"""
Monitor de Vacantes Docentes ABC - Interfaz Web
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# Configurar página
st.set_page_config(
    page_title="Vacantes Docentes ABC",
    page_icon="📚",
    layout="wide"
)

# Importar módulos del proyecto
from api_client import APIClient, filtrar_por_codigos, Vacante
from oblea_parser import obtener_codigos_habilitados, extraer_codigos_desde_texto
from storage import inicializar_db, filtrar_nuevas, marcar_como_notificada, obtener_estadisticas, _cargar_datos
from notifier import enviar_email
import config

# Archivos de configuración
CONFIG_FILE = Path(__file__).parent / "data" / "config_ui.json"
CODIGOS_FILE = Path(__file__).parent / "codigos.txt"
DATA_FILE = Path(__file__).parent / "data" / "vacantes_notificadas.json"


def cargar_config_ui():
    """Carga la configuración de la UI."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {
        "distrito": "patagones",
        "niveles": ["primaria", "secundaria", "artistica"],
        "email_to": ""
    }


def guardar_config_ui(config_data):
    """Guarda la configuración de la UI."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config_data, indent=2))


def cargar_codigos():
    """Carga los códigos del archivo."""
    if CODIGOS_FILE.exists():
        return CODIGOS_FILE.read_text()
    return ""


def guardar_codigos(texto):
    """Guarda los códigos en el archivo."""
    CODIGOS_FILE.write_text(texto)


# Inicializar
inicializar_db()

# === SIDEBAR - Configuración ===
st.sidebar.title("⚙️ Configuración")

# Cargar config actual
ui_config = cargar_config_ui()

# Distrito
DISTRITOS = [
    "patagones", "bahia blanca", "villarino", "coronel rosales",
    "la plata", "quilmes", "lomas de zamora", "la matanza",
    "general pueyrredon", "tandil", "azul", "olavarria"
]
distrito = st.sidebar.selectbox(
    "📍 Distrito",
    options=DISTRITOS,
    index=DISTRITOS.index(ui_config.get("distrito", "patagones")) if ui_config.get("distrito") in DISTRITOS else 0
)

# Niveles
NIVELES_DISPONIBLES = [
    "primaria", "secundaria", "artistica", "inicial", "especial",
    "superior", "tecnico profesional", "adultos y cens",
    "psicologia", "educacion fisica"
]
niveles = st.sidebar.multiselect(
    "🎓 Niveles educativos",
    options=NIVELES_DISPONIBLES,
    default=ui_config.get("niveles", ["primaria", "secundaria", "artistica"])
)

# Email
email_to = st.sidebar.text_input(
    "📧 Email para notificaciones",
    value=ui_config.get("email_to", "")
)

# Guardar configuración
if st.sidebar.button("💾 Guardar configuración"):
    guardar_config_ui({
        "distrito": distrito,
        "niveles": niveles,
        "email_to": email_to
    })
    st.sidebar.success("Configuración guardada!")

st.sidebar.divider()

# Códigos de oblea
st.sidebar.subheader("📋 Códigos de Oblea")
codigos_texto = st.sidebar.text_area(
    "Un código por línea (# para comentarios)",
    value=cargar_codigos(),
    height=150
)

if st.sidebar.button("💾 Guardar códigos"):
    guardar_codigos(codigos_texto)
    st.sidebar.success("Códigos guardados!")

# Mostrar cantidad de códigos
codigos_set = extraer_codigos_desde_texto(codigos_texto)
st.sidebar.caption(f"✓ {len(codigos_set)} códigos cargados")

# === CONTENIDO PRINCIPAL ===
st.title("📚 Monitor de Vacantes Docentes ABC")
st.caption(f"Distrito: **{distrito.upper()}** | Niveles: {', '.join(niveles)}")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Vacantes Actuales", "📊 Historial", "📧 Enviar Notificación"])

# === TAB 1: Vacantes Actuales ===
with tab1:
    col1, col2 = st.columns([3, 1])

    with col2:
        buscar = st.button("🔄 Buscar vacantes", type="primary", use_container_width=True)
        filtrar_oblea = st.checkbox("Filtrar por mi oblea", value=True)

    if buscar:
        with st.spinner("Consultando API..."):
            try:
                client = APIClient()
                vacantes = client.buscar_vacantes(
                    distrito=distrito,
                    niveles=niveles if niveles else None
                )

                if filtrar_oblea and codigos_set:
                    vacantes = filtrar_por_codigos(vacantes, codigos_set)

                st.session_state['vacantes'] = vacantes
                st.session_state['ultima_busqueda'] = datetime.now()

            except Exception as e:
                st.error(f"Error al consultar: {e}")

    # Mostrar vacantes
    if 'vacantes' in st.session_state:
        vacantes = st.session_state['vacantes']

        if vacantes:
            st.success(f"Se encontraron **{len(vacantes)}** vacantes")

            for v in vacantes:
                with st.expander(f"**{v.cargo}** - {v.nivel_modalidad.upper()}", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Código área:** {v.area_incumbencia}")
                        st.write(f"**Escuela:** {v.escuela}")
                        st.write(f"**Domicilio:** {v.domicilio}")
                        st.write(f"**Turno:** {v.turno} | **Jornada:** {v.jornada}")

                    with col2:
                        st.write(f"**Toma posesión:** {v.fecha_inicio or 'No especificado'}")
                        st.write(f"**Cierre oferta:** {v.fecha_fin_oferta or 'No especificado'}")
                        if v.docente_reemplazado:
                            st.write(f"**Reemplaza a:** {v.docente_reemplazado}")
                            st.write(f"**Motivo:** {v.motivo_reemplazo}")

                    # Horarios
                    horarios = [f"{dia}: {hora}" for dia, hora in v.horarios.items() if hora]
                    if horarios:
                        st.write("**Horarios:**", " | ".join(horarios))
        else:
            st.info("No se encontraron vacantes con los filtros actuales")
    else:
        st.info("👆 Hacé click en 'Buscar vacantes' para consultar")

# === TAB 2: Historial ===
with tab2:
    st.subheader("📊 Estadísticas")

    stats = obtener_estadisticas()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total notificadas", stats["total_notificadas"])
    col2.metric("Total consultas", stats["total_consultas"])

    if stats["ultima_consulta"]:
        col3.metric("Última consulta", stats["ultima_consulta"]["fecha"][:16].replace("T", " "))

    st.divider()

    st.subheader("📜 Vacantes Notificadas")

    datos = _cargar_datos()
    if datos["vacantes_notificadas"]:
        for vid, info in sorted(datos["vacantes_notificadas"].items(),
                                key=lambda x: x[1]["fecha_notificacion"],
                                reverse=True):
            st.write(f"• **{info['cargo']}** ({info['nivel']}) - {info['fecha_notificacion'][:10]}")
    else:
        st.info("No hay vacantes notificadas aún")

    st.divider()

    st.subheader("📝 Log de consultas")
    if datos["log_consultas"]:
        for log in reversed(datos["log_consultas"][-10:]):
            status = "✅" if log["estado"] == "OK" else "❌"
            st.write(f"{status} {log['fecha'][:16].replace('T', ' ')} - {log['total_encontradas']} encontradas, {log['nuevas']} nuevas")
    else:
        st.info("No hay consultas registradas")

# === TAB 3: Enviar Notificación ===
with tab3:
    st.subheader("📧 Enviar notificación manual")

    st.warning("Esta acción enviará un email con las vacantes nuevas encontradas.")

    # Verificar configuración
    email_from = st.secrets.get("EMAIL_FROM", "") if hasattr(st, 'secrets') else ""
    email_pass = st.secrets.get("EMAIL_PASSWORD", "") if hasattr(st, 'secrets') else ""

    if not email_from or not email_pass:
        st.error("⚠️ Credenciales de email no configuradas en Streamlit Secrets")
        st.info("""
        Para configurar, agregá estos secrets en Streamlit Cloud:
        - `EMAIL_FROM`: tu email de Gmail
        - `EMAIL_PASSWORD`: App Password de Gmail
        """)

    if 'vacantes' in st.session_state and st.session_state['vacantes']:
        vacantes = st.session_state['vacantes']
        nuevas = filtrar_nuevas(vacantes)

        st.write(f"Vacantes totales: **{len(vacantes)}**")
        st.write(f"Vacantes nuevas (no notificadas): **{len(nuevas)}**")

        email_destino = email_to or (st.secrets.get("EMAIL_TO", "") if hasattr(st, 'secrets') else "")

        if nuevas and email_destino:
            if st.button("📤 Enviar email con vacantes nuevas", type="primary"):
                with st.spinner("Enviando email..."):
                    # Temporalmente setear el email destino
                    import config
                    original_to = config.EMAIL_TO
                    config.EMAIL_TO = email_destino

                    if enviar_email(nuevas):
                        for v in nuevas:
                            marcar_como_notificada(v.id, v.cargo, v.area_incumbencia, v.nivel_modalidad)
                        st.success(f"Email enviado a {email_destino}!")
                    else:
                        st.error("Error al enviar email")

                    config.EMAIL_TO = original_to
        elif not nuevas:
            st.info("No hay vacantes nuevas para notificar")
        elif not email_destino:
            st.warning("Configurá un email de destino en la barra lateral")
    else:
        st.info("Primero buscá vacantes en la pestaña 'Vacantes Actuales'")

# Footer
st.divider()
st.caption("Monitor de Vacantes Docentes ABC - Patagones | Actualización automática cada 6 horas vía GitHub Actions")
