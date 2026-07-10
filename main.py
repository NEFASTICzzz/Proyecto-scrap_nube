import os
import sys
from dotenv import load_dotenv

# Asegurar que el directorio raíz está en el path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.json_api_server import app
from data.data_manager import init_db
from scheduler import start_scheduler

load_dotenv()

def main():
    print("==================================================")
    print("  Iniciando Plataforma de Scraping y Selectores LLM")
    print("==================================================")
    
    # 1. Inicializar Base de Datos (crear base de datos y tablas si no existen)
    init_db()
    
    # 2. Iniciar el planificador de tareas (Scheduler) en segundo plano
    scheduler = start_scheduler()
    
    # 3. Arrancar el servidor web Flask (Bloqueante, corre en el hilo principal)
    port = int(os.getenv("FLASK_PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    try:
        # Nota: debug=False/use_reloader=False evita que el reloader de Flask reinicie el programador
        app.run(host='0.0.0.0', port=port, use_reloader=False, debug=debug_mode)
    except (KeyboardInterrupt, SystemExit):
        print("\nDeteniendo servicios...")
        scheduler.shutdown()
        print("Plataforma apagada.")

if __name__ == "__main__":
    main()
