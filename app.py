import streamlit as st
import pandas as pd
from hospedajes_client import HospedajesClient
import os
from datetime import datetime

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
        user = st.text_input("Usuario (CIF/NIF)", "")
        pwd = st.text_input("Contraseña", type="password")
        cod_arrendador = st.text_input("Código Arrendador", "")
        app_name = st.text_input("Nombre Aplicación", "PythonClient_v1")
        
    with st.expander("📜 Certificados (SSL)", expanded=False):
        cert_file = st.file_uploader("Certificado (.pem/.crt)", type=["pem", "crt"])
        key_file = st.file_uploader("Clave Privada (.key)", type=["key"])
        
    mock_mode = st.toggle("🚀 Modo Mock (Sin red)", value=True)

# --- Session State ---
if 'client' not in st.session_state:
    st.session_state.client = None

def get_client():
    return HospedajesClient(
        wsdl_path=wsdl,
        endpoint=endpoint,
        username=user,
        password=pwd,
        mock_mode=mock_mode
    )

# --- Main Content ---
st.title("🏨 MIR Hospedajes - Portal de Comunicaciones")
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
        cod_est = st.text_input("Código Establecimiento", "")
        
    with col2:
        st.subheader("Datos de la Comunicación")
        with st.form("alta_form"):
            ref = st.text_input("Referencia del Contrato", f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            f_cont = st.date_input("Fecha Contrato", datetime.now())
            f_ent = st.datetime_input("Fecha Entrada/Inicio", datetime.now())
            f_sal = st.datetime_input("Fecha Salida/Fin", datetime.now())
            
            st.divider()
            st.write("👤 Persona Principal")
            p_nom = st.text_input("Nombre", "JUAN")
            p_ap1 = st.text_input("Primer Apellido", "GARCIA")
            p_doc = st.text_input("Documento", "12345678Z")
            p_nac = st.text_input("Nacionalidad (ISO3166-3)", "ESP")
            
            submit = st.form_submit_button("Enviar Comunicación")
            
            if submit:
                client = get_client()
                # Build mock data structure for testing
                data = [{
                    'referencia': ref,
                    'fechaContrato': f_cont.strftime('%Y-%m-%d'),
                    'fechaEntrada': f_ent.strftime('%Y-%m-%dT%H:%M:%S'),
                    'fechaSalida': f_sal.strftime('%Y-%m-%dT%H:%M:%S'),
                    'numPersonas': 1,
                    'pago': {'tipoPago': 'EF', 'medioPago': 'Efectivo'},
                    'personas': [{
                        'rol': 'VI', 'nombre': p_nom, 'apellido1': p_ap1,
                        'tipoDocumento': 'NIF', 'numeroDocumento': p_doc,
                        'fechaNacimiento': '1980-01-01', 'nacionalidad': p_nac, 'sexo': 'M',
                        'direccion': {'direccion': 'CALLE FALSA 123', 'codigoPostal': '28001', 'pais': 'ESP'}
                    }]
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
