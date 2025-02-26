from services.openai_service import OpenAIService
from services.magento_service import MagentoService
from services.hana_service import HanaService
from services.database_service import ProductService
import json
import time
from datetime import datetime

class MetaKeywordsController:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.magento_service = MagentoService()
        self.hana_service = HanaService()
        self.product_service = ProductService()

    def run_meta_keywords_service(self):
        """
        Ejecuta el servicio de generación de meta keywords para productos
        """
        # Obtener productos pendientes de meta keywords
        pending_products = self.product_service.get_pending_meta_keywords_products()
        
        if not pending_products:
            print("✨ No hay productos pendientes por procesar meta keywords")
            return
        
        for product in pending_products:
            try:
                print(f"🔄 Procesando meta keywords para producto {product['sku']} - {datetime.now()}")
                
                # Parsear los atributos
                attributes = json.loads(f"[{product['attributes']}]")
                product_data = {
                    'name': product['name'],
                    'type_id': product['type_id'],
                    'attributes': attributes
                }

                # Generar meta keywords con OpenAI
                meta_keywords = self.openai_service.generate_meta_keywords(product_data)

                # Actualizar en Magento
                magento_success = self.magento_service.update_product_meta_keywords(product['sku'], meta_keywords)
                
                # Actualizar en SAP HANA
                hana_success = self.hana_service.update_meta_keywords(product['sku'], meta_keywords)

                if magento_success and hana_success:
                    # Actualizar estado en base de datos local
                    self.product_service.update_product_meta_keywords(product['id'], meta_keywords)
                    print(f"✅ Meta keywords actualizados para producto {product['sku']}")
                else:
                    print(f"❌ Error actualizando meta keywords para producto {product['sku']}")

            except Exception as e:
                print(f"❌ Error procesando meta keywords para producto {product['sku']}: {str(e)}")
            
            # Esperar 15 segundos antes de procesar el siguiente producto
            time.sleep(15)