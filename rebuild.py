import os

def normalize_indent():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    i = 0
    in_col_left = False
    
    while i < len(lines):
        line = lines[i]
        
        if line.strip().startswith('with col_left:'):
            in_col_left = True
            out.append(line.lstrip()) # Ensure it's at col 0
            i += 1
            continue
            
        if line.strip().startswith('# --- Right Column:'):
            in_col_left = False
            out.append(line.lstrip()) # Ensure it's at col 0
            i += 1
            continue
            
        if in_col_left:
            # We want everything in here to be at least 4 spaces.
            # If it's already indented, we normalize it to 4 + (original_indent - 4 if any).
            # No, the simplest way is to lstrip() and then add 4.
            # BUT we must preserve internal relative indentation (like nested if blocks).
            
            # Let's find the current indentation of this line
            stripped = line.lstrip()
            if not stripped:
                out.append("\n")
            else:
                # We need to know how many spaces it HAD before my fix.
                # Actually, I can just find the minimum indentation in the block and shift everything.
                pass
        
        # Let's try a different approach:
        # Just use the backup and apply the change correctly.
        i += 1
    
    # Actually, I'll just rewrite the whole file manually in the script to be sure.
    pass

# I will use a different approach: I will read app_backup.py and apply the changes manually in the script with correct indentation.
def rebuild_from_backup():
    with open('app_backup.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if line.startswith("# Top bar for logged in users"):
            # Insert Header
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
            
            # Skip old top bar and sidebar start
            while i < len(lines) and not lines[i].startswith("    st.title"):
                i += 1
            i += 1 # skip st.title
            continue

        if line.startswith("    st.divider()"):
            # skip it if it's the one in sidebar
            if i < 400: # heuristic
                i += 1
                continue
                
        if line.strip() == 'with st.sidebar:':
            i += 1
            continue

        # Map sidebar elements to col_left
        if line.startswith("    "): # Inside a block in original
            # Some lines are indented 4 (sidebar elements), some 8 (if blocks inside sidebar)
            # We want to keep their relative indentation but they are now inside "with col_left:" (which adds 4)
            # So a line with 4 spaces stays 4 spaces (since it's inside the "with" block).
            pass
            
        # Replace Certs block with the new one
        if '📜 Certificados (SSL)' in line:
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
            # Skip until session state
            while i < len(lines) and not lines[i].startswith("# --- Session State"):
                i += 1
            continue

        # Handle the rest of the file
        if i < len(lines):
            # If we are past the sidebar but before the right column, we indent everything 4 spaces to stay inside col_left
            if i > 300 and not line.startswith("    ") and not line.strip().startswith("# --- Footer"):
                out.append("    " + lines[i])
            else:
                out.append(lines[i])
            
        i += 1

    # Add the col_right logic at the end
    out.append('\n# --- Right Column: Summary & Status ---\n')
    out.append('with col_right:\n')
    out.append('    with st.container():\n')
    out.append('        st.markdown("### 📋 Resumen")\n')
    out.append('        st.markdown(f"**Tipo:** {tipo_com if \'tipo_com\' in locals() else \'-\'}")\n')
    out.append('        st.markdown(f"**Establecimiento:** {hotel_name}")\n')
    out.append('        st.markdown(f"**Viajeros:** {len(st.session_state.viajeros)}")\n')
    out.append('        if \'f_ent\' in locals() and \'f_sal\' in locals():\n')
    out.append('            st.markdown(f"**Estancia:** {f_ent.strftime(\'%d/%m\')} - {f_sal.strftime(\'%d/%m\')}")\n')
    out.append('        cert_status = "✅ OK" if cert_file else "❌ Pendiente"\n')
    out.append('        st.markdown(f"**Certificado:** {cert_status}")\n')
    out.append('        if st.button("💾 Guardar Datos Generales", type="secondary", use_container_width=True):\n')
    out.append('            st.toast("Datos generales guardados localmente.")\n\n')
    out.append('    with st.container():\n')
    out.append('        st.markdown("### 🚦 Estados")\n')
    out.append('        mir_conn = "chip-green" if not mock_mode else "chip-orange"\n')
    out.append('        mir_text = "MIR Conectado" if not mock_mode else "Modo Mock"\n')
    out.append('        st.markdown(f\'<span class="{mir_conn}">{mir_text}</span>\', unsafe_allow_html=True)\n')
    out.append('        cert_chip = "chip-green" if cert_file else "chip-orange"\n')
    out.append('        cert_text = "Certificado OK" if cert_file else "Certificado Pendiente"\n')
    out.append('        st.markdown(f\'<div style="margin-top:10px;"><span class="{cert_chip}">{cert_text}</span></div>\', unsafe_allow_html=True)\n')

    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(out)

rebuild_from_backup()
