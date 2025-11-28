from flask import Blueprint, render_template
from models.escuela_model import obtener_todas_escuelas_mapa
from decimal import Decimal
import re

ubicacion_bp = Blueprint("ubicacion", __name__)

def _convert_decimals(obj):
    if isinstance(obj, list):
        return [_convert_decimals(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

@ubicacion_bp.route("/ubicacion_de_las_escuelas")
def ubicacion():
    escuelas_data = obtener_todas_escuelas_mapa() or []
    print(f"🔍 DEBUG MODELO: Se encontraron {len(escuelas_data)} escuelas en la BD.")
    
    # DEBUG: mostrar primer registro
    if escuelas_data:
        print(f"📋 Primer registro (RAW): {escuelas_data[0]}")

    try:
        escuelas_clean = _convert_decimals(escuelas_data)
    except Exception as e:
        print("❌ Error convert decimals:", e)
        escuelas_clean = []

    print(f"📦 DEBUG RUTA: Enviando {len(escuelas_clean)} escuelas al HTML.")

    return render_template("ubicacion.html", escuelas_json=escuelas_clean)