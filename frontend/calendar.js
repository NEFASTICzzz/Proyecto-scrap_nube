// Módulo de Calendario de Eventos con FullCalendar (UTN)

let calendar = null;

function initCalendar() {
    const calendarEl = document.getElementById('calendar-wrapper');
    if (!calendarEl) return;

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        locale: 'es',
        themeSystem: 'standard',
        events: async function(info, successCallback, failureCallback) {
            try {
                const response = await fetch('/api/events');
                if (!response.ok) throw new Error('Error al traer eventos de la API');
                
                const events = await response.json();
                
                // Mapear eventos de PostgreSQL al formato de FullCalendar
                const formattedEvents = events.map(ev => {
                    let color = '#6366f1'; // Indigo por defecto
                    
                    if (ev.event_type.startsWith('NEW')) {
                        color = '#10b981'; // Green
                    } else if (ev.event_type.startsWith('UPDATED')) {
                        color = '#f59e0b'; // Amber / Orange
                    } else if (ev.event_type.startsWith('DELETED')) {
                        color = '#ef4444'; // Red
                    } else if (ev.event_type === 'ERROR') {
                        color = '#dc2626'; // Dark Red
                    }
                    
                    return {
                        id: ev.id,
                        title: `${ev.title} (${ev.event_type})`,
                        start: ev.timestamp,
                        backgroundColor: color,
                        borderColor: color,
                        extendedProps: {
                            description: ev.description,
                            type: ev.event_type
                        }
                    };
                });
                
                successCallback(formattedEvents);
                updateEventsMetric(events.length);
            } catch (error) {
                console.error('Error cargando eventos en el calendario:', error);
                failureCallback(error);
            }
        },
        eventClick: function(info) {
            // Mostrar modal o alert detallado al hacer click en el evento
            alert(`[${info.event.extendedProps.type}] ${info.event.title}\n\nDetalle: ${info.event.extendedProps.description}`);
        }
    });

    calendar.render();
}

function updateEventsMetric(count) {
    document.getElementById('count-events').innerText = count;
}

function refreshCalendar() {
    if (calendar) {
        calendar.refetchEvents();
    }
}
