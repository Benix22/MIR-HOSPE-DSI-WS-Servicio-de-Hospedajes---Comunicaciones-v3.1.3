import os

def rewrite_app():
    with open('app_backup.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    i = 0
    in_sidebar = False
    in_main_content = False
    
    while i < len(lines):
        line = lines[i]
        
        # 1. Replace the old header (Lines 290)
        if line.startswith("# Top bar for logged in users"):
            # Insert the new Header
            out.append("# --- New Layout: Header & Columns ---\n")
            out.append('st.markdown(\'<div class="header-layout">\', unsafe_allow_html=True)\n')
            out.append('col_logo, col_title, col_chip, col_out = st.columns([0.5, 4, 3, 1], vertical_alignment="center")\n')
            out.append('with col_logo:\n')
            out.append('    st.image("Logo.png", width=50)\n')
            out.append('with col_title:\n')
            out.append('    st.markdown("<h3 style=\'margin:0; color:#111827;\'>Mirador <span style=\'color:#6B7280; font-weight:400; font-size:16px;\'>| Registro de Huéspedes</span></h3>", unsafe_allow_html=True)\n')
            out.append('\n')
            out.append('user_role = st.session_state.user.get("role", "user")\n')
            out.append('user_id = st.session_state.user.get("id")\n')
            out.append('current_tenant_id = "GLOBAL"\n')
            out.append('tenant_config = None\n')
            out.append('if user_role == "admin":\n')
            out.append('    tenants = get_db().get_tenants()\n')
            out.append('else:\n')
            out.append('    tenants = get_db().get_tenants(owner_id=user_id)\n')
            out.append('if tenants:\n')
            out.append('    current_tenant_id = tenants[0]["tenant_id"]\n')
            out.append('    tenant_config = get_db().get_tenant_config(current_tenant_id)\n')
            out.append('    hotel_name = tenant_config["nombre"] if tenant_config else "Desconocido"\n')
            out.append('else:\n')
            out.append('    hotel_name = "Sin asignar"\n')
            out.append('\n')
            out.append('with col_chip:\n')
            out.append('    st.markdown(f\'<div style="text-align:right;"><span class="chip-green">🟢 Conectado a {hotel_name}</span></div>\', unsafe_allow_html=True)\n')
            out.append('\n')
            out.append('with col_out:\n')
            out.append('    if st.button("Cerrar Sesión", type="secondary"):\n')
            out.append('        st.session_state.user = None\n')
            out.append('        st.rerun()\n')
            out.append('st.markdown("</div>", unsafe_allow_html=True)\n\n')
            
            out.append('# --- Two Columns Setup ---\n')
            out.append('col_left, col_right = st.columns([7, 3], gap="large")\n\n')
            out.append('with col_left:\n')
            out.append('    st.markdown("### ⚙️ Configuración")\n')
            
            # Skip old top bar and sidebar init
            while i < len(lines) and not lines[i].startswith("    # Hide global settings"):
                i += 1
            continue
            
        # 2. Modify Sidebar Config (which is now in col_left)
        if line.startswith("    # Hide global settings"):
            # We are inside the old sidebar. We keep the code but we need to remove the 4-space indent
            # because we want it under `with col_left:` which is also 4 spaces.
            # So indentation stays the same!
            pass

        # 3. Modify Certificados Expander
        if line.strip().startswith('with st.expander("📜 Certificados'):
            out.append('    # Certs block\n')
            out.append('    with st.container():\n')
            out.append('        st.markdown("### 📜 Certificados (SSL)")\n')
            out.append('        st.info("Por seguridad, no almacenamos tu certificado. Debes subirlo cada vez que inicies sesión para realizar envíos.")\n')
            out.append('        cert_file = st.file_uploader("Certificado Digital (.p12 / .pfx)", type=["p12", "pfx"])\n')
            out.append('        p12_password = st.text_input("Contraseña del Certificado", type="password", help="La contraseña de tu archivo .p12")\n')
            out.append('        verify_ssl = get_env_bool("MODO_SSL", "True")\n')
            out.append('        p12_path_ui = None\n')
            out.append('        key_file = None\n')
            out.append('        if not cert_file:\n')
            out.append('            st.markdown(\'<div class="chip-orange" style="margin-top: 10px;">⚠️ Obligatorio para enviar a MIR</div>\', unsafe_allow_html=True)\n')
            out.append('        else:\n')
            out.append('            st.markdown(\'<div class="chip-green" style="margin-top: 10px;">✅ Certificado cargado en memoria</div>\', unsafe_allow_html=True)\n')
            
            # Skip old certs block
            while i < len(lines) and not lines[i].startswith("# --- Session State"):
                i += 1
            continue

        # 4. Remove old Main Content header
        if line.startswith("# --- Main Content ---"):
            # Skip until tabs = st.tabs
            while i < len(lines) and not lines[i].startswith("if st.session_state.user.get('role') == 'admin':"):
                i += 1
            # Now we must indent everything from here to the end by 4 spaces!
            out.append("    # --- Main Content ---\n")
            in_main_content = True
            
        if in_main_content and line.startswith("st.divider()"):
            # Footer doesn't need to be in col_left
            in_main_content = False
            
        if in_main_content:
            if line.strip() == "":
                out.append("\n")
            else:
                out.append("    " + line)
        else:
            out.append(line)
            
        i += 1

    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(out)

rewrite_app()
print("app.py rewritten successfully.")
