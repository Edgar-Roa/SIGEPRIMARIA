from flask import Flask
from flask_cors import CORS  # <--- IMPORTANTE: Importamos la librería
from dotenv import load_dotenv
import os

# 1. Cargar variables de entorno (Para leer DB_HOST, PASSWORD, etc.)
load_dotenv()

# 2. Inicializar la aplicación
application = Flask(__name__)
application.secret_key = os.getenv('SECRET_KEY', 'clave_por_defecto_segura')

# 3. Activar CORS (Permite conexiones externas de forma segura)
CORS(application)

# 4. Importar Blueprints (Tus rutas)
from routes.inicio import inicio_bp
from routes.iniciar_sesion import iniciar_sesion_bp
from routes.registro import registro_bp
from routes.registro_alumno import registro_alumno_bp
from routes.panel_tutor import panel_tutor_bp
from routes.panel_director import panel_director_bp
from routes.documentos import documentos_bp
from routes.quienes_somos import quienes_somos_bp
from routes.ubicacion import ubicacion_bp
from routes.inscripcion import inscripcion_bp
from routes.panel_admin import panel_admin_bp

# 5. Registrar Blueprints
application.register_blueprint(inicio_bp)
application.register_blueprint(iniciar_sesion_bp)
application.register_blueprint(registro_bp)
application.register_blueprint(registro_alumno_bp)
application.register_blueprint(panel_tutor_bp)
application.register_blueprint(panel_director_bp)
application.register_blueprint(documentos_bp)
application.register_blueprint(quienes_somos_bp)
application.register_blueprint(ubicacion_bp)
application.register_blueprint(inscripcion_bp)
application.register_blueprint(panel_admin_bp)

# 6. Bloque de Ejecución
if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))