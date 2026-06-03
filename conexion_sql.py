from datetime import datetime, timedelta
import sqlite3
import os

DB_NAME = "thedatafixer.db"

def conectar_db():
    """Establece conexión con la base de datos SQLite (la crea si no existe)"""
    try:
        conexion = sqlite3.connect(DB_NAME)
        return conexion
    except Exception as e:
        print(f"❌ Error al conectar a SQLite: {e}")
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
    conn = conectar_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        
        # 🕒 Ajuste de Zona Horaria (UTC a UTC-5 Colombia)
        # Tomamos la hora del servidor (UTC) y le restamos 5 horas fijas
        hora_colombia = datetime.utcnow() - timedelta(hours=5)
        fecha_actual = hora_colombia.strftime('%Y-%m-%d %H:%M:%S')
        
        # Tu execute original (asegúrate de que use 'fecha_actual')
        cursor.execute("""
            INSERT INTO historial_archivos (id_usuario, nombre_archivo, filas, columnas, fecha_procesado)
            VALUES (?, ?, ?, ?, ?)
        """, (id_usuario, nombre_archivo, filas, columnas, fecha_actual))
        
        conn.commit()
        print(f"💾 Registro guardado con hora local: {nombre_archivo} a las {fecha_actual}")
        return True
    except Exception as e:
        print(f"Error al registrar archivo: {e}")
        return False
    finally:
        conn.close()

def obtener_historial_usuario(id_usuario):
    """Recupera los últimos 10 archivos procesados por el usuario."""
    conn = conectar_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre_archivo, filas_procesadas, columnas_procesadas, fecha_procesado 
            FROM historial_archivos 
            WHERE id_usuario = ? 
            ORDER BY id_archivo DESC 
            LIMIT 10
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