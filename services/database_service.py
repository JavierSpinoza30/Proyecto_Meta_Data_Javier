from database import DatabaseConnection

class ProductService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_pending_products(self):
        """
        Obtiene los productos pendientes con al menos 6 atributos
        """
        connection = self.db.connect()
        cursor = connection.cursor(dictionary=True)
        
        # consulta trae los productos pendientes
        try:
            query = """
                SELECT
                p.*, 
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'code', av.attribute_code,
                        'label', av.label
                    )
                ) as attributes
                FROM products p
                LEFT JOIN attributes_products ap ON p.id = ap.product_id
                LEFT JOIN attribute_values av ON ap.attribute_value_id = av.id
                WHERE p.status_product_description = 'pending'
                GROUP BY p.id
                HAVING COUNT(ap.attribute_value_id) >= 6
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def update_product_description(self, product_id, description):
        """
        Actualiza la descripción y el estado del producto
        """
        connection = self.db.connect()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE products 
                SET description = %s,
                    status_product_description = 'completed',
                    updated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (description, product_id))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def get_pending_meta_keywords_products(self):
        """
        Obtiene los productos pendientes de generar meta keywords con al menos 5 atributos
        """
        connection = self.db.connect()
        cursor = connection.cursor(dictionary=True)
        
        # Consulta trae los productos pendientes de meta keywords
        try:
            query = """
                SELECT
                p.*, 
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'code', av.attribute_code,
                        'label', av.label
                    )
                ) as attributes
                FROM products p
                LEFT JOIN attributes_products ap ON p.id = ap.product_id
                LEFT JOIN attribute_values av ON ap.attribute_value_id = av.id
                WHERE p.status_product_keyword = 'pending' OR p.status_product_keyword IS NULL
                GROUP BY p.id
                HAVING COUNT(ap.attribute_value_id) >= 0
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def update_product_meta_keywords(self, product_id, meta_keywords):
        """
        Actualiza los meta keywords y el estado del producto
        """
        connection = self.db.connect()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE products 
                SET meta_keyword = %s,
                    status_product_keyword = 'completed',
                    updated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (meta_keywords, product_id))
            connection.commit()
            return True
        finally:
            cursor.close()
            connection.close()

    def get_pending_meta_title_products(self):
        """
        Obtiene los productos pendientes de generar meta title con al menos 5 atributos
        """
        connection = self.db.connect()
        cursor = connection.cursor(dictionary=True)
        
        # Consulta trae los productos pendientes de meta title
        try:
            query = """
                SELECT
                p.*, 
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'code', av.attribute_code,
                        'label', av.label
                    )
                ) as attributes
                FROM products p
                LEFT JOIN attributes_products ap ON p.id = ap.product_id
                LEFT JOIN attribute_values av ON ap.attribute_value_id = av.id
                WHERE p.status_product_meta_title = 'pending' OR p.status_product_meta_title IS NULL
                GROUP BY p.id
                HAVING COUNT(ap.attribute_value_id) >=0
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def update_product_meta_title(self, product_id, meta_title):
        """
        Actualiza el meta title y el estado del producto
        """
        connection = self.db.connect()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE products 
                SET meta_title = %s,
                    status_product_meta_title = 'completed',
                    updated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (meta_title, product_id))
            connection.commit()
            return True
        finally:
            cursor.close()
            connection.close() 