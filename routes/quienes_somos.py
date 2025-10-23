from flask import Blueprint, render_template

quienes_somos_bp = Blueprint("quienes_somos", __name__)

@quienes_somos_bp.route("/Quienes_Somos")
def quienes_somos():
    return render_template("quienes_somos.html")