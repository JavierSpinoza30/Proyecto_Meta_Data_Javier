from google import genai
import os
from dotenv import load_dotenv
from database import DatabaseConnection
import json
import time
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

class ReviewSentimentAnalyzer:
    """Servicio para analizar el sentimiento y extraer información relevante de las reviews usando IA"""
    
    def __init__(self):
        """Inicializar el servicio de análisis de sentimientos"""
        # Inicializar cliente de Google Gemini
        self.gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.db = DatabaseConnection()
        
    def get_unprocessed_reviews(self, limit=20):
        """
        Obtiene las reviews que aún no han sido analizadas por IA
        
        Args:
            limit (int): Límite de reviews a procesar en cada lote
            
        Returns:
            list: Lista de reviews pendientes de análisis
        """
        connection = self.db.connect()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT id, review_id, title, detail, nickname, product_name, product_sku
                FROM review_products
                WHERE processed_at IS NULL
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
            
    def analyze_review(self, review):
        """
        Analiza una review usando IA para extraer sentimiento, palabras clave, resumen y temas
        
        Args:
            review (dict): Datos de la review a analizar
            
        Returns:
            dict: Resultados del análisis (sentiment_score, keywords, ai_summary, topics)
        """
        try:
            # Extraer el contenido de la review para evaluar
            title = review.get('title', '')
            detail = review.get('detail', '')
            nickname = review.get('nickname', '')
            product_name = review.get('product_name', '')
            
            # Texto combinado para análisis
            review_text = f"{title}. {detail}"
            
            if not review_text.strip():
                print(f"⚠️ Review #{review['review_id']} sin contenido para analizar")
                return None
                
            # Prompt para Gemini
            prompt = f"""
            Analiza esta reseña de producto y extrae la siguiente información:
            
            Producto: "{product_name}"
            Título de la reseña: "{title}"
            Contenido: "{detail}"
            Autor: "{nickname}"
            
            Responde en formato JSON con los siguientes campos:
            1. sentiment_score: un valor entre 0 y 1 donde 0 es muy negativo, 0.5 es neutro y 1 es muy positivo
            2. keywords: una lista de palabras clave relevantes (máximo 5) separadas por comas
            3. ai_summary: un breve resumen de la reseña en una sola frase (máximo 100 caracteres)
            4. topics: temas principales mencionados en la reseña (ej: "calidad,durabilidad,precio")
            
            Devuelve solo el objeto JSON, nada más.
            """
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt
            )
            
            result = response.text.strip()
            
            # Extraer JSON de la respuesta
            try:
                import re
                # Buscar patrón JSON en caso de que Gemini agregue texto adicional
                json_pattern = r'\{.*\}'
                json_match = re.search(json_pattern, result, re.DOTALL)
                
                if json_match:
                    result = json_match.group(0)
                    
                analysis = json.loads(result)
                print(f"✅ Análisis completado para review #{review['review_id']}")
                return analysis
            except json.JSONDecodeError as e:
                print(f"❌ Error al decodificar JSON para review #{review['review_id']}: {e}")
                print(f"Respuesta: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error al analizar review #{review['review_id']}: {str(e)}")
            return None
            
    def save_analysis_results(self, review_id, analysis):
        """
        Guarda los resultados del análisis en la base de datos
        
        Args:
            review_id (int): ID de la review en la tabla review_products
            analysis (dict): Resultados del análisis
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        if not analysis:
            return False
            
        connection = self.db.connect()
        cursor = connection.cursor()
        
        try:
            # Asegurarse de que keywords y topics sean strings
            keywords = analysis.get('keywords', '')
            topics = analysis.get('topics', '')
            
            # Convertir a string si son listas
            if isinstance(keywords, list):
                keywords = ','.join(keywords)
                
            if isinstance(topics, list):
                topics = ','.join(topics)
                
            query = """
                UPDATE review_products 
                SET 
                    sentiment_score = %s,
                    keywords = %s,
                    ai_summary = %s,
                    topics = %s,
                    processed_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (
                analysis.get('sentiment_score'),
                keywords,
                analysis.get('ai_summary'),
                topics,
                review_id
            ))
            connection.commit()
            print(f"✅ Resultados guardados para review #{review_id}")
            return True
        except Exception as e:
            print(f"❌ Error al guardar análisis para review #{review_id}: {str(e)}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()
            
    def process_pending_reviews(self, batch_size=20):
        """
        Procesa un lote de reviews pendientes de análisis
        
        Args:
            batch_size (int): Cantidad de reviews a procesar en cada lote
            
        Returns:
            dict: Estadísticas del procesamiento
        """
        stats = {
            "processed": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
        # Obtener reviews pendientes
        reviews = self.get_unprocessed_reviews(limit=batch_size)
        
        if not reviews:
            print("✨ No hay reviews pendientes para analizar")
            return stats
            
        print(f"🔄 Procesando {len(reviews)} reviews pendientes...")
        
        for review in reviews:
            try:
                # Analizar review
                analysis = self.analyze_review(review)
                
                # Guardar resultados
                if analysis and self.save_analysis_results(review['id'], analysis):
                    stats["processed"] += 1
                else:
                    stats["errors"] += 1
                    
                # Pausa para no sobrecargar la API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error procesando review #{review['id']}: {str(e)}")
                stats["errors"] += 1
                
        stats["end_time"] = datetime.now()
        stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        
        print(f"✅ Procesamiento completado: {stats['processed']} reviews analizadas, {stats['errors']} errores")
        return stats

# Para pruebas
if __name__ == "__main__":
    analyzer = ReviewSentimentAnalyzer()
    stats = analyzer.process_pending_reviews()
    print(f"Estadísticas: {stats}") 