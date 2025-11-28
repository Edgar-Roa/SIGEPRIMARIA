        let map, markersGroup, allLayers = [];

        document.addEventListener('DOMContentLoaded', function() {
            const escuelasRaw = {{ escuelas_json | tojson }};
            console.log("🏫 Escuelas recibidas:", escuelasRaw.length);

            function getLatLngFrom(escuela) {
                const lat = parseFloat(escuela.latitud);
                const lng = parseFloat(escuela.longitud);
                return { lat, lng };
            }

            let validCount = 0;
            (escuelasRaw || []).forEach((e) => {
                const {lat, lng} = getLatLngFrom(e);
                if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) validCount++;
            });

            console.log(`✅ Escuelas con coordenadas válidas: ${validCount}`);

            if (!Array.isArray(escuelasRaw) || validCount === 0) {
                document.getElementById('loading-map').innerHTML = '<p class="no-results">❌ No hay escuelas disponibles en el mapa.</p>';
                return;
            }

            initializeMap(escuelasRaw, validCount);
        });

        function initializeMap(escuelasRaw, totalValidas) {
            document.getElementById('loading-map').style.display = 'none';
            document.getElementById('map').style.display = 'block';

            map = L.map('map').setView([19.4326, -99.1332], 10);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
                maxZoom: 18, 
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            markersGroup = L.markerClusterGroup({
                maxClusterRadius: 80,
                disableClusteringAtZoom: 17
            });

            L.Icon.Default.mergeOptions({
                iconUrl: '/static/imagenes/marker-icon.png',
                shadowUrl: '/static/imagenes/marker-shadow.png'
            });

            const schoolIcon = L.icon({
                iconUrl: '/static/imagenes/marker-icon.png',   // usar icono por defecto local
                shadowUrl: '/static/imagenes/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            });

            let escuelasValidas = 0;
            (escuelasRaw || []).forEach(escuela => {
                const lat = parseFloat(escuela.latitud);
                const lng = parseFloat(escuela.longitud);

                if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                    const popupContent = `
                        <div class="school-popup">
                            <h3>${escuela.nombre || 'Sin nombre'}</h3>
                            <p><span class="cct-badge">${escuela.cct || 'N/A'}</span></p>
                            <p><i class="fas fa-map-marker-alt"></i> <strong>${escuela.municipio || 'Municipio desconocido'}</strong></p>
                            <p>${escuela.direccion || 'Dirección no disponible'}</p>
                            <p><strong>Turno:</strong> ${escuela.turno || 'N/A'}</p>
                            <p><strong>Cupo:</strong> ${escuela.cupo_total || 'N/A'} estudiantes</p>
                        </div>
                    `;
                    const marker = L.marker([lat, lng], {icon: schoolIcon})
                        .bindPopup(popupContent);
                    marker.schoolData = escuela;
                    markersGroup.addLayer(marker);
                    allLayers.push(marker);
                    escuelasValidas++;
                }
            });

            map.addLayer(markersGroup);
            actualizarStats(escuelasValidas);
            console.log(`✅ ${escuelasValidas} marcadores creados`);
        }

        function actualizarStats(cantidad) {
            document.getElementById('stats-text').textContent = `📍 ${cantidad} escuelas en el mapa`;
        }

        window.buscarEscuela = function() {
            const texto = document.getElementById('buscador').value.toLowerCase().trim();
            
            if (!texto) {
                markersGroup.clearLayers();
                allLayers.forEach(m => markersGroup.addLayer(m));
                map.setView([19.4326, -99.1332], 10);
                actualizarStats(allLayers.length);
                return;
            }

            const resultados = allLayers.filter(marker => {
                const e = marker.schoolData || {};
                const nombre = (e.nombre || '').toLowerCase();
                const cct = (e.cct || '').toLowerCase();
                const mun = (e.municipio || '').toLowerCase();
                return nombre.includes(texto) || cct.includes(texto) || mun.includes(texto);
            });

            markersGroup.clearLayers();
            if (resultados.length > 0) {
                resultados.forEach(m => markersGroup.addLayer(m));
                map.fitBounds(markersGroup.getBounds().pad(0.1));
                actualizarStats(resultados.length);
            } else {
                markersGroup.clearLayers();
                allLayers.forEach(m => markersGroup.addLayer(m));
                alert("❌ No se encontraron escuelas con ese criterio.");
                actualizarStats(allLayers.length);
            }
        };

        window.limpiarBusqueda = function() {
            document.getElementById('buscador').value = '';
            markersGroup.clearLayers();
            allLayers.forEach(m => markersGroup.addLayer(m));
            map.setView([19.4326, -99.1332], 10);
            actualizarStats(allLayers.length);
        };

        // Permitir búsqueda con Enter
        document.addEventListener('DOMContentLoaded', function() {
            const input = document.getElementById('buscador');
            if (input) {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') buscarEscuela();
                });
            }
        });

        // ...existing code...
(function(){
    const escuelasRaw = window.escuelasRaw || [];
    let map, markersGroup, allLayers = [];

    // usar iconos locales (asegura que existan en static/imagenes)
    L.Icon.Default.mergeOptions({
        iconUrl: '/static/imagenes/marker-icon.png',
        shadowUrl: '/static/imagenes/marker-shadow.png'
    });

    function init() {
        console.log("🏫 Escuelas recibidas:", escuelasRaw.length);

        // contar válidos
        const validCount = escuelasRaw.reduce((acc,e)=> {
            const lat = parseFloat(e.latitud); const lng = parseFloat(e.longitud);
            return acc + ((!isNaN(lat)&&!isNaN(lng)&&lat!==0&&lng!==0)?1:0);
        },0);
        console.log("✅ Con coordenadas válidas:", validCount);

        if (validCount === 0) {
            document.getElementById('loading-map').innerHTML = '<p class="no-results">❌ No hay escuelas disponibles en el mapa.</p>';
            return;
        }

        // inicializar mapa
        map = L.map('map').setView([19.4326, -99.1332], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18, attribution:'© OpenStreetMap'}).addTo(map);
        markersGroup = L.markerClusterGroup({ maxClusterRadius:80, disableClusteringAtZoom:17 });

        // crear marcadores (en lote rápido)
        const icon = L.icon({
            iconUrl: '/static/imagenes/marker-icon.png',
            shadowUrl: '/static/imagenes/marker-shadow.png',
            iconSize:[25,41], iconAnchor:[12,41], popupAnchor:[1,-34], shadowSize:[41,41]
        });

        let escuelasValidas = 0;
        for (let i=0;i<escuelasRaw.length;i++){
            const e = escuelasRaw[i];
            const lat = parseFloat(e.latitud); const lng = parseFloat(e.longitud);
            if (isNaN(lat)||isNaN(lng)||lat===0||lng===0) continue;
            const popup = `<div class="school-popup"><h3>${e.nombre||''}</h3><p><span class="cct-badge">CCT: ${e.cct||''}</span></p><p>${e.direccion||''}</p><p><strong>Municipio:</strong> ${e.municipio||''}</p></div>`;
            const m = L.marker([lat,lng],{icon}).bindPopup(popup);
            m.schoolData = e;
            allLayers.push(m);
            markersGroup.addLayer(m);
            escuelasValidas++;
        }

        document.getElementById('loading-map').style.display = 'none';
        document.getElementById('map').style.display = 'block';
        map.addLayer(markersGroup);

        // poblar filtros y estadísticas
        poblarFiltros(escuelasRaw);
        actualizarStats(escuelasValidas);
        document.getElementById('filter-count-num').textContent = escuelasValidas;
    }

    function poblarFiltros(escuelas){
        const muniSet = new Set(), turnoSet = new Set();
        (escuelas||[]).forEach(e=>{ if (e.municipio) muniSet.add((e.municipio+'').trim()); if (e.turno) turnoSet.add((e.turno+'').trim()); });
        const sel = document.getElementById('f-municipio'); sel.innerHTML = '<option value="">— Todos —</option>';
        Array.from(muniSet).sort().forEach(m=>{ const o=document.createElement('option'); o.value=m; o.textContent=m; sel.appendChild(o); });
        const div = document.getElementById('f-turnos'); div.innerHTML = '';
        Array.from(turnoSet).sort().forEach(t=>{ const id='turno-'+t.replace(/\s+/g,'_'); const lbl=document.createElement('label'); lbl.style.marginRight='6px'; const cb=document.createElement('input'); cb.type='checkbox'; cb.value=t; cb.className='f-turno'; lbl.appendChild(cb); lbl.appendChild(document.createTextNode(' '+t)); div.appendChild(lbl); });
        document.getElementById('filter-sidebar').style.display = 'block';
    }

    function aplicarFiltros(){
        const muni = (document.getElementById('f-municipio').value||'').toLowerCase().trim();
        const cupoMin = parseInt(document.getElementById('f-cupo-min').value) || 0;
        const cupoMaxVal = document.getElementById('f-cupo-max').value; const cupoMax = cupoMaxVal ? parseInt(cupoMaxVal) : Infinity;
        const checkedTurnos = Array.from(document.querySelectorAll('.f-turno:checked')).map(i=>i.value.toLowerCase().trim());
        markersGroup.clearLayers();
        let mostradas = 0;
        allLayers.forEach(marker=>{
            const e = marker.schoolData || {};
            const matchesMuni = !muni || (String(e.municipio||'').toLowerCase().indexOf(muni)!==-1);
            const turnoOk = checkedTurnos.length===0 || checkedTurnos.includes(String(e.turno||'').toLowerCase().trim());
            const cupo = Number(e.cupo_total) || 0;
            const cupoOk = cupo >= cupoMin && cupo <= cupoMax;
            if (matchesMuni && turnoOk && cupoOk){ markersGroup.addLayer(marker); mostradas++; }
        });
        if (mostradas>0){ map.addLayer(markersGroup); try{ map.fitBounds(markersGroup.getBounds().pad(0.1)); }catch(e){} } else { map.removeLayer(markersGroup); }
        actualizarStats(mostradas); document.getElementById('filter-count-num').textContent = mostradas;
    }

    function limpiarFiltros(){
        document.getElementById('f-municipio').value=''; document.getElementById('f-cupo-min').value=''; document.getElementById('f-cupo-max').value='';
        document.querySelectorAll('.f-turno').forEach(c=>c.checked=false);
        markersGroup.clearLayers(); allLayers.forEach(m=>markersGroup.addLayer(m)); map.addLayer(markersGroup); actualizarStats(allLayers.length); document.getElementById('filter-count-num').textContent = allLayers.length;
    }

    function actualizarStats(cantidad){ document.getElementById('stats-text').textContent = `📍 ${cantidad} escuelas en el mapa`; }

    window.buscarEscuela = function(){
        const texto = (document.getElementById('buscador').value||'').toLowerCase().trim();
        markersGroup.clearLayers();
        if (!texto){ allLayers.forEach(m=>markersGroup.addLayer(m)); map.setView([19.4326, -99.1332],10); actualizarStats(allLayers.length); return; }
        const resultados = allLayers.filter(marker=>{ const e = marker.schoolData||{}; return (e.nombre||'').toLowerCase().includes(texto) || (e.cct||'').toLowerCase().includes(texto) || (e.municipio||'').toLowerCase().includes(texto); });
        if (resultados.length>0){ resultados.forEach(m=>markersGroup.addLayer(m)); map.fitBounds(markersGroup.getBounds().pad(0.1)); actualizarStats(resultados.length); } else { allLayers.forEach(m=>markersGroup.addLayer(m)); alert('No se encontraron escuelas con ese criterio.'); actualizarStats(allLayers.length); }
    };

    window.limpiarBusqueda = function(){ document.getElementById('buscador').value=''; markersGroup.clearLayers(); allLayers.forEach(m=>markersGroup.addLayer(m)); map.setView([19.4326, -99.1332],10); actualizarStats(allLayers.length); };

    // eventos botones
    document.addEventListener('click', function(e){
        if (e.target && e.target.id === 'btn-apply-filters') aplicarFiltros();
        if (e.target && e.target.id === 'btn-clear-filters') limpiarFiltros();
    });

    // iniciar
    document.addEventListener('DOMContentLoaded', function(){ init(); });
})();
 // ...existing code...