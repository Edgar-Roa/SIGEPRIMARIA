document.addEventListener('DOMContentLoaded', () => {
  
  // 1. VALIDACIONES DE FORMULARIO (CURP, Fechas, etc.)
  const curpInput = document.getElementById('curp');
  const curpError = document.getElementById('curp-error');
  const curpSuccess = document.getElementById('curp-success');
  const fechaNacInput = document.getElementById('fecha_nacimiento');
  const edadInfo = document.getElementById('edad-info');
  const formRegistro = document.getElementById('formRegistro');
  const telefonoInput = document.getElementById('telefono');

  if (!formRegistro) return;

  // --- Validación CURP ---
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
        if (typeof VALIDAR_CURP_URL !== 'undefined') {
            fetch(VALIDAR_CURP_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ curp: curp })
            })
            .then(r => r.json())
            .then(data => {
                if (data.valido) {
                    curpInput.classList.add('success');
                    if (curpSuccess) curpSuccess.style.display = 'inline';
                } else {
                    curpInput.classList.add('error');
                    if (curpError) {
                        curpError.textContent = data.mensaje;
                        curpError.style.display = 'inline';
                    }
                }
            });
        }
      }, 500);
    });
  }

  // --- Calcular Edad ---
  if (fechaNacInput && edadInfo) {
    fechaNacInput.addEventListener('change', function () {
      if (!this.value) return;
      const hoy = new Date();
      const nacimiento = new Date(this.value);
      let edad = hoy.getFullYear() - nacimiento.getFullYear();
      const m = hoy.getMonth() - nacimiento.getMonth();
      if (m < 0 || (m === 0 && hoy.getDate() < nacimiento.getDate())) edad--;
      
      edadInfo.textContent = `Edad: ${edad} años`;
      edadInfo.style.color = (edad >= 5 && edad <= 15) ? '#28a745' : '#dc3545';
    });
  }

  // --- Capitalizar Nombres ---
  ['nombre', 'apellido_paterno', 'apellido_materno', 'municipio', 'entidad'].forEach(id => {
    const el = document.getElementById(id);
    if(el) {
        el.addEventListener('blur', function() {
            this.value = this.value.toLowerCase().replace(/(?:^|\s)\S/g, a => a.toUpperCase());
        });
    }
  });

  // 2. LÓGICA DE CARGA DE DOCUMENTOS (Drag & Drop)
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
  
  // IDs que coinciden con tu HTML: uploadAreaActa, uploadAreaCurp...
  const UPLOAD_CONFIGS = [
    'Acta', 
    'Curp', 
    'Cartilla', 
    'Foto', 
    'Certificado', 
    'Constancia', 
    'Ine', 
    'Comprobante'
  ];

  const selectedFilesMap = {};

  function initializeUploadArea(suffix) {
    const uploadArea = document.getElementById(`uploadArea${suffix}`);
    const fileInput = document.getElementById(`fileInput${suffix}`);
    const filesList = document.getElementById(`filesList${suffix}`);

    if (!uploadArea || !fileInput) return;

    // Click
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag & Drop
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
    uploadArea.addEventListener('dragleave', () => { uploadArea.classList.remove('dragover'); });
    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      handleFiles(suffix, e.dataTransfer.files, fileInput, filesList);
    });

    // Input Change
    fileInput.addEventListener('change', (e) => {
      handleFiles(suffix, e.target.files, fileInput, filesList);
    });
  }

  function handleFiles(suffix, files, fileInput, filesList) {
    if (files.length === 0) return;
    
    const file = files[0]; // Solo tomamos el primer archivo
    
    // Validar
    if (!validateFile(file)) {
        Swal.fire({
            toast: true, position: 'bottom-end', icon: 'warning', 
            title: 'Archivo inválido (Solo PDF/IMG < 10MB)'
        });
        fileInput.value = ''; // Limpiar
        return;
    }

    // Mostrar en lista
    filesList.innerHTML = ''; // Limpiar anteriores
    displayFile(suffix, file, filesList);

    // Asignar al input (si viene de drag & drop es necesario hacer esto manual)
    if (fileInput.files !== files) {
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
    }
  }

  function validateFile(file) {
    if (file.size > MAX_FILE_SIZE) return false;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    return ALLOWED_EXTENSIONS.includes(ext);
  }

  function displayFile(suffix, file, container) {
    const div = document.createElement('div');
    div.className = 'file-item'; // Asegúrate de tener CSS para esto
    div.style.display = 'flex';
    div.style.alignItems = 'center';
    div.style.justifyContent = 'space-between';
    div.style.padding = '10px';
    div.style.background = '#f8f9fa';
    div.style.marginTop = '10px';
    div.style.borderRadius = '5px';
    div.style.border = '1px solid #ddd';

    div.innerHTML = `
      <div style="display:flex; align-items:center; gap:10px; overflow:hidden;">
        <i class="fas fa-check-circle" style="color:#28a745;"></i>
        <span style="font-size:0.9rem; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${file.name}</span>
      </div>
      <button type="button" style="background:none; border:none; color:#dc3545; cursor:pointer;">
        <i class="fas fa-trash"></i>
      </button>
    `;

    // Botón eliminar
    div.querySelector('button').addEventListener('click', (e) => {
        e.stopPropagation();
        document.getElementById(`fileInput${suffix}`).value = '';
        container.innerHTML = '';
    });

    container.appendChild(div);
  }

  // Iniciar todos los listeners
  UPLOAD_CONFIGS.forEach(suffix => initializeUploadArea(suffix));

});