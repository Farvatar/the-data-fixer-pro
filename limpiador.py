import pandas as pd
# Importamos la función que creamos para registrar en la base de datos
import conexion_sql 

print("⏳ Leyendo el archivo 'datos_sucios.csv'...")
df = pd.read_csv("datos_sucios.csv", sep=";", header=None)

print("🔄 Transponiendo los datos de horizontal a vertical...")
df_vertical = df.transpose()

# Renombrar la columna con el título original
df_vertical.columns = [df_vertical.iloc[0, 0]]  
df_vertical = df_vertical.drop(df_vertical.index[0])  

# Limpiar los números (cambiar comas por puntos y volverlos numéricos)
nombre_columna = df_vertical.columns[0]
df_vertical[nombre_columna] = df_vertical[nombre_columna].astype(str).str.replace(',', '.')
df_vertical[nombre_columna] = pd.to_numeric(df_vertical[nombre_columna])

# Guardar el nuevo archivo limpio en la carpeta
archivo_salida = "datos_limpios.csv"
df_vertical.to_csv(archivo_salida, index=False)
print(f"✅ ¡Éxito! Archivo guardado como '{archivo_salida}' listo para graficar.")

# --- AQUÍ CONECTAMOS CON LA BASE DE DATOS ---
# Contamos cuántas filas y columnas procesamos para guardarlo como métrica
total_filas = len(df_vertical)
total_columnas = len(df_vertical.columns)

print("\n🗄️ Conectando con la base de datos para registrar la operación...")
# Llamamos a la base de datos y le pasamos los datos: (id_usuario, nombre_archivo, filas, columnas)
conexion_sql.registrar_archivo(1, archivo_salida, total_filas, total_columnas)

print("\nAsí quedaron tus datos estructurados:")
print(df_vertical)