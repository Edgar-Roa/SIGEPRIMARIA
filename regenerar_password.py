"""
Script para regenerar los hashes de contraseñas en la base de datos
Ejecutar: python regenerar_passwords.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

# ============================================
# CONFIGURACIÓN
# ============================================
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sigueprimaria',  # Cambia por tu base de datos
    'user': 'postgres',            # Cambia por tu usuario
    'password': '12345',     # Cambia por tu contraseña
    'port': '5432'
}

def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port'],
        cursor_factory=RealDictCursor
    )

def regenerar_todos_los_passwords():
    """Regenerar passwords de todos los usuarios"""
    print("\n" + "="*60)
    print("  REGENERAR CONTRASEÑAS - SIGUEPRIMARIA")
    print("="*60)
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener todos los usuarios
        cursor.execute("""
            SELECT usuario_id, nombre, apellido_paterno, correo, rol
            FROM usuarios
            ORDER BY 
                CASE rol
                    WHEN 'super_admin' THEN 1
                    WHEN 'sep_admin' THEN 2
                    WHEN 'director' THEN 3
                    WHEN 'docente' THEN 4
                    WHEN 'tutor' THEN 5
                END
        """)
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("\n❌ No hay usuarios en la base de datos")
            return
        
        print(f"\nSe encontraron {len(usuarios)} usuarios\n")
        print("="*60)
        
        for usuario in usuarios:
            print(f"\n👤 {usuario['nombre']} {usuario['apellido_paterno']}")
            print(f"   📧 {usuario['correo']}")
            print(f"   🏷️  Rol: {usuario['rol']}")
            
            nueva_password = input("   🔑 Nueva contraseña (Enter para omitir): ").strip()
            
            if nueva_password:
                if len(nueva_password) < 8:
                    print("   ⚠️  La contraseña debe tener al menos 8 caracteres, omitiendo...")
                    continue
                
                # Generar nuevo hash
                nuevo_hash = generate_password_hash(nueva_password, method='pbkdf2:sha256')
                
                # Actualizar en base de datos
                cursor.execute("""
                    UPDATE usuarios
                    SET password_hash = %s
                    WHERE usuario_id = %s
                """, (nuevo_hash, usuario['usuario_id']))
                
                print(f"   ✅ Contraseña actualizada: {nueva_password}")
            else:
                print("   ⏭️  Omitido")
        
        # Confirmar cambios
        print("\n" + "="*60)
        confirmar = input("\n¿Guardar todos los cambios? (S/N): ").strip().upper()
        
        if confirmar == 'S':
            conn.commit()
            print("\n✅ Contraseñas actualizadas exitosamente")
        else:
            conn.rollback()
            print("\n❌ Cambios descartados")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def establecer_passwords_demo():
    """Establecer contraseñas predefinidas para usuarios demo"""
    print("\n" + "="*60)
    print("  ESTABLECER CONTRASEÑAS DE DEMOSTRACIÓN")
    print("="*60)
    
    # Contraseñas por rol
    passwords_por_rol = {
        'super_admin': 'Admin2025!',
        'sep_admin': 'Admin2025!',
        'director': 'Director2025!',
        'docente': 'Docente2025!',
        'tutor': 'Tutor2025!'
    }
    
    print("\nEsto establecerá las siguientes contraseñas:")
    for rol, password in passwords_por_rol.items():
        print(f"  • {rol}: {password}")
    
    confirmar = input("\n¿Continuar? (S/N): ").strip().upper()
    
    if confirmar != 'S':
        print("\n❌ Operación cancelada")
        return
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Actualizar por rol
        for rol, password in passwords_por_rol.items():
            nuevo_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            cursor.execute("""
                UPDATE usuarios
                SET password_hash = %s
                WHERE rol = %s::user_role
            """, (nuevo_hash, rol))
            
            affected = cursor.rowcount
            print(f"✅ {affected} usuario(s) con rol '{rol}' actualizados")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ CONTRASEÑAS DE DEMOSTRACIÓN ESTABLECIDAS")
        print("="*60)
        print("\n📋 CREDENCIALES PARA PRUEBAS:")
        print("-" * 60)
        
        # Mostrar usuarios actualizados
        cursor.execute("""
            SELECT correo, rol
            FROM usuarios
            ORDER BY 
                CASE rol
                    WHEN 'super_admin' THEN 1
                    WHEN 'sep_admin' THEN 2
                    WHEN 'director' THEN 3
                    WHEN 'docente' THEN 4
                    WHEN 'tutor' THEN 5
                END
        """)
        usuarios = cursor.fetchall()
        
        for usuario in usuarios:
            password = passwords_por_rol.get(usuario['rol'], 'N/A')
            print(f"\n{usuario['rol'].upper()}:")
            print(f"  📧 {usuario['correo']}")
            print(f"  🔑 {password}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def resetear_usuario_especifico():
    """Resetear contraseña de un usuario específico"""
    print("\n" + "="*60)
    print("  RESETEAR CONTRASEÑA DE USUARIO ESPECÍFICO")
    print("="*60)
    
    correo = input("\n📧 Correo del usuario: ").strip().lower()
    nueva_password = input("🔑 Nueva contraseña (mín. 8 caracteres): ").strip()
    
    if len(nueva_password) < 8:
        print("\n❌ La contraseña debe tener al menos 8 caracteres")
        return
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("""
            SELECT usuario_id, nombre, apellido_paterno, rol
            FROM usuarios
            WHERE correo = %s
        """, (correo,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"\n❌ No se encontró un usuario con el correo: {correo}")
            return
        
        print(f"\n👤 Usuario encontrado:")
        print(f"   Nombre: {usuario['nombre']} {usuario['apellido_paterno']}")
        print(f"   Rol: {usuario['rol']}")
        
        confirmar = input("\n¿Actualizar contraseña? (S/N): ").strip().upper()
        
        if confirmar == 'S':
            # Generar nuevo hash
            nuevo_hash = generate_password_hash(nueva_password, method='pbkdf2:sha256')
            
            # Actualizar
            cursor.execute("""
                UPDATE usuarios
                SET password_hash = %s
                WHERE usuario_id = %s
            """, (nuevo_hash, usuario['usuario_id']))
            
            conn.commit()
            
            print("\n✅ Contraseña actualizada exitosamente")
            print(f"   📧 {correo}")
            print(f"   🔑 {nueva_password}")
        else:
            print("\n❌ Operación cancelada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def menu_principal():
    """Menú principal"""
    while True:
        print("\n" + "="*60)
        print("  🔐 REGENERAR CONTRASEÑAS - SIGUEPRIMARIA")
        print("="*60)
        print("\n1. Regenerar contraseñas de todos los usuarios (uno por uno)")
        print("2. Establecer contraseñas demo (rápido para pruebas)")
        print("3. Resetear contraseña de un usuario específico")
        print("4. Salir")
        
        opcion = input("\n👉 Selecciona una opción: ").strip()
        
        if opcion == '1':
            regenerar_todos_los_passwords()
            input("\nPresiona Enter para continuar...")
        elif opcion == '2':
            establecer_passwords_demo()
            input("\nPresiona Enter para continuar...")
        elif opcion == '3':
            resetear_usuario_especifico()
            input("\nPresiona Enter para continuar...")
        elif opcion == '4':
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("\n❌ Opción inválida")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    try:
        print("\n🔄 Verificando conexión a la base de datos...")
        conn = get_connection()
        conn.close()
        print("✅ Conexión exitosa\n")
        
        menu_principal()
        
    except Exception as e:
        print(f"\n❌ Error de conexión a la base de datos:")
        print(f"   {e}")
        print("\n💡 Verifica la configuración en DB_CONFIG")
        input("\nPresiona Enter para salir...")