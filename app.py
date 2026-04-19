import streamlit as st
import pandas as pd
from src.core.hospedajes_client import HospedajesClient
import os
from datetime import datetime
from dotenv import load_dotenv
from src.core.iso_countries import get_iso_countries

# --- Load Environment Variables ---
load_dotenv(override=True)

# Streamlit secrets integration
if os.path.exists("secrets.toml"):
    try:
        import toml
        secrets = toml.load("secrets.toml")
        for k, v in secrets.items():
            os.environ[k] = str(v)
    except Exception as e:
        print(f"Error loading secrets.toml: {e}")

# Optional DB Manager
try:
    from src.core import db_manager
    import importlib
    importlib.reload(db_manager)
    from src.core.db_manager import get_db
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    print(f"Database not available: {e}")

try:
    from src.core import auth
except ImportError:
    auth = None

# --- Session State ---
if 'user' not in st.session_state: st.session_state.user = None
if 'viajeros' not in st.session_state: st.session_state.viajeros = [{'nombre': '', 'apellido1': ''}]
if 'client' not in st.session_state: st.session_state.client = None

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*PKCS#12 bundle could not be parsed as DER.*")

def get_env_bool(key, default="True"):
    val = str(os.getenv(key, default)).lower().strip()
    return val in ("true", "1", "t", "y", "yes")

def add_viajero(): st.session_state.viajeros.append({'nombre': '', 'apellido1': ''})
def remove_viajero():
    if len(st.session_state.viajeros) > 1: st.session_state.viajeros.pop()

# --- Page Configuration ---
st.set_page_config(
    page_title="Mirador - Plataforma de Registro de Huéspedes",
    page_icon="Logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Custom Styles (Professional Premium Theme) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F5F5F7 !important; }
    .block-container { padding: 1.5rem 2rem !important; max-width: 1240px !important; }
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
    .stButton>button[kind="primary"] { background-color: #0F766E !important; color: white !important; border-radius: 8px; font-weight: 600 !important; height: 3.2em !important; border: none !important; }
    .stButton>button[kind="secondary"] { color: #0F766E !important; border: 1px solid #0F766E !important; border-radius: 8px; background-color: #FFFFFF !important; }
    .chip-green { background-color: #D1FAE5; color: #065F46; padding: 4px 12px; border-radius: 16px; font-size: 13px; font-weight: 600; display: inline-block; }
    .chip-orange { background-color: #FFEDD5; color: #C2410C; padding: 4px 12px; border-radius: 16px; font-size: 13px; font-weight: 600; display: inline-block; }
    .header-layout { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid #E5E7EB; padding-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- Init Database ---
if DB_AVAILABLE:
    try: get_db().init_db()
    except Exception as e: st.error(f"Error conectando a BBDD: {e}")

# --- Authentication UI ---
if not st.session_state.user:
    st.markdown("<h1 style='text-align: center;'>Bienvenido a Mirador</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>Plataforma de Registro de Huéspedes (RD 933/2021)</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab_login:
            with st.form("login_form"):
                log_email = st.text_input("Correo Electrónico")
                log_pass = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar", type="primary"):
                    user_data = get_db().get_user_by_email(log_email)
                    if user_data and auth and auth.verify_password(user_data['password_hash'], log_pass):
                        st.session_state.user = user_data
                        st.rerun()
                    else: st.error("Credenciales incorrectas")
        with tab_register:
            with st.form("register_form"):
                reg_email = st.text_input("Correo Electrónico *")
                reg_pass = st.text_input("Contraseña *", type="password")
                reg_nombre = st.text_input("Nombre Establecimiento *")
                reg_mir_user = st.text_input("Usuario MIR (CIF/NIF) *")
                reg_mir_pass = st.text_input("Contraseña MIR *", type="password")
                reg_arr = st.text_input("Código Arrendador *")
                reg_est = st.text_input("Código Establecimiento *")
                if st.form_submit_button("Crear Cuenta", type="primary"):
                    uid = get_db().create_user(reg_email, auth.hash_password(reg_pass), 'user', True)
                    import re
                    slug = re.sub(r'[^a-z0-9]', '', reg_nombre.lower())[:15] + f"_{uid}"
                    get_db().save_tenant({'tenant_id': slug, 'owner_id': uid, 'nombre': reg_nombre, 'mir_user': reg_mir_user, 'mir_password': reg_mir_pass, 'arrendador_code': reg_arr, 'establecimiento_code': reg_est})
                    st.success("Cuenta creada exitosamente.")
    st.stop()

# --- Dashboard Logic ---
user_role = st.session_state.user.get('role', 'user')
user_id = st.session_state.user.get('id')
tenants = get_db().get_tenants() if user_role == 'admin' else get_db().get_tenants(owner_id=user_id)

if tenants:
    current_tenant_id = tenants[0]['tenant_id']
    tenant_config = get_db().get_tenant_config(current_tenant_id)
    hotel_name = tenant_config['nombre']
else:
    hotel_name = "Sin asignar"
    tenant_config = None

# Header
st.markdown('<div class="header-layout">', unsafe_allow_html=True)
h_logo, h_title, h_chip, h_out = st.columns([0.5, 4, 3, 1], vertical_alignment="center")
with h_logo: st.image("Logo.png", width=50)
with h_title: st.markdown(f"### Mirador <span style='color:#6B7280; font-weight:400; font-size:16px;'>| {hotel_name}</span>", unsafe_allow_html=True)
with h_chip: st.markdown(f'<div style="text-align:right;"><span class="chip-green">🟢 Conectado</span></div>', unsafe_allow_html=True)
with h_out: 
    if st.button("Cerrar Sesión", type="secondary"): 
        st.session_state.user = None
        st.rerun()

# --- Functions (Client & Catalog) ---
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

def get_client():
    c_path = os.getenv("MIR_CERT_PATH", "")
    k_path = os.getenv("MIR_KEY_PATH", "")
    p12_pass = p12_password
    
    if cert_file:
        if not os.path.exists("temp_certs"): os.makedirs("temp_certs")
        file_bytes = cert_file.getbuffer()
        try:
            p_key, cert, chain = pkcs12.load_key_and_certificates(file_bytes, p12_pass.encode())
            c_path = os.path.join("temp_certs", "combined.pem")
            with open(c_path, "wb") as f:
                f.write(p_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
                f.write(cert.public_bytes(serialization.Encoding.PEM))
                if chain: [f.write(c.public_bytes(serialization.Encoding.PEM)) for c in chain]
        except Exception as e:
            st.error(f"Error cert: {e}")
            return None

    config_hash = f"{wsdl}-{endpoint}-{user_mir}-{pwd_mir}-{c_path}-{verify_ssl}-{mock_mode}"
    if st.session_state.client and st.session_state.get('config_hash') == config_hash:
        return st.session_state.client

    client = HospedajesClient(wsdl_path=wsdl, endpoint=endpoint, username=user_mir, password=pwd_mir, cert_path=c_path, verify_ssl=verify_ssl, mock_mode=mock_mode)
    st.session_state.client = client
    st.session_state.config_hash = config_hash
    return client

@st.cache_data(ttl=3600, show_spinner=False)
def load_catalog(tipo, defaults, tenant_id="GLOBAL"):
    mapping = {k: k for k in defaults}
    if DB_AVAILABLE:
        try:
            db_data = get_db().get_catalogo(tipo, tenant_id=tenant_id)
            if db_data: mapping = {item['codigo']: f"{item['codigo']} - {item['descripcion']}" for item in db_data}
        except: pass
    return mapping

# Layout Columns
col_left, col_right = st.columns([7, 3], gap="large")

with col_left:
    # 1. Configuración
    with st.expander("⚙️ Configuración del Sistema", expanded=False):
        if user_role == 'admin':
            env = st.selectbox("Entorno", ["Pruebas", "Producción"])
            endpoint = "https://hospedajes.pre-ses.mir.es/hospedajes-web/ws/v1/comunicacion" if env == "Pruebas" else "https://hospedajes.ses.mir.es/hospedajes-web/ws/v1/comunicacion"
            wsdl = st.text_input("WSDL", "schemas/comunicacion.wsdl")
            mock_mode = st.toggle("Modo Mock", value=get_env_bool("MODO_MOCK", "True"))
        else:
            endpoint = "https://hospedajes.ses.mir.es/hospedajes-web/ws/v1/comunicacion"
            wsdl = "schemas/comunicacion.wsdl"
            mock_mode = get_env_bool("MODO_MOCK", "False")
        
        user_mir = st.text_input("Usuario (CIF/NIF)", value=tenant_config['mir_user'] if tenant_config else "")
        pwd_mir = st.text_input("Contraseña MIR", type="password", value=tenant_config['mir_password'] if tenant_config else "")
        cod_arr = st.text_input("Código Arrendador", value=tenant_config['arrendador_code'] if tenant_config else "")
        cod_est = st.text_input("Código Establecimiento", value=tenant_config['establecimiento_code'] if tenant_config else "")
        app_name = st.text_input("Nombre Aplicación", value="Mirador")
        verify_ssl = get_env_bool("MODO_SSL", "True")

    # 2. Certificados
    with st.container():
        st.markdown("### 📜 Certificados (SSL)")
        st.info("Sube tu certificado .p12 cada vez que inicies sesión para realizar envíos.")
        cert_file = st.file_uploader("Certificado Digital (.p12 / .pfx)", type=["p12", "pfx"])
        p12_password = st.text_input("Contraseña del Certificado", type="password")
        if not cert_file: st.markdown('<span class="chip-orange">⚠️ Obligatorio para enviar a MIR</span>', unsafe_allow_html=True)
        else: st.markdown('<span class="chip-green">✅ Certificado cargado en memoria</span>', unsafe_allow_html=True)

    # 3. Tabs
    tabs = st.tabs(["📤 Alta", "🔍 Consultas", "❌ Anulaciones", "📚 Catálogo"] if user_role == 'admin' else ["📤 Alta", "🔍 Consultas", "❌ Anulaciones"])

    with tabs[0]: # ALTA
        st.markdown('''<div style="display: flex; justify-content: space-between; margin: 20px 0; font-size: 14px;">
            <span style="color: #0F766E; font-weight: 600;">1. Datos generales ➔</span>
            <span style="color: #6B7280;">2. Viajeros ➔</span>
            <span style="color: #6B7280;">3. Envío a MIR</span>
        </div>''', unsafe_allow_html=True)
        
        c_t1, c_t2, c_t3 = st.columns([2, 1, 1])
        tipo_com = c_t1.selectbox("Tipo de Comunicación", ["PV - Partes de Viajeros", "RH - Reservas de Hospedaje", "AV - Alquiler de Vehículos", "RV - Reservas de Vehículos"])
        c_t2.markdown(f"<div style='padding-top:28px; text-align:right;'>Viajeros: <b>{len(st.session_state.viajeros)}</b></div>", unsafe_allow_html=True)
        with c_t3:
            st.write("")
            b1, b2 = st.columns(2)
            b1.button("➖", on_click=remove_viajero)
            b2.button("➕", on_click=add_viajero)

        with st.form("main_data_form"):
            st.subheader("📋 Datos del Contrato")
            cc1, cc2 = st.columns(2)
            ref = cc1.text_input("🔗 Referencia del Contrato", f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            f_cont = cc1.date_input("📅 Fecha Contrato", datetime.now())
            num_hab = cc1.number_input("🏨 Número de Habitaciones", min_value=1, value=1)
            f_ent = cc2.datetime_input("🛫 Fecha Entrada/Inicio", datetime.now())
            f_sal = cc2.datetime_input("🛬 Fecha Salida/Fin", datetime.now())
            tiene_internet = cc2.checkbox("🌐 ¿Tiene acceso a Internet?", value=False)
            
            st.divider()
            st.write("💳 Datos de Pago")
            p_col1, p_col2 = st.columns([1, 2])
            cat_pago = load_catalog("TIPO_PAGO", ["EF", "TC", "TR", "OT"], tenant_id="GLOBAL")
            tipo_pago = p_col1.selectbox("💰 Tipo de Pago", options=list(cat_pago.keys()), format_func=lambda x: cat_pago[x])
            f_pago = p_col1.date_input("📆 Fecha de Pago", datetime.now())
            p_caducidad = p_col1.text_input("💳 Caducidad Tarjeta", value="", placeholder="MM/AAAA")
            medio_pago = p_col2.text_input("🆔 Identificación del Medio de Pago", value="")
            p_titular = p_col2.text_input("👤 Nombre Completo del Titular", "")
            
            st.form_submit_button("Guardar Datos Generales")

        with st.form("travelers_form"):
            st.subheader("👤 Datos de los Viajeros")
            lista_personas_data = []
            for i, viajero in enumerate(st.session_state.viajeros):
                with st.expander(f"👤 Persona {i+1}: {viajero.get('nombre', '')} {viajero.get('apellido1', '')}", expanded=(i==len(st.session_state.viajeros)-1)):
                    v1, v2 = st.columns([2, 1])
                    with v1:
                        p_nom = st.text_input(f"Nombre P{i+1}", viajero.get('nombre', ''), key=f"nom_{i}")
                        p_ap1 = st.text_input(f"Primer Apellido P{i+1}", viajero.get('apellido1', ''), key=f"ap1_{i}")
                        
                        label_ap2 = f"Segundo Apellido P{i+1}"
                        is_nif = st.session_state.get(f"tdoc_{i}") == "NIF"
                        if is_nif: label_ap2 += " ⚠️ (Obligatorio para NIF)"
                        p_ap2 = st.text_input(label_ap2, "", key=f"ap2_{i}")
                        
                        is_nie = st.session_state.get(f"tdoc_{i}") == "NIE"
                        label_soporte = f"Número Soporte P{i+1}"
                        if is_nif or is_nie: label_soporte += " ⚠️ (Obligatorio para NIF/NIE)"
                        p_soporte = st.text_input(label_soporte, "", key=f"soporte_{i}")
                    
                    with v2:
                        cat_tdoc = load_catalog("TIPO_DOCUMENTO", ["NIF", "NIE", "PAS", "ID"], tenant_id="GLOBAL")
                        p_tdoc = st.selectbox(f"Tipo Doc P{i+1}", options=list(cat_tdoc.keys()), format_func=lambda x: cat_tdoc[x], key=f"tdoc_{i}")
                        p_doc = st.text_input(f"Documento P{i+1}", "", key=f"doc_{i}")
                        cat_sexo = load_catalog("SEXO", ["M", "F", "X"], tenant_id="GLOBAL")
                        p_sexo = st.selectbox(f"Sexo P{i+1}", options=list(cat_sexo.keys()), format_func=lambda x: cat_sexo[x], key=f"sexo_{i}")
                        p_fnac = st.date_input(f"Fecha Nacimiento P{i+1}", datetime(1980, 1, 1), key=f"fnac_{i}")
                    
                    v3, v4 = st.columns(2)
                    with v3:
                        countries = get_iso_countries()
                        p_nac = st.selectbox(f"Nacionalidad P{i+1}", options=list(countries.keys()), index=list(countries.keys()).index("ESP") if "ESP" in countries else 0, format_func=lambda x: f"{x} - {countries[x]}", key=f"nac_{i}")
                    with v4:
                        cat_parentesco = load_catalog("TIPO_PARENTESCO", ["", "P", "M", "A", "H", "O"], tenant_id="GLOBAL")
                        p_parentesco = st.selectbox(f"Parentesco P{i+1}", options=list(cat_parentesco.keys()), format_func=lambda x: cat_parentesco[x] if x else "Ninguno", key=f"par_{i}")
                    
                    st.write(f"📞 Contacto P{i+1}")
                    c1, c2 = st.columns(2)
                    p_tel = c1.text_input(f"Teléfono P{i+1}", "", key=f"tel_{i}")
                    p_email = c2.text_input(f"Correo P{i+1}", "", key=f"email_{i}")
                    
                    st.write(f"🏠 Dirección P{i+1}")
                    d1, d2, d3, d4 = st.columns([2, 2, 1, 1])
                    d_dir = d1.text_input(f"Dirección P{i+1}", "", key=f"dir_{i}")
                    cat_mun = load_catalog("MUNICIPIO", ["28079"], tenant_id="GLOBAL")
                    d_mun = st.selectbox(f"Municipio P{i+1}", options=list(cat_mun.keys()), format_func=lambda x: cat_mun[x] if x in cat_mun else x, key=f"mun_{i}")
                    d_cp = d3.text_input(f"CP P{i+1}", "", key=f"cp_{i}")
                    d_pais = d4.selectbox(f"País P{i+1}", options=list(countries.keys()), index=list(countries.keys()).index("ESP"), format_func=lambda x: f"{x} - {countries[x]}", key=f"dpais_{i}")

                    lista_personas_data.append({
                        'rol': 'VI', 'nombre': p_nom, 'apellido1': p_ap1, 'apellido2': p_ap2,
                        'tipoDocumento': p_tdoc, 'numeroDocumento': p_doc, 'soporteDocumento': p_soporte,
                        'fechaNacimiento': p_fnac.strftime('%Y-%m-%d'), 'nacionalidad': p_nac, 'sexo': p_sexo,
                        'telefono': p_tel, 'correo': p_email, 'parentesco': p_parentesco,
                        'direccion': {'direccion': d_dir, 'codigoMunicipio': d_mun, 'codigoPostal': d_cp, 'pais': d_pais}
                    })

            if st.form_submit_button("🚀 ENVIAR COMUNICACIÓN A MIR", type="primary", use_container_width=True):
                client = get_client()
                if client:
                    data = [{'referencia': ref, 'fechaContrato': f_cont.strftime('%Y-%m-%d'), 'fechaEntrada': f_ent.strftime('%Y-%m-%dT%H:%M:%S'), 'fechaSalida': f_sal.strftime('%Y-%m-%dT%H:%M:%S'), 'numPersonas': len(lista_personas_data), 'numHabitaciones': num_hab, 'internet': tiene_internet, 'pago': {'tipoPago': tipo_pago, 'medioPago': medio_pago, 'fechaPago': f_pago.strftime('%Y-%m-%d'), 'titular': p_titular, 'caducidadTarjeta': p_caducidad}, 'personas': lista_personas_data}]
                    xml = client.generate_alta_parte_hospedaje_xml(cod_est, data)
                    res = client.comunicacion(cod_arr, app_name, 'A', tipo_com[:2], xml)
                    st.toast("🚀 Comunicación enviada", icon="✅")
                    st.json(res)
                    with st.expander("Ver XML"): st.code(xml.decode(), language='xml')

    with tabs[1]: # CONSULTAS
        st.header("🔍 Consultas")
        op = st.radio("Buscar por:", ["Lote", "Comunicación"])
        v = st.text_input("Valor")
        if st.button("Consultar"):
            client = get_client()
            res = client.consulta_lote([v]) if op == "Lote" else client.consulta_comunicacion([v])
            st.json(res)

    with tabs[2]: # ANULACIONES
        st.header("❌ Anulaciones")
        l = st.text_input("Lote a anular")
        if st.button("Anular", type="primary") and l:
            st.json(get_client().anulacion_lote(l))

    if user_role == 'admin':
        with tabs[3]: # CATALOGO
            st.header("📚 Catálogo")
            c_sel = st.selectbox("Catálogo", ["TIPO_DOCUMENTO", "TIPO_PAGO", "SEXO", "MUNICIPIO", "PAIS", "TIPO_PARENTESCO"])
            if st.button("Sincronizar"):
                res = get_client().get_catalogo(c_sel)
                if 'catalogo' in res:
                    get_db().save_catalogo(c_sel, res['catalogo'], "GLOBAL")
                    st.success("Sincronizado")
            st.dataframe(pd.DataFrame(get_db().get_catalogo(c_sel, "GLOBAL")))

with col_right:
    with st.container():
        st.markdown("### 📋 Resumen")
        st.markdown(f"**Hotel:** {hotel_name}")
        st.markdown(f"**Viajeros:** {len(st.session_state.viajeros)}")
        st.markdown(f"**Certificado:** {'✅ OK' if cert_file else '❌ Pendiente'}")
        if st.button("💾 Guardar Datos", type="secondary", use_container_width=True): st.toast("Guardado")
    with st.container():
        st.markdown("### 🚦 Estados")
        mir_c = "chip-green" if not mock_mode else "chip-orange"
        st.markdown(f'<span class="{mir_c}">{"MIR Conectado" if not mock_mode else "Modo Mock"}</span>', unsafe_allow_html=True)
        cert_c = "chip-green" if cert_file else "chip-orange"
        st.markdown(f'<div style="margin-top:10px;"><span class="{cert_c}">{"Certificado OK" if cert_file else "Pendiente"}</span></div>', unsafe_allow_html=True)

st.divider()
st.caption("Mirador 2026 - v1.5 Professional")
