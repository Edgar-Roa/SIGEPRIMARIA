document.addEventListener('DOMContentLoaded', function() {
    
    // 1. OBTENER DATOS (Puente con HTML)
    const escuelas = window.datosEscuelas || [];
    console.log(`✅ JS Iniciado. Escuelas cargadas: ${escuelas.length}`);

    if (escuelas.length === 0) {
        document.getElementById('loading-map').innerHTML = "⚠️ No hay datos de escuelas disponibles.";
        return;
    }

    // 2. INICIALIZAR MAPA
    const map = L.map('map').setView([19.4326, -99.1332], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const markersGroup = L.markerClusterGroup({
        maxClusterRadius: 60,
        disableClusteringAtZoom: 16
    });

    // 3. ICONO SVG (Punto Guinda con borde blanco)
    const schoolIcon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background-color:#9d2449; width:14px; height:14px; border-radius:50%; border:2px solid white; box-shadow:0 2px 4px rgba(0,0,0,0.4);"></div>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
        popupAnchor: [0, -10]
    });

    // 4. LLENAR SELECT DE MUNICIPIOS
    const municipios = [...new Set(escuelas.map(e => (e.municipio || '').trim().toUpperCase()))].sort();
    const selectMuni = document.getElementById('filtro-municipio');
    
    municipios.forEach(m => {
        if(m) {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            selectMuni.appendChild(opt);
        }
    });

    // 5. FUNCIÓN PRINCIPAL: PINTAR MAPA
    window.actualizarMapa = function(lista, mostrarAlerta = false) {
        markersGroup.clearLayers();
        const nuevosMarcadores = [];

        lista.forEach(e => {
            // Conversión segura a números
            const lat = parseFloat(e.latitud);
            const lng = parseFloat(e.longitud);

            if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                
                // --- NUEVO DISEÑO DE POPUP (Estilo Tarjeta CFE) ---
                const popupHTML = `
                    <div class="custom-popup">
                        <div class="popup-header">
                            <i class="fas fa-school"></i>
                            <h3>${e.nombre}</h3>
                        </div>
                        <div class="popup-body">
                            <div class="popup-row">
                                <span class="popup-label">Ubicación</span>
                                <span class="popup-value">${e.municipio}, Ciudad de México</span>
                            </div>
                            <div class="popup-row">
                                <span class="popup-label">Dirección</span>
                                <span class="popup-value">
                                    <i class="fas fa-map-marker-alt" style="color:#d1a84f; margin-right:4px;"></i>
                                    ${e.direccion || 'Domicilio Conocido'}
                                </span>
                            </div>
                            <div class="popup-row">
                                <span class="popup-label">Turno</span>
                                <span class="popup-value">${e.turno}</span>
                            </div>
                            
                            <div class="info-badges">
                                <div class="badge-item">CCT: <strong>${e.cct}</strong></div>
                                <div class="badge-item">Cupo: <strong>${e.cupo_total}</strong></div>
                            </div>
                        </div>
                    </div>
                `;
                // ---------------------------------------------

                const m = L.marker([lat, lng], {icon: schoolIcon}).bindPopup(popupHTML);
                nuevosMarcadores.push(m);
            }
        });

        markersGroup.addLayers(nuevosMarcadores);
        map.addLayer(markersGroup);
        
        document.getElementById('contador-escuelas').textContent = nuevosMarcadores.length.toLocaleString();

        if (nuevosMarcadores.length > 0) {
            if (nuevosMarcadores.length < 1000) {
                map.fitBounds(markersGroup.getBounds().pad(0.1));
            }
        } else if (mostrarAlerta) {
            Swal.fire({
                icon: 'info',
                title: 'Sin resultados',
                text: 'No se encontraron escuelas con los criterios seleccionados.',
                confirmButtonColor: '#9d2449'
            });
        }
    };

    // 6. FILTRADO
    window.aplicarFiltros = function() {
        const texto = document.getElementById('filtro-texto').value.toLowerCase().trim();
        const muni = document.getElementById('filtro-municipio').value;
        const turno = document.getElementById('filtro-turno').value;

        const filtradas = escuelas.filter(e => {
            const eNombre = (e.nombre || '').toLowerCase();
            const eCCT = (e.cct || '').toLowerCase();
            const eMuni = (e.municipio || '').toUpperCase().trim();
            const eTurno = (e.turno || '').toUpperCase();

            const matchTexto = !texto || eNombre.includes(texto) || eCCT.includes(texto) || eMuni.toLowerCase().includes(texto);
            const matchMuni = !muni || eMuni === muni;
            const matchTurno = !turno || eTurno.includes(turno);

            return matchTexto && matchMuni && matchTurno;
        });

        actualizarMapa(filtradas, true);
    };

    window.limpiarFiltros = function() {
        document.getElementById('filtro-texto').value = "";
        document.getElementById('filtro-municipio').value = "";
        document.getElementById('filtro-turno').value = "";
        actualizarMapa(escuelas, false);
        map.setView([19.4326, -99.1332], 10);
    };

    // Enter para buscar
    document.getElementById('filtro-texto').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') aplicarFiltros();
    });

    // Iniciar
    actualizarMapa(escuelas, false);
    document.getElementById('loading-map').style.display = 'none';
});