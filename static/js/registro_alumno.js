
    // Validación de CURP en tiempo real
    const curpInput = document.getElementById('curp');
    const curpError = document.getElementById('curp-error');
    const curpSuccess = document.getElementById('curp-success');
    
    let timeoutId;
    
    curpInput.addEventListener('input', function() {
      const curp = this.value.toUpperCase();
      this.value = curp;
      
      // Limpiar mensajes
      curpError.style.display = 'none';
      curpSuccess.style.display = 'none';
      this.classList.remove('error', 'success');
      
      if (curp.length !== 18) {
        return;
      }
      
      // Debounce
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        // Validar CURP
        fetch('{{url_for("registro_alumno.validar_curp")}}', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ curp: curp })
        })
        .then(response => response.json())
        .then(data => {
          if (data.valido) {
            curpInput.classList.add('success');
            curpSuccess.style.display = 'block';
          } else {
            curpInput.classList.add('error');
            curpError.textContent = data.mensaje;
            curpError.style.display = 'block';
          }
        });
      }, 500);
    });
    
    // Calcular edad automáticamente
    const fechaNacInput = document.getElementById('fecha_nacimiento');
    const edadInfo = document.getElementById('edad-info');
    
    fechaNacInput.addEventListener('change', function() {
      if (this.value) {
        const hoy = new Date();
        const nacimiento = new Date(this.value);
        let edad = hoy.getFullYear() - nacimiento.getFullYear();
        const mes = hoy.getMonth() - nacimiento.getMonth();
        
        if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
          edad--;
        }
        
        edadInfo.textContent = `Edad: ${edad} años`;
        edadInfo.style.color = (edad >= 5 && edad <= 15) ? '#28a745' : '#dc3545';
        
        if (edad < 5 || edad > 15) {
          edadInfo.textContent += ' (Fuera del rango recomendado para primaria)';
        }
      }
    });
    
    // Validación del formulario antes de enviar
    document.getElementById('formRegistro').addEventListener('submit', function(e) {
      const curp = document.getElementById('curp').value;
      
      if (curp.length !== 18) {
        e.preventDefault();
        alert('El CURP debe tener exactamente 18 caracteres');
        return false;
      }
      
      // Confirmar si no se seleccionó escuela
      const escuelaId = document.getElementById('escuela_id').value;
      const gradoId = document.getElementById('grado_id').value;
      
      if (!escuelaId && !gradoId) {
        const confirmar = confirm('No has seleccionado escuela ni grado. El alumno será registrado pero sin solicitud de inscripción. ¿Deseas continuar?');
        if (!confirmar) {
          e.preventDefault();
          return false;
        }
      }
      
      if (escuelaId && !gradoId) {
        e.preventDefault();
        alert('Si seleccionas una escuela, también debes seleccionar el grado');
        return false;
      }
      
      if (gradoId && !escuelaId) {
        e.preventDefault();
        alert('Si seleccionas un grado, también debes seleccionar la escuela');
        return false;
      }
      
      return true;
    });
    
    // Formatear teléfono (solo números)
    document.getElementById('telefono').addEventListener('input', function(e) {
      this.value = this.value.replace(/\D/g, '');
    });
    
    // Convertir nombres a mayúsculas inicial
    function capitalize(input) {
      input.addEventListener('blur', function() {
        const words = this.value.toLowerCase().split(' ');
        const capitalized = words.map(word => {
          return word.charAt(0).toUpperCase() + word.slice(1);
        });
        this.value = capitalized.join(' ');
      });
    }
    
    capitalize(document.getElementById('nombre'));
    capitalize(document.getElementById('apellido_paterno'));
    capitalize(document.getElementById('apellido_materno'));
    capitalize(document.getElementById('municipio'));
    capitalize(document.getElementById('entidad'));

    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
    const UPLOAD_CONFIGS = [
      { id: 'Alumno1', label: 'Acta de Nacimiento' },
      { id: 'Alumno2', label: 'Cartilla de Vacunación' },
      { id: 'Tutor1', label: 'Identificación del Tutor' },
      { id: 'Tutor2', label: 'Comprobante de Domicilio' },
      { id: 'Tutor3', label: 'Autorización de Tutor' }
    ];

    let selectedFilesMap = {};

    function initializeUploadArea(configId) {
      const uploadArea = document.getElementById(`uploadArea${configId}`);
      const fileInput = document.getElementById(`fileInput${configId}`);
      const filesList = document.getElementById(`filesList${configId}`);
      const fileCounter = document.getElementById(`fileCounter${configId}`);

      selectedFilesMap[configId] = [];

      uploadArea.addEventListener('click', () => fileInput.click());

      uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
      });

      uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
      });

      uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(configId, e.dataTransfer.files, fileInput, filesList, fileCounter);
      });

      fileInput.addEventListener('change', (e) => {
        handleFiles(configId, e.target.files, fileInput, filesList, fileCounter);
      });
    }

    function handleFiles(configId, files, fileInput, filesList, fileCounter) {
      selectedFilesMap[configId] = [];
      filesList.innerHTML = '';

      Array.from(files).forEach(file => {
        if (validateFile(file)) {
          selectedFilesMap[configId].push(file);
          displayFile(configId, file, filesList);
        }
      });

      updateFileCounter(configId, fileCounter);
      updateInputFiles(configId, fileInput);
    }

    function validateFile(file) {
      if (file.size > MAX_FILE_SIZE) return false;
      const extension = '.' + file.name.split('.').pop().toLowerCase();
      return ALLOWED_EXTENSIONS.includes(extension);
    }

    function displayFile(configId, file, filesList) {
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      
      const fileExtension = file.name.split('.').pop().toUpperCase();
      const fileSize = (file.size / 1024).toFixed(2);
      
      let icon = 'fa-file';
      if (fileExtension === 'PDF') icon = 'fa-file-pdf';
      if (['JPG', 'JPEG', 'PNG'].includes(fileExtension)) icon = 'fa-file-image';
      
      fileItem.innerHTML = `
        <div class="file-info">
          <div class="file-icon"><i class="fas ${icon}"></i></div>
          <div class="file-details">
            <div class="file-name">${file.name}</div>
            <div class="file-size">${fileSize} KB</div>
          </div>
        </div>
        <button type="button" class="remove-btn" onclick="removeFile('${configId}')">
          <i class="fas fa-trash"></i>
        </button>
      `;
      
      filesList.appendChild(fileItem);
    }

    function removeFile(configId) {
      const fileInput = document.getElementById(`fileInput${configId}`);
      const filesList = document.getElementById(`filesList${configId}`);
      const fileCounter = document.getElementById(`fileCounter${configId}`);

      selectedFilesMap[configId] = [];
      filesList.innerHTML = '';
      fileInput.value = '';

      updateFileCounter(configId, fileCounter);
    }

    function updateFileCounter(configId, fileCounter) {
      const count = selectedFilesMap[configId].length;
      if (count === 0) {
        fileCounter.style.display = 'none';
      } else {
        fileCounter.style.display = 'block';
        const text = count === 1 ? 'archivo' : 'archivos';
        fileCounter.textContent = `${count} ${text} cargado${count > 1 ? 's' : ''}`;
      }
    }

    function updateInputFiles(configId, fileInput) {
      const dataTransfer = new DataTransfer();
      selectedFilesMap[configId].forEach(file => dataTransfer.items.add(file));
      fileInput.files = dataTransfer.files;
    }

    document.getElementById('formRegistro').addEventListener('submit', function(e) {
      e.preventDefault();
      this.submit();
    });

    UPLOAD_CONFIGS.forEach(config => initializeUploadArea(config.id));
