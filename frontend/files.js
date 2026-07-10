// Módulo de Visualización de Archivos Descargados (UTN)

async function fetchFiles() {
    try {
        const response = await fetch('/api/files');
        if (!response.ok) throw new Error('Error al consultar archivos');
        
        const files = await response.json();
        renderFiles(files);
        updateFilesMetric(files.length);
    } catch (error) {
        console.error('Error fetching files:', error);
        document.getElementById('files-tbody').innerHTML = `
            <tr><td colspan="5" class="text-center text-danger">Fallo al conectar con la API</td></tr>
        `;
    }
}

function renderFiles(files) {
    const tbody = document.getElementById('files-tbody');
    if (files.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No hay archivos registrados.</td></tr>`;
        return;
    }

    tbody.innerHTML = files.map(file => {
        // Formatear fecha
        const date = new Date(file.downloaded_at).toLocaleString();
        // Convertir tamaño a KB
        const sizeKb = (file.file_size / 1024).toFixed(2);
        
        return `
            <tr>
                <td>
                    <i class="fa-regular fa-file-code text-primary me-2"></i>
                    <strong>${file.filename}</strong>
                </td>
                <td><span class="badge bg-dark">${sizeKb} KB</span></td>
                <td>${date}</td>
                <td><span class="hash-text" title="${file.sha256_hash}">${file.sha256_hash.substring(0, 16)}...</span></td>
                <td>
                    <span class="badge bg-success-subtle text-success border border-success-subtle">
                        <i class="fa-solid fa-circle-check me-1"></i> Verificado (SHA-256)
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

function updateFilesMetric(count) {
    document.getElementById('count-files').innerText = count;
}
