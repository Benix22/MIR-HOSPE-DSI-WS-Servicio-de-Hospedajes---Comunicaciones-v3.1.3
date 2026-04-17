# MIR Hospedajes Python Client (RD 933/2021)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)

Esta aplicación proporciona un cliente completo y una interfaz gráfica para interactuar con el **Servicio de Comunicación de Hospedajes y Alquiler de Vehículos** del Ministerio del Interior de España, cumpliendo con las obligaciones del **Real Decreto 933/2021**.

## 🚀 Características

- **Interfaz Visual Moderna**: Desarrollada con Streamlit para una experiencia de usuario premium.
- **Generación Automática de XML**: Crea archivos XML complejos cumpliendo estrictamente con los esquemas XSD oficiales (v3.1.3).
- **Procesamiento de Carga Útil**: Maneja automáticamente la compresión **ZIP** y codificación **Base64** requerida por el servicio.
- **Soporte de Operaciones Completo**:
  - **Alta**: Partes de viajeros (PV), Reservas de Hospedaje (RH), Alquiler de Vehículos (AV) y Reservas de Vehículos (RV).
  - **Consultas**: Búsqueda por número de lote o código de comunicación.
  - **Anulaciones**: Cancelación de lotes completos.
  - **Catálogo**: Consulta de tablas maestras (países, tipos de documento, etc.).
- **Seguridad**: Compatible con **HTTP Basic Auth** y **SSL Mutual Auth** (Certificados de cliente .crt/.key).
- **Modo Mock**: Permite previsualizar los XML y sobres SOAP sin realizar conexiones reales.

## 🛠️ Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/mir-hospedajes-client.git
   cd mir-hospedajes-client
   ```

2. Instala las dependencias:
   ```bash
   pip install streamlit zeep lxml requests
   ```

## 💻 Uso

Ejecuta la aplicación con Streamlit:

```bash
python -m streamlit run app.py
```

La aplicación se abrirá en tu navegador (por defecto en `http://localhost:8501`).

### Configuración
En la barra lateral (Sidebar), podrás configurar:
- **Entorno**: Selección entre Pruebas (Pre-producción) y Producción.
- **Credenciales**: Usuario y contraseña proporcionados por el Ministerio.
- **Certificados**: Carga tus archivos de certificado y clave privada para la conexión SSL segura.

## 📂 Estructura del Proyecto

- `app.py`: Interfaz de usuario principal.
- `hospedajes_client.py`: Clase núcleo que gestiona la lógica de negocio y comunicación SOAP.
- `comunicacion.wsdl`: Definición del servicio web.
- `*.xsd`: Esquemas de validación de datos.

## ⚖️ Descargo de Responsabilidad

Este software no es una herramienta oficial del Ministerio del Interior. El uso de esta aplicación es responsabilidad exclusiva del usuario. Asegúrese de cumplir con la normativa vigente de protección de datos (RGPD) al manejar información de viajeros.

---
Desarrollado para facilitar el cumplimiento normativo mediante automatización.
