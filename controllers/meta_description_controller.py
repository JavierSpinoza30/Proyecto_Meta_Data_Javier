from services.gemini_service import GeminiService
from services.magento_service import MagentoService
from services.hana_service import HanaService
from services.database_service import ProductService
import json
import time
from datetime import datetime

class MetaDescriptionController:
    def __init__(self):
        # Inicializar servicios necesarios
        self.gemini_service = GeminiService()
        self.magento_service = MagentoService()
        self.hana_service = HanaService()
        self.product_service = ProductService()

    def validate_meta_description(self, meta_description):
        """
        Valida que la meta descripción cumpla con los requisitos:
        - Entre 100 y 160 caracteres incluyendo espacios
        """
        if not meta_description:
            return False
            
        length = len(meta_description)
        # Verificar si la longitud está entre 100 y 160 caracteres
        if 100 <= length <= 160:
            return True
        
        print(f"⚠️ Meta descripción rechazada - Longitud: {length} (debe estar entre 100-160 caracteres)")
        return False

    def run_meta_description_service(self):
        """
        Ejecuta el servicio de generación de meta descriptions para productos
        """
        # Obtener productos pendientes de meta descripción
        pending_products = self.product_service.get_pending_meta_description_products()
        
        if not pending_products:
            print("✨ No hay productos pendientes por procesar meta descripción")
            return
        
        for product in pending_products:
            try:
                print(f"🔄 Procesando meta descripción para producto {product['sku']} - {datetime.now()}")
                
                # Parsear los atributos
                attributes = []
                if product['attributes']:
                    attributes = json.loads(f"[{product['attributes']}]")
                
                # Preparar datos del producto incluyendo categoría
                product_data = {
                    'name': product['name'],
                    'type_id': product['type_id'],
                    'attributes': attributes
                }
                
                # Añadir categoría si está disponible
                if 'category' in product and product['category']:
                    product_data['category'] = product['category']
                    print(f"📂 Categorías del producto: {product['category']}")
                else:
                    print("⚠️ Este producto no tiene categorías asignadas")

                # Generar meta descripción con Gemini
                meta_description = self.gemini_service.generate_meta_description(product_data)

                # Validar longitud de la meta descripción
                if not self.validate_meta_description(meta_description):
                    print(f"⚠️ Meta descripción no cumple con los requisitos para producto {product['sku']} - Longitud: {len(meta_description)}")
                    continue

                # Actualizar en Magento
                magento_success = self.magento_service.update_product_meta_description(product['sku'], meta_description)
                
                # Actualizar en SAP HANA
                hana_success = self.hana_service.update_meta_description(product['sku'], meta_description)

                if magento_success and hana_success:
                    # Actualizar estado en base de datos local
                    self.product_service.update_product_meta_description(product['id'], meta_description)
                    print(f"✅ Meta descripción actualizada para producto {product['sku']}")
                else:
                    print(f"❌ Error actualizando meta descripción para producto {product['sku']}")

            except Exception as e:
                print(f"❌ Error procesando meta descripción para producto {product['sku']}: {str(e)}")
            
            # Esperar 5 segundos antes de procesar el siguiente producto
            time.sleep(5)
