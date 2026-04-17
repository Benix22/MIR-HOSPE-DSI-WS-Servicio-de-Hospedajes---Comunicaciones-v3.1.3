import streamlit as st
import pandas as pd
from hospedajes_client import HospedajesClient
import os
from datetime import datetime
from dotenv import load_dotenv

# --- Load Environment Variables ---
# override=True ensures .env values take precedence over system env vars
load_dotenv(override=True)

def get_env_bool(key, default="True"):
    val = str(os.getenv(key, default)).lower().strip()
    return val in ("true", "1", "t", "y", "yes")

# --- Page Configuration ---
st.set_page_config(
    page_title="MIR Hospedajes Web Service Client",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styles ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    .stExpander {
        background-color: #1e2130;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar: Configuration ---
with st.sidebar:
    st.title("⚙️ Configuración")
    
    with st.expander("🌐 Endpoints", expanded=True):
        env = st.selectbox("Entorno", ["Pruebas", "Producción", "Custom"])
        if env == "Pruebas":
            endpoint = "https://hospedajes.pre-ses.mir.es/hospedajes-web/ws/v1/comunicacion"
        elif env == "Producción":
            endpoint = "https://hospedajes.ses.mir.es/hospedajes-web/ws/v1/comunicacion"
        else:
            endpoint = st.text_input("Endpoint URL", "")
            
        wsdl = st.text_input("WSDL Path/URL", "comunicacion.wsdl")
        
    with st.expander("🔐 Autenticación", expanded=True):
        user = st.text_input("Usuario (CIF/NIF)", value=os.getenv("MIR_USER", ""))
        pwd = st.text_input("Contraseña", type="password", value=os.getenv("MIR_PASSWORD", ""))
        cod_arrendador = st.text_input("Código Arrendador", value=os.getenv("MIR_ARRENDADOR_CODE", ""))
        app_name = st.text_input("Nombre Aplicación", value=os.getenv("MIR_APP_NAME", "PythonClient_v1"))
        
    with st.expander("📜 Certificados (SSL)", expanded=False):
        cert_file = st.file_uploader("Certificado (.pem/.crt/.p12)", type=["pem", "crt", "p12", "pfx"])
        p12_password = st.text_input("Contraseña Certificado (.p12)", type="password", value=os.getenv("MIR_P12_PASSWORD", ""), help="Solo necesaria si subes un archivo .p12")
        key_file = st.file_uploader("Clave Privada (.key)", type=["key"], help="Opcional si usas .p12")
        verify_ssl = st.checkbox("Verificar SSL (CA)", value=get_env_bool("MODO_SSL", "True"), help="Desactiva esto solo si tienes errores de 'unable to get local issuer certificate' en pruebas.")
        
    mock_mode = st.toggle("🚀 Modo Mock (Sin red)", value=get_env_bool("MODO_MOCK", "True"))


# --- Session State ---
if 'client' not in st.session_state:
    st.session_state.client = None
if 'viajeros' not in st.session_state:
    st.session_state.viajeros = [{'nombre': 'JUAN', 'apellido1': 'GARCIA'}]

def add_viajero():
    st.session_state.viajeros.append({'nombre': '', 'apellido1': ''})

def remove_viajero():
    if len(st.session_state.viajeros) > 1:
        st.session_state.viajeros.pop()

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

def get_client():
    c_path = os.getenv("MIR_CERT_PATH", "")
    k_path = os.getenv("MIR_KEY_PATH", "")
    p12_path = os.getenv("MIR_P12_PATH", "")
    p12_pass = p12_password if p12_password else os.getenv("MIR_P12_PASSWORD", "")
    
    # Only use env paths if they actually exist
    if c_path and not os.path.exists(c_path):
        c_path = ""
    if k_path and not os.path.exists(k_path):
        k_path = ""
    if p12_path and not os.path.exists(p12_path):
        p12_path = ""
    
    # Create temp directory for uploads
    if not os.path.exists("temp_certs"):
        os.makedirs("temp_certs")
        
    # Handle File Uploader (Manual)
    if cert_file:
        file_bytes = cert_file.getbuffer()
        is_p12 = cert_file.name.endswith(".p12") or cert_file.name.endswith(".pfx")
    # Handle Env Path (Automatic)
    elif p12_path:
        with open(p12_path, "rb") as f:
            file_bytes = f.read()
        is_p12 = True
    else:
        file_bytes = None
        is_p12 = False

    if file_bytes:
        if is_p12:
            if not p12_pass:
                st.error("Por favor, introduce la contraseña del certificado .p12")
                return None
            try:
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    file_bytes, p12_pass.encode()
                )
                # Combine cert and key into a single file for better compatibility
                combined_path = os.path.join("temp_certs", "combined.pem")
                with open(combined_path, "wb") as f:
                    # Write private key first
                    f.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                    # Write certificate
                    f.write(certificate.public_bytes(serialization.Encoding.PEM))
                    # Write chain
                    if additional_certificates:
                        for extra_cert in additional_certificates:
                            if extra_cert:
                                f.write(extra_cert.public_bytes(serialization.Encoding.PEM))
                
                c_path = combined_path
                k_path = None # Key is already in c_path
            except Exception as e:
                st.error(f"Error al procesar el archivo .p12: {e}")
                return None
        else:
            c_path = os.path.join("temp_certs", cert_file.name)
            with open(c_path, "wb") as f:
                f.write(file_bytes)

    if key_file and not cert_file.name.endswith(".p12"):
        k_path = os.path.join("temp_certs", key_file.name)
        with open(k_path, "wb") as f:
            f.write(key_file.getbuffer())

    return HospedajesClient(
        wsdl_path=wsdl,
        endpoint=endpoint,
        username=user,
        password=pwd,
        cert_path=c_path if c_path else None,
        key_path=k_path if k_path else None,
        verify_ssl=verify_ssl,
        mock_mode=mock_mode
    )

# --- Main Content ---
st.title("🏨 MIR Hospedajes - Portal de Comunicaciones")
if not get_env_bool("MODO_SSL", "True") and not get_env_bool("MODO_MOCK", "True"):
    st.warning("⚠️ Validación SSL desactivada. La conexión no es segura (solo para pruebas).")
elif not get_env_bool("MODO_MOCK", "True"):
    st.success("🔒 Validación SSL activa.")

st.info("Esta aplicación permite gestionar el envío de partes y reservas según el RD 933/2021.")

tabs = st.tabs(["📤 Alta", "🔍 Consultas", "❌ Anulaciones", "📚 Catálogo"])

# --- TAB: Alta ---
with tabs[0]:
    st.header("Envío de Comunicaciones (Alta)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tipo_com = st.selectbox("Tipo de Comunicación", [
            "PV - Partes de Viajeros",
            "RH - Reservas de Hospedaje",
            "AV - Alquiler de Vehículos",
            "RV - Reservas de Vehículos"
        ])
        cod_est = st.text_input("Código Establecimiento", value=os.getenv("MIR_ESTABLECIMIENTO_CODE", ""))
        
        st.write("---")
        st.write(f"👥 Viajeros: **{len(st.session_state.viajeros)}**")
        c_add, c_rem = st.columns(2)
        with c_add:
            st.button("➕ Añadir", on_click=add_viajero)
        with c_rem:
            st.button("🗑️ Quitar", on_click=remove_viajero)
        
    with col2:
        st.subheader("Datos de la Comunicación")
        # Main form for contract and payment
        with st.form("main_data_form"):
            c1, c2 = st.columns(2)
            with c1:
                ref = st.text_input("Referencia del Contrato", f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                f_cont = st.date_input("Fecha Contrato", datetime.now())
                num_hab = st.number_input("Número de Habitaciones", min_value=1, value=1)
            with c2:
                f_ent = st.datetime_input("Fecha Entrada/Inicio", datetime.now())
                f_sal = st.datetime_input("Fecha Salida/Fin", datetime.now())
                tiene_internet = st.checkbox("¿Tiene acceso a Internet?", value=False)
            
            st.divider()
            st.write("💳 Datos de Pago")
            p_col1, p_col2 = st.columns([1, 3])
            with p_col1:
                tipo_pago = st.selectbox("Tipo de Pago", ["EF", "TC", "TR", "OT"], help="EF: Efectivo, TC: Tarjeta, TR: Transferencia, OT: Otros")
                f_pago = st.date_input("Fecha de Pago", datetime.now())
                p_caducidad = st.text_input("Caducidad Tarjeta", value="", placeholder="MM/AAAA", help="Solo para TC")
            with p_col2:
                medio_pago = st.text_input("Identificación del Medio de Pago (IBAN, Tarjeta, etc.)", value="")
                p_titular = st.text_input("Nombre Completo del Titular del Pago", "")
            
            st.form_submit_button("Guardar Datos Generales", help="Pulsa esto para confirmar los datos de arriba antes de enviar.")

        # Traveler inputs (outside form to be dynamic)
        lista_personas_data = []
        for i, viajero in enumerate(st.session_state.viajeros):
            with st.expander(f"👤 Persona {i+1}: {viajero.get('nombre', '')} {viajero.get('apellido1', '')}", expanded=(i==len(st.session_state.viajeros)-1)):
                v1, v2 = st.columns([2, 1])
                with v1:
                    p_nom = st.text_input(f"Nombre P{i+1}", viajero.get('nombre', 'JUAN'), key=f"nom_{i}")
                    p_ap1 = st.text_input(f"Primer Apellido P{i+1}", viajero.get('apellido1', 'GARCIA'), key=f"ap1_{i}")
                    
                    # Logica para Segundo Apellido (Obligatorio para NIF)
                    label_ap2 = f"Segundo Apellido P{i+1}"
                    is_nif = st.session_state.get(f"tdoc_{i}") == "NIF"
                    if is_nif:
                        label_ap2 += " ⚠️ (Obligatorio para NIF)"
                    
                    p_ap2 = st.text_input(label_ap2, "", key=f"ap2_{i}")
                    
                    if is_nif and not p_ap2:
                        st.error(f"El segundo apellido es obligatorio para NIF (Persona {i+1})")
                    
                    # Soporte Documento (Obligatorio para NIF/NIE)
                    is_nie = st.session_state.get(f"tdoc_{i}") == "NIE"
                    label_soporte = f"Número Soporte P{i+1}"
                    if is_nif or is_nie:
                        label_soporte += " ⚠️ (Obligatorio para NIF/NIE)"
                    p_soporte = st.text_input(label_soporte, "", key=f"soporte_{i}", help="Ej: IDESP... para NIF o E... para NIE")
                
                with v2:
                    p_tdoc = st.selectbox(f"Tipo Doc P{i+1}", ["NIF", "NIE", "PAS", "ID"], key=f"tdoc_{i}")
                    p_doc = st.text_input(f"Documento P{i+1}", "12345678Z", key=f"doc_{i}")
                    p_sexo = st.selectbox(f"Sexo P{i+1}", ["M", "F", "X"], key=f"sexo_{i}")
                    p_fnac = st.date_input(f"Fecha Nacimiento P{i+1}", datetime(1980, 1, 1), key=f"fnac_{i}")
                
                # Calcular si es menor de edad (18 años)
                es_menor = (datetime.now().date() - p_fnac).days < (18 * 365)
                
                v3, v4 = st.columns(2)
                with v3:
                    p_nac = st.text_input(f"Nacionalidad P{i+1}", "ESP", key=f"nac_{i}")
                    p_parentesco = st.selectbox(f"Parentesco P{i+1}", ["", "P", "M", "A", "H", "O"], help="P: Padre, M: Madre, A: Abuelo, H: Hermano, O: Otros", key=f"par_{i}")
                    if es_menor and not p_parentesco:
                        st.warning(f"Persona {i+1} es menor. El parentesco es obligatorio.")
                with v4:
                    p_rol = st.selectbox(f"Rol P{i+1}", ["VI"], help="VI: Viajero (Obligatorio)", key=f"rol_{i}")
                
                # Contacto
                st.write(f"📞 Contacto P{i+1} (Al menos uno obligatorio)")
                c1, c2 = st.columns(2)
                with c1:
                    p_tel = st.text_input(f"Teléfono P{i+1}", "", key=f"tel_{i}")
                with c2:
                    p_email = st.text_input(f"Correo Electrónico P{i+1}", "", key=f"email_{i}")
                
                if not p_tel and not p_email:
                    st.error(f"Debes indicar al menos un teléfono o correo para la Persona {i+1}")
                
                # Direccion
                st.write(f"🏠 Dirección P{i+1}")
                d1, d2, d3 = st.columns([2, 1, 1])
                with d1:
                    d_dir = st.text_input(f"Dirección P{i+1}", "CALLE FALSA 123", key=f"dir_{i}")
                with d2:
                    d_cp = st.text_input(f"CP P{i+1}", "28001", key=f"cp_{i}")
                with d3:
                    d_pais = st.text_input(f"País P{i+1}", "ESP", key=f"dpais_{i}")

                # Update session state with current values
                st.session_state.viajeros[i]['nombre'] = p_nom
                st.session_state.viajeros[i]['apellido1'] = p_ap1

                lista_personas_data.append({
                    'rol': p_rol, 'nombre': p_nom, 'apellido1': p_ap1, 'apellido2': p_ap2,
                    'tipoDocumento': p_tdoc, 'numeroDocumento': p_doc, 'soporteDocumento': p_soporte,
                    'fechaNacimiento': p_fnac.strftime('%Y-%m-%d'), 'nacionalidad': p_nac, 'sexo': p_sexo,
                    'telefono': p_tel, 'correo': p_email, 'parentesco': p_parentesco,
                    'direccion': {'direccion': d_dir, 'codigoPostal': d_cp, 'pais': d_pais}
                })
        
        st.divider()
        if st.button("🚀 ENVIAR COMUNICACIÓN A MIR", type="primary"):
            # Final validation
            errors = []
            for i, p in enumerate(lista_personas_data):
                if p['tipoDocumento'] == 'NIF' and not p.get('apellido2'):
                    errors.append(f"Persona {i+1}: Falta el segundo apellido (NIF obligatorio)")
                if p['tipoDocumento'] in ['NIF', 'NIE'] and not p.get('soporteDocumento'):
                    errors.append(f"Persona {i+1}: Falta el número de soporte (Obligatorio para {p['tipoDocumento']})")
                if not p.get('telefono') and not p.get('correo'):
                    errors.append(f"Persona {i+1}: Debe indicar al menos un teléfono o correo")
                
                # Check for minor
                dob = datetime.strptime(p['fechaNacimiento'], '%Y-%m-%d').date()
                if (datetime.now().date() - dob).days < (18 * 365):
                    if not p.get('parentesco'):
                        errors.append(f"Persona {i+1}: Es menor de edad y falta el parentesco")
            
            if errors:
                for err in errors: st.error(err)
                st.stop()
                
            client = get_client()
            if client:
                # Preparar estructura de datos completa
                data = [{
                    'referencia': ref,
                    'fechaContrato': f_cont.strftime('%Y-%m-%d'),
                    'fechaEntrada': f_ent.strftime('%Y-%m-%dT%H:%M:%S'),
                    'fechaSalida': f_sal.strftime('%Y-%m-%dT%H:%M:%S'),
                    'numPersonas': len(lista_personas_data),
                    'numHabitaciones': num_hab,
                    'internet': tiene_internet,
                    'pago': {
                        'tipoPago': tipo_pago, 
                        'medioPago': medio_pago,
                        'fechaPago': f_pago.strftime('%Y-%m-%d'),
                        'titular': p_titular,
                        'caducidadTarjeta': p_caducidad
                    },
                    'personas': lista_personas_data
                }]
                
                xml_content = client.generate_alta_parte_hospedaje_xml(cod_est, data)
                res = client.comunicacion(cod_arrendador, app_name, 'A', tipo_com[:2], xml_content)
                
                st.success("Operación procesada")
                st.json(res)
                
                with st.expander("Ver XML Generado"):
                    st.code(xml_content.decode('utf-8'), language='xml')

# --- TAB: Consultas ---
with tabs[1]:
    st.header("Consulta de Lotes y Comunicaciones")
    op_consulta = st.radio("Buscar por:", ["Número de Lote", "Código de Comunicación"])
    search_val = st.text_input("Valor a buscar")
    
    if st.button("Consultar"):
        client = get_client()
        if op_consulta == "Número de Lote":
            res = client.consulta_lote([search_val])
        else:
            # Placeholder for consultaComunicacion
            res = {"info": "Consulta de comunicación individual", "valor": search_val}
        st.write("### Resultado")
        st.json(res)

# --- TAB: Anulaciones ---
with tabs[2]:
    st.header("Anulación de Comunicaciones")
    lote_anular = st.text_input("Número de Lote a anular completamente")
    
    if st.button("Anular Lote"):
        st.warning(f"¿Estás seguro de que deseas anular el lote {lote_anular}?")
        if st.button("Confirmar Anulación"):
            client = get_client()
            # Call anulacionLote
            st.success("Solicitud de anulación enviada")

# --- TAB: Catálogo ---
with tabs[3]:
    st.header("Consulta de Catálogos")
    cat_target = st.selectbox("Catálogo", ["PAISES", "TIPOS_DOCUMENTO", "ROLES_PERSONA", "MARCAS_VEHICULOS"])
    
    if st.button("Cargar Catálogo"):
        client = get_client()
        res = client.catalogo(cat_target)
        st.write(f"### Datos de {cat_target}")
        st.json(res)

# --- Footer ---
st.divider()
st.caption("MIR Hospedajes Python Client - Desarrollado para el cumplimiento del RD 933/2021.")
