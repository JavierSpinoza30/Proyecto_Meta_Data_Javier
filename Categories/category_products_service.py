import sys
import os

# Agregar el directorio principal al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from magento_connection import MagentoConnection
from database import DatabaseConnection

class CategoryProductsService:
    def __init__(self):
        # Inicializar la conexión a Magento
        self.magento_connection = MagentoConnection()
        # Inicializar la conexión a la base de datos
        self.db_connection = DatabaseConnection()

    def get_category_products(self):
        query = """
            SELECT 
            p.sku,
            cp.category_id,
            cat.level AS category_level, -- Agregamos el nivel de la categoría
            GROUP_CONCAT(
                category_names.value
                ORDER BY LOCATE(CONCAT('/', category_entities.entity_id, '/'), CONCAT(cat.path, '/'))
                SEPARATOR ' > '
            ) AS category_path
            FROM 
                catalog_product_entity p
            JOIN 
                catalog_category_product cp ON p.entity_id = cp.product_id
            JOIN 
                catalog_category_entity cat ON cp.category_id = cat.entity_id
            JOIN 
                catalog_category_entity category_entities ON FIND_IN_SET(category_entities.entity_id, REPLACE(cat.path, '/', ','))
            JOIN 
                catalog_category_entity_varchar category_names ON (
                    category_names.row_id = category_entities.row_id
                    AND category_names.attribute_id = 134  -- ID del atributo 'name'
                    AND category_names.store_id = 0
                )
            WHERE 
                category_entities.level > 1  -- Excluimos la categoría raíz
            GROUP BY 
                p.sku, cp.category_id, cat.level
            ORDER BY 
                p.sku, cat.path;
        """
        # Ejecutar la consulta usando la conexión a Magento
        return self.magento_connection.execute_query(query)

    def save_category_products_to_db(self):
        """
        Obtiene los datos de productos y categorías de Magento y los guarda en la base de datos local.
        Para SKUs repetidos, solo guarda el registro con el nivel de categoría más alto.
        Usa ON DUPLICATE KEY UPDATE para mayor eficiencia.
        """
        try:
            # Obtener los datos de Magento
            magento_data = self.get_category_products()
            if not magento_data:
                print("❌ No se encontraron datos para guardar")
                return False

            # Conectar a la base de datos
            connection = self.db_connection.connect()
            if not connection:
                print("❌ Error al conectar a la base de datos")
                return False

            cursor = connection.cursor()
            
            # Preparar la consulta SQL con ON DUPLICATE KEY UPDATE
            insert_query = """
                INSERT INTO product_category_info 
                (sku, category_id, category_level, category_path)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    category_level = IF(VALUES(category_level) > category_level, 
                                      VALUES(category_level), 
                                      category_level),
                    category_path = IF(VALUES(category_level) > category_level,
                                     VALUES(category_path),
                                     category_path)
            """
            
            # Diccionario para almacenar el nivel más alto de cada SKU
            sku_highest_level = {}
            
            # Procesar los datos línea por línea
            lines = magento_data.strip().split('\n')
            
            # Ignorar la primera línea (encabezados) si existe
            if lines and 'category_id' in lines[0]:
                lines = lines[1:]
            
            # Primera pasada: encontrar el nivel más alto para cada SKU
            for line in lines:
                if not line.strip():  # Ignorar líneas vacías
                    continue
                    
                parts = line.split('\t')
                if len(parts) == 4:  # Asegurarnos de que tengamos todos los datos
                    try:
                        sku = parts[0].strip()
                        level = int(parts[2].strip())
                        
                        # Actualizar el nivel más alto para este SKU
                        if sku not in sku_highest_level or level > sku_highest_level[sku]:
                            sku_highest_level[sku] = level
                            
                    except ValueError:
                        continue
            
            # Segunda pasada: insertar todos los registros con nivel más alto
            registros_procesados = 0
            for line in lines:
                if not line.strip():
                    continue
                    
                parts = line.split('\t')
                if len(parts) == 4:
                    try:
                        sku = parts[0].strip()
                        category_id = int(parts[1].strip())
                        level = int(parts[2].strip())
                        category_path = parts[3].strip()
                        
                        # Solo procesar si es el nivel más alto para este SKU
                        if level == sku_highest_level[sku]:
                            data_tuple = (sku, category_id, level, category_path)
                            cursor.execute(insert_query, data_tuple)
                            registros_procesados += 1
                            
                    except ValueError as ve:
                        print(f"❌ Error al procesar la línea: {line}")
                        print(f"Error específico: {str(ve)}")
                        continue
            
            # Confirmar los cambios
            connection.commit()
            print(f"✅ Proceso completado: {registros_procesados} registros procesados")
            print("   Los registros existentes fueron actualizados solo si el nuevo nivel era mayor")
            
            cursor.close()
            self.db_connection.disconnect()
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar los datos: {str(e)}")
            if 'connection' in locals() and connection.is_connected():
                connection.rollback()
                self.db_connection.disconnect()
            return False