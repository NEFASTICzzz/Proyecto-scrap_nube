# Plataforma de Scraping, Visualización y Generación de Selectores LLM

**Carrera:** Ingeniería en Tecnologías de la Información  
**Curso:** Computación en la Nube  
**Profesor:** Andrés Joseph Jiménez Leandro  
**Universidad:** Universidad Técnica Nacional (UTN)  
**Ciclo Lectivo:** IIC-2026  

---

## Descripción del Proyecto

Este proyecto consiste en una plataforma web avanzada y profesional diseñada para realizar scraping de datos dinámicos y estáticos en segundo plano, persistirlos en una base de datos **PostgreSQL**, y presentarlos en un Dashboard interactivo moderno con visualizaciones en tiempo real y soporte de calendarios (**FullCalendar.js**). 

Una de las características innovadoras de la plataforma es la integración con **Azure OpenAI (gpt-4o-mini)**. Si la estructura DOM del sitio dinámico cambia (rompiendo los selectores CSS de extracción predefinidos), el sistema captura de manera autónoma un fragmento de HTML, consulta el LLM para deducir y generar la nueva clase/selector CSS y continúa la recolección de datos de manera resiliente y autoadaptable.

Adicionalmente, se incluye una simulación local de descargas de archivos para monitorear hashes de integridad **SHA-256**, detectando archivos modificados en origen (reemplazo automático), nuevos archivos, y archivos eliminados (sincronización y depuración local).

---

## Estructura Final del Proyecto

```
proyecto-scrap-nube/
├── api/
│   └── json_api_server.py     # Servidor Flask (API JSON, Sitios Mocks y Tester LLM)
├── data/
│   ├── database.sql           # Script de creación de tablas en PostgreSQL
│   ├── database_filled_backup.sql # Script SQL completo de la BD llena de respaldo
│   └── database_backup.backup # Archivo de backup binario de la BD (Instrucciones)
├── docs/
│   └── guiainicio.md          # Guía de inicio rápido para el evaluador
├── downloads/                 # Carpeta local para almacenamiento de descargas
│   └── .gitkeep               # Archivo para forzar el rastreo del folder en Git
├── frontend/
│   ├── index.html             # Dashboard UI principal
│   ├── styles.css             # Estilos de diseño premium (Tema oscuro y glassmorphism)
│   ├── main.js                # Orquestador del frontend y llamadas a API
│   ├── results.js             # Visualizador de datos estructurados escrapeados
│   ├── files.js               # Gestor visual de integridad de archivos
│   └── calendar.js            # Visualizador de alertas basado en FullCalendar
├── llm/
│   └── llm_selector.py        # Módulo de integración con Azure OpenAI
├── logs/
│   └── scraper.log            # Logs estructurados en formato JSON
├── mock_source_files/         # Archivos fuente para simulación de descargas estáticas
├── scraper/
│   ├── scraper_dynamic.py     # Scraper Selenium adaptativo por LLM
│   └── scraper_static.py      # Scraper BeautifulSoup con validación de SHA-256
├── .env                       # Variables de entorno y llaves de acceso protegidas
├── main.py                    # Punto de entrada unificado de la plataforma
├── requirements.txt           # Dependencias requeridas del proyecto
├── test_execution.py          # Script corto para pruebas y demostración de cambios
└── README.md                  # Información del proyecto e instrucciones básicas
```

---

## Configuración y Variables de Entorno (.env)

El archivo `.env` en la raíz del proyecto debe tener la siguiente estructura y valores de configuración:

```ini
# Configuración de Base de Datos PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scraping_db
DB_USER=postgres
DB_PASSWORD=postgres

# Configuración de Azure OpenAI (Credenciales Académicas de UTN)
AZURE_OPENAI_ENDPOINT=https://voiceflip-openai.openai.azure.com/
AZURE_OPENAI_KEY=FwsUIhIZedFYxW7nGYwKgoJsMXYAH62OE4QThqLrwtKuCc5m17AjJQQJ99BEACYeBjFXJ3w3AAABACOGfF7h
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Configuración de la API y Servidor Flask
FLASK_PORT=5000
FLASK_DEBUG=True

# Intervalo del scheduler en minutos (Para pruebas rápidas puede reducirse a 1 o 2 minutos)
SCHEDULER_INTERVAL_MINUTES=30
```

---

## Arquitectura y Diseño

### 1. Persistencia y Base de Datos (PostgreSQL)
El backend utiliza PostgreSQL para almacenar el estado global de la aplicación en tres tablas clave:
* `scraped_products`: Almacena el título, precio y enlace único de los ítems recopilados por Selenium.
* `scraped_files`: Registra el historial de archivos descargados locales y su correspondiente firma digital SHA-256.
* `events_log`: Bitácora de operaciones y detecciones del planificador, usado para alertar al usuario y poblar el widget de calendario.

Para restaurar la base de datos a partir de los respaldos incluidos en la carpeta `data/`:
* **Script SQL Pre-llenado:**
  ```bash
  psql -h localhost -U postgres -d scraping_db -f data/database_filled_backup.sql
  ```
* **Respaldo Binario (.backup):**
  ```bash
  pg_restore -h localhost -U postgres -d scraping_db -v data/database_backup.backup
  ```

### 2. Detección de Cambios y Resiliencia
* **Scraper Estático:** Mediante solicitudes HTTP con BeautifulSoup, el script extrae los enlaces a archivos, los descarga temporalmente y compara su hash SHA-256 con el registro en la BD. Si detecta diferencias, sobrescribe el archivo en `./downloads/` y genera una alerta de modificación. Si detecta archivos huérfanos que ya no existen en la página de descargas, los remueve del sistema localmente y en la base de datos de manera limpia.
* **Scraper Dinámico:** Utiliza Selenium en modo invisible (headless). Al toparse con una estructura de DOM cambiada (por ejemplo, cuando se alteran las clases de la tienda mock de "default" a "changed"), el scraper solicita auxilio al LLM mediante una consulta estructurada a la API de Azure OpenAI. El modelo devuelve el selector CSS correcto en milisegundos, el script actualiza su archivo de caché `data/selectors_cache.json` y completa la recolección sin detenerse.

### 3. Interfaz Visual Premium (Frontend)
El frontend se construyó en HTML5 y CSS3 nativo buscando una experiencia visual premium e inmersiva:
* **Tema Oscuro y Glassmorphism:** Interfaz minimalista con tonalidades profundas e iluminación led violeta/azul para evitar la fatiga visual.
* **Integración Modular con JavaScript:** Archivos separados para control de calendario (`calendar.js`), archivos (`files.js`), productos (`results.js`) y orquestación (`main.js`).
* **FullCalendar.js:** Mapea cronológicamente los eventos e inserciones en base a sus tipos con colores semánticos (verde: creación, amarillo: actualización, rojo: eliminación).
* **Tester de Selectores LLM:** Incluye una herramienta interactiva para que el docente pueda pegar cualquier bloque HTML y probar en vivo la generación de selectores por Azure OpenAI.
