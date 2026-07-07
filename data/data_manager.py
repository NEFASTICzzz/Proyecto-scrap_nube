import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "scraping_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
os.makedirs(DATA_DIR, exist_ok=True)

RESULTS_JSON = os.path.join(DATA_DIR, 'results.json')
FILES_JSON = os.path.join(DATA_DIR, 'files.json')
EVENTS_JSON = os.path.join(DATA_DIR, 'events.json')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def is_db_available():
    """Verifica si PostgreSQL está disponible."""
    try:
        conn = get_db_connection()
        conn.close()
        return True
    except Exception:
        return False

def init_db():
    """Inicializa la base de datos PostgreSQL, creándola si no existe."""
    try:
        # Intentar conectar a 'postgres' por defecto para crear la base de datos si no existe
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"[DB Manager] Base de datos '{DB_NAME}' creada con éxito.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB Manager Warning] No se pudo verificar la base de datos en postgres default: {e}")

    # Ejecutar script database.sql para crear tablas
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql_path = os.path.join(os.path.dirname(__file__), 'database.sql')
        if os.path.exists(sql_path):
            with open(sql_path, 'r', encoding='utf-8') as f:
                cur.execute(f.read())
            conn.commit()
            print("[DB Manager] Tablas inicializadas en PostgreSQL.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB Manager Error] No se pudo conectar a PostgreSQL para crear tablas: {e}")
        print("[DB Manager] Se activará el almacenamiento local de respaldo (.json).")

# --- Auxiliares de Lectura/Escritura JSON local ---

def _read_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _write_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error escribiendo en {filepath}: {e}")

# --- OPERACIONES DE PRODUCTOS (Dynamic Scraping) ---

def get_all_products():
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM scraped_products ORDER BY last_updated DESC;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            # Convertir decimales a flotantes para serializar JSON
            for r in rows:
                r['price'] = float(r['price'])
                if isinstance(r['scraped_at'], datetime):
                    r['scraped_at'] = r['scraped_at'].isoformat()
                if isinstance(r['last_updated'], datetime):
                    r['last_updated'] = r['last_updated'].isoformat()
            return rows
        except Exception as e:
            print(f"[DB Error] get_all_products falló: {e}")
    
    # Fallback
    return _read_json(RESULTS_JSON)

def save_product(title, price, url):
    """Guarda o actualiza un producto en DB o JSON. Retorna (es_nuevo, precio_previo)."""
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT price, title FROM scraped_products WHERE url = %s;", (url,))
            row = cur.fetchone()
            
            if row is None:
                cur.execute(
                    "INSERT INTO scraped_products (title, price, url) VALUES (%s, %s, %s);",
                    (title, price, url)
                )
                conn.commit()
                cur.close()
                conn.close()
                return True, None
            else:
                db_price, db_title = row
                db_price = float(db_price)
                if db_price != price or db_title != title:
                    cur.execute(
                        "UPDATE scraped_products SET title = %s, price = %s, last_updated = CURRENT_TIMESTAMP WHERE url = %s;",
                        (title, price, url)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    return False, db_price
                
                cur.close()
                conn.close()
                return None, None  # Sin cambios
        except Exception as e:
            print(f"[DB Error] save_product falló: {e}")

    # Fallback JSON
    products = _read_json(RESULTS_JSON)
    found = None
    for p in products:
        if p['url'] == url:
            found = p
            break
            
    now_str = datetime.now().isoformat()
    if found is None:
        new_id = max([p['id'] for p in products] + [0]) + 1
        products.append({
            "id": new_id,
            "title": title,
            "price": price,
            "url": url,
            "scraped_at": now_str,
            "last_updated": now_str
        })
        _write_json(RESULTS_JSON, products)
        return True, None
    else:
        old_price = float(found['price'])
        if old_price != price or found['title'] != title:
            found['title'] = title
            found['price'] = price
            found['last_updated'] = now_str
            _write_json(RESULTS_JSON, products)
            return False, old_price
        return None, None

def delete_product(url):
    """Elimina un producto por url. Retorna título si se eliminó, None en caso contrario."""
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT title FROM scraped_products WHERE url = %s;", (url,))
            row = cur.fetchone()
            if row:
                title = row[0]
                cur.execute("DELETE FROM scraped_products WHERE url = %s;", (url,))
                conn.commit()
                cur.close()
                conn.close()
                return title
            cur.close()
            conn.close()
            return None
        except Exception as e:
            print(f"[DB Error] delete_product falló: {e}")

    # Fallback JSON
    products = _read_json(RESULTS_JSON)
    for i, p in enumerate(products):
        if p['url'] == url:
            title = p['title']
            del products[i]
            _write_json(RESULTS_JSON, products)
            return title
    return None

# --- OPERACIONES DE ARCHIVOS (Static Scraping) ---

def get_all_files():
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM scraped_files ORDER BY downloaded_at DESC;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            for r in rows:
                if isinstance(r['downloaded_at'], datetime):
                    r['downloaded_at'] = r['downloaded_at'].isoformat()
            return rows
        except Exception as e:
            print(f"[DB Error] get_all_files falló: {e}")
            
    return _read_json(FILES_JSON)

def save_file(filename, original_url, sha256_hash, file_size):
    """Guarda o actualiza un archivo. Retorna (es_nuevo, hash_previo)."""
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT sha256_hash FROM scraped_files WHERE filename = %s;", (filename,))
            row = cur.fetchone()
            
            if row is None:
                cur.execute(
                    "INSERT INTO scraped_files (filename, original_url, sha256_hash, file_size) VALUES (%s, %s, %s, %s);",
                    (filename, original_url, sha256_hash, file_size)
                )
                conn.commit()
                cur.close()
                conn.close()
                return True, None
            else:
                db_hash = row[0]
                if db_hash != sha256_hash:
                    cur.execute(
                        "UPDATE scraped_files SET sha256_hash = %s, file_size = %s, downloaded_at = CURRENT_TIMESTAMP WHERE filename = %s;",
                        (sha256_hash, file_size, filename)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    return False, db_hash
                cur.close()
                conn.close()
                return None, None
        except Exception as e:
            print(f"[DB Error] save_file falló: {e}")

    # Fallback JSON
    files = _read_json(FILES_JSON)
    found = None
    for f in files:
        if f['filename'] == filename:
            found = f
            break
            
    now_str = datetime.now().isoformat()
    if found is None:
        new_id = max([f['id'] for f in files] + [0]) + 1
        files.append({
            "id": new_id,
            "filename": filename,
            "original_url": original_url,
            "sha256_hash": sha256_hash,
            "file_size": file_size,
            "downloaded_at": now_str
        })
        _write_json(FILES_JSON, files)
        return True, None
    else:
        old_hash = found['sha256_hash']
        if old_hash != sha256_hash:
            found['sha256_hash'] = sha256_hash
            found['file_size'] = file_size
            found['downloaded_at'] = now_str
            _write_json(FILES_JSON, files)
            return False, old_hash
        return None, None

def delete_file(filename):
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM scraped_files WHERE filename = %s;", (filename,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB Error] delete_file falló: {e}")

    # Fallback JSON
    files = _read_json(FILES_JSON)
    for i, f in enumerate(files):
        if f['filename'] == filename:
            del files[i]
            _write_json(FILES_JSON, files)
            return True
    return False

# --- OPERACIONES DE EVENTOS (Logs & Calendario) ---

def get_all_events():
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM events_log ORDER BY timestamp DESC;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            for r in rows:
                if isinstance(r['timestamp'], datetime):
                    r['timestamp'] = r['timestamp'].isoformat()
            return rows
        except Exception as e:
            print(f"[DB Error] get_all_events falló: {e}")
            
    return _read_json(EVENTS_JSON)

def log_event(event_type, title, description):
    """Guarda una alerta en DB o JSON."""
    if is_db_available():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO events_log (event_type, title, description) VALUES (%s, %s, %s);",
                (event_type, title, description)
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception as e:
            print(f"[DB Error] log_event falló: {e}")

    # Fallback JSON
    events = _read_json(EVENTS_JSON)
    new_id = max([e['id'] for e in events] + [0]) + 1
    events.append({
        "id": new_id,
        "event_type": event_type,
        "title": title,
        "description": description,
        "timestamp": datetime.now().isoformat()
    })
    # Limitar tamaño de alertas en JSON a 100 para no inflar archivo
    if len(events) > 100:
        events = events[-100:]
    _write_json(EVENTS_JSON, events)
