from attribute_service import AttributeService
from product_service import ProductService
from controllers.description_controller import DescriptionController
from controllers.meta_keywords_controller import MetaKeywordsController
from controllers.meta_title_controller import MetaTitleController
from Categories.category_products_service import CategoryProductsService
from Categories.categoty_update_products import UpdateProductCategories
from database import DatabaseConnection
from datetime import datetime, timedelta

def should_truncate(connection):
    """Verifica si ha pasado más de un día desde el último TRUNCATE."""
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT last_truncate FROM execution_log ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()

    if result and result["last_truncate"]:
        last_truncate = result["last_truncate"]
        diferencia = datetime.now() - last_truncate
        return diferencia > timedelta(days=10)  # Solo truncar si han pasado más de 10 días

    return True  # Si no hay registros, hacer el TRUNCATE

def log_execution(connection, truncate=False):
    """Registra la última ejecución y opcionalmente la del TRUNCATE."""
    cursor = connection.cursor()

    now = datetime.now()

    if truncate:
        # Si se hizo el TRUNCATE, se guarda la fecha en ambos campos
        cursor.execute("INSERT INTO execution_log (last_execution, last_truncate) VALUES (%s, %s)", (now, now))
    else:
        # Obtener la última fecha de TRUNCATE
        cursor.execute("SELECT last_truncate FROM execution_log ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()  # Consumimos correctamente el resultado
        last_truncate = result[0] if result else None  # Si no hay registros, asignamos None

        # Insertar la ejecución sin modificar last_truncate
        cursor.execute("INSERT INTO execution_log (last_execution, last_truncate) VALUES (%s, %s)", (now, last_truncate))

    connection.commit()
    cursor.close()

def truncate_tables(connection):
    """Ejecuta el TRUNCATE en las tablas indicadas."""
    cursor = connection.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE attribute_values;")
    cursor.execute("TRUNCATE TABLE products;")
    cursor.execute("TRUNCATE TABLE attributes_products;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    connection.commit()
    cursor.close()
    print("\n🔄 Tablas truncadas exitosamente.")

def main():
    db = DatabaseConnection()
    connection = db.connect()

    if connection:
        # Verificar si es necesario truncar las tablas
        if should_truncate(connection):
            truncate_tables(connection)
            log_execution(connection, truncate=True)
        else:
            log_execution(connection, truncate=False)

        db.disconnect()

    # Procesamiento de atributos
    # print("Procesando atributos...")
    # attribute_service = AttributeService()
    # attribute_service.process_all_attributes()

    # Procesamiento de productos y crear relacion con atributos
    # print("\nProcesando productos...")
    # product_service = ProductService()
    # product_service.save_to_database()

    # Procesamiento de categorías de productos
    # print("\n🚀 Iniciando servicio de categorías de productos...")
    # category_service = CategoryProductsService()
    # try:
    #     category_service.save_category_products_to_db()
    # except KeyboardInterrupt:
    #     print("\n👋 Servicio de categorías detenido por el usuario")

    # Procesamiento de asignar categorías a los productos
    print("\n🚀 Iniciando servicio de asignar categorías a los productos...")
    try:
        UpdateProductCategories()
    except KeyboardInterrupt:
        print("\n👋 Servicio de asignar categorías a los productos detenido por el usuario")

    # Servicio de meta keywords de productos
    # print("\n🚀 Iniciando servicio de meta keywords de productos...")
    # meta_keywords_controller = MetaKeywordsController()
    # try:
    #     meta_keywords_controller.run_meta_keywords_service()
    # except KeyboardInterrupt:
    #     print("\n👋 Servicio de meta keywords detenido por el usuario")

    # Servicio de meta titles de productos
    # print("\n🚀 Iniciando servicio de meta titles de productos...")
    # meta_title_controller = MetaTitleController()
    # try:
    #     meta_title_controller.run_meta_title_service()
    # except KeyboardInterrupt:
    #     print("\n👋 Servicio de meta titles detenido por el usuario")

    # # Servicio de descripción de productos
    # print("\n🚀 Iniciando servicio de descripción de productos...")
    # description_controller = DescriptionController()
    # try:
    #     description_controller.run_description_service()
    # except KeyboardInterrupt:
    #     print("\n👋 Servicio de descripción detenido por el usuario")

    print("\nProceso completado!")

if __name__ == "__main__":
    main()
