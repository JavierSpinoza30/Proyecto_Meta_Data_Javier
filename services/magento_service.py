import requests
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

class MagentoService:
    def __init__(self):
        # Obtener las variables de entorno
        self.base_url = os.getenv('MAGENTO_API_URL')
        self.token = os.getenv('MAGENTO_API_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def update_product_description(self, sku, description):
        """
        Actualiza la descripción del producto en Magento
        """
        endpoint = f"{self.base_url}/rest/all/V1/products/{sku}"
        payload = {
            'product': {
                'custom_attributes': [
                    {
                        'attribute_code': 'description',
                        'value': description
                    }
                ]
            }
        }

        response = requests.put(endpoint, json=payload, headers=self.headers)
        return response.status_code == 200

    def update_product_meta_keywords(self, sku, meta_keywords):
        """
        Actualiza los meta keywords del producto en Magento
        """
        endpoint = f"{self.base_url}/rest/all/V1/products/{sku}"
        payload = {
            'product': {
                'custom_attributes': [
                    {
                        'attribute_code': 'meta_keyword',
                        'value': meta_keywords
                    }
                ]
            }
        }

        response = requests.put(endpoint, json=payload, headers=self.headers)
        return response.status_code == 200

    def update_product_meta_title(self, sku, meta_title):
        """
        Actualiza el meta title del producto en Magento
        """
        endpoint = f"{self.base_url}/rest/all/V1/products/{sku}"
        payload = {
            'product': {
                'custom_attributes': [
                    {
                        'attribute_code': 'meta_title',
                        'value': meta_title
                    }
                ]
            }
        }

        response = requests.put(endpoint, json=payload, headers=self.headers)
        return response.status_code == 200
