import csv

archivo_csv = 'escuelas_reales.csv'

try:
    with open(archivo_csv, mode='r', encoding='utf-8-sig') as f:
        # Leer solo la primera línea (encabezados)
        reader = csv.reader(f)
        encabezados = next(reader) 
        
        print("\n🔍 NOMBRES DE COLUMNAS ENCONTRADOS:")
        print("===================================")
        for i, nombre in enumerate(encabezados):
            print(f"{i}: {nombre}")
        print("===================================\n")
        
        # Leer la primera fila de datos para ver ejemplos
        primera_fila = next(reader)
        print("EJEMPLO DE DATOS (Fila 1):")
        print(primera_fila)

except Exception as e:
    print(f"Error leyendo el archivo: {e}")
    print("Prueba cambiando el encoding a 'latin-1' si sale error de caracteres.")