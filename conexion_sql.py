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
    """Inserta un registro en el historial de archivos procesados"""
    conn = conectar_db()
    if conn is None: return False
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO historial_archivos (id_usuario, nombre_archivo, filas_procesadas, columnas_procesadas)
            VALUES (?, ?, ?, ?);
        """, (id_usuario, nombre_archivo, filas, columnas))
        conn.commit()
        print(f"💾 Registro guardado en SQLite: {nombre_archivo} ({filas}x{columnas})")
        return True
    except Exception as e:
        print(f"❌ Error al guardar en el historial: {e}")
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
# Inicializamos las tablas automáticamente al importar este módulo
inicializar_tablas()