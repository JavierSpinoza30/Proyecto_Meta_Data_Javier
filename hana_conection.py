from hdbcli import dbapi
import os
from dotenv import load_dotenv

def connect_hana():
    # Cargar variables de entorno
    load_dotenv()
    
    # Parámetros de conexión a la base de datos desde variables de entorno
    connection_params = {
        'address': os.getenv('HANA_ADDRESS'),
        'port': os.getenv('HANA_PORT'),
        'user': os.getenv('HANA_USER'),
        'password': os.getenv('HANA_PASSWORD')
    }

    try:
        # Intentar establecer la conexión
        conn = dbapi.connect(**connection_params)
        print("✅ Conexión exitosa a SAP HANA")
        return conn
    except dbapi.Error as e:
        # Manejo de errores de conexión
        print(f"❌ Error de conexión a SAP HANA: {str(e)}")
        return None

def execute_query(connection, query):
    try:
        # Crear un cursor para ejecutar consultas
        cursor = connection.cursor()
        
        # Ejecutar la consulta
        cursor.execute(query)
        
        # Obtener los resultados
        results = cursor.fetchall()
        
        # Cerrar el cursor
        cursor.close()
        
        return results
    except dbapi.Error as e:
        print(f"❌ Error al ejecutar la consulta: {str(e)}")
        return None

# Probar la conexión cuando se ejecuta el archivo directamente
if __name__ == "__main__":
    # Intentar establecer la conexión
    connection = connect_hana()
    
    if connection:
        # Si la conexión fue exitosa, cerrarla
        connection.close()
