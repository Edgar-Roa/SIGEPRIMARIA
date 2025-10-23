from flask import Blueprint, render_template

ubicacion_bp = Blueprint("ubicacion", __name__)

@ubicacion_bp.route("/ubicacion_de_las_escuelas")
def ubicacion():
    return render_template("ubicacion.html")