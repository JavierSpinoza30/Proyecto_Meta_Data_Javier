#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime

# Agregar el directorio base al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import ReviewsApiClient
from data_processor import ReviewDataProcessor

def main():
    """Función principal para ejecutar la importación de reseñas"""
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Importador de reseñas desde la API de Magento')
    parser.add_argument('--page-size', type=int, default=100, help='Número de reseñas por página')
    parser.add_argument('--max-pages', type=int, default=0, help='Número máximo de páginas a procesar (0 = todas)')
    args = parser.parse_args()
    
    print(f"=== Iniciando importación de reseñas ===")
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Inicializar cliente de API
    api_client = ReviewsApiClient()
    
    # Obtener reseñas
    print(f"Obteniendo reseñas desde la API...")
    
    if args.max_pages > 0:
        # Obtener un número limitado de páginas
        all_reviews = []
        for page in range(1, args.max_pages + 1):
            print(f"Obteniendo página {page}...")
            response = api_client.get_reviews(args.page_size, page)
            
            if not response or 'items' not in response:
                print(f"No se encontraron más reseñas o hubo un error")
                break
                
            items = response.get('items', [])
            all_reviews.extend(items)
            
            # Verificar si hay más páginas
            total_count = response.get('total_count', 0)
            if len(all_reviews) >= total_count:
                print(f"Se han obtenido todas las reseñas disponibles")
                break
    else:
        # Obtener todas las reseñas
        print(f"Obteniendo todas las reseñas disponibles...")
        all_reviews = api_client.get_all_reviews()
    
    print(f"Se encontraron {len(all_reviews)} reseñas")
    
    if not all_reviews:
        print("No hay reseñas para procesar")
        return
    
    # Procesar y guardar las reseñas en la base de datos
    print(f"Guardando reseñas en la base de datos...")
    processor = ReviewDataProcessor()
    result = processor.process_reviews(all_reviews)
    
    # Mostrar resultados
    print("\n=== Resultado de la importación ===")
    print(f"Total de reseñas procesadas: {result.get('total', 0)}")
    print(f"Reseñas insertadas/actualizadas: {result.get('inserted', 0)}")
    print(f"Errores: {result.get('errors', 0)}")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
if __name__ == "__main__":
    main() 