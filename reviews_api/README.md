# Importador de Reseñas de Productos

Este módulo permite importar reseñas de productos desde la API de Magento y guardarlas en la base de datos para su posterior análisis.

## Estructura de archivos

- `api_client.py`: Cliente para consumir la API de reseñas de Magento
- `data_processor.py`: Procesador para guardar los datos en la base de datos
- `main.py`: Script principal para ejecutar la importación

## Requisitos

- Python 3.6 o superior
- MySQL/MariaDB
- Acceso a la API de Magento con token válido

## Configuración

Las credenciales de conexión y tokens de API deben estar configurados en el archivo `.env` en la raíz del proyecto:

```
# Conexión a la base de datos
DB_HOST=localhost
DB_USER=usuario
DB_PASSWORD=contraseña
DB_NAME=nombre_db
DB_PORT=3306

# API de Magento para reseñas
MAGENTO_API_REVIEW_URL=https://url-de-magento.com
MAGENTO_API_REVIEW_TOKEN=token-de-api
```

## Uso

Para ejecutar la importación de reseñas:

```bash
python reviews_api/main.py
```

Opciones disponibles:

- `--page-size`: Número de reseñas por página (default: 100)
- `--max-pages`: Número máximo de páginas a procesar (0 = todas, default: 0)

Ejemplos:

```bash
# Importar todas las reseñas
python reviews_api/main.py

# Importar solo 50 reseñas por página, máximo 2 páginas
python reviews_api/main.py --page-size 50 --max-pages 2
```

## Estructura de la base de datos

Las reseñas se guardan en dos tablas:

1. `review_products`: Almacena la información principal de las reseñas
2. `review_ratings`: Almacena las calificaciones asociadas a cada reseña

## Proceso de importación

1. Conexión a la API de Magento
2. Obtención de reseñas paginadas
3. Procesamiento y almacenamiento en la base de datos
4. Generación de informe de resultados 