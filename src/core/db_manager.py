import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

class DBManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError(" DATABASE_URL environment variable is not set")

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    def init_db(self):
        """Initializes the database schema if it doesn't exist."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) DEFAULT 'user',
                        subscription_active BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS tenants (
                        tenant_id VARCHAR(50) PRIMARY KEY,
                        owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        nombre VARCHAR(100) NOT NULL,
                        mir_user VARCHAR(50) NOT NULL,
                        mir_password VARCHAR(100) NOT NULL,
                        arrendador_code VARCHAR(50) NOT NULL,
                        establecimiento_code VARCHAR(50) NOT NULL,
                        p12_path TEXT,
                        p12_password VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- For existing DBs, ensure the column exists
                    ALTER TABLE tenants ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

                    CREATE TABLE IF NOT EXISTS catalogos (
                        id SERIAL PRIMARY KEY,
                        tenant_id VARCHAR(50) DEFAULT 'GLOBAL',
                        tipo_catalogo VARCHAR(50) NOT NULL,
                        codigo VARCHAR(50) NOT NULL,
                        descripcion VARCHAR(255) NOT NULL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tenant_id, tipo_catalogo, codigo)
                    );

                    CREATE TABLE IF NOT EXISTS comunicaciones (
                        id SERIAL PRIMARY KEY,
                        tenant_id VARCHAR(50) REFERENCES tenants(tenant_id),
                        lote VARCHAR(50),
                        tipo_comunicacion VARCHAR(2),
                        referencia_contrato VARCHAR(100),
                        fecha_entrada TIMESTAMP,
                        fecha_salida TIMESTAMP,
                        raw_response JSONB,
                        status_code INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS viajeros (
                        id SERIAL PRIMARY KEY,
                        comunicacion_id INTEGER REFERENCES comunicaciones(id) ON DELETE CASCADE,
                        nombre VARCHAR(100),
                        apellido1 VARCHAR(100),
                        apellido2 VARCHAR(100),
                        tipo_documento VARCHAR(10),
                        numero_documento VARCHAR(50),
                        nacionalidad VARCHAR(3),
                        sexo VARCHAR(1),
                        fecha_nacimiento DATE,
                        pais_residencia VARCHAR(3),
                        municipio_residencia VARCHAR(50)
                    );
                """)
            conn.commit()
        finally:
            conn.close()

    def save_catalogo(self, tipo_catalogo, items, tenant_id="GLOBAL"):
        """
        Saves or updates catalog items in the database.
        `items` should be a list of dictionaries with 'codigo' and 'descripcion'.
        """
        if not items:
            return

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Use execute_values or executemany. For simplicity and upsert, we loop or use bulk
                for item in items:
                    codigo = item.get('codigo')
                    descripcion = item.get('descripcion')
                    if codigo is not None and descripcion is not None:
                        cur.execute("""
                            INSERT INTO catalogos (tenant_id, tipo_catalogo, codigo, descripcion, last_updated)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (tenant_id, tipo_catalogo, codigo) 
                            DO UPDATE SET 
                                descripcion = EXCLUDED.descripcion,
                                last_updated = CURRENT_TIMESTAMP;
                        """, (tenant_id, tipo_catalogo, codigo, descripcion))
            conn.commit()
        finally:
            conn.close()

    def save_catalogo_batch(self, tipo_catalogo, items, tenant_id="GLOBAL"):
        from psycopg2.extras import execute_values
        if not items: return
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                values = [(tenant_id, tipo_catalogo, item.get('codigo'), item.get('descripcion')) 
                          for item in items if item.get('codigo') and item.get('descripcion')]
                execute_values(cur, """
                    INSERT INTO catalogos (tenant_id, tipo_catalogo, codigo, descripcion, last_updated)
                    VALUES %s
                    ON CONFLICT (tenant_id, tipo_catalogo, codigo) 
                    DO UPDATE SET 
                        descripcion = EXCLUDED.descripcion,
                        last_updated = CURRENT_TIMESTAMP;
                """, values, template="(%s, %s, %s, %s, CURRENT_TIMESTAMP)")
            conn.commit()
        finally:
            conn.close()

    def get_catalogo(self, tipo_catalogo, tenant_id="GLOBAL"):
        """
        Retrieves a catalog from the database.
        Returns a list of dicts: [{'codigo': ..., 'descripcion': ...}, ...]
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT codigo, descripcion, last_updated 
                    FROM catalogos 
                    WHERE tenant_id = %s AND tipo_catalogo = %s
                    ORDER BY codigo ASC;
                """, (tenant_id, tipo_catalogo))
                results = cur.fetchall()
                # Convert RealDictRow to standard dict
                return [dict(row) for row in results]
        finally:
            conn.close()

    def get_tenants(self, owner_id=None):
        """Returns a list of tenants. If owner_id is provided, filters by owner."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if owner_id:
                    cur.execute("SELECT tenant_id, nombre FROM tenants WHERE owner_id = %s ORDER BY nombre ASC;", (owner_id,))
                else:
                    cur.execute("SELECT tenant_id, nombre FROM tenants ORDER BY nombre ASC;")
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_tenant_config(self, tenant_id):
        """Returns the full configuration for a specific tenant."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM tenants WHERE tenant_id = %s;", (tenant_id,))
                res = cur.fetchone()
                return dict(res) if res else None
        finally:
            conn.close()

    def save_tenant(self, data):
        """Saves or updates a tenant configuration."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tenants (
                        tenant_id, owner_id, nombre, mir_user, mir_password, 
                        arrendador_code, establecimiento_code, p12_path, p12_password
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id) DO UPDATE SET
                        owner_id = COALESCE(EXCLUDED.owner_id, tenants.owner_id),
                        nombre = EXCLUDED.nombre,
                        mir_user = EXCLUDED.mir_user,
                        mir_password = EXCLUDED.mir_password,
                        arrendador_code = EXCLUDED.arrendador_code,
                        establecimiento_code = EXCLUDED.establecimiento_code,
                        p12_path = EXCLUDED.p12_path,
                        p12_password = EXCLUDED.p12_password;
                """, (
                    data['tenant_id'], data.get('owner_id'), data['nombre'], data['mir_user'], data['mir_password'],
                    data['arrendador_code'], data['establecimiento_code'], 
                    data.get('p12_path'), data.get('p12_password')
                ))
            conn.commit()
        finally:
            conn.close()

    def save_comunicacion_completa(self, tenant_id, data_com, raw_response):
        """
        Guarda el lote de comunicación y sus viajeros asociados.
        `data_com` es la lista de diccionarios enviada al Ministerio.
        `raw_response` es el dict de respuesta del Ministerio.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # 1. Guardar la comunicación general (usamos el primer contrato como referencia si hay varios)
                # En este cliente solemos enviar un contrato por lote.
                com = data_com[0]
                resp_header = raw_response.get('respuesta', {})
                lote = resp_header.get('lote', 'N/A')
                status_code = resp_header.get('codigo', 0)
                
                cur.execute("""
                    INSERT INTO comunicaciones (
                        tenant_id, lote, tipo_comunicacion, referencia_contrato, 
                        fecha_entrada, fecha_salida, raw_response, status_code
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """, (
                    tenant_id, lote, 'PV', com.get('referencia'), 
                    com.get('fechaEntrada'), com.get('fechaSalida'), 
                    json.dumps(raw_response), status_code
                ))
                com_id = cur.fetchone()[0]
                
                # 2. Guardar los viajeros
                for p in com.get('personas', []):
                    dir_p = p.get('direccion', {})
                    cur.execute("""
                        INSERT INTO viajeros (
                            comunicacion_id, nombre, apellido1, apellido2, 
                            tipo_documento, numero_documento, nacionalidad, sexo, 
                            fecha_nacimiento, pais_residencia, municipio_residencia
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        com_id, p.get('nombre'), p.get('apellido1'), p.get('apellido2'),
                        p.get('tipoDocumento'), p.get('numeroDocumento'), p.get('nacionalidad'), p.get('sexo'),
                        p.get('fechaNacimiento') if p.get('fechaNacimiento') else None, 
                        dir_p.get('pais'), dir_p.get('codigoMunicipio')
                    ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving communication to DB: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_statistics(self, tenant_id):
        """Calcula estadísticas para un tenant específico."""
        conn = self.get_connection()
        stats = {}
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total viajeros
                cur.execute("""
                    SELECT COUNT(*) as total 
                    FROM viajeros v 
                    JOIN comunicaciones c ON v.comunicacion_id = c.id 
                    WHERE c.tenant_id = %s
                """, (tenant_id,))
                stats['total_viajeros'] = cur.fetchone()['total']
                
                # Nacionalidades (Top 5)
                cur.execute("""
                    SELECT nacionalidad, COUNT(*) as count 
                    FROM viajeros v 
                    JOIN comunicaciones c ON v.comunicacion_id = c.id 
                    WHERE c.tenant_id = %s 
                    GROUP BY nacionalidad 
                    ORDER BY count DESC 
                    LIMIT 5
                """, (tenant_id,))
                stats['nacionalidades'] = [dict(r) for r in cur.fetchall()]
                
                # Evolución (por día en los últimos 30 días)
                cur.execute("""
                    SELECT DATE(created_at) as fecha, COUNT(*) as count 
                    FROM comunicaciones 
                    WHERE tenant_id = %s 
                    GROUP BY fecha 
                    ORDER BY fecha ASC
                """, (tenant_id,))
                stats['evolucion'] = [dict(r) for r in cur.fetchall()]
                
                # Provincias (Top 5 - Solo España)
                cur.execute("""
                    SELECT COALESCE(cat.descripcion, SUBSTRING(v.municipio_residencia, 1, 2)) as provincia, COUNT(*) as count 
                    FROM viajeros v 
                    JOIN comunicaciones c ON v.comunicacion_id = c.id 
                    LEFT JOIN catalogos cat ON SUBSTRING(v.municipio_residencia, 1, 2) = cat.codigo 
                         AND cat.tipo_catalogo = 'PROVINCIA'
                    WHERE c.tenant_id = %s AND v.nacionalidad = 'ESP' AND v.municipio_residencia IS NOT NULL
                    GROUP BY cat.descripcion, SUBSTRING(v.municipio_residencia, 1, 2)
                    ORDER BY count DESC 
                    LIMIT 5
                """, (tenant_id,))
                stats['provincias'] = [dict(r) for r in cur.fetchall()]
                
                # Municipios (Top 5)
                cur.execute("""
                    SELECT COALESCE(cat.descripcion, v.municipio_residencia) as municipio, COUNT(*) as count 
                    FROM viajeros v 
                    JOIN comunicaciones c ON v.comunicacion_id = c.id 
                    LEFT JOIN catalogos cat ON v.municipio_residencia = cat.codigo 
                         AND cat.tipo_catalogo = 'MUNICIPIO'
                    WHERE c.tenant_id = %s AND v.municipio_residencia IS NOT NULL
                    GROUP BY COALESCE(cat.descripcion, v.municipio_residencia)
                    ORDER BY count DESC 
                    LIMIT 5
                """, (tenant_id,))
                stats['municipios'] = [dict(r) for r in cur.fetchall()]
                
                # Viajeros Recurrentes
                cur.execute("""
                    SELECT numero_documento, nombre, apellido1, COUNT(*) as estancias 
                    FROM viajeros v 
                    JOIN comunicaciones c ON v.comunicacion_id = c.id 
                    WHERE c.tenant_id = %s 
                    GROUP BY numero_documento, nombre, apellido1 
                    HAVING COUNT(*) > 1 
                    ORDER BY estancias DESC
                """, (tenant_id,))
                stats['repetidores'] = [dict(r) for r in cur.fetchall()]
                
            return stats
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return None
        finally:
            conn.close()

    def get_historial(self, tenant_id, limit=50):
        """Obtiene el histórico de comunicaciones de un tenant."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT c.id, c.lote, c.tipo_comunicacion, c.referencia_contrato, 
                           c.fecha_entrada, c.fecha_salida, c.status_code, c.created_at,
                           COUNT(v.id) as num_viajeros
                    FROM comunicaciones c
                    LEFT JOIN viajeros v ON v.comunicacion_id = c.id
                    WHERE c.tenant_id = %s 
                    GROUP BY c.id
                    ORDER BY c.created_at DESC 
                    LIMIT %s
                """, (tenant_id, limit))
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_viajeros_by_comunicacion(self, com_id):
        """Obtiene la lista de viajeros de una comunicación específica."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT v.nombre, v.apellido1, v.apellido2, v.tipo_documento, v.numero_documento, 
                           v.nacionalidad, v.sexo, v.fecha_nacimiento, 
                           COALESCE(cat.descripcion, v.municipio_residencia) as municipio
                    FROM viajeros v
                    LEFT JOIN catalogos cat ON v.municipio_residencia = cat.codigo AND cat.tipo_catalogo = 'MUNICIPIO'
                    WHERE v.comunicacion_id = %s
                """, (com_id,))
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # --- User Management ---
    
    def create_user(self, email, password_hash, role='user', subscription_active=False):
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO users (email, password_hash, role, subscription_active)
                    VALUES (%s, %s, %s, %s) RETURNING id;
                """, (email, password_hash, role, subscription_active))
                res = cur.fetchone()
            conn.commit()
            return res['id'] if res else None
        finally:
            conn.close()

    def get_user_by_email(self, email):
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
                res = cur.fetchone()
                return dict(res) if res else None
        finally:
            conn.close()

# Singleton instance for easy importing
db = None

def get_db():
    global db
    if db is None:
        db = DBManager()
    return db
