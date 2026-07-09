import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Importar el generador de selectores del LLM
from llm.llm_selector import generate_css_selector
# Importar el gestor de datos centralizado
from data.data_manager import save_product, delete_product, get_all_products, log_event

load_dotenv()

# Logger estructurado en JSON
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

logger = logging.getLogger("scraper_dynamic")
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
# Sitio público real por defecto (Mercado Libre Costa Rica)
DEFAULT_DYNAMIC_URL = "https://listado.mercadolibre.co.cr/laptop"
DYNAMIC_SITE_URL = os.getenv("DYNAMIC_SITE_URL", DEFAULT_DYNAMIC_URL)

CACHE_FILE = os.path.join(os.path.dirname(__file__), '../data/selectors_cache.json')
os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

# Selectores CSS por defecto para Mercado Libre Costa Rica
DEFAULT_SELECTORS = {
    "card": "li.ui-search-layout__item",
    "title": "h2.ui-search-item__title",
    "price": "span.andes-money-amount__fraction",
    "url": "a.ui-search-link"
}

# Si el usuario configura usar la simulación local de Flask, adaptamos los selectores por defecto
if "localhost" in DYNAMIC_SITE_URL or "127.0.0.1" in DYNAMIC_SITE_URL:
    DEFAULT_SELECTORS = {
        "card": ".product-card",
        "title": ".product-title",
        "price": ".product-price",
        "url": ".prod-url"
    }

def load_cached_selectors():
    """Carga los selectores almacenados localmente."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SELECTORS.copy()

def save_cached_selectors(selectors):
    """Guarda los selectores generados en caché."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(selectors, f, indent=4)
    except Exception as e:
        logger.error(f"Error al guardar caché de selectores: {e}")

def setup_driver():
    """Inicializa Selenium en modo headless con técnicas de evasión de detección de bots."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # Evasión de detección de bots (User-Agent real y remover banderas de automatización)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(options=chrome_options)
    # Ejecutar script para limpiar la propiedad navigator.webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "const newProto = navigator.__proto__; delete newProto.webdriver; navigator.__proto__ = newProto;"
    })
    return driver

def run_dynamic_scraper():
    logger.info(f"Iniciando scraper dinámico con Selenium en: {DYNAMIC_SITE_URL}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get(DYNAMIC_SITE_URL)
        driver.implicitly_wait(7)
        
        selectors = load_cached_selectors()
        
        # Intentar extraer elementos con los selectores actuales
        cards = driver.find_elements(By.CSS_SELECTOR, selectors["card"])
        
        # Si no encontramos ningún elemento (ej: la estructura de Mercado Libre cambió o estamos usando la simulación rota)
        if not cards:
            logger.warning("No se encontraron tarjetas de productos. Activando Azure OpenAI para re-generar selectores...")
            
            # Capturar el HTML del body para pasárselo al LLM
            body_html = driver.find_element(By.TAG_NAME, "body").get_attribute("outerHTML")
            snippet = body_html[:6000] # Fragmento representativo
            
            # Consultar al LLM para re-deducir
            logger.info("Solicitando nuevos selectores a Azure OpenAI...")
            new_card = generate_css_selector(snippet, "el contenedor principal de un item de producto en una lista de busqueda", DEFAULT_SELECTORS["card"])
            
            selectors["card"] = new_card
            cards = driver.find_elements(By.CSS_SELECTOR, new_card)
            
            if cards:
                card_snippet = cards[0].get_attribute("outerHTML")
                new_title = generate_css_selector(card_snippet, "el nombre del producto o titulo", DEFAULT_SELECTORS["title"])
                new_price = generate_css_selector(card_snippet, "el precio o valor numerico del producto", DEFAULT_SELECTORS["price"])
                new_url = generate_css_selector(card_snippet, "el enlace o link del producto", DEFAULT_SELECTORS["url"])
                
                selectors["title"] = new_title
                selectors["price"] = new_price
                selectors["url"] = new_url
                
                save_cached_selectors(selectors)
                logger.info(f"Nuevos selectores guardados: {selectors}")
            else:
                logger.error("El LLM no pudo resolver el selector del contenedor principal de la lista.")
                return
        
        # Iniciar extracción con los selectores listos
        scraped_urls = []
        
        # Limitar a los primeros 10 productos para evitar sobrecargar la BD en la prueba corta
        for card in cards[:10]:
            try:
                # Extraer título
                title_elem = card.find_element(By.CSS_SELECTOR, selectors["title"])
                title = title_elem.text.strip()
                
                # Extraer precio (limpiándolo para convertirlo a float)
                price_elem = card.find_element(By.CSS_SELECTOR, selectors["price"])
                price_text = price_elem.text.strip().replace('$', '').replace('¢', '').replace('.', '').replace(',', '').strip()
                
                # Para Mercado Libre Costa Rica: el precio viene sin decimales, ej "450000"
                # Limpiar texto no numérico
                clean_price = "".join([c for c in price_text if c.isdigit()])
                price = float(clean_price) if clean_price else 0.0
                
                # Extraer URL del producto
                url_elem = card.find_element(By.CSS_SELECTOR, selectors["url"])
                url = url_elem.text.strip() if url_elem.tag_name != 'a' else url_elem.get_attribute("href")
                
                if not url or not title:
                    continue
                    
                scraped_urls.append(url)
                
                # Guardar/Actualizar usando el gestor centralizado
                status, prev_price = save_product(title, price, url)
                
                if status is True:
                    msg = f"Nuevo producto detectado: {title} (${price}) - URL: {url}"
                    logger.info(msg)
                    log_event("NEW_PRODUCT", f"Nuevo: {title[:30]}...", msg)
                elif status is False:
                    msg = f"Producto modificado: '{title}' cambio precio de ${prev_price} a ${price}"
                    logger.info(msg)
                    log_event("UPDATED_PRODUCT", f"Modificado: {title[:30]}...", msg)
                else:
                    logger.info(f"Producto sin cambios: {title[:40]}...")
                        
            except Exception as item_err:
                # Omitir logs ruidosos para elementos vacíos publicitarios de Mercado Libre
                pass
                
        # --- Detección de Productos Eliminados del Origen ---
        try:
            db_products = get_all_products()
            # Solo comparar eliminación si logramos extraer productos en esta ronda
            if scraped_urls:
                for db_prod in db_products:
                    db_url = db_prod['url']
                    db_title = db_prod['title']
                    
                    # Evitar borrar productos locales si estamos alternando de sitio (real vs local)
                    if db_url.startswith("https://") and DYNAMIC_SITE_URL.startswith("https://"):
                        if db_url not in scraped_urls:
                            delete_product(db_url)
                            msg = f"Producto eliminado en origen. Eliminado de la BD: {db_title}"
                            logger.info(msg)
                            log_event("DELETED_PRODUCT", f"Eliminado: {db_title[:30]}...", msg)
                    elif "localhost" in DYNAMIC_SITE_URL and "localhost" in db_url:
                        if db_url not in scraped_urls:
                            delete_product(db_url)
                            msg = f"Producto eliminado en origen. Eliminado de la BD: {db_title}"
                            logger.info(msg)
                            log_event("DELETED_PRODUCT", f"Eliminado: {db_title[:30]}...", msg)
                    
        except Exception as del_err:
            logger.error(f"Error detectando productos eliminados: {del_err}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Fallo general en el scraper dinámico: {e}", exc_info=True)
        log_event("ERROR", "Fallo Scraper Dinámico", str(e))
    finally:
        if driver:
            driver.quit()
            
    logger.info("Scraper dinámico finalizado.")

if __name__ == "__main__":
    run_dynamic_scraper()
