from services.openai_service import OpenAIService
from services.magento_service import MagentoService
from services.database_service import ProductService
import json
import time
from datetime import datetime

class DescriptionController:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.magento_service = MagentoService()
        self.product_service = ProductService()

    def run_description_service(self):
        """
        Ejecuta el servicio de descripción de productos
        """
        # Obtener productos pendientes
        pending_products = self.product_service.get_pending_products()
        
        if not pending_products:
            print("✨ No hay productos pendientes por procesar")
            return
        
        for product in pending_products:
            try:
                print(f"🔄 Procesando producto {product['sku']} - {datetime.now()}")
                
                # Parsear los atributos
                attributes = json.loads(f"[{product['attributes']}]")
                product_data = {
                    'name': product['name'],
                    'type_id': product['type_id'],
                    'attributes': attributes
                }

                # Generar descripción con OpenAI
                description = self.openai_service.generate_product_description(product_data)

                # Actualizar en Magento
                if self.magento_service.update_product_description(product['sku'], description):
                    # Limpiar descripción para la base de datos (quitar comillas)
                    db_description = description.replace('"', "'")
                    self.product_service.update_product_description(product['id'], db_description)
                    print(f"✅ Producto {product['sku']} actualizado exitosamente")
                else:
                    print(f"❌ Error actualizando producto {product['sku']} en Magento")

            except Exception as e:
                print(f"❌ Error procesando producto {product['sku']}: {str(e)}")
            
            # Esperar 15 segundos antes de procesar el siguiente producto
            time.sleep(15)

    # para que funcione el boton de forma manual
    # def process_pending_descriptions(self):
    #     """
    #     Procesa todos los productos pendientes
    #     """
    #     # Obtener productos pendientes
    #     pending_products = self.product_service.get_pending_products()
        
    #     for product in pending_products:
    #         try:
    #             # Parsear los atributos
    #             attributes = json.loads(f"[{product['attributes']}]")
    #             product_data = {
    #                 'name': product['name'],
    #                 'type_id': product['type_id'],
    #                 'attributes': attributes
    #             }

    #             # Generar descripción con OpenAI
    #             description = self.openai_service.generate_product_description(product_data)

    #             # Actualizar en Magento
    #             if self.magento_service.update_product_description(product['sku'], description):
    #                 # Actualizar en la base de datos local
    #                 self.product_service.update_product_description(product['id'], description)
    #                 print(f"✅ Producto {product['sku']} actualizado exitosamente")
    #             else:
    #                 print(f"❌ Error actualizando producto {product['sku']} en Magento")

    #         except Exception as e:
    #             print(f"❌ Error procesando producto {product['sku']}: {str(e)}") 