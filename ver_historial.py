import sqlite3

# Nos conectamos al archivo de la base de datos
conn = sqlite3.connect("thedatafixer.db")
cursor = conn.cursor()

print("🔍 Consultando el historial de uso en la base de datos...\n")

# Hacemos un SELECT con un JOIN para unir el nombre del usuario con sus archivos
query = """
    SELECT u.nombre, h.nombre_archivo, h.filas_procesadas, h.columnas_procesadas, h.fecha_procesado
    FROM usuarios u
    JOIN historial_archivos h ON u.id_usuario = h.id_usuario
    WHERE u.id_usuario = 1;
"""

cursor.execute(query)
resultados = cursor.fetchall()

# Mostramos los resultados estéticos en pantalla
if resultados:
    print(f"📋 HISTORIAL DE ARCHIVOS PARA EL USUARIO: {resultados[0][0].upper()}")
    print("-" * 75)
    print(f"{'Archivo Procesado':<25} | {'Filas':<6} | {'Columnas':<8} | {'Fecha y Hora (UTC)'}")
    print("-" * 75)
    for fila in resultados:
        print(f"{fila[1]:<25} | {fila[2]:<6} | {fila[3]:<8} | {fila[4]}")
    print("-" * 75)
else:
    print("❌ No se encontraron archivos procesados para este usuario.")

conn.close()