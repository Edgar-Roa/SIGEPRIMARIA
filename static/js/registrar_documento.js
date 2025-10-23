    // Mostrar info del documento seleccionado
    document.getElementById('tipo_doc_id').addEventListener('change', function() {
      const selectedOption = this.options[this.selectedIndex];
      const descripcion = selectedOption.dataset.descripcion;
      const docInfoCard = document.getElementById('docInfoCard');
      const docDescripcion = document.getElementById('docDescripcion');
      
      if (this.value && descripcion) {
        docDescripcion.textContent = descripcion;
        docInfoCard.classList.add('show');
      } else {
        docInfoCard.classList.remove('show');
      }
    });

    // Validar fecha no futura
    document.getElementById('formRegistro').addEventListener('submit', function(e) {
      const fechaEntrega = new Date(document.getElementById('fecha_entrega').value);
      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);
      
      if (fechaEntrega > hoy) {
        e.preventDefault();
        alert('La fecha de entrega no puede ser futura');
        return false;
      }
      
      // Confirmar registro
      const tipoDoc = document.getElementById('tipo_doc_id');
      const nombreDoc = tipoDoc.options[tipoDoc.selectedIndex].text;
      
      if (!confirm(`¿Confirma el registro de: ${nombreDoc}?`)) {
        e.preventDefault();
        return false;
      }
    });