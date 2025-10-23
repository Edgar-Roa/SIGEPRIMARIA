from flask import Blueprint, render_template, request, redirect, flash, session
from models.usuario_model import registrar_usuario, correo_existe
from models.tutor_model import registrar_tutor
from werkzeug.security import generate_password_hash

registro_bp = Blueprint("registro", __name__)

@registro_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido_paterno = request.form.get("apellido_paterno", "").strip()
        apellido_materno = request.form.get("apellido_materno", "").strip()
        correo = request.form.get("correo", "").strip()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar_password", "")
        telefono = request.form.get("telefono", "").strip()
        edad = request.form.get("edad", "").strip()
        rol = "tutor"

        # Validaciones básicas
        if not all([nombre, apellido_paterno, apellido_materno, correo, password, confirmar, telefono, edad]):
            flash("Todos los campos son obligatorios", "error")
            return render_template("registro.html")

        if password != confirmar:
            flash("Las contraseñas no coinciden", "error")
            return render_template("registro.html")

        if correo_existe(correo):
            flash("Este correo ya está registrado", "error")
            return render_template("registro.html")

        try:
            password_hash = generate_password_hash(password)
            print(f"Registrando usuario con: {nombre} {apellido_paterno} {apellido_materno} {correo} {rol}")
            usuario_id = registrar_usuario(nombre, apellido_paterno, apellido_materno, correo, password_hash, rol)

            # ✅ CORRECCIÓN: Verificar None en lugar de falsy
            # Esto permite que usuario_id=0 sea válido
            if usuario_id is None:
                flash("Hubo un error al registrar el usuario", "error")
                return render_template("registro.html")

            print(f"Usuario registrado exitosamente con ID: {usuario_id}")
            print(f"Registrando tutor con: {usuario_id}, {nombre}, {apellido_paterno}, {apellido_materno}, {telefono}, {edad}")
            tutor_id = registrar_tutor(usuario_id, nombre, apellido_paterno, apellido_materno, telefono, edad)

            # ✅ CORRECCIÓN: Verificar None en lugar de falsy
            if tutor_id is None:
                flash("Hubo un error al registrar al tutor", "error")
                return render_template("registro.html")

            print(f"Tutor registrado exitosamente con ID: {tutor_id}")
            
            session["usuario_id"] = usuario_id
            session["rol"] = rol
            flash("Registro exitoso", "success")
            return redirect("/panel-tutor")

        except Exception as e:
            import traceback
            print(f"Error en el registro: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            flash("Ocurrió un error inesperado", "error")
            return render_template("registro.html")

    return render_template("registro.html")