import sys
import os
from datetime import datetime

# Agregar el directorio base al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseConnection

class ReviewDataProcessor:
    """Procesa y guarda los datos de reseñas en la base de datos"""
    
    def __init__(self):
        """Inicializar conexión a la base de datos"""
        self.db = DatabaseConnection()
        
    def process_reviews(self, reviews):
        """
        Procesa una lista de reseñas y las guarda en la base de datos
        
        Args:
            reviews (list): Lista de reseñas obtenidas de la API
            
        Returns:
            dict: Estadísticas del procesamiento
        """
        conn = self.db.connect()
        
        if not conn:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        stats = {
            "total": len(reviews),
            "inserted": 0,
            "updated": 0,
            "errors": 0
        }
        
        try:
            for review in reviews:
                # Procesar y guardar la reseña principal
                review_saved = self._save_review(cursor, review)
                
                if review_saved:
                    # Procesar y guardar las calificaciones asociadas
                    self._save_ratings(cursor, review)
                    
                    stats["inserted"] += 1
                else:
                    stats["errors"] += 1
            
            # Confirmar todos los cambios
            conn.commit()
            
        except Exception as e:
            print(f"Error durante el procesamiento: {e}")
            conn.rollback()
            stats["errors"] += 1
        finally:
            cursor.close()
            self.db.disconnect()
            
        return stats
    
    def _save_review(self, cursor, review):
        """
        Guarda o actualiza una reseña en la tabla review_products
        
        Args:
            cursor: Cursor de la conexión a la base de datos
            review (dict): Datos de la reseña
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Verificar si la reseña ya existe
            check_query = "SELECT id FROM review_products WHERE review_id = %s"
            cursor.execute(check_query, (review.get('review_id'),))
            existing = cursor.fetchone()
            
            # Preparar los datos
            review_data = {
                'review_id': review.get('review_id'),
                'created_at': review.get('created_at'),
                'entity_id': review.get('entity_id'),
                'entity_pk_value': review.get('entity_pk_value'),
                'status_id': review.get('status_id'),
                'title': review.get('title'),
                'detail': review.get('detail'),
                'nickname': review.get('nickname'),
                'customer_id': review.get('customer_id', None),
                'product_name': review.get('product_name', ''),
                'product_sku': review.get('product_sku', '')
            }
            
            if existing:
                # Actualizar registro existente
                update_query = """
                UPDATE review_products 
                SET 
                    created_at = %s, 
                    entity_id = %s, 
                    entity_pk_value = %s, 
                    status_id = %s,
                    title = %s, 
                    detail = %s, 
                    nickname = %s, 
                    customer_id = %s, 
                    product_name = %s, 
                    product_sku = %s,
                    processed_at = NULL
                WHERE review_id = %s
                """
                cursor.execute(update_query, (
                    review_data['created_at'],
                    review_data['entity_id'],
                    review_data['entity_pk_value'],
                    review_data['status_id'],
                    review_data['title'],
                    review_data['detail'],
                    review_data['nickname'],
                    review_data['customer_id'],
                    review_data['product_name'],
                    review_data['product_sku'],
                    review_data['review_id']
                ))
            else:
                # Insertar nuevo registro
                insert_query = """
                INSERT INTO review_products (
                    review_id, created_at, entity_id, entity_pk_value, 
                    status_id, title, detail, nickname, customer_id, 
                    product_name, product_sku, 
                    sentiment_score, keywords, ai_summary, topics, processed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL, NULL, NULL)
                """
                cursor.execute(insert_query, (
                    review_data['review_id'],
                    review_data['created_at'],
                    review_data['entity_id'],
                    review_data['entity_pk_value'],
                    review_data['status_id'],
                    review_data['title'],
                    review_data['detail'],
                    review_data['nickname'],
                    review_data['customer_id'],
                    review_data['product_name'],
                    review_data['product_sku']
                ))
            
            return True
            
        except Exception as e:
            print(f"Error al guardar reseña {review.get('review_id')}: {e}")
            return False
    
    def _save_ratings(self, cursor, review):
        """
        Guarda las calificaciones asociadas a una reseña
        
        Args:
            cursor: Cursor de la conexión a la base de datos
            review (dict): Datos completos de la reseña incluyendo ratings
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            review_id = review.get('review_id')
            ratings = review.get('ratings', [])
            
            if not ratings:
                return True
                
            # Eliminar calificaciones existentes para esta reseña
            delete_query = "DELETE FROM review_ratings WHERE review_id = %s"
            cursor.execute(delete_query, (review_id,))
            
            # Insertar las nuevas calificaciones
            for rating in ratings:
                insert_query = """
                INSERT INTO review_ratings (
                    review_id, rating_id, rating_code, value, percent
                ) VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    review_id,
                    rating.get('rating_id'),
                    rating.get('rating_code'),
                    rating.get('value'),
                    rating.get('percent')
                ))
            
            # Si hay ratings, actualizar el rating promedio en la tabla principal
            if ratings:
                avg_rating = sum(r.get('value', 0) for r in ratings) / len(ratings)
                update_query = "UPDATE review_products SET review_rating = %s WHERE review_id = %s"
                cursor.execute(update_query, (avg_rating, review_id))
            
            return True
            
        except Exception as e:
            print(f"Error al guardar ratings para reseña {review.get('review_id')}: {e}")
            return False 