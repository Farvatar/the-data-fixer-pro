import sqlite3
# Importamos la conexión que ya sabe cómo crear las tablas
import conexion_sql 

# Forzamos a que se asegure de crear las tablas primero
print("🛠️ Verificando y estructurando tablas de la base de datos...")
conexion_sql.inicializar_tablas()

# Ahora sí, nos conectamos de forma segura para meter el usuario
conn = sqlite3.connect("thedatafixer.db")
cursor = conn.cursor()

try:
    # Insertamos tu usuario de prueba con ID 1
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id_usuario, nombre, email, tipo_plan)
        VALUES (1, 'Fabian', 'fabian@ejemplo.com', 'Gratis');
    """)
    conn.commit()
    print("👤 ¡Éxito! Usuario de prueba verificado/creado con éxito (ID: 1).")
except Exception as e:
    print(f"❌ Error al insertar usuario: {e}")
finally:
    conn.close()