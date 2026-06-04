import csv
import random

# Definimos el tamaño del estrés
filas = 50000
columnas = 10

print(f"Generando archivo de {filas}x{columnas} filas/columnas...")

try:
    with open("archivo_pesado.csv", "w", newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Escribir encabezados
        writer.writerow([f"Col_{i}" for i in range(columnas)])
        
        # Escribir filas
        for i in range(filas):
            fila = [random.uniform(0, 100) if random.random() > 0.05 else "" for _ in range(columnas)]
            writer.writerow(fila)
            
            # Avisar progreso cada 10,000 filas
            if (i + 1) % 10000 == 0:
                print(f"Progreso: {i + 1} filas escritas...")

    print("✅ Archivo 'archivo_pesado.csv' generado correctamente en la carpeta de tu proyecto.")

except Exception as e:
    print(f"❌ Ocurrió un error: {e}")