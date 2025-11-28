import csv
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def importar_escuelas():
    print("🚀 Iniciando importación (Modo: Solo Nuevas o Actualizar)...")
    
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cursor = conn.cursor()
        print("✅ Conexión exitosa.")

        archivo_csv = 'escuelas_reales.csv'
        
        if not os.path.exists(archivo_csv):
            print(f"❌ Error: No se encontró '{archivo_csv}'.")
            return

        with open(archivo_csv, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Contadores
            procesadas = 0
            nuevas = 0
            actualizadas = 0
            
            for row in reader:
                try:
                    # --- 1. FILTROS (Solo Primarias de CDMX) ---
                    servicio = row.get('tiponivelsub_c_servicion1', '').strip().upper()
                    nombre = row.get('c_nombre', '').strip().upper()
                    entidad = row.get('inmueble_c_nom_ent', '').strip().upper()
                    if not entidad: entidad = row.get('c_administrativa', '').strip().upper()

                    # Filtro Nivel
                    if "PRIMARIA" not in servicio and "PRIMARIA" not in nombre:
                        continue

                    # Filtro Entidad
                    if "CIUDAD DE MÉXICO" not in entidad and \
                       "CDMX" not in entidad and \
                       "DISTRITO FEDERAL" not in entidad:
                        continue 

                    # --- 2. DATOS ---
                    cct = row.get('cv_cct', '').strip().upper()
                    nombre_escuela = row.get('c_nombre', '').strip()
                    municipio = row.get('inmueble_c_nom_mun', '').strip() # Alcaldía
                    
                    # Dirección
                    calle = row.get('inmueble_c_vialidad_principal', '')
                    num = row.get('inmueble_n_extnum', '')
                    colonia = row.get('inmueble_c_nom_asen', '')
                    direccion = f"{calle} {num}, {colonia}".strip()

                    # Coordenadas
                    try:
                        lat = float(row.get('latitud', 0))
                        lon = float(row.get('longitud', 0))
                    except:
                        lat, lon = 0, 0
                    
                    if lat == 0 or lon == 0 or not cct: continue

                    # Turno
                    turno_raw = row.get('c_turno_1', '').upper()
                    turno = 'matutino'
                    if 'VESPERTINO' in turno_raw: turno = 'vespertino'
                    elif 'MIXTO' in turno_raw or 'DISCONTINUO' in turno_raw: turno = 'mixto'

                    # --- 3. EL TRUCO ANTI-DUPLICADOS (ON CONFLICT) ---
                    # Esto intenta insertar. Si el CCT ya existe, solo actualiza la info.
                    cursor.execute("""
                        INSERT INTO escuelas (
                            cct, nombre, direccion, municipio, entidad, 
                            turno, latitud, longitud, cupo_total, activo
                        ) VALUES (
                            %s, %s, %s, %s, 'Ciudad de México', 
                            %s::school_shift, %s, %s, 300, TRUE
                        )
                        ON CONFLICT (cct) 
                        DO UPDATE SET 
                            nombre = EXCLUDED.nombre,
                            direccion = EXCLUDED.direccion,
                            latitud = EXCLUDED.latitud, 
                            longitud = EXCLUDED.longitud,
                            municipio = EXCLUDED.municipio;
                    """, (cct, nombre_escuela, direccion, municipio, turno, lat, lon))
                    
                    procesadas += 1
                    if procesadas % 500 == 0:
                        print(f"   -> Procesando... ({procesadas} escuelas revisadas)")

                except Exception:
                    pass

            conn.commit()
            print("\n" + "="*50)
            print(f"✅ FINALIZADO CORRECTAMENTE")
            print(f"🏫 Total de escuelas procesadas en BD: {procesadas}")
            print("   (Las que ya existían se actualizaron, las nuevas se crearon)")
            print("   (Tus escuelas ficticias están a salvo)")
            print("="*50)

    except Exception as e:
        print(f"🔥 Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    importar_escuelas()