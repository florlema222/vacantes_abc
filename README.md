# Monitor de Vacantes Docentes ABC - Patagones

Herramienta que monitorea automáticamente las vacantes docentes del portal ABC (Provincia de Buenos Aires) y envía notificaciones por email cuando aparecen nuevas ofertas.

## Funcionalidades

- Consulta la API del portal ABC cada 6 horas
- Filtra vacantes por distrito (Patagones) y niveles (Primaria, Secundaria, Artística)
- Compara con los códigos de habilitación de tu oblea
- Envía email solo cuando hay vacantes nuevas donde estás habilitada
- No repite notificaciones de vacantes ya informadas

## Configuración

### 1. Códigos de Oblea

Editar el archivo `codigos.txt` con tus códigos de área/incumbencia (uno por línea):

```
/PR
CCD
APV
# Puedes agregar comentarios con #
```

### 2. Secrets de GitHub Actions

En tu repositorio: Settings → Secrets and variables → Actions

| Secret | Descripción |
|--------|-------------|
| `EMAIL_FROM` | Tu email de Gmail |
| `EMAIL_PASSWORD` | App Password de Gmail ([crear aquí](https://myaccount.google.com/apppasswords)) |
| `EMAIL_TO` | Email donde recibir notificaciones |

### 3. Activar GitHub Actions

1. Ir a la pestaña "Actions" del repositorio
2. Habilitar los workflows

## Ejecución

### Automática (GitHub Actions)
Se ejecuta automáticamente cada 6 horas (0:00, 6:00, 12:00, 18:00 UTC).

También puedes ejecutarlo manualmente desde Actions → "Verificar Vacantes Docentes" → "Run workflow".

### Local
```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar credenciales
cp .env.example .env
# Editar .env con tus datos

# Ejecutar una vez
python main.py --once

# Ver estadísticas
python main.py --stats
```

## Filtros Configurados

- **Distrito:** Patagones
- **Niveles:** Primaria, Secundaria, Artística
- **Habilitaciones:** Según códigos en `codigos.txt`

Para modificar filtros, editar `config.py`.

## Estructura

```
├── main.py              # Script principal
├── api_client.py        # Cliente API del portal ABC
├── oblea_parser.py      # Lector de códigos de oblea
├── notifier.py          # Envío de emails
├── storage.py           # Registro de vacantes notificadas
├── config.py            # Configuración
├── codigos.txt          # Tus códigos de habilitación
├── data/                # Datos persistentes (JSON)
└── .github/workflows/   # Automatización GitHub Actions
```

## Licencia

Uso personal.
