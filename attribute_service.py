import requests
from database import DatabaseConnection
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import logging
import os
from dotenv import load_dotenv
from magento_connection import MagentoConnection

class AttributeService:
    def __init__(self, max_workers=4):
        # Cargar variables de entorno desde .env
        load_dotenv()
        
        self.magento = MagentoConnection()
        self.max_workers = max_workers
        self.db_lock = Lock()
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Lista completa de atributos con su formato mejorado
        self.attributes = [
            {'magento_code': 'adaptacion_de_valvula', 'custom_code': 'adaptacion de valvula'},
            {'magento_code': 'ajuste_manubrio_spinning', 'custom_code': 'ajuste de manubrio spinning'},
            {'magento_code': 'ajuste_rebote_tenedor', 'custom_code': 'ajuste de rebote tenedor'},
            {'magento_code': 'ajuste_sillin_spinning', 'custom_code': 'ajuste de sillin spinning'},
            {'magento_code': 'alto', 'custom_code': 'alto'},
            {'magento_code': 'ancho', 'custom_code': 'ancho'},
            {'magento_code': 'ANCHO_MOTO', 'custom_code': 'ancho de moto'},
            {'magento_code': 'barbore_espiga', 'custom_code': 'barbore de espiga'},
            {'magento_code': 'boquilla', 'custom_code': 'boquilla'},
            {'magento_code': 'cantidad_funciones', 'custom_code': 'cantidad de funciones'},
            {'magento_code': 'cant_led', 'custom_code': 'cantidad de leds'},
            {'magento_code': 'capacidad', 'custom_code': 'capacidad'},
            {'magento_code': 'capacidad_total_bolso', 'custom_code': 'capacidad total de bolso'},
            {'magento_code': 'capacidad_vejiga', 'custom_code': 'capacidad de vejiga'},
            {'magento_code': 'color', 'custom_code': 'color'},
            {'magento_code': 'color_marco_lente', 'custom_code': 'color de marco lente'},
            {'magento_code': 'color_protector_plastico', 'custom_code': 'color de protector plastico'},
            {'magento_code': 'componentes_del_juego', 'custom_code': 'componentes del juego'},
            {'magento_code': 'composicion', 'custom_code': 'composicion'},
            {'magento_code': 'configuracion_dientes', 'custom_code': 'configuracion de dientes'},
            {'magento_code': 'deporte', 'custom_code': 'deporte'},
            {'magento_code': 'diametro', 'custom_code': 'diametro'},
            {'magento_code': 'diametro_x_ancho', 'custom_code': 'diametro por ancho'},
            {'magento_code': 'diseno_cintas', 'custom_code': 'diseño de cintas'},
            {'magento_code': 'ensamblado', 'custom_code': 'ensamblado'},
            {'magento_code': 'estructura_multifuerza', 'custom_code': 'estructura multifuerza'},
            {'magento_code': 'flare_direccion', 'custom_code': 'flare de direccion'},
            {'magento_code': 'forma_pesas', 'custom_code': 'forma de pesas'},
            {'magento_code': 'genero', 'custom_code': 'genero'},
            {'magento_code': 'guias_chocles', 'custom_code': 'guias de chocles'},
            {'magento_code': 'integrada_direccion', 'custom_code': 'direccion integrada'},
            {'magento_code': 'largo', 'custom_code': 'largo'},
            {'magento_code': 'longitud', 'custom_code': 'longitud'},
            {'magento_code': 'Lumens', 'custom_code': 'lumens'},
            {'magento_code': 'luz', 'custom_code': 'luz'},
            {'magento_code': 'manga', 'custom_code': 'manga'},
            {'magento_code': 'marca', 'custom_code': 'marca'},
            {'magento_code': 'MarcaFre01', 'custom_code': 'marca freno'},
            {'magento_code': 'marca_de_cambios', 'custom_code': 'marca de cambios'},
            {'magento_code': 'material', 'custom_code': 'material'},
            {'magento_code': 'material_barra_mancuernas', 'custom_code': 'material de barra mancuernas'},
            {'magento_code': 'material_biela', 'custom_code': 'material de biela'},
            {'magento_code': 'material_botellas_tenedor', 'custom_code': 'material de botellas tenedor'},
            {'magento_code': 'material_canasta', 'custom_code': 'material de canasta'},
            {'magento_code': 'material_chasis_patines', 'custom_code': 'material de chasis patines'},
            {'magento_code': 'material_coronilla', 'custom_code': 'material de coronilla'},
            {'magento_code': 'material_discos_mancuernas', 'custom_code': 'material de discos mancuernas'},
            {'magento_code': 'material_lente', 'custom_code': 'material de lente'},
            {'magento_code': 'material_manecillas_freno', 'custom_code': 'material de manecillas freno'},
            {'magento_code': 'material_mango_cuerda', 'custom_code': 'material de mango cuerda'},
            {'magento_code': 'material_recubrimiento', 'custom_code': 'material de recubrimiento'},
            {'magento_code': 'material_riel_galapago', 'custom_code': 'material de riel galapago'},
            {'magento_code': 'material_ruedas_patines', 'custom_code': 'material de ruedas patines'},
            {'magento_code': 'material_suela', 'custom_code': 'material de suela'},
            {'magento_code': 'medida_cadena_moto', 'custom_code': 'medida de cadena moto'},
            {'magento_code': 'modalidad', 'custom_code': 'modalidad'},
            {'magento_code': 'modelo', 'custom_code': 'modelo'},
            {'magento_code': 'modelo_bateria', 'custom_code': 'modelo de bateria'},
            {'magento_code': 'modelo_bujia', 'custom_code': 'modelo de bujia'},
            {'magento_code': 'modelo_camisa', 'custom_code': 'modelo de camisa'},
            {'magento_code': 'modelo_de_palanca', 'custom_code': 'modelo de palanca'},
            {'magento_code': 'modelo_de_pedal', 'custom_code': 'modelo de pedal'},
            {'magento_code': 'modelo_guante', 'custom_code': 'modelo de guante'},
            {'magento_code': 'modelo_luz', 'custom_code': 'modelo de luz'},
            {'magento_code': 'modelo_pantaloneta', 'custom_code': 'modelo de pantaloneta'},
            {'magento_code': 'modelo_pata', 'custom_code': 'modelo de pata'},
            {'magento_code': 'modelo_portacaram', 'custom_code': 'modelo de porta caramañola'},
            {'magento_code': 'modelo_zapatilla', 'custom_code': 'modelo de zapatilla'},
            {'magento_code': 'monitor_funciones', 'custom_code': 'monitor de funciones'},
            {'magento_code': 'numero_ejercicios_multifuerza', 'custom_code': 'numero de ejercicios multifuerza'},
            {'magento_code': 'numero_eslabones_cadena', 'custom_code': 'numero de eslabones cadena'},
            {'magento_code': 'numero_huecos_manzana', 'custom_code': 'numero de huecos manzana'},
            {'magento_code': 'numero_niveles_eliptica', 'custom_code': 'numero de niveles eliptica'},
            {'magento_code': 'numero_programas_caminadora', 'custom_code': 'numero de programas caminadora'},
            {'magento_code': 'numero_ruedas_patines', 'custom_code': 'numero de ruedas patines'},
            {'magento_code': 'palma', 'custom_code': 'palma'},
            {'magento_code': 'patron_labrado', 'custom_code': 'patron de labrado'},
            {'magento_code': 'perfil_aro', 'custom_code': 'perfil de aro'},
            {'magento_code': 'peso_fitness', 'custom_code': 'peso fitness'},
            {'magento_code': 'peso_maximo', 'custom_code': 'peso maximo'},
            {'magento_code': 'peso_torre_multifuerza', 'custom_code': 'peso de torre multifuerza'},
            {'magento_code': 'peso_unidad_pesas', 'custom_code': 'peso de unidad pesas'},
            {'magento_code': 'peso_volante', 'custom_code': 'peso de volante'},
            {'magento_code': 'piezas', 'custom_code': 'piezas'},
            {'magento_code': 'posicion', 'custom_code': 'posicion'},
            {'magento_code': 'potencia_motor', 'custom_code': 'potencia de motor'},
            {'magento_code': 'presion_maxima', 'custom_code': 'presion maxima'},
            {'magento_code': 'recorrido_tenedor', 'custom_code': 'recorrido de tenedor'},
            {'magento_code': 'resistencia_maxima', 'custom_code': 'resistencia maxima'},
            {'magento_code': 'rin', 'custom_code': 'rin'},
            {'magento_code': 'rise_alto', 'custom_code': 'rise alto'},
            {'magento_code': 'seguridad', 'custom_code': 'seguridad'},
            {'magento_code': 'sistema_freno', 'custom_code': 'sistema de freno'},
            {'magento_code': 'sistema_repuesto', 'custom_code': 'sistema de repuesto'},
            {'magento_code': 'sistema_transmision_spinning', 'custom_code': 'sistema de transmision spinning'},
            {'magento_code': 'size', 'custom_code': 'talla'},
            {'magento_code': 'tamano_banda_caminadora', 'custom_code': 'tamaño de banda caminadora'},
            {'magento_code': 'tamano_barra_mancuernas', 'custom_code': 'tamaño de barra mancuernas'},
            {'magento_code': 'tamano_extension', 'custom_code': 'tamaño de extension'},
            {'magento_code': 'tamano_fitness', 'custom_code': 'tamaño fitness'},
            {'magento_code': 'Tamano_Galapago', 'custom_code': 'tamaño de galapago'},
            {'magento_code': 'tamano_llanta', 'custom_code': 'tamaño de llanta'},
            {'magento_code': 'tamano_manecillas_freno', 'custom_code': 'tamaño de manecillas freno'},
            {'magento_code': 'tamano_mango', 'custom_code': 'tamaño de mango'},
            {'magento_code': 'tamano_neumatico', 'custom_code': 'tamaño de neumatico'},
            {'magento_code': 'tamano_ruedas_patines', 'custom_code': 'tamaño de ruedas patines'},
            {'magento_code': 'tamano_tapete', 'custom_code': 'tamaño de tapete'},
            {'magento_code': 'tamano_valvula_neumatico', 'custom_code': 'tamaño de valvula neumatico'},
            {'magento_code': 'tecnologia_llanta', 'custom_code': 'tecnologia de llanta'},
            {'magento_code': 'terminado', 'custom_code': 'terminado'},
            {'magento_code': 'terminado_cadena', 'custom_code': 'terminado de cadena'},
            {'magento_code': 'textura', 'custom_code': 'textura'},
            {'magento_code': 'tipo', 'custom_code': 'tipo'},
            {'magento_code': 'tipo_agarre', 'custom_code': 'tipo de agarre'},
            {'magento_code': 'tipo_ajuste_mancuernas', 'custom_code': 'tipo de ajuste mancuernas'},
            {'magento_code': 'tipo_banco', 'custom_code': 'tipo de banco'},
            {'magento_code': 'tipo_barra', 'custom_code': 'tipo de barra'},
            {'magento_code': 'tipo_bloqueo_suspension', 'custom_code': 'tipo de bloqueo suspension'},
            {'magento_code': 'tipo_bomba', 'custom_code': 'tipo de bomba'},
            {'magento_code': 'tipo_cadena_moto', 'custom_code': 'tipo de cadena moto'},
            {'magento_code': 'tipo_caminadora', 'custom_code': 'tipo de caminadora'},
            {'magento_code': 'tipo_cana_tenedor', 'custom_code': 'tipo de caña tenedor'},
            {'magento_code': 'tipo_candado', 'custom_code': 'tipo de candado'},
            {'magento_code': 'tipo_cierre', 'custom_code': 'tipo de cierre'},
            {'magento_code': 'tipo_de_ajuste', 'custom_code': 'tipo de ajuste'},
            {'magento_code': 'Tipo_de_manecilla', 'custom_code': 'tipo de manecilla'},
            {'magento_code': 'tipo_direccion_bicicletas', 'custom_code': 'tipo de direccion bicicletas'},
            {'magento_code': 'tipo_eje', 'custom_code': 'tipo de eje'},
            {'magento_code': 'tipo_espiga', 'custom_code': 'tipo de espiga'},
            {'magento_code': 'tipo_freno', 'custom_code': 'tipo de freno'},
            {'magento_code': 'tipo_galapago', 'custom_code': 'tipo de galapago'},
            {'magento_code': 'tipo_guante', 'custom_code': 'tipo de guante'},
            {'magento_code': 'tipo_guardabarro', 'custom_code': 'tipo de guardabarro'},
            {'magento_code': 'tipo_inclinacion_caminadora', 'custom_code': 'tipo de inclinacion caminadora'},
            {'magento_code': 'tipo_labrado_llanta', 'custom_code': 'tipo de labrado llanta'},
            {'magento_code': 'TIPO_LLANTA_MOTO', 'custom_code': 'tipo de llanta moto'},
            {'magento_code': 'tipo_luz', 'custom_code': 'tipo de luz'},
            {'magento_code': 'tipo_mango', 'custom_code': 'tipo de mango'},
            {'magento_code': 'tipo_manzana', 'custom_code': 'tipo de manzana'},
            {'magento_code': 'tipo_manzana_freno', 'custom_code': 'tipo de manzana freno'},
            {'magento_code': 'tipo_moldeado_neumatico', 'custom_code': 'tipo de moldeado neumatico'},
            {'magento_code': 'tipo_palanca', 'custom_code': 'tipo de palanca'},
            {'magento_code': 'tipo_pantaloneta', 'custom_code': 'tipo de pantaloneta'},
            {'magento_code': 'tipo_pesas', 'custom_code': 'tipo de pesas'},
            {'magento_code': 'tipo_pista_direccion', 'custom_code': 'tipo de pista direccion'},
            {'magento_code': 'tipo_plato', 'custom_code': 'tipo de plato'},
            {'magento_code': 'tipo_puno', 'custom_code': 'tipo de puño'},
            {'magento_code': 'tipo_relleno', 'custom_code': 'tipo de relleno'},
            {'magento_code': 'tipo_rodamiento', 'custom_code': 'tipo de rodamiento'},
            {'magento_code': 'tipo_suspension', 'custom_code': 'tipo de suspension'},
            {'magento_code': 'Tipo_tapa', 'custom_code': 'tipo de tapa'},
            {'magento_code': 'tipo_tenedor', 'custom_code': 'tipo de tenedor'},
            {'magento_code': 'MarcaTen01', 'custom_code': 'marca de tenedor'},
            {'magento_code': 'tipo_valvula_neumatico', 'custom_code': 'tipo de valvula neumatico'},
            {'magento_code': 'tpi_llanta', 'custom_code': 'tpi de llanta'},
            {'magento_code': 'uso_barra', 'custom_code': 'uso de barra'},
            {'magento_code': 'uso_bolso', 'custom_code': 'uso de bolso'},
            {'magento_code': 'uso_para_patines', 'custom_code': 'uso para patines'},
            {'magento_code': 'uso_ropa', 'custom_code': 'uso de ropa'},
            {'magento_code': 'velocidades', 'custom_code': 'velocidades'},
            {'magento_code': 'velocidades_bicicletas', 'custom_code': 'velocidades de bicicletas'},
            {'magento_code': 'velocidades_cadena', 'custom_code': 'velocidades de cadena'},
            {'magento_code': 'velocidad_maxima', 'custom_code': 'velocidad maxima'}
        ]
    
    def get_attribute_data(self, attribute_mapping):
        """Obtiene datos de atributos directamente de la base de datos de Magento"""
        query = f'''
        SELECT 
            ea.attribute_code,
            eaov.value_id,
            eaov.value AS label
        FROM 
            eav_attribute_option_value eaov
        JOIN 
            eav_attribute_option eao ON eaov.option_id = eao.option_id
        JOIN 
            eav_attribute ea ON eao.attribute_id = ea.attribute_id
        WHERE 
            ea.entity_type_id = (
                SELECT entity_type_id 
                FROM eav_entity_type 
                WHERE entity_type_code = 'catalog_product'
            )
            AND ea.attribute_code = '{attribute_mapping["magento_code"]}'
            AND UPPER(eaov.value) != 'N/A'
        '''
        
        output = self.magento.execute_query(query)
        if not output:
            return None
            
        lines = output.strip().split('\n')[1:]  # Ignorar la primera línea (headers)
        
        options = []
        for line in lines:
            if line.strip():
                _, value_id, label = line.split('\t')
                options.append({
                    'value': value_id,
                    'label': label
                })
        
        return {'options': options}
    
    def validate_option(self, option):
        """Valida y limpia los datos de una opción antes de insertarla"""
        value_id = option.get('value', '')
        
        # Si value_id está vacío o no es numérico, retornar None
        if not value_id or not str(value_id).strip().isdigit():
            return None
            
        return {
            'value_id': int(value_id),
            'label': option.get('label', '').strip() or 'Sin etiqueta'
        }
            
    def save_attribute_to_database(self, attribute_code, base_attribute_code, data):
        if not data or 'options' not in data:
            logging.warning(f"No se encontraron datos de {attribute_code} para guardar")
            return
            
        db = DatabaseConnection()
        connection = db.connect()
        
        if not connection:
            return
            
        cursor = None
        try:
            with self.db_lock:
                cursor = connection.cursor()
                
                check_query = """
                SELECT id FROM attribute_values 
                WHERE attribute_code = %s AND value_id = %s
                """
                
                insert_query = """
                INSERT INTO attribute_values (base_attribute_code, attribute_code, value_id, label)
                VALUES (%s, %s, %s, %s)
                """
                
                registros_nuevos = 0
                registros_existentes = 0
                registros_invalidos = 0
                
                for option in data['options']:
                    # Validar y limpiar los datos
                    validated_option = self.validate_option(option)
                    
                    if validated_option is None:
                        registros_invalidos += 1
                        continue
                        
                    cursor.execute(check_query, (attribute_code, validated_option['value_id']))
                    exists = cursor.fetchone()
                    
                    if not exists:
                        values = (
                            base_attribute_code,
                            attribute_code,
                            validated_option['value_id'],
                            validated_option['label']
                        )
                        cursor.execute(insert_query, values)
                        registros_nuevos += 1
                    else:
                        registros_existentes += 1
                
                connection.commit()
                logging.info(f"Proceso completado para {attribute_code}:")
                logging.info(f"- Registros nuevos insertados: {registros_nuevos}")
                logging.info(f"- Registros existentes omitidos: {registros_existentes}")
                logging.info(f"- Registros inválidos omitidos: {registros_invalidos}")
                
        except Exception as e:
            logging.error(f"Error al guardar los datos de {attribute_code}: {e}")
            if connection:
                connection.rollback()
        
        finally:
            if cursor:
                cursor.close()
            db.disconnect()
    
    def process_attribute(self, attribute):
        """Procesa un único atributo - función para ser ejecutada en un hilo"""
        logging.info(f"Iniciando proceso para {attribute['custom_code']}...")
        data = self.get_attribute_data(attribute)
        if data:
            self.save_attribute_to_database(
                attribute['custom_code'],
                attribute['magento_code'],
                data
            )
        logging.info(f"Finalizado proceso para {attribute['custom_code']}")
    
    def process_all_attributes(self):
        logging.info("Iniciando proceso de actualización de atributos...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_attribute, attribute) 
                      for attribute in self.attributes]
            
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error en proceso de atributo: {e}")
        
        logging.info("Proceso de actualización de atributos completado")

if __name__ == "__main__":
    service = AttributeService(max_workers=5)
    service.process_all_attributes()