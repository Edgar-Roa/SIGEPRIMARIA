// ...existing code...
document.addEventListener('DOMContentLoaded', () => {
  // Elementos principales (con guards)
  const curpInput = document.getElementById('curp');
  const curpError = document.getElementById('curp-error');
  const curpSuccess = document.getElementById('curp-success');
  const fechaNacInput = document.getElementById('fecha_nacimiento');
  const edadInfo = document.getElementById('edad-info');
  const formRegistro = document.getElementById('formRegistro');
  const telefonoInput = document.getElementById('telefono');

  if (!formRegistro) return;

  // ---------- CURP: validación en tiempo real ----------
  let timeoutId;
  if (curpInput) {
    curpInput.addEventListener('input', function () {
      const curp = this.value.toUpperCase();
      this.value = curp;

      if (curpError) curpError.style.display = 'none';
      if (curpSuccess) curpSuccess.style.display = 'none';
      this.classList.remove('error', 'success');

      if (curp.length !== 18) return;

      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        if (typeof VALIDAR_CURP_URL === 'undefined' || !VALIDAR_CURP_URL) {
          console.error('VALIDAR_CURP_URL no definido en la plantilla.');
          return;
        }
        fetch(VALIDAR_CURP_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ curp: curp })
        })
          .then(response => {
            if (!response.ok) throw new Error('Respuesta no OK del servidor');
            return response.json();
          })
          .then(data => {
            if (data && data.valido) {
              curpInput.classList.add('success');
              if (curpSuccess) curpSuccess.style.display = 'inline';
            } else {
              curpInput.classList.add('error');
              if (curpError) {
                curpError.textContent = (data && data.mensaje) ? data.mensaje : 'CURP inválido';
                curpError.style.display = 'inline';
              }
            }
          })
          .catch(err => {
            console.error('Error validando CURP:', err);
            if (curpError) {
              curpError.textContent = 'Error validando CURP (intenta de nuevo)';
              curpError.style.display = 'inline';
            }
          });
      }, 500);
    });
  }

  // ---------- Fecha de nacimiento -> edad ----------
  if (fechaNacInput && edadInfo) {
    fechaNacInput.addEventListener('change', function () {
      if (!this.value) {
        edadInfo.textContent = '';
        return;
      }
      const hoy = new Date();
      const nacimiento = new Date(this.value);
      let edad = hoy.getFullYear() - nacimiento.getFullYear();
      const m = hoy.getMonth() - nacimiento.getMonth();
      if (m < 0 || (m === 0 && hoy.getDate() < nacimiento.getDate())) edad--;
      edadInfo.textContent = `Edad: ${edad} años`;
      edadInfo.style.color = (edad >= 5 && edad <= 15) ? '#28a745' : '#dc3545';
      if (edad < 5 || edad > 15) {
        edadInfo.textContent += ' (Fuera del rango recomendado para primaria)';
      }
    });
  }

  // ---------- Validación al enviar el formulario ----------
  formRegistro.addEventListener('submit', function (e) {
    const curpVal = (curpInput && curpInput.value) ? curpInput.value.trim() : '';
    if (curpVal.length !== 18) {
      e.preventDefault();
      alert('El CURP debe tener exactamente 18 caracteres');
      return false;
    }

    const escuelaEl = document.getElementById('escuela_id');
    const gradoEl = document.getElementById('grado_id');
    const escuelaId = escuelaEl ? escuelaEl.value : '';
    const gradoId = gradoEl ? gradoEl.value : '';

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

  // ---------- Teléfono: solo números ----------
  if (telefonoInput) {
    telefonoInput.addEventListener('input', function () {
      this.value = this.value.replace(/\D/g, '');
    });
  }

  // ---------- Capitalizar nombres al perder foco ----------
  function capitalize(inputEl) {
    if (!inputEl) return;
    inputEl.addEventListener('blur', function () {
      const words = this.value.trim().toLowerCase().split(/\s+/);
      const capitalized = words.map(w => w ? (w.charAt(0).toUpperCase() + w.slice(1)) : '').join(' ');
      this.value = capitalized;
    });
  }

  ['nombre', 'apellido_paterno', 'apellido_materno', 'municipio', 'entidad'].forEach(id => {
    capitalize(document.getElementById(id));
  });

  // ---------- Upload areas ----------
  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
  const UPLOAD_CONFIGS = [
    { id: 'Alumno1', label: 'Acta de Nacimiento' },
    { id: 'Alumno2', label: 'Cartilla de Vacunación' },
    { id: 'Tutor1', label: 'Identificación del Tutor' },
    { id: 'Tutor2', label: 'Comprobante de Domicilio' },
    { id: 'Tutor3', label: 'Autorización de Tutor' }
  ];

  const selectedFilesMap = {};

  function initializeUploadArea(configId) {
    const uploadArea = document.getElementById(`uploadArea${configId}`);
    const fileInput = document.getElementById(`fileInput${configId}`);
    const filesList = document.getElementById(`filesList${configId}`);
    const fileCounter = document.getElementById(`fileCounter${configId}`);

    if (!uploadArea || !fileInput) return;

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
    if (filesList) filesList.innerHTML = '';

    Array.from(files).forEach(file => {
      if (validateFile(file)) {
        selectedFilesMap[configId].push(file);
        if (filesList) displayFile(configId, file, filesList);
      } else {
        console.warn('Archivo no permitido o demasiado grande:', file.name);
      }
    });

    updateFileCounter(configId, fileCounter);
    updateInputFiles(configId, fileInput);
  }

  function validateFile(file) {
    if (!file) return false;
    if (file.size > MAX_FILE_SIZE) return false;
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    return ALLOWED_EXTENSIONS.includes(extension);
  }

  function displayFile(configId, file, filesList) {
    if (!filesList) return;
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';

    const fileExtension = file.name.split('.').pop().toUpperCase();
    const fileSizeKb = (file.size / 1024).toFixed(2);

    let icon = 'fa-file';
    if (fileExtension === 'PDF') icon = 'fa-file-pdf';
    if (['JPG', 'JPEG', 'PNG'].includes(fileExtension)) icon = 'fa-file-image';

    const info = document.createElement('div');
    info.className = 'file-info';
    info.innerHTML = `
      <div class="file-icon"><i class="fas ${icon}"></i></div>
      <div class="file-details">
        <div class="file-name">${file.name}</div>
        <div class="file-size">${fileSizeKb} KB</div>
      </div>
    `;

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-btn';
    removeBtn.innerHTML = '<i class="fas fa-trash"></i>';

    removeBtn.addEventListener('click', () => {
      removeFile(configId);
    });

    const container = document.createElement('div');
    container.appendChild(info);
    container.appendChild(removeBtn);

    filesList.appendChild(container);
  }

  function removeFile(configId) {
    const fileInput = document.getElementById(`fileInput${configId}`);
    const filesList = document.getElementById(`filesList${configId}`);
    const fileCounter = document.getElementById(`fileCounter${configId}`);

    selectedFilesMap[configId] = [];
    if (filesList) filesList.innerHTML = '';
    if (fileInput) fileInput.value = '';

    updateFileCounter(configId, fileCounter);
  }

  function updateFileCounter(configId, fileCounter) {
    const count = selectedFilesMap[configId] ? selectedFilesMap[configId].length : 0;
    if (!fileCounter) return;
    if (count === 0) {
      fileCounter.style.display = 'none';
    } else {
      fileCounter.style.display = 'block';
      const texto = count === 1 ? 'archivo' : 'archivos';
      fileCounter.textContent = `${count} ${texto} cargado${count > 1 ? 's' : ''}`;
    }
  }

  function updateInputFiles(configId, fileInput) {
    if (!fileInput) return;
    const dt = new DataTransfer();
    (selectedFilesMap[configId] || []).forEach(f => dt.items.add(f));
    fileInput.files = dt.files;
  }

  // Inicializar todas las áreas disponibles
  UPLOAD_CONFIGS.forEach(cfg => initializeUploadArea(cfg.id));
});
// ...existing code...