# Monitor de Vacantes Docentes ABC - Patagones

## Arquitectura

Sistema de monitoreo automático de vacantes docentes del portal ABC (Provincia de Buenos Aires).

### Componentes principales

- `api_client.py`: Cliente para API Solr de ABC. Usa TLSAdapter para manejar certificados legacy del gobierno.
- `notifier.py`: Envío de emails HTML vía SMTP Gmail.
- `storage.py`: Persistencia con JSON (compatible con GitHub Actions).
- `oblea_parser.py`: Parser de códigos de habilitación desde PDF o txt.
- `main.py`: Scheduler (cada 6 horas) y CLI.
- `streamlit_app.py`: UI web opcional.

### API ABC

Endpoint Solr: `https://servicios3.abc.gob.ar/valoracion.docente/api/apd.oferta.encabezado/select`

Campos clave de la respuesta:
- `id` / `iddetalle`: ID único de la vacante
- `idoferta`: ID de la oferta (usado para link a postulantes)
- `areaincumbencia`: Código de área (MAT, LEN, MUP, etc.)
- `escuela`: Código de escuela (ej: 0078PP0014)

### Mapeo de escuelas

El código de escuela (ej: `0078PP0014`) se traduce al nombre completo usando `data/escuelas_patagones.json`.
- Fuente: [Datos Abiertos PBA](https://catalogo.datos.gba.gob.ar/dataset/establecimientos-educativos)
- Módulo: `escuelas.py` con función `obtener_nombre_escuela()`

### Link a postulantes

Cada vacante incluye un link para ver el ranking personal:
```
https://misservicios.abc.gob.ar/actos.publicos.digitales/postulantes/?oferta={idoferta}&detalle={id}
```
Este link requiere autenticación con credenciales ABC del docente.

## Ejecución

```bash
python main.py --once    # Una verificación
python main.py --test    # Email de prueba
python main.py           # Scheduler (6h)
```

## Variables de entorno

- `EMAIL_FROM`: Gmail remitente
- `EMAIL_PASSWORD`: App Password de Gmail
- `EMAIL_TO`: Destinatario
