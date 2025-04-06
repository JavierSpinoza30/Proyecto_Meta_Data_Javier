from services.gemini_service import GeminiService
from services.magento_service import MagentoService
from services.hana_service import HanaService
from services.database_service import ProductService
import json
import time
from datetime import datetime

class MetaTitleController:
    def __init__(self):
        # Inicializar servicios necesarios
        self.gemini_service = GeminiService()
        self.magento_service = MagentoService()
        self.hana_service = HanaService()
        self.product_service = ProductService()

    def validate_meta_title(self, meta_title):
        """
        Valida que el meta title cumpla con los requisitos
        """
        # Validar longitud máxima de 60 caracteres incluyendo espacios
        if len(meta_title) > 60:
            return False
        return True

    def run_meta_title_service(self):
        """
        Ejecuta el servicio de generación de meta titles para productos
        """
        # Obtener productos pendientes de meta title
        pending_products = self.product_service.get_pending_meta_title_products()
        
        if not pending_products:
            print("✨ No hay productos pendientes por procesar meta title")
            return
        
        for product in pending_products:
            try:
                print(f"🔄 Procesando meta title para producto {product['sku']} - {datetime.now()}")
                
                # Parsear los atributos
                attributes = json.loads(f"[{product['attributes']}]")
                product_data = {
                    'name': product['name'],
                    'type_id': product['type_id'],
                    'attributes': attributes
                }

                # Generar meta title con Gemini
                meta_title = self.gemini_service.generate_meta_title(product_data)

                # Validar longitud del meta title
                if not self.validate_meta_title(meta_title):
                    print(f"⚠️ Meta title excede 60 caracteres para producto {product['sku']} - Longitud: {len(meta_title)}")
                    continue

                # Actualizar en Magento
                magento_success = self.magento_service.update_product_meta_title(product['sku'], meta_title)
                
                # Actualizar en SAP HANA
                hana_success = self.hana_service.update_meta_title(product['sku'], meta_title)

                if magento_success and hana_success:
                    # Actualizar estado en base de datos local
                    self.product_service.update_product_meta_title(product['id'], meta_title)
                    print(f"✅ Meta title actualizado para producto {product['sku']}")
                else:
                    print(f"❌ Error actualizando meta title para producto {product['sku']}")

            except Exception as e:
                print(f"❌ Error procesando meta title para producto {product['sku']}: {str(e)}")
            
            # Esperar 5 segundos antes de procesar el siguiente producto
            time.sleep(5) 