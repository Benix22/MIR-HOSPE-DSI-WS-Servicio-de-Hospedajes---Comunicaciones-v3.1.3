import os
import re

def full_rewrite():
    with open('app_backup.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. New CSS
    css = """st.markdown(\"\"\"
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F5F5F7 !important; }
    .block-container { padding: 1.5rem 2rem !important; max-width: 1200px !important; }
    h1, h2, h3 { color: #111827 !important; font-weight: 600 !important; }
    label, .stMarkdown p { color: #6B7280 !important; font-size: 14px !important; }
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: #FFFFFF !important; border-radius: 12px !important; padding: 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important; border: 1px solid #E5E7EB !important; margin-bottom: 1rem !important;
    }
    .stExpander { background-color: #FFFFFF !important; border: 1px solid #E5E7EB !important; border-radius: 8px !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; border-radius: 6px !important;
    }
    .stButton>button[kind="primary"] { background-color: #0F766E !important; color: white !important; border-radius: 8px; font-weight: 600 !important; }
    .stButton>button[kind="secondary"] { color: #0F766E !important; border: 1px solid #0F766E !important; border-radius: 8px; }
    .chip-green { background-color: #D1FAE5; color: #065F46; padding: 4px 12px; border-radius: 16px; font-size: 13px; font-weight: 600; }
    .chip-orange { background-color: #FFEDD5; color: #C2410C; padding: 4px 12px; border-radius: 16px; font-size: 13px; font-weight: 600; }
    .header-layout { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid #E5E7EB; padding-bottom: 1rem; }
    </style>
    \"\"\", unsafe_allow_html=True)"""
    
    content = re.sub(r'st\.markdown\(\"\"\"\s+<style>.*?</style>\s+\"\"\", unsafe_allow_html=True\)', css, content, flags=re.DOTALL)

    # 2. Layout Structure
    # Insert session state and helper at top
    # Actually, keep them where they are but indent them.
    
    # 3. Completely replace the body from line 290
    # Let's find the split point
    header_end_marker = "# --- Authentication UI ---"
    header_part = content.split(header_end_marker)[0]
    auth_part = content.split(header_end_marker)[1].split("st.stop()")[0] + "st.stop()"
    
    body_part = """
# --- New Layout: Header & Columns ---
st.markdown('<div class="header-layout">', unsafe_allow_html=True)
col_logo, col_title, col_chip, col_out = st.columns([0.5, 4, 3, 1], vertical_alignment="center")
with col_logo:
    st.image("Logo.png", width=50)
with col_title:
    st.markdown("<h3 style='margin:0; color:#111827;'>Mirador <span style='color:#6B7280; font-weight:400; font-size:16px;'>| Registro de Huéspedes</span></h3>", unsafe_allow_html=True)

user_role = st.session_state.user.get("role", "user")
user_id = st.session_state.user.get("id")
current_tenant_id = "GLOBAL"
tenant_config = None
if user_role == "admin":
    tenants = get_db().get_tenants()
else:
    tenants = get_db().get_tenants(owner_id=user_id)
if tenants:
    current_tenant_id = tenants[0]["tenant_id"]
    tenant_config = get_db().get_tenant_config(current_tenant_id)
    hotel_name = tenant_config["nombre"] if tenant_config else "Desconocido"
else:
    hotel_name = "Sin asignar"

with col_chip:
    st.markdown(f'<div style="text-align:right;"><span class="chip-green">🟢 Conectado a {hotel_name}</span></div>', unsafe_allow_html=True)
with col_out:
    if st.button("Cerrar Sesión", type="secondary"):
        st.session_state.user = None
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

col_left, col_right = st.columns([7, 3], gap="large")

with col_left:
    st.markdown("### ⚙️ Configuración")
    if user_role == 'admin':
        with st.expander("🌐 Endpoints", expanded=False):
            env = st.selectbox("Entorno", ["Pruebas", "Producción", "Custom"])
            endpoint = "https://hospedajes.pre-ses.mir.es/hospedajes-web/ws/v1/comunicacion" if env == "Pruebas" else "https://hospedajes.ses.mir.es/hospedajes-web/ws/v1/comunicacion"
            wsdl = st.text_input("WSDL Path/URL", "schemas/comunicacion.wsdl")
        mock_mode = st.toggle("🚀 Modo Mock (Sin red)", value=get_env_bool("MODO_MOCK", "True"))
    else:
        endpoint = "https://hospedajes.ses.mir.es/hospedajes-web/ws/v1/comunicacion"
        wsdl = "schemas/comunicacion.wsdl"
        mock_mode = get_env_bool("MODO_MOCK", "False")

    with st.expander("🔐 Autenticación", expanded=True):
        user = st.text_input("Usuario (CIF/NIF)", value=tenant_config['mir_user'] if tenant_config else "")
        pwd = st.text_input("Contraseña", type="password", value=tenant_config['mir_password'] if tenant_config else "")
        cod_arrendador = st.text_input("Código Arrendador", value=tenant_config['arrendador_code'] if tenant_config else "")
        cod_est_auth = st.text_input("Código Establecimiento", value=tenant_config['establecimiento_code'] if tenant_config else "")
        app_name = st.text_input("Nombre Aplicación", value="Mirador")

    with st.container():
        st.markdown("### 📜 Certificados (SSL)")
        st.info("Por seguridad, no almacenamos tu certificado.")
        cert_file = st.file_uploader("Certificado Digital (.p12 / .pfx)", type=["p12", "pfx"])
        p12_password = st.text_input("Contraseña del Certificado", type="password")
        verify_ssl = get_env_bool("MODO_SSL", "True")
        p12_path_ui = None
        if not cert_file:
            st.markdown('<div class="chip-orange" style="margin-top: 10px;">⚠️ Obligatorio para enviar a MIR</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chip-green" style="margin-top: 10px;">✅ Certificado cargado</div>', unsafe_allow_html=True)

    # --- Session State & Helper (Inside col_left) ---
    if 'viajeros' not in st.session_state: st.session_state.viajeros = [{'nombre': '', 'apellido1': ''}]
    def add_viajero(): st.session_state.viajeros.append({'nombre': '', 'apellido1': ''})
    def remove_viajero(): 
        if len(st.session_state.viajeros) > 1: st.session_state.viajeros.pop()

    # (Skipping get_client and load_catalog defs for brevity, they should be here)
    # ...
"""
    
    # Actually, I'll just write the whole file content to avoid any more errors.
    # I'll create a clean version of app.py by combining the parts.
    pass

full_rewrite()
