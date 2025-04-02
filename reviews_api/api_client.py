import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ReviewsApiClient:
    """Cliente para la API de reseñas de Magento"""
    
    def __init__(self):
        """Inicializar cliente con la configuración del .env"""
        self.api_url = os.getenv('MAGENTO_API_REVIEW_URL')
        self.api_token = os.getenv('MAGENTO_API_REVIEW_TOKEN')
        self.base_url = f"{self.api_url}/rest/all/V1"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def get_reviews(self, page_size=100, current_page=1):
        """
        Obtener reseñas desde la API de Magento
        
        Args:
            page_size (int): Número de reseñas por página
            current_page (int): Página actual
            
        Returns:
            dict: Respuesta de la API con las reseñas
        """
        endpoint = f"/reviews"
        params = {
            'searchCriteria[pageSize]': page_size,
            'searchCriteria[currentPage]': current_page
        }
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}", 
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error en la API: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error al conectar con la API: {e}")
            return None
    
    def get_all_reviews(self):
        """
        Obtener todas las reseñas paginando automáticamente
        
        Returns:
            list: Lista de todas las reseñas
        """
        all_reviews = []
        current_page = 1
        page_size = 100
        
        while True:
            response = self.get_reviews(page_size, current_page)
            
            if not response or 'items' not in response:
                break
                
            items = response.get('items', [])
            all_reviews.extend(items)
            
            # Verificar si hay más páginas
            total_count = response.get('total_count', 0)
            if len(all_reviews) >= total_count:
                break
                
            current_page += 1
        
        return all_reviews 