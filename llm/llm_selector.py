import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Cargar variables de entorno
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://voiceflip-openai.openai.azure.com/")
subscription_key = os.getenv("AZURE_OPENAI_KEY", "FwsUIhIZedFYxW7nGYwKgoJsMXYAH62OE4QThqLrwtKuCc5m17AjJQQJ99BEACYeBjFXJ3w3AAABACOGfF7h")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

def get_azure_openai_client():
    """Crea y retorna el cliente de Azure OpenAI."""
    if not subscription_key or subscription_key == "<your-api-key>":
        raise ValueError("API Key de Azure OpenAI no está configurada o es inválida.")
    
    return AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

def generate_css_selector(html_snippet, element_description, default_selector):
    """
    Envía un fragmento de HTML y la descripción del elemento deseado a Azure OpenAI
    para generar el selector CSS correspondiente de manera dinámica.
    """
    try:
        client = get_azure_openai_client()
        
        prompt = f"""
        Analiza el siguiente fragmento de código HTML y genera un selector CSS válido y específico para extraer el elemento que contiene: "{element_description}".
        
        HTML:
        \"\"\"
        {html_snippet}
        \"\"\"
        
        Reglas estrictas:
        - Responde ÚNICAMENTE con la cadena de texto del selector CSS (ej. ".product-title", "h3.item-name-alt", "span.price").
        - No incluyas explicaciones, ni bloques de código markdown (como ```css ... ```), ni comillas adicionales.
        - Si el selector es de clase, asegúrate de incluir el punto inicial (.).
        - El selector debe poder aplicarse con BeautifulSoup (.select_one o .select) o Selenium (By.CSS_SELECTOR).
        """
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "Eres un asistente experto en web scraping y selectores CSS/XPath. Eres preciso y sigues reglas de salida sin decoraciones."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        selector = response.choices[0].message.content.strip()
        # Limpieza básica por si el modelo incluye Markdown accidentalmente
        selector = selector.replace("```css", "").replace("```", "").strip()
        selector = selector.strip("'\"")
        
        print(f"[LLM Selector] Generado: '{selector}' para '{element_description}'")
        return selector

    except Exception as e:
        print(f"[LLM Selector Error] Error al generar selector dinámico: {e}")
        print(f"[LLM Selector] Usando selector por defecto: '{default_selector}'")
        return default_selector

# Código para pruebas rápidas
if __name__ == "__main__":
    test_html = """
    <div class="item-box-alt" data-id="1">
        <h3 class="item-name-alt">Laptop Gamer Ryzen 7</h3>
        <div class="item-cost-alt">$1250.00</div>
        <div class="meta-info">Enlace original: <span class="prod-url">https://tiendamock.com/laptop-gaming-1</span></div>
    </div>
    """
    print("--- Test LLM Selector ---")
    title_sel = generate_css_selector(test_html, "el nombre del producto (título)", ".product-title")
    price_sel = generate_css_selector(test_html, "el precio del producto", ".product-price")
    print(f"Resultado del título: {title_sel}")
    print(f"Resultado del precio: {price_sel}")
