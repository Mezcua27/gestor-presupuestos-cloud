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
from reportlab.lib import colors  # 🌟 Esencial para paletas de colores profesionales

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

# --- GESTIÓN DE PRODUCTOS ---

def consultar_productos(empresa, username=""):
    try:
        columnas = "id, categoria, elemento, marca_fabricante, precio_unitario, unidad_medida, foto_url"
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

# --- PRESUPUESTOS Y HISTORIAL ---

def obtener_siguiente_id_presupuesto(empresa):
    try:
        res = supabase.table("budgets").select("count", count="exact").eq("empresa", empresa.lower().strip()).execute()
        return f"PRE-{(res.count or 0) + 1:04d}"
    except: 
        return "PRE-0001"

def guardar_presupuesto_en_bd(id_presupuesto, numero_cliente, items, descuento, iva_porcentaje, empresa):
    try:
        supabase.table("budgets").insert({
            "id_presupuesto": id_presupuesto, 
            "numero_cliente": numero_cliente, 
            "estado": "Pendiente", 
            "descuento_porcentaje": descuento,
            "iva_porcentaje": iva_porcentaje,
            "empresa": empresa.lower().strip()
        }).execute()
        
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
            res = supabase.table("budgets").select("id_presupuesto, estado, fecha_envio, descuento_porcentaje, iva_porcentaje, empresa, clientes(nombre, telefono, email)").execute()
        else:
            res = supabase.table("budgets").select("id_presupuesto, estado, fecha_envio, descuento_porcentaje, iva_porcentaje, clientes(nombre, telefono, email)").eq("empresa", empresa.lower().strip()).execute()
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

# --- 🎨 SISTEMA DE GENERACIÓN DE PDF AVANZADO ---
def generar_pdf_bytes(id_presupuesto, nombre_empresa_activa):
    res = supabase.table("budgets").select("estado, fecha_envio, descuento_porcentaje, iva_porcentaje, clientes(nombre, email, telefono)").eq("id_presupuesto", id_presupuesto).execute()
    if not res.data: 
        return None
    
    pres_cabecera = res.data[0]
    estado = pres_cabecera["estado"]
    fecha_envio = pres_cabecera["fecha_envio"] or datetime.date.today().strftime("%Y-%m-%d")
    pct_descuento = float(pres_cabecera.get("descuento_porcentaje", 0) or 0)
    pct_iva = float(pres_cabecera.get("iva_porcentaje", 21) or 0)
    info_cliente = pres_cabecera.get("clientes") or {"nombre": "Cliente General", "email": "-", "telefono": "-"}
    
    articulos = consultar_detalles_de_un_presupuesto(id_presupuesto)
    
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # 🌟 COLOR PALETTE CORPORATIVO
    COLOR_PRIMARIO = colors.HexColor("#1A365D")   # Azul Oscuro Ejecutivo
    COLOR_SECUNDARIO = colors.HexColor("#2B6CB0") # Azul Claro Detalles
    COLOR_TEXTO_DARK = colors.HexColor("#2D3748") # Gris Antracita (Para legibilidad)
    COLOR_BG_TABLA = colors.HexColor("#EDF2F7")   # Gris Claro para Cabecera de Tabla
    
    # 🌟 MARCA DE AGUA CORPORATIVA SUTIL
    pdf.saveState()
    pdf.setFont("Helvetica-Bold", 38)
    pdf.setFillColorRGB(0.95, 0.95, 0.95) 
    pdf.translate(300, 420)
    pdf.rotate(45)
    pdf.drawCentredString(0, 0, "OFERTA COMERCIAL")
    pdf.restoreState()
    
    # 🌟 DISEÑO DE CABECERA AVANZADA (BLOQUE DE COLOR)
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.rect(0, 720, 612, 92, fill=True, stroke=False) # Franja superior completa
    
    # Texto dentro de la franja superior
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(40, 755, nombre_empresa_activa.upper())
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#E2E8F0"))
    pdf.drawString(40, 740, "Soluciones Profesionales y Suministros")
    
    # Etiqueta destacada del documento
    pdf.setFillColor(colors.white)
    pdf.rect(440, 735, 130, 45, fill=True, stroke=False)
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(505, 760, "PRESUPUESTO")
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(COLOR_SECUNDARIO)
    pdf.drawCentredString(505, 745, id_presupuesto)
    
    # 🌟 DATOS DE EMISIÓN Y CLIENTE (DOS COLUMNAS LIMPIAS)
    pdf.setFillColor(COLOR_TEXTO_DARK)
    
    # Columna Izquierda: Datos del Presupuesto
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(40, 680, "DATOS DEL DOCUMENTO")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(40, 665, f"Fecha de Emisión: {fecha_envio}")
    pdf.drawString(40, 652, f"Vencimiento (15d): {(datetime.datetime.strptime(fecha_envio, '%Y-%m-%d') + datetime.timedelta(days=15)).strftime('%Y-%m-%d')}")
    pdf.drawString(40, 639, f"Estado Actual: {estado.upper()}")
    
    # Columna Derecha: Datos del Cliente
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(320, 680, "DESTINATARIO / CLIENTE")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(320, 665, f"Razón Social: {info_cliente['nombre']}")
    pdf.drawString(320, 652, f"Email: {info_cliente['email']}")
    pdf.drawString(320, 639, f"Teléfono: {info_cliente['telefono']}")
    
    # Línea decorativa sutil de separación
    pdf.setStrokeColor(colors.HexColor("#CBD5E0"))
    pdf.setLineWidth(0.5)
    pdf.line(40, 620, 570, 620)
    
    # 🌟 TABLA DE ARTÍCULOS ESTILIZADA
    y_superior = 595
    pdf.setFillColor(COLOR_BG_TABLA)
    pdf.rect(40, y_superior, 530, 20, fill=True, stroke=False) # Fondo cabecera tabla
    
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
        
        # Procesamiento de texto largo en celdas
        texto_producto = f"**{art['marca_producto']}** - {art['modelo_producto']}"
        p = Paragraph(texto_producto, estilo_celda)
        ancho_disponible = 230
        lineas_parrafo = p.wrap(ancho_disponible, 100)
        alto_texto = lineas_parrafo[1]
        
        if alto_texto > 11:
            y_pos -= (alto_texto - 11)
            
        p.drawOn(pdf, 48, y_pos)
        
        # Datos numéricos
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(320, y_pos + 1, f"{art['precio_cobrado']:.2f}€")
        pdf.drawCentredString(420, y_pos + 1, str(cant_val))
        pdf.drawCentredString(525, y_pos + 1, f"{sub_art:.2f}€")
        
        # Línea de puntos divisoria sutil por cada fila
        pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
        pdf.setLineWidth(0.5)
        pdf.line(40, y_pos - 6, 570, y_pos - 6)
        
        y_pos -= 22
        
    y_inferior = y_pos + 16
    
    # Enmarcar los bordes laterales de la tabla para limpieza visual
    pdf.setStrokeColor(colors.HexColor("#CBD5E0"))
    pdf.line(40, y_superior + 20, 40, y_inferior)
    pdf.line(570, y_superior + 20, 570, y_inferior)
    pdf.line(40, y_inferior, 570, y_inferior)
    
    # 🌟 BLOQUE DE TOTALES FINALES (DESGLOSE PROFESIONAL)
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
        pdf.setFillColor(colors.HexColor("#C53030")) # Texto rojo sutil para el descuento
        pdf.drawString(360, y_bloque, f"Descuento Comercial ({pct_descuento:.0f}%):")
        pdf.drawRightString(560, y_bloque, f"-{importe_descuento:.2f} €")
        pdf.setFillColor(COLOR_TEXTO_DARK)
        
    y_bloque -= 14
    pdf.drawString(360, y_bloque, "Base Imponible:")
    pdf.drawRightString(560, y_bloque, f"{base_imponible:.2f} €")
    
    y_bloque -= 14
    pdf.drawString(360, y_bloque, f"I.V.A. Aplicado ({pct_iva:.0f}%):")
    pdf.drawRightString(560, y_bloque, f"{importe_iva:.2f} €")
    
    # Línea divisoria antes del total neto
    y_bloque -= 10
    pdf.setStrokeColor(COLOR_PRIMARIO)
    pdf.setLineWidth(1)
    pdf.line(360, y_bloque, 570, y_bloque)
    
    y_bloque -= 16
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(COLOR_PRIMARIO)
    pdf.drawString(360, y_bloque, "TOTAL NETO:")
    pdf.drawRightString(560, y_bloque, f"{total_general:.2f} €")
    
    # 🌟 SECCIÓN DE CONFORMIDAD Y FIRMA (NUEVA)
    y_firma = y_bloque - 65
    pdf.setStrokeColor(colors.HexColor("#CBD5E0"))
    pdf.setLineWidth(0.5)
    
    # Cuadro de firma del cliente
    pdf.line(40, y_firma, 200, y_firma)
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.HexColor("#718096"))
    pdf.drawString(40, y_firma - 12, "Firma de Conformidad Cliente")
    pdf.drawString(40, y_firma - 22, "Fecha: ____ / ____ / ________")
    
    # Pie de página fijo
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
            if exito: st.success(f"¡Cuenta asignada a la empresa '{empresa_reg.upper()}'!")

# --- APLICACIÓN PRINCIPAL ---
else:
    es_admin = st.session_state.usuario.lower().strip() == "admin"
    opciones_menu = ["🏠 Inicio", "📦 Productos", "👥 Clientes", "✍️ Nuevo Presupuesto", "📜 Historial"]
    
    menu = st.sidebar.radio("Navegación", opciones_menu)
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # --- PANEL DE INICIO ---
    if menu == "🏠 Inicio":
        st.title(f"🏠 Panel de Control - {st.session_state.empresa.upper()}")
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
                    nombre_c = p["clientes"]["nombre"] if p.get("clientes") else "Desconocido"
                    
                    if dias_restantes < 0:
                        st.error(f"🔴 **{p['id_presupuesto']}** | **{nombre_c}** | HA CADUCADO.")
                    elif dias_restantes <= 3:
                        st.warning(f"🚨 **¡Urgente! {p['id_presupuesto']}** | **{nombre_c}** | Quedan {dias_restantes} días.")
                    else:
                        st.info(f"✅ **{p['id_presupuesto']}** | **{nombre_c}** | Quedan {dias_restantes} días.")
                except: pass

    # --- SECCIÓN PRODUCTOS ---
    elif menu == "📦 Productos":
        st.title("📦 Gestión del Catálogo de Productos")
        tab_ver, tab_add = st.tabs(["👁️ Ver Catálogo", "➕ Añadir Manual"])
        with tab_ver:
            lista_p = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            if lista_p: st.dataframe(lista_p, use_container_width=True, hide_index=True)
        with tab_add:
            cat = st.text_input("Categoría")
            elem = st.text_input("Elemento")
            marca = st.text_input("Marca")
            precio = st.number_input("Precio Unitario (€)", min_value=0.0)
            if st.button("Guardar"):
                guardar_producto_en_bd(cat, elem, marca, precio, "Uds.", st.session_state.empresa)
                st.rerun()

    # --- SECCIÓN CLIENTES ---
    elif menu == "👥 Clientes":
        st.title("👥 Gestión de Clientes")
        n = st.text_input("Nombre")
        t = st.text_input("Teléfono (Ej: 34600112233)")
        e = st.text_input("Email")
        if st.button("Guardar Cliente"):
            guardar_cliente_en_bd(n, t, e, st.session_state.empresa)
            st.rerun()
        st.dataframe(consultar_clientes(st.session_state.empresa, st.session_state.usuario), use_container_width=True, hide_index=True)

    # --- SECCIÓN NUEVO PRESUPUESTO ---
    elif menu == "✍️ Nuevo Presupuesto":
        st.title("✍️ Generar Presupuesto")
        id_pres = obtener_siguiente_id_presupuesto(st.session_state.empresa)
        
        clientes = consultar_clientes(st.session_state.empresa, st.session_state.usuario)
        opciones_clientes = {f"{c['numero_cliente']} - {c['nombre']}": c['numero_cliente'] for c in clientes}
        
        if opciones_clientes:
            cliente_sel = st.selectbox("Selecciona el Cliente", list(opciones_clientes.keys()))
            productos = consultar_productos(st.session_state.empresa, st.session_state.usuario)
            opciones_productos = {f"{p['elemento']} ({p['marca_fabricante']}) - {p['precio_unitario']}€": p for p in productos}
            
            if opciones_productos:
                col_p, col_c = st.columns([3, 1])
                with col_p:
                    prod_sel = st.selectbox("Selecciona Producto", list(opciones_productos.keys()))
                with col_c:
                    cant = st.number_input("Cantidad", min_value=1, value=1)
                    
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
                    with col_desc:
                        descuento_global = st.number_input("Descuento Comercial Global (%)", min_value=0, max_value=100, value=0, step=1)
                    with col_iva:
                        tipo_iva = st.selectbox("Tipo de I.V.A. Aplicable", [21, 10, 4, 0], format_func=lambda x: f"General ({x}%)" if x == 21 else (f"Reducido ({x}%)" if x > 0 else "Exento (0%)"))
                    
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
                            st.success(f"¡Presupuesto {id_pres} registrado correctamente!")
                            st.session_state.items_presupuesto = []
                            st.rerun()

    # --- SECCIÓN HISTORIAL ---
    elif menu == "📜 Historial":
        st.title("📜 Historial de Presupuestos")
        historial = consultar_historial_presupuestos(st.session_state.empresa, st.session_state.usuario)
        
        datos_tabla = []
        mapeo_completo = {}
        
        for h in historial:
            cod = h["id_presupuesto"]
            cli_info = h.get("clientes") or {}
            nombre_c = cli_info.get("nombre", "Desconocido")
            
            item_tabla = {"Código": cod, "Cliente": nombre_c, "Estado": h["estado"]}
            datos_tabla.append(item_tabla)
            
            mapeo_completo[cod] = {
                "nombre": nombre_c,
                "telefono": cli_info.get("telefono", ""),
                "email": cli_info.get("email", ""),
                "desc": float(h.get("descuento_porcentaje", 0) or 0),
                "iva": float(h.get("iva_porcentaje", 21) or 0)
            }
            
        if datos_tabla:
            st.dataframe(datos_tabla, use_container_width=True, hide_index=True)
            id_sel = st.selectbox("Selecciona código:", [d["Código"] for d in datos_tabla])
            
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
            
            # 🌟 Inyección del nombre de la empresa activa para el membrete dinámico
            pdf_data = generar_pdf_bytes(id_sel, st.session_state.empresa)
            if pdf_data:
                st.download_button(label="📥 Descargar PDF Ejecutivo Diseñado", data=pdf_data, file_name=f"Presupuesto_Diseñado_{id_sel}.pdf", mime="application/pdf", use_container_width=True)
            
            col_wa, col_em = st.columns(2)
            with col_wa:
                tel = str(datos_c_sel["telefono"]).strip()
                if tel and tel != "None":
                    msg = f"Hola *{datos_c_sel['nombre']}*.\n\nTe adjunto el presupuesto *{id_sel}* por un importe total de *{total_calc:.2f}€* (I.V.A. incluido).\n\nValidez de la oferta: 15 días."
                    st.link_button("🟢 Enviar por WhatsApp", f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}", use_container_width=True)
            with col_em:
                email = str(datos_c_sel["email"]).strip()
                if email and email != "None":
                    asunto = f"Presupuesto {id_sel} - {st.session_state.empresa.upper()}"
                    cuerpo = f"Estimado/a {datos_c_sel['nombre']},\n\nLe hacemos entrega del presupuesto solicitado {id_sel} por un importe total de {total_calc:.2f}€ (I.V.A. incluido)."
                    st.link_button("🔵 Preparar Email", f"mailto:{email}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}", use_container_width=True)