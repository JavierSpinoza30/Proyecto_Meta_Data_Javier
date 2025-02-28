import sys
import os

# Agregar el directorio principal al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseConnection
from datetime import datetime

class UpdateProductCategories:
    def __init__(self):
        # Inicializar conexión a la base de datos
        self.db = DatabaseConnection()
        self.connection = self.db.connect()
        
        if not self.connection:
            print("No se pudo establecer conexión con la base de datos")
            sys.exit(1)
        
        self.update_categories()
    
    def update_categories(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Consulta para obtener todos los registros de product_category_info
            select_query = """
                SELECT sku, category_path 
                FROM product_category_info
            """
            cursor.execute(select_query)
            category_info_records = cursor.fetchall()
            
            # Contador para seguimiento de actualizaciones
            updates_count = 0
            
            # Iterar sobre cada registro y actualizar la tabla products
            for record in category_info_records:
                update_query = """
                    UPDATE products 
                    SET category = %s,
                        updated_at = %s
                    WHERE sku = %s
                """
                
                current_time = datetime.now()
                cursor.execute(update_query, (
                    record['category_path'],
                    current_time,
                    record['sku']
                ))
                
                if cursor.rowcount > 0:
                    updates_count += 1
            
            # Confirmar los cambios en la base de datos
            self.connection.commit()
            
            print(f"Proceso completado. Se actualizaron {updates_count} productos con sus categorías.")
            
        except Exception as e:
            print(f"Error durante la actualización: {e}")
            self.connection.rollback()
        
        finally:
            cursor.close()
            self.db.disconnect()

if __name__ == "__main__":
    UpdateProductCategories()
