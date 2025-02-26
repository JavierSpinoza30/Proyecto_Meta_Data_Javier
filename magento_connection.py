import paramiko
import logging
from dotenv import load_dotenv
import os

class MagentoConnection:
    _instance = None

    def __new__(cls):
        # Patrón Singleton para asegurar una única instancia
        if cls._instance is None:
            cls._instance = super(MagentoConnection, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Solo inicializar una vez
        if self._initialized:
            return
            
        # Cargar variables de entorno
        load_dotenv()
        
        # Configuración SSH
        self.ssh_config = {
            'host': os.getenv('MAGENTO_SSH_HOST'),
            'port': int(os.getenv('MAGENTO_SSH_PORT', 22)),
            'username': os.getenv('MAGENTO_SSH_USERNAME'),
            'private_key_path': os.getenv('MAGENTO_SSH_KEY_PATH')
        }
        
        # Configuración DB
        self.db_config = {
            'host': os.getenv('MAGENTO_DB_HOST'),
            'user': os.getenv('MAGENTO_DB_USER'),
            'password': os.getenv('MAGENTO_DB_PASSWORD'),
            'database': os.getenv('MAGENTO_DB_NAME')
        }
        
        self._initialized = True
        
    def test_connection(self):
        """Prueba la conexión a Magento y devuelve True si es exitosa"""
        ssh = None
        try:
            # Configurar cliente SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            private_key = paramiko.RSAKey.from_private_key_file(self.ssh_config['private_key_path'])
            
            # Conectar
            ssh.connect(
                hostname=self.ssh_config['host'],
                port=self.ssh_config['port'],
                username=self.ssh_config['username'],
                pkey=private_key
            )
            
            print("✅ Conexión exitosa a Magento a través de SSH")
            return True
        except Exception as e:
            print(f"❌ Error de conexión a Magento: {str(e)}")
            return False
        finally:
            if ssh:
                ssh.close()

    def execute_query(self, query):
        """Ejecuta una consulta en la base de datos de Magento a través de SSH"""
        ssh = None
        try:
            # Configurar cliente SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            private_key = paramiko.RSAKey.from_private_key_file(self.ssh_config['private_key_path'])
            
            # Conectar
            ssh.connect(
                hostname=self.ssh_config['host'],
                port=self.ssh_config['port'],
                username=self.ssh_config['username'],
                pkey=private_key
            )
            
            print("✅ Conexión exitosa a Magento a través de SSH")
            
            # Construir comando MySQL
            command = f"mysql -h {self.db_config['host']} -u {self.db_config['user']} -p{self.db_config['password']} {self.db_config['database']} -e \"{query}\""
            
            # Ejecutar comando
            stdin, stdout, stderr = ssh.exec_command(command)
            
            # Procesar resultado
            output = stdout.read().decode()
            errors = stderr.read().decode()
            
            if errors:
                print(f"❌ Error en la consulta MySQL: {errors}")
                logging.error(f"Error en la consulta MySQL: {errors}")
                return None
                
            print("✅ Consulta ejecutada correctamente en la base de datos de Magento")
            return output
            
        except Exception as e:
            print(f"❌ Error en la conexión o consulta a Magento: {str(e)}")
            logging.error(f"Error en la conexión o consulta: {e}")
            return None
        finally:
            if ssh:
                ssh.close()

# Probar la conexión cuando se ejecuta el archivo directamente
if __name__ == "__main__":
    # Crear una instancia
    magento = MagentoConnection()
    
    # Probar la conexión
    magento.test_connection() 