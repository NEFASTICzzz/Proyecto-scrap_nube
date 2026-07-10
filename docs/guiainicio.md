# Guía de Inicio Rápido - UTN Cloud Scraping

Esta guía contiene los pasos necesarios para configurar, arrancar y probar la plataforma en su entorno local.

## Requisitos Previos

Asegúrese de tener instalados los siguientes componentes:
1. **Python 3.9 o superior**
2. **PostgreSQL** (con un servidor activo corriendo localmente)
3. **Google Chrome** (instalado en su sistema, Selenium se encargará de configurar el controlador automáticamente)

---

## Instrucciones de Configuración

1. **Clonar/Extraer el Proyecto**
   Coloque todos los archivos del proyecto en una carpeta.

2. **Crear y Activar el Entorno Virtual (Recomendado)**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Instalar Dependencias**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configurar la Base de Datos PostgreSQL**
   * Abra su herramienta de administración de base de datos (como pgAdmin o la consola `psql`).
   * Cree una base de datos llamada `scraping_db` (o el nombre que defina en el archivo `.env`):
     ```sql
     CREATE DATABASE scraping_db;
     ```
   * *Opcional:* Puede ejecutar directamente el script `data/database.sql` para pre-crear las tablas, aunque la aplicación las creará automáticamente al iniciar si no existen.

5. **Configurar el archivo `.env`**
   * Cree o edite el archivo `.env` en la raíz del proyecto.
   * Ajuste las credenciales de PostgreSQL (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) según su configuración local.
   * La clave de Azure OpenAI ya viene pre-configurada con las credenciales académicas del profesor en el archivo `.env`.

---

## Cómo Iniciar la Aplicación

Para iniciar todo el sistema integrado (Base de datos, Scheduler en segundo plano, y API de Flask):

```powershell
python main.py
```

### Qué sucede al iniciar:
1. La consola mostrará la inicialización de la conexión con PostgreSQL.
2. Se creará automáticamente la estructura de tablas si no existían.
3. Se iniciará el **Orquestador (scheduler.py)** que ejecutará una carga inicial inmediata de scraping estático y dinámico.
4. Se levantará el servidor web Flask en la dirección `http://localhost:5000/`.

---

## Pruebas de Funcionamiento en Vivo

### 1. Panel de Visualización (Dashboard)
* Ingrese a: `http://localhost:5000/`
* Encontrará el contador de productos, archivos descargados, y un historial de alertas/eventos en tiempo real.
* Podrá cambiar de secciones (Datos Estructurados, Gestión de Archivos, Calendario, y Generador de Selectores).

### 2. Prueba del Scraper Estático y Detección de Cambios de Hash (SHA-256)
* Entre a la carpeta `mock_source_files/` del proyecto.
* Modifique el texto de cualquier archivo (ej. `documento_1.txt`) y guárdelo.
* En el próximo ciclo del scheduler (o si reinicia la aplicación para forzar la carga inmediata), el scraper descargará el archivo, calculará el nuevo hash, reemplazará el archivo viejo local en `./downloads/`, registrará la actualización en PostgreSQL y enviará una alerta visible en el dashboard y el calendario.
* Si borra un archivo de `mock_source_files/`, el scraper detectará que ya no está en el listado del sitio estático (`http://localhost:5000/mock/static`), lo eliminará de `./downloads/`, de la BD y guardará el registro.

### 3. Prueba de Adaptabilidad de Selectores con IA (Azure OpenAI)
* **Scraping Real (Por Defecto):** La aplicación está configurada para extraer datos en vivo de **Mercado Libre Costa Rica** (`https://listado.mercadolibre.co.cr/laptop`), cumpliendo con el requisito del sitio público real.
* **Prueba de Simulación Local (Para evaluar cambios del DOM y Azure OpenAI):**
  1. Abre tu archivo `.env` y edita la variable `DYNAMIC_SITE_URL` para que apunte a: `http://localhost:5000/mock/dynamic`.
  2. Reinicia la aplicación (`python main.py`).
  3. Ingresa a `http://localhost:5000/mock/dynamic` en tu navegador. Por defecto, sirve productos con las clases estándar CSS (`product-title` y `product-price`).
  4. Presiona el botón naranja **"Cambiar Estructura DOM"**. Esto alterará instantáneamente las clases de los elementos en la página (cambiándolas a `item-name-alt` y `item-cost-alt`).
  5. Cuando el scheduler ejecute el scraper dinámico, notará que no puede encontrar los productos. Enviará automáticamente un fragmento del HTML a Azure OpenAI (`gpt-4o-mini`), deducirá las nuevas clases, actualizará su caché local (`data/selectors_cache.json`) y continuará extrayendo sin interrupciones.

### 4. Script de Prueba Rápido (test_execution.py)
* Para realizar una demostración inmediata sin esperar el intervalo de 30 minutos del scheduler, puedes ejecutar:
  ```powershell
  python test_execution.py
  ```
* Este script validará que el servidor Flask local esté encendido, disparará una ronda de scraping estático y dinámico, y listará los resultados y eventos generados directamente en tu terminal.


