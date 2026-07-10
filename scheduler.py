import os
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.scraper_static import run_static_scraper
from scraper.scraper_dynamic import run_dynamic_scraper
from dotenv import load_dotenv

load_dotenv()

INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "30"))

def run_all_scrapers():
    """Ejecuta los dos scrapers de manera secuencial."""
    print(f"\n--- [Orquestador] Iniciando ciclo de scraping: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    try:
        # Ejecutar scraper estático
        run_static_scraper()
    except Exception as e:
        print(f"[Orquestador Error] Fallo en el scraper estático: {e}")
        
    try:
        # Ejecutar scraper dinámico
        run_dynamic_scraper()
    except Exception as e:
        print(f"[Orquestador Error] Fallo en el scraper dinámico: {e}")
    print("--- [Orquestador] Ciclo de scraping finalizado. ---\n")

def run_delayed_initial_scrape():
    """Espera a que el servidor Flask esté levantado antes de arrancar el primer scraping."""
    print("[Orquestador] Esperando 4 segundos a que Flask inicialice...")
    time.sleep(4)
    print("[Orquestador] Ejecutando scraping de carga inicial...")
    run_all_scrapers()

def start_scheduler():
    """Inicializa y arranca el programador de tareas en segundo plano."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_all_scrapers, 'interval', minutes=INTERVAL_MINUTES)
    scheduler.start()
    print(f"[Orquestador] Programador iniciado. Ejecución configurada cada {INTERVAL_MINUTES} minutos.")
    
    # Lanzar la carga inicial en un hilo separado de forma asíncrona para no bloquear a Flask
    threading.Thread(target=run_delayed_initial_scrape, daemon=True).start()
    
    return scheduler

if __name__ == "__main__":
    print("Iniciando orquestador independiente...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_all_scrapers, 'interval', minutes=INTERVAL_MINUTES)
    scheduler.start()
    print(f"Orquestador corriendo en primer plano. Intervalo: {INTERVAL_MINUTES} min. Presiona Ctrl+C para salir.")
    
    run_all_scrapers()
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Orquestador apagado.")
