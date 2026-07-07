-- SCRIPT SQL COMPLETO DE LA BD LLENA DE RESPALDO (UTN)

-- 1. Crear estructura de tablas si no existen
CREATE TABLE IF NOT EXISTS scraped_products (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scraped_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    file_size INTEGER NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Limpiar registros anteriores antes de poblar la base
TRUNCATE TABLE scraped_products RESTART IDENTITY CASCADE;
TRUNCATE TABLE scraped_files RESTART IDENTITY CASCADE;
TRUNCATE TABLE events_log RESTART IDENTITY CASCADE;

-- 3. Cargar datos de prueba de Productos
INSERT INTO scraped_products (title, price, url, scraped_at, last_updated) VALUES
('Laptop Gamer Ryzen 7', 1250.00, 'https://tiendamock.com/laptop-gaming-1', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour'),
('Teclado Mecanico RGB', 89.99, 'https://tiendamock.com/teclado-rgb-2', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
('Monitor 144Hz IPS 27', 249.99, 'https://tiendamock.com/monitor-27-3', CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP - INTERVAL '30 minutes'),
('Mouse Inalámbrico Pro', 59.99, 'https://tiendamock.com/mouse-pro-4', CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP - INTERVAL '1 hour');

-- 4. Cargar datos de prueba de Archivos (SHA-256 Hashes)
INSERT INTO scraped_files (filename, original_url, sha256_hash, file_size, downloaded_at) VALUES
('documento_1.txt', 'http://localhost:5000/mock/downloads/documento_1.txt', 'b5a2c9629b35ffb0d3047c1ec08847d1754f738f6cf9c7c3b7a5a8f79fbe5843', 1024, CURRENT_TIMESTAMP - INTERVAL '1 hour'),
('documento_2.txt', 'http://localhost:5000/mock/downloads/documento_2.txt', '1f5c6e838e1215b223405786a4ff5920a6e9a7e6514757cff58d24b615ae1c11', 2048, CURRENT_TIMESTAMP - INTERVAL '1 hour'),
('documento_3.txt', 'http://localhost:5000/mock/downloads/documento_3.txt', '3e76a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0', 512, CURRENT_TIMESTAMP - INTERVAL '30 minutes');

-- 5. Cargar registro de eventos iniciales
INSERT INTO events_log (event_type, title, description, timestamp) VALUES
('NEW_PRODUCT', 'Nuevo: Laptop Gamer Ryzen 7', 'Nuevo producto detectado: Laptop Gamer Ryzen 7 ($1250.00)', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
('NEW_FILE', 'Archivo: documento_1.txt', 'Nuevo archivo detectado y guardado: documento_1.txt', CURRENT_TIMESTAMP - INTERVAL '1 hour'),
('UPDATED_PRODUCT', 'Modificado: Monitor 144Hz IPS 27', 'Producto modificado: Monitor 144Hz IPS 27 cambio de precio de $259.99 a $249.99', CURRENT_TIMESTAMP - INTERVAL '30 minutes');
