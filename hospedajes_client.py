import base64
import io
import zipfile
import lxml.etree as ET
from zeep import Client, Transport
from zeep.wsse import UsernameToken
from requests import Session
import requests

class HospedajesClient:
    def __init__(self, wsdl_path, endpoint=None, username=None, password=None, cert_path=None, key_path=None, mock_mode=False):
        self.wsdl_path = wsdl_path
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.cert_path = cert_path
        self.key_path = key_path
        self.mock_mode = mock_mode
        self.client = None
        
        if not mock_mode:
            session = Session()
            if cert_path and key_path:
                session.cert = (cert_path, key_path)
            elif cert_path:
                session.cert = cert_path
            
            if username and password:
                session.auth = requests.auth.HTTPBasicAuth(username, password)
            
            transport = Transport(session=session)
            self.client = Client(wsdl_path, transport=transport)
            if endpoint:
                self.service = self.client.create_service(
                    '{http://www.soap.servicios.hospedajes.mir.es/comunicacion}ComunicacionPortSoap11',
                    endpoint
                )
            else:
                self.service = self.client.service

    def _create_zip_base64(self, xml_content, filename="solicitud.xml"):
        """Compress XML content into a ZIP and encode as Base64."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(filename, xml_content)
        
        return base64.b64encode(zip_buffer.getvalue()).decode("utf-8")

    def generate_alta_parte_hospedaje_xml(self, cod_establecimiento, comunicaciones):
        """
        comunicaciones is a list of dicts:
        {
            'referencia': '...',
            'fechaContrato': 'YYYY-MM-DD',
            'fechaEntrada': 'YYYY-MM-DDTHH:MM:SS',
            'fechaSalida': 'YYYY-MM-DDTHH:MM:SS',
            'numPersonas': 1,
            'numHabitaciones': 1,
            'internet': True,
            'pago': {'tipoPago': '...', ...},
            'personas': [{'rol': 'VI', 'nombre': '...', ...}]
        }
        """
        NS_MAP = {
            None: "http://www.neg.hospedajes.mir.es/altaParteHospedaje",
            "hospe": "http://www.neg.hospedajes.mir.es/tiposGenerales"
        }
        
        root = ET.Element("{http://www.neg.hospedajes.mir.es/altaParteHospedaje}peticion", nsmap=NS_MAP)
        solicitud = ET.SubElement(root, "solicitud")
        ET.SubElement(solicitud, "codigoEstablecimiento").text = cod_establecimiento
        
        for com in comunicaciones:
            com_el = ET.SubElement(solicitud, "comunicacion")
            contrato = ET.SubElement(com_el, "contrato")
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}referencia").text = com['referencia']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaContrato").text = com['fechaContrato']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaEntrada").text = com['fechaEntrada']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaSalida").text = com['fechaSalida']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}numPersonas").text = str(com['numPersonas'])
            if 'numHabitaciones' in com:
                ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}numHabitaciones").text = str(com['numHabitaciones'])
            if 'internet' in com:
                ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}internet").text = "1" if com['internet'] else "0"
            
            # Pago
            pago = ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}pago")
            p_data = com['pago']
            ET.SubElement(pago, "{http://www.neg.hospedajes.mir.es/tiposGenerales}tipoPago").text = p_data['tipoPago']
            if 'fechaPago' in p_data:
                ET.SubElement(pago, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaPago").text = p_data['fechaPago']
            if 'medioPago' in p_data:
                ET.SubElement(pago, "{http://www.neg.hospedajes.mir.es/tiposGenerales}medioPago").text = p_data['medioPago']
            if 'titular' in p_data:
                ET.SubElement(pago, "{http://www.neg.hospedajes.mir.es/tiposGenerales}titular").text = p_data['titular']
            if 'caducidadTarjeta' in p_data:
                ET.SubElement(pago, "{http://www.neg.hospedajes.mir.es/tiposGenerales}caducidadTarjeta").text = p_data['caducidadTarjeta']

            # Personas
            for pers in com['personas']:
                p_el = ET.SubElement(com_el, "persona")
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}rol").text = pers['rol']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}nombre").text = pers['nombre']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}apellido1").text = pers['apellido1']
                if 'apellido2' in pers:
                    ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tipedadesGenerales}apellido2").text = pers['apellido2']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}tipoDocumento").text = pers['tipoDocumento']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}numeroDocumento").text = pers['numeroDocumento']
                if 'soporteDocumento' in pers:
                    ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}soporteDocumento").text = pers['soporteDocumento']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaNacimiento").text = pers['fechaNacimiento']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}nacionalidad").text = pers['nacionalidad']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}sexo").text = pers['sexo']
                
                # Direccion
                dir_el = ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}direccion")
                d_data = pers['direccion']
                ET.SubElement(dir_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}direccion").text = d_data['direccion']
                ET.SubElement(dir_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}codigoPostal").text = d_data['codigoPostal']
                ET.SubElement(dir_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}pais").text = d_data['pais']
                if 'nombreMunicipio' in d_data:
                    ET.SubElement(dir_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}nombreMunicipio").text = d_data['nombreMunicipio']

        return ET.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    def generate_alta_reserva_hospedaje_xml(self, comunicaciones):
        """comunicaciones: list of dicts with 'establecimiento', 'contrato', 'persona'"""
        NS_MAP = {
            None: "http://www.neg.hospedajes.mir.es/altaReservaHospedaje",
            "hospe": "http://www.neg.hospedajes.mir.es/tiposGenerales"
        }
        root = ET.Element("{http://www.neg.hospedajes.mir.es/altaReservaHospedaje}peticion", nsmap=NS_MAP)
        solicitud = ET.SubElement(root, "solicitud")
        
        for com in comunicaciones:
            com_el = ET.SubElement(solicitud, "comunicacion")
            est = ET.SubElement(com_el, "establecimiento")
            ET.SubElement(est, "{http://www.neg.hospedajes.mir.es/tiposGenerales}codigo").text = com.get('cod_est', '')
            
            contrato = ET.SubElement(com_el, "contrato")
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}referencia").text = com['referencia']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaContrato").text = com['fechaContrato']
            
            for pers in com['personas']:
                p_el = ET.SubElement(com_el, "persona")
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}rol").text = pers['rol']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}nombre").text = pers['nombre']
                ET.SubElement(p_el, "{http://www.neg.hospedajes.mir.es/tiposGenerales}apellido1").text = pers['apellido1']
        
        return ET.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    def generate_anulacion_xml(self, codigos):
        """Generates the XML for anulating specific communications."""
        NS_MAP = {None: "http://www.neg.hospedajes.mir.es/anularComunicacion"}
        root = ET.Element("{http://www.neg.hospedajes.mir.es/anularComunicacion}peticion", nsmap=NS_MAP)
        solicitud = ET.SubElement(root, "solicitud")
        for cod in codigos:
            ET.SubElement(solicitud, "codigoComunicacion").text = cod
        return ET.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    def generate_alta_alquiler_vehiculo_xml(self, cod_arrendador, comunicaciones):
        """Generates the XML for High Alquiler Vehiculo (AV)."""
        NS_MAP = {
            None: "http://www.neg.hospedajes.mir.es/altaAlquilerVehiculo",
            "hospe": "http://www.neg.hospedajes.mir.es/tiposGenerales"
        }
        root = ET.Element("{http://www.neg.hospedajes.mir.es/altaAlquilerVehiculo}peticion", nsmap=NS_MAP)
        solicitud = ET.SubElement(root, "solicitud")
        ET.SubElement(solicitud, "codigoArrendador").text = cod_arrendador
        
        for com in comunicaciones:
            com_el = ET.SubElement(solicitud, "comunicacion")
            contrato = ET.SubElement(com_el, "contrato")
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}referencia").text = com['referencia']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaContrato").text = com['fechaContrato']
            ET.SubElement(contrato, "{http://www.neg.hospedajes.mir.es/tiposGenerales}fechaRecogida").text = com['fechaRecogida']
            
            # Vehiculo
            veh = ET.SubElement(com_el, "vehiculo")
            ET.SubElement(veh, "{http://www.neg.hospedajes.mir.es/tiposGenerales}marca").text = com['vehiculo']['marca']
            ET.SubElement(veh, "{http://www.neg.hospedajes.mir.es/tiposGenerales}modelo").text = com['vehiculo']['modelo']
            ET.SubElement(veh, "{http://www.neg.hospedajes.mir.es/tiposGenerales}matricula").text = com['vehiculo']['matricula']
            
        return ET.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    def generate_alta_reserva_vehiculo_xml(self, comunicaciones):
        """Generates the XML for High Reserva Vehiculo (RV)."""
        NS_MAP = {
            None: "http://www.neg.hospedajes.mir.es/altaReservaVehiculo",
            "hospe": "http://www.neg.hospedajes.mir.es/tiposGenerales"
        }
        root = ET.Element("{http://www.neg.hospedajes.mir.es/altaReservaVehiculo}peticion", nsmap=NS_MAP)
        solicitud = ET.SubElement(root, "solicitud")
        
        for com in comunicaciones:
            com_el = ET.SubElement(solicitud, "comunicacion")
            # Similar structure...
        return ET.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    def comunicacion(self, cod_arrendador, aplicacion, tipo_operacion, tipo_comunicacion, xml_content):
        payload = self._create_zip_base64(xml_content)
        
        cabecera = {
            'codigoArrendador': cod_arrendador,
            'aplicacion': aplicacion,
            'tipoOperacion': tipo_operacion,
            'tipoComunicacion': tipo_comunicacion
        }
        
        if self.mock_mode:
            return {"status": "MOCK", "cabecera": cabecera, "payload_preview": payload[:50] + "..."}
        
        try:
            response = self.service.comunicacion(peticion={'cabecera': cabecera, 'solicitud': payload})
            return response
        except Exception as e:
            return {"error": str(e)}

    def consulta_lote(self, codigos_lote):
        if self.mock_mode:
            return {"status": "MOCK", "action": "consulta_lote", "codigos": codigos_lote}
        
        try:
            response = self.service.consultaLote(codigosLote={'lote': codigos_lote})
            return response
        except Exception as e:
            return {"error": str(e)}

    def catalogo(self, nombre_catalogo):
        if self.mock_mode:
            return {"status": "MOCK", "action": "catalogo", "target": nombre_catalogo}
        
        try:
            response = self.service.catalogo(peticion={'catalogo': nombre_catalogo})
            return response
        except Exception as e:
            return {"error": str(e)}
