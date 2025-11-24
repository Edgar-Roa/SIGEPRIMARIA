document.addEventListener('DOMContentLoaded', function() {
  // Referencias a los elementos del DOM
  const tipoDocSelect = document.getElementById('tipo_doc_id');
  const docInfoCard = document.getElementById('docInfoCard');
  const docDescripcion = document.getElementById('docDescripcion');
  const archivoInput = document.getElementById('archivo_digital');
  const form = document.getElementById('formRegistro');

  // 1. Mostrar info del documento seleccionado (Mantenemos tu lógica visual)
  if (tipoDocSelect) {
    tipoDocSelect.addEventListener('change', function() {
      const selectedOption = this.options[this.selectedIndex];
      // Usamos getAttribute para mayor compatibilidad o dataset
      const descripcion = selectedOption.getAttribute('data-descripcion');
      
      if (this.value && descripcion) {
        docDescripcion.textContent = descripcion;
        // Si usas una clase CSS '.show' para mostrar:
        if (docInfoCard) docInfoCard.classList.add('show');
        // O si prefieres manipular el estilo directamente:
        // docInfoCard.style.display = 'block'; 
      } else {
        if (docInfoCard) docInfoCard.classList.remove('show');
        // docInfoCard.style.display = 'none';
      }
    });
  }

  // 2. Validar el archivo AL SELECCIONARLO (Nueva funcionalidad)
  if (archivoInput) {
    archivoInput.addEventListener('change', function() {
      const file = this.files[0];
      const maxSize = 5 * 1024 * 1024; // 5MB en bytes

      if (file) {
        // A. Validar tamaño
        if (file.size > maxSize) {
          alert('El archivo es demasiado pesado. El tamaño máximo permitido es 5MB.');
          this.value = ''; // Borrar la selección
          return;
        }

        // B. Validar extensión (Doble seguridad)
        const validExtensions = ['pdf', 'jpg', 'jpeg', 'png'];
        const extension = file.name.split('.').pop().toLowerCase();
        
        if (!validExtensions.includes(extension)) {
          alert('Formato no válido. Solo se permiten archivos PDF, JPG o PNG.');
          this.value = '';
        }
      }
    });
  }

  // 3. Validar al ENVIAR el formulario
  if (form) {
    form.addEventListener('submit', function(e) {
      
      // A. Validar que se haya seleccionado un documento
      if (!tipoDocSelect.value) {
        e.preventDefault();
        alert('Por favor, seleccione el Tipo de Documento.');
        return false;
      }

      // B. Validar que se haya subido un archivo
      if (archivoInput.files.length === 0) {
        e.preventDefault();
        alert('Es obligatorio adjuntar el archivo digital.');
        return false;
      }

      // C. Confirmación (Mantenemos tu lógica de confirmación)
      const nombreDoc = tipoDocSelect.options[tipoDocSelect.selectedIndex].text.trim();
      
      if (!confirm(`¿Confirma que desea subir y registrar: ${nombreDoc}?`)) {
        e.preventDefault();
        return false;
      }

      // D. Efecto visual de carga (Opcional pero recomendado)
      const btnSubmit = form.querySelector('button[type="submit"]');
      if (btnSubmit) {
        const originalText = btnSubmit.innerText;
        btnSubmit.innerText = 'Subiendo...';
        btnSubmit.disabled = true;
        // Si el usuario cancela o hay error, esto evita que se quede pegado, 
        // aunque al enviarse el form la página recargará.
      }
    });
  }
});