from datetime import datetime, timedelta
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "thedatafixer.db")

def conectar_db():
    try:
        # Creamos la conexión usando la ruta absoluta definida arriba
        conn = sqlite3.connect(DB_NAME)
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def inicializar_tablas():
    """Crea las tablas necesarias si es la primera vez que se corre la app"""
    conn = conectar_db()
    if conn is None: return
    
    cursor = conn.cursor()
    
    # Activamos el soporte para llaves foráneas en SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        tipo_plan TEXT DEFAULT 'Gratis',
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Tabla de Historial
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial_archivos (
        id_archivo INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        nombre_archivo TEXT NOT NULL,
        filas_procesadas INTEGER DEFAULT 0,
        columnas_procesadas INTEGER DEFAULT 0,
        fecha_procesado DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

def registrar_archivo(id_usuario, nombre_archivo, filas, columnas):
    id_usuario = int(id_usuario)
    conn = conectar_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        # Aseguramos que id_usuario sea un entero. Si falla, el valor por defecto es 0.
        id_seguro = int(id_usuario) if id_usuario is not None else 0
        
        # INSERT directo
        cursor.execute("""
            INSERT INTO historial_archivos (id_usuario, nombre_archivo, filas, columnas, fecha_procesado)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
        """, (id_seguro, nombre_archivo, filas, columnas))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"DEBUG: Error en insert: {e}")
        return False
    finally:
        conn.close()

def obtener_historial_usuario(id_usuario):
    conn = conectar_db()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Asegúrate de que estos nombres de columna sean los mismos que usas en el INSERT
        cursor.execute("""
            SELECT nombre_archivo, filas, columnas, fecha_procesado 
            FROM historial_archivos 
            WHERE id_usuario = ? 
            ORDER BY fecha_procesado DESC LIMIT 10
        """, (id_usuario,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []
    finally:
        conn.close()
        
def registrar_nuevo_usuario(nombre, email, tipo_plan='Gratis'):
    """Registra un nuevo usuario en la base de datos si el email no existe."""
    conn = conectar_db()
    if conn is None:
        return False, "Error de conexión a la base de datos."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone():
            return False, "El correo electrónico ya está registrado."
            
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, tipo_plan)
            VALUES (?, ?, ?)
        """, (nombre, email, tipo_plan))
        conn.commit()
        return True, "¡Usuario registrado con éxito!"
    except Exception as e:
        print(f"Error al registrar usuario: {e}")
        return False, f"Error en el sistema: {e}"
    finally:
        conn.close()

def verificar_login_usuario(email):
    """Verifica si un usuario existe por su email y retorna sus datos."""
    conn = conectar_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, nombre, email, tipo_plan 
            FROM usuarios 
            WHERE email = ?
        """, (email,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error al verificar login: {e}")
        return None
    finally:
        conn.close()
def obtener_conteo_archivos(id_usuario):
    """Devuelve la cantidad de archivos procesados por un usuario."""
    conn = conectar_db()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM historial_archivos WHERE id_usuario = ?", (id_usuario,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    except Exception as e:
        print(f"Error al contar archivos: {e}")
        return 0
    finally:
        conn.close()
# Inicializamos las tablas automáticamente al importar este módulo
inicializar_tablas()

def diagnostico_db():
    conn = conectar_db()
    cursor = conn.cursor()
    # Verifica si la tabla existe y qué columnas tiene
    cursor.execute("PRAGMA table_info(historial_archivos)")
    columnas = cursor.fetchall()
    # Cuenta cuántos registros totales hay sin filtrar por ID
    cursor.execute("SELECT COUNT(*) FROM historial_archivos")
    total = cursor.fetchone()[0]
    conn.close()
    return columnas, total