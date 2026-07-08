import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request, send_from_directory, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Importar gestor de datos centralizado
from data.data_manager import init_db, get_all_products, get_all_files, get_all_events

# Directorios de simulación
MOCK_SOURCE_DIR = os.path.join(os.path.dirname(__file__), '../mock_source_files')
os.makedirs(MOCK_SOURCE_DIR, exist_ok=True)

# Crear algunos archivos mock iniciales si no existen
for i in range(1, 4):
    file_path = os.path.join(MOCK_SOURCE_DIR, f"documento_{i}.txt")
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Contenido original del documento mock numero {i}.\nHASH inicial estable.")

# --- Endpoints de API para el Dashboard ---

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/results', methods=['GET'])
def get_results():
    try:
        return jsonify(get_all_products())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    try:
        return jsonify(get_all_files())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        return jsonify(get_all_events())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Sitio Mock Estático (para descargas de archivos) ---

@app.route('/mock/static')
def mock_static_site():
    # Renderizar una página simple que contiene enlaces a los archivos
    files = os.listdir(MOCK_SOURCE_DIR)
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sitio Estático de Descarga Simulada</title>
        <style>
            body { font-family: sans-serif; margin: 40px; background: #f8f9fa; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #343a40; }
            ul { list-style: none; padding: 0; }
            li { padding: 10px; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center;}
            a { text-decoration: none; color: #007bff; font-weight: bold; }
            a:hover { text-decoration: underline; }
            .btn { background: #6c757d; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Sitio de Descarga de Archivos de la UTN</h1>
            <p>Lista de recursos disponibles para el scraper estático:</p>
            <ul>
                {% for file in files %}
                <li>
                    <span>{{ file }}</span>
                    <a href="/mock/downloads/{{ file }}" class="btn">Descargar Archivo</a>
                </li>
                {% endfor %}
            </ul>
            <p style="color: #6c757d; font-size: 0.8em; margin-top: 20px;">
                Nota: Modifica directamente los archivos en la carpeta <code>mock_source_files/</code> para alterar sus hashes SHA-256.
            </p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, files=files)

@app.route('/mock/downloads/<filename>')
def mock_download_file(filename):
    return send_from_directory(MOCK_SOURCE_DIR, filename, as_attachment=True)

# --- Sitio Mock Dinámico (para scraping con Selenium) ---

@app.route('/mock/dynamic')
def mock_dynamic_site():
    # Parámetro para forzar el cambio de selectores (para simular cambios en el DOM)
    class_type = request.args.get('class_type', 'default')
    
    # Definir clases dinámicamente
    if class_type == 'changed':
        title_class = 'item-name-alt'
        price_class = 'item-cost-alt'
        card_class = 'item-box-alt'
    else:
        title_class = 'product-title'
        price_class = 'product-price'
        card_class = 'product-card'

    # Lista mock de productos
    products = [
        {"id": 1, "title": "Laptop Gamer Ryzen 7", "price": "1250.00", "url": "https://tiendamock.com/laptop-gaming-1"},
        {"id": 2, "title": "Teclado Mecanico RGB", "price": "89.99", "url": "https://tiendamock.com/teclado-rgb-2"},
        {"id": 3, "title": "Monitor 144Hz IPS 27", "price": "249.99", "url": "https://tiendamock.com/monitor-27-3"},
        {"id": 4, "title": "Mouse Inalámbrico Pro", "price": "59.99", "url": "https://tiendamock.com/mouse-pro-4"}
    ]

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sitio de Scraping Dinámico (Simulado)</title>
        <style>
            body { font-family: sans-serif; background: #eef2f3; margin: 30px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { text-align: center; color: #2c3e50; }
            .catalog { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .{{ card_class }} { background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .{{ title_class }} { margin: 0 0 10px 0; font-size: 1.2em; color: #2c3e50; }
            .{{ price_class }} { font-weight: bold; color: #e74c3c; font-size: 1.1em; }
            .meta-info { font-size: 0.8em; color: #7f8c8d; margin-top: 10px; }
            .config-bar { background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #ddd; }
            .btn { background: #3498db; color: white; padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block;}
            .btn-orange { background: #e67e22; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Tienda de Electrónicos - UTN Cloud</h1>
            
            <div class="config-bar">
                <h3>Panel de Simulación de Cambios en la Estructura Web (DOM)</h3>
                <p>Usa los botones para cambiar las clases HTML de los productos. Esto romperá los selectores fijos y forzará al Scraper a pedirle nuevos selectores a Azure OpenAI.</p>
                <a href="/mock/dynamic?class_type=default" class="btn">Clases Estándar (product-title / product-price)</a>
                <a href="/mock/dynamic?class_type=changed" class="btn btn-orange">Cambiar Estructura DOM (item-name-alt / item-cost-alt)</a>
                <p><strong>Clase actual activa:</strong> <code>{{ class_type }}</code></p>
            </div>

            <div class="catalog">
                {% for prod in products %}
                <div class="{{ card_class }}" data-id="{{ prod.id }}">
                    <h3 class="{{ title_class }}">{{ prod.title }}</h3>
                    <div class="{{ price_class }}">${{ prod.price }}</div>
                    <div class="meta-info">Enlace original: <span class="prod-url">{{ prod.url }}</span></div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(
        html_template, 
        products=products, 
        card_class=card_class, 
        title_class=title_class, 
        price_class=price_class,
        class_type=class_type
    )

# --- Endpoint para interactuar con Azure OpenAI desde la UI ---

@app.route('/api/llm/generate-selector', methods=['POST'])
def generate_selector_api():
    try:
        data = request.get_json()
        html_snippet = data.get("html", "")
        description = data.get("description", "")
        
        if not html_snippet or not description:
            return jsonify({"error": "Falta HTML o descripción"}), 400
            
        from llm.llm_selector import generate_css_selector
        selector = generate_css_selector(html_snippet, description, ".default-selector")
        
        return jsonify({"selector": selector})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
