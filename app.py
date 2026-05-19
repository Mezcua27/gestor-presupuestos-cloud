import streamlit as st
import datetime
import hashlib
import io
import pandas as pd

# 📄 Importaciones para ReportLab (PDFs)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ☁️ Conexión oficial a Supabase
SUPABASE_URL = "https://aaossliyjhlddjygkhyl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhb3NzbGl5amhsZGRqeWdraHlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxODg3MjYsImV4cCI6MjA5NDc2NDcyNn0.cBMyrkW3L-Yvc_6jadmMq5JNeuXV93hAI-R7VkaZvCw"

from supabase import create_client, Client

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ==========================================
# FUNCIONES DE BASE DE DATOS PROTEGIDAS
# ==========================================

def encriptar_contrasena(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_credenciales(username, password):
    try:
        pass_encriptada = encriptar_contrasena(password)
        res = supabase.table("usuarios").select("*").eq("username", username.lower().strip()).eq("password_hash", pass_encriptada).execute()
        if len(res.data) > 0:
            return res.data[0]
        return None
    except: 
        return None

def guardar_usuario_en_bd(username, password, empresa):
    try:
        user_limpio = username.lower().strip()
        empresa_limpia = empresa.lower().strip()
        if not user_limpio or not password or not empresa_limpia: 
            return False, "Por favor, rellena todos los campos."
            
        pass_encriptada = encriptar_contrasena(password)
        supabase.table("usuarios").insert({
            "username": user_limpio, 
            "password_hash": pass_encriptada,
            "empresa": empresa_limpia
        }).execute()
        return True, None
    except Exception as e: 
        return False, str(e)

# --- 👑 FUNCIONES EXCLUSIVAS DEL ADMIN CONTROL DE USUARIOS ---

def consultar_todos_los_usuarios():
    try:
        # Traemos TODOS los usuarios registrados sin importar su empresa ni alias raros
        res = supabase.table("usuarios").select("*").execute()
        if res.data:
            return res.data
        return []
    except Exception as e:
        print(f"Error real al traer usuarios: {str(e)}")
        return []

def eliminar_usuario_en_bd(username_a_borrar):
    try:
        # Eliminamos de forma segura buscando por el nombre de usuario único
        supabase.table("usuarios").delete().eq("username", username_a_borrar).execute()
        return True
    except:
        return False

# --- GESTIÓN DE PRODUCTOS ---

def consultar_productos(empresa, username=""):
    try:
        columnas = "id, categoria, elemento, marca_fabricante, precio_unitario (PVP con IVA), unidad_medida, foto_url"
        if username.lower().strip() == "admin":
            res = supabase.table("productos").select(f"{columnas}, empresa").execute()
        else:
            res = supabase.table("productos").select(columnas).eq("empresa", empresa.lower().strip()).execute()
        return res.data
    except: 
        return []

def guardar_producto_en_bd(categoria, elemento, marca, precio, unidad, empresa):
    try:
        supabase.table("productos").insert({
            "categoria": categoria, 
            "elemento": elemento, 
            "marca_fabricante": marca, 
            "precio_unitario": precio, 
            "unidad_medida": unidad, 
            "empresa": empresa.lower().strip()
        }).execute()
        return True
    except: 
        return False

def actualizar_producto_en_bd(prod_id, categoria, elemento, marca, precio, unidad):
    try:
        supabase.table("productos").update({
            "categoria": categoria, 
            "elemento": elemento, 
            "marca_fabricante": marca, 
            "precio_unitario": precio, 
            "unidad_medida": unidad
        }).eq("id", prod_id).execute()
        return True
    except:
        return False

def actualizar_foto_producto_en_bd(prod_id, url_foto):
    try:
        supabase.table("productos").update({"foto_url": url_foto}).eq("id", prod_id).execute()
        return True
    except:
        return False

def eliminar_producto_en_bd(prod_id):
    try:
        supabase.table("productos").delete().eq("id", prod_id).execute()
        return True
    except:
        return False

def subir_imagen_a_supabase(file_bytes, file_name):
    try:
        bucket_name = "productos-fotos"
        path_en_bucket = f"foto_{int(datetime.datetime.now().timestamp())}_{file_name}"
        
        supabase.storage.from_(bucket_name).upload(
            path=path_en_bucket,
            file=file_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        url_publica = supabase.storage.from_(bucket_name).get_public_url(path_en_bucket)
        return url_publica
    except Exception as e:
        st.error(f"Error técnico al subir al almacenamiento: {str(e)}")
        return None

# --- GESTIÓN DE CLIENTES ---

def consultar_clientes(empresa, username=""):
    try:
        if username.lower().strip() == "admin":
            res = supabase.table("clientes").select("id, numero_cliente, nombre, telefono, email, empresa").execute()
        else:
            res = supabase.table("clientes").select("id, numero_cliente, nombre, telefono, email").eq("empresa", empresa.lower().strip()).execute()
        return res.data
    except: 
        return []

def guardar_cliente_en_bd(nombre, telefono, email, empresa):
    try:
        empresa_limpia = empresa.lower().strip()
        res = supabase.table("clientes").select("numero_cliente").eq("empresa", empresa_limpia).execute()
        
        siguiente_num = len(res.data) + 1
        num_cliente = f"CLI-{siguiente_num:04d}"
        
        supabase.table("clientes").insert({
            "numero_cliente": num_cliente, 
            "nombre": nombre, 
            "telefono": telefono, 
            "email": email, 
            "empresa": empresa_limpia
        }).execute()
        return True, None
    except Exception as e: 
        return False, str(e)

def actualizar_cliente_en_bd(cli_id, nombre, telefono, email):
    try:
        supabase.table("clientes").update({
            "nombre": nombre, "telefono": telefono, "email": email
        }).eq("id", cli_id).execute()
        return True
    except:
        return False

def eliminar_cliente_en_bd(cli_id):
    try:
        supabase.table("clientes").delete().eq("id", cli_id).execute()
        return True
    except:
        return False

# --- PRESUPUESTOS Y HISTORIAL ---

def obtener_siguiente_id_presupuesto(empresa):
    try:
        res = supabase.table("budgets").select("count", count="exact").eq("empresa", empresa.lower().strip()).execute()
        return f"PRE-{(res.count or 0) + 1:04d}"
    except: 
        return "PRE-0001"

def guardar_presupuesto_en_bd(id_presupuesto, numero_cliente, items, empresa):
    try:
        supabase.table("budgets").insert({"id_presupuesto": id_presupuesto, "numero_cliente": numero_cliente, "estado": "Pendiente", "empresa": empresa.lower().strip()}).execute()
        for item in items:
            supabase.table("detalles_presupuesto").insert({
                "id_presupuesto": id_presupuesto, 
                "marca_producto": item['elemento'], 
                "modelo_producto": item['marca_fabricante'],
                "precio_cobrado": item['precio'], 
                "cantidad": item['cantidad']
            }).execute()
        return True
    except: 
        return False

def consultar_historial_presupuestos(empresa, username=""):
    try:
        if username.lower().strip() == "admin":
            res = supabase.table("budgets").select("id_presupuesto, estado, empresa, clientes(nombre)").execute()
        else:
            res = supabase.table("budgets").select("id_presupuesto, estado, clientes(nombre)").eq("empresa", empresa.lower().strip()).execute()
        return res.data
    except: 
        return []

def consultar_detalles_de_un_presupuesto(id_presupuesto):
    try:
        res = supabase.table("detalles_presupuesto").select("marca_producto, modelo_producto, precio_cobrado, quantity:cantidad").eq("id_presupuesto", id_presupuesto).execute()
        return res.data
    except: 
        return []

def registrar_envio_presupuesto(id_presupuesto):
    fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    supabase.table("budgets").update({"estado": "Enviado", "fecha_envio": fecha_hoy}).eq("id_presupuesto", id_presupuesto).execute()

def actualizar_estado_presupuesto(id_presupuesto, nuevo_estado):
    supabase.table("budgets").update({"estado": nuevo_estado}).eq("id_presupuesto", id_presupuesto).execute()

def generar_pdf_bytes(id_presupuesto):
    res = supabase.table("budgets").select("estado, fecha_envio").eq("id_presupuesto", id_presupuesto).execute()
    if not res.data: 
        return None
    estado, fecha_envio = res.data[0]["estado"], res.data[0]["fecha_envio"] or "No enviado aún"
    
    articulos = consultar_detalles_de_un_presupuesto(id_presupuesto)
    
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 750, "PRESUPUESTO FORMAL")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 730, f"Código: {id_presupuesto}")
    pdf.drawString(50, 715, f"Fecha: {fecha_envio}")
    pdf.drawString(50, 700, f"Estado: {estado}")
    pdf.line(50, 685, 550, 685)
    
    y_superior = 660
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(55, 645, "Producto / Elemento")
    pdf.drawCentredString(290, 645, "Precio U.")
    pdf.drawCentredString(390, 645, "Cant.")
    pdf.drawCentredString(495, 645, "Subtotal")
    pdf.line(50, 635, 550, 635)
    
    y_pos = 615
    total_acumulado = 0.0
    pdf.setFont("Helvetica", 10)
    for art in articulos:
        cant_val = art.get('quantity', art.get('cantidad', 1))
        subtotal = art['precio_cobrado'] * cant_val
        total_acumulado += subtotal
        pdf.drawString(55, y_pos, f"{art['marca_producto']} - {art['modelo_producto']}")
        pdf.drawCentredString(290, y_pos, f"{art['precio_cobrado']:.2f}€")
        pdf.drawCentredString(390, y_pos, str(cant_val))
        pdf.drawCentredString(495, y_pos, f"{subtotal:.2f}€")
        y_pos -= 20
        
    y_inferior = y_pos + 15
    pdf.line(50, y_superior, 550, y_superior)
    pdf.line(50, y_inferior, 550, y_inferior)
    pdf.line(50, y_superior, 50, y_inferior)
    pdf.line(240, y_superior, 240, y_inferior)
    pdf.line(340, y_superior, 340, y_inferior)
    pdf.line(440, y_superior, 440, y_inferior)
    pdf.line(550, y_superior, 550, y_inferior)
    
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(340, y_inferior - 20, "TOTAL:")
    pdf.drawCentredString(495, y_inferior - 20, f"{total_acumulado:.2f} €")
    pdf.save()
    
    buffer.seek(0)
    return buffer

# ==========================================
# INTERFAZ GRÁFICA (Streamlit)
# ==========================================

st.set_page_config(page_title="Gestor Cloud", page_icon="☁️", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "empresa" not in st.session_state:
    st.session_state.empresa = ""
if "items_presupuesto" not in st.session_state:
    st.session_state.items_presupuesto = []

# --- PANTALLA DE ACCESO ---
if not st.session_state.autenticado:
    st.title("☁️ Acceso Multi-Empresa")
    pestana_login, pestana_registro = st.tabs(["🔑 Iniciar Sesión", "🚀 Crear Cuenta"])
    
    with pestana_login:
        user_log = st.text_input("Usuario", key="log_user")
        pass_log = st.text_input("Contraseña", type="password", key="log_pass")
        if st.button("Entrar", use_container_width=True):
            datos_usuario = verificar_credenciales(user_log, pass_log)
            if datos_usuario:
                st.session_state.autenticado = True
                st.session_state.usuario = user_log
                st.session_state.empresa = datos_usuario.get("empresa", "global")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
                
    with pestana_registro:
        user_reg = st.text_input("Elige Nombre de Usuario", key="reg_user")
        pass_reg = st.text_input("Elige tu Contraseña", type="password", key="reg_pass")
        empresa_reg = st.text_input("Nombre de tu Empresa / Grupo de Trabajo")
        
        if st.button("Registrarme", use_container_width=True):
            exito, error_msg = guardar_usuario_en_bd(user_reg, pass_reg, empresa_reg)
            if exito:
                st.success(f"¡Cuenta asignada a la empresa '{empresa_reg.upper()}'! Ya puedes iniciar sesión.")
            else:
                st.error(f"No se pudo registrar: {error_msg}")

# --- APLICACIÓN PRINCIPAL ---
else:
    es_admin = st.session_state.usuario.lower().strip() == "admin"
    
    # ⚙️ Menú dinámico según si es Admin o un usuario de empresa normal
    opciones_menu = ["📦 Productos", "👥 Clientes", "✍️ Nuevo Presupuesto", "📜 Historial"]
    if es_admin:
        st.sidebar.title("👑 PANEL ADMINISTRADOR")
        opciones_menu.insert(0, "👥 Gestión de Usuarios")
    else:
        st.sidebar.title(f"🏢 {st.session_state.empresa.upper()}")
        
    st.sidebar.caption(f"Usuario activo: {st.session_state.usuario}")
    menu = st.sidebar.radio("Navegación", opciones_menu)
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.session_state.empresa = ""
        st.rerun()

    # --- 👑 SECCIÓN EXCLUSIVA: GESTIÓN DE OPERARIOS/USUARIOS (SÓLO ADMIN) ---
    if menu == "👥 Gestión de Usuarios" and es_admin:
        st.title("👥 Control Maestro de Usuarios / Operarios")
        st.write("Como administrador global, aquí puedes auditar las cuentas de los empleados registradas y gestionar sus accesos.")
        
        tab_lista_u, tab_crear_u = st.tabs(["👁️ Ver Usuarios Activos", "➕ Registrar Nueva Empresa/Usuario"])
        
        with tab_lista_u:
            usuarios = consultar_todos_los_usuarios()
            if not usuarios:
                st.info("No hay cuentas de usuario/empleados registradas en el sistema todavía.")
            else:
                df_u = pd.DataFrame(usuarios)
                
                # Renombramos para que se vea claro en el panel de control
                columnas_a_renombrar = {
                    "username": "Empleado / Operario", 
                    "empresa": "Empresa / Grupo"
                }
                if "created_at" in df_u.columns:
                    columnas_a_renombrar["created_at"] = "Fecha de Alta"
                    
                df_u = df_u.rename(columns=columnas_a_renombrar)
                
                # Ocultamos la contraseña hash por obvias razones de seguridad
                if "password_hash" in df_u.columns:
                    df_u = df_u.drop(columns=["password_hash"])
                    
                st.dataframe(df_u, use_container_width=True, hide_index=True)
                
                st.divider()
                st.subheader("🗑️ Dar de baja un usuario")
                # Excluimos al admin de las opciones para no autoborrarse
                opciones_borrar = {f"{u['username'].upper()} (Empresa: {u['empresa'].upper()})": u for u in usuarios if u['username'].lower() != 'admin'}
                
                if not opciones_borrar:
                    st.caption("No hay usuarios externos que borrar.")
                else:
                    u_seleccionado = st.selectbox("Selecciona la cuenta que deseas eliminar permanentemente:", list(opciones_borrar.keys()))
                    user_a_borrar = opciones_borrar[u_seleccionado]
                    
                    st.warning(f"⚠️ ¡Atención! Eliminarás al usuario '{user_a_borrar['username']}'. Esta acción no se puede deshacer.")
                    if st.button("Confirmar Eliminación Definitiva", type="secondary", use_container_width=True):
                        # Eliminamos por username para blindar el borrado si no hay clave ID estándar
                        if eliminar_usuario_en_bd(user_a_borrar['username']):
                            st.success(f"El usuario {user_a_borrar['username']} ha sido eliminado del sistema.")
                            st.rerun()
                            
        with tab_crear_u:
            st.subheader("Crear cuenta corporativa directa")
            st.write("Utiliza este formulario si quieres dar de alta tú mismo a un empleado/organización sin que tengan que registrarse desde fuera.")
            adm_user = st.text_input("Usuario corporativo", key="adm_u_reg")
            adm_pass = st.text_input("Contraseña inicial", type="password", key="adm_p_reg")
            adm_emp = st.text_input("Nombre de la Organización / Empresa", key="adm_e_reg")
            
            if st.button("Dar de alta cuenta", type="primary", use_container_width=True):
                exito, error_msg = guardar_usuario_en_bd(adm_user, adm_pass, adm_emp)
                if exito:
                    st.success(f"¡Empresa '{adm_emp.upper()}' registrada con éxito bajo el usuario '{adm_user}'!")
                else:
                    st.error(f"Error al registrar: {error_msg}")

    # --- SECCIÓN PRODUCTOS ---
    elif menu == "📦 Productos":
        st.title("📦 Gestión del Catálogo de Productos")
        
        tab_ver_prod, tab_anadir_prod, tab_importar_excel, tab_editar_prod = st.tabs([
            "👁️ Ver Catálogo", "➕ Añadir Manual", "📥 Importar desde Excel", "✏️ Modificar / Añadir Fotos"
        ])
        
        with tab_ver_prod:
            st.subheader("Catálogo Actual")
            lista_p = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            if lista_p:
                df_mostrar = pd.DataFrame(lista_p)
                df_mostrar = df_mostrar.rename(columns={
                    "categoria": "Categoría", "elemento": "Elemento / Componente", 
                    "marca_fabricante": "Marca / Fabricante", "precio_unitario": "Precio (€)", 
                    "unidad_medida": "Unidad", "foto_url": "Enlace Foto"
                })
                st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            else:
                st.info("No hay productos registrados en tu catálogo.")
                
        with tab_anadir_prod:
            st.subheader("Registrar nuevo producto a mano")
            cat = st.text_input("Categoría (Ej: Iluminación)")
            elem = st.text_input("Elemento / Componente (Ej: Proyector LED)")
            marca_f = st.text_input("Marca / Fabricante (Ej: Philips)")
            precio = st.number_input("Precio Unitario (€)", min_value=0.0, step=1.0, key="add_p_precio")
            unidad = st.selectbox("Unidad de Medida", ["Uds.", "Metros", "Kg", "Horas", "Litros"], key="add_p_unidad")
            
            if st.button("Guardar Producto", use_container_width=True):
                if cat and elem and marca_f:
                    if guardar_producto_en_bd(cat, elem, marca_f, precio, unidad, st.session_state.empresa):
                        st.success("¡Producto guardado correctamente!")
                        st.rerun()
                else:
                    st.warning("Por favor, rellena los campos de Categoría, Elemento y Marca.")
                    
        with tab_importar_excel:
            st.subheader("Carga masiva desde archivo Excel")
            st.write("Sube tu archivo Excel. El sistema buscará las columnas automáticamente.")
            archivo_excel = st.file_uploader("Selecciona tu archivo .xlsx", type=["xlsx"])
            
            if archivo_excel is not None:
                if st.button("🚀 Procesar e Importar todo el Excel", use_container_width=True):
                    try:
                        df = pd.read_excel(archivo_excel)
                        
                        # Si los títulos reales estaban más abajo, buscamos automáticamente la cabecera
                        if not any(col for col in df.columns if "categor" in str(col).lower()):
                            for i, fila in df.iterrows():
                                valores_fila = [str(v).lower() for v in fila.values]
                                if any("categor" in vf for vf in valores_fila):
                                    df = pd.read_excel(archivo_excel, skiprows=i+1)
                                    break

                        # Limpiamos los nombres de las columnas a minúsculas
                        df.columns = [str(c).strip().lower() for c in df.columns]
                        
                        # Mapeo inteligente por palabras clave (Flexible a tildes, mayúsculas y símbolos)
                        col_cat = next((c for c in df.columns if "categor" in c), None)
                        col_elem = next((c for c in df.columns if "elemento" in c or "componente" in c), None)
                        col_marca = next((c for c in df.columns if "marca" in c or "fabricante" in c), None)
                        col_precio = next((c for c in df.columns if "precio" in c or "eur" in c or "coste" in c), None)
                        col_unidad = next((c for c in df.columns if "unidad" in c or "medida" in c), None)

                        # Validación amigable de campos
                        columnas_faltantes = []
                        if not col_cat: columnas_faltantes.append("Categoría")
                        if not col_elem: columnas_faltantes.append("Elemento / Componente")
                        if not col_marca: columnas_faltantes.append("Marca / Fabricante")
                        if not col_precio: columnas_faltantes.append("Precio Unitario")
                        
                        if columnas_faltantes:
                            st.error(f"No encuentro estas columnas en tu Excel: {columnas_faltantes}. Por favor, comprueba los nombres de la cabecera.")
                        else:
                            # Limpiamos las celdas vacías de las filas críticas
                            df = df.dropna(subset=[col_cat, col_elem, col_marca])
                            
                            contador_exito = 0
                            for index, fila in df.iterrows():
                                c_cat = str(fila[col_cat]).strip()
                                c_elem = str(fila[col_elem]).strip()
                                c_marca = str(fila[col_marca]).strip()
                                
                                # Extraemos el precio con salvavidas por si viene como texto
                                try:
                                    valor_precio = fila[col_precio]
                                    c_precio = float(valor_precio) if pd.notnull(valor_precio) else 0.0
                                except:
                                    c_precio = 0.0
                                    
                                c_unidad = str(fila[col_unidad]).strip() if col_unidad and pd.notnull(fila[col_unidad]) else "Uds."
                                
                                exito = guardar_producto_en_bd(c_cat, c_elem, c_marca, c_precio, c_unidad, st.session_state.empresa)
                                if exito:
                                    contador_exito += 1
                                    
                            st.success(f"¡Importación masiva completada con éxito! Se han añadido {contador_exito} productos al catálogo.")
                            st.rerun()
                    except Exception as err:
                        st.error(f"Error inesperado al procesar el archivo: {str(err)}")
                        
        with tab_editar_prod:
            st.subheader("Modificar información o añadir foto real")
            lista_p_edit = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            if not lista_p_edit:
                st.info("No hay productos disponibles.")
            else:
                opciones_p = {f"[{p['categoria'].upper()}] {p['elemento']} - {p['marca_fabricante']}": p for p in lista_p_edit}
                p_seleccionado = st.selectbox("Selecciona producto a gestionar", list(opciones_p.keys()))
                prod_data = opciones_p[p_seleccionado]
                
                if prod_data.get("foto_url"):
                    st.image(prod_data["foto_url"], caption="Foto actual del producto", width=250)
                
                imagen_subida = st.file_uploader("Haz una foto o elige de tu galería", type=["jpg", "jpeg", "png"], key=f"foto_{prod_data['id']}")
                if imagen_subida is not None:
                    if st.button("📤 Subir y Enlazar Foto", use_container_width=True):
                        bytes_data = imagen_subida.read()
                        url_final = subir_imagen_a_supabase(bytes_data, imagen_subida.name)
                        if url_final and actualizar_foto_producto_en_bd(prod_data['id'], url_final):
                            st.success("¡Foto guardada y enlazada!")
                            st.rerun()
                
                edit_cat = st.text_input("Modificar Categoría", value=prod_data['categoria'])
                edit_elem = st.text_input("Modificar Elemento", value=prod_data['elemento'])
                edit_marca = st.text_input("Modificar Marca/Fabricante", value=prod_data['marca_fabricante'])
                edit_precio = st.number_input("Modificar Precio (€)", min_value=0.0, value=float(prod_data['precio_unitario']), step=0.5)
                edit_unidad = st.selectbox("Modificar Unidad", ["Uds.", "Metros", "Kg", "Horas", "Litros"], index=["Uds.", "Metros", "Kg", "Horas", "Litros"].index(prod_data['unidad_medida']))
                
                col_btn_p1, col_btn_p2 = st.columns(2)
                with col_btn_p1:
                    if st.button("💾 Guardar Cambios de Texto", type="primary", use_container_width=True):
                        if actualizar_producto_en_bd(prod_data['id'], edit_cat, edit_elem, edit_marca, edit_precio, edit_unidad):
                            st.success("¡Información actualizada!")
                            st.rerun()
                with col_btn_p2:
                    if st.button("🗑️ Eliminar del Catálogo", type="secondary", use_container_width=True):
                        if eliminar_producto_en_bd(prod_data['id']):
                            st.warning("Producto eliminado.")
                            st.rerun()

    # --- SECCIÓN CLIENTES ---
    elif menu == "👥 Clientes":
        st.title("👥 Gestión de Clientes")
        
        tab_ver_cli, tab_anadir_cli, tab_editar_cli = st.tabs(["👁️ Ver Clientes", "➕ Añadir Cliente", "✏️ Modificar / Eliminar"])
        
        with tab_ver_cli:
            st.subheader("Lista de Clientes")
            lista_c = consultar_clientes(st.session_state.empresa, st.session_state.usuario)
            if lista_c:
                st.dataframe(lista_c, use_container_width=True, hide_index=True)
            else:
                st.info("No hay clientes guardados en tu agenda.")
                
        with tab_anadir_cli:
            st.subheader("Registrar nuevo cliente")
            nombre = st.text_input("Nombre / Razón Social")
            telefono = st.text