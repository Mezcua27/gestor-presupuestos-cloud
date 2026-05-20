import streamlit as st
import datetime
import hashlib
import io
import pandas as pd
import urllib.parse

# 📄 Importaciones para ReportLab (PDFs Avanzados)
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# ☁️ Conexión oficial a Supabase
SUPABASE_URL = "https://aaossliyjhlddjygkhyl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhb3NzbGl5amhsZGRqeWdraHlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxODg3MjYsImV4cCI6MjA5NDc2NDcyNn0.cBMyrkW3L-Yvc_6jadmMq5JNeuXV93hAI-R7VkaZvCw"

from supabase import create_client, Client

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ==========================================
# 🔐 SEGURIDAD Y CONTROL DE ACCESO
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

def consultar_todos_los_usuarios():
    try:
        res = supabase.table("usuarios").select("*").execute()
        return res.data if res.data else []
    except:
        return []

def eliminar_usuario_en_bd(username_a_borrar):
    try:
        supabase.table("usuarios").delete().eq("username", username_a_borrar).execute()
        return True
    except:
        return False

# ==========================================
# 📦 LOGÍSTICA DE CATALOGO / PRODUCTOS
# ==========================================

def consultar_productos(empresa, username=""):
    try:
        columnas = "id, categoria, elemento, marca_fabricante, precio_unitario, unidad_medida, foto_url"
        if username.lower().strip() == "admin":
            res = supabase.table("productos").select(f"{columnas}, empresa").execute()
        else:
            res = supabase.table("productos").select(columnas).eq("empresa", empresa.lower().strip()).execute()
        return res.data if res.data else []
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
        return supabase.storage.from_(bucket_name).get_public_url(path_en_bucket)
    except:
        return None

# ==========================================
# 👥 RELACIONES Y CLIENTES
# ==========================================

def consultar_clientes(empresa, username=""):
    try:
        if username.lower().strip() == "admin":
            res = supabase.table("clientes").select("id, numero_cliente, nombre, telefono, email, empresa").execute()
        else:
            res = supabase.table("clientes").select("id, numero_cliente, nombre, telefono, email").eq("empresa", empresa.lower().strip()).execute()
        return res.data if res.data else []
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
        supabase.table("clientes").update({"nombre": nombre, "telefono": telefono, "email": email}).eq("id", cli_id).execute()
        return True
    except:
        return False

def eliminar_cliente_en_bd(cli_id):
    try:
        supabase.table("clientes").delete().eq("id", cli_id).execute()
        return True
    except:
        return False

# ==========================================
# ✍️ CONTROL FINANCIERO Y HISTORIAL
# ==========================================

def obtener_siguiente_id_presupuesto(empresa):
    try:
        res = supabase.table("budgets").select("count", count="exact").eq("empresa", empresa.lower().strip()).execute()
        return f"PRE-{(res.count or 0) + 1:04d}"
    except: 
        return "PRE-0001"

def guardar_presupuesto_en_bd(id_presupuesto, numero_cliente, items, descuento, iva_porcentaje, empresa):
    try:
        # Insertar cabecera del presupuesto
        supabase.table("budgets").insert({
            "id_presupuesto": id_presupuesto, 
            "numero_cliente": numero_cliente, 
            "estado": "Pendiente", 
            "descuento_porcentaje": descuento,
            "iva_porcentaje": iva_porcentaje,
            "empresa": empresa.lower().strip()
        }).execute()
        
        # 🛠️ Inserción segura con doble mapeo por si la base de datos pide 'quantity' o 'cantidad'
        for item in items:
            supabase.table("detalles_presupuesto").insert({
                "id_presupuesto": id_presupuesto, 
                "marca_producto": item['elemento'], 
                "modelo_producto": item['marca_fabricante'],
                "precio_cobrado": item['precio'], 
                "cantidad": item['cantidad'],
                "quantity": item['cantidad']
            }).execute()
        return True
    except Exception as e:
        # Permite ver el error exacto en la terminal si vuelve a fallar la estructura de la tabla
        print("Error Supabase Insert:", str(e))
        return False

def consultar_historial_presupuestos(empresa, username=""):
    try:
        if username.lower().strip() == "admin":
            res = supabase.table("budgets").select("id_presupuesto, estado, fecha_envio, descuento_porcentaje, iva_porcentaje, numero_cliente, empresa").execute()
        else:
            res = supabase.table("budgets").select("id_presupuesto, estado, fecha_envio, descuento_porcentaje, iva_porcentaje, numero_cliente").eq("empresa", empresa.lower().strip()).execute()
        
        presupuestos = res.data if res.data else []
        
        if presupuestos:
            res_clientes = supabase.table("clientes").select("numero_cliente, nombre, telefono, email").execute()
            dict_clientes = {c["numero_cliente"]: c for c in res_clientes.data} if res_clientes.data else {}
            
            for p in presupuestos:
                num_c = p.get("numero_cliente")
                if num_c in dict_clientes:
                    p["clientes"] = dict_clientes[num_c]
                else:
                    p["clientes"] = {"nombre": "Cliente General", "telefono": "No registrado", "email": "-"}
        return presupuestos
    except: 
        return []

def consultar_detalles_de_un_presupuesto(id_presupuesto):
    try:
        res = supabase.table("detalles_presupuesto").select("marca_producto, modelo_producto, precio_cobrado, quantity:cantidad, cantidad").eq("id_presupuesto", id_presupuesto).execute()
        return res.data if res.data else []
    except: 
        return []

def registrar_envio_presupuesto(id_presupuesto):
    fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    supabase.table("budgets").update({"estado": "Enviado", "fecha_envio": fecha_hoy}).eq("id_presupuesto", id_presupuesto).execute()

def actualizar_estado_presupuesto(id_presupuesto, nuevo_estado):
    supabase.table("budgets").update({"estado": nuevo_estado}).eq("id_presupuesto", id_presupuesto).execute()

# --- 🎨 GENERACIÓN DE PDF CORPORATIVO PREMIUM ---
def generar_pdf_bytes(id_presupuesto, nombre_empresa_activa):
    res = supabase.table("budgets").select("estado, fecha_envio, descuento_porcentaje, iva_porcentaje, numero_cliente").eq("id_presupuesto", id_presupuesto).execute()
    if not res.data: return None
    
    pres_cabecera = res.data[0]
    estado = pres_cabecera["estado"]
    fecha_envio = pres_cabecera["fecha_envio"] or datetime.date.today().strftime("%Y-%m-%d")
    pct_descuento = float(pres_cabecera.get("descuento_porcentaje", 0) or 0)
    pct_iva = float(pres_cabecera.get("iva_porcentaje", 21) or 0)
    
    res_c = supabase.table("clientes").select("nombre, email, telefono").eq("numero_cliente", pres_cabecera.get("numero_cliente")).execute()
    info_cliente = res_c.data[0] if res_c.data else {"nombre": "Cliente General", "email": "-", "telefono": "-"}
    
    articulos = consultar_detalles_de_un_presupuesto(id_presupuesto)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    COLOR_PRIMARIO = colors.HexColor("#1A365D")
    COLOR_SECUNDARIO = colors.HexColor("#2B6CB0")
    COLOR_TEXTO_DARK = colors.HexColor("#2D3748")
    COLOR_BG_TABLA = colors.HexColor("#EDF2F7")
    
    pdf.saveState()
    pdf.setFont("Helvetica-Bold", 38)
    pdf.setFillColorRGB(0.95, 0.95, 0.95)
    pdf.translate(300, 420)
    pdf.rotate(45)
    pdf.drawCentredString(0, 0, "OFERTA COMERCIAL")
    pdf.restoreState()
    
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.rect(0, 720, 612, 92, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(40, 755, nombre_empresa_activa.upper())
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#E2E8F0"))
    pdf.drawString(40, 740, "Soluciones Profesionales y Suministros")
    
    pdf.setFillColor(colors.white)
    pdf.rect(440, 735, 130, 45, fill=True, stroke=False)
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(505, 760, "PRESUPUESTO")
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(COLOR_SECUNDARIO)
    pdf.drawCentredString(505, 745, id_presupuesto)
    
    pdf.setFillColor(COLOR_TEXTO_DARK)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(40, 680, "DATOS DEL DOCUMENTO")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(40, 665, f"Fecha de Emisión: {fecha_envio}")
    pdf.drawString(40, 652, f"Vencimiento (15d): {(datetime.datetime.strptime(fecha_envio, '%Y-%m-%d') + datetime.timedelta(days=15)).strftime('%Y-%m-%d')}")
    pdf.drawString(40, 639, f"Estado Actual: {estado.upper()}")
    
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(320, 680, "DESTINATARIO / CLIENTE")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(320, 665, f"Razón Social: {info_cliente['nombre']}")
    pdf.drawString(320, 652, f"Email: {info_cliente['email']}")
    pdf.drawString(320, 639, f"Teléfono: {info_cliente['telefono']}")
    
    pdf.setStrokeColor(colors.HexColor("#CBD5E0"))
    pdf.setLineWidth(0.5)
    pdf.line(40, 620, 570, 620)
    
    y_superior = 595
    pdf.setFillColor(COLOR_BG_TABLA)
    pdf.rect(40, y_superior, 530, 20, fill=True, stroke=False)
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(48, y_superior + 6, "DESCRIPCIÓN DEL PRODUCTO / COMPONENTE")
    pdf.drawCentredString(320, y_superior + 6, "PRECIO U.")
    pdf.drawCentredString(420, y_superior + 6, "CANTIDAD")
    pdf.drawCentredString(525, y_superior + 6, "SUBTOTAL")
    
    estilos = getSampleStyleSheet()
    estilo_celda = ParagraphStyle('EstiloCeldaPDF', parent=estilos['Normal'], fontName='Helvetica', fontSize=9, leading=11, textColor=COLOR_TEXTO_DARK)
    
    y_pos = y_superior - 20
    subtotal_acumulado = 0.0
    
    for art in articulos:
        cant_val = art.get('quantity', art.get('cantidad', 1))
        sub_art = art['precio_cobrado'] * cant_val
        subtotal_acumulado += sub_art
        
        texto_producto = f"**{art['marca_producto']}** - {art['modelo_producto']}"
        p = Paragraph(texto_producto, estilo_celda)
        ancho_disponible = 230
        lineas_parrafo = p.wrap(ancho_disponible, 100)
        alto_texto = lineas_parrafo[1]
        
        if alto_texto > 11:
            y_pos -= (alto_texto - 11)
            
        p.drawOn(pdf, 48, y_pos)
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(320, y_pos + 1, f"{art['precio_cobrado']:.2f}€")
        pdf.drawCentredString(420, y_pos + 1, str(cant_val))
        pdf.drawCentredString(525, y_pos + 1, f"{sub_art:.2f}€")
        
        pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
        pdf.line(40, y_pos - 6, 570, y_pos - 6)
        y_pos -= 22
        
    y_inferior = y_pos + 16
    pdf.setStrokeColor(colors.HexColor("#CBD5E0"))
    pdf.line(40, y_superior + 20, 40, y_inferior)
    pdf.line(570, y_superior + 20, 570, y_inferior)
    pdf.line(40, y_inferior, 570, y_inferior)
    
    importe_descuento = subtotal_acumulado * (pct_descuento / 100.0)
    base_imponible = subtotal_acumulado - importe_descuento
    importe_iva = base_imponible * (pct_iva / 100.0)
    total_general = base_imponible + importe_iva
    
    y_bloque = y_inferior - 25
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(COLOR_TEXTO_DARK)
    
    pdf.drawString(360, y_bloque, "Subtotal Bruto:")
    pdf.drawRightString(560, y_bloque, f"{subtotal_acumulado:.2f} €")
    
    if pct_descuento > 0:
        y_bloque -= 14
        pdf.setFillColor(colors.HexColor("#C53030"))
        pdf.drawString(360, y_bloque, f"Descuento Comercial ({pct_descuento:.0f}%):")
        pdf.drawRightString(560, y_bloque, f"-{importe_descuento:.2f} €")
        pdf.setFillColor(COLOR_TEXTO_DARK)
        
    y_bloque -= 14
    pdf.drawString(360, y_bloque, "Base Imponible:")
    pdf.drawRightString(560, y_bloque, f"{base_imponible:.2f} €")
    
    y_bloque -= 14
    pdf.drawString(360, y_bloque, f"I.V.A. Aplicado ({pct_iva:.0f}%):")
    pdf.drawRightString(560, y_bloque, f"{importe_iva:.2f} €")
    
    y_bloque -= 10
    pdf.setStrokeColor(COLOR_PRIMARIO)
    pdf.setLineWidth(1)
    pdf.line(360, y_bloque, 570, y_bloque)
    
    y_bloque -= 16
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.drawString(360, y_bloque, "TOTAL NETO:")
    pdf.drawRightString(560, y_bloque, f"{total_general:.2f} €")
    
    y_firma = y_bloque - 65
    pdf.setStrokeColor(colors.HexColor("#CBD5E0"))
    pdf.setLineWidth(0.5)
    pdf.line(40, y_firma, 200, y_firma)
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.HexColor("#718096"))
    pdf.drawString(40, y_firma - 12, "Firma de Conformidad Cliente")
    pdf.drawString(40, y_firma - 22, "Fecha: ____ / ____ / ________")
    
    pdf.setFont("Helvetica-Oblique", 7.5)
    pdf.setFillColor(colors.HexColor("#A0AEC0")) 
    pdf.drawCentredString(306, 40, f"Este presupuesto está sujeto a las condiciones generales de servicio de {nombre_empresa_activa.upper()}.")
    pdf.drawCentredString(306, 28, f"Validez legal de los precios mostrados: 15 días naturales desde su generación ({fecha_envio}).")
    
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

else:
    es_admin = st.session_state.usuario.lower().strip() == "admin"
    opciones_menu = ["🏠 Inicio", "📦 Productos", "👥 Clientes", "✍️ Nuevo Presupuesto", "📜 Historial"]
    if es_admin:
        st.sidebar.title("👑 PANEL ADMINISTRADOR")
        opciones_menu.insert(1, "👥 Gestión de Usuarios")
    else:
        st.sidebar.title(f"🏢 {st.session_state.empresa.upper()}")
        
    st.sidebar.caption(f"Usuario activo: {st.session_state.usuario}")
    menu = st.sidebar.radio("Navegación", opciones_menu)
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    if menu == "🏠 Inicio":
        st.title(f"🏠 Panel de Control - {st.session_state.empresa.upper()}")
        st.write("Seguimiento comercial y control de vencimientos automáticos.")
        st.subheader("⚠️ Alertas de Validez Comercial (Ofertas de 15 días)")
        
        historial_alertas = consultar_historial_presupuestos(st.session_state.empresa, st.session_state.usuario)
        presupuestos_enviados = [h for h in historial_alertas if h["estado"] == "Enviado" and h.get("fecha_envio")]
        
        if not presupuestos_enviados:
            st.success("🎉 No tienes ningún presupuesto pendiente de vencimiento.")
        else:
            fecha_actual = datetime.date.today()
            for p in presupuestos_enviados:
                try:
                    fecha_envio_obj = datetime.datetime.strptime(p["fecha_envio"], "%Y-%m-%d").date()
                    dias_restantes = 15 - (fecha_actual - fecha_envio_obj).days
                    nombre_c = p["clientes"]["nombre"] if p.get("clientes") else "Cliente Desconocido"
                    
                    if dias_restantes < 0:
                        st.error(f"🔴 **{p['id_presupuesto']}** | **{nombre_c}** | Enviado hace {abs(dias_restantes)+15} días. **HA CADUCADO**.")
                    elif dias_restantes <= 3:
                        st.warning(f"🚨 **¡Urgente! {p['id_presupuesto']}** | **{nombre_c}** | Quedan {dias_restantes} días de validez.")
                    else:
                        st.info(f"✅ **{p['id_presupuesto']}** | **{nombre_c}** | Quedan {dias_restantes} días activos.")
                except: pass

    elif menu == "👥 Gestión de Usuarios" and es_admin:
        st.title("👥 Control Maestro de Usuarios / Operarios")
        tab_lista_u, tab_borrar_u = st.tabs(["👁️ Ver Usuarios Activos", "❌ Dar de Baja Cuenta"])
        
        with tab_lista_u:
            usuarios = consultar_todos_los_usuarios()
            if not usuarios:
                st.info("No hay cuentas registradas.")
            else:
                df_u = pd.DataFrame(usuarios)
                if "password_hash" in df_u.columns: df_u = df_u.drop(columns=["password_hash"])
                st.dataframe(df_u.rename(columns={"username":"Usuario", "empresa":"Empresa Asignada"}), use_container_width=True, hide_index=True)
                
        with tab_borrar_u:
            usuarios_eliminar = consultar_todos_los_usuarios()
            lista_nombres = [u["username"] for u in usuarios_eliminar if u["username"] != "admin"]
            if lista_nombres:
                u_a_borrar = st.selectbox("Selecciona la cuenta que deseas eliminar permanentemente", lista_nombres)
                if st.button("⚠️ Confirmar Borrado Absoluto", type="primary", use_container_width=True):
                    if eliminar_usuario_en_bd(u_a_borrar):
                        st.success(f"Usuario {u_a_borrar} borrado."); st.rerun()
            else:
                st.info("No hay cuentas operarias que puedan ser borradas.")

    elif menu == "📦 Productos":
        st.title("📦 Gestión del Catálogo de Productos")
        tab_ver_p, tab_add_p, tab_excel_p, tab_fotos_p = st.tabs(["👁️ Ver Catálogo", "➕ Añadir Manual", "📥 Importar desde Excel", "✏️ Modificar / Fotos"])
        
        with tab_ver_p:
            lista_p = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            if lista_p:
                for p in lista_p:
                    col_t, col_im = st.columns([3, 1])
                    with col_t:
                        st.markdown(f"### {p['elemento']} ({p['marca_fabricante']})")
                        st.write(f"**Categoría:** {p['categoria']} | **Precio:** {p['precio_unitario']:.2f}€ | **Medida:** {p['unidad_medida']}")
                    with col_im:
                        if p.get("foto_url"): st.image(p["foto_url"], width=100)
                        else: st.caption("Sin foto")
                    st.divider()
            else: st.info("Catálogo vacío.")
            
        with tab_add_p:
            cat = st.text_input("Categoría")
            elem = st.text_input("Elemento/Producto")
            marca = st.text_input("Marca / Fabricante")
            precio = st.number_input("Precio Unitario (€)", min_value=0.0, step=0.1)
            unid = st.selectbox("Unidad", ["Uds.", "Metros", "Kg", "Horas"])
            if st.button("Guardar Producto"):
                guardar_producto_en_bd(cat, elem, marca, precio, unid, st.session_state.empresa)
                st.rerun()
                
        with tab_excel_p:
            archivo_excel = st.file_uploader("Selecciona archivo .xlsx", type=["xlsx"])
            if archivo_excel and st.button("🚀 Procesar e Importar todo el Excel", use_container_width=True):
                try:
                    df = pd.read_excel(archivo_excel)
                    for _, row in df.iterrows():
                        guardar_producto_en_bd(
                            str(row.get('categoria', 'General')), 
                            str(row.get('elemento', 'Producto sin nombre')), 
                            str(row.get('marca_fabricante', 'Genérico')), 
                            float(row.get('precio_unitario', 0.0)), 
                            str(row.get('unidad_medida', 'Uds.')), 
                            st.session_state.empresa
                        )
                    st.success("¡Catálogo del Excel importado con éxito!"); st.rerun()
                except Exception as e: st.error(f"Error procesando excel: {str(e)}")
                
        with tab_fotos_p:
            lista_p_edit = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            if lista_p_edit:
                opciones_p = {f"{p['elemento']} - {p['marca_fabricante']}": p for p in lista_p_edit}
                p_sel = st.selectbox("Selecciona producto a modificar", list(opciones_p.keys()))
                prod_data = opciones_p[p_sel]
                
                edit_cat = st.text_input("Editar Categoría", value=prod_data['categoria'])
                edit_elem = st.text_input("Editar Elemento", value=prod_data['elemento'])
                edit_marca = st.text_input("Editar Marca", value=prod_data['marca_fabricante'])
                edit_precio = st.number_input("Editar Precio (€)", min_value=0.0, value=float(prod_data['precio_unitario']))
                edit_unid = st.selectbox("Editar Unidad", ["Uds.", "Metros", "Kg", "Horas"])
                
                archivo_foto = st.file_uploader("🖼️ Subir o Cambiar Foto del Producto", type=["jpg", "jpeg", "png"])
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💾 Guardar Cambios", use_container_width=True):
                        actualizar_producto_en_bd(prod_data['id'], edit_cat, edit_elem, edit_marca, edit_precio, edit_unid)
                        if archivo_foto:
                            url_subida = subir_imagen_a_supabase(archivo_foto.getvalue(), archivo_foto.name)
                            if url_subida: actualizar_foto_producto_en_bd(prod_data['id'], url_subida)
                        st.success("Datos actualizados correctamente."); st.rerun()
                with col_b2:
                    if st.button("🗑️ Eliminar Producto", type="primary", use_container_width=True):
                        eliminar_producto_en_bd(prod_data['id'])
                        st.rerun()

    elif menu == "👥 Clientes":
        st.title("👥 Gestión de Clientes")
        tab_v_cli, tab_e_cli = st.tabs(["👁️ Directorio", "✏️ Crear / Modificar Clientes"])
        
        with tab_v_cli:
            st.dataframe(consultar_clientes(st.session_state.empresa, st.session_state.usuario), use_container_width=True, hide_index=True)
            
        with tab_e_cli:
            st.subheader("Añadir Nuevo Cliente")
            n = st.text_input("Nombre / Razón Social")
            t = st.text_input("Teléfono (Ej: 34600112233)")
            e = st.text_input("Email Corporativo")
            if st.button("Guardar Cliente en la Nube", use_container_width=True):
                guardar_cliente_en_bd(n, t, e, st.session_state.empresa)
                st.rerun()
                
            st.divider()
            st.subheader("Modificar / Dar de Baja Cliente Existente")
            lista_c_edit = consultar_clientes(st.session_state.empresa, st.session_state.usuario)
            if lista_c_edit:
                opciones_c = {f"{c['numero_cliente']} - {c['nombre']}": c for c in lista_c_edit}
                c_sel = st.selectbox("Selecciona un cliente", list(opciones_c.keys()))
                cli_data = opciones_c[c_sel]
                
                edit_n_cli = st.text_input("Modificar Nombre", value=cli_data['nombre'])
                edit_t_cli = st.text_input("Modificar Teléfono", value=cli_data['telefono'])
                edit_e_cli = st.text_input("Modificar Email", value=cli_data['email'])
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("💾 Actualizar Ficha Cliente", use_container_width=True):
                        actualizar_cliente_en_bd(cli_data['id'], edit_n_cli, edit_t_cli, edit_e_cli)
                        st.rerun()
                with col_c2:
                    if st.button("🗑️ Dar de Baja Cliente", type="primary", use_container_width=True):
                        eliminar_cliente_en_bd(cli_data['id'])
                        st.rerun()

    elif menu == "✍️ Nuevo Presupuesto":
        st.title("✍️ Generar Presupuesto Comercial")
        id_pres = obtener_siguiente_id_presupuesto(st.session_state.empresa)
        
        clientes = consultar_clientes(st.session_state.empresa, st.session_state.usuario)
        opciones_clientes = {f"{c['numero_cliente']} - {c['nombre']}": c['numero_cliente'] for c in clientes}
        
        if opciones_clientes:
            cliente_sel = st.selectbox("Selecciona el Cliente", list(opciones_clientes.keys()))
            productos = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            opciones_productos = {f"{p['elemento']} ({p['marca_fabricante']}) - {p['precio_unitario']}€": p for p in productos}
            
            if opciones_productos:
                col_p, col_c = st.columns([3, 1])
                with col_p: prod_sel = st.selectbox("Selecciona Producto", list(opciones_productos.keys()))
                with col_c: cant = st.number_input("Cantidad", min_value=1, value=1)
                    
                if st.button("➕ Añadir línea al presupuesto", use_container_width=True):
                    st.session_state.items_presupuesto.append({
                        "elemento": opciones_productos[prod_sel]['elemento'], 
                        "marca_fabricante": opciones_productos[prod_sel]['marca_fabricante'], 
                        "precio": opciones_productos[prod_sel]['precio_unitario'], 
                        "cantidad": cant
                    })
                
                if st.session_state.items_presupuesto:
                    st.divider()
                    st.subheader("Líneas Añadidas")
                    st.dataframe(st.session_state.items_presupuesto, use_container_width=True)
                    
                    subtotal_interfaz = sum(i['precio'] * i['cantidad'] for i in st.session_state.items_presupuesto)
                    
                    st.divider()
                    st.subheader("⚙️ Configuración Fiscal y Comercial")
                    col_desc, col_iva = st.columns(2)
                    with col_desc: descuento_global = st.number_input("Descuento Comercial Global (%)", min_value=0, max_value=100, value=0, step=1)
                    with col_iva: tipo_iva = st.selectbox("Tipo de I.V.A. Aplicable", [21, 10, 4, 0], format_func=lambda x: f"General ({x}%)" if x == 21 else (f"Reducido ({x}%)" if x > 0 else "Exento (0%)"))
                    
                    total_descuento_ui = subtotal_interfaz * (descuento_global / 100.0)
                    base_imponible_ui = subtotal_interfaz - total_descuento_ui
                    total_iva_ui = base_imponible_ui * (tipo_iva / 100.0)
                    total_neto_ui = base_imponible_ui + total_iva_ui
                    
                    st.markdown("### 📊 Resumen Económico")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Subtotal Bruto", f"{subtotal_interfaz:.2f} €")
                    c2.metric("Descuento", f"-{total_descuento_ui:.2f} €" if descuento_global > 0 else "0.00 €")
                    c3.metric("Base Imponible", f"{base_imponible_ui:.2f} €")
                    c4.metric("TOTAL NETO", f"{total_neto_ui:.2f} €")
                    
                    if st.button("💾 Guardar y Confirmar Presupuesto", type="primary", use_container_width=True):
                        if guardar_presupuesto_en_bd(id_pres, opciones_clientes[cliente_sel], st.session_state.items_presupuesto, descuento_global, tipo_iva, st.session_state.empresa):
                            st.success(f"🎉 ¡Éxito! El presupuesto {id_pres} ha sido guardado de forma permanente en la base de datos.")
                            st.session_state.items_presupuesto = [] 
                        else:
                            st.error("Error crítico: Estructura de columnas incompatible detectada en 'detalles_presupuesto'.")

    elif menu == "📜 Historial":
        st.title("📜 Historial de Presupuestos")
        historial = consultar_historial_presupuestos(st.session_state.empresa, st.session_state.usuario)
        
        if not historial:
            st.info("📂 Aún no se han registrado presupuestos para esta empresa o el historial está vacío.")
        else:
            datos_tabla = []
            mapeo_completo = {}
            
            for h in historial:
                cod = h["id_presupuesto"]
                cli_info = h.get("clientes") or {"nombre": "Desconocido"}
                nombre_c = cli_info.get("nombre", "Desconocido")
                
                item_tabla = {"Código": cod, "Cliente": nombre_c, "Estado": h["estado"]}
                if es_admin: item_tabla["Empresa"] = h.get("empresa", "").upper()
                datos_tabla.append(item_tabla)
                
                mapeo_completo[cod] = {
                    "nombre": nombre_c,
                    "telefono": cli_info.get("telefono", ""),
                    "email": cli_info.get("email", ""),
                    "desc": float(h.get("descuento_porcentaje", 0) or 0),
                    "iva": float(h.get("iva_porcentaje", 21) or 0)
                }
                
            st.dataframe(datos_tabla, use_container_width=True, hide_index=True)
            id_sel = st.selectbox("Selecciona un código para gestionar o enviar:", [d["Código"] for d in datos_tabla])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✉️ Marcar Enviado", use_container_width=True): registrar_envio_presupuesto(id_sel); st.rerun()
            with col2:
                if st.button("✔️ Aceptar", use_container_width=True): actualizar_estado_presupuesto(id_sel, "Aceptado"); st.rerun()
            with col3:
                if st.button("❌ Rechazar", use_container_width=True): actualizar_estado_presupuesto(id_sel, "Rechazado"); st.rerun()
            
            st.divider()
            datos_c_sel = mapeo_completo[id_sel]
            articulos_p = consultar_detalles_de_un_presupuesto(id_sel)
            
            sub_calc = sum(art['precio_cobrado'] * art.get('quantity', art.get('cantidad', 1)) for art in articulos_p)
            base_calc = sub_calc - (sub_calc * (datos_c_sel["desc"] / 100.0))
            total_calc = base_calc + (base_calc * (datos_c_sel["iva"] / 100.0))
            
            pdf_data = generar_pdf_bytes(id_sel, st.session_state.empresa)
            if pdf_data:
                st.download_button(label="📥 Descargar PDF Ejecutivo Diseñado", data=pdf_data, file_name=f"Presupuesto_{id_sel}.pdf", mime="application/pdf", use_container_width=True)
            
            col_wa, col_em = st.columns(2)
            with col_wa:
                tel = str(datos_c_sel["telefono"]).strip()
                if tel and tel != "None" and tel != "No registrado":
                    msg = f"Hola *{datos_c_sel['nombre']}*.\n\nTe adjunto el presupuesto *{id_sel}* por un importe total de *{total_calc:.2f}€* (I.V.A. incluido).\n\nValidez de la oferta: 15 días."
                    st.link_button("🟢 Enviar por WhatsApp", f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}", use_container_width=True)
                else: st.button("🟢 Falta Teléfono Cliente", disabled=True, use_container_width=True)
            with col_em:
                email = str(datos_c_sel["email"]).strip()
                if email and email != "None" and email != "-":
                    asunto = f"Presupuesto {id_sel} - {st.session_state.empresa.upper()}"
                    cuerpo = f"Estimado/a {datos_c_sel['nombre']},\n\nLe hacemos entrega del presupuesto solicitado con código {id_sel} por un importe total de {total_calc:.2f}€ (I.V.A. incluido)."
                    st.link_button("🔵 Preparar Email", f"mailto:{email}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}", use_container_width=True)
                else: st.button("🔵 Falta Email Cliente", disabled=True, use_container_width=True)