from magento_connection import MagentoConnection
from database import DatabaseConnection
from datetime import datetime
import os
from dotenv import load_dotenv
from multiprocessing import Pool, cpu_count
from itertools import islice
import pandas as pd

class ProductService:
    def __init__(self):
        # Cargar variables de entorno desde .env
        load_dotenv()
        self.magento = MagentoConnection()
        self.page_size = 500
        self.batch_size = 4000
        self.num_processes = 5  # Limitamos a 5 procesos en lugar de usar cpu_count()
        # self.num_processes = cpu_count()  # Número de procesadores disponibles y lo usa todos

    def get_products_data(self):
        """Obtiene los datos de los productos desde la base de datos de Magento"""
        query = """
        SELECT DISTINCT
            e.entity_id as id,
            e.sku,
            e.created_at,
            e.updated_at,
            e.type_id as product_type_id,
            eav.attribute_code,
            CASE 
                WHEN eav.backend_type = 'varchar' THEN varchar_table.value
                WHEN eav.backend_type = 'int' AND eav.frontend_input = 'select' THEN 
                    (SELECT value FROM eav_attribute_option_value 
                     WHERE option_id = int_table.value 
                     AND store_id = 0)
                WHEN eav.backend_type = 'int' THEN int_table.value
                WHEN eav.backend_type = 'text' THEN text_table.value
                WHEN eav.backend_type = 'decimal' THEN decimal_table.value
                WHEN eav.backend_type = 'datetime' THEN datetime_table.value
            END as valor_atributo
        FROM catalog_product_entity e
        CROSS JOIN eav_attribute eav 
        LEFT JOIN catalog_product_entity_varchar varchar_table 
            ON varchar_table.attribute_id = eav.attribute_id 
            AND varchar_table.row_id = e.row_id
        LEFT JOIN catalog_product_entity_int int_table 
            ON int_table.attribute_id = eav.attribute_id 
            AND int_table.row_id = e.row_id
        LEFT JOIN catalog_product_entity_text text_table 
            ON text_table.attribute_id = eav.attribute_id 
            AND text_table.row_id = e.row_id
        LEFT JOIN catalog_product_entity_decimal decimal_table 
            ON decimal_table.attribute_id = eav.attribute_id 
            AND decimal_table.row_id = e.row_id
        LEFT JOIN catalog_product_entity_datetime datetime_table 
            ON datetime_table.attribute_id = eav.attribute_id 
            AND datetime_table.row_id = e.row_id
        WHERE eav.entity_type_id = 4
        AND (
            varchar_table.value IS NOT NULL OR
            int_table.value IS NOT NULL OR
            text_table.value IS NOT NULL OR
            decimal_table.value IS NOT NULL OR
            datetime_table.value IS NOT NULL
        )
        ORDER BY e.entity_id, eav.attribute_code
        """
        return self.magento.execute_query(query)

    def process_batch(self, batch_data):
        """Procesa un lote de datos de productos"""
        connection = None
        try:
            db = DatabaseConnection()
            connection = db.connect()
            cursor = connection.cursor()
            
            products = {}
            attribute_relations = []
            
            # Procesamiento del lote
            for line in batch_data:
                if not line.strip():
                    continue
                
                # Validación de que la línea tenga todos los campos necesarios
                fields = line.split('\t')
                if len(fields) != 7:
                    print(f"Línea con formato incorrecto: {line}")
                    continue
                
                product_id, sku, created_at, updated_at, type_id, attribute_code, value = fields
                
                # Validación de que el value no sea None o vacío
                if value is None or value.strip() == '':
                    continue

                if product_id not in products:
                    products[product_id] = {
                        'id': int(product_id),
                        'sku': sku,
                        'name': '',
                        'type_id': type_id,
                        'meta_title': '',
                        'meta_keyword': '',
                        'meta_description': '',
                        'description': '',
                        'status_product_meta_title': 'pending',
                        'status_product_keyword': 'pending',
                        'status_product_meta_description': 'pending',
                        'status_product_description': 'pending',
                        'created_at': created_at,
                        'updated_at': updated_at
                    }
                
                if attribute_code in ['name', 'meta_title', 'meta_keyword', 'meta_description', 'description']:
                    # Solo actualizamos si el nuevo valor no es vacío
                    if value and value.strip():
                        products[product_id][attribute_code] = value.strip()

                # Optimizamos la consulta de atributos usando IN
                cursor.execute(
                    "SELECT id, base_attribute_code, label FROM attribute_values WHERE base_attribute_code = %s AND label = %s",
                    (attribute_code, value)
                )
                attribute_value_id = cursor.fetchone()
                if attribute_value_id:
                    attribute_relations.append((int(product_id), attribute_value_id[0]))

            # Filtrar productos que no tengan nombre
            products = {k: v for k, v in products.items() if v['name']}

            # Validar status
            for product in products.values():
                # Validación para todos los campos meta y description
                if product['meta_title'] and product['meta_title'] != product['name']:
                    product['status_product_meta_title'] = 'completed'

                if product['meta_keyword'] and product['meta_keyword'] != product['name']:
                    product['status_product_keyword'] = 'completed'

                if product['meta_description'] and product['meta_description'] != product['name']:
                    product['status_product_meta_description'] = 'completed'

                if product['description'] and product['description'] != product['name']:
                    product['status_product_description'] = 'completed'

            # Primero insertamos los productos
            if products:
                product_values = list(products.values())
                self._bulk_insert_products(cursor, product_values)
                
                # Hacemos commit después de insertar productos
                connection.commit()
                
                # SOLO DESPUÉS insertamos las relaciones
                if attribute_relations:
                    self._bulk_insert_relations(cursor, attribute_relations)
                    connection.commit()
            
            return len(products), len(attribute_relations)
            
        except Exception as e:
            print(f"Error en proceso batch: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                cursor.close()
                db.disconnect()

    def _bulk_insert_products(self, cursor, products):
        """Optimiza la inserción masiva de productos"""
        insert_query = """
        INSERT INTO products (
            id, sku, name, type_id, meta_title, meta_keyword, 
            meta_description, description, status_product_meta_title,
            status_product_keyword, status_product_meta_description,
            status_product_description, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sku = VALUES(sku),
            name = VALUES(name),
            type_id = VALUES(type_id),
            meta_title = VALUES(meta_title),
            meta_keyword = VALUES(meta_keyword),
            meta_description = VALUES(meta_description),
            description = VALUES(description),
            status_product_meta_title = VALUES(status_product_meta_title),
            status_product_keyword = VALUES(status_product_keyword),
            status_product_meta_description = VALUES(status_product_meta_description),
            status_product_description = VALUES(status_product_description),
            created_at = VALUES(created_at),
            updated_at = VALUES(updated_at)
        """
        cursor.executemany(insert_query, [
            (p['id'], p['sku'], p['name'], p['type_id'], p['meta_title'],
             p['meta_keyword'], p['meta_description'], p['description'],
             p['status_product_meta_title'], p['status_product_keyword'],
             p['status_product_meta_description'], p['status_product_description'],
             p['created_at'], p['updated_at']) for p in products
        ])

    def _bulk_insert_relations(self, cursor, relations):
        """Optimiza la inserción masiva de relaciones"""
        if not relations:
            return
        
        try:
            product_ids = list({relation[0] for relation in relations})
            print(f"Verificando {len(product_ids)} productos únicos")
            
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"SELECT id FROM products WHERE id IN ({placeholders})"
            
            cursor.execute(query, product_ids)
            existing_products = {row[0] for row in cursor.fetchall()}
            print(f"Encontrados {len(existing_products)} productos existentes")
            
            valid_relations = [
                relation for relation in relations 
                if relation[0] in existing_products
            ]
            print(f"Relaciones válidas a insertar: {len(valid_relations)}")
            
            if valid_relations:
                insert_relation_query = """
                INSERT INTO attributes_products (product_id, attribute_value_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE attribute_value_id = VALUES(attribute_value_id)
                """
                cursor.executemany(insert_relation_query, valid_relations)
            
        except Exception as e:
            print(f"Error en _bulk_insert_relations: {str(e)}")
            raise

    def process_products(self):
        """Procesa y guarda los productos en la base de datos local usando multiprocesamiento"""
        raw_data = self.get_products_data()
        if not raw_data:
            print("No se obtuvieron datos de productos")
            return

        # Dividir datos en lotes para procesamiento paralelo
        data_lines = raw_data.strip().split('\n')[1:]
        total_lines = len(data_lines)
        batch_size = total_lines // (self.num_processes * 2)  # Dividimos en lotes según los procesadores
        
        batches = []
        for i in range(0, total_lines, batch_size):
            batch = data_lines[i:i + batch_size]
            if batch:
                batches.append(batch)

        # Agregar logging
        print(f"Total de líneas a procesar: {total_lines}")
        print(f"Tamaño de lote: {batch_size}")
        print(f"Número de lotes: {len(batches)}")

        # Procesar en paralelo
        with Pool(processes=self.num_processes) as pool:
            results = pool.map(self.process_batch, batches)

        # Logging detallado de resultados
        for i, (products, relations) in enumerate(results):
            print(f"Lote {i+1}: {products} productos, {relations} relaciones")

        # Sumar resultados
        total_products = sum(r[0] for r in results)
        total_relations = sum(r[1] for r in results)
        
        print(f"Se procesaron {total_products} productos y {total_relations} relaciones exitosamente")

    def save_to_database(self):
        """Método principal para guardar los productos"""
        self.process_products()
