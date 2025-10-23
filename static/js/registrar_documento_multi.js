// File: static/js/registrar_documento_multi.js

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('formRegistroMulti');
    const defaultDateInput = document.getElementById('fecha_entrega_default');
    const checkboxes = document.querySelectorAll('.doc-checkbox');

    // 1. Manejar la visibilidad de los detalles al marcar un documento
    checkboxes.forEach(checkbox => {
        const item = checkbox.closest('.document-item-multi');
        const details = item.querySelector('.doc-details');
        
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                details.style.display = 'block';
                // Copiar la fecha por defecto al input individual
                const individualDateInput = item.querySelector('.doc-fecha-entrega');
                individualDateInput.value = defaultDateInput.value;
            } else {
                details.style.display = 'none';
            }
        });
    });

    // 2. Aplicar la fecha por defecto a todos los marcados cuando cambia la fecha por defecto
    defaultDateInput.addEventListener('change', () => {
        const newDate = defaultDateInput.value;
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const item = checkbox.closest('.document-item-multi');
                const individualDateInput = item.querySelector('.doc-fecha-entrega');
                individualDateInput.value = newDate;
            }
        });
    });

    // 3. Validar y construir los datos antes de enviar el formulario
    form.addEventListener('submit', function(e) {
        let documentosAEnviar = [];
        let hayDocumentosMarcados = false;
        
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                hayDocumentosMarcados = true;
                const docId = checkbox.value;
                const item = checkbox.closest('.document-item-multi');
                const fechaEntrega = item.querySelector('.doc-fecha-entrega').value;
                const observaciones = item.querySelector('textarea').value;
                const nombreDoc = item.querySelector('label').textContent.trim();
                
                // Validación de fecha (doble chequeo)
                const fecha = new Date(fechaEntrega);
                const hoy = new Date();
                hoy.setHours(0, 0, 0, 0);

                if (!fechaEntrega) {
                    e.preventDefault();
                    alert(`Debe ingresar la fecha de entrega para el documento: ${nombreDoc}`);
                    return; // Detiene el bucle (pero no el submit, necesitamos preventDefault)
                }
                
                if (fecha > hoy) {
                    e.preventDefault();
                    alert(`La fecha de entrega de ${nombreDoc} no puede ser futura.`);
                    return; // Detiene el bucle (pero no el submit, necesitamos preventDefault)
                }

                documentosAEnviar.push({
                    tipo_doc_id: docId,
                    fecha_entrega: fechaEntrega,
                    observaciones: observaciones
                });
            }
        });
        
        if (e.defaultPrevented) return; // Si alguna alerta detuvo el proceso, salimos

        if (!hayDocumentosMarcados) {
            e.preventDefault();
            alert('Debe seleccionar al menos un documento para registrar.');
            return;
        }

        // CONFIRMACIÓN
        const count = documentosAEnviar.length;
        if (!confirm(`¿Confirma el registro de ${count} documento(s) para este alumno?`)) {
             e.preventDefault();
             return;
        }
        
        // El envío con Flask usando arrays es complejo, la mejor práctica aquí es serializar los datos y enviarlos en un campo oculto 
        // o usar Fetch API para enviar un JSON.
        // Puesto que ya estás enviando por POST, vamos a enviar los datos vía campos ocultos para cada documento:
        
        // Limpiamos los inputs originales (solo enviamos lo necesario)
        form.querySelectorAll('input[name^="fecha_entrega_"], textarea[name^="observaciones_"]').forEach(el => el.remove());
        form.querySelectorAll('input[name="doc_id"]').forEach(el => el.remove());
        
        // Creamos un input oculto JSON con todos los datos que queremos enviar
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'documentos_json'; // El nombre que usaremos en Flask
        hiddenInput.value = JSON.stringify(documentosAEnviar);
        form.appendChild(hiddenInput);

        // Si usaste preventDefault previamente, el submit se detendrá.
        // Si todo es exitoso, el formulario se enviará normalmente con el campo oculto.
    });
});