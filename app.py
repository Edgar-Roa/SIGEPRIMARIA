from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os


load_dotenv()


application = Flask(__name__)
application.secret_key = os.getenv('SECRET_KEY', 'clave_por_defecto_segura')

@application.after_request
def add_header(response):
    """
    Agrega cabeceras para que el navegador NO guarde las páginas en caché.
    Esto evita que al dar 'Atrás' después de logout se vea la página anterior.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


CORS(application)


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


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))