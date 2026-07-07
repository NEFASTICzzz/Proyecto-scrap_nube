-- Script SQL de inicialización de la Base de Datos para el proyecto UTN

-- Tabla para datos estructurados (Scraping Dinámico)
CREATE TABLE IF NOT EXISTS scraped_products (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para registro de archivos y hashes (Scraping Estático)
CREATE TABLE IF NOT EXISTS scraped_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    file_size INTEGER NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para alertas y eventos (Detección de cambios / Historial de FullCalendar)
CREATE TABLE IF NOT EXISTS events_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- 'NEW_PRODUCT', 'UPDATED_PRODUCT', 'DELETED_PRODUCT', 'NEW_FILE', 'UPDATED_FILE', 'DELETED_FILE', 'ERROR'
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento de búsquedas
CREATE INDEX IF NOT EXISTS idx_products_url ON scraped_products(url);
CREATE INDEX IF NOT EXISTS idx_files_hash ON scraped_files(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events_log(timestamp);
