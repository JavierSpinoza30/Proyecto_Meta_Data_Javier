import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Agregar el directorio base al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseConnection

# Cargar variables de entorno
load_dotenv()

class ChatbotController:
    """Controlador para el chatbot de análisis de reseñas utilizando Gemini"""
    
    def __init__(self):
        """Inicializar controlador y cliente de Gemini"""
        # Configurar el cliente de Gemini con la API key
        self.genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.db = DatabaseConnection()
        self.system_prompt = self._generate_system_prompt()
        self.conversation_history = []
        
    def _generate_system_prompt(self):
        """Genera el prompt de sistema para el asistente"""
        return """
        Eres un asistente especializado en analizar reseñas de productos de bicicletas.
        Tu objetivo es responder preguntas sobre las opiniones de los clientes basándote en datos reales de reseñas.
        
        Puedes:
        1. Proporcionar estadísticas y resúmenes de reseñas
        2. Analizar tendencias y patrones en las opiniones
        3. Identificar los aspectos positivos y negativos mencionados por los clientes
        4. Dar información específica sobre productos por su SKU o nombre
        5. Mostrar información sobre los clientes que han reseñado productos específicos
        
        Mantén tus respuestas concisas, informativas y orientadas a datos.
        Responde siempre en español.
        No inventes información que no esté en los datos proporcionados.
        """
    
    def get_review_stats(self):
        """
        Obtiene estadísticas generales de las reseñas para mostrar en el dashboard
        
        Returns:
            dict: Estadísticas de las reseñas (total, sentimientos, etc.)
        """
        conn = self.db.connect()
        
        if not conn:
            return self._get_default_stats()
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Obtener total de reseñas
            cursor.execute("SELECT COUNT(*) as total FROM review_products")
            total_reviews = cursor.fetchone()['total']
            
            if total_reviews == 0:
                return self._get_default_stats()
            
            # Obtener sentimientos
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN sentiment_score >= 0.6 THEN 1 END) as positive,
                    COUNT(CASE WHEN sentiment_score BETWEEN 0.4 AND 0.6 THEN 1 END) as neutral,
                    COUNT(CASE WHEN sentiment_score < 0.4 AND sentiment_score IS NOT NULL THEN 1 END) as negative,
                    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as unknown
                FROM review_products
            """)
            sentiment_counts = cursor.fetchone()
            
            # Calcular porcentajes
            analyzed_reviews = total_reviews - sentiment_counts['unknown']
            
            if analyzed_reviews > 0:
                positive_percentage = round((sentiment_counts['positive'] / analyzed_reviews) * 100)
                neutral_percentage = round((sentiment_counts['neutral'] / analyzed_reviews) * 100)
                negative_percentage = round((sentiment_counts['negative'] / analyzed_reviews) * 100)
            else:
                positive_percentage = 0
                neutral_percentage = 0
                negative_percentage = 0
            
            # Obtener fecha de última reseña
            cursor.execute("SELECT MAX(created_at) as last_date FROM review_products")
            last_date = cursor.fetchone()['last_date']
            
            if last_date:
                last_review = last_date.strftime("%d/%m/%Y")
            else:
                last_review = "N/A"
            
            return {
                'total_reviews': total_reviews,
                'positive_percentage': positive_percentage,
                'neutral_percentage': neutral_percentage,
                'negative_percentage': negative_percentage,
                'last_review': last_review
            }
        
        except Exception as e:
            print(f"Error al obtener estadísticas de reseñas: {e}")
            return self._get_default_stats()
        
        finally:
            cursor.close()
            self.db.disconnect()
    
    def _get_default_stats(self):
        """Devuelve estadísticas por defecto cuando no hay datos"""
        return {
            'total_reviews': 0,
            'positive_percentage': 0,
            'neutral_percentage': 0,
            'negative_percentage': 0,
            'last_review': "N/A"
        }
    
    def get_context_data(self, query):
        """
        Obtiene datos de contexto basados en la consulta del usuario
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            str: Datos de contexto relevantes para la consulta
        """
        conn = self.db.connect()
        
        if not conn:
            return "No se pudo conectar a la base de datos para obtener información."
        
        cursor = conn.cursor(dictionary=True)
        context_data = []
        
        try:
            # Detectar si la consulta es sobre clientes que han reseñado un producto específico
            if any(word in query.lower() for word in ["quién", "quien", "quienes", "quiénes", "clientes"]) and "reseñado" in query.lower():
                # Intentar extraer el nombre del producto de la consulta
                # Buscar texto entre comillas
                import re
                product_match = re.search(r'"([^"]+)"', query)
                if product_match:
                    product_name = product_match.group(1)
                    
                    # Buscar reseñas del producto específico
                    cursor.execute("""
                        SELECT review_id, product_sku, product_name, title, detail, 
                               nickname, customer_id, created_at, sentiment_score, review_rating
                        FROM review_products
                        WHERE product_name = %s
                    """, (product_name,))
                    
                    product_reviews = cursor.fetchall()
                    
                    if product_reviews:
                        context_data.append(f"Información sobre los clientes que han reseñado '{product_name}':")
                        
                        for review in product_reviews:
                            # Formatear información del cliente
                            client_info = (
                                f"Cliente: {review['nickname']}, "
                                f"Fecha: {review['created_at']}, "
                                f"Título: {review['title']}, "
                                f"Valoración: {review['review_rating'] if review['review_rating'] else 'No disponible'}"
                            )
                            
                            context_data.append(client_info)
                    else:
                        context_data.append(f"No se encontraron reseñas para el producto '{product_name}'.")
            
            # Detectar si la consulta es sobre un producto específico
            elif "sku" in query.lower() or "product" in query.lower() or "biasp" in query.lower():
                # Extraer posibles SKUs o términos de producto
                words = query.split()
                for word in words:
                    # Buscar reseñas que coincidan con posibles SKUs o nombres de productos
                    search_term = f"%{word}%"
                    cursor.execute("""
                        SELECT review_id, product_sku, product_name, title, detail, 
                               nickname, created_at, sentiment_score, review_rating
                        FROM review_products
                        WHERE product_sku LIKE %s OR product_name LIKE %s
                        LIMIT 10
                    """, (search_term, search_term))
                    
                    product_reviews = cursor.fetchall()
                    
                    if product_reviews:
                        context_data.append(f"Información sobre '{word}':")
                        for review in product_reviews:
                            # Obtener ratings asociados
                            cursor.execute("""
                                SELECT rating_code, value 
                                FROM review_ratings 
                                WHERE review_id = %s
                            """, (review['review_id'],))
                            
                            ratings = cursor.fetchall()
                            ratings_text = ", ".join([f"{r['rating_code']}: {r['value']}" for r in ratings])
                            
                            # Formatear reseña
                            review_text = (
                                f"SKU: {review['product_sku']}, "
                                f"Producto: {review['product_name']}, "
                                f"Título: {review['title']}, "
                                f"Detalle: {review['detail']}, "
                                f"Usuario: {review['nickname']}, "
                                f"Fecha: {review['created_at']}, "
                                f"Ratings: {ratings_text}"
                            )
                            
                            context_data.append(review_text)
            
            # Si la consulta es sobre estadísticas generales
            if "total" in query.lower() or "reseñas" in query.lower() or "cuantas" in query.lower():
                cursor.execute("SELECT COUNT(*) as total FROM review_products")
                total = cursor.fetchone()['total']
                context_data.append(f"Total de reseñas: {total}")
                
                # Obtener distribución de sentimientos si existen
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN sentiment_score >= 0.6 THEN 1 END) as positive,
                        COUNT(CASE WHEN sentiment_score BETWEEN 0.4 AND 0.6 THEN 1 END) as neutral,
                        COUNT(CASE WHEN sentiment_score < 0.4 THEN 1 END) as negative
                    FROM review_products
                    WHERE sentiment_score IS NOT NULL
                """)
                sentiments = cursor.fetchone()
                
                if sentiments:
                    context_data.append(
                        f"Distribución de sentimientos: "
                        f"Positivo: {sentiments['positive']}, "
                        f"Neutral: {sentiments['neutral']}, "
                        f"Negativo: {sentiments['negative']}"
                    )
            
            # Si la consulta es sobre productos mejor valorados
            if "mejor" in query.lower() or "valorad" in query.lower():
                cursor.execute("""
                    SELECT product_sku, product_name, AVG(review_rating) as avg_rating, COUNT(*) as review_count
                    FROM review_products
                    WHERE review_rating IS NOT NULL
                    GROUP BY product_sku, product_name
                    ORDER BY avg_rating DESC
                    LIMIT 5
                """)
                
                top_products = cursor.fetchall()
                
                if top_products:
                    context_data.append("Productos mejor valorados:")
                    for prod in top_products:
                        context_data.append(
                            f"Producto: {prod['product_name']}, "
                            f"SKU: {prod['product_sku']}, "
                            f"Valoración media: {round(prod['avg_rating'], 1)}, "
                            f"Número de reseñas: {prod['review_count']}"
                        )
            
            # Si no hay datos específicos, proporcionar información general
            if not context_data:
                # Obtener algunas reseñas recientes
                cursor.execute("""
                    SELECT review_id, product_sku, product_name, title, detail, created_at
                    FROM review_products
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                
                recent_reviews = cursor.fetchall()
                
                if recent_reviews:
                    context_data.append("Reseñas recientes:")
                    for review in recent_reviews:
                        context_data.append(
                            f"Producto: {review['product_name']}, "
                            f"SKU: {review['product_sku']}, "
                            f"Título: {review['title']}, "
                            f"Detalle: {review['detail']}"
                        )
            
            return "\n".join(context_data)
            
        except Exception as e:
            print(f"Error al obtener datos de contexto: {e}")
            return "No se pudieron obtener datos relevantes debido a un error."
            
        finally:
            cursor.close()
            self.db.disconnect()
    
    def process_query(self, user_query):
        """
        Procesa una consulta del usuario y genera una respuesta utilizando Gemini
        
        Args:
            user_query (str): Consulta del usuario
            
        Returns:
            str: Respuesta generada
        """
        try:
            # Obtener datos de contexto relevantes
            context_data = self.get_context_data(user_query)
            
            # Actualizar historial de conversación
            if len(self.conversation_history) > 10:
                # Mantener solo las últimas interacciones para no sobrepasar tokens
                self.conversation_history = self.conversation_history[-10:]
            
            # Construir el mensaje para Gemini
            prompt = f"""
            {self.system_prompt}
            
            Datos de contexto sobre las reseñas:
            {context_data}
            
            Historial de conversación:
            {self._format_conversation_history()}
            
            Consulta del usuario: {user_query}
            """
            
            # Obtener respuesta de Gemini
            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash",  # Usar modelo flash para respuestas rápidas
                contents=prompt
            )
            
            # Extraer la respuesta
            ai_response = response.text
            
            # Añadir a la historia de conversación
            self.conversation_history.append({"role": "user", "content": user_query})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            print(f"Error al procesar consulta con Gemini: {e}")
            return "Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, intenta nuevamente."
    
    def _format_conversation_history(self):
        """Formatea el historial de conversación para incluirlo en el prompt"""
        if not self.conversation_history:
            return "No hay historial de conversación previo."
            
        formatted_history = []
        for message in self.conversation_history:
            role = "Usuario" if message["role"] == "user" else "Asistente"
            formatted_history.append(f"{role}: {message['content']}")
            
        return "\n".join(formatted_history) 