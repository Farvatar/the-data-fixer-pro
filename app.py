from conexion_sql import obtener_historial_usuario, registrar_archivo, registrar_nuevo_usuario, verificar_login_usuario, obtener_conteo_archivos
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
    st.session_state["usuario_nombre"] = "Invitado"
    st.session_state["usuario_plan"] = "Gratis"

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
if "conectado" not in st.session_state:
    st.session_state["conectado"] = False
    st.session_state["usuario_id"] = None
    st.session_state["usuario_nombre"] = "Invitado"
    st.session_state["usuario_plan"] = "Gratis"

LIMITE_GRATUITO = 10

# 1. Definimos el ID a consultar
id_para_contar = st.session_state.get("usuario_id", 0)

# 2. Obtenemos el nombre y plan de la sesión
nombre_usuario = st.session_state["usuario_nombre"]
plan_usuario = st.session_state["usuario_plan"]

# 3. Consultamos el conteo real usando nuestra función del conexion_sql.py
archivos_procesados = obtener_conteo_archivos(id_para_contar)

# Renderizado de métricas (esto se queda igual, pero ahora 'archivos_procesados' tendrá el valor real)
col_user, col_plan, col_usage = st.columns(3)
with col_user:
    st.metric(label="👤 Cuenta", value=nombre_usuario)
with col_plan:
    st.metric(label="💎 Nivel de Plan", value=plan_usuario)
with col_usage:
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
            df_original = pd.read_csv(archivo_cargado, sep=';', nrows=50000)
            
            with st.expander("👀 Ver estructura del archivo original cargado"):
                st.dataframe(df_original, use_container_width=True)
            
            st.write("### ⚙️ Preferencias de Optimización")
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1: eliminar_dup = st.checkbox("Eliminar registros duplicados", value=True)
            with col_opt2: reparar_nulos = st.checkbox("Autocompletar celdas vacías", value=True)
            
            if st.button("✨ Procesar y Optimizar Base de Datos"):
                with st.spinner("Ejecutando algoritmos de transformación..."):
                
                    try:
                        # 1. Transposición directa sin crear copias innecesarias
                        df_vertical = df_original.transpose()
                        
                        # 2. Asignar encabezados y limpiar índices
                        df_vertical.columns = df_vertical.iloc[0].astype(str)
                        df_vertical = df_vertical.iloc[1:] # Usamos iloc para evitar copias pesadas
                        
                        # 3. Limpieza de datos en una sola pasada (sin bucles 'for' lentos)
                        # Reemplazamos ',' por '.' en todo el df y convertimos a numérico
                        df_vertical = df_vertical.replace(',', '.', regex=True)
                        df_vertical = df_vertical.apply(pd.to_numeric, errors='coerce')
                            
                    except Exception as e:
                        st.error(f"Error procesando datos: {e}")
                        st.stop()

                   
                    # 4. CÁLCULO DE MÉTRICAS (Sin usar nombre_columna)
                    filas_finales = len(df_vertical)
                    # Contar nulos y duplicados sobre el resultado final
                    nulos_reparados = df_vertical.isna().sum().sum()
                    duplicados_eliminados = df_vertical.duplicated().sum()
                    
                    # Registrar log en base de datos
                    nombre_salida = f"optimizando_{archivo_cargado.name}"
                    # Usamos el ID del usuario si está conectado, si no, le asignamos 0 (Invitado)
                    usuario_id = st.session_state.get("usuario_id")
                    id_registro = int(usuario_id) if usuario_id is not None else 0
                    conexion_sql.registrar_archivo(id_registro, nombre_salida, len(df_vertical), len(df_vertical.columns))
                
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

# Reemplaza la lógica actual en tab_historial con esto:
with tab_historial:
    st.header("🔄 Historial y Auditoría de Procesos")
    
    usuario_id = st.session_state.get("usuario_id")
    id_para_consultar = int(usuario_id) if usuario_id is not None else 0
    
    if st.button("🔄 Sincronizar y Actualizar Historial"):
        rows = obtener_historial_usuario(id_para_consultar)
        
        if rows:
            # Creamos el DataFrame correctamente
            df_historial = pd.DataFrame(rows, columns=["Archivo", "Filas", "Columnas", "Fecha"])
            st.dataframe(df_historial, use_container_width=True)
        else:
            st.info(f"No hay registros procesados para el ID {id_para_consultar}.")

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
                    # Validación de formato de correo electrónica integrada de forma segura
                    import re
                    patron_correo = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                    
                    if not re.match(patron_correo, nuevo_email):
                        st.error("❌ Por favor, ingresa un correo electrónico válido (ejemplo@correo.com).")
                    else:
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
        if st.button("⚠️ REINICIAR TODO Y CREAR TABLA LIMPIA"):
            conn = sqlite3.connect("thedatafixer.db")
            cursor = conn.cursor()
            # Destruye todo
            cursor.execute("DROP TABLE IF EXISTS historial_archivos")
            # Crea la tabla de nuevo
            cursor.execute("""
                CREATE TABLE historial_archivos (
                    id_usuario INTEGER,
                    nombre_archivo TEXT,
                    filas INTEGER,
                    columnas INTEGER,
                    fecha_procesado TEXT
                )
            """)
            conn.commit()
            conn.close()
            st.success("Base de datos recreada. Prueba procesar ahora.")
            st.rerun()
            
        if st.button("❌ Cerrar Sesión", use_container_width=True):
            st.session_state["conectado"] = False
            st.session_state["usuario_id"] = None
            st.session_state["usuario_nombre"] = "Invitado"
            st.session_state["usuario_plan"] = "Gratis"
            st.info("Sesion cerrada correctamente.")
            st.rerun()