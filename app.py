from flask import Flask
from dotenv import load_dotenv
import os

# 🔐 Cargar variables de entorno
load_dotenv()

# 🚀 Inicializar aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave_por_defecto_segura')

# 📦 Importar Blueprints
from routes.inicio import inicio_bp
from routes.iniciar_sesion import iniciar_sesion_bp
from routes.registro import registro_bp
from routes.registro_alumno import registro_alumno_bp
from routes.panel_tutor import panel_tutor_bp
from routes.panel_director import panel_director_bp
from routes.documentos import documentos_bp  # ✅ NUEVO
from routes.quienes_somos import quienes_somos_bp
from routes.ubicacion import ubicacion_bp
from routes.inscripcion import inscripcion_bp
from routes.panel_admin import panel_admin_bp

# 🔗 Registrar Blueprints
app.register_blueprint(inicio_bp)
app.register_blueprint(iniciar_sesion_bp)
app.register_blueprint(registro_bp)
app.register_blueprint(registro_alumno_bp)
app.register_blueprint(panel_tutor_bp)
app.register_blueprint(panel_director_bp)
app.register_blueprint(documentos_bp)  # ✅ NUEVO
app.register_blueprint(quienes_somos_bp)
app.register_blueprint(ubicacion_bp)
app.register_blueprint(inscripcion_bp)
app.register_blueprint(panel_admin_bp)

# 🏁 Ejecutar servidor
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))