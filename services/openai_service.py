from google import genai
from google.genai import types
import os
from dotenv import load_dotenv  # Importar dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    def generate_product_description(self, product_data):
        """
        Genera una descripción del producto basada en sus atributos y categorías
        """
        # Obtener el número de atributos y categorías
        num_attributes = len(product_data['attributes']) if product_data.get('attributes') else 0
        categories = product_data.get('category', '').split(' > ')
        num_categories = len(categories)
        
        # Identificar el contexto principal del producto
        main_category = categories[0] if categories else ''
        product_context = self._get_product_context(main_category, product_data['name'])
        
        # Construir el prompt con los atributos y categorías del producto
        prompt = f"""
        Genera una descripción técnica y comercial para este producto:
        
        Nombre: {product_data['name']}
        Tipo: {product_data['type_id']}
        Contexto: {product_context}
        Jerarquía de Categorías: {' > '.join(categories) if categories else 'No disponible'}
        
        {'Atributos Técnicos:' if num_attributes > 0 else 'IMPORTANTE: Este producto no tiene atributos técnicos específicos documentados'}
        {self._format_attributes(product_data['attributes']) if num_attributes > 0 else ''}
        
        INSTRUCCIONES ESPECÍFICAS:
        {self._get_context_instructions(num_attributes, num_categories, main_category)}
        
        REGLAS ESTRICTAS PARA LA FICHA TÉCNICA:
        1. NO INVENTES características técnicas que no estén en los atributos proporcionados
        2. Si no hay atributos técnicos, la ficha técnica SOLO debe incluir:
           - Tipo de producto: {product_data['type_id']}
           - Categoría principal: {main_category}
           - Aplicación: {categories[-1] if categories else 'General'}
        3. NO agregues especificaciones inventadas de:
           - Materiales
           - Dimensiones
           - Colores
           - Características técnicas no documentadas
        
        La descripción debe ser detallada, enfocada en beneficios y características principales.
        DEBE USAR ESTE FORMATO HTML:
        
        <h1 data-content-type="heading">[NOMBRE DEL PRODUCTO AQUÍ]</h1>
        [CONTENIDO DESCRIPTIVO AQUÍ CON PÁRRAFOS, LISTAS Y ELEMENTOS HTML como <strong> ]
        {'<p><strong>Ficha técnica:</strong><br>[USAR SOLO LOS ATRIBUTOS PROPORCIONADOS, NO INVENTAR]</p>' if num_attributes > 0 else '<p><strong>Información General:</strong><br>[SOLO TIPO, CATEGORÍA Y APLICACIÓN]</p>'}
        <p>[AGREGAR UN PÁRRAFO FINAL QUE RESUMA LOS BENEFICIOS DEL PRODUCTO Y LLAME A LA ACCIÓN]</p>
        
        Debes usar negritas con <strong> y saltos de línea con <br>, no puedes incluir otros caracteres como **. NO INCLUIR el estilo inicial, solo el contenido.
        """

        # Configuración del sistema para Gemini
        system_instruction = f"Eres un experto técnico en {product_context}. Tu objetivo es crear descripciones precisas y técnicamente correctas que ayuden a los compradores a entender el producto y su aplicación específica. NUNCA debes inventar especificaciones técnicas no proporcionadas."

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.5,
                max_output_tokens=800
            ),
            contents=prompt
        )

        return self._wrap_in_html_template(response.text)

    def _get_product_context(self, main_category, product_name):
        """
        Determina el contexto técnico del producto basado en su categoría principal y nombre
        """
        context_map = {
            'MOTOS': 'repuestos y componentes de motocicletas',
            'BICICLETAS': 'bicicletas y sus componentes',
            'REPUESTOS': 'repuestos y accesorios para vehículos',
            'ACCESORIOS': 'accesorios y equipamiento para ciclismo y motociclismo'
        }
        return context_map.get(main_category, 'productos automotrices y de ciclismo')

    def _get_context_instructions(self, num_attributes, num_categories, main_category):
        """
        Genera instrucciones específicas basadas en la cantidad de atributos y categorías disponibles
        """
        if num_attributes >= 6:
            return f"""
            - Este es un producto técnico de {main_category.lower()} - mantén un enfoque técnico y preciso
            - Utiliza SOLO los atributos disponibles para detallar especificaciones técnicas
            - Menciona compatibilidad y aplicaciones específicas
            - Incluye información sobre instalación o uso si es relevante
            """
        elif num_categories >= 4:
            return f"""
            - Este es un producto técnico de {main_category.lower()} con {num_categories} niveles de especialización
            - Enfatiza el uso específico y aplicación técnica según su categorización
            - Describe la función específica del componente en el sistema o vehículo
            - {'Usa ÚNICAMENTE los ' + str(num_attributes) + ' atributos técnicos disponibles' if num_attributes > 0 else 'NO INVENTES especificaciones técnicas, céntrate en la función y aplicación específica del componente'}
            - Menciona compatibilidad con modelos específicos SOLO si está en las categorías
            - Incluye información sobre instalación o mantenimiento general
            """
        else:
            return f"""
            - Este es un producto técnico de {main_category.lower()} - mantén el enfoque técnico
            - Describe la función específica del componente sin inventar especificaciones
            - Menciona compatibilidad y aplicaciones según las categorías proporcionadas
            - NO agregues características técnicas que no estén documentadas
            """

    def _format_attributes(self, attributes):
        # Formatea los atributos para el prompt con nombres en negrita
        return "\n".join([f"- <strong>{attr['code']}</strong>: {attr['label']}" for attr in attributes])

    def _wrap_in_html_template(self, content):
        # Eliminar ```html si están presentes
        content = content.replace('```html', '').replace('```', '').strip()
        
        # Separar el nombre del producto del contenido
        product_name = content.split('</h1>')[0].replace('<h1 data-content-type="heading">', '')
        description_content = content.split('</h1>')[1].strip()

        # Plantilla con el formato requerido y CSS escapado
        base_template = """<style>#html-body [data-pb-style=FKK7CQJ],#html-body [data-pb-style=OGKJ8X3]{{justify-content:flex-start;display:flex;flex-direction:column;background-position:left top;background-size:cover;background-repeat:no-repeat;background-attachment:scroll}}</style>
        <div data-content-type="row" data-appearance="contained" data-element="main">
            <div data-enable-parallax="0" data-parallax-speed="0.5" data-background-images="" data-background-type="image" data-video-loop="true" data-video-play-only-visible="true" data-video-lazy-load="true" data-video-fallback-src="" data-element="inner" data-pb-style="FKK7CQJ">
                <h1 data-content-type="heading" data-appearance="default" data-element="main">{}</h1>
            </div>
        </div>
        <div data-content-type="row" data-appearance="contained" data-element="main">
            <div data-enable-parallax="0" data-parallax-speed="0.5" data-background-images="" data-background-type="image" data-video-loop="true" data-video-play-only-visible="true" data-video-lazy-load="true" data-video-fallback-src="" data-element="inner" data-pb-style="OGKJ8X3">
                <div data-content-type="text" data-appearance="default" data-element="main">
                    {}
                </div>
            </div>
        </div>"""
        
        # Formatear correctamente el contenido
        formatted_content = description_content.replace('\n', '</p>\r\n<p>').replace('\r', '')
        return base_template.format(product_name, formatted_content)
    # fin generar descripcion de los productos
    
    def generate_meta_keywords(self, product_data):
        """
        Genera meta keywords para el producto basado en sus atributos
        """
        num_attributes = len(product_data['attributes'])
        
        prompt = f"""
        Genera meta keywords optimizadas para SEO y conversión comercial:
        
        Nombre: {product_data['name']}
        Tipo: {product_data['type_id']}
        Atributos:
        {self._format_attributes(product_data['attributes'])}
        
        REGLAS IMPORTANTES:
        1. {'Generar solo 2-3 keywords relevantes' if num_attributes <= 2 else 'Máximo 3-15 keywords relevantes'}
        2. MANTENER EL CONTEXTO DEL TIPO DE PRODUCTO:
           - Si es un KIT: enfocarse en términos como "kit", "set", "conjunto"
           - Si es un ACCESORIO: usar términos como "accesorio", "complemento"
           - Si es un REPUESTO: usar términos como "repuesto", "pieza", "parte"
           
        3. NO CONFUNDIR CATEGORÍAS:
           - Si es un kit de bicicleta, NO generar keywords como si fuera una bicicleta completa
           - Si es un repuesto de moto, NO generar keywords relacionadas con la moto completa
           - Si es un accesorio, NO generar keywords del producto principal
        
        4. ESTRUCTURA DE KEYWORDS según cantidad de atributos:
           {'- Nombre completo del producto y máximo 2 términos genéricos relevantes' if num_attributes <= 2 else '''
           - Términos específicos del tipo de producto (ej: "kit ensamble bicicleta")
           - Variaciones con características principales (ej: "kit bicicleta 29er")
           - Términos de búsqueda comunes (ej: "kit armado bicicleta")
           - Especificaciones relevantes (ej: "kit bicicleta 9 velocidades")'''}
        
        5. IMPORTANTE: 
           - Separar keywords solo con comas
           - Mantener el contexto del tipo de producto en CADA keyword
           - NO generar confusión con productos completos
        
        {'Ejemplo para productos con pocos atributos:' if num_attributes <= 2 else 'Ejemplo IDEAL de formato según tipo de producto:'}
        {'tornillo m4 acero, tornillos métricos, repuesto tornillo' if num_attributes <= 2 else '''
        Para un KIT:
        kit ensamble bicicleta 29er, kit armado jasper hl, set ensamble bicicleta 9v, kit bicicleta negro blanco
        
        Para una BICICLETA:
        bicicleta optimus aquila, optimus aquila 29er, bicicleta montaña optimus, mtb optimus aquila
        
        Para un REPUESTO DE MOTO:
        repuesto freno ax100, pastilla freno moto ax100, repuesto original ax100, freno delantero ax100
        
        Para un ACCESORIO:
        soporte celular moto, accesorio porta celular, soporte gps motocicleta, accesorio moto universal
        
        Para HERRAMIENTAS:
        llave allen 4mm, herramienta allen métrica, llave hexagonal bicicleta, herramienta taller
        
        NOTA: Observa cómo cada tipo de producto mantiene sus palabras clave distintivas:
        - KITs siempre incluyen "kit", "set" o "ensamble"
        - REPUESTOS usan "repuesto", "pieza", "parte"
        - ACCESORIOS usan "accesorio", "soporte", "complemento"
        - HERRAMIENTAS usan "herramienta", "llave", términos técnicos específicos'''}
        """

        # Configuración del sistema para Gemini
        system_instruction = "Eres un experto en SEO y marketing de bicicletas. Genera keywords que coincidan EXACTAMENTE con lo que los compradores buscan, incluyendo términos cortos y directos."

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.5
            ),
            contents=prompt
        )

        # Limpiar la respuesta
        keywords = response.text.strip()
        if ":" in keywords:
            keywords = keywords.split(":")[-1].strip()
        keywords = keywords.replace('"', '').replace('`', '')
        
        return keywords

    def generate_meta_title(self, product_data):
        """
        Genera meta title para el producto basado en sus atributos
        """
        num_attributes = len(product_data['attributes'])
        
        prompt = f"""
        Genera un meta title optimizado para SEO y conversión comercial:
        
        Nombre: {product_data['name']}
        Tipo: {product_data['type_id']}
        Atributos:
        {self._format_attributes(product_data['attributes'])}
        
        REGLAS IMPORTANTES QUE DEBES CUMPLIR:
        1. Longitud máxima: 50-60 caracteres
        2. Debe incluir el nombre exacto del producto
        3. Debe incluir una palabra clave principal
        4. Estructura según tipo de producto:
           - KIT: "Kit de [Producto específico] | Alta Calidad"
           - ACCESORIO: "[Tipo Accesorio específico] para [Producto] | Calidad"
           - REPUESTO: "[Tipo Repuesto específico] [Producto] | Original"
        
        5. IMPORTANTE:
           - Usar palabras relevantes al inicio
           - Incluir características distintivas
           - Separar secciones con '|' o '-'
           - NO usar caracteres especiales
           - NO incluir marcadores de posición como [Marca] o [Tu Marca]
           - Usar el nombre específico del producto ya proporcionado
        
        Ejemplos según tipo:
        - KIT: "Kit de Frenos MTB Shimano Deore | Alta Calidad"
        - ACCESORIO: "Soporte GPS Universal para Moto | Resistente"
        - REPUESTO: "Pastillas de Freno Yamaha R3 | Original"
        """

        # Configuración del sistema para Gemini
        system_instruction = "Eres un experto en SEO y marketing. Genera meta titles optimizados que maximicen la visibilidad en buscadores. Usa SOLO información real, nunca uses marcadores de posición como [Marca] o [Tu Marca]."

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            ),
            contents=prompt
        )

        # Limpiar la respuesta
        meta_title = response.text.strip()
        if ":" in meta_title:
            meta_title = meta_title.split(":")[-1].strip()
        meta_title = meta_title.replace('"', '').replace('`', '')
        
        # Eliminar cualquier marcador de posición que pudiera haberse colado
        meta_title = meta_title.replace('[Tu Marca]', '').replace('[Marca]', '')
        meta_title = meta_title.replace('| |', '|').replace('||', '|').strip()
        if meta_title.endswith('|'):
            meta_title = meta_title[:-1].strip()
        
        return meta_title
