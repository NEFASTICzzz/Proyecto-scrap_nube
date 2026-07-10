import os
import sys
import requests
import time

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.scraper_static import run_static_scraper
from scraper.scraper_dynamic import run_dynamic_scraper
from data.data_manager import get_all_products, get_all_files, get_all_events

FLASK_PORT = os.getenv("FLASK_PORT", "5000")
API_URL = f"http://localhost:{FLASK_PORT}/"

def test_system():
    print("==================================================")
    print("     Script de Pruebas y Testeo - UTN Cloud       ")
    print("==================================================")
    
    # 1. Verificar si el servidor Flask está activo
    print("\n[Paso 1] Verificando servidor Flask local...")
    try:
        res = requests.get(API_URL, timeout=5)
        if res.status_code == 200:
            print("  -> Servidor Flask: ACTIVO (Escuchando en puerto 5000)")
        else:
            print(f"  -> Servidor Flask respondió con código HTTP: {res.status_code}")
    except requests.exceptions.ConnectionError:
        print("  [ERROR] El servidor Flask no está encendido.")
        print("  Por favor abre otra consola e inicia: python main.py")
        sys.exit(1)

    # 2. Ejecutar Scraper Estático (BS4)
    print("\n[Paso 2] Ejecutando demostración de Scraper Estático (BeautifulSoup)...")
    run_static_scraper()
    
    # Obtener archivos en base de datos/almacenamiento
    files = get_all_files()
    print(f"  -> Total de archivos registrados: {len(files)}")
    for f in files:
        print(f"     - Nombre: {f['filename']} | Hash SHA-256: {f['sha256_hash'][:24]}...")

    # 3. Ejecutar Scraper Dinámico (Selenium)
    print("\n[Paso 3] Ejecutando demostración de Scraper Dinámico (Selenium)...")
    run_dynamic_scraper()
    
    # Obtener productos registrados
    products = get_all_products()
    print(f"  -> Total de productos registrados: {len(products)}")
    for p in products:
        print(f"     - Título: {p['title']} | Precio: ${p['price']} | URL: {p['url']}")

    # 4. Mostrar últimos eventos registrados (detección de cambios)
    print("\n[Paso 4] Ultimas alertas de detección de cambios (PostgreSQL/JSON):")
    events = get_all_events()
    recent_events = events[:5]
    for ev in recent_events:
        print(f"     [{ev['event_type']}] {ev['title']} - {ev['description']}")

    print("\n==================================================")
    print("      Ejecución de Prueba Finalizada con Éxito    ")
    print("==================================================")

if __name__ == "__main__":
    test_system()
