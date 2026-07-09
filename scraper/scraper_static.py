import os
import json
import hashlib
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Importar el gestor de datos centralizado
from data.data_manager import save_file, delete_file, get_all_files, log_event

load_dotenv()

# Configuración del Directorio de Logs y Logger en JSON
LOG_DIR = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'scraper.log')

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

logger = logging.getLogger("scraper_static")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)

# Parámetros del entorno
FLASK_PORT = os.getenv("FLASK_PORT", "5000")
STATIC_SITE_URL = f"http://localhost:{FLASK_PORT}/mock/static"
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), '../downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def calculate_sha256(file_path):
    """Calcula el hash SHA-256 de un archivo en disco."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_static_scraper():
    logger.info("Iniciando scraper estático de archivos...")
    
    try:
        response = requests.get(STATIC_SITE_URL, timeout=10)
        if response.status_code != 200:
            logger.error(f"No se pudo acceder al sitio estático: HTTP {response.status_code}")
            return
    except Exception as e:
        logger.error(f"Error de conexión con el sitio estático: {e}", exc_info=True)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select('a.btn')  # Los enlaces de descarga tienen clase 'btn'
    
    scraped_files_list = []
    
    for link in links:
        href = link.get('href')
        if not href:
            continue
        
        # URL de descarga completa
        download_url = f"http://localhost:{FLASK_PORT}{href}"
        filename = href.split('/')[-1]
        local_path = os.path.join(DOWNLOAD_DIR, filename)
        
        scraped_files_list.append(filename)
        
        try:
            # Descargar archivo temporal
            file_response = requests.get(download_url, timeout=15)
            if file_response.status_code != 200:
                logger.error(f"Error descargando {filename}: HTTP {file_response.status_code}")
                continue
            
            # Guardar temporalmente para comparar hash
            temp_path = local_path + ".tmp"
            with open(temp_path, "wb") as f:
                f.write(file_response.content)
            
            new_hash = calculate_sha256(temp_path)
            file_size = len(file_response.content)
            
            # Guardar/Actualizar usando el gestor centralizado
            status, prev_value = save_file(filename, download_url, new_hash, file_size)
            
            if status is True:
                # Caso: Nuevo Archivo
                if os.path.exists(local_path):
                    os.remove(local_path)
                os.rename(temp_path, local_path)
                msg = f"Nuevo archivo detectado y guardado: {filename} (SHA-256: {new_hash})"
                logger.info(msg)
                log_event("NEW_FILE", f"Archivo: {filename}", msg)
                
            elif status is False:
                # Caso: Archivo Modificado (Diferente Hash)
                if os.path.exists(local_path):
                    os.remove(local_path)
                os.rename(temp_path, local_path)
                msg = f"Archivo modificado en origen. Reemplazado localmente: {filename} (Nuevo Hash: {new_hash})"
                logger.info(msg)
                log_event("UPDATED_FILE", f"Modificado: {filename}", msg)
                
            else:
                # Sin cambios
                os.remove(temp_path)
                logger.info(f"Archivo sin cambios: {filename}")
                
        except Exception as e:
            logger.error(f"Error procesando el archivo {filename}: {e}", exc_info=True)
            log_event("ERROR", f"Error Archivo: {filename}", str(e))
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # --- Detección de Archivos Eliminados del Origen ---
    try:
        db_files = get_all_files()
        
        for db_file in db_files:
            db_filename = db_file['filename']
            if db_filename not in scraped_files_list:
                # El archivo ya no está en el listado HTML original -> Fue eliminado del origen
                local_path = os.path.join(DOWNLOAD_DIR, db_filename)
                if os.path.exists(local_path):
                    os.remove(local_path)
                
                delete_file(db_filename)
                
                msg = f"Archivo eliminado del origen. Eliminado localmente y de la BD: {db_filename}"
                logger.info(msg)
                log_event("DELETED_FILE", f"Eliminado: {db_filename}", msg)
                
    except Exception as e:
        logger.error(f"Error detectando archivos eliminados: {e}", exc_info=True)
        log_event("ERROR", "Detección de Archivos Eliminados", str(e))

    logger.info("Scraper estático finalizado con éxito.")

if __name__ == "__main__":
    run_static_scraper()
