from conexion_sql import obtener_historial_usuario, registrar_archivo, registrar_nuevo_usuario, verificar_login_usuario
import streamlit as st
import pandas as pd
import conexion_sql
import csv
import sqlite3
import io

# Inicializar variables globales de sesión si no existen al arrancar la app
if "conectado" not in st.session_state:
    st.session_state["conectado"] = False
    st.session_state["usuario_id"] = None
    st.session_state["usuario_nombre"] = "Usuario Pro"
    st.session_state["usuario_plan"] = "Premium"

# Configuración avanzada de la página
st.set_page_config(
    page_title="The Data Fixer Pro", 
    page_icon="⚡", 
    layout="centered"
)

# ELIMINAMOS el CSS viejo que dañaba el modo oscuro. 
# Ahora dejamos que Streamlit adapte los textos automáticamente a tu pantalla.

# Encabezado Principal con Diseño
st.title("⚡ The Data Fixer Pro")
st.caption("La plataforma inteligente para estructurar, limpiar y analizar tus bases de datos horizontales en segundos.")

ID_USUARIO_ACTUAL = 1
LIMITE_GRATUITO = 100

# ==================== CONEXIÓN DE BASE DE DATOS Y MÉTRICAS ====================
# 1. Aseguramos que existan las variables de sesión al arrancar la app
if "conectado" not in st.session_state:
    st.session_state["conectado"] = False
    st.session_state["usuario_id"] = None
    st.session_state["usuario_nombre"] = "Usuario Pro"
    st.session_state["usuario_plan"] = "Premium"

# Variables para controlar los límites
LIMITE_GRATUITO = 10
archivos_procesados = 0

# 2. Control dinámico de la sesión
if st.session_state["conectado"] and st.session_state["usuario_id"] is not None:
    # Si el usuario inició sesión, traemos sus datos en tiempo real
    try:
        import sqlite3
        conn = sqlite3.connect("thedatafixer.db")
        cursor = conn.cursor()
        
        # Consultamos datos del perfil
        cursor.execute("SELECT nombre, tipo_plan FROM usuarios WHERE id_usuario = ?", (st.session_state["usuario_id"],))
        usuario_info = cursor.fetchone()
        
        # Consultamos cuántos archivos lleva procesados este usuario real
        cursor.execute("SELECT COUNT(*) FROM historial_archivos WHERE id_usuario = ?", (st.session_state["usuario_id"],))
        archivos_procesados = cursor.fetchone()[0]
        
        conn.close()
        
        if usuario_info:
            nombre_usuario = usuario_info[0]
            plan_usuario = usuario_info[1]
        else:
            nombre_usuario = st.session_state["usuario_nombre"]
            plan_usuario = st.session_state["usuario_plan"]
            
    except Exception as e:
        nombre_usuario = st.session_state["usuario_nombre"]
        plan_usuario = st.session_state["usuario_plan"]
else:
    # Si NO hay nadie conectado (o cerró sesión), valores limpios por defecto
    nombre_usuario = st.session_state["usuario_nombre"]
    plan_usuario = st.session_state["usuario_plan"]
    archivos_procesados = 0

# 3. Renderizado estético de métricas de usuario (Tus 3 columnas originales)
col_user, col_plan, col_usage = st.columns(3)

with col_user:
    st.metric(label="👤 Cuenta", value=nombre_usuario)

with col_plan:
    st.metric(label="💎 Nivel de Plan", value=plan_usuario)

with col_usage:
    # Si es plan Gratis muestra el contador X/10, si es Premium muestra Ilimitado
    valor_uso = f"{archivos_procesados} / {LIMITE_GRATUITO}" if plan_usuario == "Gratis" else "✨ Ilimitado"
    st.metric(label="📊 Uso Mensual", value=valor_uso)

st.markdown("---")

# --- SISTEMA DE PESTAÑAS ---
tab_limpieza, tab_historial, tab_config = st.tabs(["🚀 Motor de Limpieza", "🗄️ Historial de Uso", "🛠️ Ajustes del Sistema"])

# ==================== PESTAÑA 1: MOTOR DE LIMPIEZA ====================
with tab_limpieza:
    bloqueado = False
    if plan_usuario == "Gratis" and archivos_procesados >= LIMITE_GRATUITO:
        bloqueado = True
        st.error(f"🚨 **Acceso Restringido:** Has alcanzado el límite de tu plan gratuito ({archivos_procesados}/{LIMITE_GRATUITO} archivos).")
        
        with st.container():
            st.markdown("""
            <div style="background-color:#fff3cd; padding:20px; border-radius:10px; border-left: 5px solid #ffc107; color: #856404;">
                <h4>🔓 Desbloquea el poder ilimitado</h4>
                <p>Por solo <b>$9 USD/mes</b> obtén procesamiento sin restricciones, exportación directa a Excel y soporte prioritario.</p>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("🚀 Convertirme en Miembro Premium"):
                conn = sqlite3.connect("thedatafixer.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE usuarios SET tipo_plan = 'Premium' WHERE id_usuario = ?;", (st.session_state["usuario_id"],))
                conn.commit()
                conn.close()
                st.success("🎉 ¡Excelente elección! Tu cuenta ha sido promovida a Premium. Refresca la página para comenzar.")
                st.balloons()

    st.header("1. Carga tu matriz de datos")
    archivo_cargado = st.file_uploader("Arrastra aquí tu archivo .csv listo para transformar", type=["csv"], disabled=bloqueado)

    if archivo_cargado is not None and not bloqueado:
        try:
            contenido_crudo = archivo_cargado.read()
            texto_muestra = contenido_crudo.decode("utf-8")
            try:
                sniffer = csv.Sniffer()
                dialecto = sniffer.sniff(texto_muestra[:2048])
                separador_detectado = dialecto.delimiter
                st.success(f"🤖 **Asistente IA:** Detecté que tus datos usan el separador `'{separador_detectado}'`.")
            except Exception:
                separador_detectado = ";"
                st.info("ℹ️ Separador estándar configurado (';').")
                
            archivo_cargado.seek(0)
            df_original = pd.read_csv(archivo_cargado, sep=separador_detectado, header=None)
            
            with st.expander("👀 Ver estructura del archivo original cargado"):
                st.dataframe(df_original, use_container_width=True)
            
            st.write("### ⚙️ Preferencias de Optimización")
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1: eliminar_dup = st.checkbox("Eliminar registros duplicados", value=True)
            with col_opt2: reparar_nulos = st.checkbox("Autocompletar celdas vacías", value=True)
            
            if st.button("✨ Procesar y Optimizar Base de Datos"):
                with st.spinner("Ejecutando algoritmos de transformación..."):
                    # 1. Transposición básica
                    df_vertical = df_original.transpose()
                    
                    # Guardamos el título original de la primera celda
                    titulo_sucio = str(df_vertical.iloc[0, 0])
                    
                    # CORRECCIÓN: Si el título viene con punto y coma ';', lo limpiamos
                    if ";" in titulo_sucio:
                        titulo_limpio = titulo_sucio.split(";")[0]
                    else:
                        titulo_limpio = titulo_sucio
                        
                    # Asignamos el nombre limpio a la columna
                    df_vertical.columns = [titulo_limpio]  
                    df_vertical = df_vertical.drop(df_vertical.index[0])  
                    
                    nombre_columna = df_vertical.columns[0]
                    columna_texto = df_vertical[nombre_columna].astype(str)
                    
                    # 2. Corrección regional de decimales
                    conteo_comas = columna_texto.str.contains(',').sum()
                    conteo_puntos = columna_texto.str.contains(r'\.').sum()
                    if conteo_comas > conteo_puntos:
                        df_vertical[nombre_columna] = columna_texto.str.replace(',', '.')
                    else:
                        df_vertical[nombre_columna] = columna_texto
                    
                    df_vertical[nombre_columna] = pd.to_numeric(df_vertical[nombre_columna], errors='coerce')
                    
                    # --- AQUÍ ESTÁ LA CORRECCIÓN: Definimos las variables de control ---
                    filas_iniciales = len(df_vertical)
                    duplicados_eliminados = 0
                    nulos_reparados = 0
                    
                    # 3. FILTRADO: Duplicados
                    if eliminar_dup:
                        df_vertical = df_vertical.drop_duplicates()
                        duplicados_eliminados = filas_iniciales - len(df_vertical)
                        
                    # 4. FILTRADO: Valores Nulos
                    if reparar_nulos:
                        nulos_reparados = df_vertical[nombre_columna].isna().sum()
                        if nulos_reparados > 0:
                            df_vertical[nombre_columna] = df_vertical[nombre_columna].interpolate(method='linear')
                    
                    # Limpieza final de filas vacías persistentes
                    df_vertical = df_vertical.dropna()
                    
                    # Registrar log en base de datos
                    nombre_salida = f"optimizando_{archivo_cargado.name}"
                    conexion_sql.registrar_archivo(ID_USUARIO_ACTUAL, nombre_salida, len(df_vertical), len(df_vertical.columns))
                
                st.balloons()
                st.subheader("🎉 ¡Optimización Finalizada con Éxito!")
                
                # Render de KPIs
                kpi1, kpi2, kpi3 = st.columns(3)
                with kpi1: st.metric("Filas Finales", len(df_vertical))
                with kpi2: st.metric("Duplicados Borrados", int(duplicados_eliminados))
                with kpi3: st.metric("Celdas Reparadas", int(nulos_reparados))
                
                st.write("### 📊 Gráfico Analítico de la Tendencia")
                st.line_chart(df_vertical)
                
                st.write("### 📥 Panel de Descarga del Producto")
                col_down1, col_down2 = st.columns(2)
                
                with col_down1:
                    csv_datos = df_vertical.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📄 Descargar en Formato .CSV",
                        data=csv_datos,
                        file_name=f"clean_{archivo_cargado.name}",
                        mime="text/csv"
                    )
                
                with col_down2:
                    buffer_excel = io.BytesIO()
                    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                        df_vertical.to_excel(writer, index=False, sheet_name="Datos_Limpios")
                    
                    st.download_button(
                        label="🟢 Descargar en Formato .EXCEL",
                        data=buffer_excel.getvalue(),
                        file_name=f"clean_{archivo_cargado.name.replace('.csv', '.xlsx')}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error(f"Ocurrió un inconveniente estructural en los datos: {e}")

# ==================== PESTAÑA 2: HISTORIAL DE USO ====================
with tab_historial:
    st.header("🔄 Historial y Auditoría de Procesos")
    
    # 1. ID temporal de usuario (mientras no implementemos el login real)
    ID_USUARIO_ACTUAL = 1 
    
    # 2. El botón que ya tenías programado
    if st.button("🔄 Sincronizar y Actualizar Historial"):
        
        # Llamamos directamente a la función de tu archivo conexion_sql.py
        rows = obtener_historial_usuario(ID_USUARIO_ACTUAL)
        
        if rows:
            import pandas as pd
            
            # Convertimos a DataFrame para mostrarlo en la interfaz
            df_historial = pd.DataFrame(
                rows, 
                columns=["Archivo Destino", "Líneas Procesadas", "Columnas Procesadas", "Fecha de Proceso"]
            )
            st.dataframe(df_historial, use_container_width=True)
            
            # 📊 BONUS: Un gráfico de barras interactivo para que explote visualmente
            st.subheader("📈 Volumen de datos corregidos")
            st.bar_chart(data=df_historial, x="Archivo Destino", y="Líneas Procesadas")
        else:
            st.info("No se registran transacciones previas en este perfil.")

# ==================== PESTAÑA 3: CONFIGURACIÓN ====================
with tab_config:
    st.header("🔧 Panel de Control Técnico")
    
    if not st.session_state["conectado"]:
        st.subheader("🔑 Acceso al Sistema")
        
        # Pestañas internas para Login y Registro
        tab_login, tab_registro = st.tabs(["Ingresar", "Crear Cuenta"])
        
        with tab_login:
            email_login = st.text_input("Correo Electrónico", key="login_email")
            if st.button("Iniciar Sesión", use_container_width=True):
                if email_login:
                    usuario = verificar_login_usuario(email_login)
                    if usuario:
                        st.session_state["conectado"] = True
                        st.session_state["usuario_id"] = usuario[0]
                        st.session_state["usuario_nombre"] = usuario[1]
                        st.session_state["usuario_plan"] = usuario[3]
                        st.success(f"¡Bienvenido, {usuario[1]}!")
                        st.rerun()  # Recarga la interfaz para actualizar las tarjetas de arriba
                    else:
                        st.error("El correo no está registrado. Crea una cuenta primero.")
                else:
                    st.warning("Por favor ingresa tu correo.")
                    
        with tab_registro:
            nuevo_nombre = st.text_input("Nombre Completo", key="reg_nombre")
            nuevo_email = st.text_input("Correo Electrónico", key="reg_email")
            plan_seleccionado = st.selectbox("Selecciona tu Plan", ["Gratis", "Premium", "Enterprise"])
            
            if st.button("Registrarme", use_container_width=True):
                if nuevo_nombre and nuevo_email:
                    exito, mensaje = registrar_nuevo_usuario(nuevo_nombre, nuevo_email, plan_seleccionado)
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
                else:
                    st.warning("Por favor completa todos los campos.")
                    
    else:
        # Perfil del usuario activo
        st.subheader("👤 Perfil de Ingeniero Activo")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nombre:** {st.session_state['usuario_nombre']}")
            st.write(f"**ID de Cuenta:** #{st.session_state['usuario_id']}")
        with col2:
            st.write(f"**Nivel de Plan:** {st.session_state['usuario_plan']}")
            
        st.write("---")
        
        # AQUÍ CONVIVE TU LÓGICA ORIGINAL DE PRUEBAS
        st.subheader("⚡ Herramientas de Desarrollo")
        if st.button("⚠️ Reiniciar Entorno de Pruebas", use_container_width=True):
            conn = sqlite3.connect("thedatafixer.db")
            cursor = conn.cursor()
            # Usamos el ID dinámico del usuario logueado para limpiar sus datos
            cursor.execute("UPDATE usuarios SET tipo_plan = 'Gratis' WHERE id_usuario = ?", (st.session_state["usuario_id"],))
            cursor.execute("DELETE FROM historial_archivos WHERE id_usuario = ?", (st.session_state["usuario_id"],))
            conn.commit()
            conn.close()
            st.success("🔄 Entorno reseteado con éxito.")
            st.rerun()
            
        if st.button("❌ Cerrar Sesión", use_container_width=True):
            st.session_state["conectado"] = False
            st.session_state["usuario_id"] = None
            st.session_state["usuario_nombre"] = "Usuario Pro"
            st.session_state["usuario_plan"] = "Premium"
            st.info("Sesion cerrada correctamente.")
            st.rerun()