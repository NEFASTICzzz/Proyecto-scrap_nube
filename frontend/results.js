// Módulo de Renderizado de Productos Escrapeados (UTN)

async function fetchProducts() {
    try {
        const response = await fetch('/api/results');
        if (!response.ok) throw new Error('Error al consultar productos');
        
        const products = await response.json();
        renderProducts(products);
        updateProductMetric(products.length);
    } catch (error) {
        console.error('Error fetching products:', error);
        document.getElementById('products-tbody').innerHTML = `
            <tr><td colspan="5" class="text-center text-danger">Fallo al conectar con la API</td></tr>
        `;
    }
}

function renderProducts(products) {
    const tbody = document.getElementById('products-tbody');
    if (products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No hay productos guardados en PostgreSQL aún.</td></tr>`;
        return;
    }

    tbody.innerHTML = products.map(prod => {
        // Formatear fecha
        const date = new Date(prod.last_updated).toLocaleString();
        
        return `
            <tr id="product-row-${prod.id}">
                <td><strong>#${prod.id}</strong></td>
                <td>${prod.title}</td>
                <td><span class="text-success fw-bold">$${parseFloat(prod.price).toFixed(2)}</span></td>
                <td><a href="${prod.url}" target="_blank" class="text-info text-decoration-none small text-truncate d-inline-block" style="max-width: 250px;">${prod.url}</a></td>
                <td><span class="text-muted">${date}</span></td>
            </tr>
        `;
    }).join('');
}

function updateProductMetric(count) {
    document.getElementById('count-products').innerText = count;
}

// Configurar filtro de búsqueda
document.getElementById('search-products').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#products-tbody tr');
    
    rows.forEach(row => {
        const titleCell = row.cells[1];
        if (titleCell) {
            const titleText = titleCell.textContent.toLowerCase();
            if (titleText.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
});
