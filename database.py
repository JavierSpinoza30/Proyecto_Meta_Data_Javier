import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print("Conexión exitosa a MySQL")
                return self.connection
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None
            
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión cerrada") 