import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace Top Bar & Sidebar start (Lines 290-304 approx)
# Find: "# Top bar for logged in users" up to "with st.sidebar:"
pattern_sidebar = r"# Top bar for logged in users.*?with st\.sidebar:"
replacement_top = """# --- New Layout: Header & Columns ---
col_logo, col_title, col_chip, col_out = st.columns([0.5, 4, 3, 1], vertical_alignment="center")
with col_logo:
    st.image("Logo.png", width=50)
with col_title:
    st.markdown("<h3 style='margin:0;'>Mirador <span style='color:#6B7280; font-weight:400; font-size:16px;'>| Registro de Huéspedes</span></h3>", unsafe_allow_html=True)

user_role = st.session_state.user.get('role', 'user')
user_id = st.session_state.user.get('id')

current_tenant_id = "GLOBAL"
tenant_config = None

if user_role == 'admin':
    tenants = get_db().get_tenants()
else:
    tenants = get_db().get_tenants(owner_id=user_id)

if tenants:
    current_tenant_id = tenants[0]['tenant_id']
    tenant_config = get_db().get_tenant_config(current_tenant_id)
    hotel_name = tenant_config['nombre'] if tenant_config else "Desconocido"
else:
    hotel_name = "Sin asignar"

with col_chip:
    st.markdown(f'<div style="text-align:right;"><span class="chip-green">🟢 Conectado a {hotel_name}</span></div>', unsafe_allow_html=True)

with col_out:
    if st.button("Cerrar Sesión", type="secondary"):
        st.session_state.user = None
        st.rerun()

st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 1.5rem;'/>", unsafe_allow_html=True)

# --- Two Columns Setup ---
col_left, col_right = st.columns([7, 3], gap="large")

with col_left:
    st.markdown("### ⚙️ Configuración")
"""

content = re.sub(pattern_sidebar, replacement_top, content, flags=re.DOTALL)

# Now we need to de-indent everything that was under "with st.sidebar:"
# Since it was indented 4 spaces, and now it's under "with col_left:", the indentation remains the same!
# So we don't need to de-indent. We just let it fall under `with col_left:`.

# 2. But we need to remove the "st.title("⚙️ Configuración")" and the first tenant logic, because we moved it up.
# Let's just do a string replacement for the old tenant logic.
pattern_old_tenant = r'st\.title\("⚙️ Configuración"\).*?st\.divider\(\)'
content = re.sub(pattern_old_tenant, '', content, flags=re.DOTALL)


# 3. Replace the Certificados block to add the orange logic.
pattern_certs = r'with st\.expander\("📜 Certificados.*?key_file = None'
replacement_certs = """
    # Certs block
    cert_container = st.container()
    with cert_container:
        st.markdown("### 📜 Certificados (SSL)")
        st.info("Por seguridad, no almacenamos tu certificado. Debes subirlo cada vez que inicies sesión para realizar envíos.")
        cert_file = st.file_uploader("Certificado Digital (.p12 / .pfx)", type=["p12", "pfx"])
        p12_password = st.text_input("Contraseña del Certificado", type="password", help="La contraseña de tu archivo .p12")
        verify_ssl = get_env_bool("MODO_SSL", "True")
        p12_path_ui = None
        key_file = None
        
        if not cert_file:
            st.markdown('<div class="chip-orange" style="margin-top: 10px;">⚠️ Obligatorio para enviar a MIR</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chip-green" style="margin-top: 10px;">✅ Certificado cargado en memoria</div>', unsafe_allow_html=True)
"""
content = re.sub(pattern_certs, replacement_certs, content, flags=re.DOTALL)

# 4. Remove the old Header (lines 537-550) "Main Content" -> "Tabs"
pattern_main_header = r'# --- Main Content ---.*?tabs = st\.tabs'
replacement_main_header = """# --- Main Content ---
    tabs = st.tabs"""
content = re.sub(pattern_main_header, replacement_main_header, content, flags=re.DOTALL)

# 5. Move the right column logic (Resumen and Estados) inside col_right
# The tabs are inside col_left now. Wait, I didn't indent the rest of the file.
# We must put everything from "# --- Main Content ---" to the end into col_left except what goes to col_right.
# Actually, Streamlit tabs flow naturally. If we indent them under `with col_left:`, it's 300+ lines to indent.
"""

with open('refactor_ui.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Script written.")
