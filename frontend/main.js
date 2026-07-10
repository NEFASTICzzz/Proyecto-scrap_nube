// Controlador Principal de la Interfaz (UTN)

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    refreshAll();
    initCalendar();
});

// Cambiar de vistas en el sidebar
function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            // Quitar clase activa de nav items
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            // Mostrar la sección correspondiente
            const target = item.getAttribute("data-target");
            sections.forEach(sec => {
                if (sec.id === target) {
                    sec.classList.add("active");
                } else {
                    sec.classList.remove("active");
                }
            });

            // Si es la sección del calendario, refrescarlo para ajustar tamaño
            if (target === "calendar-section") {
                setTimeout(() => {
                    refreshCalendar();
                }, 100);
            }
        });
    });
}

// Sincronizar todos los datos de la interfaz
function refreshAll() {
    fetchProducts();
    fetchFiles();
    fetchRecentEvents();
    refreshCalendar();
}

// Cargar historial rápido en el Panel Principal
async function fetchRecentEvents() {
    try {
        const response = await fetch('/api/events');
        if (!response.ok) throw new Error('Error trayendo alertas');
        
        const events = await response.json();
        const tbody = document.getElementById("recent-events-tbody");
        
        if (events.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No se registran alertas recientes.</td></tr>`;
            return;
        }

        // Mostrar solo los últimos 5 para la tabla resumida
        const recent = events.slice(0, 5);
        
        tbody.innerHTML = recent.map(ev => {
            const date = new Date(ev.timestamp).toLocaleTimeString();
            let badgeClass = 'bg-primary';
            
            if (ev.event_type.startsWith('NEW')) badgeClass = 'bg-success';
            else if (ev.event_type.startsWith('UPDATED')) badgeClass = 'bg-warning text-dark';
            else if (ev.event_type.startsWith('DELETED')) badgeClass = 'bg-danger';
            else if (ev.event_type === 'ERROR') badgeClass = 'bg-danger';
            
            return `
                <tr>
                    <td><span class="badge ${badgeClass}">${ev.event_type}</span></td>
                    <td><strong>${ev.title}</strong></td>
                    <td class="text-muted small">${ev.description}</td>
                    <td>${date}</td>
                </tr>
            `;
        }).join('');
        
    } catch (err) {
        console.error("Error trayendo historial:", err);
        document.getElementById("recent-events-tbody").innerHTML = `
            <tr><td colspan="4" class="text-center text-danger">Error al cargar alertas del Panel</td></tr>
        `;
    }
}

// Probar selector con Azure OpenAI desde la UI
async function testLlmSelector() {
    const htmlSnippet = document.getElementById("llm-html").value;
    const description = document.getElementById("llm-description").value;
    const waiting = document.getElementById("llm-result-waiting");
    const resultContainer = document.getElementById("llm-result-container");

    if (!htmlSnippet || !description) {
        alert("Por favor completa el HTML y la descripción.");
        return;
    }

    waiting.classList.remove("d-none");
    resultContainer.innerHTML = "";

    try {
        const response = await fetch('/api/llm/generate-selector', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                html: htmlSnippet,
                description: description
            })
        });

        if (!response.ok) throw new Error("Fallo en la consulta de selectores");
        const data = await response.json();

        waiting.classList.add("d-none");
        resultContainer.innerHTML = `
            <h5 class="text-success mb-2">¡Selector CSS Generado Exitosamente!</h5>
            <div class="selector-output">${data.selector}</div>
            <p class="text-muted mt-3 small">Selector retornado por el modelo gpt-4o-mini de Azure OpenAI</p>
        `;
    } catch (error) {
        waiting.classList.add("d-none");
        resultContainer.innerHTML = `
            <div class="alert alert-danger w-100">
                <i class="fa-solid fa-triangle-exclamation me-2"></i> Error: ${error.message}
            </div>
        `;
    }
}
