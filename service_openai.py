import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

# Obtener la clave API de las variables de entorno
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[
                {"role": "system", "content": "Eres un experto en SEO de Magento"},
                {"role": "user", "content": "Hola como estas"}
            ],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
