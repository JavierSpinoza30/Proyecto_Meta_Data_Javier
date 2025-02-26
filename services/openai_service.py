from openai import OpenAI
import os
from dotenv import load_dotenv  # Importar dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def generate_product_description(self, product_data):
        """
        Genera una descripción del producto basada en sus atributos
        """
        # Construir el prompt con los atributos del producto
        prompt = f"""
        Genera una descripción atractiva y SEO friendly para este producto:
        
        Nombre: {product_data['name']}
        Tipo: {product_data['type_id']}
        Atributos:
        {self._format_attributes(product_data['attributes'])}
        
        La descripción debe ser detallada, enfocada en beneficios y características principales.
        DEBE USAR ESTE FORMATO HTML:
        
        <h1 data-content-type="heading">[NOMBRE DEL PRODUCTO AQUÍ]</h1>
        [CONTENIDO DESCRIPTIVO AQUÍ CON PÁRRAFOS, LISTAS Y ELEMENTOS HTML como <strong> ]
        <p><strong>Ficha técnica:</strong><br>[LISTA DE ESPECIFICACIONES TÉCNICAS]</p>
        <p>[AGREGAR UN PÁRRAFO FINAL QUE RESUMA LOS BENEFICIOS DEL PRODUCTO Y LLAME A LA ACCIÓN]</p>
        
        Debes usar negritas con <strong> y saltos de línea con <br>, no puedes incluir otros caracteres como **. NO INCLUIR el estilo inicial, solo el contenido.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en marketing, SEO y descripción de productos. Tu objetivo es crear descripciones atractivas y optimizadas para motores de búsqueda que destaquen los beneficios clave del producto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=780    # Limita la respuesta a ~500 palabras
        )

        return self._wrap_in_html_template(response.choices[0].message.content)

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

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en SEO y marketing de bicicletas. Genera keywords que coincidan EXACTAMENTE con lo que los compradores buscan, incluyendo términos cortos y directos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        # Limpiar la respuesta
        keywords = response.choices[0].message.content.strip()
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
        1. Longitud máxima: 45-50 caracteres
        2. Debe incluir la marca/nombre del producto
        3. Debe incluir una palabra clave principal
        4. Estructura según tipo de producto:
           - KIT: "Kit [Producto] | [Marca/Característica Principal]"
           - ACCESORIO: "[Tipo Accesorio] para [Producto] | [Marca]"
           - REPUESTO: "[Tipo Repuesto] [Producto] | [Marca/Especificación]"
        
        5. IMPORTANTE:
           - Usar palabras relevantes al inicio
           - Incluir la marca o característica distintiva
           - Separar secciones con '|' o '-'
           - NO usar caracteres especiales
        
        Ejemplos según tipo:
        - KIT: "Kit de Frenos MTB Shimano | Alta Calidad"
        - ACCESORIO: "Soporte GPS Universal para Moto | Resistente al Agua"
        - REPUESTO: "Pastillas de Freno Yamaha R3 | Original"
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en SEO y marketing. Genera meta titles optimizados que maximicen la visibilidad en buscadores."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        # Limpiar la respuesta
        meta_title = response.choices[0].message.content.strip()
        if ":" in meta_title:
            meta_title = meta_title.split(":")[-1].strip()
        meta_title = meta_title.replace('"', '').replace('`', '')
        
        return meta_title
