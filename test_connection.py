from hospedajes_client import HospedajesClient
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def test():
    print("--- Iniciando Prueba de Conexión ---")
    
    # Configuración desde .env
    wsdl = "comunicacion.wsdl"
    endpoint = "https://hospedajes.pre-ses.mir.es/hospedajes-web/ws/v1/comunicacion"
    user = os.getenv("MIR_USER")
    pwd = os.getenv("MIR_PASSWORD")
    p12_path = os.getenv("MIR_P12_PATH")
    p12_pass = os.getenv("MIR_P12_PASSWORD")
    
    print(f"Endpoint: {endpoint}")
    print(f"Usuario: {user}")
    print(f"Certificado: {p12_path}")
    
    # Intentamos cargar el certificado si es P12
    # Nota: En el cliente real, app.py hace la conversión. 
    # Para esta prueba, si no hay PEM, fallará, lo cual es útil para saber qué falta.
    
    client = HospedajesClient(
        wsdl_path=wsdl,
        endpoint=endpoint,
        username=user,
        password=pwd,
        cert_path=None, # Dejamos que falle para ver el error exacto de SSL
        verify_ssl=True
    )
    
    print("\nSolicitando Catálogo de PAISES...")
    res = client.catalogo("PAISES")
    print(f"Resultado: {res}")

if __name__ == "__main__":
    test()
