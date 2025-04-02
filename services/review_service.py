import requests
import json
import os
from dotenv import load_dotenv
import time
from google import genai

# Cargar variables de entorno
load_dotenv()

class ReviewService:
    def __init__(self):
        # Configuración de API de Magento para reviews
        self.api_url = os.getenv('MAGENTO_API_REVIEW_URL')
        self.api_token = os.getenv('MAGENTO_API_REVIEW_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Inicializar cliente de Google Gemini
        self.gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Estados de reviews
        self.APPROVED = 1
        self.PENDING = 2
        self.NOT_APPROVED = 3
        self.PENDING_HUMAN_REVIEW = 4
        
    def get_pending_reviews(self):
        """Obtiene todas las reviews en estado pendiente"""
        try:
            endpoint = f"{self.api_url}/rest/all/V1/reviews/status/{self.PENDING}"
            print(f"🔍 Consultando reviews pendientes en: {endpoint}")
            
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                # Obtener el texto crudo de la respuesta para depuración
                raw_response = response.text
                print(f"📝 Respuesta cruda de la API: {raw_response}")
                
                # Verificar si la respuesta es una lista o un diccionario
                try:
                    data = response.json()
                except Exception as e:
                    print(f"❌ Error al convertir la respuesta a JSON: {str(e)}")
                    print(f"📝 Contenido de la respuesta: {raw_response}")
                    return []
                
                # Estructura de Magento: Verificar si hay una clave 'items'
                if isinstance(data, dict) and 'items' in data:
                    print(f"✅ Respuesta con estructura de Magento con {len(data['items'])} reviews en 'items'")
                    return data['items']
                
                # Si la respuesta es un string, puede ser "[]" vacío
                if isinstance(data, str):
                    print(f"🔍 La respuesta es un string: '{data}'")
                    if data.strip() == "[]" or not data.strip():
                        return []
                    # Intentar convertir el string a JSON si es posible
                    try:
                        parsed_data = json.loads(data)
                        print(f"✅ String convertido a JSON: {type(parsed_data)}")
                        
                        # Verificar si hay una clave 'items' en el JSON parseado
                        if isinstance(parsed_data, dict) and 'items' in parsed_data:
                            return parsed_data['items']
                        
                        if isinstance(parsed_data, list):
                            return parsed_data
                        else:
                            # Si es un único objeto, lo convertimos a lista
                            return [parsed_data]
                    except:
                        print(f"❌ La API devolvió un string que no se puede convertir a JSON: {data}")
                        # Intentar procesarlo como una review individual
                        if '"review_id"' in data:
                            print("🔍 Se encontró 'review_id' en el string, intentando procesarlo como review individual")
                            return [{"raw_data": data}]
                        return []
                
                # Si la respuesta ya es una lista, la devolvemos directamente
                if isinstance(data, list):
                    print(f"✅ La respuesta es una lista con {len(data)} elementos")
                    # Verificar contenido de la lista para depuración
                    for i, item in enumerate(data):
                        print(f"📋 Review #{i+1}: {item}")
                    return data
                
                # Si es un único objeto, lo convertimos a lista
                if isinstance(data, dict):
                    print(f"✅ La respuesta es un objeto individual: {data}")
                    return [data]
                
                # Si no es ninguno de los tipos esperados
                print(f"❌ Formato de respuesta inesperado: {type(data)}")
                # Intentar procesar como dato crudo
                return [{"raw_data": raw_response}]
            else:
                print(f"❌ Error al obtener reviews pendientes: {response.status_code}")
                print(response.text)
                return []
                
        except Exception as e:
            print(f"❌ Error en la conexión a la API de reviews: {str(e)}")
            return []
            
    def update_review_status(self, review_id, status_id):
        """Actualiza el estado de una review"""
        try:
            endpoint = f"{self.api_url}/rest/all/V1/reviews/{review_id}/status"
            data = {"statusId": status_id}
            
            print(f"🔄 Enviando actualización a: {endpoint}")
            print(f"📝 Datos: {data}")
            
            # Usar PUT que es el método correcto para esta API
            response = requests.put(
                endpoint, 
                headers=self.headers, 
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                print(f"✅ Review {review_id} actualizada a estado {status_id}")
                return True
            # Si falla con la ruta /rest/all/V1, intentar con /rest/V1
            elif response.status_code == 404:
                print("⚠️ Primera ruta no encontrada, probando alternativa...")
                alternative_endpoint = f"{self.api_url}/rest/V1/reviews/{review_id}/status"
                
                response = requests.put(
                    alternative_endpoint, 
                    headers=self.headers, 
                    data=json.dumps(data)
                )
                
                if response.status_code == 200:
                    print(f"✅ Review {review_id} actualizada a estado {status_id} (ruta alternativa)")
                    return True
                else:
                    print(f"❌ Error al actualizar review {review_id} (ruta alternativa): {response.status_code}")
                    print(f"📝 Respuesta: {response.text}")
                    return False
            else:
                print(f"❌ Error al actualizar review {review_id}: {response.status_code}")
                print(f"📝 Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en la conexión a la API de reviews: {str(e)}")
            return False
            
    def extract_review_id(self, review_data):
        """
        Extrae el ID de la review de diferentes formatos posibles
        """
        # Si es un diccionario normal
        if isinstance(review_data, dict):
            if 'review_id' in review_data:
                return review_data.get('review_id')
            # Buscar en otras claves posibles
            keys_to_check = ['reviewId', 'id', 'review', 'reviewid']
            for key in keys_to_check:
                if key in review_data:
                    return review_data.get(key)
        
        # Si es un string que parece contener un ID
        if isinstance(review_data, str):
            # Buscar patrones como "review_id": 123
            import re
            id_patterns = [
                r'"review_id"\s*:\s*(\d+)',
                r'"reviewId"\s*:\s*(\d+)',
                r'"id"\s*:\s*(\d+)',
                r'review_id=(\d+)',
                r'reviewId=(\d+)'
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, review_data)
                if match:
                    return int(match.group(1))
        
        # Si tiene raw_data, intentar extraer ID de ahí
        if isinstance(review_data, dict) and 'raw_data' in review_data:
            return self.extract_review_id(review_data['raw_data'])
            
        return None
            
    def evaluate_review_content(self, review):
        """
        Evalúa el contenido de una review usando IA para determinar si contiene
        contenido inapropiado (groserías, palabras ofensivas, etc.)
        """
        try:
            # Extraer el contenido de la review para evaluar
            title = ''
            detail = ''
            nickname = ''
            
            # Si es un diccionario, intentar extraer directamente
            if isinstance(review, dict):
                title = review.get('title', '')
                detail = review.get('detail', '')
                nickname = review.get('nickname', '')
                
                # Si tiene raw_data, intentar extraer de ahí también
                if 'raw_data' in review and not (title or detail):
                    raw_data = review['raw_data']
                    # Intentar extraer del raw_data
                    import re
                    title_match = re.search(r'"title"\s*:\s*"([^"]*)"', raw_data)
                    detail_match = re.search(r'"detail"\s*:\s*"([^"]*)"', raw_data)
                    nickname_match = re.search(r'"nickname"\s*:\s*"([^"]*)"', raw_data)
                    
                    if title_match:
                        title = title_match.group(1)
                    if detail_match:
                        detail = detail_match.group(1)
                    if nickname_match:
                        nickname = nickname_match.group(1)
            
            # Si es un string, intentar extraer mediante regex
            elif isinstance(review, str):
                import re
                title_match = re.search(r'"title"\s*:\s*"([^"]*)"', review)
                detail_match = re.search(r'"detail"\s*:\s*"([^"]*)"', review)
                nickname_match = re.search(r'"nickname"\s*:\s*"([^"]*)"', review)
                
                if title_match:
                    title = title_match.group(1)
                if detail_match:
                    detail = detail_match.group(1)
                if nickname_match:
                    nickname = nickname_match.group(1)
            
            print(f"📝 Datos extraídos para evaluación - Título: '{title}', Detalle: '{detail}', Autor: '{nickname}'")
            
            # Si no tenemos datos suficientes, enviar a revisión humana
            if not title and not detail:
                print("⚠️ Review sin título ni contenido, enviando a revisión humana")
                return self.PENDING_HUMAN_REVIEW
            
            # Prompt para Gemini
            prompt = f"""
            Evalúa la siguiente reseña de producto para determinar si contiene lenguaje inapropiado, 
            groserías, insultos, contenido ofensivo, spam o información irrelevante al producto.
            
            Título de la reseña: "{title}"
            Contenido: "{detail}"
            Autor: "{nickname}"
            
            Clasifica esta reseña como una de las siguientes opciones:
            1. APROBAR - No contiene contenido inapropiado y es relevante como reseña de producto
            2. REVISAR MANUALMENTE - Contiene posible contenido inapropiado o es spam
            
            Responde solo con "APROBAR" o "REVISAR MANUALMENTE".
            """
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt
            )
            
            result = response.text.strip()
            print(f"🤖 Decisión de IA: {result}")
            
            if "APROBAR" in result:
                return self.APPROVED
            else:
                return self.PENDING_HUMAN_REVIEW
                
        except Exception as e:
            print(f"❌ Error al evaluar review con IA: {str(e)}")
            # Si hay error, enviamos a revisión humana por seguridad
            return self.PENDING_HUMAN_REVIEW
            
    def process_pending_reviews(self):
        """Procesa todas las reviews pendientes"""
        pending_reviews = self.get_pending_reviews()
        
        if not pending_reviews:
            print("✨ No hay reviews pendientes para procesar")
            return
            
        print(f"🔄 Procesando {len(pending_reviews)} reviews pendientes...")
        
        for i, review in enumerate(pending_reviews):
            try:
                print(f"\n📋 Procesando review #{i+1}:")
                print(f"📝 Datos crudos: {review}")
                
                # Extraer ID de la review usando métodos robustos
                review_id = self.extract_review_id(review)
                
                # Si no encontramos ID válido
                if not review_id:
                    # Imprimir todo el objeto para diagnóstico
                    print(f"❌ No se pudo extraer ID de: {json.dumps(review, indent=2) if isinstance(review, dict) else review}")
                    print("❌ Review sin ID válido, omitiendo")
                    continue
                    
                print(f"🔄 Evaluando review #{review_id}")
                
                # Evaluar contenido con IA
                new_status = self.evaluate_review_content(review)
                
                # Actualizar estado
                status_text = "aprobada" if new_status == self.APPROVED else "enviada a revisión humana"
                if self.update_review_status(review_id, new_status):
                    print(f"✅ Review #{review_id} {status_text}")
                else:
                    print(f"❌ Error al actualizar review #{review_id}")
                    
                # Pequeña pausa para no sobrecargar la API
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error procesando review: {str(e)}")
                import traceback
                traceback.print_exc()
                
        print("✅ Procesamiento de reviews completado")

# Para pruebas
if __name__ == "__main__":
    service = ReviewService()
    service.process_pending_reviews() 